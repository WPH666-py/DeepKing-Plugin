# -*- coding: utf-8 -*-
"""由 gen_suit17.py(基线)派生出 gen_suit20.py。

做法: 以 _suit20-src/gen_suit17_base.py 为输入, 逐条做"必须命中且唯一"的字符串替换,
写出 gen_suit20.py。所有改写集中在本文件的 PAIRS / 两个辅助函数里, 一目了然。

Suit20 与 Suit17/19 的区别:
  * 素材 1104x630 ≈ 16:9, 与屏幕同形 -> cover 铺满几乎不裁切(上下各约 1%),
    因此恢复单张样式的惯例默认: grid = 全屏 cover, single1 = 卡片单图;
  * 素材是夜景插画(带背景), 桌宠取人物区域。

用法: python _suit20-src/make_gen20.py
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "gen_suit17_base.py")
DST = os.path.join(HERE, "gen_suit20.py")

# (旧文本, 新文本, 期望次数)
PAIRS = [
    # ---------------------------------------------------------------- 头部
    ("生成 Deepseek-Skin-Suit17 仓库。",
     "生成 Deepseek-Skin-Suit20 仓库。", 1),
    ('模板: _suit17-src/tpl/(取自 Suit12 的"单张样式"套件)',
     '模板: _suit20-src/tpl/(取自 Suit12 的"单张样式"套件)', 1),
    ("脚本与文档都按 Suit17 显式写出(不再靠对上一套做链式替换, 避免文案串味)。",
     "脚本与文档都按 Suit20 显式写出(不再靠对上一套做链式替换, 避免文案串味)。", 1),
    ("用法: python _suit17-src/gen_suit17.py",
     "用法: python _suit20-src/gen_suit20.py", 1),
    ("产物: D:\\\\projects-py\\\\DeepKing-Plugin\\\\Deepseek-Skin-Suit17",
     "产物: D:\\\\projects-py\\\\DeepKing-Plugin\\\\Deepseek-Skin-Suit20", 1),
    ('DST = os.path.join(ROOT, "Deepseek-Skin-Suit17")',
     'DST = os.path.join(ROOT, "Deepseek-Skin-Suit20")', 1),
    ('NUM = "17"', 'NUM = "20"', 1),

    # ---------------------------------------------------------------- 素材参数
    ('ASSET_SRC = "img1-quad.jpg"          # 素材源(四格拼图, 960x960)',
     'ASSET_SRC = "img1-village.jpg"       # 素材源(夜景插画, 1104x630 = 16:9)', 1),
    ('ASSET_DST = "01-quad.jpg"            # 仓库内文件名',
     'ASSET_DST = "01-village.jpg"         # 仓库内文件名', 1),
    ('ASSET_STEM = "01-quad"', 'ASSET_STEM = "01-village"', 1),
    ('WALLPAPER_NAME = "鲸鱼四连(2×2 四格)"',
     'WALLPAPER_NAME = "苗寨灯火(16:9 宽幅)"', 1),
    ('PET_NAME = "鲸鱼娘"', 'PET_NAME = "苗寨灯火"', 1),
    ('# 桌宠: 四格拼图里取左上"胆孝"那一格(方形取景, 角色居中且不带格线)',
     '# 桌宠: 取人物区域(方形取景; 夜景插画无白底可抠)', 1),
    ('PET_CROP = (0.26, 0.26, 0.18)        # (中心x比例, 中心y比例, 半边长占最短边比例)',
     'PET_CROP = (0.70, 0.62, 0.46)        # (中心x比例, 中心y比例, 半边长占最短边比例)', 1),
    ('"GRID_FIT = True  # True: grid=完整卡片(不裁切); False: grid=全屏单图(cover)\\n"',
     '"GRID_FIT = False  # False: grid=全屏铺满(cover; 本套素材同形几乎不裁切)\\n"', 1),

    # ------------------------------------------------- skin_core 注释(docstring/模式名见辅助函数)
    ('"# 单张样式。素材是 1:1 方形, 在 16:9 屏上 cover 会裁掉上下各约 22%(四格文案会被切),\\n"',
     '"# 单张样式: 素材 1104x630 与屏幕同形, grid = cover 铺满(几乎不裁切),\\n"', 1),
    ('"# 因此默认 grid = 完整卡片(适合屏幕), single1 = 全屏铺满(cover)。\\n"',
     '"# single1 = 卡片单图(模糊填充 + 圆角卡片)。\\n"', 1),
    ('"# 想换回 Suit12 那种默认, 把 GRID_FIT 改成 False 即可。"',
     '"# 想改成整张不裁切的完整卡片: 把 GRID_FIT 改成 True。"', 1),
    ("    方形/竖版素材在 16:9 屏幕上 cover 会裁掉约 22% 的高度, 四格文案会被切;",
     "    方形/竖版素材在 16:9 屏幕上 cover 会裁掉约 22% 的高度, 大字会被切;", 1),
    ('("DeepSeek 蓝色大肥鱼 · 皮肤套件 —— 核心库",',
     '("DeepSeek 蓝色大肥鱼 · 皮肤套件 —— 核心库",', 1),

    # ---------------------------------------------------------------- wallpaper 文档
    ('"  python tools/wallpaper.py grid --set            # 生成并设置完整卡片单图(默认, 不裁切)"',
     '"  python tools/wallpaper.py grid --set            # 生成并设置全屏铺满单图(默认, cover)"', 1),
    ('"  python tools/wallpaper.py 1 --set               # 生成并设置全屏单图(cover 铺满, 上下裁切)"',
     '"  python tools/wallpaper.py 1 --set               # 生成并设置卡片单图(模糊填充 + 圆角)"', 1),

    # ---------------------------------------------------------------- pet 注释
    ('\'SLEEP_STEM = "%s"  # 四格拼图取景: 慢慢晃\' % ASSET_STEM),',
     '\'SLEEP_STEM = "%s"  # 人物区域取景: 慢慢晃\' % ASSET_STEM),', 1),
    ('"# 四格拼图整张不好抠: 取景裁剪出左上「胆孝」那一格做桌宠贴图\\n"',
     '"# 夜景插画没有白底可抠: 取景裁剪出人物区域\\n"', 1),

    # ---------------------------------------------------------------- install / vscode
    ('"  • 全屏铺满单图:         python tools/wallpaper.py 1 --set"',
     '"  • 卡片单图:             python tools/wallpaper.py 1 --set"', 1),
    ('"    { mode: \'grid\', t: \'完整卡片(不裁切)\', img: \'thumb-grid.png\' },\\n"',
     '"    { mode: \'grid\', t: \'全屏铺满(cover)\', img: \'thumb-grid.png\' },\\n"', 1),
    ('"    { mode: \'single1\', t: \'全屏铺满(cover)\', img: \'thumb-1.png\' }\\n"',
     '"    { mode: \'single1\', t: \'卡片单图\', img: \'thumb-1.png\' }\\n"', 1),
    ('    p = p.replace(": 全屏单图", ": 完整卡片(不裁切)")',
     '    p = p.replace(": 全屏单图", ": 全屏铺满(cover)")', 1),
    ('    p = p.replace(": 卡片单图", ": 全屏铺满(cover)")',
     '    p = p.replace(": 卡片单图", ": 卡片单图(模糊填充)")', 1),

    # ---------------------------------------------------------------- AGENTS 文档
    ("(四格表情拼图: 鲸鱼神了我大胆孝 / 鲸鱼拉了我偷偷孝 / 鲸鱼超越其他模型我跳脸孝 / 鲸鱼被其他模型超我嘴硬孝),",
     "(夜景插画: 鲸鱼娘着苗银盛装, 倚在吊脚楼栏杆边眺望万家灯火),", 1),
    ("提供**单张样式**壁纸两种形态——完整卡片单图(整张不裁切, 默认)与全屏铺满单图(cover),",
     "提供**单张样式**壁纸两种形态——全屏铺满单图(cover, 默认)与卡片单图(模糊填充),", 1),
    ("脚本会自动: 装 Pillow(若缺失) → 按屏幕分辨率合成**完整卡片单图壁纸**(整张素材居中加圆角阴影,\n不裁切任何一格文案) → 设为系统壁纸 → 打印后续玩法。",
     "脚本会自动: 装 Pillow(若缺失) → 按屏幕分辨率合成**全屏铺满单图壁纸**(cover 铺满整屏)\n→ 设为系统壁纸 → 打印后续玩法。", 1),
    ("**关于裁切**: 素材是 1:1 方形四格拼图, 16:9 屏上用 cover 铺满会裁掉上下各约 22%, 四格文案会被切;\n所以默认走\"完整卡片\"。想改成铺满整屏: `python tools/wallpaper.py 1 --set`。",
     "**关于裁切**: 素材是 1104x630(约 16:9), 与常见屏幕同形, cover 铺满时上下各只裁约 1%。\n想改成整张居中不裁切的卡片样式: `python tools/wallpaper.py 1 --set`。", 1),
    ("python tools/wallpaper.py 1 --set        # 全屏铺满单图(cover, 上下裁掉约 22%)\npython tools/wallpaper.py grid --set     # 回到完整卡片单图(不裁切)",
     "python tools/wallpaper.py 1 --set        # 卡片单图(整张居中 + 模糊填充)\npython tools/wallpaper.py grid --set     # 回到全屏铺满(cover)", 1),
    ('python tools/pet.py                      # 桌面桌宠(取左上"胆孝"那格, 右键换/退出)',
     'python tools/pet.py                      # 桌面桌宠(取人物区域, 右键换/退出)', 1),

    # ---------------------------------------------------------------- README 文档
    ("DeepSeek 蓝色大肥鱼(鲸鱼娘)主题皮肤第十七弹: **单张样式**——一张四格表情拼图,",
     "DeepSeek 蓝色大肥鱼(鲸鱼娘)主题皮肤第二十弹: **单张样式**——一张夜景宽幅插画,", 1),
    ("提供 **完整卡片单图**(整张不裁切, 默认)与 **全屏铺满单图** 两种壁纸形态,",
     "提供 **全屏铺满单图**(cover, 默认)与 **卡片单图**(模糊填充 + 圆角卡片)两种壁纸形态,", 1),
    ("四格: 鲸鱼神了我大胆孝 · 鲸鱼拉了我偷偷孝 · 鲸鱼超越其他模型我跳脸孝 · 鲸鱼被其他模型超我嘴硬孝。",
     "画面: 鲸鱼娘着苗银盛装, 倚在吊脚楼栏杆边, 眺望山下万家灯火与夜色群山。", 1),
    ("![完整卡片单图预览](docs/single-preview.png)",
     "![全屏单图预览](docs/single-preview.png)", 1),
    ("| 完整卡片单图 | 整张素材居中 + 圆角阴影 + 渐变底, 不裁切任何一格文案(默认) |",
     "| 全屏铺满单图 | 素材按 cover 铺满整屏(默认; 1104x630 与屏幕同形, 几乎不裁切) |", 1),
    ("| 全屏铺满单图 | 素材按 cover 铺满整屏; 方形素材在 16:9 屏上下各裁约 22% |",
     "| 卡片单图 | 整张素材居中 + 圆角卡片 + 模糊填充背景 |", 1),
    ("| 桌面桌宠 | `tools/pet.py`: 取左上「胆孝」那一格, 透明置顶可拖动, 右键换/退出 |",
     "| 桌面桌宠 | `tools/pet.py`: 取人物区域, 透明置顶可拖动, 右键换/退出 |", 1),
    ("| JetBrains 素材 | 生成完整卡片图与铺满图, 供 PyCharm/WebStorm 背景图导入 |",
     "| JetBrains 素材 | 生成全屏铺满图与卡片图, 供 PyCharm/WebStorm 背景图导入 |", 1),
    ("> 素材是 1:1 方形四格拼图。默认的「完整卡片单图」保证四格文案完整可见;\n> 「全屏铺满单图」更沉浸, 但 16:9 屏会裁掉上下各约 22%。",
     "> 素材是 1104x630(约 16:9), 与常见屏幕同形, 默认的「全屏铺满」上下各只裁约 1%;\n> 想让整张原封不动显示, 用「卡片单图」。", 1),
    ("python tools/wallpaper.py 1 --set        # 全屏铺满单图(cover)\npython tools/wallpaper.py grid --set     # 回到完整卡片单图(不裁切)",
     "python tools/wallpaper.py 1 --set        # 卡片单图(模糊填充)\npython tools/wallpaper.py grid --set     # 回到全屏铺满(cover)", 1),
    ("assets/           1 张四格表情拼图(01-quad.jpg, 960x960)",
     "assets/           1 张夜景宽幅插画(01-village.jpg, 1104x630)", 1),
    ("python tools/install.py          # 装 Pillow → 生成全屏单图 → 设为系统壁纸",
     "python tools/install.py          # 装 Pillow → 生成全屏铺满 → 设为系统壁纸", 1),

    # ---------------------------------------------------------------- JetBrains 文档
    ("grid-<宽>x<高>.jpg       完整卡片单图(整张不裁切, 推荐编辑器用)\nsingle1-<宽>x<高>.jpg    全屏铺满单图(cover, 上下裁约 22%)",
     "grid-<宽>x<高>.jpg       全屏铺满单图(cover, 默认)\nsingle1-<宽>x<高>.jpg    卡片单图(整张居中 + 模糊填充)", 1),
    ("- 编辑器: `grid-*.jpg`(整张完整, 不裁字), 不透明度 10% 左右。\n- 欢迎页: `single1-*.jpg`(铺满), 不透明度可到 40%。",
     "- 编辑器: `single1-*.jpg`(整张居中, 背景不抢注意力), 不透明度 10% 左右。\n- 欢迎页: `grid-*.jpg`(铺满), 不透明度可到 40%。", 1),

    # ---------------------------------------------------------------- 皮肤大全总数
    ("    total = 27", "    total = 30", 1),
]


def swap_modes_lines(text):
    """把 skin_core 里 MODES 那两行(src 中是转义后的字面量)换成 Suit20 文案。

    按"行内含关键中文"定位, 再对该行做子串替换 —— 不手写转义, 免得数错反斜杠。
    """
    lines = text.split("\n")
    hit = [i for i, l in enumerate(lines) if "完整单图(默认, 不裁切)" in l and "grid" in l]
    if len(hit) != 1:
        raise SystemExit("[make20] MODES 定位失败, 命中 %d 行" % len(hit))
    a = hit[0]
    b = a + 1
    if "全屏单图(铺满, 上下裁切)" not in lines[b]:
        raise SystemExit("[make20] MODES 第二行不是预期内容")
    lines[a] = lines[a].replace("完整单图(默认, 不裁切)", "全屏铺满(默认, cover)")
    lines[b] = lines[b].replace("全屏单图(铺满, 上下裁切)", "卡片单图(模糊填充)")
    print("[make20] MODES 行已换: 第 %d-%d 行" % (a + 1, b + 1))
    return "\n".join(lines)


def main():
    text = open(SRC, encoding="utf-8", newline="").read()

    for old, new, cnt in PAIRS:
        n = text.count(old)
        if n == 0:
            raise SystemExit("[make20] 未找到片段(0 次):\n%r" % old[:200])
        if n != cnt:
            raise SystemExit("[make20] 片段出现 %d 次, 期望 %d:\n%r" % (n, cnt, old[:200]))
        text = text.replace(old, new)

    text = swap_modes_lines(text)

    with open(DST, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    print("[make20] 写出 %s (%d bytes), %d 条替换 + MODES 换行"
          % (os.path.basename(DST), len(text.encode("utf-8")), len(PAIRS)))

    for label, keys in (("17", ("17",)),
                        ("上一套文案", ("四格", "胆孝", "01-quad", "完整卡片(不裁切)"))):
        bad = [(i, l.strip()[:110]) for i, l in enumerate(text.split("\n"), 1)
               if any(k in l for k in keys)]
        if bad:
            print("[make20] 仍含 %s 的行:" % label)
            for i, l in bad:
                print("   %4d  %s" % (i, l))
        else:
            print("[make20] 自检通过: 无 %s 残留" % label)


if __name__ == "__main__":
    main()
