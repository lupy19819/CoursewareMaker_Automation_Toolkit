# 魔法拼拼乐专项生成与校验规则

## 概览

本文只描述主流程中「模板游戏 > 魔法拼拼乐」在配置生成和专项校验阶段的固定规则。

意图判定、素材同名确认、任务清单、新建游戏、导入保存、回读比对、预览和发布都由主流程 `workflow/` 控制。本文不得作为独立完整链路执行。

---

## 主流程挂载点

```text
任务输入 / Router / Planner
  -> 素材确认与同名资源确认（主流程）
  -> 任务清单锁定 game_family=template_game, game_subtype=magic_spelling
  -> 配置生成（本文：generate_mofappl_config.py / fix_mofappl_v3.py）
  -> 配置校验（本文：结构参考 + 魔法拼拼乐专项规则）
  -> 后续创建 / 导入 / 回读 / 预览 / 发布（主流程）
```

---

## 数据来源

| 来源 | 说明 |
|---|---|
| 题目 JSON | `--input <题目.json>`，含句子、音频、槽位、选项、固定文本结构 |
| 校验基准 | `reference_configs/spelling_validation_ref.json`（只作参考结构/资源校验，不作为正式题目来源） |
| 结构参考 | `output/mofappl_configs/77cb396a-babd-11f0-885a-ba4dce53cceb.json`（5槽模板） |

---

## 数据映射规则

| 表格字段 | 魔法拼拼乐对应 | 备注 |
|---|---|---|
| `拖拽放置区`（type） | `LDragPlace` 组件，itemList=[答题区内容] | 每关槽位数 = 拖拽放置区数量 |
| 选项文本 | `MDraggable` 组件，tag=选项文本 | |
| `英语空格`（type） | **跳过，不生成组件** | 由文本头/尾图片留白实现 |
| `文本(固定)` | **跳过，不生成组件** | 固定内容画进图里 |
| 题干图片 URL | `题目配图` 组件的 source.MSprite.value | 从校验基准文件提取 |
| 题目音频 URL | `喇叭` 组件的 source.MAudio.value | 从校验基准文件提取 |
| `文本-xx`（固定字母） | `MLabel` 组件，name=`文本-xx` | 如 `文本-a`、`文本-the` |

---

## 组件层级规则

> **关键**：渲染顺序由 JSON `components` 数组顺序决定，**不是 zIndex**。  
> 数组越靠后 = 面板越靠下 = 层级越高（渲染在上层）。

标准层级顺序（从底层到顶层，即数组从前到后）：

```
节点
题目配图
题图光效
投影1
投影2
IP角色
关卡数组件
喇叭
拖拽放置区1..N
英语空格1..M（占位，默认隐藏）
文本-xx（固定字母，如 文本-a）
英语空格（剩余）
文本-fin          ← 句子展示组件
IP角色烟雾遮挡    ← 必须在文本-fin 之后（层级高于 fin）
拖拽物品1..K      ← 最高层，在所有组件之上
```

---

## 组件 State 规则

### 拖拽放置区 / 文本-xx（固定字母）
- `default`：`active=show`
- `compLoadFinish`：`active=hide`，倒计时3秒→default（与文本-fin展示句子同步隐藏后显现）

### 文本-fin（句子展示）
- `default`：`active=hide`
- `compLoadFinish`：`active=show`，倒计时3秒→default（展示3秒后隐藏，gameplay出现）

### 拖拽物品
- `default`：隐藏（active=hide）
- 各答题状态：show/placed/dragging/correct/wrong

---

## 脚本

| 脚本 | 用途 |
|---|---|
| `scripts/generate_mofappl_config.py` | 从题目数据生成配置 JSON |
| `scripts/fix_mofappl_v3.py` | 修复坐标偏移、尺寸、state 等问题 |

---

## 生成流程

```bash
python3 scripts/generate_mofappl_config.py \
  --input data/magic_spelling_questions.json \
  --output output/mofappl_configs/<游戏名>.json \
  --meta output/mofappl_configs/<游戏名>.build-meta.json

# 可选：修复坐标/尺寸/state
python3 scripts/fix_mofappl_v3.py output/mofappl_configs/新游戏名.json

# 后续导入保存、回读、预览由主流程执行
```

正式输入示例：

```json
{
  "questions": [
    {
      "sentence": "make a snowman",
      "sentence_parts": [
        {"type": "slot", "content": "m"},
        {"type": "slot", "content": "ake"},
        {"type": "space", "content": " "},
        {"type": "fixed", "content": "a"},
        {"type": "space", "content": " "},
        {"type": "slot", "content": "snowman"}
      ],
      "slots": ["m", "ake", "snowman"],
      "items": ["snowman", "ake", "m"],
      "audio_url": "https://...mp3"
    }
  ]
}
```

模板骨架、皮肤资源、组件状态结构可以来自固定参考配置；`sentence/sentence_parts/slots/items/audio_url` 属于题目相关信息，正式任务必须从 `--input` 读取。

---

## 关键参数

```python
# 组件 component_id
SLOT_COMPONENT_ID  = 'f9b49402-f73d-11ee-b9ef-8e2f78cd4bcd'   # LDragPlace
ITEM_COMPONENT_ID  = 'd8b73bec-f719-11ee-b9ef-8e2f78cd4bcd'   # MDraggable

# 拖拽物品布局
ITEM_Y       = -342.35
ITEM_STEP_X  = 368         # 每个物品横向间距

# 坐标系
# 校验文件中心 x = -163.89，需 +163.89 对齐画布中心

# 文本颜色
TEXT_COLOR_LABEL  = '#5f5cd7'   # 文本-xx
ITEM_DEFAULT      = '#cc601b'
ITEM_CORRECT      = '#2f9b1f'
ITEM_WRONG        = '#f51515'

# 文本头背景图（固定不变）
TEXT_BG_URL = 'https://courseware-maker-1252161091.cos.ap-beijing.myqcloud.com/assets/image/345733/2026-04-29/fdae75aa5ed239208875fdd6a9810489.png'
```

---

## 校验检查项

生成后用 `spelling_validation_ref.json` 做如下校验：

- [ ] 每关槽位数量与表格一致
- [ ] 每关拖拽物品 tag 与表格选项列一致
- [ ] 题目配图 URL 与校验基准匹配
- [ ] 题目音频 URL 与校验基准匹配
- [ ] IP角色烟雾遮挡在数组中位于 文本-fin 之后、拖拽物品之前
- [ ] 文本-xx 有 compLoadFinish=hide+3s 状态
- [ ] 文本-fin 有 compLoadFinish=show+3s 状态


---
## ⚠️ 重要规则（2026-05-11）

**句子和作答区排布必须按每题实际需求灵活处理，不能照搬结构模板！**
- 每题槽位数量、组件顺序、排布方式根据题目数据动态确定
- 模板仅作为组件类型和参数参考，不作为排布参考
