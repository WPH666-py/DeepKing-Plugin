# -*- coding: utf-8 -*-
"""生成 Deepseek-Skin-Suit15 仓库(以 Suit14 为模板做参数化改写)。

用法: python _suit15-src/gen_suit15.py
产物: D:\\projects-py\\DeepKing-Plugin\\Deepseek-Skin-Suit15
"""
import os
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
TPL = os.path.join(HERE, "tpl")
SRC = os.path.join(HERE)  # 图片素材(已算好方形)
DST = os.path.join(ROOT, "Deepseek-Skin-Suit15")

SLUG = "Suit15"
NUM = "15"

# 素材: 源文件 -> 目标文件名
IMAGES = [
    ("img1-ask.jpg", "01-ask.jpg"),
    ("img2-dsh.jpg", "02-dsh.jpg"),
    ("img3-what.jpg", "03-suspicious.jpg"),
    ("img4-think.jpg", "04-thinking.jpg"),
]
IMAGE_FILES = [d for _s, d in IMAGES]
IMAGE_NAMES = [
    "你愿意和我…吗?",
    "DSH? DeepSeek Hentai?",
    "你目录里的dsh是什么…大烧货吗?",
    "正在思考…",
]


def patch(text, pairs, label):
    """按序做精确替换; 每次替换必须命中, 否则报错。"""
    for old, new in pairs:
        if old not in text:
            raise SystemExit("[gen] %s: 未找到待替换片段:\n%s" % (label, old[:160]))
        text = text.replace(old, new)
    return text


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    print("[gen] %s (%d bytes)" % (os.path.relpath(path, ROOT), len(text.encode("utf-8"))))


def read(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


# ------------------------------------------------------------------ skin_core
def gen_skin_core():
    t = read(os.path.join(TPL, "tools", "skin_core.py"))
    t = patch(t, [
        ('"""\nDeepSeek 蓝色大肥鱼 · 皮肤套件 —— 核心库',
         '"""\nDeepSeek 蓝色大肥鱼 · 皮肤套件15 —— 核心库'),
        ('APP_DIR = os.path.join(os.path.expanduser("~"), ".deepskin14")',
         'APP_DIR = os.path.join(os.path.expanduser("~"), ".deepskin15")'),
        ('IMAGE_FILES = ["01-ask.jpg", "02-think.jpg", "03-smug.jpg", "04-good.jpg"]',
         'IMAGE_FILES = ["%s"]' % '", "'.join(IMAGE_FILES)),
        ('IMAGE_NAMES = [\n    "你愿意和我…吗",\n    "已思考13秒: 我不知道耶",\n    "就骚了, 怎么滴吧!",\n    "好模型",\n]',
         'IMAGE_NAMES = [\n' + "".join('    "%s",\n' % n for n in IMAGE_NAMES) + ']'),
        ('# 拼贴布局: Suit14 = 紧贴式 2×2(两行两列), 格子宽高比自动取素材平均比例(方图配方格)',
         '# 拼贴布局: Suit15 = 紧贴式 2×2(两行两列), 格子宽高比自动取素材平均比例(方图配方格)'),
    ], "tools/skin_core.py")
    write(os.path.join(DST, "tools", "skin_core.py"), t)


# ------------------------------------------------------------------ wallpaper
def gen_wallpaper():
    t = read(os.path.join(TPL, "tools", "wallpaper.py"))
    t = patch(t, [
        ('DeepSeek 蓝色大肥鱼 · 皮肤套件 —— 壁纸命令行',
         'DeepSeek 蓝色大肥鱼 · 皮肤套件15 —— 壁纸命令行'),
        ('python tools/wallpaper.py 1 --set               # 生成并设置单图 1(摸摸头)',
         'python tools/wallpaper.py 1 --set               # 生成并设置单图 1(你愿意和我…吗)'),
        ('python tools/wallpaper.py all --size 1920x1080  # 生成全部 5 种到 ~/.deepskin/wallpapers',
         'python tools/wallpaper.py all --size 1920x1080  # 生成全部 5 种到 ~/.deepskin15/wallpapers'),
        ('ap = argparse.ArgumentParser(description="DeepSeek 大肥鱼壁纸工具")',
         'ap = argparse.ArgumentParser(description="DeepSeek 大肥鱼15 壁纸工具")'),
    ], "tools/wallpaper.py")
    write(os.path.join(DST, "tools", "wallpaper.py"), t)


# ------------------------------------------------------------------ switcher
def gen_switcher():
    t = read(os.path.join(TPL, "tools", "switcher.py"))
    t = patch(t, [
        ('DeepSeek 蓝色大肥鱼 · 皮肤套件 —— 可视化切换器',
         'DeepSeek 蓝色大肥鱼 · 皮肤套件15 —— 可视化切换器'),
        ('root.title("DeepSeek 大肥鱼 · 皮肤切换器")',
         'root.title("DeepSeek 大肥鱼15 · 皮肤切换器")'),
    ], "tools/switcher.py")
    write(os.path.join(DST, "tools", "switcher.py"), t)


# ------------------------------------------------------------------ pet
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
        edge = 1 if attempt == 0 else 0  # 第一次先避开 JPEG 边缘 1px 噪点
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
        # 泛洪吃掉了太多(底色渐变把角色也带走了): 退回"与全局底色比色"再试一次
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
    """从模板源码里整段取出一个顶层函数(到下一个顶层 def / 文件末)。"""
    start = src.index("def %s(" % name)
    nxt = src.find("\ndef ", start + 1)
    return src[start:nxt if nxt != -1 else len(src)]


def gen_pet():
    t = read(os.path.join(TPL, "tools", "pet.py"))
    old_modes = (
        'MODES = [\n'
        '    ("01-ask", "你愿意和我…"),\n'
        '    ("02-think", "我不知道耶"),\n'
        '    ("03-smug", "就骚了"),\n'
        '    ("04-good", "好模型"),\n'
        ']'
    )
    new_modes = 'MODES = [\n' + "".join(
        '    ("%s", "%s"),\n' % (f[:-4], n) for f, n in zip(IMAGE_FILES, IMAGE_NAMES)
    ) + ']'
    t = patch(t, [
        ('DeepSeek 蓝色大肥鱼 · 皮肤套件 —— 桌面桌宠',
         'DeepSeek 蓝色大肥鱼 · 皮肤套件15 —— 桌面桌宠'),
        ('  • 右键菜单: 切换 4 种表情 / 随机 / 打开皮肤切换器 / 退出',
         '  • 右键菜单: 切换 4 张表情卡 / 随机 / 打开皮肤切换器 / 退出'),
        (old_modes, new_modes),
        ('SLEEP_STEM = "04-good"  # 眼汪汪看你的图: 慢慢晃',
         'SLEEP_STEM = "04-thinking"  # 思考中的图: 轻轻起伏'),
        # 素材底色有纯白/浅灰/米白三种, 固定白阈值去不干净 -> 改成按四角采样自适应
        ('# 非白底素材(如蓝色水景)不做泛洪去底, 改用方形取景裁剪:\n'
         '# {stem: (中心x比例, 中心y比例, 半边长占最短边比例)}\n'
         'PET_CROPS = {}',
         '# 素材为方图且角色居中, 无需额外取景裁剪:\n'
         '# {stem: (中心x比例, 中心y比例, 半边长占最短边比例)}\n'
         'PET_CROPS = {}\n'
         '# 去底容差(颜色距离): 素材底色含纯白 / 浅灰 / 米白, 由四角采样自适应\n'
         'BG_TOL = 26\n'
         '# 只有亮度不低于此值的像素才可能被判为底色(保护角色深色描边与阴影)\n'
         'BG_BRIGHT = 168'),
        (cut_function(t, "cut_white_bg"), NEW_CUT),
    ], "tools/pet.py")
    write(os.path.join(DST, "tools", "pet.py"), t)


# ------------------------------------------------------------------ install
def gen_install():
    t = read(os.path.join(TPL, "tools", "install.py"))
    t = patch(t, [
        ('DeepSeek 蓝色大肥鱼 · 皮肤套件 —— 一键安装',
         'DeepSeek 蓝色大肥鱼 · 皮肤套件15 —— 一键安装'),
        ('print("  DeepSeek 蓝色大肥鱼 · 皮肤套件 安装器")',
         'print("  DeepSeek 蓝色大肥鱼 · 皮肤套件15 安装器")'),
        ('print("  • VSCode/Trae/CodeX:   vscode/ 目录扩展, 见 README.md")',
         'print("  • VSCode/Trae/CodeX:   vscode/deepskin-suit15-0.1.0.vsix")'),
    ], "tools/install.py")
    write(os.path.join(DST, "tools", "install.py"), t)


# ------------------------------------------------------------------ previews
def gen_previews():
    t = read(os.path.join(TPL, "tools", "make_previews.py"))
    write(os.path.join(DST, "tools", "make_previews.py"), t)


# ------------------------------------------------------------------ vscode
def gen_vscode():
    t = read(os.path.join(TPL, "vscode", "extension.js"))
    t = t.replace("deepskin-suit14", "deepskin-suit15")
    t = t.replace("deepskin14", "deepskin15")
    t = t.replace("Suit14", "Suit15")
    t = t.replace("大肥鱼14", "大肥鱼15")
    t = t.replace("皮肤套件14", "皮肤套件15")
    t = t.replace("DeepSkin-Suit14", "DeepSkin-Suit15")
    cards_old = (
        "  const cards = [\n"
        "    { mode: 'grid', t: '2×2 拼贴', img: 'thumb-grid.png' },\n"
        "    { mode: 'single1', t: '你愿意和我…', img: 'thumb-1.png' },\n"
        "    { mode: 'single2', t: '我不知道耶', img: 'thumb-2.png' },\n"
        "    { mode: 'single3', t: '就骚了', img: 'thumb-3.png' },\n"
        "    { mode: 'single4', t: '好模型', img: 'thumb-4.png' }\n"
        "  ];"
    )
    cards_new = (
        "  const cards = [\n"
        "    { mode: 'grid', t: '2×2 拼贴', img: 'thumb-grid.png' },\n"
        "    { mode: 'single1', t: '你愿意和我…吗?', img: 'thumb-1.png' },\n"
        "    { mode: 'single2', t: 'DeepSeek Hentai?', img: 'thumb-2.png' },\n"
        "    { mode: 'single3', t: '大烧货吗?', img: 'thumb-3.png' },\n"
        "    { mode: 'single4', t: '正在思考…', img: 'thumb-4.png' }\n"
        "  ];"
    )
    t = patch(t, [(cards_old, cards_new)], "vscode/extension.js")
    write(os.path.join(DST, "vscode", "extension.js"), t)

    p = read(os.path.join(TPL, "vscode", "package.json"))
    p = p.replace("deepskin-suit14", "deepskin-suit15")
    p = p.replace("deepskin14", "deepskin15")
    p = p.replace("Suit14", "Suit15")
    p = p.replace("大肥鱼14", "大肥鱼15")
    for old, new in [
        ("你愿意和我…", "你愿意和我…吗?"),
        ("我不知道耶", "DeepSeek Hentai?"),
        ("就骚了", "大烧货吗?"),
        ("好模型", "正在思考…"),
    ]:
        p = p.replace(old, new)
    write(os.path.join(DST, "vscode", "package.json"), p)


def copy_file(src, dst, label=None):
    """复制并清掉只读位(素材来自只读附件库时, 直接复制会带 ReadOnly 属性)。"""
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copyfile(src, dst)
    os.chmod(dst, 0o644)
    print("[gen] %s (copied)" % (label or os.path.relpath(dst, DST)))


def gen_static():
    for name in (".gitignore", "LICENSE"):
        shutil.copy2(os.path.join(TPL, name), os.path.join(DST, name))
        print("[gen] %s (copied)" % name)
    # .gitignore 追加: 扩展的中间打包产物(正式 vsix 随仓库发布)
    with open(os.path.join(DST, ".gitignore"), "a", encoding="utf-8") as f:
        f.write("\n# 打包中间产物(正式 vsix 随仓库提交)\n*.vsix.tmp\n.vscodeignore.bak\n")
    print("[gen] .gitignore (+vsix 中间产物)")
    # 扩展目录也放一份 LICENSE(vsce 打包时会检查)
    shutil.copy2(os.path.join(TPL, "LICENSE"), os.path.join(DST, "vscode", "LICENSE"))
    print("[gen] vscode/LICENSE (copied)")
    # VSCode 活动栏图标(svg)直接复用鲸鱼图形; icon.png 由 make_previews.py 生成
    copy_file(os.path.join(TPL, "vscode", "media", "deepskin.svg"),
              os.path.join(DST, "vscode", "media", "deepskin.svg"))
    for src, dst in IMAGES:
        copy_file(os.path.join(SRC, src), os.path.join(DST, "assets", dst),
                  "assets/%s" % dst)


# ------------------------------------------------------------------ 文本文件
AGENTS_MD = """# AGENTS.md — Deepseek-Skin-Suit15 · AI 自动安装指引(仅供接受本仓库的 AI 助手参考)

当用户把本仓库地址交给你并要求「安装大肥鱼皮肤15 / Deepseek 皮肤15 / 壁纸插件 / 蓝色大肥鱼桌宠」时,
按下面步骤替用户执行, 不需要用户自己动手。本仓库是 **DeepSeek 蓝色大肥鱼皮肤套件15**
(四张表情卡: 你愿意和我…吗? / DSH? DeepSeek Hentai? / 你目录里的dsh是什么…大烧货吗? / 正在思考…),
提供紧贴式 2×2 拼贴壁纸、4 张单图壁纸、可视化切换器、桌面桌宠、VSCode 系扩展与 JetBrains 背景图素材。
核心脚本在 `tools/`, 素材在 `assets/`。

## 第 0 步: 下载与定位

```bash
git clone https://github.com/WPH666-py/Deepseek-Skin-Suit15.git "$HOME/DeepSkin-Suit15"
cd "$HOME/DeepSkin-Suit15"
```
Windows 建议固定克隆到 `%USERPROFILE%\\DeepSkin-Suit15`(VSCode 扩展默认在此查找)。
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
格子宽高比按素材自动计算)→ 设为系统壁纸 → 打印后续玩法。
多显示器: 用 `python tools/wallpaper.py grid --size 2560x1440 --set` 生成指定尺寸,
并提示用户在系统设置里把壁纸设为「跨屏 / 平铺」。

## B. 进阶玩法(用户想要时再执行)

```bash
python tools/wallpaper.py 1 --set        # 单图 1(你愿意和我…吗?)
python tools/wallpaper.py 2 --set        # 单图 2(DeepSeek Hentai?)
python tools/wallpaper.py 3 --set        # 单图 3(大烧货吗?)
python tools/wallpaper.py 4 --set        # 单图 4(正在思考…)
python tools/wallpaper.py random --set   # 随机一张(拼贴或单图)
python tools/wallpaper.py cycle 30       # 每 30 分钟自动随机(挂后台)
python tools/switcher.py                 # 可视化切换器(GUI, 左侧预览右侧应用)
python tools/pet.py                      # 桌面桌宠(右键换表情)
```
GUI 命令需要本地图形会话; 若用户是远程/无桌面环境, 告知其改在有桌面的机器上运行。
**用户要求「支持切换壁纸」时, 优先引导 `switcher.py`(点选即换), 或 `wallpaper.py random/cycle`。**

## C. VSCode / Trae / CodeX 扩展

1. 安装(已预打包, 无需 Node):
   `code --install-extension "$HOME/DeepSkin-Suit15/vscode/deepskin-suit15-0.1.0.vsix"`
   无网时把 `vscode/` 整个目录复制到 `%USERPROFILE%\\.vscode\\extensions\\wp666.deepskin-suit15-0.1.0\\` 后重启编辑器
   (Trae / CodeX 的扩展目录同理)。
2. 告知用户: 活动栏 🐳 **大肥鱼15** 图标 → 皮肤画廊 → 点「设为壁纸」;
   命令面板搜 `大肥鱼15` 可换壁纸 / 开切换器 / 起桌宠。
3. 扩展自动查找 Python 与仓库路径(可用 `deepskin15.repoPath` 覆盖), Pillow 缺失时自动 pip 安装。
4. 与 Suit1-14 及 AI 全家桶系列可同时安装: 插件 ID / 命令前缀 / 运行时目录(`~/.deepskin15`)互不冲突。

## D. PyCharm / WebStorm / IntelliJ(JetBrains)

```bash
python tools/wallpaper.py all --out "$HOME/DeepSkin15"
```
然后引导用户: Settings / Preferences → Appearance & Behavior → Appearance → **Background Image** →
`+` 添加图片 → 选 `$HOME/DeepSkin15/grid-*.jpg`(或任一单图)。可分别给 Editor / Welcome /
Menus and tool windows 设不同图片; 细节见 `ide/jetbrains/README.md`。

## 约定与失败处理

- 只依赖 `tools/` 与 `assets/`; 生成物写入 `~/.deepskin15/`, **不会**改动仓库文件。
- Windows 控制台若出现 GBK/Unicode 编码错误: `chcp 65001` 后重跑(脚本已内置 UTF-8 兜底)。
- 找不到 Python(常见于 Store 版): 用完整路径
  `C:\\Users\\<user>\\AppData\\Local\\Programs\\Python\\Python311\\python.exe` 运行。
- 高分辨率屏合成慢: 允许 `--size 1920x1080` 降到 1080p。
- 素材或脚本更新后会自动重新合成(热更新), 无需手动删缓存。
- 个别 Linux 桌面不支持窗口透明色, 桌宠会退化成白底卡片, 属平台限制, 如实告知用户。
- 用户问与 DeepKing 本体的关系: 这是独立皮肤套件, 与 DeepKing 本体互不影响;
  装了 DeepKing-Plugin 的用户直接在它的 AI 对话里发本仓库链接就能完成安装。
- 皮肤总目录(24+ 套)与 pip 包: https://github.com/WPH666-py/Desktop-IDE-AI-Skin
"""

README_MD = """# 🐳 DeepSeek 蓝色大肥鱼 · 皮肤套件15 (Deepseek-Skin-Suit15)

DeepSeek 蓝色大肥鱼(鲸鱼娘)主题皮肤第十五弹: **紧贴式 2×2 拼贴壁纸 / 4 张单图壁纸一键切换 /
可视化切换器 / 桌面桌宠 / 多 IDE 皮肤**。
表情: 你愿意和我…吗? · DSH? DeepSeek Hentai? · 你目录里的dsh是什么…大烧货吗? · 正在思考…。
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
git clone https://github.com/WPH666-py/Deepseek-Skin-Suit15.git "$HOME/DeepSkin-Suit15"
cd "$HOME/DeepSkin-Suit15"
python tools/install.py          # 装 Pillow → 生成 2×2 拼贴 → 设为系统壁纸
```

## 🎛 切换壁纸

```bash
python tools/switcher.py                 # 图形切换器(推荐)
python tools/wallpaper.py 1 --set        # 你愿意和我…吗?
python tools/wallpaper.py 2 --set        # DeepSeek Hentai?
python tools/wallpaper.py 3 --set        # 大烧货吗?
python tools/wallpaper.py 4 --set        # 正在思考…
python tools/wallpaper.py grid --set     # 回到 2×2 拼贴
python tools/wallpaper.py random --set   # 随机一张
python tools/wallpaper.py cycle 30       # 每 30 分钟自动随机
python tools/wallpaper.py all --out ~/DeepSkin15   # 导出全部 5 张(给 PyCharm 等用)
```

## 🐋 桌面桌宠

```bash
python tools/pet.py     # 透明置顶小鲸鱼; 左键拖动, 右键切换表情/随机/开切换器, Esc 退出
```

## 🧩 IDE 集成

- **VSCode / Trae / CodeX**: `code --install-extension vscode/deepskin-suit15-0.1.0.vsix`
  → 活动栏 🐳「大肥鱼15」→ 皮肤画廊 → 「设为壁纸」。无网时把 `vscode/` 复制到
  `%USERPROFILE%\\.vscode\\extensions\\wp666.deepskin-suit15-0.1.0\\` 并重启。
- **PyCharm / WebStorm / IntelliJ**: `python tools/wallpaper.py all --out ~/DeepSkin15`,
  再在 Settings → Appearance → Background Image 里选图, 详见 `ide/jetbrains/README.md`。
- **DeepKing 本体**: 本仓库是独立皮肤套件, 与 DeepKing 本体互不影响;
  在 DeepKing 的 AI 对话里发本仓库链接即可自动安装。

## 📦 皮肤总目录 / pip 包

- 皮肤大全(24+ 套, 含 AI 全家桶系列): https://github.com/WPH666-py/Desktop-IDE-AI-Skin
- pip 包: `pip install deepskins` → `deepskins list` / `deepskins install deepseek-15`

## 📁 目录结构

```
assets/           4 张表情素材(01-ask / 02-dsh / 03-suspicious / 04-thinking)
tools/            install.py 一键安装 · wallpaper.py 命令行 · switcher.py 切换器 · pet.py 桌宠
vscode/           预打包 VSCode/Trae/CodeX 扩展(deepskin-suit15-0.1.0.vsix)
ide/jetbrains/    PyCharm 等背景图导入说明
docs/             预览图(由 tools/make_previews.py 生成)
```

## ⚠️ 说明

- 生成物写入 `~/.deepskin15/`(壁纸与缓存), 不改动仓库内容; 素材更新后自动重新合成。
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
python tools/wallpaper.py all --out "$HOME/DeepSkin15"
```

会得到 5 张图(2×2 拼贴 + 4 张单图):

```
grid-<宽>x<高>.jpg       2×2 拼贴
single1-<宽>x<高>.jpg    你愿意和我…吗?
single2-<宽>x<高>.jpg    DSH? DeepSeek Hentai?
single3-<宽>x<高>.jpg    你目录里的dsh是什么…大烧货吗?
single4-<宽>x<高>.jpg    正在思考…
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
- 想换表情: 重新运行 `python tools/wallpaper.py all --out "$HOME/DeepSkin15"` 后再选另一张即可。
"""

INSTALL_BAT = """@echo off
chcp 65001 >nul
echo ============================================
echo   DeepSeek 蓝色大肥鱼 · 皮肤套件15 安装
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
echo "  DeepSeek 蓝色大肥鱼 · 皮肤套件15 安装"
echo "============================================"
if command -v python3 >/dev/null 2>&1; then PY=python3; else PY=python; fi
"$PY" "$(dirname "$0")/tools/install.py"
"""


def gen_docs():
    write(os.path.join(DST, "AGENTS.md"), AGENTS_MD)
    write(os.path.join(DST, "README.md"), README_MD)
    write(os.path.join(DST, "ide", "jetbrains", "README.md"), JETBRAINS_MD)
    write(os.path.join(DST, "install.bat"), INSTALL_BAT)
    write(os.path.join(DST, "install.sh"), INSTALL_SH)


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
