/* DeepKing · 共享 Webview（VSCode 模式 / 本地服务模式 自适应） */
(() => {
  "use strict";
  /* —— 自诊断：任何脚本错误直接在页面顶部显示（Trae 控制台不可见时也能定位） —— */
  window.addEventListener("error", (e) => showBanner("⚠️ 脚本错误: " + (e.message || e.error) + "\n" + ((e.error && e.error.stack) ? String(e.error.stack).slice(0, 800) : "")));
  window.addEventListener("unhandledrejection", (e) => showBanner("⚠️ Promise 错误: " + ((e.reason && (e.reason.stack || e.reason.message)) || e.reason)));
  function showBanner(text) {
    const b = document.querySelector("#errBanner");
    if (b) { b.textContent = text; b.style.display = "block"; }
    else console.error(text);
  }
  const $ = (s) => document.querySelector(s);
  /** 安全取元素；避免 null 直接炸 */
  const el = (s) => { const n = document.querySelector(s); return n || null; };
  const MODES = [
    { id: "dsh", label: "DSH (Harness)" }, { id: "dsk", label: "DSK (K3)" },
    { id: "dsq", label: "DSQ (Qwen3.8)" }, { id: "dsg", label: "DSG (GLM5.3)" },
  ];

  /* ── 传输层 ── */
  const vscode = typeof acquireVsCodeApi === "function" ? acquireVsCodeApi() : null;
  const params = new URLSearchParams(location.search);
  const SERVER_PORT = params.get("port") || "";

  const store = vscode
    ? (() => { try { return vscode.getState() || {}; } catch { return {}; } })()
    : (() => { try { return JSON.parse(sessionStorage.getItem("dk") || "{}"); } catch { return {}; } })();
  const persist = (st) => {
    store.state = st;
    if (vscode) { try { vscode.setState(st); } catch {} } else { try { sessionStorage.setItem("dk", JSON.stringify(st)); } catch {} }
  };

  const state = store.state || { settings: {}, messages: [], toolCalls: [], running: false };
  if (!state.settings) state.settings = {};
  if (!Array.isArray(state.messages)) state.messages = [];
  const me = {
    post(msg) {
      if (vscode) vscode.postMessage(msg);
      else return fetch(`http://127.0.0.1:${SERVER_PORT}/rpc`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(msg) }).then((r) => r.json());
    },
    send(msg) { return this.post(msg); },
  };

  /* ── 渲染 ── */
  const msgs = $("#messages");
  function esc(s) { return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;"); }
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
      if (/^\s*```/.test(line)) { code = ""; buf = []; out.push(`<pre><code>`); continue; }
      if (/^(#{1,4})\s+/.test(line)) { out.push(`<h${line.match(/^#{1,4}/)[0].length}>${renderInline(line.replace(/^#{1,4}\s+/, ""))}</h${line.match(/^#{1,4}/)[0].length}>`); continue; }
      if (/^\s*[-*]\s+/.test(line)) { out.push(`<li>${renderInline(line.replace(/^\s*[-*]\s+/, ""))}</li>`); continue; }
      if (/^\s*>\s?/.test(line)) { out.push(`<blockquote>${renderInline(line.replace(/^\s*>\s?/, ""))}</blockquote>`); continue; }
      if (line.trim() === "") continue;
      out.push(`<p>${renderInline(line)}</p>`);
    }
    if (code === "" && buf.length) out.push(`<pre><code>${esc(buf.join("\n"))}</code></pre>`);
    return out.join("");
  }
  const roleLabel = { user: "你", assistant: "AI", system: "系统" };
  function addMsg(role, content) {
    $("#emptyTip").style.display = "none";
    const wrap = document.createElement("div");
    wrap.className = `dk-msg ${role}`;
    wrap.innerHTML = `<div class="dk-role">${roleLabel[role] || role}</div><div class="dk-content">${renderMarkdown(content)}</div>`;
    msgs.appendChild(wrap);
    msgs.scrollTop = msgs.scrollHeight;
    return wrap;
  }
  function renderAll() {
    msgs.innerHTML = "";
    if (!state.messages.length) { $("#emptyTip").style.display = ""; return; }
    state.messages.forEach((m) => addMsg(m.role, m.content));
    if (state.toolCalls.length) renderToolCalls();
    if (state.running) showProgress();
    msgs.scrollTop = msgs.scrollHeight;
  }
  function renderToolCalls() {
    let html = `<div class="dk-tools"><div class="dk-tools-title">🛠 工具调用 (${state.toolCalls.length})</div>`;
    for (const tc of state.toolCalls) {
      const args = JSON.stringify(tc.arguments || {});
      const statusCss = tc.status === "error" ? "err" : tc.status === "done" ? "ok" : "wait";
      html += `<details class="dk-tool ${statusCss}">
        <summary>${esc(tc.name)} ${tc.status === "running" ? "…" : tc.status === "done" ? "✓" : "✗"}</summary>
        <div class="dk-tool-body">
          <div class="dk-tool-label">参数</div><pre class="dk-tool-pre">${esc(args)}</pre>
          <div class="dk-tool-label">${tc.status === "error" ? "✗ 错误" : "✓ 结果"}</div>
          <pre class="dk-tool-pre" style="white-space:pre-wrap">${esc((tc.output || "").slice(0, 3000))}</pre>
        </div></details>`;
    }
    html += "</div>";
    const old = document.querySelector(".dk-tools");
    if (old) old.remove();
    const asst = Array.from(msgs.querySelectorAll(".dk-msg.assistant")).pop();
    if (asst) asst.insertAdjacentHTML("afterend", html);
    else msgs.insertAdjacentHTML("beforeend", html);
  }
  function setRunning(r) { state.running = r; $("#btnSend").disabled = r || !$("#input").value.trim(); }
  function showProgress() {
    const p = $("#progress");
    p.style.display = "";
    p.textContent = `AI 思考中… ${state.progress || ""}`;
    const tip = document.querySelector(".dk-msg.assistant:last-child .dk-content");
    if (tip) tip.innerHTML = renderMarkdown(state.assistant || "🛠 工具调用中…");
  }
  function hideProgress() { $("#progress").style.display = "none"; }

  /* ── 事件处理（宿主推送） ── */
  const AGENT_EVENT_TYPES = ["started", "iteration", "tool_call_requested", "tool_call_executed", "assistant_text", "done", "error", "file_changed", "context_compressed"];
  function onAgentEvent(ev) {
    if (!ev || !ev.type || !AGENT_EVENT_TYPES.includes(ev.type)) return;
    const k = ev;
    if (k.type === "started") { state.progress = `0/${k.max_iterations} 步`; }
    else if (k.type === "iteration") { state.progress = `${k.current}/${k.max} 步`; }
    else if (k.type === "tool_call_requested") { state.toolCalls.push({ id: k.id, name: k.name, arguments: k.arguments, status: "running", output: "" }); }
    else if (k.type === "tool_call_executed") {
      const tc = state.toolCalls.find((t) => t.id === k.id);
      if (tc) { tc.success = k.success; tc.output = k.output; tc.status = k.success ? "done" : "error"; }
    }
    else if (k.type === "assistant_text") { state.assistant = (state.assistant || "") + k.content; }
    else if (k.type === "done") {
      const content = state.assistant || k.content || "";
      state.messages.push({ role: "assistant", content });
      state.assistant = ""; state.toolCalls = []; state.progress = "";
      persist(state); setRunning(false); hideProgress(); renderAll();
      state.toolCalls = []; state.assistant = ""; state.progress = "";
    }
    else if (k.type === "error") {
      addMsg("system", `⚠️ 错误：${k.message}`);
      state.messages.push({ role: "system", content: `⚠️ 错误：${k.message}` });
      persist(state); setRunning(false); hideProgress();
    }
    else if (k.type === "file_changed") { /* 可扩展：刷新文件树 */ }
    showProgress(); renderToolCalls();
  }
  if (vscode) {
    window.addEventListener("message", (e) => {
      const m = e.data;
      if (m && m.type === "ev") onAgentEvent(m.ev);
      else if (m && m.type === "config") { Object.assign(state.settings, m.config || {}); renderWorkdirLabel(); }
      else if (m && m.type === "reset") { state.messages = []; persist(state); renderAll(); }
    });
  }

  /* ── 发送 ── */
  async function send() {
    const input = $("#input");
    const text = input.value.trim();
    if (!text || state.running) return;
    state.messages.push({ role: "user", content: text });
    state.toolCalls = []; state.assistant = ""; state.progress = "";
    persist(state);
    addMsg("user", text);
    input.value = "";
    setRunning(true);
    showProgress();
    const payload = {
      type: "chat", mode: $("#mode").value,
      content: text,
      history: state.messages.filter((m) => m.role !== "system"),
      settings: state.settings,
    };
    if (vscode) {
      vscode.postMessage(payload);
    } else {
      // 本地服务模式：一次性返回事件流
      try {
        const r = await me.send(payload);
        for (const ev of r.events) onAgentEvent(ev);
        if (!r.events.some((e) => e.type === "done" || e.type === "error")) { addMsg("system", "⚠️ 宿主未返回结果"); setRunning(false); hideProgress(); }
      } catch (e) {
        addMsg("system", `⚠️ 通信失败：${e.message}`);
        state.messages.push({ role: "system", content: `⚠️ 通信失败：${e.message}` });
        persist(state); setRunning(false); hideProgress();
      }
    }
  }
  function renderWorkdirLabel() {
    $("#workdirLabel").textContent = state.settings.workdir || "(浏览器模式请在工作目录设置中填写)";
  }

  /* ── 初始化 ── */
  function init() {
    /* 标记：chat.js 已执行（排障时看标题是否出现 ✓） */
    const vt = document.getElementById("verTag");
    if (vt) vt.textContent = "v0.1.1 ✓";

    /* 先绑定设置按钮（最简、最优先，避免被后续错误连累） */
    const btnSettings = document.getElementById("btnSettings");
    const overlay = document.getElementById("settingsOverlay");
    const openSettings = () => { if (overlay) { overlay.style.display = "flex"; } else showBanner("⚠️ 未找到设置面板 DOM"); };
    if (btnSettings) {
      btnSettings.addEventListener("click", openSettings);
      btnSettings.onclick = openSettings; // 双保险
    }

    const sel = $("#mode");
    MODES.forEach((m) => { const o = document.createElement("option"); o.value = m.id; o.textContent = m.label; sel.appendChild(o); });
    sel.value = state.settings.mode || "dsh";
    $("#setKey").value = state.settings.apiKey || "";
    $("#setBase").value = state.settings.baseUrl || "https://api.deepseek.com";
    $("#setModel").value = state.settings.model || "deepseek-chat";
    $("#setWorkdir").value = state.settings.workdir || "";
    renderAll();
    renderWorkdirLabel();

    $("#btnSend").addEventListener("click", send);
    $("#input").addEventListener("keydown", (e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); } });
    $("#input").addEventListener("input", () => { $("#btnSend").disabled = state.running || !$("#input").value.trim(); });
    $("#mode").addEventListener("change", () => { state.settings.mode = $("#mode").value; persist(state); });
    $("#btnClear").addEventListener("click", () => {
      state.messages = []; state.toolCalls = []; state.assistant = ""; persist(state); renderAll();
      if (vscode) vscode.postMessage({ type: "cleared" });
    });
    $("#btnCancel").addEventListener("click", () => { overlay.style.display = "none"; });
    $("#btnSave").addEventListener("click", () => {
      state.settings.apiKey = $("#setKey").value.trim();
      state.settings.baseUrl = $("#setBase").value.trim() || "https://api.deepseek.com";
      state.settings.model = $("#setModel").value.trim() || "deepseek-chat";
      state.settings.workdir = $("#setWorkdir").value.trim();
      persist(state); renderWorkdirLabel();
      if (vscode) vscode.postMessage({ type: "saveConfig", config: state.settings });
      overlay.style.display = "none";
    });
  }
  try { init(); } catch (e) { showBanner("⚠️ 初始化失败: " + e.message); }
})();
