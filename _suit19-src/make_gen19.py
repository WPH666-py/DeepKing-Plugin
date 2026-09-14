# -*- coding: utf-8 -*-
"""由 gen_suit17.py 派生出 gen_suit19.py(单张样式 -> 另一套素材)。

gen_suit17.py 是为 Suit17 显式写死的, 这里逐条参数化。每条替换都断言"存在且唯一",
避免上一轮那种静默留下旧套件文案的问题。

用法: python _suit19-src/make_gen19.py
读:   _suit19-src/gen_suit17_base.py
写:   _suit19-src/gen_suit19.py
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "gen_suit17_base.py")
DST = os.path.join(HERE, "gen_suit19.py")

# (旧, 新, 允许出现次数)  —— 次数用于断言; None 表示至少 1 次
PAIRS = [
    # 头部
    ("生成 Deepseek-Skin-Suit17 仓库。", "生成 Deepseek-Skin-Suit19 仓库。", 1),
    ("模板: _suit17-src/tpl/(取自 Suit12 的\"单张样式\"套件)",
     "模板: _suit19-src/tpl/(取自 Suit12 的\"单张样式\"套件)", 1),
    ("脚本与文档都按 Suit17 显式写出", "脚本与文档都按 Suit19 显式写出", 1),
    ("用法: python _suit17-src/gen_suit17.py", "用法: python _suit19-src/gen_suit19.py", 1),
    ("产物: D:\\\\projects-py\\\\DeepKing-Plugin\\\\Deepseek-Skin-Suit17",
     "产物: D:\\\\projects-py\\\\DeepKing-Plugin\\\\Deepseek-Skin-Suit19", 1),
    ('DST = os.path.join(ROOT, "Deepseek-Skin-Suit17")',
     'DST = os.path.join(ROOT, "Deepseek-Skin-Suit19")', 1),
    ('NUM = "17"', 'NUM = "19"', 1),
    # 素材参数
    ('ASSET_SRC = "img1-quad.jpg"          # 素材源(四格拼图, 960x960)',
     'ASSET_SRC = "img1-charge.jpg"        # 素材源(充值通道插画, 1080x1095)', 1),
    ('ASSET_DST = "01-quad.jpg"            # 仓库内文件名',
     'ASSET_DST = "01-charge.jpg"          # 仓库内文件名', 1),
    ('ASSET_STEM = "01-quad"', 'ASSET_STEM = "01-charge"', 1),
    ('WALLPAPER_NAME = "鲸鱼四连(2×2 四格)"',
     'WALLPAPER_NAME = "特别充值通道 1鲸子=1tonken"', 1),
    ('PET_NAME = "鲸鱼娘"', 'PET_NAME = "鲸鱼娘"', 1),
    ("PET_CROP = (0.26, 0.26, 0.18)        # (中心x比例, 中心y比例, 半边长占最短边比例)",
     "PET_CROP = (0.70, 0.50, 0.32)        # (中心x比例, 中心y比例, 半边长占最短边比例)", 1),
    # 文档里的套件描述
    ("(四格表情拼图: 鲸鱼神了我大胆孝 / 鲸鱼拉了我偷偷孝 / 鲸鱼超越其他模型我跳脸孝 / 鲸鱼被其他模型超我嘴硬孝)",
     "(单张插画: 鲸鱼娘提裙比嘘, 配字「这是特别充值通道, 1鲸子=1tonken(仅限中出)」)", 1),
    ("四格: 鲸鱼神了我大胆孝 · 鲸鱼拉了我偷偷孝 · 鲸鱼超越其他模型我跳脸孝 · 鲸鱼被其他模型超我嘴硬孝。",
     "插画: 鲸鱼娘提裙比「嘘」, 大字「这是特别充值通道, 1鲸子=1tonken」, 小字「(仅限中出)」。", 1),
    ("一张四格表情拼图,", "一张充值通道插画,", 1),
    ("assets/           1 张四格表情拼图(01-quad.jpg, 960x960)",
     "assets/           1 张插画(01-charge.jpg, 1080x1095)", 1),
    ('# 桌宠: 四格拼图里取左上"胆孝"那一格(方形取景, 角色居中且不带格线)',
     '# 桌宠: 取人物区域(方形取景, 角色居中)', 1),
    ('"# 四格拼图整张不好抠: 取景裁剪出左上「胆孝」那一格做桌宠贴图\\n"',
     '"# 取人物区域做桌宠贴图(方形取景, 不抠图)\\n"', 1),
    ('python tools/pet.py                      # 桌面桌宠(取左上"胆孝"那格, 右键换/退出)',
     'python tools/pet.py                      # 桌面桌宠(取人物区域, 右键换/退出)', 1),
    ("| 桌面桌宠 | `tools/pet.py`: 取左上「胆孝」那一格, 透明置顶可拖动, 右键换/退出 |",
     "| 桌面桌宠 | `tools/pet.py`: 取人物区域, 透明置顶可拖动, 右键换/退出 |", 1),
    # 素材方图 -> 本次素材比例说明(文案保持一致即可, 不改语义)
    ("**关于裁切**: 素材是 1:1 方形四格拼图, 16:9 屏上用 cover 铺满会裁掉上下各约 22%, 四格文案会被切;",
     "**关于裁切**: 素材接近 1:1 方形, 16:9 屏上用 cover 铺满会裁掉上下各约 22%, 大字文案会被切;", 1),
    ("> 素材是 1:1 方形四格拼图。默认的「完整卡片单图」保证四格文案完整可见;",
     "> 素材接近 1:1 方形。默认的「完整卡片单图」保证大字与画中人完整可见;", 1),
    # skin_core / pet 里生成的注释(注意: 这些在生成器源码里是带 \n 转义的字符串字面量)
    ('"# 单张样式。素材是 1:1 方形, 在 16:9 屏上 cover 会裁掉上下各约 22%(四格文案会被切),\\n"',
     '"# 单张样式。素材接近 1:1, 在 16:9 屏上 cover 会裁掉上下各约 22%(大字文案会被切),\\n"', 1),
    ("    方形/竖版素材在 16:9 屏幕上 cover 会裁掉约 22% 的高度, 四格文案会被切;",
     "    方形/竖版素材在 16:9 屏幕上 cover 会裁掉约 22% 的高度, 文案会被切;", 1),
    ('\'SLEEP_STEM = "%s"  # 四格拼图取景: 慢慢晃\' % ASSET_STEM),',
     '\'SLEEP_STEM = "%s"  # 人物区域取景: 慢慢晃\' % ASSET_STEM),', 1),
    # 套件号处理说明: gen_suit17.py 里所有 17 都集中在文件头部(第 2-20 行),
    # 已被上面的显式替换逐条消化; 运行时目录/扩展 id/命令前缀都是 %s 拼出来的,
    # 由 NUM 驱动。所以这里不需要再做整体 17 -> 19 替换。
    # 皮肤大全总数
    ("    total = 27", "    total = 29", 1),
]


def main():
    with open(SRC, "r", encoding="utf-8", newline="") as f:
        text = f.read()
    nl = "\r\n" if "\r\n" in text else "\n"

    for old, new, cnt in PAIRS:
        n = text.count(old)
        if n == 0:
            raise SystemExit("[make19] 未找到片段(0 次): %r" % old[:110])
        if cnt is not None and n != cnt:
            raise SystemExit("[make19] 片段出现 %d 次, 期望 %d: %r" % (n, cnt, old[:110]))
        text = text.replace(old, new)
        print("[make19] %-46s x%d" % (old[:44].replace(nl, "\\n"), n))

    with open(DST, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    print("\n[make19] 写出 %s (%d bytes)" % (os.path.basename(DST), len(text.encode("utf-8"))))

    # 自检: 不应再有 17 的痕迹
    bad = [(i, l.strip()[:100]) for i, l in enumerate(text.split("\n"), 1) if "17" in l]
    if bad:
        print("[make19] 仍含 17 的行:")
        for i, l in bad:
            print("   %4d  %s" % (i, l))
    else:
        print("[make19] 自检通过: 无残留 17 引用")


if __name__ == "__main__":
    main()
