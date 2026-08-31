#!/usr/bin/env node
/* ============================================================
 * DeepKing-Plugin · shared/node-host.js
 * DeepKing AI 助手核心（移植自 DeepKing Rust 端：deepseek.rs + tools.rs + agent_loop.rs）
 * 双模式：
 *   - 作为库被 vscode/extension.js require（进程内 Agent Loop + 工具）
 *   - `node node-host.js --port 0` 启动 JSON-RPC 服务（JetBrains/浏览器模式）
 * ============================================================ */
"use strict";
const fs = require("fs");
const path = require("path");
const { execFile, spawn } = require("child_process");

/* ───────── 模式 Persona（精简版，源自 DeepKing personas + agent_loop directives） ───────── */
const MODES = {
  dsh: {
    label: "DSH (Harness)",
    system: `You are an autonomous coding agent (DeepSeek Harness style) working in the user's workspace.
Rules:
- For multi-step tasks FIRST call todo_write to plan; mark items completed as you go.
- For unknown codebases FIRST call glob + grep to build a map.
- Use bash for any build/test/run. Prefer small, runnable iterations; verify after each step.
- Before editing an existing file, call read on it first (exact content for old_string).
- If a tool call fails twice, switch approach and explain why.
- When done, output a concise summary with file paths. Max iterations: 20.`,
  },
  dsk: {
    label: "DSK (K3)",
    system: `You are a fast-iteration coding agent (K3 style).
Rules:
- Plan → Generate → Review → Refine. State your plan briefly before generating code.
- Prefer minimal runnable iterations; verify after each step.
- Read before edit; exact old_string matching.
- Every 5 iterations review the original goal and stop if it is complete.
- Output a concise summary when done. Max iterations: 15.`,
  },
  dsq: {
    label: "DSQ (Qwen3.8)",
    system: `You are a collaborative coding agent (Qwen3.8 style).
Rules:
- For any non-trivial task FIRST call todo_write to break it into subtasks; mark in_progress/completed.
- Mirror the existing project style: read similar files first, then write consistent code.
- Prefer complete runnable code over partial snippets. Chinese answers are welcome.
- Read before edit. Max iterations: 18.`,
  },
  dsg: {
    label: "DSG (GLM5.3)",
    system: `You are a global-view coding agent (GLM5.3 style).
Rules:
- For unfamiliar codebases call glob + grep first.
- Check usages with grep before editing shared functions.
- Be concise: show code first, reasoning only when asked.
- Read before edit; handle edge cases explicitly.
- Max iterations: 20.`,
  },
};

/* ───────── 工具 Schema（对标 DeepKing 15 工具核心集） ───────── */
const TOOL_SCHEMAS = [
  tool("read", "Read a file from the workspace. Returns lines with numbers. Use offset/limit for large files.", {
    type: "object", properties: { file_path: { type: "string" }, offset: { type: "integer" }, limit: { type: "integer" } }, required: ["file_path"],
  }),
  tool("write", "Create or overwrite a file. content MUST be <= 2000 chars; for longer files, write first chunk then append with edit.", {
    type: "object", properties: { file_path: { type: "string" }, content: { type: "string" } }, required: ["file_path", "content"],
  }),
  tool("edit", "Edit a file by replacing an exact string (old_string). MUST read the file first.", {
    type: "object", properties: { file_path: { type: "string" }, old_string: { type: "string" }, new_string: { type: "string" }, replace_all: { type: "boolean" } }, required: ["file_path", "old_string", "new_string"],
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
  tool("read_image", "Read an image file by path and return a short description you can rely on (model vision may be used).", {
    type: "object", properties: { image_path: { type: "string" } }, required: ["image_path"],
  }),
];
function tool(name, description, parameters) { return { type: "function", function: { name, description, parameters } }; }

/* ───────── 工具执行（移植自 DeepKing tools.rs） ───────── */
function resolvePath(workdir, p) { return path.isAbsolute(p) ? p : path.join(workdir, p); }

function execTool(workdir, name, args) {
  try {
    if (name === "read") return toolRead(workdir, args);
    if (name === "write") return toolWrite(workdir, args);
    if (name === "edit") return toolEdit(workdir, args);
    if (name === "glob") return toolGlob(workdir, args);
    if (name === "grep") return toolGrep(workdir, args);
    if (name === "todo_write" || name === "task") return { success: true, output: `[${name}] 任务列表已更新（前端展示）`, data: { ok: true } };
    if (name === "check_runtime") return toolCheckRuntime(args);
    if (name === "read_image") return { success: false, output: "webview 中无法本地解码图片；请在 VSCode 中打开图片查看，或用 bash 描述文件信息。", data: null };
    if (name === "bash") return { success: false, output: "bash 为异步工具，见 runBash()", data: null };
    if (name === "web_search") return { success: false, output: "插件版暂未内置搜索（可用 bash + python 实现），请改用其他方式。", data: null };
    return { success: false, output: `Unknown tool: ${name}`, data: null };
  } catch (e) {
    return { success: false, output: `工具执行错误: ${e.message}`, data: null };
  }
}

function toolRead(workdir, args) {
  const full = resolvePath(workdir, args.file_path || "");
  if (!fs.existsSync(full)) return { success: false, output: `读取失败: 文件不存在 ${args.file_path}`, data: null };
  let content = fs.readFileSync(full, "utf8").replace(/^\uFEFF/, "");
  const lines = content.split(/\r?\n/);
  const total = lines.length;
  const start = Math.max(0, args.offset || 0);
  const end = Math.min(total, start + (args.limit || 200));
  const out = lines.slice(start, end).map((l, i) => `${String(start + i + 1).padStart(6)}\t${l}`).join("\n");
  return { success: true, output: `File: ${args.file_path}\nLines ${start + 1}-${end} of ${total}\n\n${out}`, data: { total_lines: total } };
}

function toolWrite(workdir, args) {
  const full = resolvePath(workdir, args.file_path || "");
  const content = args.content || "";
  fs.mkdirSync(path.dirname(full), { recursive: true });
  fs.writeFileSync(full, content, "utf8");
  return { success: true, output: `Wrote ${Buffer.byteLength(content)} chars to ${args.file_path}`, data: { bytes_written: Buffer.byteLength(content) } };
}

function toolEdit(workdir, args) {
  const full = resolvePath(workdir, args.file_path || "");
  const oldString = args.old_string || "";
  const newString = args.new_string || "";
  if (!fs.existsSync(full)) return { success: false, output: `编辑失败: 文件不存在 ${args.file_path}`, data: null };
  const content = fs.readFileSync(full, "utf8");
  if (!content.includes(oldString)) return { success: false, output: `old_string 未在 ${args.file_path} 中找到，请先 read 获取精确内容`, data: null };
  const count = content.split(oldString).length - 1;
  if (!args.replace_all && count > 1) return { success: false, output: `old_string 出现 ${count} 次，请设置 replace_all=true 或提供更多上下文`, data: null };
  const next = args.replace_all ? content.split(oldString).join(newString) : content.replace(oldString, newString);
  fs.writeFileSync(full, next, "utf8");
  return { success: true, output: `Replaced ${args.replace_all ? count : 1} occurrence(s) in ${args.file_path}`, data: { replacements: args.replace_all ? count : 1 } };
}

/* 简化 glob：仅支持 * ? ** */
function compileGlob(pat) {
  let reg = "";
  let i = 0;
  while (i < pat.length) {
    const c = pat[i];
    if (c === "*" && pat[i + 1] === "*") { reg += ".*"; i += 2; continue; }
    if (c === "*") { reg += "[^\\/]*"; i++; continue; }
    if (c === "?") { reg += "[^\\/]"; i++; continue; }
    if (c === ".") { reg += "\\."; i++; continue; }
    if (c === "." || c === "-") { reg += c; i++; continue; }
    if ("^$()+[]{}|\\".includes(c)) { reg += "\\" + c; i++; continue; }
    reg += c; i++;
  }
  return new RegExp("^" + reg.replace(/\\\//g, "/") + "$");
}
function toolGlob(workdir, args) {
  const base = path.isAbsolute(args.path || "") ? args.path : path.join(workdir, args.path || ".");
  const pat = (args.pattern || "**/*").replace(/\\/g, "/");
  const re = compileGlob(pat);
  const out = [];
  const SKIP = new Set(["node_modules", ".git", "target", "dist", ".venv", "venv", "__pycache__", ".idea", ".vscode"]);
  (function walk(dir, rel) {
    let entries;
    try { entries = fs.readdirSync(dir, { withFileTypes: true }); } catch { return; }
    for (const e of entries) {
      if (e.name.startsWith(".") && SKIP.has(e.name)) continue;
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
  let re;
  try { re = new RegExp(args.pattern || "", "i"); } catch (e) { return { success: false, output: `正则无效: ${e.message}`, data: null }; }
  const ext = args.include_glob ? args.include_glob.replace(/[.*]/g, (m) => (m === "." ? "\\." : ".*")) : null;
  const out = [];
  const SKIP = new Set(["node_modules", ".git", "target", "dist", ".venv", "venv", "__pycache__", ".idea"]);
  let scanned = 0;
  (function walk(dir) {
    let entries;
    try { entries = fs.readdirSync(dir, { withFileTypes: true }); } catch { return; }
    for (const e of entries) {
      if (SKIP.has(e.name)) continue;
      const p = path.join(dir, e.name);
      if (e.isDirectory()) { walk(p); continue; }
      if (ext && !p.endsWith(ext)) continue;
      if (/\.(exe|dll|so|bin|png|jpg|jpeg|gif|ico|webp|db|pyc)$/i.test(e.name)) continue;
      scanned++;
      if (out.length >= 200) continue;
      let lines;
      try { lines = fs.readFileSync(p, "utf8").split(/\r?\n/); } catch { continue; }
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
    execFile(bin[0], bin.slice(1), { timeout: 5000 }, (err, stdout, stderr) => {
      resolve({ success: !err, output: err ? `[exit ${err.code ?? -1}] ${String(err.message).slice(0, 200)}` : String(stdout || stderr).trim(), data: { available: !err } });
    });
  });
}

const DANGEROUS = ["rm -rf /", "del /f /s /q C:", "format ", ":(){:|:&};:"];
function runBash(workdir, command, timeoutMs) {
  return new Promise((resolve) => {
    for (const p of DANGEROUS) if (command.includes(p)) return resolve({ success: false, output: `BLOCKED: 危险命令模式 (${p})`, data: { exit_code: -1 } });
    const isWin = process.platform === "win32";
    const shell = isWin ? "cmd" : "sh";
    const args = isWin ? ["/D", "/S", "/C", `set PYTHONIOENCODING=utf-8&& ${command}`] : ["-c", command];
    const child = execFile(shell, args, { cwd: workdir, maxBuffer: 8 * 1024 * 1024, timeout: timeoutMs || 30000, windowsHide: true }, (err, stdout, stderr) => {
      const code = err ? (typeof err.code === "number" ? err.code : -1) : 0;
      const out = String(stdout || "");
      const errOut = String(stderr || "");
      const combined = errOut ? `${out}\n[stderr]\n${errOut}` : out;
      resolve({ success: code === 0, output: `[exit ${code}]\n${combined.slice(0, 20000)}`, data: { exit_code: code } });
    });
    child.on("error", (e) => resolve({ success: false, output: `无法启动命令: ${e.message}`, data: { exit_code: -1 } }));
  });
}

/* ───────── DeepSeek 客户端（移植自 deepseek.rs） ───────── */
function normalizeCall(call) {
  let args = call.function.arguments;
  if (typeof args === "string") { try { args = JSON.parse(args); } catch { args = {}; } }
  return { id: call.id, name: call.function.name, arguments: args };
}
async function deepseekChat(config, system, messages, tools) {
  const body = {
    model: config.model,
    messages: [{ role: "system", content: system }, ...messages],
    stream: false,
    max_tokens: 8192,
    temperature: 0.7,
    tools,
    tool_choice: tools ? "auto" : undefined,
  };
  const url = `${config.baseUrl.replace(/\/$/, "")}/v1/chat/completions`;
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), 300000);
  try {
    const resp = await fetch(url, {
      method: "POST",
      headers: { "Authorization": `Bearer ${config.apiKey}`, "Content-Type": "application/json" },
      body: JSON.stringify(body),
      signal: ctrl.signal,
    });
    if (!resp.ok) {
      const text = await resp.text().catch(() => "");
      return { ok: false, error: `API error (${resp.status}): ${text.slice(0, 400)}` };
    }
    return { ok: true, data: await resp.json() };
  } catch (e) {
    return { ok: false, error: `Network error: ${e.message}` };
  } finally {
    clearTimeout(timer);
  }
}

/* ───────── Agent Loop（移植自 agent_loop.rs） ───────── */
async function runAgentLoop(config, mode, userMessage, history, workdir, onEvent) {
  const persona = MODES[mode] || MODES.dsh;
  const maxIter = 25;
  let messages = history.filter((m) => m.role !== "system" && m.id === undefined || true).map((m) => ({ role: m.role, content: m.content, tool_calls: m.tool_calls, tool_call_id: m.tool_call_id, name: m.name })).filter((m) => m.role !== "system");
  messages.push({ role: "user", content: userMessage });
  let finalContent = "";
  let toolCount = 0;
  onEvent({ type: "started", max_iterations: maxIter });
  for (let iter = 0; iter < maxIter; iter++) {
    onEvent({ type: "iteration", current: iter + 1, max: maxIter });
    const resp = await deepseekChat(config, persona.system, messages, TOOL_SCHEMAS);
    if (!resp.ok) { onEvent({ type: "error", message: resp.error }); return; }
    const choice = resp.data.choices && resp.data.choices[0];
    if (!choice) { onEvent({ type: "error", message: "无有效响应" }); return; }
    const msg = choice.message || {};
    finalContent = msg.content || "";
    if (msg.content) onEvent({ type: "assistant_text", content: msg.content });
    const calls = msg.tool_calls || [];
    messages.push({ role: "assistant", content: msg.content || null, tool_calls: msg.tool_calls || undefined });
    if (!calls.length) {
      onEvent({ type: "done", content: finalContent, total_iterations: iter + 1, total_tool_calls: toolCount });
      return;
    }
    for (const raw of calls) {
      toolCount++;
      const call = normalizeCall(raw);
      onEvent({ type: "tool_call_requested", id: call.id, name: call.name, arguments: call.arguments });
      let result;
      if (call.name === "bash") result = await runBash(workdir, call.arguments.command || "", call.arguments.timeout_ms);
      else { result = execTool(workdir, call.name, call.arguments); if (result instanceof Promise) result = await result; }
      const output = (result.output || "").length > 4000 ? result.output.slice(0, 3200) + `... [truncated, ${result.output.length} total chars]` : result.output;
      onEvent({ type: "tool_call_executed", id: call.id, name: call.name, success: result.success, output });
      messages.push({ role: "tool", tool_call_id: call.id, name: call.name, content: (result.success ? "" : "[ERROR] ") + output });
      if (/^(write|edit|bash|delete)$/.test(call.name) && result.success) onEvent({ type: "file_changed", reason: call.name });
    }
  }
  onEvent({ type: "done", content: finalContent, total_iterations: maxIter, total_tool_calls: toolCount });
}

/* ───────── CLI / JSON-RPC 服务模式（JetBrains / 浏览器使用） ───────── */
function startServer(port, ready) {
  const http = require("http");
  const MIME = { ".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8", ".css": "text/css; charset=utf-8", ".png": "image/png", ".ico": "image/x-icon", ".json": "application/json" };
  const WEBVIEW = path.join(__dirname, "webview");
  const server = http.createServer((req, res) => {
    const cors = { "Access-Control-Allow-Origin": "*", "Access-Control-Allow-Headers": "Content-Type", "Access-Control-Allow-Methods": "POST,OPTIONS" };
    if (req.method === "OPTIONS") { res.writeHead(204, cors); return res.end(); }
    if (req.url === "/rpc") { return handleRpc(req, res, cors); }
    // 静态 Web UI（JetBrains JCEF / 浏览器模式共用）
    let p = decodeURIComponent((req.url || "/").split("?")[0]);
    if (p === "/") p = "/index.html";
    const file = path.normalize(path.join(WEBVIEW, p));
    if (!file.startsWith(path.normalize(WEBVIEW))) { res.writeHead(403, cors); return res.end("forbidden"); }
    if (!fs.existsSync(file) || fs.statSync(file).isDirectory()) { res.writeHead(404, cors); return res.end("not found"); }
    const ext = path.extname(file).toLowerCase();
    res.writeHead(200, { ...cors, "Content-Type": MIME[ext] || "application/octet-stream", "Cache-Control": "no-cache" });
    return res.end(fs.readFileSync(file));
  });
  server.listen(port, "127.0.0.1", () => {
    const addr = server.address();
    ready(addr.port);
  });
  return server;
}

function handleRpc(req, res, cors) {
  let raw = "";
  req.on("data", (c) => (raw += c));
  req.on("end", () => {
    let msg;
    try { msg = JSON.parse(raw); } catch { res.writeHead(400, cors); return res.end("bad json"); }
    const config = { apiKey: (msg.config || {}).apiKey || "", baseUrl: (msg.config || {}).baseUrl || "https://api.deepseek.com", model: (msg.config || {}).model || "deepseek-chat" };
    const events = [];
    const p = runAgentLoop(config, msg.mode || "dsh", msg.content || "", msg.history || [], msg.workdir || process.cwd(), (ev) => events.push(ev));
    p.then(() => { res.writeHead(200, { ...cors, "Content-Type": "application/json" }); res.end(JSON.stringify({ events })); });
  });
}

/* 库模式入口（VSCode 用） */
module.exports = { runAgentLoop, MODES, TOOL_SCHEMAS, startServer, runBash, execTool };

if (require.main === module) {
  const portArg = process.argv.indexOf("--port");
  const port = portArg >= 0 ? Number(process.argv[portArg + 1] || 0) : 0;
  startServer(port, (p) => console.log(`[deepking-host] listening on 127.0.0.1:${p}`));
}
