# _suit*-src — 皮肤套件生成器（脚手架）

这里放的是把**一套新素材**变成**一个完整皮肤仓库**的生成器。
每个生成器都会产出 `../Deepseek-Skin-SuitNN/`（素材 → `tools/` 脚本 → 文档 → 扩展 → 预览图）。

素材图片（`img*.jpg`）**没有进仓**（已被 `.gitignore` 排除）：它们和各自皮肤仓库
`assets/` 里的那份是同一批文件。要重跑生成器，先从对应仓库取回素材，或把新素材按下面的
命名放进来。

## 目录

| 目录 | 产出的套件 | 样式 | 说明 |
|---|---|---|---|
| `_suit15-src/` | Deepseek-Skin-Suit15 | 2×2 拼贴 | 以 Suit14 为模板起点（`gen_suit15.py` 内含对模板的逐条改写） |
| `_suit16-src/` | Deepseek-Skin-Suit16 | 2×2 拼贴 | 由 15 派生；`make_gen16.py` + `patch_gen16_vscode.py` |
| `_suit17-src/` | Deepseek-Skin-Suit17 | 单张（完整卡片/铺满） | 以 **Suit12** 单张模板为起点，全量显式改写 |
| `_suit18-src/` | Deepseek-Skin-Suit18 | 2×2 拼贴 | 以 Suit16 的 2×2 模板为起点，全量显式改写 |
| `_suit19-src/` | Deepseek-Skin-Suit19 | 单张（完整卡片/铺满） | 由 17 派生；`make_gen19.py` |
| `_suit20-src/` | Deepseek-Skin-Suit20 | 单张（铺满/卡片） | 由 17 派生；`make_gen20.py`。素材 16:9，故默认恢复 cover |

## 怎么重跑

每个生成器都需要一个同目录下的 `tpl/`（模板仓库的源码副本），它没有进仓——
用一条命令从对应套件仓库恢复即可：

```bash
# 例：重跑 Suit18（模板取自 Suit16）
mkdir -p _suit18-src/tpl
cp -r Deepseek-Skin-Suit16/tools    _suit18-src/tpl/
cp -r Deepseek-Skin-Suit16/vscode   _suit18-src/tpl/
cp    Deepseek-Skin-Suit16/LICENSE  Deepseek-Skin-Suit16/.gitignore _suit18-src/tpl/
# 取回素材(它们不进仓, 与皮肤仓库 assets/ 里同一批)
cp    Deepseek-Skin-Suit18/assets/*.jpg _suit18-src/
# 素材要重命名成生成器期望的名字, 见 gen_suit18.py 顶部的 IMAGES 映射
python _suit18-src/gen_suit18.py
```

Windows 上把 `mk`/`cp` 换成 `New-Item -ItemType Directory` / `Copy-Item` 亦可。

## 加一套新皮肤

1. 挑一个**样式相同**的现有套件当模板（2×2 用 Suit16/18，单张用 Suit12/17/19）。
2. 照抄最近的一个生成器，改开头那组参数：`NUM` / `ASSET_*` / `WALLPAPER_NAME` /
   `PET_NAME` / `PET_CROP` / `IMAGES`+`IMAGE_NAMES`，以及文档字符串。
3. 桌面桌宠的取景参数 `PET_CROP = (中心x比例, 中心y比例, 半边长占最短边比例)` 需要实拍确认：
   先生成候选方格图挑一版，再看 `docs/_pet*.png` 是否居中、有没有把文字/格线带进来。
4. 在 `Desktop-IDE-AI-Skin/catalog.json` 追加一行，`python scripts/sync_catalog.py` 同步包内目录，
   再 `python -m build && python -m twine upload dist/*` 发版。

## 三个坑（都踩过）

- **别用"整串替换上一套文案"的方式生成新套件。** 链条越长越容易静默漏改，曾经把上一套的
  卡片标题、`package.json` 命令名、`AGENTS.md` 描述留在新仓库里，而且不报错。
  现在的写法是 `patch()` 逐条断言"必须命中且唯一"，同时把卡片标题之类改成由 `IMAGE_NAMES` **现算**。
- **`patch()` 的锚点必须与模板逐字一致**，包括尾逗号、`\n` 转义、以及只存在于"生成出的代码"里
  （而非生成器源码里）的注释。`_suit19-src/make_gen19.py` 的注释里记了具体案例。
- **派生新生成器时，先确认 `tpl/` 是哪一代的模板。** 这一坑耗了 Suit20 大半时间：
  `gen_suit17_base.py` 里的锚点是写给 **Suit12** 模板的，我一开始却把 **Suit17 的成品仓库**
  当模板塞进 `tpl/`，于是大量锚点"已定型"、全部匹配失败（`patch` 报"未找到片段"）。
  规则：**从哪一代复制生成器，就用它当初那一代的模板**（见上表"模板起点"一列）。
  排查手法：拿 `patch` 报出的缺失片段去 `tpl/` 里 `grep`，命中不了就是模板代次错了。

## 单张样式为什么默认"完整卡片"而不是 cover

单张样式的惯例（Suit12）是 `grid = cover 铺满`。但 17/19 的素材都接近 1:1，
16:9 屏幕上 cover 会上下各裁约 22%，把大字文案切掉。所以这两套的 `skin_core.py` 里
`GRID_FIT = True` 让默认变成"完整卡片（不裁切）"，`single1` 才是 cover。
想换回惯例把 `GRID_FIT` 改成 `False`。
