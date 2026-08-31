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

  /* ── 渲染 ── */
  const msgs = $("#messages") || document.body;
  function esc(s) { return String(s == null ? "" : s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;"); }
  function renderInline(s) {
    let t = esc(s);
    t = t.replace(/`([^`]+)`/g, "<code>$1</code>");
    t = t.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
    t = t.replace(/\[([^\]]+)\]\(([^)\s]+)\)/g, '<a href="$2">$1</a>');
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
  function addMsg(role, content) {
    const tip = $("#emptyTip"); if (tip) tip.style.display = "none";
    const wrap = document.createElement("div");
    wrap.className = "dk-msg " + role;
    wrap.innerHTML = `<div class="dk-role">${roleLabel[role] || role}</div><div class="dk-content">${renderMarkdown(content)}</div>`;
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
    state.messages.forEach((m) => addMsg(m.role, m.content));
    if (state.toolCalls.length) renderToolCalls();
    msgs.scrollTop = msgs.scrollHeight;
  }
  function setRunning(r) { state.running = r; const b = $("#btnSend"); if (b) { const i = $("#input"); b.disabled = r || !i.value.trim(); } }
  function showProgress() {
    const p = $("#progress"); if (p) { p.style.display = ""; p.textContent = "AI 思考中… " + (state.progress || ""); }
    const tips = msgs.querySelectorAll(".dk-msg.assistant"); const tip = tips[tips.length - 1];
    if (tip && state.assistant) tip.querySelector(".dk-content").innerHTML = renderMarkdown(state.assistant);
  }
  function hideProgress() { const p = $("#progress"); if (p) p.style.display = "none"; }
  function updateSettingsUI() {
    const fill = (id, v) => { const n = document.getElementById(id); if (n) n.value = v == null ? "" : v; };
    fill("setKey", state.settings.apiKey);
    fill("setBase", state.settings.baseUrl || "https://api.deepseek.com");
    fill("setModel", state.settings.model || "deepseek-chat");
    fill("setWorkdir", state.settings.workdir);
    const wl = $("#workdirLabel"); if (wl) wl.textContent = state.settings.workdir || "(工作目录见设置)";
  }
  function saveSettingsFromUI() {
    state.settings.apiKey = val("setKey").trim();
    state.settings.baseUrl = val("setBase").trim() || "https://api.deepseek.com";
    state.settings.model = val("setModel").trim() || "deepseek-chat";
    state.settings.workdir = val("setWorkdir").trim();
    persist(state);
    if (vscode) { try { vscode.postMessage({ type: "saveConfig", config: state.settings }); } catch (_) {} }
    const wl = $("#workdirLabel"); if (wl) wl.textContent = state.settings.workdir || "(工作目录见设置)";
  }

  /* ── 事件处理（宿主推送）── */
  const AGENT_EVENT_TYPES = ["started", "iteration", "tool_call_requested", "tool_call_executed", "assistant_text", "done", "error", "file_changed", "context_compressed"];
  function onAgentEvent(k) {
    try {
      if (!k || !k.type || !AGENT_EVENT_TYPES.includes(k.type)) return;
      if (k.type === "started") { state.progress = `0/${k.max_iterations} 步`; }
      else if (k.type === "iteration") { state.progress = `${k.current}/${k.max} 步`; }
      else if (k.type === "tool_call_requested") { state.toolCalls.push({ id: k.id, name: k.name, arguments: k.arguments, status: "running", output: "" }); }
      else if (k.type === "tool_call_executed") { const tc = state.toolCalls.find((t) => t.id === k.id); if (tc) { tc.success = k.success; tc.output = k.output; tc.status = k.success ? "done" : "error"; } }
      else if (k.type === "assistant_text") { state.assistant = (state.assistant || "") + k.content; }
      else if (k.type === "done") {
        state.messages.push({ role: "assistant", content: state.assistant || k.content || "" });
        state.assistant = ""; state.toolCalls = []; state.progress = "";
        persist(state); setRunning(false); hideProgress(); renderAll();
      }
      else if (k.type === "error") {
        const text = "⚠️ 错误：" + k.message;
        state.messages.push({ role: "system", content: text });
        persist(state); setRunning(false); hideProgress(); renderAll();
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
      else if (m && m.type === "config") { updateSettingsUI(); }
      else if (m && m.type === "reset") { state.messages = []; persist(state); renderAll(); }
    });
  }

  /* ── 发送 ── */
  async function send() {
    if (state.running) return;
    const input = $("#input");
    const text = (input ? input.value : "").trim();
    if (!text) return;
    saveSettingsFromUI();
    state.messages.push({ role: "user", content: text });
    state.toolCalls = []; state.assistant = ""; state.progress = "";
    persist(state);
    addMsg("user", text);
    if (input) input.value = "";
    setRunning(true); showProgress();
    const payload = { type: "chat", mode: ($("#mode") || {}).value || "dsh", content: text, history: state.messages.filter((m) => m.role !== "system"), settings: state.settings };
    try {
      if (vscode) { vscode.postMessage(payload); return; }
      const resp = await fetch(`http://127.0.0.1:${SERVER_PORT}/rpc`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
      const data = await resp.json();
      for (const ev of data.events || []) onAgentEvent(ev);
      if (!(data.events || []).some((x) => x.type === "done" || x.type === "error")) { onAgentEvent({ type: "error", message: "宿主未返回结果" }); }
    } catch (e) {
      onAgentEvent({ type: "error", message: "通信失败: " + e.message });
    }
  }

  /* ── 初始化（全防御式，分步骤捕获）── */
  function step(fn, label) {
    try { fn(); } catch (e) { showBanner("⚠️ 初始化失败[" + label + "]: " + e.message + "\n" + String((e.stack || "")).slice(0, 300)); }
  }
  step(() => {
    const vt = document.getElementById("verTag"); if (vt) vt.textContent = "v0.1.2 ✓";
  }, "ver");
  step(() => {
    const sel = $("#mode"); if (!sel) return;
    for (const m of MODES) { const o = document.createElement("option"); o.value = m.id; o.textContent = m.label; sel.appendChild(o); }
    sel.value = state.settings.mode || "dsh";
    sel.addEventListener("change", () => { state.settings.mode = sel.value; persist(state); });
  }, "mode");
  step(() => {
    updateSettingsUI();
    for (const id of ["setKey", "setBase", "setModel", "setWorkdir"]) {
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
    }
  }, "send");
  step(() => {
    const btn = $("#btnClear");
    if (btn) btn.addEventListener("click", () => {
      state.messages = []; state.toolCalls = []; state.assistant = ""; persist(state); renderAll();
      if (vscode) { try { vscode.postMessage({ type: "cleared" }); } catch (_) {} }
    });
  }, "clear");
})();
