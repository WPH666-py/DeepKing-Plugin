#!/usr/bin/env node
/* DeepKing-Plugin · 卸载器：移除已安装的扩展目录 */
"use strict";
const fs = require("fs");
const path = require("path");

const PKG_NAME = "WPH666-py.deepking-plugin-0.1.0";
function ideDirs() {
  const home = process.env.USERPROFILE || process.env.HOME || ".";
  const appData = process.env.APPDATA || path.join(home, "AppData", "Roaming");
  const dirs = [
    path.join(home, ".trae-cn", "extensions"),
    path.join(home, ".trae", "extensions"),
    path.join(appData, "Trae", "extensions"),
    path.join(appData, "TraeCN", "extensions"),
    path.join(appData, "Trae CN", "extensions"),
    path.join(home, ".vscode", "extensions"),
    path.join(home, ".cursor", "extensions"),
    path.join(home, ".codex", "extensions"),
    path.join(home, ".windsurf", "extensions"),
    path.join(home, ".vscodium", "extensions"),
    path.join(appData, "Code", "extensions"),
  ];
  if (process.env.DEEPKING_IDE_EXTENSIONS) dirs.unshift(process.env.DEEPKING_IDE_EXTENSIONS);
  return dirs;
}
let removed = 0;
for (const d of ideDirs()) {
  const p = path.join(d, PKG_NAME);
  if (fs.existsSync(p)) { try { fs.rmSync(p, { recursive: true, force: true }); console.log(`✅ 已移除 ${p}`); removed++; } catch (e) { console.log(`⚠️ ${p}: ${e.message}`); } }
}
console.log(removed ? `完成（移除 ${removed} 处）。请重启 IDE。` : "未发现 DeepKing 扩展安装。");
