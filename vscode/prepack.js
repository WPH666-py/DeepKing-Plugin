/* 打包前处理：把共享核心(../shared)复制进 vscode/shared（vsce 只打包扩展根目录内内容） */
const fs = require("fs");
const path = require("path");

const dst = path.join(__dirname, "shared");
fs.rmSync(dst, { recursive: true, force: true });
fs.mkdirSync(dst, { recursive: true });
const src = path.join(__dirname, "..", "shared");
for (const f of fs.readdirSync(src)) {
  if (f === "webview") {
    fs.cpSync(path.join(src, f), path.join(dst, f), { recursive: true });
  } else {
    fs.copyFileSync(path.join(src, f), path.join(dst, f));
  }
}
console.log("shared copied into vscode/ for packaging");
