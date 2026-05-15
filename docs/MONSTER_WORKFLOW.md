# 贪吃小怪兽专项生成与校验规则

## 概览

本文只描述主流程中「模板游戏 > 贪吃小怪兽」在配置生成和专项校验阶段的固定规则。

主流程控制权仍在 `workflow/` 规则层：

- 意图判定、素材同名确认、任务清单、新建游戏、导入保存、回读比对、预览和发布都由主流程决定。
- 本文不得作为独立完整链路执行，不得因为进入贪吃小怪兽专项就自动新建游戏、导入或发布。
- 当 `workflow_planner.py` 的任务单进入 `generate_config` 且 `game_subtype=monster` 时，才调用本文件中的生成规则。
- 当任务单进入 `validate` 且 `game_subtype=monster` 时，才调用本文件中的校验规则。

---

## 主流程挂载点

```text
任务输入 / Router / Planner
  -> 题目来源导出（fetch_yach_sheet.py 或本地 xlsx）
  -> 当前 sheet 资源解析（resolve_sheet_resources.py）
  -> 任务清单锁定 game_family=template_game, game_subtype=monster
  -> 配置生成（本文：build_sj6_monster_config.py）
  -> 配置校验（本文：validate_monster_config.py）
  -> 后续创建 / 导入 / 回读 / 预览 / 发布（主流程）
```

阻塞规则：

- 没有题目 Excel、资源 JSON、模板 JSON 或输出路径时，停在任务清单阶段补齐。
- `resolve_sheet_resources.py` 只检查当前 sheet 实际引用的资源名。当前任务引用资源存在同名时，停在素材确认阶段；历史资源库中无关同名不阻塞本任务。
- 不要在生成脚本里默认复用同名资源或默认改名上传。
- 用户要求“上传到已有 game_id / 返修 / 检查”时，不能从本文跳转到新建游戏。
- 生成或校验失败时，只返回失败原因，后续保存动作由主流程 guard 决定。

---

## Excel 题目表格式

| 列 | 字段 | 说明 |
|---|---|---|
| A | 题目序号 | 整数 |
| B | 音频命名 | 对应资源库中的音频文件名 |
| C | 题干图片 | 对应资源库中的图片文件名 |
| D | 题干文本 | 题干文字（可选） |
| E | 选项序号 | 整数 |
| F | 选项图片 | 对应资源库图片名 |
| G | 选项文本 | 选项文字 |
| H | 是否正确 | 1=正确，0=错误 |

---

## 关键参数与固定对应关系

```python
# 选项节点名（最多3个选项）
NODE_NAME_BY_OPTION = {1: "节点", 2: "节点_104", 3: "节点_103"}
RIGHT_ANIMATION_BY_OPTION = {1: "right_1_2", 2: "right_2_2", 3: "right_3_2"}
```

---

## 生成脚本规则

`scripts/build_sj6_monster_config.py` 当前是贪吃小怪兽通用参数化入口，默认仍兼容 SJ6 文件名，但推荐显式传参。

```bash
python3 scripts/build_sj6_monster_config.py \
  --xlsx <题目.xlsx> \
  --sheet <SheetName> \
  --resources <resources.json> \
  --template reference_configs/monster/贪吃_reference_clean.json \
  --output <输出.config.json> \
  --meta <输出.build-meta.json>
```

### 输入校验

生成前会先检查：

- 每题必须正好 3 个选项，选项序号必须是 `1/2/3`。
- 每题必须且只能有 1 个正确项。
- 资源名必须存在，且 category 必须匹配：题干音频为 `audio`，选项图片和题干图片为 `image`。
- 资源表中同名资源默认会阻塞；只有已经完成同名确认后，才可加 `--allow-duplicate-resource-names`。
- 支持 `pure_audio`、`no_audio_image`、`audio_text`、`audio_image` 四类题干；如果输入字段和模板承载组件不匹配，会阻塞并报出缺失的 prompt node。

推荐先用资源解析脚本生成本任务专用资源表，避免全量资源库里的历史重复名干扰：

```bash
python3 scripts/resolve_sheet_resources.py \
  --xlsx <题目.xlsx> \
  --sheet <SheetName> \
  --resources resources/latest_resources.json \
  --output <filtered.resources.json> \
  --manifest <resources.manifest.json>
```

之后把 `<filtered.resources.json>` 传给 `build_sj6_monster_config.py`。

### 题型记录

脚本会在 build-meta 中记录：

- `question_type`: `pure_audio` / `no_audio_image` / `audio_text` / `audio_image` / `no_audio_text`
- `option_type`: `image` / `text` / `mixed_or_layered`
- 每题题干模式、题干节点、音频/图片 URL、选项节点映射、点击组件映射、正确项、反馈动效。

### 题干图片/文字规则

- `pure_audio`：使用 `TitleStem` 承载题干音频，不需要中心题干视觉节点。
- `audio_text`：`stem_text` 写入中心 `MLabel` 题干节点；节点按 `base=MLabel`、中心偏上位置识别，不依赖节点名。
- `audio_image`：`stem_img_name` 查资源后写入中心 `MSprite` 题干节点；节点按中心位置、尺寸和图片资源特征识别。
- `no_audio_image`：不要求 `TitleStem`，`stem_img_name` 写入中心 `MSprite` 题干节点；下方文字选项节点按 x 坐标左中右映射。
- 如果模板里找不到对应中心文字/图片节点，脚本必须阻塞，不能静默丢弃题干字段。

### 题干音频统一规则

当前仓库统一为：

- `TitleStem.clickEnd.source.MAudio.value` 写题干音频。
- `TitleStem.compLoadFinish.source.MAudio.value` 必须清空。
- `TitleStem.compLoadFinish.jump` 必须为 `countdown -> clickEnd`。
- `TitleStem.level_correct.active` 必须为隐藏态。

不再保留首关自动播放题干音频。

### 选项视觉与点击判定

选项视觉写在节点组件：

| 选项序号 | 位置 | 视觉节点 | 点击判定 |
|---|---|---|---|
| 1 | 左 | `节点` | x < -200 的 `AloneClickChoice` |
| 2 | 中 | `节点_104` | -200 <= x < 200 的 `AloneClickChoice` |
| 3 | 右 | `节点_103` | x >= 200 的 `AloneClickChoice` |

图片选项写 `MSprite.value`，文字选项写 `MLabel.value`。若模板有独立选项文字层，则按文字节点 x 坐标左中右同步写入；文字选项不会清空选项底图。

### 正确项与反馈

- 正确项点击组件：`anwserRadio = 1`
- 错误项点击组件：`anwserRadio = 2`
- 只有正确项视觉节点保留 `level_correct`，且 active 为 hide。
- 错误项视觉节点必须移除 `level_correct`。
- `节点_102.level_correct.source.MSpine.animation` 根据正确项写入：
  - 1 -> `right_1_2`
  - 2 -> `right_2_2`
  - 3 -> `right_3_2`

---

## 校验脚本说明

必跑：

```bash
python3 scripts/validate_monster_config.py <输出.config.json> --meta <输出.build-meta.json>
```

可选，仅在任务单锁定了同一参考模板且需要结构差异排查时使用：

```bash
python3 scripts/check_monster_vs_ref.py <输出.config.json> <reference.json> <关卡数>
```

- `validate_monster_config.py`：检查根结构、TitleStem 音频规则、题干写入、选项节点/点击组件映射、正确项唯一、`level_correct` 隐藏态、错误项无 `level_correct`、反馈动效和 build-meta 是否一致。
- `check_monster_vs_ref.py`：对比参考配置与生成配置，找出组件顺序或结构差异；不同题型模板之间不要强行对比。

---

## 组件渲染顺序

**⚠️ 渲染层级 = `components[]` 数组顺序（越靠后越在上层），zIndex 字段仅作编辑器排序参考，不影响运行时渲染。**

贪吃小怪兽为「复制替换型」游戏，所有组件顺序来自参考模板 deepcopy，**不在生成脚本中重排**。只要基准模板的 `components[]` 顺序正确，生成结果即正确。

当前参考配置组件顺序（从数组前到后）：

```
[背景] → [节点_102(小怪兽反馈动效)] → [关卡数组件] → [TitleStem(题干音频)]
→ [节点/节点_103/节点_104(选项视觉)] → [AloneClickChoice(点击判定)]
→ [节点_106(错误遮罩/错误反馈)]
```

> 选项图片/文字通过 `节点` 组件展示，点击逻辑通过 `AloneClickChoice` 组件判定，两者在数中先后配对。

---

## 相关文件

| 文件 | 说明 |
|---|---|
| `scripts/build_sj6_monster_config.py` | 主生成脚本 |
| `scripts/validate_monster_config.py` | 专项校验 |
| `scripts/resolve_sheet_resources.py` | 从当前 sheet 提取资源名并输出本任务 filtered resources |
| `scripts/fetch_yach_sheet.py` | 跨平台导出 Yach/知音楼在线表格 |
| `workflow/workflow_executor.py` | 唯一执行入口；按 planner steps 调用本游戏适配 |
| `workflow/run_courseware_task.py` | 旧命令兼容壳，仅转发到 workflow_executor.py |
| `scripts/check_monster_vs_ref.py` | 同模板参考对比 |
| `scripts/fix_j8_monster.py` | 修复特定版本配置问题 |
