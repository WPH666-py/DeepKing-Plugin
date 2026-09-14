# -*- coding: utf-8 -*-
"""由 _suit21-src/make_gen21.py 产出 _suit22-src/make_gen22.py。

沿用 Suit21 验证过的两段式做法:
  1) 中文/名字/注释 -> 直接 replace(不含反斜杠, 安全)
  2) 含 \\n \\" 的转义字面量 -> 按"行内关键中文"定位到行, 只改该行片段
另有两处整串 token(仓库名、皮肤大全总数), 放在最后统一替换, 免得改掉 PAIRS 自己的 key。

用法: python _suit22-src/build_make22.py
"""
import ast
import io
import os

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "make_gen21_base.py")
DST = os.path.join(HERE, "make_gen22.py")

# ---- 1) (旧, 新) 直接替换 ----
SIMPLE = [
    ("由 gen_suit17.py(基线)派生出 gen_suit21.py。",
     "由 gen_suit17.py(基线)派生出 gen_suit22.py。"),
    ("Suit21 与 Suit17/19/20 的区别:", "Suit22 与 Suit20/21 的区别:"),
    ("素材是银杏银饰特写(带背景), 桌宠取人物区域。",
     "素材是苗寨鼓楼人物插画(带背景), 桌宠取人物区域。"),
    ("用法: python _suit21-src/make_gen21.py", "用法: python _suit22-src/make_gen22.py"),
    ('DST = os.path.join(HERE, "gen_suit21.py")', 'DST = os.path.join(HERE, "gen_suit22.py")'),
    ("生成 Deepseek-Skin-Suit21 仓库。", "生成 Deepseek-Skin-Suit22 仓库。"),
    ("脚本与文档都按 Suit21 显式写出", "脚本与文档都按 Suit22 显式写出"),
    ("用法: python _suit21-src/gen_suit21.py", "用法: python _suit22-src/gen_suit22.py"),
    ("[make21]", "[make22]"),

    # 素材
    ('ASSET_SRC = "img1-ginkgo.jpg"        # 素材源(银杏银饰特写, 1104x637 = 16:9)',
     'ASSET_SRC = "img1-drum.jpg"          # 素材源(苗寨鼓楼插画, 1104x629 = 16:9)'),
    ('ASSET_DST = "01-ginkgo.jpg"          # 仓库内文件名',
     'ASSET_DST = "01-drum.jpg"            # 仓库内文件名'),
    ('ASSET_STEM = "01-ginkgo"', 'ASSET_STEM = "01-drum"'),
    ('WALLPAPER_NAME = "银杏银饰(16:9 宽幅)"', 'WALLPAPER_NAME = "苗寨鼓楼(16:9 宽幅)"'),
    ("PET_CROP = (0.47, 0.50, 0.44)", "PET_CROP = (0.42, 0.66, 0.44)"),

    # 生成器内部注释
    ("特写插画没有白底可抠", "苗寨插画没有白底可抠"),

    # AGENTS / README 文案
    ("(特写插画: 鲸鱼娘戴苗银头冠, 银杏叶环绕, 微笑伸手),",
     "(苗寨插画: 鲸鱼娘戴苗银头冠, 手执折扇, 端坐鼓楼屋檐),"),
    ("素材是 1104x637(约 16:9), 与常见屏幕同形, cover 铺满时几乎不裁切。",
     "素材是 1104x629(约 16:9), 与常见屏幕同形, cover 铺满时几乎不裁切。"),
    ("DeepSeek 蓝色大肥鱼(鲸鱼娘)主题皮肤第二十一弹: **单张样式**——一张银杏银饰特写,",
     "DeepSeek 蓝色大肥鱼(鲸鱼娘)主题皮肤第二十二弹: **单张样式**——一张苗寨鼓楼插画,"),
    ("画面: 鲸鱼娘戴苗银头冠, 银杏叶环绕身侧, 微笑着伸手, 暖金与藏蓝相衬。",
     "画面: 鲸鱼娘戴苗银头冠、手执折扇, 端坐鼓楼屋檐之上, 身后是层叠苗寨与远山。"),
    ("默认; 1104x637 与屏幕同形, 几乎不裁切", "默认; 1104x629 与屏幕同形, 几乎不裁切"),
    ("素材是 1104x637(约 16:9), 与常见屏幕同形, 默认的「全屏铺满」几乎不裁切;",
     "素材是 1104x629(约 16:9), 与常见屏幕同形, 默认的「全屏铺满」几乎不裁切;"),
    ("assets/           1 张特写插画(01-ginkgo.jpg, 1104x637)",
     "assets/           1 张苗寨插画(01-drum.jpg, 1104x629)"),
]

# ---- 2) 行内片段替换(定位用中文, 只改该行里的片段) ----
LINE_FIXES = [
    ("单张样式: 素材 1104x637 与屏幕同形", [("1104x637", "1104x629")]),
]

# ---- 3) 最后统一替换的 token ----
TOKENS = [
    ("Deepseek-Skin-Suit21", "Deepseek-Skin-Suit22"),   # docstring 路径 + patch 值
    # PAIRS 跑完后, NUM 已变成 21, 这里再推到 22
    (chr(39) + 'NUM = "21"' + chr(39), chr(39) + 'NUM = "22"' + chr(39)),
    ("total = 30", "total = 32"),                        # 皮肤大全总数
]


def main():
    text = io.open(SRC, encoding="utf-8").read()

    for old, new in SIMPLE:
        n = text.count(old)
        if n == 0:
            raise SystemExit("[build22] 普通替换未命中: %r" % old[:100])
        text = text.replace(old, new)
        print("[build22] %-40s x%d" % (old[:38], n))

    lines = text.split("\n")
    for needle, pairs in LINE_FIXES:
        idx = [i for i, l in enumerate(lines) if needle in l]
        if len(idx) != 1:
            raise SystemExit("[build22] 行定位失败(%r): 命中 %d" % (needle, len(idx)))
        i = idx[0]
        for old, new in pairs:
            if old not in lines[i]:
                raise SystemExit("[build22] 行内未找到 %r" % old)
            lines[i] = lines[i].replace(old, new)
        print("[build22] 行改写 %-30s -> 第 %d 行" % (needle[:28], i + 1))
    text = "\n".join(lines)

    for old, new in TOKENS:
        n = text.count(old)
        if n == 0:
            raise SystemExit("[build22] token 未出现: %r" % old)
        text = text.replace(old, new)
        print("[build22] token %-24s -> %-24s (%d 处)" % (old, new, n))

    io.open(DST, "w", encoding="utf-8", newline="\n").write(text)
    ast.parse(text)
    print("[build22] 写出 %s (%d bytes), 语法 OK"
          % (os.path.basename(DST), len(text.encode("utf-8"))))

    bad = [(i, l.strip()[:110]) for i, l in enumerate(text.split("\n"), 1) if "21" in l]
    if bad:
        print("[build22] 仍含 21 的行:")
        for i, l in bad:
            print("   %4d  %s" % (i, l))
    else:
        print("[build22] 自检通过: 无残留 21")


if __name__ == "__main__":
    main()
