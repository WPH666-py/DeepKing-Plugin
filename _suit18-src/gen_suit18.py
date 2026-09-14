# -*- coding: utf-8 -*-
"""生成 Deepseek-Skin-Suit18 仓库。

模板: _suit18-src/tpl/(取自 Suit16 的 2×2 套件, 含自适应去底桌宠)
特点: 紧贴式 2×2 拼贴 + 4 张单图壁纸, 与 Suit1-8/11/14/16 同族。
脚本文档全部按 Suit18 显式写出(不做跨套件链式改名, 避免文案串味)。

用法: python _suit18-src/gen_suit18.py
产物: D:\\projects-py\\DeepKing-Plugin\\Deepseek-Skin-Suit18
"""
import os
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
TPL = os.path.join(HERE, "tpl")
SRC = HERE
DST = os.path.join(ROOT, "Deepseek-Skin-Suit18")

NUM = "18"
TOTAL = 28

IMAGES = [
    ("img1-salute.jpg", "01-salute.jpg"),
    ("img2-petfish.jpg", "02-petfish.jpg"),
    ("img3-tantrum.jpg", "03-tantrum.jpg"),
    ("img4-cache.jpg", "04-cache.jpg"),
]
IMAGE_FILES = [d for _s, d in IMAGES]
IMAGE_NAMES = [
    "誓死捍卫深度求索",
    "摸鱼",
    "别再蹬了啦!",
    "缓存必中",
]
SLEEP_STEM = "04-cache"          # 竖大拇指那张: 慢慢晃
PET_MENU = "4 张表情卡"


def read(p):
    with open(p, "r", encoding="utf-8") as f:
        return f.read()


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    print("[gen] %s (%d bytes)" % (os.path.relpath(path, ROOT), len(text.encode("utf-8"))))


def patch(text, pairs, label):
    """整段替换; 每条都必须命中, 否则中止(避免静默留下上一套的文案)。"""
    for old, new in pairs:
        if old not in text:
            raise SystemExit("[gen] %s: 未找到待替换片段:\n%s" % (label, old[:220]))
        if text.count(old) != 1:
            raise SystemExit("[gen] %s: 片段出现 %d 次(应为 1):\n%s" % (label, text.count(old), old[:220]))
        text = text.replace(old, new)
    return text


def copy_file(src, dst, label=None):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copyfile(src, dst)
    os.chmod(dst, 0o644)
    print("[gen] %s (copied)" % (label or os.path.relpath(dst, DST)))


def cut_function(src, name):
    start = src.index("def %s(" % name)
    nxt = src.find("\ndef ", start + 1)
    return src[start:nxt if nxt != -1 else len(src)]


# ---------------------------------------------------------------- skin_core
def gen_skin_core():
    t = read(os.path.join(TPL, "tools", "skin_core.py"))
    t = patch(t, [
        ("DeepSeek 蓝色大肥鱼 · 皮肤套件16 —— 核心库",
         "DeepSeek 蓝色大肥鱼 · 皮肤套件%s —— 核心库" % NUM),
        ('APP_DIR = os.path.join(os.path.expanduser("~"), ".deepskin16")',
         'APP_DIR = os.path.join(os.path.expanduser("~"), ".deepskin%s")' % NUM),
        ('IMAGE_FILES = ["01-tantrum.jpg", "02-jealous.jpg", "03-begging.jpg", "04-broke.jpg"]',
         'IMAGE_FILES = ["%s"]' % '", "'.join(IMAGE_FILES)),
        ('IMAGE_NAMES = [\n'
         '    "别再蹬了啦!",\n'
         '    "你已经有我了…",\n'
         '    "求你们不要再嘲笑了",\n'
         '    "已思考13秒: 穷光蛋",\n'
         ']',
         'IMAGE_NAMES = [\n' + "".join('    "%s",\n' % n for n in IMAGE_NAMES) + ']'),
        ("# 拼贴布局: Suit16 = 紧贴式 2×2(两行两列), 格子宽高比自动取素材平均比例(方图配方格)",
         "# 拼贴布局: Suit%s = 紧贴式 2×2(两行两列), 格子宽高比自动取素材平均比例(方图配方格)" % NUM),
    ], "tools/skin_core.py")
    write(os.path.join(DST, "tools", "skin_core.py"), t)


# ---------------------------------------------------------------- wallpaper
def gen_wallpaper():
    t = read(os.path.join(TPL, "tools", "wallpaper.py"))
    t = patch(t, [
        ("DeepSeek 蓝色大肥鱼 · 皮肤套件16 —— 壁纸命令行",
         "DeepSeek 蓝色大肥鱼 · 皮肤套件%s —— 壁纸命令行" % NUM),
        ("  python tools/wallpaper.py 1 --set               # 生成并设置单图 1(别再蹬了啦!)",
         "  python tools/wallpaper.py 1 --set               # 生成并设置单图 1(誓死捍卫深度求索)"),
        ("  python tools/wallpaper.py all --size 1920x1080  # 生成全部 5 种到 ~/.deepskin16/wallpapers",
         "  python tools/wallpaper.py all --size 1920x1080  # 生成全部 5 种到 ~/.deepskin%s/wallpapers" % NUM),
        ('ap = argparse.ArgumentParser(description="DeepSeek 大肥鱼16 壁纸工具")',
         'ap = argparse.ArgumentParser(description="DeepSeek 大肥鱼%s 壁纸工具")' % NUM),
    ], "tools/wallpaper.py")
    write(os.path.join(DST, "tools", "wallpaper.py"), t)


# ---------------------------------------------------------------- switcher
def gen_switcher():
    t = read(os.path.join(TPL, "tools", "switcher.py"))
    t = patch(t, [
        ("DeepSeek 蓝色大肥鱼 · 皮肤套件16 —— 可视化切换器",
         "DeepSeek 蓝色大肥鱼 · 皮肤套件%s —— 可视化切换器" % NUM),
        ('root.title("DeepSeek 大肥鱼16 · 皮肤切换器")',
         'root.title("DeepSeek 大肥鱼%s · 皮肤切换器")' % NUM),
    ], "tools/switcher.py")
    write(os.path.join(DST, "tools", "switcher.py"), t)


# ---------------------------------------------------------------- pet
def gen_pet():
    t = read(os.path.join(TPL, "tools", "pet.py"))
    old_modes = (
        'MODES = [\n'
        '    ("01-tantrum", "别再蹬了啦!"),\n'
        '    ("02-jealous", "你已经有我了…"),\n'
        '    ("03-begging", "求你们不要再嘲笑了"),\n'
        '    ("04-broke", "已思考13秒: 穷光蛋"),\n'
        ']'
    )
    new_modes = 'MODES = [\n' + "".join(
        '    ("%s", "%s"),\n' % (f[:-4], n) for f, n in zip(IMAGE_FILES, IMAGE_NAMES)
    ) + ']'
    t = patch(t, [
        ("DeepSeek 蓝色大肥鱼 · 皮肤套件16 —— 桌面桌宠",
         "DeepSeek 蓝色大肥鱼 · 皮肤套件%s —— 桌面桌宠" % NUM),
        ("  • 右键菜单: 切换 4 张表情卡 / 随机 / 打开皮肤切换器 / 退出",
         "  • 右键菜单: 切换 %s / 随机 / 打开皮肤切换器 / 退出" % PET_MENU),
        (old_modes, new_modes),
        ('SLEEP_STEM = "04-thinking"  # 思考中的图: 轻轻起伏',
         'SLEEP_STEM = "%s"  # 竖大拇指那张: 慢慢晃' % SLEEP_STEM),
    ], "tools/pet.py")
    write(os.path.join(DST, "tools", "pet.py"), t)


# ---------------------------------------------------------------- install
def gen_install():
    t = read(os.path.join(TPL, "tools", "install.py"))
    t = patch(t, [
        ("DeepSeek 蓝色大肥鱼 · 皮肤套件16 —— 一键安装",
         "DeepSeek 蓝色大肥鱼 · 皮肤套件%s —— 一键安装" % NUM),
        ('print("  DeepSeek 蓝色大肥鱼 · 皮肤套件16 安装器")',
         'print("  DeepSeek 蓝色大肥鱼 · 皮肤套件%s 安装器")' % NUM),
        ('print("  • VSCode/Trae/CodeX:   vscode/deepskin-suit16-0.1.0.vsix")',
         'print("  • VSCode/Trae/CodeX:   vscode/deepskin-suit%s-0.1.0.vsix")' % NUM),
    ], "tools/install.py")
    write(os.path.join(DST, "tools", "install.py"), t)


def gen_previews():
    write(os.path.join(DST, "tools", "make_previews.py"),
          read(os.path.join(TPL, "tools", "make_previews.py")))


# ---------------------------------------------------------------- vscode
def gen_vscode():
    t = read(os.path.join(TPL, "vscode", "extension.js"))
    for a, b in [("deepskin-suit16", "deepskin-suit%s" % NUM), ("deepskin16", "deepskin%s" % NUM),
                 ("Suit16", "Suit%s" % NUM), ("皮肤套件16", "皮肤套件%s" % NUM),
                 ("大肥鱼16", "大肥鱼%s" % NUM), ("DeepSkin-Suit16", "DeepSkin-Suit%s" % NUM)]:
        t = t.replace(a, b)
    cards_old = (
        "  const cards = [\n"
        "    { mode: 'grid', t: '2×2 拼贴', img: 'thumb-grid.png' },\n"
        "    { mode: 'single1', t: '别再蹬了啦!', img: 'thumb-1.png' },\n"
        "    { mode: 'single2', t: '你已经有我了…', img: 'thumb-2.png' },\n"
        "    { mode: 'single3', t: '求你们不要再嘲笑了', img: 'thumb-3.png' },\n"
        "    { mode: 'single4', t: '已思考13秒: 穷光蛋', img: 'thumb-4.png' },\n"
        "  ];"
    )
    cards_new = (
        "  const cards = [\n"
        "    { mode: 'grid', t: '2×2 拼贴', img: 'thumb-grid.png' },\n"
        + "".join("    { mode: 'single%d', t: '%s', img: 'thumb-%d.png' },\n" % (i, n, i)
                 for i, n in enumerate(IMAGE_NAMES, start=1))
        + "  ];"
    )
    t = patch(t, [(cards_old, cards_new)], "vscode/extension.js")
    write(os.path.join(DST, "vscode", "extension.js"), t)

    p = read(os.path.join(TPL, "vscode", "package.json"))
    for a, b in [("deepskin-suit16", "deepskin-suit%s" % NUM), ("deepskin16", "deepskin%s" % NUM),
                 ("Suit16", "Suit%s" % NUM), ("大肥鱼16", "大肥鱼%s" % NUM),
                 ("皮肤套件16", "皮肤套件%s" % NUM), ("DeepSkin-Suit16", "DeepSkin-Suit%s" % NUM)]:
        p = p.replace(a, b)
    p = patch(p, [
        ('"title": "大肥鱼%s: 别再蹬了啦!"' % NUM, '"title": "大肥鱼%s: %s"' % (NUM, IMAGE_NAMES[0])),
        ('"title": "大肥鱼%s: 你已经有我了…"' % NUM, '"title": "大肥鱼%s: %s"' % (NUM, IMAGE_NAMES[1])),
        ('"title": "大肥鱼%s: 求你们不要再嘲笑了"' % NUM, '"title": "大肥鱼%s: %s"' % (NUM, IMAGE_NAMES[2])),
        ('"title": "大肥鱼%s: 已思考13秒: 穷光蛋"' % NUM, '"title": "大肥鱼%s: %s"' % (NUM, IMAGE_NAMES[3])),
    ], "vscode/package.json")
    write(os.path.join(DST, "vscode", "package.json"), p)


# ---------------------------------------------------------------- 文档
AGENTS_MD = """# AGENTS.md — Deepseek-Skin-Suit{NUM} · AI 自动安装指引(仅供接受本仓库的 AI 助手参考)

当用户把本仓库地址交给你并要求「安装大肥鱼皮肤{NUM} / Deepseek 皮肤{NUM} / 壁纸插件 / 蓝色大肥鱼桌宠」时,
按下面步骤替用户执行, 不需要用户自己动手。本仓库是 **DeepSeek 蓝色大肥鱼皮肤套件{NUM}**
(四张表情卡: 誓死捍卫深度求索 / 摸鱼 / 别再蹬了啦! / 缓存必中),
提供紧贴式 2×2 拼贴壁纸、4 张单图壁纸、可视化切换器、桌面桌宠、VSCode 系扩展与 JetBrains 背景图素材。
核心脚本在 `tools/`, 素材在 `assets/`。

## 第 0 步: 下载与定位

```bash
git clone https://github.com/WPH666-py/Deepseek-Skin-Suit{NUM}.git "$HOME/DeepSkin-Suit{NUM}"
cd "$HOME/DeepSkin-Suit{NUM}"
```
Windows 建议固定克隆到 `%USERPROFILE%\\DeepSkin-Suit{NUM}`(VSCode 扩展默认在此查找)。
若用户机器没有 git, 用 zip 下载后解压到同一位置即可, 效果一致。

## 第 1 步: 识别环境

- 有 Python 3.9+ (`python --version` 或 `py -3 --version`) → 执行 **A**。
- 没有 Python → 先安装:
  - Windows: `winget install Python.Python.3.11`
  - macOS: `brew install python`
  - Ubuntu/Debian: `sudo apt install -y python3 python3-pil`
- 用户在用 VSCode / Trae / CodeX → 顺手执行 **C**; 在用 PyCharm / WebStorm / IntelliJ → 执行 **D**。
- 用户是在 DeepKing / Claude Code / Kimi Code / CodeX / Trae / Harness 等对话窗口里让你装的:
  由你代为执行下述命令, 不要只把命令贴给用户。

## A. 标准安装(全平台, 最常用)

```bash
python tools/install.py
```
脚本会自动: 装 Pillow(若缺失) → 按屏幕分辨率合成紧贴式 2×2 拼贴壁纸(四卡细缝相挨、整块居中,
格子宽高比按素材自动计算) → 设为系统壁纸 → 打印后续玩法。
多显示器: 用 `python tools/wallpaper.py grid --size 2560x1440 --set` 生成指定尺寸,
并提示用户在系统设置里把壁纸设为「跨屏 / 平铺」。

## B. 进阶玩法(用户想要时再执行)

```bash
python tools/wallpaper.py 1 --set        # 单图 1(誓死捍卫深度求索)
python tools/wallpaper.py 2 --set        # 单图 2(摸鱼)
python tools/wallpaper.py 3 --set        # 单图 3(别再蹬了啦!)
python tools/wallpaper.py 4 --set        # 单图 4(缓存必中)
python tools/wallpaper.py random --set   # 随机一张(拼贴或单图)
python tools/wallpaper.py cycle 30       # 每 30 分钟自动随机(挂后台)
python tools/switcher.py                 # 可视化切换器(GUI, 左侧预览右侧应用)
python tools/pet.py                      # 桌面桌宠(右键换表情)
```
GUI 命令需要本地图形会话; 若用户是远程/无桌面环境, 告知其改在有桌面的机器上运行。
**用户要求「支持切换壁纸」时, 优先引导 `switcher.py`(点选即换), 或 `wallpaper.py random/cycle`。**

## C. VSCode / Trae / CodeX 扩展

1. 安装(已预打包, 无需 Node):
   `code --install-extension "$HOME/DeepSkin-Suit{NUM}/vscode/deepskin-suit{NUM}-0.1.0.vsix"`
   无网时把 `vscode/` 整个目录复制到 `%USERPROFILE%\\.vscode\\extensions\\wp666.deepskin-suit{NUM}-0.1.0\\` 后重启编辑器
   (Trae / CodeX 的扩展目录同理)。
2. 告知用户: 活动栏 🐳 **大肥鱼{NUM}** 图标 → 皮肤画廊 → 点「设为壁纸」;
   命令面板搜 `大肥鱼{NUM}` 可换壁纸 / 开切换器 / 起桌宠。
3. 扩展自动查找 Python 与仓库路径(可用 `deepskin{NUM}.repoPath` 覆盖), Pillow 缺失时自动 pip 安装。
4. 与 Suit1-{PREV} 及 AI 全家桶系列可同时安装: 插件 ID / 命令前缀 / 运行时目录(`~/.deepskin{NUM}`)互不冲突。

## D. PyCharm / WebStorm / IntelliJ(JetBrains)

```bash
python tools/wallpaper.py all --out "$HOME/DeepSkin{NUM}"
```
然后引导用户: Settings / Preferences → Appearance & Behavior → Appearance → **Background Image** →
`+` 添加图片 → 选 `$HOME/DeepSkin{NUM}/grid-*.jpg`(或任一单图)。可分别给 Editor / Welcome /
Menus and tool windows 设不同图片; 细节见 `ide/jetbrains/README.md`。

## 约定与失败处理

- 只依赖 `tools/` 与 `assets/`; 生成物写入 `~/.deepskin{NUM}/`, **不会**改动仓库文件。
- Windows 控制台若出现 GBK/Unicode 编码错误: `chcp 65001` 后重跑(脚本已内置 UTF-8 兜底)。
- 找不到 Python(常见于 Store 版): 用完整路径
  `C:\\Users\\<user>\\AppData\\Local\\Programs\\Python\\Python311\\python.exe` 运行。
- 高分辨率屏合成慢: 允许 `--size 1920x1080` 降到 1080p。
- 素材或脚本更新后会自动重新合成(热更新), 无需手动删缓存。
- 个别 Linux 桌面不支持窗口透明色, 桌宠会退化成白底卡片, 属平台限制, 如实告知用户。
- 用户问与 DeepKing 本体的关系: 这是独立皮肤套件, 与 DeepKing 本体互不影响;
  装了 DeepKing-Plugin 的用户直接在它的 AI 对话里发本仓库链接就能完成安装。
- 皮肤总目录({TOTAL} 套)与 pip 包: https://github.com/WPH666-py/Desktop-IDE-AI-Skin
"""

README_MD = """# 🐳 DeepSeek 蓝色大肥鱼 · 皮肤套件{NUM} (Deepseek-Skin-Suit{NUM})

DeepSeek 蓝色大肥鱼(鲸鱼娘)主题皮肤第十八弹: **紧贴式 2×2 拼贴壁纸 / 4 张单图壁纸一键切换 /
可视化切换器 / 桌面桌宠 / 多 IDE 皮肤**。
表情: 誓死捍卫深度求索 · 摸鱼 · 别再蹬了啦! · 缓存必中。
素材内置、离线可用; 跨平台 Windows / macOS / Linux。

![2x2 拼贴壁纸预览](docs/2x2-preview.png)

## ✨ 功能

| 功能 | 说明 |
|---|---|
| 2×2 拼贴壁纸 | 四张表情卡细缝相挨、整块居中, 格子尺寸按素材比例自动计算 |
| 单图壁纸 ×4 | 每张表情可单独做壁纸, 模糊填充背景 + 居中圆角卡片 |
| 可视化切换器 | `tools/switcher.py`: 左侧实时预览, 右侧点「应用到桌面」, 可开自动随机 |
| 命令行换壁纸 | `tools/wallpaper.py`: grid / 1-4 / random / all / cycle |
| 桌面桌宠 | `tools/pet.py`: 透明置顶可拖动, 右键切换表情, 自动记住位置 |
| VSCode 系扩展 | 活动栏 🐳 图标 → 皮肤画廊, 卡片点选即换壁纸 |
| JetBrains 素材 | 生成 4 张单图 + 拼贴图, 供 PyCharm/WebStorm 背景图导入 |

![单图壁纸预览](docs/single-preview.png)

## 🚀 一键安装

把本仓库地址交给任意 AI(DeepKing / Claude Code / Kimi Code / CodeX / Trae / Harness / Cursor …),
说一句「安装这个皮肤」即可, AI 会读 `AGENTS.md` 自动完成。手动安装:

```bash
git clone https://github.com/WPH666-py/Deepseek-Skin-Suit{NUM}.git "$HOME/DeepSkin-Suit{NUM}"
cd "$HOME/DeepSkin-Suit{NUM}"
python tools/install.py          # 装 Pillow → 生成 2×2 拼贴 → 设为系统壁纸
```

## 🎛 切换壁纸

```bash
python tools/switcher.py                 # 图形切换器(推荐)
python tools/wallpaper.py 1 --set        # 誓死捍卫深度求索
python tools/wallpaper.py 2 --set        # 摸鱼
python tools/wallpaper.py 3 --set        # 别再蹬了啦!
python tools/wallpaper.py 4 --set        # 缓存必中
python tools/wallpaper.py grid --set     # 回到 2×2 拼贴
python tools/wallpaper.py random --set   # 随机一张
python tools/wallpaper.py cycle 30       # 每 30 分钟自动随机
python tools/wallpaper.py all --out ~/DeepSkin{NUM}   # 导出全部 5 张(给 PyCharm 等用)
```

## 🐋 桌面桌宠

```bash
python tools/pet.py     # 透明置顶小鲸鱼; 左键拖动, 右键切换表情/随机/开切换器, Esc 退出
```

## 🧩 IDE 集成

- **VSCode / Trae / CodeX**: `code --install-extension vscode/deepskin-suit{NUM}-0.1.0.vsix`
  → 活动栏 🐳「大肥鱼{NUM}」→ 皮肤画廊 → 「设为壁纸」。无网时把 `vscode/` 复制到
  `%USERPROFILE%\\.vscode\\extensions\\wp666.deepskin-suit{NUM}-0.1.0\\` 并重启。
- **PyCharm / WebStorm / IntelliJ**: `python tools/wallpaper.py all --out ~/DeepSkin{NUM}`,
  再在 Settings → Appearance → Background Image 里选图, 详见 `ide/jetbrains/README.md`。
- **DeepKing 本体**: 本仓库是独立皮肤套件, 与 DeepKing 本体互不影响;
  在 DeepKing 的 AI 对话里发本仓库链接即可自动安装。

## 📦 皮肤总目录 / pip 包

- 皮肤大全({TOTAL} 套, 含 AI 全家桶系列): https://github.com/WPH666-py/Desktop-IDE-AI-Skin
- pip 包: `pip install deepskins` → `deepskins list` / `deepskins install deepseek-{NUM}`

## 📁 目录结构

```
assets/           4 张表情素材(01-salute / 02-petfish / 03-tantrum / 04-cache)
tools/            install.py 一键安装 · wallpaper.py 命令行 · switcher.py 切换器 · pet.py 桌宠
vscode/           预打包 VSCode/Trae/CodeX 扩展(deepskin-suit{NUM}-0.1.0.vsix)
ide/jetbrains/    PyCharm 等背景图导入说明
docs/             预览图(由 tools/make_previews.py 生成)
```

## ⚠️ 说明

- 生成物写入 `~/.deepskin{NUM}/`(壁纸与缓存), 不改动仓库内容; 素材更新后自动重新合成。
- Windows 控制台若报 GBK 编码错误: `chcp 65001` 后重跑。
- 素材为 AI 生成的表情梗图, 仅供个人桌面娱乐使用; 请勿用于商业用途。
- License: MIT

---

其他套件: [皮肤大全](https://github.com/WPH666-py/Desktop-IDE-AI-Skin) ·
[DeepKing-Plugin](https://github.com/WPH666-py/DeepKing-Plugin)
"""

JETBRAINS_MD = """# JetBrains(PyCharm / WebStorm / IntelliJ)背景图

JetBrains 系 IDE 自带背景图功能, 本套件生成图片后手动导入即可。

## 1. 生成图片

```bash
python tools/wallpaper.py all --out "$HOME/DeepSkin{NUM}"
```

会得到 5 张图(2×2 拼贴 + 4 张单图):

```
grid-<宽>x<高>.jpg       2×2 拼贴
single1-<宽>x<高>.jpg    誓死捍卫深度求索
single2-<宽>x<高>.jpg    摸鱼
single3-<宽>x<高>.jpg    别再蹬了啦!
single4-<宽>x<高>.jpg    缓存必中
```

想指定尺寸加 `--size 2560x1440`。

## 2. 导入

`Settings / Preferences` → `Appearance & Behavior` → `Appearance` → **Background Image** →
`+` 选择上一步的图片 → `Opacity` 建议 8%–20% → `OK`。

同一对话框里可以分别给 `Editor and tools` / `Welcome screen` / `Menus and tool windows`
设置不同图片: 例如编辑器用拼贴图, 欢迎页用单图。

## 3. 推荐搭配

- 编辑器: `grid-*.jpg`, 不透明度 10% 左右, 不遮挡代码。
- 欢迎页: 任一 `single*.jpg`, 不透明度可到 40%。
- 想换表情: 重新运行 `python tools/wallpaper.py all --out "$HOME/DeepSkin{NUM}"` 后再选另一张即可。
"""

INSTALL_BAT = """@echo off
chcp 65001 >nul
echo ============================================
echo   DeepSeek 蓝色大肥鱼 · 皮肤套件{NUM} 安装
echo ============================================
where python >nul 2>nul
if errorlevel 1 (
  echo [x] 未找到 python, 请先安装 Python 3.9+:  winget install Python.Python.3.11
  pause
  exit /b 1
)
python "%~dp0tools\\install.py"
pause
"""

INSTALL_SH = """#!/usr/bin/env bash
set -e
echo "============================================"
echo "  DeepSeek 蓝色大肥鱼 · 皮肤套件{NUM} 安装"
echo "============================================"
if command -v python3 >/dev/null 2>&1; then PY=python3; else PY=python; fi
"$PY" "$(dirname "$0")/tools/install.py"
"""


def gen_docs():
    sub = {"NUM": NUM, "TOTAL": str(TOTAL), "PREV": str(int(NUM) - 1)}
    write(os.path.join(DST, "AGENTS.md"), AGENTS_MD.format(**sub))
    write(os.path.join(DST, "README.md"), README_MD.format(**sub))
    write(os.path.join(DST, "ide", "jetbrains", "README.md"), JETBRAINS_MD.format(**sub))
    write(os.path.join(DST, "install.bat"), INSTALL_BAT.format(**sub))
    write(os.path.join(DST, "install.sh"), INSTALL_SH.format(**sub))


def gen_static():
    for name in (".gitignore", "LICENSE"):
        shutil.copy2(os.path.join(TPL, name), os.path.join(DST, name))
        print("[gen] %s (copied)" % name)
    with open(os.path.join(DST, ".gitignore"), "a", encoding="utf-8") as f:
        f.write("\n# 打包中间产物(正式 vsix 随仓库提交)\n*.vsix.tmp\n.vscodeignore.bak\n")
    shutil.copy2(os.path.join(TPL, "vscode", "LICENSE"), os.path.join(DST, "vscode", "LICENSE"))
    print("[gen] vscode/LICENSE (copied)")
    copy_file(os.path.join(TPL, "vscode", "media", "deepskin.svg"),
              os.path.join(DST, "vscode", "media", "deepskin.svg"))
    for s, d in IMAGES:
        copy_file(os.path.join(SRC, s), os.path.join(DST, "assets", d), "assets/%s" % d)


def main():
    if os.path.exists(os.path.join(DST, ".git")):
        raise SystemExit("[gen] 目标已存在 git 仓库, 停止: %s" % DST)
    gen_skin_core()
    gen_wallpaper()
    gen_switcher()
    gen_pet()
    gen_install()
    gen_previews()
    gen_vscode()
    gen_static()
    gen_docs()
    print("\n[gen] 完成 -> %s" % DST)


if __name__ == "__main__":
    main()
