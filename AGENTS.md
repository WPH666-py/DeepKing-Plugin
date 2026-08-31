# AGENTS.md — DeepKing-Plugin · AI 自动安装指引（AI 助手必读）

当用户把本仓库地址交给你并要求「安装 DeepKing 插件」时，按下述步骤执行。

## 第 1 步：识别用户环境

- VSCode / Trae / CodeX → 执行「A」（VSCode 系侧边栏）。
- PyCharm / WebStorm / IntelliJ（JetBrains 系）→ 执行「B」。
- 其它（任意浏览器 / 远程）→ 执行「C」。

## A. VSCode / Trae / CodeX

1. 下载 `https://github.com/WPH666-py/DeepKing-Plugin`（zip 或 git clone 均可）。
2. 打包并安装扩展：
   ```bash
   cd <clone>/vscode
   npx --yes @vscode/vsce package
   code --install-extension ./deepking-plugin-0.1.3.vsix
   ```
   若无网络/CLI：把 `vscode/` 整个目录复制到 `%USERPROFILE%\.vscode\extensions\wp666.deepking-plugin-0.1.0\`（Trae/CodeX 兼容），并提示用户重启编辑器。
3. 告知用户：活动栏鲸鱼图标（DeepKing）→ 侧边栏 AI 助手 → 右上角 ⚙ 配置 DeepSeek API Key 后即可对话。

## B. PyCharm / WebStorm（JetBrains）

1. 需要 Node.js ≥ 18（`node --version` 检查；无则先安装或设置 `DEEPKING_NODE`）。
2. 构建插件：
   ```bash
   cd <clone>/jetbrains
   ./gradlew buildPlugin
   ```
3. 安装 `build/distributions/deepking-plugin-0.1.3.zip`：IDE → Settings → Plugins → ⚙ → Install Plugin from Disk → 重启。
4. 告知用户：右侧 **DeepKing** 面板即 AI 助手（JCEF 内嵌，同款界面）。

## C. 浏览器模式

```bash
node <clone>/shared/node-host.js --port 8787
浏览器打开 http://127.0.0.1:8787
```

## 约定与失败处理

- 核心在 `shared/`：node-host.js（Agent Loop + 工具 + DeepSeek）+ webview/（UI）。三端共用，**不要**在 vscode/ 与 jetbrains/ 里复制逻辑。
- webview 原生 JS 无构建；改完静态资源直接生效（VSCode 里重载窗口即可）。
- `bash` 工具在 Windows 走 `cmd /D /S /C`，危险模式已拦截；命令默认 30s 超时。
- API Key 存本机（VSCode globalState / 浏览器 sessionStorage），不会上传到任何第三方。
- 用户询问与 DeepKing 本体的关系时如实说明：本插件是把 DeepKing 的 AI 助手能力抽出的独立扩展，DeepKing 本体仓库零改动。
