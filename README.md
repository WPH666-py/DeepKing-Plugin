# DeepKing-Plugin（DeepKing 插件版）

把 **DeepKing** 的多模态 Agentic IDE **AI 助手**（DeepSeek 对话 × 多模式 Persona × 工具 Agent Loop）
以侧边栏形式带进主流 IDE —— 就像 Claude Code 在 VSCode 里一样。**DeepKing 本体代码零改动**，本仓库为独立插件。

![DeepKing](icon/deepking.png)

## 一、架构（怎么实现的）

DeepKing 的 AI 助手 = 前端对话 UI + 后端三件套（`deepseek.rs` 客户端 / `tools.rs` 16 工具 / `agent_loop.rs` 循环 + `personas` 模式）。
插件的映射关系：

| DeepKing（Rust/Tauri，不变） | DeepKing-Plugin（本仓库） |
|---|---|
| `commands/ai.rs` 对话与事件 | `shared/node-host.js` 的 `runAgentLoop()`（事件流同构：started/iteration/tool_call/text/done/error） |
| `ai/deepseek.rs`（chat + tools、300s 超时） | `shared/node-host.js` `deepseekChat()`（fetch，AbortController 300s） |
| `ai/tools.rs`（15 个工具 schema + 执行） | `shared/node-host.js` 核心工具集：read / write / edit / bash / grep / glob / todo_write / task / check_runtime（危险命令拦截、超时、路径规范化同源） |
| `ai/agent_loop.rs`（迭代上限、工具结果回灌） | `runAgentLoop()`（迭代上限 25、工具结果 [ERROR] 前缀回灌、输出截断） |
| `personas/` 四模式 | `MODES`（DSH/DSK/DSQ/DSG 精简版系统提示词） |
| Vue 聊天界面 | `shared/webview/`（原生 JS 单页：消息/工具卡片/Markdown 渲染/设置） |

**同一份核心，三种挂载方式**（这就是"支持多个 IDE 侧边栏"的原因）：

```
DeepKing-Plugin/
├── shared/                ★ 核心（唯一源）
│   ├── node-host.js       Windows/macOS/Linux 可运行：库模式 require() / 服务模式 --port
│   └── webview/           index.html + chat.js + style.css + deepking.png
├── vscode/                ← VSCode / Trae / CodeX
│   ├── package.json       activitybar 图标(DeepKing) + webview 侧边栏 + 命令
│   ├── extension.js       适配器：进程内 require(shared/node-host.js)，事件 push 到 Webview
│   └── media/             activitybar.svg + deepking.png（市场图标）
├── jetbrains/             ← PyCharm / WebStorm / IntelliJ
│   ├── plugin.xml         右侧 ToolWindow(DeepKing 图标)
│   ├── build.gradle.kts   打包时把 shared/ 拷进资源
│   └── .../DeepKingToolWindowFactory.kt   “壳”：起 node-host --port 0 → JCEF 加载 localhost UI
└── AGENTS.md              给 AI 助手的自动安装指引
```

- **VSCode 系**：`extension.js`（Node 进程）直接 require 核心 → 事件流 `postMessage` 到 Webview（`enableScripts`），无网络端口、无外部依赖。
- **JetBrains 系**：JCEF 内嵌浏览器加载 `http://127.0.0.1:<随机端口>`，端口由插件拉起的 `node shared/node-host.js --port 0` 提供（同款 UI + 同款核心；浏览器模式也走这条路）。
- **浏览器模式**：`node shared/node-host.js --port 8787` → 打开 `http://127.0.0.1:8787`（适合远程/无 IDE 环境）。

## 二、功能

- 💬 侧边栏 Webview 聊天（Enter 发送、Markdown 渲染、系统提示）
- 🛠 Agent Loop：工具调用实时卡片（参数/结果可展开），写文件后自动提示
- 🌓 四模式 Persona：DSH / DSK / DSQ / DSG
- ⚙ 配置：API Key / Base URL / 模型 / 工作目录（VSCode 存 globalState；JetBrains/浏览器存本地）
- 🔒 安全：危险命令模式拦截、命令超时（30s）、API 请求超时（300s）、路径规范化
- 🐳 图标 = DeepKing.ico（活动栏/市场/工具栏均为 DeepKing）

## 三、安装 / 使用

### VSCode / Trae / CodeX

```bash
# 方式 1：直接安装（本地打包）
cd vscode && npx @vscode/vsce package
code --install-extension ./deepking-plugin-0.1.0.vsix

# 方式 2：开发调试（F5 自动开 Extension Development Host）
# 在 vscode/ 内 code . 打开仓库，按 F5
```

打开后：活动栏鲸鱼图标 → **DeepKing AI** 侧边栏 → ⚙ 填 DeepSeek API Key → 提问。

### PyCharm / WebStorm / IntelliJ

```bash
cd jetbrains
./gradlew buildPlugin   # 产物: build/distributions/deepking-plugin-0.1.0.zip
# IDE → Settings → Plugins → ⚙ → Install Plugin from Disk → 选择 zip，重启
```

右侧 **DeepKing** 面板即 AI 助手。**要求本机 Node.js ≥ 18**（可设环境变量 `DEEPKING_NODE` 指定 node 路径）。

### 浏览器（任何环境）

```bash
node shared/node-host.js --port 8787
# 浏览器打开 http://127.0.0.1:8787 （如远程服务器，配合反向代理）
```

## 四、端口对照（DeepKing 原版能力 → 插件 v0.1.0）

| 能力 | DeepKing | 插件版 |
|---|---|---|
| DeepSeek 对话 + 工具循环 | ✅ | ✅ |
| read/write/edit/bash/grep/glob | ✅ | ✅ |
| todo/task/check_runtime | ✅ | ✅ |
| 视觉识图 / PDF / Excel 上下文 | ✅ | v1 占位（可用 bash+python 兜底） |
| web_search 工具 | ✅ | v1 未内置（可用 bash 实现） |
| 会话持久化 / 撤回对话 | ✅ | v1 内存会话（可扩展） |
| 多模态粘贴图片 | ✅ | v1 未含 |

## 五、开发约定

- **核心改动只改 `shared/`**，三端（VSCode / JetBrains / 浏览器）自动生效；
- webview 无构建步骤（原生 JS），改完即用；
- 事件协议与 DeepKing 的 `ai-agent-event` 保持同构，便于后续移植更多能力。

## 版权

DeepKing 本体与本插件由水哥（WPH666-py）开发；本插件仅供学习交流。DeepSeek API 由用户自备 Key，所有对话与文件操作仅在本机执行。
