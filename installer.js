#!/usr/bin/env node
/* ============================================================
 * DeepKing-Plugin · npm 安装器（postinstall）
 * 把扩展（vscode/ + shared/）复制进 VSCode 系 IDE 的扩展目录：
 *   Trae / Trae CN / VSCode / CodeX / Cursor / Windsurf/VSCodium 等
 * 用法：
 *   node installer.js            自动检测并安装（默认跳过已存在）
 *   node installer.js --force    覆盖重装
 *   node installer.js --list     列出检测到的扩展目录
 *   node installer.js --target <dir>   指定安装到某目录（调试用）
 *   node installer.js --dry-run  只打印将要执行的动作
 * ============================================================ */
"use strict";
const fs = require("fs");
const path = require("path");

/* 扩展文件夹名 = publisher.name-version，必须与 vscode/package.json 的 version 一致：
 * Trae CN 的扫描器在文件夹名与清单版本不符时会静默跳过该扩展（标准 VS Code 才容忍）。 */
let PKG_NAME = "WPH666-py.deepking-plugin-0.1.0"; // 兜底值
try {
  const extPkg = JSON.parse(fs.readFileSync(path.join(__dirname, "vscode", "package.json"), "utf8"));
  PKG_NAME = `${extPkg.publisher}.${extPkg.name}-${extPkg.version}`;
} catch (e) { /* vscode/package.json 缺失时使用兜底值 */ }

/* —— 候选扩展目录（按优先级） —— */
function ideDirs() {
  const home = process.env.USERPROFILE || process.env.HOME || ".";
  const appData = process.env.APPDATA || path.join(home, "AppData", "Roaming");
  const dirs = [
    // Trae（国际版 / 中文版通用候选）
    path.join(home, ".trae-cn", "extensions"),
    path.join(home, ".trae", "extensions"),
    path.join(appData, "Trae", "extensions"),
    path.join(appData, "TraeCN", "extensions"),
    path.join(appData, "Trae CN", "extensions"),
    // VSCode 系
    path.join(home, ".vscode", "extensions"),
    path.join(home, ".cursor", "extensions"),
    path.join(home, ".codex", "extensions"),
    path.join(home, ".windsurf", "extensions"),
    path.join(home, ".vscodium", "extensions"),
    // Windows 商店版 VSCode
    path.join(appData, "Code", "extensions"),
  ];
  // 环境变量指定
  if (process.env.DEEPKING_IDE_EXTENSIONS) dirs.unshift(process.env.DEEPKING_IDE_EXTENSIONS);
  return dirs;
}

/* —— 构建扩展内容（扩展根 = package.json；shared 同级） —— */
function buildExtensionContent() {
  const out = [];
  const add = (rel) => { const p = path.join(__dirname, rel); if (fs.existsSync(p)) out.push([rel, p]); };
  for (const f of ["package.json", "extension.js", "LICENSE.txt", "README.md", "media"]) {
    add(`vscode/${f}`);
  }
  add("shared/node-host.js");
  add("shared/webview");
  return out;
}

function copyEntry(dst, rel, src) {
  // rel 中的 "vscode/" 前缀去掉：扩展根 = package.json 所在层
  const clean = rel.replace(/^vscode[\\/]/, "");
  const target = path.join(dst, clean);
  if (fs.statSync(src).isDirectory()) fs.cpSync(src, target, { recursive: true });
  else { fs.mkdirSync(path.dirname(target), { recursive: true }); fs.copyFileSync(src, target); }
}

function installTo(dir, force, dry) {
  const idDir = path.join(dir, PKG_NAME);
  if (fs.existsSync(idDir) && !force) { console.log(`  ⏭  ${idDir} 已存在（--force 覆盖）`); return false; }
  if (dry) { console.log(`  ❯ 安装到 ${idDir}`); return true; }
  fs.rmSync(idDir, { recursive: true, force: true });
  for (const [rel, src] of buildExtensionContent()) copyEntry(idDir, rel, src);
  console.log(`  ✅ 已安装 ${idDir}`);
  return true;
}

function main() {
  const args = process.argv.slice(2);
  const force = args.includes("--force");
  const list = args.includes("--list");
  const dry = args.includes("--dry-run");
  const tIdx = args.indexOf("--target");
  const target = tIdx >= 0 ? args[tIdx + 1] : null;

  console.log("DeepKing-Plugin 安装器");
  if (list) {
    console.log("检测到的扩展目录：");
    for (const d of ideDirs()) console.log(`  ${fs.existsSync(d) ? "●（存在）" : "○（不存在）"} ${d}`);
    return;
  }
  const targets = target ? [path.resolve(target)] : ideDirs().filter((d) => fs.existsSync(d) || target);
  if (!targets.length) {
    console.log("未检测到 Trae/VSCode 系扩展目录。可在 IDE 已安装的机器上执行，或(DEEPKING_IDE_EXTENSIONS=<目录>) 指定。");
    return;
  }
  let installed = 0;
  for (const d of targets) { try { if (installTo(d, force, dry)) installed++; } catch (e) { console.log(`  ⚠️ ${d}: ${e.message}`); } }
  console.log(installed
    ? `完成（${installed} 处）。请重启 Trae / IDE，活动栏出现 DeepKing 图标即为成功。`
    : "未安装新副本（已有安装 / --dry-run）。");
}

main();
