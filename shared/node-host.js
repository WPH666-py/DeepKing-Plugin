#!/usr/bin/env node
/* ============================================================
 * DeepKing-Plugin · shared/node-host.js  (v0.1.3 功能对齐 DeepKing)
 * - DeepSeek 客户端 + Agent Loop（含上下文自动压缩）
 * - 工具集：read/write/edit/bash/grep/glob/todo/task/check_runtime
 *           delete/read_image(视觉)/read_pdf/read_excel/web_search/install/check python
 * - 多模态视觉：ModLens / DeepSeek-OCR（OpenAI 兼容 vision API，移植自 DeepKing vision.rs）
 * - 双模式：库模式（VSCode require） / --port 服务模式（JetBrains/浏览器）
 * ============================================================ */
"use strict";
const fs = require("fs");
const path = require("path");
const { execFile } = require("child_process");

/* ───────── 模式 Persona ───────── */
const MODES = {
  dsh: {
    label: "DSH (Harness)",
    system: `You are an autonomous coding agent (DeepSeek Harness style) working in the user's workspace.
Rules:
- For multi-step tasks FIRST call todo_write to plan; mark items completed as you go.
- For unknown codebases FIRST call glob + grep to build a map.
- Use bash for any build/test/run. Prefer small, runnable iterations; verify after each step.
- Before editing an existing file, call read on it first (exact content for old_string).
- Efficiency: ONE batch_edit/batch_write call for several files; delegate independent subtasks to subagents (1-4, parallel).
- If a tool call fails twice, switch approach and explain why.
- When done, output a concise summary with file paths. No iteration limit: keep working until the task is fully complete.`,
  },
  dsk: {
    label: "DSK (K3)",
    system: `You are a fast-iteration coding agent (K3 style).
Rules:
- Plan → Generate → Review → Refine. State your plan briefly before generating code.
- Prefer minimal runnable iterations; verify after each step.
- Read before edit; exact old_string matching.
- Efficiency: ONE batch_edit/batch_write call for several files; delegate independent subtasks to subagents (1-4, parallel).
- Every 5 iterations review the original goal and stop if it is complete.
- Output a concise summary when done. No iteration limit: keep working until the task is fully complete.`,
  },
  dsq: {
    label: "DSQ (Qwen3.8)",
    system: `You are a collaborative coding agent (Qwen3.8 style).
Rules:
- For any non-trivial task FIRST call todo_write to break it into subtasks; mark in_progress/completed.
- Mirror the existing project style: read similar files first, then write consistent code.
- Prefer complete runnable code over partial snippets. Chinese answers are welcome.
- Read before edit.
- Efficiency: ONE batch_edit/batch_write call for several files; delegate independent subtasks to subagents (1-4, parallel).
- No iteration limit: keep working until the task is fully complete.`,
  },
  dsg: {
    label: "DSG (GLM5.3)",
    system: `You are a global-view coding agent (GLM5.3 style).
Rules:
- For unfamiliar codebases call glob + grep first.
- Check usages with grep before editing shared functions.
- Be concise: show code first, reasoning only when asked.
- Read before edit; handle edge cases explicitly.
- Efficiency: ONE batch_edit/batch_write call for several files; delegate independent subtasks to subagents (1-4, parallel).
- No iteration limit: keep working until the task is fully complete.`,
  },
};

/* ───────── 工具 Schema（对标 DeepKing 15 工具） ───────── */
const TOOL_SCHEMAS = [
  tool("read", "Read a file from the workspace. Returns lines with numbers. Use offset/limit for large files.", {
    type: "object", properties: { file_path: { type: "string" }, offset: { type: "integer" }, limit: { type: "integer" } }, required: ["file_path"],
  }),
  tool("write", "Create or overwrite a file. content up to 60000 chars — prefer writing the WHOLE file in one call (no chunking).", {
    type: "object", properties: { file_path: { type: "string" }, content: { type: "string" } }, required: ["file_path", "content"],
  }),
  tool("edit", "Edit a file by replacing an exact string (old_string). MUST read the file first.", {
    type: "object", properties: { file_path: { type: "string" }, old_string: { type: "string" }, new_string: { type: "string" }, replace_all: { type: "boolean" } }, required: ["file_path", "old_string", "new_string"],
  }),
  tool("batch_write", "Write MULTIPLE files in ONE call (array of {file_path, content}, each content up to 60000 chars). Use for creating/overwriting several files at once.", {
    type: "object", properties: { files: { type: "array", items: { type: "object", properties: { file_path: { type: "string" }, content: { type: "string" } }, required: ["file_path", "content"] } } }, required: ["files"],
  }),
  tool("batch_edit", "Apply MULTIPLE exact-string edits ACROSS MULTIPLE FILES in ONE call (array of {file_path, old_string, new_string, replace_all}). Prefer this over many separate edit calls.", {
    type: "object", properties: { edits: { type: "array", items: { type: "object", properties: { file_path: { type: "string" }, old_string: { type: "string" }, new_string: { type: "string" }, replace_all: { type: "boolean" } }, required: ["file_path", "old_string", "new_string"] } } }, required: ["edits"],
  }),
  tool("subagents", "Run 1-4 INDEPENDENT sub-agent tasks IN PARALLEL. Each sub-agent has a fresh context and the full tool set (read/edit/bash/grep/batch_edit...), runs up to 40 rounds, and returns its conclusion. Use for parallel investigation/fixing of independent files or modules: ONE call replaces many sequential calls. Result is a per-task summary.", {
    type: "object", properties: { tasks: { type: "array", minItems: 1, maxItems: 4, items: { type: "object", properties: { id: { type: "string" }, instruction: { type: "string" } }, required: ["id", "instruction"] } } }, required: ["tasks"],
  }),
  tool("delete", "Delete a file (or empty folder). Use with caution.", {
    type: "object", properties: { file_path: { type: "string" } }, required: ["file_path"],
  }),
  tool("bash", "Execute a shell command in the workspace root (Windows: cmd /C). Returns stdout+stderr and exit code.", {
    type: "object", properties: { command: { type: "string" }, timeout_ms: { type: "integer" } }, required: ["command"],
  }),
  tool("grep", "Recursively search files by regular expression.", {
    type: "object", properties: { pattern: { type: "string" }, path: { type: "string" }, include_glob: { type: "string" } }, required: ["pattern"],
  }),
  tool("glob", "List files matching a glob (e.g. **/*.py, src/**/*.ts).", {
    type: "object", properties: { pattern: { type: "string" }, path: { type: "string" } }, required: ["pattern"],
  }),
  tool("todo_write", "Maintain a task list for the current goal.", {
    type: "object", properties: { todos: { type: "array", items: { type: "object", properties: { content: { type: "string" }, status: { type: "string", enum: ["pending", "in_progress", "completed"] } }, required: ["content"] } } }, required: ["todos"],
  }),
  tool("task", "Decompose the current task into ordered subtasks.", {
    type: "object", properties: { title: { type: "string" }, tasks: { type: "array", items: { type: "string" } } }, required: ["title"],
  }),
  tool("check_runtime", "Check whether a runtime (python/node/java/gcc) is available.", {
    type: "object", properties: { name: { type: "string" } }, required: ["name"],
  }),
  tool("read_image", "Analyze an image with the vision engine (ModLens/DeepSeek-OCR) and return structured text evidence.", {
    type: "object", properties: { image_path: { type: "string" } }, required: ["image_path"],
  }),
  tool("read_pdf", "Extract text from a PDF using Python pymupdf (fitz).", {
    type: "object", properties: { file_path: { type: "string" } }, required: ["file_path"],
  }),
  tool("read_excel", "Extract an Excel sheet as Markdown table using Python pandas (if installed).", {
    type: "object", properties: { file_path: { type: "string" }, sheet: { type: "string" } }, required: ["file_path"],
  }),
  tool("web_search", "Search the web with DuckDuckGo (lightweight, no API key). Returns top results title+snippet+url.", {
    type: "object", properties: { query: { type: "string" }, max_results: { type: "integer" } }, required: ["query"],
  }),
  tool("install_python_package", "Install a Python package via pip into the default environment.", {
    type: "object", properties: { package: { type: "string" } }, required: ["package"],
  }),
  tool("check_python_package", "Check whether a Python package is importable (returns version if possible).", {
    type: "object", properties: { package: { type: "string" } }, required: ["package"],
  }),
];
function tool(name, description, parameters) { return { type: "function", function: { name, description, parameters } }; }

/* ───────── 工具执行 ───────── */
function resolvePath(workdir, p) { return path.isAbsolute(p) ? p : path.join(workdir, p); }
function truncate(s, n) { s = String(s || ""); return s.length > n ? s.slice(0, n) + `... [truncated, ${s.length} total chars]` : s; }
/* API Key 必然是纯 ASCII 无空白字符串；粘贴时常混入全角/不换行空格、换行或中文，先清洗再使用 */
function cleanApiKey(k) {
  return String(k || "").replace(/\s+/g, "").replace(/[^\x21-\x7E]/g, "");
}

function execTool(workdir, name, args, ctx) {
  try {
    if (name === "read") return toolRead(workdir, args);
    if (name === "write") return toolWrite(workdir, args);
    if (name === "edit") return toolEdit(workdir, args);
    if (name === "delete") return toolDelete(workdir, args);
    if (name === "glob") return toolGlob(workdir, args);
    if (name === "grep") return toolGrep(workdir, args);
    if (name === "todo_write" || name === "task") return { success: true, output: `[${name}] 任务列表已更新`, data: { ok: true } };
    if (name === "check_runtime") return toolCheckRuntime(args);
    if (name === "read_image") return toolReadImage(workdir, args, ctx && ctx.vision);
    if (name === "read_pdf") return toolReadPdf(workdir, args);
    if (name === "read_excel") return toolReadExcel(workdir, args);
    if (name === "web_search") return toolWebSearch(args);
    if (name === "install_python_package") return toolInstallPackage(workdir, args);
    if (name === "check_python_package") return toolCheckPythonPackage(workdir, args);
    if (name === "batch_write") return toolBatchWrite(workdir, args, ctx);
    if (name === "batch_edit") return toolBatchEdit(workdir, args, ctx);
    if (name === "bash") return { success: false, output: "bash 走异步 runBash", data: null };
    return { success: false, output: `Unknown tool: ${name}`, data: null };
  } catch (e) {
    return { success: false, output: `工具执行错误: ${e.message}`, data: null };
  }
}

function toolRead(workdir, args) {
  const full = resolvePath(workdir, args.file_path || "");
  if (!fs.existsSync(full)) return { success: false, output: `读取失败: 文件不存在 ${args.file_path}`, data: null };
  const lines = fs.readFileSync(full, "utf8").replace(/^\uFEFF/, "").split(/\r?\n/);
  const start = Math.max(0, args.offset || 0);
  const end = Math.min(lines.length, start + (args.limit || 200));
  return { success: true, output: `File: ${args.file_path}\nLines ${start + 1}-${end} of ${lines.length}\n\n${lines.slice(start, end).map((l, i) => `${String(start + i + 1).padStart(6)}\t${l}`).join("\n")}`, data: { total_lines: lines.length } };
}
function toolWrite(workdir, args) {
  const full = resolvePath(workdir, args.file_path || "");
  fs.mkdirSync(path.dirname(full), { recursive: true });
  fs.writeFileSync(full, args.content || "", "utf8");
  return { success: true, output: `Wrote ${Buffer.byteLength(args.content || "")} chars to ${args.file_path}`, data: { bytes_written: Buffer.byteLength(args.content || "") } };
}
function toolEdit(workdir, args) {
  const full = resolvePath(workdir, args.file_path || "");
  if (!fs.existsSync(full)) return { success: false, output: `编辑失败: 文件不存在 ${args.file_path}`, data: null };
  const content = fs.readFileSync(full, "utf8");
  const oldString = args.old_string || "";
  if (!content.includes(oldString)) return { success: false, output: `old_string 未在 ${args.file_path} 中找到，请先 read 获取精确内容`, data: null };
  const count = content.split(oldString).length - 1;
  if (!args.replace_all && count > 1) return { success: false, output: `old_string 出现 ${count} 次，请设置 replace_all=true 或提供更多上下文`, data: null };
  const next = args.replace_all ? content.split(oldString).join(args.new_string || "") : content.replace(oldString, args.new_string || "");
  fs.writeFileSync(full, next, "utf8");
  return { success: true, output: `Replaced ${args.replace_all ? count : 1} occurrence(s) in ${args.file_path}`, data: { replacements: args.replace_all ? count : 1 } };
}
function toolDelete(workdir, args) {
  const full = resolvePath(workdir, args.file_path || "");
  if (!fs.existsSync(full)) return { success: false, output: `删除失败: 不存在 ${args.file_path}`, data: null };
  fs.rmSync(full, { recursive: true, force: true });
  return { success: true, output: `已删除 ${args.file_path}`, data: { deleted: true } };
}
function compileGlob(pat) {
  let reg = "", i = 0;
  while (i < pat.length) {
    const c = pat[i];
    if (c === "*" && pat[i + 1] === "*") { reg += ".*"; i += 2; continue; }
    if (c === "*") { reg += "[^\\/]*"; i++; continue; }
    if (c === "?") { reg += "[^\\/]"; i++; continue; }
    if ("^$()+[]{}|\\.".includes(c)) { reg += "\\" + c; i++; continue; }
    reg += c; i++;
  }
  return new RegExp("^" + reg + "$");
}
function toolGlob(workdir, args) {
  const base = path.isAbsolute(args.path || "") ? args.path : path.join(workdir, args.path || ".");
  const re = compileGlob((args.pattern || "**/*").replace(/\\/g, "/"));
  const out = [];
  const SKIP = new Set(["node_modules", ".git", "target", "dist", ".venv", "venv", "__pycache__", ".idea", ".vscode", ".trae", ".trae-cn", ".cursor"]);
  (function walk(dir, rel) {
    let entries; try { entries = fs.readdirSync(dir, { withFileTypes: true }); } catch { return; }
    for (const e of entries) {
      if (SKIP.has(e.name)) continue;
      const r = rel ? rel + "/" + e.name : e.name;
      if (e.isDirectory()) walk(path.join(dir, e.name), r);
      else if (re.test(r) && !/\.(exe|dll|so|dylib|bin|png|jpg|jpeg|gif|ico|webp|db|pyc)$/i.test(e.name)) out.push(r);
    }
  })(base, "");
  return { success: true, output: out.slice(0, 200).join("\n") || "(无匹配)", data: { count: out.length } };
}
function toolGrep(workdir, args) {
  const base = path.isAbsolute(args.path || "") ? args.path : path.join(workdir, args.path || ".");
  let re; try { re = new RegExp(args.pattern || "", "i"); } catch (e) { return { success: false, output: `正则无效: ${e.message}`, data: null }; }
  const out = [];
  const SKIP = new Set(["node_modules", ".git", "target", "dist", ".venv", "venv", "__pycache__", ".idea", ".trae", ".trae-cn", ".cursor"]);
  let scanned = 0;
  (function walk(dir) {
    let entries; try { entries = fs.readdirSync(dir, { withFileTypes: true }); } catch { return; }
    for (const e of entries) {
      if (SKIP.has(e.name)) continue;
      const p = path.join(dir, e.name);
      if (e.isDirectory()) { walk(p); continue; }
      if (/\.(exe|dll|so|bin|png|jpg|jpeg|gif|ico|webp|db|pyc)$/i.test(e.name)) continue;
      scanned++;
      if (out.length >= 200) continue;
      let lines; try { lines = fs.readFileSync(p, "utf8").split(/\r?\n/); } catch { continue; }
      for (let i = 0; i < lines.length && out.length < 200; i++) {
        if (re.test(lines[i])) out.push(`${path.relative(workdir, p).replace(/\\/g, "/")}:${i + 1}: ${lines[i].trim().slice(0, 180)}`);
      }
    }
  })(base);
  return { success: true, output: out.length ? out.join("\n") : `(无匹配，已扫描 ${scanned} 个文件)`, data: { scanned } };
}
function toolCheckRuntime(args) {
  const cmd = (args.name || "").toLowerCase();
  const bin = { python: ["py", "-3", "--version"], node: ["node", "--version"], java: ["java", "-version"], gcc: ["gcc", "--version"] }[cmd];
  if (!bin) return { success: false, output: `未知运行时: ${args.name}`, data: null };
  return new Promise((resolve) => {
    execFile(bin[0], bin.slice(1), { timeout: 5000, windowsHide: true }, (err, stdout, stderr) => {
      resolve({ success: !err, output: err ? `[exit ${err.code ?? -1}] ${String(err.stderr || err.message).slice(0, 200)}` : String(stdout || stderr).trim(), data: { available: !err } });
    });
  });
}
function toolCheckPythonPackage(workdir, args) {
  const pkg = String(args.package || "").trim();
  if (!/^[A-Za-z0-9][A-Za-z0-9._-]*$/.test(pkg)) return { success: false, output: `包名不合法（仅允许字母/数字/._-）: ${pkg}`, data: null };
  const script = `import sys\nimport importlib\ntry:\n m=importlib.import_module(sys.argv[1])\n print(getattr(m,'__version__','installed'))\nexcept Exception as e:\n print('ERROR:',e,file=sys.stderr)\n sys.exit(1)\n`;
  return runPython(workdir, script, 30000, [pkg]);
}
function toolInstallPackage(workdir, args) {
  const pkg = String(args.package || "").trim();
  if (!/^[A-Za-z0-9][A-Za-z0-9._-]*$/.test(pkg)) return { success: false, output: `拒绝安装：包名不合法（仅允许字母/数字/._-，禁止 shell 元字符）: ${pkg}`, data: { exit_code: -1 } };
  return runBash(workdir, `python -m pip install -q ${pkg}`, 120000).then((r) => ({ success: r.success, output: truncate(r.output, 2000), data: r.data }));
}
/* ───────── 批量多文件写/改（一次调用 = 多个文件，大幅减少主循环步数） ───────── */
function toolBatchWrite(workdir, args, ctx) {
  const files = Array.isArray((args || {}).files) ? args.files : [];
  if (!files.length) return { success: false, output: "files 为空（需要 [{file_path, content}]）", data: null };
  const report = [];
  let ok = 0;
  for (const f of files) {
    const full = resolvePath(workdir, (f && f.file_path) || "");
    if (!full) { report.push("❌ file_path 为空"); continue; }
    try {
      if (ctx && ctx.onUndo) recordUndo(workdir, "write", f, ctx.onUndo);
      fs.mkdirSync(path.dirname(full), { recursive: true });
      fs.writeFileSync(full, (f && f.content) || "", "utf8");
      ok++;
      report.push(`✅ ${f.file_path}（${Buffer.byteLength(String((f && f.content) || ""))} chars）`);
    } catch (e) { report.push(`❌ ${f.file_path}: ${e.message}`); }
  }
  return { success: ok === files.length, output: `批量写入 ${ok}/${files.length}\n` + report.join("\n"), data: { written: ok } };
}
function toolBatchEdit(workdir, args, ctx) {
  const edits = Array.isArray((args || {}).edits) ? args.edits : [];
  if (!edits.length) return { success: false, output: "edits 为空（需要 [{file_path, old_string, new_string}]）", data: null };
  const report = [];
  let ok = 0;
  for (const e of edits) {
    const full = resolvePath(workdir, (e && e.file_path) || "");
    if (!fs.existsSync(full)) { report.push(`❌ ${e.file_path}: 文件不存在`); continue; }
    let content; try { content = fs.readFileSync(full, "utf8"); } catch (ex) { report.push(`❌ ${e.file_path}: ${ex.message}`); continue; }
    const oldString = (e && e.old_string) || "";
    if (!oldString || !content.includes(oldString)) { report.push(`❌ ${e.file_path}: old_string 未找到（请先 read 获取精确内容）`); continue; }
    const count = content.split(oldString).length - 1;
    if (!e.replace_all && count > 1) { report.push(`❌ ${e.file_path}: old_string 出现 ${count} 次，请设置 replace_all=true 或提供更多上下文`); continue; }
    try {
      if (ctx && ctx.onUndo) recordUndo(workdir, "edit", e, ctx.onUndo);
      const next = e.replace_all ? content.split(oldString).join(e.new_string || "") : content.replace(oldString, e.new_string || "");
      fs.writeFileSync(full, next, "utf8");
      ok++;
      report.push(`✅ ${e.file_path}（${e.replace_all ? count : 1} 处）`);
    } catch (ex) { report.push(`❌ ${e.file_path}: ${ex.message}`); }
  }
  return { success: ok === edits.length, output: `批量编辑 ${ok}/${edits.length}\n` + report.join("\n"), data: { edited: ok } };
}
/* ───────── 并行子智能体：独立上下文 + 全套工具并发执行，结论汇总回主循环 ───────── */
async function toolSubagents(config, mode, workdir, args, onEvent, vision, onUndo, runId) {
  const tasks = Array.isArray((args || {}).tasks) ? args.tasks.filter((t) => t && t.instruction).slice(0, 4) : [];
  if (!tasks.length) return { success: false, output: "tasks 为空（需要 [{id, instruction}]，最多 4 个）", data: null };
  const runOne = (t) => {
    const subId = `s${Date.now()}_${Math.floor(Math.random() * 1e6)}`;
    const silent = () => {}; // 子智能体事件不直接上屏；其结论通过工具结果回传给主模型
    return runAgentLoop(config, mode || "dsh", String(t.instruction || ""), [], workdir, silent, vision, onUndo, subId, { maxIter: 40 })
      .then((r) => ({ id: t.id || "task", content: (r && r.content) || "", error: (r && r.error) || null }));
  };
  const results = await Promise.all(tasks.map(runOne));
  const lines = results.map((r) => `## ${r.id}${r.error ? "（出错）" : ""}\n${r.error ? "ERROR: " + r.error : (r.content || "（空结果）")}`);
  return { success: results.every((r) => !r.error), output: `✅ 子智能体完成 ${results.filter((r) => !r.error).length}/${tasks.length}\n\n` + lines.join("\n\n"), data: { tasks: results.length } };
}
function toolReadImage(workdir, args, visionCfg) {
  if (!visionCfg || !visionCfg.apiKey) return { success: false, output: "视觉引擎未配置（设置 → 视觉识别填写 API Key）", data: null };
  return analyzeImage(visionCfg, resolvePath(workdir, args.image_path || ""), null)
    .then((text) => ({ success: true, output: truncate(text, 4000), data: { provider: visionCfg.provider } }))
    .catch((e) => ({ success: false, output: "视觉识别失败: " + e.message, data: null }));
}
function toolReadPdf(workdir, args) {
  const full = resolvePath(workdir, args.file_path || "");
  const script = `import sys\nimport fitz\ntry:\n doc=fitz.open(sys.argv[1])\n print('\\n'.join(p.get_text() for p in doc))\nexcept Exception as e:\n print('ERROR:',e,file=sys.stderr)\n sys.exit(1)\n`;
  return runPython(workdir, script, 60000, [full]);
}
function toolReadExcel(workdir, args) {
  const full = resolvePath(workdir, args.file_path || "");
  const sheet = (args.sheet || "0").replace(/'/g, "");
  const script = `import sys\nimport pandas as pd\ntry:\n _sn=sys.argv[2] if len(sys.argv)>2 else "0"\n df=pd.read_excel(sys.argv[1],sheet_name=(0 if _sn=="0" else _sn))\n print(df.to_markdown(index=False))\nexcept ImportError as e:\n print('ERROR: 需要 pandas/openpyxl，请先 pip install pandas openpyxl', file=sys.stderr); sys.exit(2)\nexcept Exception as e:\n print('ERROR:',e,file=sys.stderr); sys.exit(1)\n`;
  return runPython(workdir, script, 60000, [full, sheet]);
}
function runPython(workdir, script, timeoutMs, extraArgs) {
  return new Promise((resolve) => {
    const tryRun = (py, attempt) => execFile(py, ["-c", script, ...(extraArgs || [])], { cwd: workdir, timeout: timeoutMs || 60000, maxBuffer: 8 * 1024 * 1024, windowsHide: true }, (err, stdout, stderr) => {
      const code = err ? (typeof err.code === "number" ? err.code : -1) : 0;
      const text = String(stdout || "") + (stderr ? "\n[stderr]\n" + stderr : "");
      if ((code === 9009 || code === -1) && attempt < 2) return tryRun("python", attempt + 1);
      resolve({ success: code === 0, output: truncate(`[exit ${code}]\n${text}`, 6000), data: { exit_code: code } });
    });
    tryRun(process.platform === "win32" ? "py" : "python3", 0);
  });
}
function toolWebSearch(args) {
  const q = encodeURIComponent(args.query || "");
  const max = Math.min(10, args.max_results || 5);
  return new Promise((resolve) => {
    const ctrl = new AbortController();
    const timer = setTimeout(() => ctrl.abort(), 15000);
    fetch(`https://html.duckduckgo.com/html/?q=${q}`, { headers: { "User-Agent": "Mozilla/5.0" }, signal: ctrl.signal })
      .then((r) => r.text())
      .then((html) => {
        clearTimeout(timer);
        const items = [];
        const re = /<a[^>]*class="result__a"[^>]*href="([^"]+)"[^>]*>([\s\S]*?)<\/a>[\s\S]*?class="result__snippet"[^>]*>([\s\S]*?)<\/a>/g;
        let m;
        while ((m = re.exec(html)) && items.length < max) {
          const url = m[1].replace(/&amp;/g, "&");
          const title = m[2].replace(/<[^>]+>/g, "").trim();
          const snippet = m[3].replace(/<[^>]+>/g, "").trim();
          items.push(`- ${title}\n  ${snippet}\n  ${url}`);
        }
        resolve({ success: items.length > 0, output: items.length ? items.join("\n\n") : "(无结果，DuckDuckGo 可能返回了验证页)", data: { count: items.length } });
      })
      .catch((e) => { clearTimeout(timer); resolve({ success: false, output: "搜索失败: " + e.message, data: null }); });
  });
}

const DANGEROUS = ["rm -rf /", "del /f /s /q C:", "format ", ":(){:|:&};:"];
function runBash(workdir, command, timeoutMs) {
  return new Promise((resolve) => {
    for (const p of DANGEROUS) if (command.includes(p)) return resolve({ success: false, output: `BLOCKED: 危险命令模式 (${p})`, data: { exit_code: -1 } });
    const isWin = process.platform === "win32";
    const args = isWin ? ["/D", "/S", "/C", `set PYTHONIOENCODING=utf-8&& ${command}`] : ["-c", command];
    execFile(isWin ? "cmd" : "sh", args, { cwd: workdir, maxBuffer: 8 * 1024 * 1024, timeout: timeoutMs || 30000, windowsHide: true }, (err, stdout, stderr) => {
      const code = err ? (typeof err.code === "number" ? err.code : -1) : 0;
      const combined = stderr ? `${stdout}\n[stderr]\n${stderr}` : `${stdout}`;
      resolve({ success: code === 0, output: truncate(`[exit ${code}]\n${combined}`, 20000), data: { exit_code: code } });
    });
  });
}

/* ───────── 多模态视觉（移植自 DeepKing vision.rs：ModLens / DeepSeek-OCR） ───────── */
const VISION_DEFAULT_PROMPT = {
  modlens: "请识别这张图片并返回结构化 JSON 证据，包含：ocr（图中全部文字）、layout（版面/区域描述）、semantics(图片语义、场景、意图)。若图片是报错截图或 UI 设计稿，请在 semantics 中重点描述。",
  "deepseek-ocr": "请对这张图片做高质量的文档 OCR：提取其中的全部文字、公式、表格，并尽量保留版面结构。表格用 Markdown 表格呈现，公式保留 LaTeX。",
};
function guessMime(p) { const e = path.extname(p).toLowerCase(); return { ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".gif": "image/gif", ".webp": "image/webp", ".bmp": "image/bmp" }[e] || "image/png"; }
async function analyzeImage(vision, imagePath, prompt) {
  if (!vision || !vision.apiKey) throw new Error("Vision API Key not configured.");
  const vKey = cleanApiKey(vision.apiKey);
  if (!vKey) throw new Error("Vision API Key 无效（为空或仅含空白/非 ASCII 字符），请在设置中重新粘贴。");
  const b64 = fs.readFileSync(imagePath).toString("base64");
  const dataUrl = `data:${guessMime(imagePath)};base64,${b64}`;
  const provider = vision.provider === "deepseek-ocr" ? "deepseek-ocr" : "modlens";
  const system = provider === "deepseek-ocr"
    ? "You are a precise document OCR engine. Return only extraction results with layout preserved."
    : "You are ModLens, a vision engine that turns images into structured text evidence for a text-only LLM.";
  const hint = provider === "deepseek-ocr" ? "输出 Markdown，保留标题层级与表格结构。" : "输出一个 JSON 对象：{ \"ocr\": string, \"layout\": string, \"semantics\": string }。";
  const body = {
    model: vision.model || "gpt-4o-mini",
    max_tokens: 4096,
    temperature: 0.2,
    messages: [
      { role: "system", content: system },
      { role: "user", content: [{ type: "text", text: `${prompt || VISION_DEFAULT_PROMPT[provider]}\n\n${hint}` }, { type: "image_url", image_url: { url: dataUrl } }] },
    ],
  };
  const url = `${(vision.baseUrl || "https://api.openai.com/v1").replace(/\/$/, "")}/chat/completions`;
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), 180000);
  try {
    const resp = await fetch(url, { method: "POST", headers: { "Authorization": `Bearer ${vKey}`, "Content-Type": "application/json" }, body: JSON.stringify(body), signal: ctrl.signal });
    if (!resp.ok) throw new Error(`Vision API error (${resp.status}): ${(await resp.text().catch(() => "")).slice(0, 300)}`);
    const json = await resp.json();
    const text = ((json.choices && json.choices[0] && json.choices[0].message && json.choices[0].message.content) || "").trim();
    if (!text) throw new Error("Vision model returned empty result.");
    return text;
  } finally { clearTimeout(timer); }
}
function saveTempImage(dataUrl, ext, workdir) {
  const b64 = String(dataUrl || "").split(",").pop() || "";
  const bytes = Buffer.from(b64, "base64");
  if (!bytes.length) throw new Error("图片数据无效");
  const dir = path.join(workdir, ".deepking-paste");
  fs.mkdirSync(dir, { recursive: true });
  const p = path.join(dir, `img_${Date.now()}.${(ext || "png").replace(/^\./, "")}`);
  fs.writeFileSync(p, bytes);
  return p;
}

/* ───────── DeepSeek 客户端 ───────── */
function normalizeCall(call) {
  let args = call.function.arguments;
  if (typeof args === "string") { try { args = JSON.parse(args); } catch { args = {}; } }
  return { id: call.id, name: call.function.name, arguments: args };
}
async function deepseekChat(config, system, messages, tools, dbg) {
  const apiKey = cleanApiKey(config.apiKey);
  if (!apiKey) return { ok: false, error: "API Key 无效：为空或仅含空白/非 ASCII 字符（可能粘贴了错误内容）。请在设置中清空后，重新粘贴 sk- 开头的 DeepSeek API Key。" };
  const body = { model: config.model || "deepseek-chat", messages: [{ role: "system", content: system }, ...messages], stream: false, max_tokens: 16384, temperature: 0.7 };
  // 对齐官方 Tool Calls 指南：不传 tool_choice（默认即 auto），tools 仅在有工具时携带
  if (tools && tools.length) body.tools = tools;
  const url = `${(config.baseUrl || "https://api.deepseek.com").replace(/\/$/, "")}/v1/chat/completions`;
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), 300000);
  // 调试记录：请求/响应落盘（不含 API Key），出错时给出路径
  const dbgDir = dbg && dbg.workdir ? path.join(dbg.workdir, ".deepking-debug") : null;
  const dbgWrite = (name, data) => { if (!dbgDir) return; try { fs.mkdirSync(dbgDir, { recursive: true }); fs.writeFileSync(path.join(dbgDir, name), JSON.stringify(data, null, 2), "utf8"); } catch (_) {} };
  try {
    if (dbgDir) dbgWrite(`req-${Date.now()}.json`, { url, model: body.model, tools: body.tools ? body.tools.length : 0, messages: body.messages.map((m) => ({ role: m.role, content: (m.content || "").slice(0, 200), reasoning_content: m.reasoning_content !== undefined ? String(m.reasoning_content).slice(0, 80) : undefined, tool_calls: m.tool_calls ? m.tool_calls.length : 0 })) });
    const resp = await fetch(url, { method: "POST", headers: { "Authorization": `Bearer ${apiKey}`, "Content-Type": "application/json" }, body: JSON.stringify(body), signal: ctrl.signal });
    const respText = await resp.text().catch(() => "");
    if (dbgDir) dbgWrite(`resp-${Date.now()}.json`, { status: resp.status, body: respText.slice(0, 200000) });
    if (!resp.ok) return { ok: false, error: `API error (${resp.status}): ${respText.slice(0, 400)}${dbgDir ? `（详见 ${dbgDir}）` : ""}` };
    return { ok: true, data: JSON.parse(respText) };
  } catch (e) { if (dbgDir) dbgWrite(`err-${Date.now()}.json`, { error: String(e && e.message || e) }); return { ok: false, error: `Network error: ${e.message}${dbgDir ? `（详见 ${dbgDir}）` : ""}` }; }
  finally { clearTimeout(timer); }
}

/* ───────── 上下文自动压缩（移植自 DeepKing context.rs） ───────── */
const CTX_MAX_TOKENS = 6000, CTX_THRESHOLD = 0.7, PRESERVE_TURNS = 8;
function estimateTokens(text) { return Math.ceil(String(text || "").length / 2.5); }
function compressHistory(history) {
  const total = history.reduce((s, m) => s + estimateTokens(m.content), 0);
  if (total <= CTX_MAX_TOKENS * CTX_THRESHOLD) return { history, compressed: false, before: total, after: total };
  if (history.length <= PRESERVE_TURNS) return { history, compressed: false, before: total, after: total };
  const early = history.slice(0, history.length - PRESERVE_TURNS);
  const keep = history.slice(history.length - PRESERVE_TURNS);
  const summary = early.map((m) => `- ${m.role}: ${String(m.content || "").replace(/\s+/g, " ").slice(0, 140)}`).join("\n");
  const summaryMsg = { role: "user", content: `[对话摘要 — 早期 ${early.length} 条消息已被自动压缩]\n${summary}` };
  const after = estimateTokens(summaryMsg.content) + keep.reduce((s, m) => s + estimateTokens(m.content), 0);
  return { history: [summaryMsg, ...keep], compressed: true, before: total, after };
}

/* ───────── 循环内增量压缩（防止 messages 无限膨胀顶爆上下文窗口） ───────── */
const LOOP_TOKEN_CAP = 36000;   // 循环内估算超过该值触发压缩
const LOOP_KEEP_BUDGET = 22000; // 压缩后保留最近约多少 tokens（含最近工具结果）
function compactInLoop(messages, keepBudget) {
  const total = messages.reduce((s, m) => s + estimateTokens(String(m.content || "")), 0);
  if (total <= LOOP_TOKEN_CAP) return null;
  // 从后往前找最靠前的 user/assistant 边界，使"保留后缀"不超过预算；
  // 只能切在 user/assistant 前，保证被保留侧的 tool 结果（role=tool）链完整。
  let tail = 0, cut = -1;
  for (let i = messages.length - 1; i >= 0; i--) {
    tail += estimateTokens(String(messages[i].content || ""));
    if (tail > keepBudget) break;
    if (messages[i].role === "user" || messages[i].role === "assistant") cut = i;
  }
  if (cut <= 0 || messages.slice(0, cut).length < 4) return null;
  const early = messages.slice(0, cut);
  const keep = messages.slice(cut);
  const summaryLines = early.map((m) => {
    let c;
    if (m.role === "tool") c = String(m.content || "").replace(/\s+/g, " ").slice(0, 100) || "(结果已省略)";
    else if (m.role === "assistant") c = String(m.content || "").replace(/\s+/g, " ").slice(0, 100) || (m.tool_calls && m.tool_calls.length ? `[调用 ${m.tool_calls.length} 个工具]` : "(空)");
    else c = String(m.content || "").replace(/\s+/g, " ").slice(0, 100);
    return `- ${m.role}${m.role === "tool" ? `(${m.name || ""})` : ""}: ${c}`;
  }).filter(Boolean).join("\n");
  const summaryMsg = { role: "system", content: `[对话摘要 — 早期 ${early.length} 条消息已被自动压缩]\n${summaryLines}` };
  return { messages: [summaryMsg, ...keep], before: total, after: estimateTokens(summaryMsg.content) + tail };
}

/* ───────── DSML 工具调用解析（DeepSeek 推理模型有时把 tool_calls 写成 DSML 纯文本） ───────── */
/* DeepSeek 的 DSML 标签形如 <｜｜DSML｜｜tool_calls>（全角竖线 U+FF5C 包裹 DSML 标记），
 * 归一化为 <tool_calls> 后再用常规正则解析 */
const DSML_PREFIX = "｜｜DSML｜｜";
function hasDSMLToolCalls(text) {
  const t = String(text || "").replace(/\uFF5C/g, "");
  return /<(?:DSML)?tool_calls>/.test(t) || /<tool_calls>/.test(t) || /<tool_calls[\s\S]*?>/.test(t);
}
function parseDSMLToolCalls(text) {
  const out = [];
  if (!text) return out;
  text = String(text).split(DSML_PREFIX).join("");
  /* 真实 DSML 格式为 <｜DSML｜tag>（竖线+DSML 关键字+标签名），去掉竖线后是 <DSMLtag>；
   * 所有标签正则都必须容忍可选 DSML 关键字，否则解析永远落空 */
  if (!/<(?:DSML)?tool_calls>/.test(text)) return out;
  const blocks = text.match(/<(?:DSML)?tool_calls>[\s\S]*?<\/(?:DSML)?tool_calls>/g) || [];
  for (const block of blocks) {
    const invokes = block.match(/<(?:DSML)?invoke\s+name="([^"]+)"[^>]*>[\s\S]*?<\/(?:DSML)?invoke>/g) || [];
    for (const inv of invokes) {
      const name = (inv.match(/<(?:DSML)?invoke\s+name="([^"]+)"/) || [])[1] || "";
      if (!name) continue;
      const args = {};
      const params = inv.match(/<(?:DSML)?parameter\s+([^>]*)>([\s\S]*?)<\/(?:DSML)?parameter>/g) || [];
      for (const p of params) {
        const head = (p.match(/<(?:DSML)?parameter\s+([^>]*)>/) || [])[1] || "";
        const pname = (head.match(/name="([^"]+)"/) || [])[1] || "";
        if (!pname) continue;
        const isStr = /string="true"/.test(head);
        let val = (p.match(/>([\s\S]*?)<\/(?:DSML)?parameter>/) || [])[1] || "";
        if (!isStr) { try { val = JSON.parse(val); } catch (_) {} } else { val = String(val); }
        args[pname] = val;
      }
      out.push({ id: "dsml_" + out.length, name, arguments: args });
    }
  }
  return out;
}

/* ───────── 撤销/回滚（对标 DeepKing 撤回对话） ───────── */
function recordUndo(workdir, name, args, onUndo) {
  if (!onUndo) return;
  try {
    const full = resolvePath(workdir, args.file_path || "");
    if (!full) return;
    const existed = fs.existsSync(full);
    let original = null;
    if (existed) { try { original = fs.readFileSync(full, "utf8"); } catch (_) { original = null; } }
    onUndo({ path: full, existed, original, tool: name });
  } catch (_) {}
}
function applyUndo(entries) {
  let count = 0;
  for (const e of (entries || []).slice().reverse()) {
    try {
      if (e.existed && e.original != null) { fs.mkdirSync(path.dirname(e.path), { recursive: true }); fs.writeFileSync(e.path, e.original, "utf8"); count++; }
      else if (!e.existed) { fs.rmSync(e.path, { recursive: true, force: true }); count++; }
    } catch (_) {}
  }
  return count;
}

/* ───────── Agent Loop（agent_loop.rs；max/工具开关 + 压缩 + 撤销日志） ───────── */
async function runAgentLoop(config, mode, userMessage, history, workdir, onEvent, vision, onUndo, runId, opts) {
  const persona = MODES[mode] || MODES.dsh;
  const useTools = config.tools !== false && config.max !== false;
  /* 0 = 不设步数上限：循环只会在模型给出结论（不再调用工具）或出错时结束；上下文超阈值自动摘要压缩 */
  const maxIter = opts && opts.maxIter ? opts.maxIter : 0;
  const com = compressHistory(history.filter((m) => m.role !== "system"));
  let messages = com.history.map((m) => ({ role: m.role, content: m.content, reasoning_content: m.reasoning_content, tool_calls: m.tool_calls, tool_call_id: m.tool_call_id, name: m.name })).filter((m) => m.role !== "system");
  messages.push({ role: "user", content: userMessage });
  let finalContent = "", finalReasoning = "", toolCount = 0;
  onEvent({ type: "started", max_iterations: maxIter || null, use_tools: useTools, run_id: runId });
  if (com.compressed) onEvent({ type: "context_compressed", before_tokens: com.before, after_tokens: com.after });
  const schemas = useTools ? TOOL_SCHEMAS : null;
  for (let iter = 0; maxIter === 0 || iter < maxIter; iter++) {
    onEvent({ type: "iteration", current: iter + 1, max: maxIter || null });
    const resp = await deepseekChat(config, persona.system, messages, schemas, { workdir, runId });
    if (!resp.ok) { onEvent({ type: "error", message: resp.error }); return { error: resp.error }; }
    const choice = resp.data.choices && resp.data.choices[0];
    if (!choice) { onEvent({ type: "error", message: "无有效响应" }); return { error: "无有效响应" }; }
    const msg = choice.message || {};
    /* thinking 模式（deepseek-v4-pro 等）要求：assistant 消息的 reasoning_content 必须回传，否则 400 */
    if (msg.reasoning_content !== undefined) finalReasoning = String(msg.reasoning_content);
    let calls = msg.tool_calls || [];
    const rawText = String(msg.content || "");
    /* DeepSeek 推理模型有时把工具调用以 DSML 文本写在 content（而非结构化字段）：
     * 解析成可执行调用，避免把 DSML 原文当作结论展示 */
    let dsmlParsed = false;
    /* DSML 工具调用可能被模型写进 content 或 reasoning_content（思考模式行为不一致），两处都解析 */
    const dsmlSource = rawText + String(msg.reasoning_content || "");
    if (!calls.length && hasDSMLToolCalls(dsmlSource)) {
      const dsml = parseDSMLToolCalls(dsmlSource);
      if (dsml.length) { calls = dsml; dsmlParsed = true; }
    }
    finalContent = dsmlParsed ? "" : rawText;
    if (rawText && !dsmlParsed) onEvent({ type: "assistant_text", content: rawText });
    const apiCalls = (calls.length ? calls : []).map((c) => {
      const name = c.function ? c.function.name : c.name;
      const j = (v) => (typeof v === "string" ? v : JSON.stringify(v || {}));
      return { id: c.id, type: "function", function: { name, arguments: c.function ? j(c.function.arguments) : j(c.arguments) } };
    });
    messages.push({ role: "assistant", content: apiCalls.length ? null : (rawText || null), reasoning_content: msg.reasoning_content !== undefined ? String(msg.reasoning_content) : undefined, tool_calls: apiCalls.length ? apiCalls : undefined });
    if (!calls.length) { onEvent({ type: "done", content: finalContent, reasoning_content: finalReasoning || undefined, total_iterations: iter + 1, total_tool_calls: toolCount }); return { content: finalContent, reasoning_content: finalReasoning || undefined, iterations: iter + 1, tool_calls: toolCount }; }
    for (const raw of calls) {
      toolCount++;
      const call = raw.function ? normalizeCall(raw) : raw;
      onEvent({ type: "tool_call_requested", id: call.id, name: call.name, arguments: call.arguments });
      let result;
      if (call.name === "bash") result = await runBash(workdir, call.arguments.command || "", call.arguments.timeout_ms);
      else if (call.name === "subagents") result = await toolSubagents(config, mode, workdir, call.arguments, onEvent, vision, onUndo, runId);
      else {
        // 写入类工具执行前记录撤销日志（撤回对话时整体回退）
        if (["write", "edit", "delete"].includes(call.name)) recordUndo(workdir, call.name, call.arguments, onUndo);
        result = execTool(workdir, call.name, call.arguments, { vision, onUndo }); if (result instanceof Promise) result = await result;
      }
      const output = truncate(result.output || "", 3200);
      onEvent({ type: "tool_call_executed", id: call.id, name: call.name, success: result.success, output });
      messages.push({ role: "tool", tool_call_id: call.id, name: call.name, content: (result.success ? "" : "[ERROR] ") + output });
      if (/^(write|edit|delete|bash|batch_write|batch_edit|subagents)$/.test(call.name) && result.success) onEvent({ type: "file_changed", reason: call.name });
    }
    /* 每轮结束后检查：上下文超阈值就把早期轮次摘要压缩，保留最近内容 */
    const compacted = compactInLoop(messages, LOOP_KEEP_BUDGET);
    if (compacted) {
      messages = compacted.messages;
      onEvent({ type: "context_compressed", before_tokens: compacted.before, after_tokens: compacted.after, in_loop: true });
    }
  }
  /* 步数用尽：若模型全程在调用工具、始终没给出结论文字，追加一次"强制总结轮"
   *（不带工具，仅文字输出），避免出现"跑满步数却返回空内容"的假死现象 */
  if (!(finalContent && String(finalContent).trim())) {
    onEvent({ type: "iteration", current: maxIter + 1, max: maxIter + 1 });
    messages.push({
      role: "system",
      content: `工具调用轮次已达上限（${maxIter} 步），无法再调用工具。请基于对话中已经读取到的文件信息直接给出完整结论；若信息不足，请明确说明缺少什么，并给出获取这些信息的具体建议。不要调用任何工具，不要输出空内容。`,
    });
    let sumText = "";
    /* 总结轮若仍出现 DSML 工具调用文本：执行后最多再要 2 次总结（bounded） */
    for (let sRetry = 0; sRetry < 3; sRetry++) {
      const sum = await deepseekChat(config, persona.system, messages, null, { workdir, runId });
      if (!sum.ok) { onEvent({ type: "error", message: sum.error }); return { error: sum.error }; }
      const sm = sum.data.choices && sum.data.choices[0] ? (sum.data.choices[0].message || {}) : {};
      if (sm.reasoning_content !== undefined) finalReasoning = String(sm.reasoning_content);
      sumText = String(sm.content || "");
      const smDsml = sumText + String(sm.reasoning_content || "");
      if ((sm.tool_calls || []).length || !hasDSMLToolCalls(smDsml)) break;
      const dsml = parseDSMLToolCalls(smDsml);
      if (!dsml.length) break;
      messages.push({ role: "assistant", content: null, reasoning_content: sm.reasoning_content !== undefined ? String(sm.reasoning_content) : undefined, tool_calls: dsml.map((c) => ({ id: c.id, type: "function", function: { name: c.name, arguments: typeof c.arguments === "string" ? c.arguments : JSON.stringify(c.arguments) } })) });
      for (const raw of dsml) {
        toolCount++;
        const call = raw.function ? normalizeCall(raw) : raw;
        onEvent({ type: "tool_call_requested", id: call.id, name: call.name, arguments: call.arguments });
        let result;
        if (call.name === "bash") result = await runBash(workdir, call.arguments.command || "", call.arguments.timeout_ms);
        else if (call.name === "subagents") result = await toolSubagents(config, mode, workdir, call.arguments, onEvent, vision, onUndo, runId);
        else {
          if (["write", "edit", "delete"].includes(call.name)) recordUndo(workdir, call.name, call.arguments, onUndo);
          result = execTool(workdir, call.name, call.arguments, { vision, onUndo }); if (result instanceof Promise) result = await result;
        }
        const output = truncate(result.output || "", 3200);
        onEvent({ type: "tool_call_executed", id: call.id, name: call.name, success: result.success, output });
        messages.push({ role: "tool", tool_call_id: call.id, name: call.name, content: (result.success ? "" : "[ERROR] ") + output });
      }
    }
    finalContent = sumText;
    if (finalContent && !/<tool_calls>/.test(finalContent)) onEvent({ type: "assistant_text", content: finalContent });
  }
  onEvent({ type: "done", content: finalContent, reasoning_content: finalReasoning || undefined, total_iterations: maxIter, total_tool_calls: toolCount });
  return { content: finalContent, reasoning_content: finalReasoning || undefined, iterations: maxIter || 0, tool_calls: toolCount };
}

/* ───────── 多模态流程：识图 → 结合问题发送 ───────── */
async function handleMultimodal(config, vision, dataUrl, mime, prompt, workdir, onEvent, onUndo, runId) {
  if (!vision || !vision.apiKey) { onEvent({ type: "error", message: "未配置视觉引擎（设置 → 视觉识别：API Key/Base URL/模型）" }); return; }
  try {
    const imgPath = saveTempImage(dataUrl, mime, workdir);
    onEvent({ type: "started", max_iterations: 25, use_tools: config.tools !== false, run_id: runId });
    onEvent({ type: "assistant_text", content: "📷 正在识别图片…(ModLens/DeepSeek-OCR)\n" });
    const text = await analyzeImage(vision, imgPath, null);
    onEvent({ type: "assistant_text", content: `\n✅ 图片识别结果（${vision.provider || "modlens"}）：\n${text}\n\n` });
    const finalPrompt = (prompt && prompt.trim()) ? `${prompt.trim()}\n\n[用户粘贴了一张图片，以下是视觉识别结果，请结合回答]：\n${text}` : `用户粘贴了一张图片，以下是视觉识别结果，请描述并分析：\n${text}`;
    await runAgentLoop(config, config.mode || "dsh", finalPrompt, [], workdir, onEvent, vision, onUndo, runId);
  } catch (e) {
    onEvent({ type: "error", message: "识图失败: " + e.message });
  }
}

/* ───────── 服务模式（JetBrains / 浏览器） ───────── */
function startServer(port, ready) {
  const http = require("http");
  const MIME = { ".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8", ".css": "text/css; charset=utf-8", ".png": "image/png", ".ico": "image/x-icon" };
  const WEBVIEW = path.join(__dirname, "webview");
  const server = http.createServer((req, res) => {
    const cors = { "Access-Control-Allow-Origin": "*", "Access-Control-Allow-Headers": "Content-Type", "Access-Control-Allow-Methods": "POST,OPTIONS" };
    if (req.method === "OPTIONS") { res.writeHead(204, cors); return res.end(); }
    if (req.url === "/rpc") { return handleRpc(req, res, cors); }
    let p = decodeURIComponent((req.url || "/").split("?")[0]);
    if (p === "/") p = "/index.html";
    const file = path.normalize(path.join(WEBVIEW, p));
    if (!file.startsWith(path.normalize(WEBVIEW))) { res.writeHead(403, cors); return res.end("forbidden"); }
    if (!fs.existsSync(file) || fs.statSync(file).isDirectory()) { res.writeHead(404, cors); return res.end("not found"); }
    res.writeHead(200, { ...cors, "Content-Type": MIME[path.extname(file).toLowerCase()] || "application/octet-stream", "Cache-Control": "no-cache" });
    return res.end(fs.readFileSync(file));
  });
  server.listen(port, "127.0.0.1", () => ready(server.address().port));
  return server;
}
function handleRpc(req, res, cors) {
  let raw = "";
  req.on("data", (c) => (raw += c));
  req.on("end", () => {
    let msg; try { msg = JSON.parse(raw); } catch { res.writeHead(400, cors); return res.end("bad json"); }
    const cfg = { ...(msg.config || {}) };
    const vision = msg.vision || null;
    const events = [];
    const emit = (ev) => events.push(ev);
    const workdir = msg.workdir || process.cwd();
    // 撤销（撤回对话）：按 run 顺序回滚文件变更
    if (msg.type === "undo") {
      let restored = 0;
      const logs = handleRpc.undoStore || (handleRpc.undoStore = {});
      for (const rid of msg.runIds || []) { restored += applyUndo(logs[rid] || []); delete logs[rid]; }
      res.writeHead(200, { ...cors, "Content-Type": "application/json" });
      return res.end(JSON.stringify({ events: [{ type: "undo_result", restored }] }));
    }
    const runId = `r${Date.now()}_${Math.floor(Math.random() * 1e6)}`;
    const logs = handleRpc.undoStore || (handleRpc.undoStore = {});
    logs[runId] = [];
    const p = msg.type === "multimodal"
      ? handleMultimodal(cfg, vision, msg.dataUrl, msg.mime, msg.prompt, workdir, emit, (e) => logs[runId].push(e), runId)
      : runAgentLoop(cfg, msg.mode || "dsh", msg.content || "", msg.history || [], workdir, emit, vision, (e) => logs[runId].push(e), runId);
    p.then(() => { res.writeHead(200, { ...cors, "Content-Type": "application/json" }); res.end(JSON.stringify({ events })); });
  });
}

module.exports = { runAgentLoop, handleMultimodal, analyzeImage, saveTempImage, MODES, TOOL_SCHEMAS, startServer, runBash, execTool, compressHistory, applyUndo };

if (require.main === module) {
  const portArg = process.argv.indexOf("--port");
  const port = portArg >= 0 ? Number(process.argv[portArg + 1] || 0) : 0;
  startServer(port, (p) => console.log(`[deepking-host] listening on 127.0.0.1:${p}`));
}
