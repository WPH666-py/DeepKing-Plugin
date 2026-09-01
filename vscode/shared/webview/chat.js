/* DeepKing · 共享 Webview（VSCode 模式 / 本地服务模式 自适应）
 * v0.1.2：常驻内联设置表单；全防御式 DOM 访问；错误红条带行号 */
(() => {
  "use strict";

  function showBanner(text) {
    try {
      const b = document.querySelector("#errBanner");
      if (b) { b.textContent = text; b.style.display = "block"; return; }
    } catch (_) {}
    try { console.error(text); } catch (_) {}
  }
  window.addEventListener("error", (e) => {
    const stack = e.error && e.error.stack ? String(e.error.stack).split("\n").slice(0, 3).join(" | ") : "";
    showBanner("⚠️ 脚本错误: " + (e.message || "") + (stack ? "\n" + stack : ""));
  });
  window.addEventListener("unhandledrejection", (e) => {
    const r = e.reason || {};
    showBanner("⚠️ Promise 错误: " + ((r.stack || r.message || String(r)).toString().slice(0, 300)));
  });

  const $ = (s) => { try { return document.querySelector(s); } catch (_) { return null; } };
  const val = (id) => { const n = document.getElementById(id); return n ? n.value : ""; };

  const MODES = [
    { id: "dsh", label: "DSH (Harness)" }, { id: "dsk", label: "DSK (K3)" },
    { id: "dsq", label: "DSQ (Qwen3.8)" }, { id: "dsg", label: "DSG (GLM5.3)" },
  ];

  /* ── 传输层 ── */
  const vscode = (typeof acquireVsCodeApi === "function") ? acquireVsCodeApi() : null;
  const SERVER_PORT = (new URLSearchParams(location.search)).get("port") || "";

  function readStore() {
    try {
      if (vscode) return vscode.getState() || {};
      return JSON.parse(sessionStorage.getItem("dk") || "{}");
    } catch (_) { return {}; }
  }
  function persist(st) {
    try {
      if (vscode) vscode.setState(st);
      else sessionStorage.setItem("dk", JSON.stringify(st));
    } catch (_) {}
  }
  const state = readStore().state || {};
  if (typeof state.settings !== "object" || !state.settings) state.settings = {};
  if (!Array.isArray(state.messages)) state.messages = [];
  if (!Array.isArray(state.toolCalls)) state.toolCalls = [];
  if (typeof state.running !== "boolean") state.running = false;
  if (typeof state.runIds !== "object" || !state.runIds) state.runIds = {};
  state.pendingRunUser = null; state.currentRunId = null;

  /* ── 渲染 ── */
  const msgs = $("#messages") || document.body;
  function esc(s) { return String(s == null ? "" : s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;"); }
  function renderInline(s) {
    let t = esc(s);
    t = t.replace(/`([^`]+)`/g, "<code>$1</code>");
    t = t.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
    t = t.replace(/\[([^\]]+)\]\(([^)\s]+)\)/g, (m, txt, url) => (/^https?:\/\//i.test(url) ? `<a href="${url}">${txt}</a>` : m));
    return t;
  }
  function renderMarkdown(md) {
    const lines = (md || "").split(/\r?\n/);
    let out = [], code = null, buf = [];
    for (const line of lines) {
      if (code !== null) { if (/^\s*```/.test(line)) { out.push(`<pre><code>${esc(buf.join("\n"))}</code></pre>`); code = null; } else buf.push(line); continue; }
      if (/^\s*```/.test(line)) { code = ""; buf = []; continue; }
      if (/^(#{1,4})\s+/.test(line)) { const n = line.match(/^#{1,4}/)[0].length; out.push(`<h${n}>${renderInline(line.replace(/^#{1,4}\s+/, ""))}</h${n}>`); continue; }
      if (/^\s*[-*]\s+/.test(line)) { out.push(`<li>${renderInline(line.replace(/^\s*[-*]\s+/, ""))}</li>`); continue; }
      if (/^\s*>\s?/.test(line)) { out.push(`<blockquote>${renderInline(line.replace(/^\s*>\s?/, ""))}</blockquote>`); continue; }
      if (line.trim() === "") continue;
      out.push(`<p>${renderInline(line)}</p>`);
    }
    return out.join("");
  }
  const roleLabel = { user: "你", assistant: "AI", system: "系统" };
  function addMsg(role, content, extra) {
    const tip = $("#emptyTip"); if (tip) tip.style.display = "none";
    const wrap = document.createElement("div");
    wrap.className = "dk-msg " + role;
    const btn = (role === "user") ? `<button class="dk-withdraw" data-id="${esc(extra && extra.id ? extra.id : "")}" title="撤回该对话：内容回到输入框，并回滚本次文件修改">↩ 撤回</button>` : "";
    wrap.innerHTML = `<div class="dk-role">${roleLabel[role] || role}</div><div class="dk-content">${renderMarkdown(content)}</div>${btn}`;
    msgs.appendChild(wrap);
    msgs.scrollTop = msgs.scrollHeight;
    return wrap;
  }
  function renderToolCalls() {
    let html = `<div class="dk-tools"><div class="dk-tools-title">🛠 工具调用 (${state.toolCalls.length})</div>`;
    for (const tc of state.toolCalls) {
      const statusCss = tc.status === "error" ? "err" : tc.status === "done" ? "ok" : "wait";
      html += `<details class="dk-tool ${statusCss}"><summary>${esc(tc.name)} ${tc.status === "running" ? "…" : tc.status === "done" ? "✓" : "✗"}</summary>
        <div class="dk-tool-body"><div class="dk-tool-label">参数</div><pre class="dk-tool-pre">${esc(JSON.stringify(tc.arguments || {}))}</pre>
        <div class="dk-tool-label">${tc.status === "error" ? "✗ 错误" : "✓ 结果"}</div>
        <pre class="dk-tool-pre" style="white-space:pre-wrap">${esc((tc.output || "").slice(0, 3000))}</pre></div></details>`;
    }
    html += "</div>";
    const old = document.querySelector(".dk-tools"); if (old) old.remove();
    const asst = Array.from(msgs.querySelectorAll(".dk-msg.assistant")).pop();
    if (asst) asst.insertAdjacentHTML("afterend", html);
    else msgs.insertAdjacentHTML("beforeend", html);
  }
  function renderAll() {
    msgs.innerHTML = "";
    if (!state.messages.length) { const tip = $("#emptyTip"); if (tip) tip.style.display = ""; return; }
    state.messages.forEach((m) => addMsg(m.role, m.content, m));
    if (state.toolCalls.length) renderToolCalls();
    msgs.scrollTop = msgs.scrollHeight;
  }
  function setRunning(r) {
    state.running = r;
    const b = $("#btnSend"); if (b) { const i = $("#input"); b.disabled = r || !i.value.trim(); }
    const i = $("#input"); if (i) i.disabled = r;
    const m = $("#mode"); if (m) m.disabled = r;
  }
  function showProgress() {
    const p = $("#progress"); if (p) { p.style.display = ""; p.classList.remove("dk-done", "dk-error"); p.textContent = "🔄 AI 思考中… " + (state.progress || ""); }
    const tips = msgs.querySelectorAll(".dk-msg.assistant"); const tip = tips[tips.length - 1];
    if (tip && state.assistant) tip.querySelector(".dk-content").innerHTML = renderMarkdown(state.assistant);
  }
  function hideProgress() { const p = $("#progress"); if (p) { p.style.display = "none"; p.classList.remove("dk-done", "dk-error"); } }
  /** 完成/失败状态提示（绿/红，5 秒后自动消失） */
  function finishStatus(text, isError) {
    const p = $("#progress");
    if (p) {
      p.style.display = "";
      p.classList.toggle("dk-done", !isError);
      p.classList.toggle("dk-error", !!isError);
      p.textContent = text;
      setTimeout(() => { if (p.textContent === text) hideProgress(); }, 8000);
    }
  }
  /* 看门狗：运行中超 60s 无事件 → 提示可能卡住（非阻塞，完成自动停） */
  let watchdogTimer = null, lastEventAt = 0;
  function armWatchdog() { lastEventAt = Date.now(); clearInterval(watchdogTimer); watchdogTimer = setInterval(() => { if (state.running && Date.now() - lastEventAt > 150000) showBanner("⏳ 已 150 秒无响应。V4 思考模式推理可能长达数分钟，请稍候；若超过 5 分钟仍无输出会自动报错（API 超时兜底）。"); }, 5000); }
  function disarmWatchdog() { clearInterval(watchdogTimer); watchdogTimer = null; }
  function updateSettingsUI() {
    const fill = (id, v) => { const n = document.getElementById(id); if (n) n.value = v == null ? "" : v; };
    const chk = (id, v) => { const n = document.getElementById(id); if (n) n.checked = v !== false; };
    fill("setKey", state.settings.apiKey);
    fill("setBase", state.settings.baseUrl || "https://api.deepseek.com");
    fill("setModel", state.settings.model || "deepseek-chat");
    fill("setWorkdir", state.settings.workdir);
    chk("swTools", state.settings.tools);
    chk("swMax", state.settings.max);
    chk("swMM", state.settings.multimodal);
    fill("visionProvider", (state.settings.vision && state.settings.vision.provider) || "modlens");
    fill("visionKey", state.settings.vision && state.settings.vision.apiKey);
    fill("visionBase", (state.settings.vision && state.settings.vision.baseUrl) || "https://api.openai.com/v1");
    fill("visionModel", (state.settings.vision && state.settings.vision.model) || "gpt-4o-mini");
    syncVisionVisibility();
    const wl = $("#workdirLabel"); if (wl) wl.textContent = state.settings.workdir || "(工作目录见设置)";
  }
  /** 模式指示（一眼看出是纯文字还是 Agent） */
  function updateModeHint() {
    const hint = $("#ctxHint"); if (!hint) return;
    const toolsOn = state.settings.tools !== false && state.settings.max !== false;
    const mmOn = state.settings.multimodal !== false;
    hint.textContent = `模式：${toolsOn ? "Agent（16 工具）" : "纯文字（工具关）"} · ${mmOn ? "多模态开" : "多模态关"}`;
  }
  /** 对标 DeepKing：多模态未开启 → 隐藏视觉识别配置（无需填写） */
  function syncVisionVisibility() {
    const n = document.getElementById("swMM");
    const sec = document.getElementById("visionSection");
    if (!sec) return;
    const on = n ? n.checked : false;
    sec.style.display = on ? "" : "none";
    updateModeHint();
  }
  function saveSettingsFromUI() {
    state.settings.apiKey = val("setKey").trim();
    state.settings.baseUrl = val("setBase").trim() || "https://api.deepseek.com";
    state.settings.model = val("setModel").trim() || "deepseek-chat";
    state.settings.workdir = val("setWorkdir").trim();
    const chkV = (id) => { const n = document.getElementById(id); return n ? n.checked : true; };
    state.settings.tools = chkV("swTools");
    state.settings.max = chkV("swMax");
    state.settings.multimodal = chkV("swMM");
    state.settings.vision = {
      provider: val("visionProvider").trim() || "modlens",
      apiKey: val("visionKey").trim(),
      baseUrl: val("visionBase").trim() || "https://api.openai.com/v1",
      model: val("visionModel").trim() || "gpt-4o-mini",
    };
    persist(state);
    if (vscode) { try { vscode.postMessage({ type: "saveConfig", config: state.settings }); } catch (_) {} }
    updateModeHint();
    if (!state.running) finishStatus("✅ 配置已保存", false);
    const wl = $("#workdirLabel"); if (wl) wl.textContent = state.settings.workdir || "(工作目录见设置)";
  }

  /* ── 事件处理（宿主推送）── */
  const AGENT_EVENT_TYPES = ["started", "iteration", "tool_call_requested", "tool_call_executed", "assistant_text", "done", "error", "file_changed", "context_compressed"];
  function onAgentEvent(k) {
    try {
      if (!k || !k.type || !AGENT_EVENT_TYPES.includes(k.type)) return;
      lastEventAt = Date.now();
      if (k.type === "started") {
        state.progress = `0/${k.max_iterations} 步`;
        state.currentRunId = k.run_id || null;
        armWatchdog();
      }
      else if (k.type === "iteration") { state.progress = `${k.current}/${k.max} 步`; }
      else if (k.type === "tool_call_requested") { state.toolCalls.push({ id: k.id, name: k.name, arguments: k.arguments, status: "running", output: "" }); }
      else if (k.type === "tool_call_executed") { const tc = state.toolCalls.find((t) => t.id === k.id); if (tc) { tc.success = k.success; tc.output = k.output; tc.status = k.success ? "done" : "error"; } }
      else if (k.type === "assistant_text") { state.assistant = (state.assistant || "") + k.content; }
      else if (k.type === "done") {
        disarmWatchdog();
        const content = state.assistant || k.content || "";
        state.messages.push({ role: "assistant", content });
        state.assistant = ""; state.toolCalls = []; state.progress = "";
        // 记录本次运行（撤回用）：绑定到当前用户消息
        if (state.currentRunId && state.pendingRunUser) state.runIds[state.pendingRunUser] = state.currentRunId;
        state.currentRunId = null; state.pendingRunUser = null;
        persist(state); setRunning(false); hideProgress(); renderAll();
        let note = `✅ 已完成（${k.total_iterations} 步 · ${k.total_tool_calls} 工具）`;
        if (!content.trim()) note += " —— 模型返回为空，可尝试重新发送";
        const toolsOn = state.settings.tools !== false && state.settings.max !== false;
        if (toolsOn && !k.total_tool_calls) note += " —— 模型未调用任何工具：若期望读文件/改代码，请改用 deepseek-v4-pro 或 deepseek-chat（flash 可能不支持 Tool Calls）";
        finishStatus(note, false);
        return;
      }
      else if (k.type === "error") {
        disarmWatchdog();
        const text = "⚠️ 错误：" + k.message;
        state.messages.push({ role: "system", content: text });
        state.currentRunId = null; state.pendingRunUser = null;
        persist(state); setRunning(false); hideProgress(); renderAll();
        finishStatus("❌ 执行出错：" + (k.message || "").slice(0, 80), true);
        return;
      }
      showProgress(); if (state.toolCalls.length) renderToolCalls();
    } catch (e) {
      showBanner("⚠️ 事件处理错误: " + e.message + "\n" + String((e.stack || "")).slice(0, 300));
    }
  }
  if (vscode) {
    window.addEventListener("message", (e) => {
      const m = e.data;
      if (m && m.type === "ev") onAgentEvent(m.ev);
      else if (m && m.type === "config") {
        // 宿主配置（globalState 的真正来源）合并进本地状态并刷新 UI
        if (m.config) { state.settings = { ...state.settings, ...(m.config || {}) }; persist(state); }
        updateSettingsUI(); updateModeHint();
        const p = $("#progress");
        if (p && !state.running) { finishStatus("✅ 配置已加载", false); }
      }
      else if (m && m.type === "reset") { state.messages = []; persist(state); renderAll(); }
      else if (m && m.type === "undo_result") {
        finishStatus(`↩ 撤回完成，已回滚 ${m.restored} 处文件变更`, false);
      }
    });
  }

  /* ── 粘贴图片（多模态）── */
  function setPastedImage(dataUrl, mime, name) {
    state.pasted = { dataUrl, mime, name };
    const chip = $("#pasteChip"), img = $("#pastePreview"), nm = $("#pasteName");
    if (chip && img) { img.src = dataUrl; chip.style.display = "flex"; }
    if (nm) nm.textContent = name || "图片";
    persist(state);
  }
  function clearPastedImage() { state.pasted = null; const chip = $("#pasteChip"); if (chip) chip.style.display = "none"; persist(state); }

  /* ── 发送 ── */
  async function send() {
    if (state.running) return;
    const input = $("#input");
    const text = (input ? input.value : "").trim();
    if (!text && !state.pasted) return;
    saveSettingsFromUI();
    const pasted = (state.settings.multimodal !== false && state.pasted) ? state.pasted : null;
    const userMsg = { id: `u${Date.now()}_${Math.floor(Math.random() * 1e6)}`, role: "user", content: (pasted ? "📷[图片] " : "") + (text || "请描述这张图片。") };
    state.messages.push(userMsg);
    state.toolCalls = []; state.assistant = ""; state.progress = "";
    state.pendingRunUser = userMsg.id; state.currentRunId = null;
    persist(state);
    addMsg("user", userMsg.content, userMsg);
    if (input) input.value = "";
    clearPastedImage();
    setRunning(true); showProgress();
    const payload = pasted
      ? { type: "multimodal", dataUrl: pasted.dataUrl, mime: pasted.mime, prompt: text, mode: ($("#mode") || {}).value || "dsh", settings: state.settings }
      : { type: "chat", mode: ($("#mode") || {}).value || "dsh", content: text, history: state.messages.filter((m) => m.role !== "system" && m.id !== userMsg.id), settings: state.settings };
    try {
      if (vscode) { vscode.postMessage(payload); return; }
      const resp = await fetch(`http://127.0.0.1:${SERVER_PORT}/rpc`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ ...payload, config: payload.type === "multimodal" ? payload.settings : payload.settings, vision: payload.settings.vision }) });
      const data = await resp.json();
      for (const ev of data.events || []) onAgentEvent(ev);
      if (!(data.events || []).some((x) => x.type === "done" || x.type === "error")) { onAgentEvent({ type: "error", message: "宿主未返回结果" }); }
    } catch (e) {
      onAgentEvent({ type: "error", message: "通信失败: " + e.message });
    }
  }

  /* ── 撤回对话（对标 DeepKing：消息回输入框 + 文件变更整体回退）── */
  async function withdrawMessage(msgId) {
    if (!msgId || state.running) return;
    const idx = state.messages.findIndex((m) => m.id === msgId);
    if (idx < 0) return;
    const target = state.messages[idx];
    const runIds = [];
    for (let i = idx; i < state.messages.length; i++) {
      const rid = state.runIds[state.messages[i].id || ""];
      if (rid) runIds.push(rid);
    }
    if (runIds.length) {
      if (vscode) { vscode.postMessage({ type: "undo", runIds }); }
      else {
        try {
          const r = await fetch(`http://127.0.0.1:${SERVER_PORT}/rpc`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ type: "undo", runIds }) });
          const d = await r.json();
          const ev = (d.events || []).find((x) => x.type === "undo_result");
          if (ev) finishStatus(`↩ 撤回完成，已回滚 ${ev.restored} 处文件变更`, false);
        } catch (_) {}
      }
    }
    // 移除本消息及之后所有消息（内容回填输入框）
    for (let i = idx; i < state.messages.length; i++) delete state.runIds[state.messages[i].id || ""];
    state.messages.splice(idx);
    persist(state); renderAll();
    const input = $("#input"); if (input) { input.value = target.content; setRunning(false); input.focus(); }
    addMsg("system", "↩ 已撤回该对话（内容已回到输入框，本次文件修改已回滚）");
  }

  /* ── 初始化（全防御式，分步骤捕获）── */
  function step(fn, label) {
    try { fn(); } catch (e) { showBanner("⚠️ 初始化失败[" + label + "]: " + e.message + "\n" + String((e.stack || "")).slice(0, 300)); }
  }
  step(() => {
    const vt = document.getElementById("verTag"); if (vt) vt.textContent = "v0.1.10 ✓";
  }, "ver");
  step(() => {
    const sel = $("#mode"); if (!sel) return;
    for (const m of MODES) { const o = document.createElement("option"); o.value = m.id; o.textContent = m.label; sel.appendChild(o); }
    sel.value = state.settings.mode || "dsh";
    sel.addEventListener("change", () => { state.settings.mode = sel.value; persist(state); });
  }, "mode");
  step(() => {
    updateSettingsUI();
    updateModeHint();
    for (const id of ["setKey", "setBase", "setModel", "setWorkdir", "visionProvider", "visionKey", "visionBase", "visionModel"]) {
      const n = document.getElementById(id);
      if (n) n.addEventListener("change", saveSettingsFromUI);
    }
    /* 多模态开关联动：关闭 → 隐藏视觉配置（对标 DeepKing） */
    const swMM = document.getElementById("swMM");
    if (swMM) swMM.addEventListener("change", () => { saveSettingsFromUI(); syncVisionVisibility(); });
    for (const id of ["swTools", "swMax"]) {
      const n = document.getElementById(id);
      if (n) n.addEventListener("change", saveSettingsFromUI);
    }
  }, "settings");
  step(() => { renderAll(); }, "render");
  step(() => {
    const btn = $("#btnSend"); const input = $("#input");
    if (btn) btn.addEventListener("click", send);
    if (input) {
      input.addEventListener("keydown", (e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); } });
      input.addEventListener("input", () => setRunning(state.running));
      /* Ctrl+V 粘贴图片 → 多模态（多模态未开启时禁用，对标 DeepKing） */
      input.addEventListener("paste", (e) => {
        const mm = document.getElementById("swMM");
        if (mm && !mm.checked) return;
        const items = (e.clipboardData || {}).items; if (!items) return;
        for (const it of items) {
          if (it.kind === "file" && it.type && it.type.startsWith("image/")) {
            e.preventDefault();
            const f = it.getAsFile(); if (!f) return;
            const reader = new FileReader();
            reader.onload = () => setPastedImage(String(reader.result || ""), it.type, f.name || "粘贴图片");
            reader.readAsDataURL(f);
            return;
          }
        }
      });
    }
  }, "send");
  step(() => {
    const btn = $("#pasteRemove"); if (btn) btn.addEventListener("click", clearPastedImage);
  }, "paste");
  step(() => {
    /* 撤回按钮：事件委托（渲染后依然生效） */
    msgs.addEventListener("click", (e) => {
      const btn = e.target && e.target.closest ? e.target.closest(".dk-withdraw") : null;
      if (btn) withdrawMessage(btn.getAttribute("data-id"));
    });
  }, "withdraw");
  step(() => {
    const btn = $("#btnClear");
    if (btn) btn.addEventListener("click", () => {
      state.messages = []; state.toolCalls = []; state.assistant = ""; persist(state); renderAll();
      if (vscode) { try { vscode.postMessage({ type: "cleared" }); } catch (_) {} }
    });
  }, "clear");
})();
