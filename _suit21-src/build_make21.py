# -*- coding: utf-8 -*-
"""由 _suit20-src/make_gen20.py 产出 _suit21-src/make_gen21.py —— 手工定点改写版。

上一版想做成"参数化转换器", 结果又陷进反斜杠转义的泥潭(和 Suit20 那次同款)。
这次换个稳的做法: 先整体拷过来, 再用**不依赖转义**的方式逐处改:

  * 中文字符串、注释、名字  -> 直接 replace(它们不含反斜杠)
  * 含 \\n / \\" 的转义字面量 -> 按"行内包含关键中文"定位到行, 只改该行里的中文片段,
                              绝不手写字面量本身

用法: python _suit21-src/build_make21.py
"""
import ast
import io
import os

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(os.path.dirname(HERE), "_suit20-src", "make_gen20.py")
DST = os.path.join(HERE, "make_gen21.py")

# ---- 1) 普通替换(不含反斜杠, 安全) ----
SIMPLE = [
    ("由 gen_suit17.py(基线)派生出 gen_suit20.py。",
     "由 gen_suit17.py(基线)派生出 gen_suit21.py。"),
    ("Suit20 与 Suit17/19 的区别:", "Suit21 与 Suit17/19/20 的区别:"),
    ("因此恢复单张样式的惯例默认: grid = 全屏 cover, single1 = 卡片单图;",
     "因此默认 grid = 全屏 cover, single1 = 卡片单图;"),
    ("  * 素材是夜景插画(带背景), 桌宠取人物区域。",
     "  * 素材是银杏银饰特写(带背景), 桌宠取人物区域。"),
    ("用法: python _suit20-src/make_gen20.py", "用法: python _suit21-src/make_gen21.py"),
    ('DST = os.path.join(HERE, "gen_suit20.py")', 'DST = os.path.join(HERE, "gen_suit21.py")'),
    ("生成 Deepseek-Skin-Suit20 仓库。", "生成 Deepseek-Skin-Suit21 仓库。"),
    ("脚本与文档都按 Suit20 显式写出", "脚本与文档都按 Suit21 显式写出"),
    ("用法: python _suit20-src/gen_suit20.py", "用法: python _suit21-src/gen_suit21.py"),
    ('DST = os.path.join(ROOT, "Deepseek-Skin-Suit20")',
     'DST = os.path.join(ROOT, "Deepseek-Skin-Suit21")'),
    ('NUM = "20"', 'NUM = "21"'),

    # 素材
    ('ASSET_SRC = "img1-village.jpg"       # 素材源(夜景插画, 1104x630 = 16:9)',
     'ASSET_SRC = "img1-ginkgo.jpg"        # 素材源(银杏银饰特写, 1104x637 = 16:9)'),
    ('ASSET_DST = "01-village.jpg"         # 仓库内文件名',
     'ASSET_DST = "01-ginkgo.jpg"          # 仓库内文件名'),
    ('ASSET_STEM = "01-village"', 'ASSET_STEM = "01-ginkgo"'),
    ('WALLPAPER_NAME = "苗寨灯火(16:9 宽幅)"', 'WALLPAPER_NAME = "银杏银饰(16:9 宽幅)"'),
    ('PET_NAME = "苗寨灯火"', 'PET_NAME = "青羽"'),
    ("# 桌宠: 取人物区域(方形取景; 夜景插画无白底可抠)",
     "# 桌宠: 取人物区域(方形取景; 特写插画无白底可抠)"),
    ("PET_CROP = (0.70, 0.62, 0.46)", "PET_CROP = (0.47, 0.50, 0.44)"),

    # AGENTS / README 文案
    ("(夜景插画: 鲸鱼娘着苗银盛装, 倚在吊脚楼栏杆边眺望万家灯火),",
     "(特写插画: 鲸鱼娘戴苗银头冠, 银杏叶环绕, 微笑伸手),"),
    ("素材是 1104x630(约 16:9), 与常见屏幕同形, cover 铺满时上下各只裁约 1%。",
     "素材是 1104x637(约 16:9), 与常见屏幕同形, cover 铺满时几乎不裁切。"),
    ("DeepSeek 蓝色大肥鱼(鲸鱼娘)主题皮肤第二十弹: **单张样式**——一张夜景宽幅插画,",
     "DeepSeek 蓝色大肥鱼(鲸鱼娘)主题皮肤第二十一弹: **单张样式**——一张银杏银饰特写,"),
    ("画面: 鲸鱼娘着苗银盛装, 倚在吊脚楼栏杆边, 眺望山下万家灯火与夜色群山。",
     "画面: 鲸鱼娘戴苗银头冠, 银杏叶环绕身侧, 微笑着伸手, 暖金与藏蓝相衬。"),
    ("默认; 1104x630 与屏幕同形, 几乎不裁切", "默认; 1104x637 与屏幕同形, 几乎不裁切"),
    ("素材是 1104x630(约 16:9), 与常见屏幕同形, 默认的「全屏铺满」上下各只裁约 1%;",
     "素材是 1104x637(约 16:9), 与常见屏幕同形, 默认的「全屏铺满」几乎不裁切;"),
    ("assets/           1 张夜景宽幅插画(01-village.jpg, 1104x630)",
     "assets/           1 张特写插画(01-ginkgo.jpg, 1104x637)"),

    # 剩余细枝末节(仅日志标签; docstring 里的路径说明属装饰, 留着不影响产物)
    ("[make20]", "[make21]"),
]

# ---- 2) 转义字面量: 按"行内关键中文"定位, 只改中文片段 ----
LINE_FIXES = [
    # (定位用的行内中文, [(旧片段, 新片段), ...])
    # 注意: 运行时目录里的 .deepskin20 是 %s 由 NUM 拼出来的, base 里没有该字面量。
    ("单张样式: 素材 1104x630 与屏幕同形", [("1104x630", "1104x637")]),
    ("夜景插画没有白底可抠: 取景裁剪出人物区域",
     [("夜景插画没有白底可抠", "特写插画没有白底可抠")]),
]


def main():
    text = io.open(SRC, encoding="utf-8").read()

    for old, new in SIMPLE:
        n = text.count(old)
        if n == 0:
            raise SystemExit("[build21] 普通替换未命中: %r" % old[:100])
        text = text.replace(old, new)
        print("[build21] %-34s x%d" % (old[:32], n))

    lines = text.split("\n")
    for needle, pairs in LINE_FIXES:
        idx = [i for i, l in enumerate(lines) if needle in l]
        if len(idx) != 1:
            raise SystemExit("[build21] 行定位失败(%r): 命中 %d" % (needle, len(idx)))
        i = idx[0]
        for old, new in pairs:
            if old not in lines[i]:
                raise SystemExit("[build21] 行内未找到 %r" % old)
            lines[i] = lines[i].replace(old, new)
        print("[build21] 行改写 %-30s -> 第 %d 行" % (needle[:28], i + 1))
    text = "\n".join(lines)

    io.open(DST, "w", encoding="utf-8", newline="\n").write(text)
    ast.parse(text)
    print("[build21] 写出 %s (%d bytes), 语法 OK"
          % (os.path.basename(DST), len(text.encode("utf-8"))))

    bad = [(i, l.strip()[:110]) for i, l in enumerate(text.split("\n"), 1) if "20" in l]
    if bad:
        print("[build21] 仍含 20 的行:")
        for i, l in bad:
            print("   %4d  %s" % (i, l))
    else:
        print("[build21] 自检通过: 无残留 20")


if __name__ == "__main__":
    main()
