# -*- coding: utf-8 -*-
"""由 gen_suit15.py 派生出 gen_suit16.py(套件号 / 素材名 / 文案全部参数化)。

用法: python _suit16-src/make_gen16.py
读:   _suit15-src/gen_suit15.py
写:   _suit16-src/gen_suit16.py
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = os.path.join(ROOT, "_suit15-src", "gen_suit15.py")
DST = os.path.join(HERE, "gen_suit16.py")

PAIRS = [
    # 套件号
    ('"""生成 Deepseek-Skin-Suit15 仓库(以 Suit14 为模板做参数化改写)。',
     '"""生成 Deepseek-Skin-Suit16 仓库(以 Suit15 为模板做参数化改写)。'),
    ('SLUG = "Suit15"', 'SLUG = "Suit16"'),
    ('NUM = "15"', 'NUM = "16"'),
    # 素材映射
    ('("img1-ask.jpg", "01-ask.jpg"),', '("img1-tantrum.jpg", "01-tantrum.jpg"),'),
    ('("img2-dsh.jpg", "02-dsh.jpg"),', '("img2-jealous.jpg", "02-jealous.jpg"),'),
    ('("img3-what.jpg", "03-suspicious.jpg"),', '("img3-begging.jpg", "03-begging.jpg"),'),
    ('("img4-think.jpg", "04-thinking.jpg"),', '("img4-broke.jpg", "04-broke.jpg"),'),
    # 文案(README / AGENTS / 剧本里的提示行同步按素材顺序)
    ('    "你愿意和我…吗?",\n    "DSH? DeepSeek Hentai?",\n    "你目录里的dsh是什么…大烧货吗?",\n    "正在思考…",\n',
     '    "别再蹬了啦!",\n    "你已经有我了…",\n    "求你们不要再嘲笑了",\n    "已思考13秒: 穷光蛋",\n'),
    # 皮肤14 -> 16 的模板链式引用("Suit14"/"14" 交给下面的 RENAMES 逐词替换)
]

RENAMES = {
    "img1-ask.jpg": "img1-tantrum.jpg",
    "img2-dsh.jpg": "img2-jealous.jpg",
    "img3-what.jpg": "img3-begging.jpg",
    "img4-think.jpg": "img4-broke.jpg",
    # 不重命名素材"词干"(01-ask 等): gen_pet 的 old_modes 锚点必须与 tpl 逐字一致,
    # 而目标 MODES 是由 IMAGE_FILES 现算的(见 gen_pet 的 new_modes)。
    "你愿意和我…吗?": "别再蹬了啦!",
    "DSH? DeepSeek Hentai?": "你已经有我了…",
    "你目录里的dsh是什么…大烧货吗?": "求你们不要再嘲笑了",
    "正在思考…": "已思考13秒: 穷光蛋",
    ".deepskin15": ".deepskin16",
    "DeepSeek 大肥鱼15": "DeepSeek 大肥鱼16",
    "大肥鱼15": "大肥鱼16",
    "皮肤套件15": "皮肤套件16",
    "Suit15": "Suit16",
    "deepskin-suit15": "deepskin-suit16",
    "deepskin15": "deepskin16",
    "deepseek-15": "deepseek-16",
    "DeepSkin-Suit15": "DeepSkin-Suit16",
    "DeepSkin15": "DeepSkin16",          # 导出目录(PyCharm 背景图)
    "_suit15-src/gen_suit15.py": "_suit16-src/gen_suit16.py",
    "安装大肥鱼皮肤15 / Deepseek 皮肤15": "安装大肥鱼皮肤16 / Deepseek 皮肤16",
}

# 补丁里的 old_string 必须与 tpl/(Suit14) 原文逐字一致。RENAMES 用的是不带引号的
# 纯词干("01-ask"), 而补丁锚点里是带引号的 IMAGE_FILES 字面量, 两者不会互相误伤,
# 所以这里当前为空; 保留机制以便将来词干规则变化时救急(键=被误改后, 值=模板原文)。
TEMPLATE_ANCHOR_FIXES = {}


def main():
    with open(SRC, "r", encoding="utf-8") as f:
        text = f.read()

    for old, new in PAIRS:
        if old not in text:
            raise SystemExit("[make16] 未找到片段: %r" % old[:90])
        text = text.replace(old, new)

    for old, new in RENAMES.items():
        text = text.replace(old, new)

    # 生成器自身不能再引用 15 的目录
    text = text.replace('os.path.join(ROOT, "_suit15-src"', 'os.path.join(ROOT, "_suit16-src"')

    for bad, good in TEMPLATE_ANCHOR_FIXES.items():
        if bad == good:
            continue
        if bad not in text:
            raise SystemExit("[make16] 待修正的模板锚点未出现: %r" % bad[:90])
        text = text.replace(bad, good)

    with open(DST, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    print("[make16] 写出 %s (%d bytes)" % (os.path.relpath(DST, ROOT), len(text.encode("utf-8"))))

    # 自检: 不该再有 15 的痕迹(模板链式注释除外)
    bad = []
    for i, line in enumerate(text.splitlines(), 1):
        if "15" in line and "Suit14" not in line and "以 Suit15 为模板" not in line:
            bad.append((i, line.strip()[:100]))
    if bad:
        print("[make16] 留意以下仍含 15 的行:")
        for i, line in bad:
            print("   %4d  %s" % (i, line))
    else:
        print("[make16] 自检通过: 无残留 15 引用")


if __name__ == "__main__":
    main()
