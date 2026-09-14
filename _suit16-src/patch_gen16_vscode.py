# -*- coding: utf-8 -*-
"""gen_suit16.py 的两处收尾修正(链式改写会漏掉卡片/文案标题):

1. gen_vscode 的卡片标题与 package.json 标题, 改成由 IMAGE_NAMES 现算;
2. gen_suit16 自带 AGENTS/README 文案里遗留的上一套标题, 换成 NEW_TITLES。

用行号/精确子串定位, 不依赖空白风格。重复执行安全(已修正过会跳过)。
用法: python _suit16-src/patch_gen16_vscode.py
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
TARGET = os.path.join(HERE, "gen_suit16.py")

# 与 gen_suit16.IMAGE_NAMES 同序
NEW_TITLES = [
    "别再蹬了啦!",
    "你已经有我了…",
    "求你们不要再嘲笑了",
    "已思考13秒: 穷光蛋",
]
# 上一套(15)的标题, 同序; 生成器文案里若还留着就换成 NEW_TITLES
STALE_TITLES = [
    "你愿意和我…吗?",
    "DSH? DeepSeek Hentai?",
    "你目录里的dsh是什么…大烧货吗?",
    "正在思考…",
]

NEW_CARDS = '''    # 卡片标题直接由 IMAGE_NAMES 现算(避免链式改写把上一套的文案留在卡片上)
    cards_old = (
        "  const cards = [\\n"
        "    { mode: 'grid', t: '2×2 拼贴', img: 'thumb-grid.png' },\\n"
        "    { mode: 'single1', t: '你愿意和我…', img: 'thumb-1.png' },\\n"
        "    { mode: 'single2', t: '我不知道耶', img: 'thumb-2.png' },\\n"
        "    { mode: 'single3', t: '就骚了', img: 'thumb-3.png' },\\n"
        "    { mode: 'single4', t: '好模型', img: 'thumb-4.png' }\\n"
        "  ];"
    )
    _js = []
    for _i, _name in enumerate(IMAGE_NAMES, start=1):
        _js.append("    { mode: 'single%d', t: '%s', img: 'thumb-%d.png' },\\n"
                   % (_i, _name.replace("'", "\\\\'"), _i))
    cards_new = (
        "  const cards = [\\n"
        "    { mode: 'grid', t: '2×2 拼贴', img: 'thumb-grid.png' },\\n"
        + "".join(_js) +
        "  ];"
    )
'''

NEW_TITLES_BLOCK = '''    for old, new in zip(
        ["你愿意和我…", "我不知道耶", "就骚了", "好模型"],
        IMAGE_NAMES,
    ):
        p = p.replace(old, new)
'''


def main():
    with open(TARGET, "r", encoding="utf-8", newline="") as f:
        text = f.read()

    # 0) 生成器自带文案里的遗留标题
    for stale, fresh in zip(STALE_TITLES, NEW_TITLES):
        if stale == fresh or stale not in text:
            continue
        n = text.count(stale)
        text = text.replace(stale, fresh)
        print("[patch] 文案 %r -> %r (%d 处)" % (stale, fresh, n))
    # 与 DeepKing 皮肤大全同步的套数
    if "皮肤大全(24+ 套" in text:
        text = text.replace("皮肤大全(24+ 套", "皮肤大全(26 套")
        print("[patch] 更新皮肤大全套数 -> 26 套")
    if "皮肤总目录(24+ 套)" in text:
        text = text.replace("皮肤总目录(24+ 套)", "皮肤总目录(26 套)")
        print("[patch] 更新皮肤总目录套数 -> 26 套")
    # 上一套的标题在"单图 N(...)"注释里带着问号/省略号, 与 STALE_TITLES 不同形, 单独修
    for stale, fresh in (
        ("单图 2(DeepSeek Hentai?)", "单图 2(你已经有我了…)"),
        ("单图 3(大烧货吗?)", "单图 3(求你们不要再嘲笑了)"),
        ("# DeepSeek Hentai?", "# 你已经有我了…"),
        ("# 大烧货吗?", "# 求你们不要再嘲笑了"),
        ("# 生成并设置单图 1(你愿意和我…吗)", "# 生成并设置单图 1(别再蹬了啦!)"),
    ):
        if stale in text:
            n = text.count(stale)
            text = text.replace(stale, fresh)
            print("[patch] 注释标题 %r -> %r (%d 处)" % (stale, fresh, n))

    nl = "\r\n" if "\r\n" in text else "\n"
    lines = text.split(nl)

    def find(pred, start=0):
        for i in range(start, len(lines)):
            if pred(lines[i]):
                return i
        return -1

    # 1) cards 块(只在还是旧写法时替换)
    cs = find(lambda s: s.strip() == "cards_old = (")
    if cs == -1:
        print("[patch] cards 块: 未找到(可能已修正, 跳过)")
    else:
        ce = -1
        for i in range(cs + 1, len(lines)):
            if lines[i].startswith("    t = patch(t, [(cards_old"):
                ce = i - 1
                break
        assert ce > cs, "未找到 cards 块结尾"
        assert lines[ce].strip() == ")", "cards 块结尾不是 ')': %r" % lines[ce]
        # 已经是新写法就跳过
        if any("_js.append" in lines[j] for j in range(cs, ce + 1)):
            print("[patch] cards 块: 已是现算写法, 跳过")
        else:
            lines[cs:ce + 1] = NEW_CARDS.rstrip("\n").split("\n")
            print("[patch] cards 块: 行 %d-%d 已改为现算" % (cs + 1, ce + 1))

    # 2) package.json 标题替换列表
    ts = find(lambda s: s.strip() == "for old, new in [")
    if ts == -1:
        print("[patch] 标题列表: 未找到(可能已修正, 跳过)")
    else:
        te = -1
        for i in range(ts + 1, len(lines)):
            if lines[i].strip() == "p = p.replace(old, new)":
                te = i
                break
        assert te > ts, "未找到标题替换列表结尾"
        lines[ts:te + 1] = NEW_TITLES_BLOCK.rstrip("\n").split("\n")
        print("[patch] 标题列表: 行 %d-%d 已改为 zip(IMAGE_NAMES)" % (ts + 1, te + 1))

    out = nl.join(lines)
    with open(TARGET, "w", encoding="utf-8", newline="") as f:
        f.write(out)
    print("[patch] 已写回 %s" % os.path.basename(TARGET))


if __name__ == "__main__":
    main()
