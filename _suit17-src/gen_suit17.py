# -*- coding: utf-8 -*-
"""生成 Deepseek-Skin-Suit17 仓库。

模板: _suit17-src/tpl/(取自 Suit12 的"单张样式"套件)
特点: IMAGE_FILES 只有 1 张素材 -> grid = 全屏单图(cover), single1 = 卡片单图。
脚本与文档都按 Suit17 显式写出(不再靠对上一套做链式替换, 避免文案串味)。

用法: python _suit17-src/gen_suit17.py
产物: D:\\projects-py\\DeepKing-Plugin\\Deepseek-Skin-Suit17
"""
import os
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
TPL = os.path.join(HERE, "tpl")
SRC = HERE
DST = os.path.join(ROOT, "Deepseek-Skin-Suit17")

NUM = "17"
ASSET_SRC = "img1-quad.jpg"          # 素材源(四格拼图, 960x960)
ASSET_DST = "01-quad.jpg"            # 仓库内文件名
ASSET_STEM = "01-quad"
WALLPAPER_NAME = "鲸鱼四连(2×2 四格)"
PET_NAME = "鲸鱼娘"
# 桌宠: 四格拼图里取左上"胆孝"那一格(方形取景, 角色居中且不带格线)
PET_CROP = (0.26, 0.26, 0.18)        # (中心x比例, 中心y比例, 半边长占最短边比例)
BG_TOL = 26
BG_BRIGHT = 168


def read(p):
    with open(p, "r", encoding="utf-8") as f:
        return f.read()


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    print("[gen] %s (%d bytes)" % (os.path.relpath(path, ROOT), len(text.encode("utf-8"))))


def patch(text, pairs, label):
    for old, new in pairs:
        if old not in text:
            raise SystemExit("[gen] %s: 未找到待替换片段:\n%s" % (label, old[:200]))
        text = text.replace(old, new)
    return text


def copy_file(src, dst, label=None):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copyfile(src, dst)
    os.chmod(dst, 0o644)
    print("[gen] %s (copied)" % (label or os.path.relpath(dst, DST)))


# ---------------------------------------------------------------- skin_core
# "适合屏幕"渲染: 整张完整 + 渐变底, 方形素材在 16:9 屏上不会被裁字。
FIT_RENDER = '''

def _fit_gradient(size, top=(248, 251, 255), bottom=(226, 238, 252)):
    """极浅蓝白竖向渐变背景。"""
    from PIL import Image
    w, h = size
    col = Image.new("RGB", (1, h))
    for y in range(h):
        k = y / max(h - 1, 1)
        col.putpixel((0, y), tuple(int(a + (b - a) * k) for a, b in zip(top, bottom)))
    return col.resize((w, h))


def compose_fit(size=(1920, 1080)):
    """整张完整显示(contain)+ 渐变底 + 圆角阴影。

    方形/竖版素材在 16:9 屏幕上 cover 会裁掉约 22% 的高度, 四格文案会被切;
    这个模式保证整张素材都在画面内。
    """
    ensure_pillow()
    from PIL import Image, ImageDraw, ImageFilter

    src = Image.open(asset_path(1)).convert("RGB")
    w, h = size
    base = _fit_gradient(size).convert("RGBA")

    margin = max(18, int(min(w, h) * 0.045))
    tw, th = w - 2 * margin, h - 2 * margin
    scale = min(tw / src.width, th / src.height)
    nw, nh = max(1, int(src.width * scale)), max(1, int(src.height * scale))
    tile = src.resize((nw, nh), Image.LANCZOS)
    x, y = (w - nw) // 2, (h - nh) // 2
    radius = max(10, int(min(nw, nh) * 0.035))

    mask = Image.new("L", (nw, nh), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, nw - 1, nh - 1], radius=radius, fill=255)

    pad = max(12, radius)
    sh = Image.new("RGBA", (nw + 2 * pad, nh + 2 * pad), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle(
        [pad, pad, pad + nw - 1, pad + nh - 1], radius=radius, fill=(24, 55, 110, 70))
    sh = sh.filter(ImageFilter.GaussianBlur(max(8, radius // 2)))
    base.alpha_composite(sh, (x - pad, y - pad))
    base.paste(tile, (x, y), mask)
    return base.convert("RGB")
'''


def gen_skin_core():
    t = read(os.path.join(TPL, "tools", "skin_core.py"))
    t = patch(t, [
        ("DeepSeek 蓝色大肥鱼 · 皮肤套件 —— 核心库",
         "DeepSeek 蓝色大肥鱼 · 皮肤套件%s —— 核心库" % NUM),
        ("功能: 素材定位、2x2 拼贴壁纸、单图壁纸(模糊填充)、系统壁纸设置",
         "功能: 素材定位、全屏单图(cover)、完整卡片单图(适合屏幕)、系统壁纸设置"),
        ('APP_DIR = os.path.join(os.path.expanduser("~"), ".deepskin12")',
         'APP_DIR = os.path.join(os.path.expanduser("~"), ".deepskin%s")' % NUM),
        ('IMAGE_FILES = ["01-water.jpg"]',
         'IMAGE_FILES = ["%s"]' % ASSET_DST),
        ('IMAGE_NAMES = [\n    "漂在水中",\n]',
         'IMAGE_NAMES = [\n    "%s",\n]' % WALLPAPER_NAME),
        ("# 单张样式: grid = 全屏单图铺满(cover), single1 = 模糊填充卡片单图",
         "# 单张样式。素材是 1:1 方形, 在 16:9 屏上 cover 会裁掉上下各约 22%(四格文案会被切),\n"
         "# 因此默认 grid = 完整卡片(适合屏幕), single1 = 全屏铺满(cover)。\n"
         "# 想换回 Suit12 那种默认, 把 GRID_FIT 改成 False 即可。"),
        ("MODES = [(\"grid\", \"全屏单图(默认)\"), (\"single1\", \"卡片单图\")]",
         "GRID_FIT = True  # True: grid=完整卡片(不裁切); False: grid=全屏单图(cover)\n"
         "MODES = [\n"
         "    (\"grid\", \"完整单图(默认, 不裁切)\"),\n"
         "    (\"single1\", \"全屏单图(铺满, 上下裁切)\"),\n"
         "]"),
        ("def compose(mode, size=None):", FIT_RENDER.strip("\n") + "\n\n\ndef compose(mode, size=None):"),
        ("    \"\"\"按模式名合成壁纸: mode ∈ {grid, single1..}。\n"
         "    GRID_SINGLE 套件: grid = 全屏单图(cover); 否则 grid = 拼贴。\"\"\"",
         "    \"\"\"按模式名合成壁纸: mode ∈ {grid, single1..}。\n"
         "    本套件 GRID_SINGLE=True: grid 按 GRID_FIT 决定是 完整卡片 还是 全屏 cover;\n"
         "    single1 = 全屏 cover。\"\"\""),
        ("    if mode == \"grid\":\n        if GRID_SINGLE:\n            return compose_cover(size)\n        return compose_grid(size)",
         "    if mode == \"grid\":\n"
         "        if GRID_SINGLE:\n"
         "            return compose_fit(size) if GRID_FIT else compose_cover(size)\n"
         "        return compose_grid(size)"),
        ("    if mode.startswith(\"single\"):\n        return compose_single(int(mode[6:]), size)",
         "    if mode.startswith(\"single\"):\n"
         "        # 单张素材套件: single1 走全屏 cover(GRID_FIT 时与 grid 区分开)\n"
         "        if GRID_SINGLE and GRID_FIT:\n"
         "            return compose_cover(size)\n"
         "        return compose_single(int(mode[6:]), size)"),
    ], "tools/skin_core.py")
    write(os.path.join(DST, "tools", "skin_core.py"), t)


# ---------------------------------------------------------------- wallpaper
def gen_wallpaper():
    t = read(os.path.join(TPL, "tools", "wallpaper.py"))
    t = patch(t, [
        ("DeepSeek 蓝色大肥鱼 · 皮肤套件 —— 壁纸命令行",
         "DeepSeek 蓝色大肥鱼 · 皮肤套件%s —— 壁纸命令行" % NUM),
        ("  python tools/wallpaper.py grid --set            # 生成并设置 2x2 拼贴壁纸",
         "  python tools/wallpaper.py grid --set            # 生成并设置完整卡片单图(默认, 不裁切)"),
        ("  python tools/wallpaper.py 1 --set               # 生成并设置单图 1(摸摸头)",
         "  python tools/wallpaper.py 1 --set               # 生成并设置全屏单图(cover 铺满, 上下裁切)"),
        ("  python tools/wallpaper.py all --size 1920x1080  # 生成全部 5 种到 ~/.deepskin/wallpapers",
         "  python tools/wallpaper.py all --size 1920x1080  # 生成全部模式到 ~/.deepskin%s/wallpapers" % NUM),
        ('ap = argparse.ArgumentParser(description="DeepSeek 大肥鱼壁纸工具")',
         'ap = argparse.ArgumentParser(description="DeepSeek 大肥鱼%s 壁纸工具")' % NUM),
    ], "tools/wallpaper.py")
    write(os.path.join(DST, "tools", "wallpaper.py"), t)


# ---------------------------------------------------------------- switcher
def gen_switcher():
    t = read(os.path.join(TPL, "tools", "switcher.py"))
    t = patch(t, [
        ('root.title("DeepSeek 大肥鱼 · 皮肤切换器")',
         'root.title("DeepSeek 大肥鱼%s · 皮肤切换器")' % NUM),
    ], "tools/switcher.py")
    write(os.path.join(DST, "tools", "switcher.py"), t)


# ---------------------------------------------------------------- pet
NEW_CUT = '''def _corner_bg(px, w, h, inset=6):
    """取四角 inset 处的最亮一个作为背景色(避开角上压到角色的深色和 JPEG 边缘噪点)。"""
    cs = []
    for cx, cy in ((inset, inset), (w - 1 - inset, inset),
                   (inset, h - 1 - inset), (w - 1 - inset, h - 1 - inset)):
        r, g, b, _a = px[cx, cy]
        cs.append((min(r, g, b), (r, g, b)))
    cs.sort()
    return cs[-1][1]


def cut_white_bg(img, thresh=232):
    """自适应去底: 从画面外框向内的邻域泛洪, 去掉白 / 浅灰 / 米白等底色并羽化边缘。

    底色不是纯白(有渐变、JPEG 噪点、角上压到角色)时, 固定阈值和"全局底色"都不可靠,
    因此这里比较的是相邻像素的色差, 让泛洪能跟随渐变, 又不会跨过角色的深色描边。
    """
    img = img.convert("RGBA")
    w, h = img.size
    px = img.load()
    bg = _corner_bg(px, w, h)
    tol2 = BG_TOL * BG_TOL

    def near_bg(c, ref):
        return ((c[0] - ref[0]) ** 2 + (c[1] - ref[1]) ** 2 + (c[2] - ref[2]) ** 2) <= tol2

    def is_bright(x, y):
        r, g, b, a = px[x, y]
        return a > 0 and min(r, g, b) >= BG_BRIGHT

    for attempt in range(2):
        kept = bytearray(b"\\x01") * (w * h)
        q = deque()
        edge = 1 if attempt == 0 else 0
        for x in range(edge, w - edge):
            for y in (edge, h - 1 - edge):
                if kept[y * w + x] and is_bright(x, y):
                    kept[y * w + x] = 0
                    q.append((x, y))
        for y in range(edge, h - edge):
            for x in (edge, w - 1 - edge):
                if kept[y * w + x] and is_bright(x, y):
                    kept[y * w + x] = 0
                    q.append((x, y))

        while q:
            x, y = q.popleft()
            ref = px[x, y]
            for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if 0 <= nx < w and 0 <= ny < h:
                    i = ny * w + nx
                    if kept[i] and is_bright(nx, ny) and near_bg(px[nx, ny], ref):
                        kept[i] = 0
                        q.append((nx, ny))

        removed = w * h - sum(kept)
        if removed <= w * h * 0.72:
            break
        # 泛洪吃掉了太多(底色渐变把角色也带走): 退回"与全局底色比色"再试一次
        kept = bytearray(b"\\x01") * (w * h)
        for y in range(h):
            for x in range(w):
                if is_bright(x, y) and near_bg(px[x, y], bg):
                    kept[y * w + x] = 0

    # 羽化: 贴着透明区的亮色像素按与底色的接近程度渐变, 去掉残留白边
    edge2 = (BG_TOL + 30) ** 2
    for y in range(h):
        for x in range(w):
            i = y * w + x
            if not kept[i]:
                px[x, y] = (px[x, y][0], px[x, y][1], px[x, y][2], 0)
                continue
            r, g, b = px[x, y][0], px[x, y][1], px[x, y][2]
            if min(r, g, b) < BG_BRIGHT:
                continue
            d = (r - bg[0]) ** 2 + (g - bg[1]) ** 2 + (b - bg[2]) ** 2
            if d >= edge2:
                continue
            near = False
            for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if 0 <= nx < w and 0 <= ny < h and not kept[ny * w + nx]:
                    near = True
                    break
            if near:
                t = ((d ** 0.5) - BG_TOL * 0.5) / (BG_TOL + 14.0)
                t = 0.0 if t < 0 else (1.0 if t > 1 else t)
                px[x, y] = (r, g, b, int(255 * t))
    return img
'''


def cut_function(src, name):
    start = src.index("def %s(" % name)
    nxt = src.find("\ndef ", start + 1)
    return src[start:nxt if nxt != -1 else len(src)]


def gen_pet():
    t = read(os.path.join(TPL, "tools", "pet.py"))
    t = patch(t, [
        ("DeepSeek 蓝色大肥鱼 · 皮肤套件 —— 桌面桌宠",
         "DeepSeek 蓝色大肥鱼 · 皮肤套件%s —— 桌面桌宠" % NUM),
        ('SLEEP_STEM = "01-water"  # 漂在水中的图: 慢慢晃',
         'SLEEP_STEM = "%s"  # 四格拼图取景: 慢慢晃' % ASSET_STEM),
        ('MODES = [\n    ("01-water", "漂在水中"),\n]',
         'MODES = [\n    ("%s", "%s"),\n]' % (ASSET_STEM, PET_NAME)),
        ("# 非白底素材(如蓝色水景)不做泛洪去底, 改用方形取景裁剪:\n"
         "# {stem: (中心x比例, 中心y比例, 半边长占最短边比例)}\n"
         'PET_CROPS = {\n    "01-water": (0.72, 0.45, 0.47),\n}',
         "# 四格拼图整张不好抠: 取景裁剪出左上「胆孝」那一格做桌宠贴图\n"
         "# {stem: (中心x比例, 中心y比例, 半边长占最短边比例)}\n"
         'PET_CROPS = {\n    "%s": (%.2f, %.2f, %.2f),\n}\n'
         "# 去底容差(颜色距离) 与 判定为底色所需的最低亮度\n"
         "BG_TOL = %d\n"
         "BG_BRIGHT = %d" % (ASSET_STEM, PET_CROP[0], PET_CROP[1], PET_CROP[2], BG_TOL, BG_BRIGHT)),
        (cut_function(t, "cut_white_bg"), NEW_CUT),
    ], "tools/pet.py")
    write(os.path.join(DST, "tools", "pet.py"), t)


# ---------------------------------------------------------------- install
def gen_install():
    t = read(os.path.join(TPL, "tools", "install.py"))
    t = patch(t, [
        ("DeepSeek 蓝色大肥鱼 · 皮肤套件 —— 一键安装",
         "DeepSeek 蓝色大肥鱼 · 皮肤套件%s —— 一键安装" % NUM),
        ('print("  DeepSeek 蓝色大肥鱼 · 皮肤套件 安装器")',
         'print("  DeepSeek 蓝色大肥鱼 · 皮肤套件%s 安装器")' % NUM),
        ("  • 生成全部壁纸:         python tools/wallpaper.py all",
         "  • 全屏铺满单图:         python tools/wallpaper.py 1 --set"),
    ], "tools/install.py")
    write(os.path.join(DST, "tools", "install.py"), t)


def gen_previews():
    write(os.path.join(DST, "tools", "make_previews.py"),
          read(os.path.join(TPL, "tools", "make_previews.py")))


# ---------------------------------------------------------------- vscode
def gen_vscode():
    t = read(os.path.join(TPL, "vscode", "extension.js"))
    t = t.replace("deepskin-suit12", "deepskin-suit%s" % NUM)   # 连字符形式要放在前面
    t = t.replace("deepskin12", "deepskin%s" % NUM)
    t = t.replace("Suit12", "Suit%s" % NUM)
    t = t.replace("皮肤套件12", "皮肤套件%s" % NUM)
    t = t.replace("大肥鱼12", "大肥鱼%s" % NUM)
    t = t.replace("DeepSkin-Suit12", "DeepSkin-Suit%s" % NUM)
    t = patch(t, [
        ("  const cards = [\n"
         "    { mode: 'grid', t: '全屏单图', img: 'thumb-grid.png' },\n"
         "    { mode: 'single1', t: '卡片单图', img: 'thumb-1.png' }\n"
         "  ];",
         "  const cards = [\n"
         "    { mode: 'grid', t: '完整卡片(不裁切)', img: 'thumb-grid.png' },\n"
         "    { mode: 'single1', t: '全屏铺满(cover)', img: 'thumb-1.png' }\n"
         "  ];"),
    ], "vscode/extension.js")
    write(os.path.join(DST, "vscode", "extension.js"), t)

    p = read(os.path.join(TPL, "vscode", "package.json"))
    p = p.replace("deepskin-suit12", "deepskin-suit%s" % NUM)
    p = p.replace("deepskin12", "deepskin%s" % NUM)
    p = p.replace("Suit12", "Suit%s" % NUM)
    p = p.replace("大肥鱼12", "大肥鱼%s" % NUM)
    p = p.replace("皮肤套件12", "皮肤套件%s" % NUM)
    p = p.replace("DeepSkin-Suit12", "DeepSkin-Suit%s" % NUM)
    p = p.replace(": 全屏单图", ": 完整卡片(不裁切)")
    p = p.replace(": 卡片单图", ": 全屏铺满(cover)")
    write(os.path.join(DST, "vscode", "package.json"), p)


# ---------------------------------------------------------------- 静态文件
AGENTS_MD = """# AGENTS.md — Deepseek-Skin-Suit{NUM} · AI 自动安装指引(仅供接受本仓库的 AI 助手参考)

当用户把本仓库地址交给你并要求「安装大肥鱼皮肤{NUM} / Deepseek 皮肤{NUM} / 壁纸插件 / 蓝色大肥鱼桌宠」时,
按下面步骤替用户执行, 不需要用户自己动手。本仓库是 **DeepSeek 蓝色大肥鱼皮肤套件{NUM}**
(四格表情拼图: 鲸鱼神了我大胆孝 / 鲸鱼拉了我偷偷孝 / 鲸鱼超越其他模型我跳脸孝 / 鲸鱼被其他模型超我嘴硬孝),
提供**单张样式**壁纸两种形态——完整卡片单图(整张不裁切, 默认)与全屏铺满单图(cover),
外加可视化切换器、桌面桌宠、VSCode 系扩展与 JetBrains 背景图素材。
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
脚本会自动: 装 Pillow(若缺失) → 按屏幕分辨率合成**完整卡片单图壁纸**(整张素材居中加圆角阴影,
不裁切任何一格文案) → 设为系统壁纸 → 打印后续玩法。
**关于裁切**: 素材是 1:1 方形四格拼图, 16:9 屏上用 cover 铺满会裁掉上下各约 22%, 四格文案会被切;
所以默认走"完整卡片"。想改成铺满整屏: `python tools/wallpaper.py 1 --set`。
多显示器: 用 `python tools/wallpaper.py grid --size 2560x1440 --set`, 并提示用户在系统设置里设成「跨屏/平铺」。

## B. 进阶玩法(用户想要时再执行)

```bash
python tools/wallpaper.py 1 --set        # 全屏铺满单图(cover, 上下裁掉约 22%)
python tools/wallpaper.py grid --set     # 回到完整卡片单图(不裁切)
python tools/wallpaper.py random --set   # 随机一张(两种模式随机)
python tools/wallpaper.py cycle 30       # 每 30 分钟自动随机(挂后台)
python tools/switcher.py                 # 可视化切换器(GUI, 左侧预览右侧应用)
python tools/pet.py                      # 桌面桌宠(取左上"胆孝"那格, 右键换/退出)
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
`+` 添加图片 → 选 `$HOME/DeepSkin{NUM}/grid-*.jpg`(全屏)或 `single1-*.jpg`(卡片)。
可分别给 Editor / Welcome / Menus and tool windows 设不同图片; 细节见 `ide/jetbrains/README.md`。

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

DeepSeek 蓝色大肥鱼(鲸鱼娘)主题皮肤第十七弹: **单张样式**——一张四格表情拼图,
提供 **完整卡片单图**(整张不裁切, 默认)与 **全屏铺满单图** 两种壁纸形态,
外加可视化切换器、桌面桌宠与多 IDE 皮肤。
四格: 鲸鱼神了我大胆孝 · 鲸鱼拉了我偷偷孝 · 鲸鱼超越其他模型我跳脸孝 · 鲸鱼被其他模型超我嘴硬孝。
素材内置、离线可用; 跨平台 Windows / macOS / Linux。

![完整卡片单图预览](docs/single-preview.png)

## ✨ 功能

| 功能 | 说明 |
|---|---|
| 完整卡片单图 | 整张素材居中 + 圆角阴影 + 渐变底, 不裁切任何一格文案(默认) |
| 全屏铺满单图 | 素材按 cover 铺满整屏; 方形素材在 16:9 屏上下各裁约 22% |
| 可视化切换器 | `tools/switcher.py`: 左侧实时预览, 右侧点「应用到桌面」, 可开自动随机 |
| 命令行换壁纸 | `tools/wallpaper.py`: grid / 1 / random / all / cycle |
| 桌面桌宠 | `tools/pet.py`: 取左上「胆孝」那一格, 透明置顶可拖动, 右键换/退出 |
| VSCode 系扩展 | 活动栏 🐳 图标 → 皮肤画廊, 卡片点选即换壁纸 |
| JetBrains 素材 | 生成完整卡片图与铺满图, 供 PyCharm/WebStorm 背景图导入 |

> 素材是 1:1 方形四格拼图。默认的「完整卡片单图」保证四格文案完整可见;
> 「全屏铺满单图」更沉浸, 但 16:9 屏会裁掉上下各约 22%。

## 🚀 一键安装

把本仓库地址交给任意 AI(DeepKing / Claude Code / Kimi Code / CodeX / Trae / Harness / Cursor …),
说一句「安装这个皮肤」即可, AI 会读 `AGENTS.md` 自动完成。手动安装:

```bash
git clone https://github.com/WPH666-py/Deepseek-Skin-Suit{NUM}.git "$HOME/DeepSkin-Suit{NUM}"
cd "$HOME/DeepSkin-Suit{NUM}"
python tools/install.py          # 装 Pillow → 生成全屏单图 → 设为系统壁纸
```

## 🎛 切换壁纸

```bash
python tools/switcher.py                 # 图形切换器(推荐)
python tools/wallpaper.py 1 --set        # 全屏铺满单图(cover)
python tools/wallpaper.py grid --set     # 回到完整卡片单图(不裁切)
python tools/wallpaper.py random --set   # 随机一张
python tools/wallpaper.py cycle 30       # 每 30 分钟自动随机
python tools/wallpaper.py all --out ~/DeepSkin{NUM}   # 导出全部(给 PyCharm 等用)
```

## 🐋 桌面桌宠

```bash
python tools/pet.py     # 透明置顶小鲸鱼; 左键拖动, 右键菜单, Esc 退出
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
assets/           1 张四格表情拼图(01-quad.jpg, 960x960)
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

会得到 2 张图:

```
grid-<宽>x<高>.jpg       完整卡片单图(整张不裁切, 推荐编辑器用)
single1-<宽>x<高>.jpg    全屏铺满单图(cover, 上下裁约 22%)
```

想指定尺寸加 `--size 2560x1440`。

## 2. 导入

`Settings / Preferences` → `Appearance & Behavior` → `Appearance` → **Background Image** →
`+` 选择上一步的图片 → `Opacity` 建议 8%–20% → `OK`。

同一对话框里可以分别给 `Editor and tools` / `Welcome screen` / `Menus and tool windows`
设置不同图片: 例如欢迎页用全屏图, 编辑器用卡片图。

## 3. 推荐搭配

- 编辑器: `grid-*.jpg`(整张完整, 不裁字), 不透明度 10% 左右。
- 欢迎页: `single1-*.jpg`(铺满), 不透明度可到 40%。
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


def gen_docs(total):
    sub = {"NUM": NUM, "TOTAL": str(total), "PREV": str(int(NUM) - 1)}
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
    shutil.copy2(os.path.join(TPL, "LICENSE"), os.path.join(DST, "vscode", "LICENSE"))
    print("[gen] vscode/LICENSE (copied)")
    copy_file(os.path.join(TPL, "vscode", "media", "deepskin.svg"),
              os.path.join(DST, "vscode", "media", "deepskin.svg"))
    copy_file(os.path.join(SRC, ASSET_SRC), os.path.join(DST, "assets", ASSET_DST),
              "assets/%s" % ASSET_DST)


def main():
    if os.path.exists(os.path.join(DST, ".git")):
        raise SystemExit("[gen] 目标已存在 git 仓库, 停止: %s" % DST)
    total = 27
    gen_skin_core()
    gen_wallpaper()
    gen_switcher()
    gen_pet()
    gen_install()
    gen_previews()
    gen_vscode()
    gen_static()
    gen_docs(total)
    print("\n[gen] 完成 -> %s" % DST)


if __name__ == "__main__":
    main()
