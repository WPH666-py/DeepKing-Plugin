# DeepKing · AI 助手（VSCode 系）

> 本扩展为 [DeepKing-Plugin](../README.md) 的 VSCode / Trae / CodeX 侧边栏版本。
> 核心实现位于仓库根目录 `shared/`（与本仓库 JetBrains 版、浏览器版共用同一份代码）。

## 使用

1. 安装：打开扩展 → 活动栏 **DeepKing**（鲸鱼图标）→ AI 助手侧边栏；
2. 右上角 ⚙ 填写 **DeepSeek API Key / Base URL / 模型**（保存于本机 globalState）；
3. 选择模式（DSH / DSK / DSQ / DSG）输入问题。

## 开发 / 打包

```bash
cd vscode
npm run package        # prepack(复制 shared) + vsce 打包 → ./deepking-plugin-0.1.0.vsix
code --install-extension ./deepking-plugin-0.1.0.vsix
```

发布到市场（官方 VSCode Marketplace 需 Azure DevOps PAT；或 Open VSX token）：

```bash
npm run package
npx @vscode/vsce publish --pat <AZURE_DEVOPS_PAT>          # Marketplace
npx ovsx publish -p <OPEN_VSX_TOKEN>                       # Open VSX
```
