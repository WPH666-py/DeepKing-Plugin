# -*- coding: utf-8 -*-
"""把共享基线里 compose() docstring 的过时措辞改掉, 让新套件不必再逐次修补。

基线: _suit20-src/gen_suit17_base.py 与 _suit21-src/gen_suit17_base.py(同一份)
旧: 本套件 GRID_SINGLE=True: grid 按 GRID_FIT 决定是 完整卡片 还是 全屏 cover;
新: 本套件 GRID_SINGLE=True: grid 默认走 cover 铺满(GRID_FIT=True 时改为完整卡片);
"""
import ast
import io
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

OLD = "    本套件 GRID_SINGLE=True: grid 按 GRID_FIT 决定是 完整卡片 还是 全屏 cover;"
NEW = "    本套件 GRID_SINGLE=True: grid 默认走 cover 铺满(GRID_FIT=True 时改为完整卡片);"

TARGETS = [
    os.path.join(ROOT, "_suit20-src", "gen_suit17_base.py"),
    os.path.join(ROOT, "_suit21-src", "gen_suit17_base.py"),
]

for p in TARGETS:
    if not os.path.exists(p):
        print("[skip] 不存在: %s" % p)
        continue
    t = io.open(p, encoding="utf-8").read()
    n = t.count(OLD)
    if n == 0:
        print("[skip] 未命中(可能已改): %s" % os.path.relpath(p, ROOT))
        continue
    t = t.replace(OLD, NEW)
    io.open(p, "w", encoding="utf-8", newline="\n").write(t)
    ast.parse(t)
    print("[fix] %s (%d 处), 语法 OK" % (os.path.relpath(p, ROOT), n))
