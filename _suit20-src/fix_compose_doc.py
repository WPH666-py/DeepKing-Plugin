# -*- coding: utf-8 -*-
"""把 Suit20 的 skin_core.compose() docstring 里残留的"完整卡片"措辞改成现有默认。

默认已改成 cover 铺满, 但 compose() 的 docstring 还写着"完整卡片 还是 全屏 cover"。
改生成器(gen_suit20.py)与产物(Deepseek-Skin-Suit20/tools/skin_core.py)两处, 保持可重跑一致。
"""
import ast
import io
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

OLD = "    本套件 GRID_SINGLE=True: grid 按 GRID_FIT 决定是 完整卡片 还是 全屏 cover;"
NEW = "    本套件 GRID_SINGLE=True: grid 默认走 cover 铺满(GRID_FIT=True 时改为完整卡片);"

TARGETS = [
    os.path.join(HERE, "gen_suit20.py"),
    os.path.join(ROOT, "Deepseek-Skin-Suit20", "tools", "skin_core.py"),
]

for p in TARGETS:
    if not os.path.exists(p):
        print("[skip] 不存在: %s" % p)
        continue
    t = io.open(p, encoding="utf-8").read()
    n = t.count(OLD)
    if n == 0:
        print("[skip] 未命中: %s" % os.path.basename(p))
        continue
    t = t.replace(OLD, NEW)
    io.open(p, "w", encoding="utf-8", newline="\n").write(t)
    if p.endswith(".py"):
        ast.parse(t)
    print("[fix] %s (%d 处)" % (os.path.basename(p), n))

# 复核产物
sc = os.path.join(ROOT, "Deepseek-Skin-Suit20", "tools", "skin_core.py")
t = io.open(sc, encoding="utf-8").read()
for probe in ("完整卡片 还是 全屏 cover", "GRID_FIT=True 时改为完整卡片"):
    print("  复核 %r: %s" % (probe, probe in t))
