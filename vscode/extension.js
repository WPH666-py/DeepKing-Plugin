/* ============================================================
 * DeepKing-Plugin · vscode/extension.js
 * VSCode / Trae / CodeX（VSCode 系）适配器：
 *   - 侧边栏 Webview（活动栏鲸鱼图标 → "DeepKing AI 助手"）
 *   - 宿主端复用 shared/node-host.js（DeepSeek + Agent Loop + 工具）
 * ============================================================ */
"use strict";
const path = require("path");
const vscode = require("vscode");
const { runAgentLoop, MODES } = require(path.join(__dirname, "..", "shared", "node-host.js"));

const WEBVIEW_DIR = path.join(__dirname, "..", "shared", "webview");

class DeepKingViewProvider {
  constructor(context) {
    this.context = context;
    this.view = null;
    this.config = context.globalState.get("deepking.config") || { apiKey: "", baseUrl: "https://api.deepseek.com", model: "deepseek-chat", workdir: "" };
  }
  resolveWebviewView(webviewView) {
    this.view = webviewView;
    webviewView.webview.options = { enableScripts: true, localResourceRoots: [vscode.Uri.file(WEBVIEW_DIR)] };
    webviewView.webview.html = this.html(webviewView.webview);
    webviewView.webview.onDidReceiveMessage(async (msg) => {
      if (!msg) return;
      if (msg.type === "chat") {
        const workdir = this.config.workdir || (vscode.workspace.workspaceFolders && vscode.workspace.workspaceFolders[0].uri.fsPath) || process.cwd();
        const config = {
          apiKey: this.config.apiKey || "",
          baseUrl: this.config.baseUrl || "https://api.deepseek.com",
          model: this.config.model || "deepseek-chat",
        };
        if (!config.apiKey) { this.ev({ type: "error", message: "请先在右上角 ⚙ 设置 DeepSeek API Key" }); return; }
        const post = (ev) => this.ev(ev);
        await runAgentLoop(config, msg.mode || "dsh", msg.content || "", msg.history || [], workdir, post);
      } else if (msg.type === "saveConfig") {
        this.config = { ...this.config, ...(msg.config || {}) };
        this.context.globalState.update("deepking.config", this.config);
        this.ev({ type: "config", config: this.config });
      } else if (msg.type === "cleared") {
        /* 前端已清空；宿主端无需持久化 */
      }
    });
    // 初始化回传配置
    this.ev({ type: "config", config: { ...this.config, workdir: this.config.workdir || (vscode.workspace.workspaceFolders ? vscode.workspace.workspaceFolders[0].uri.fsPath : "") } });
  }
  ev(ev) { if (this.view) this.view.webview.postMessage({ type: "ev", ev }); }
  html(webview) {
    // 直接复用共享 webview 页面（与 JetBrains / 浏览器模式同一份 UI）
    const dir = (f) => webview.asWebviewUri(vscode.Uri.file(path.join(WEBVIEW_DIR, f))).toString();
    let html = require("fs").readFileSync(path.join(WEBVIEW_DIR, "index.html"), "utf8");
    html = html
      .replace(/href="style\.css"/, `href="${dir("style.css")}"`)
      .replace(/src="chat\.js"/, `src="${dir("chat.js")}"`)
      .replace(/src="deepking\.png"/, `src="${dir("deepking.png")}"`);
    return html;
  }
}

function activate(context) {
  // 共享 Node 宿主已通过 require 加载；此处提供 vsce 可见的生命周期
  const provider = new DeepKingViewProvider(context);
  context.subscriptions.push(
    vscode.window.registerWebviewViewProvider("deepking.chatView", provider, { webviewOptions: { retainContextWhenHidden: true } }),
    vscode.commands.registerCommand("deepking.openChat", () => vscode.commands.executeCommand("deepking.chatView.focus")),
    vscode.commands.registerCommand("deepking.configure", () => provider.view && provider.view.webview.postMessage({ type: "ev", ev: { type: "_openSettings" } }))
  );
  context.globalState.update("deepking.hostVersion", "0.1.0");
  banner(context);
}
function banner(context) {
  const first = context.globalState.get("deepking.welcomed");
  if (first) return;
  context.globalState.update("deepking.welcomed", true);
  void vscode.window.showInformationMessage("DeepKing AI 助手已激活：点击活动栏鲸鱼图标开始使用（右上角 ⚙ 配置 DeepSeek API Key）");
}
function deactivate() {}

module.exports = { activate, deactivate };
