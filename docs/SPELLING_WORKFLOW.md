# 单词拼拼乐专项生成与校验规则

## 概览

本文只描述主流程中「模板游戏 > 单词拼拼乐」在配置生成和专项校验阶段的固定规则。与魔法拼拼乐共用同一套题目数据格式。

意图判定、素材同名确认、任务清单、新建游戏、导入保存、回读比对、预览和发布都由主流程 `workflow/` 控制。本文不得作为独立完整链路执行。

---

## 主流程挂载点

```
任务输入 / Router / Planner
  -> 素材确认与同名资源确认（主流程）
  -> 任务清单锁定 game_family=template_game, game_subtype=spelling
  -> 配置生成（本文：generate_spelling_config.py）
  -> 配置校验（本文：reference_configs/spelling_validation_ref.json + 专项规则）
  -> 后续创建 / 导入 / 回读 / 预览 / 发布（主流程）
```

生成前必须锁定：

- `--input <题目.json>` 动态题目数据来源；不得通过临时修改脚本内 `LEVELS` 承载正式题目。
- 题目插图和单词音频的最终 URL。
- 输出路径和参考校验配置。
- 同名资源处理结论。

---

## 答题区三种组件类型

| 类型 | 说明 | 生成组件 |
|---|---|---|
| `slot` | 拖拽放置区，学生需拖入正确音节 | `LDragPlace`，content=正确答案 |
| `space` | 词间空格（不可交互） | `MSprite` 透明占位图，默认隐藏 |
| `fixed` | 固定字母/单词（不可拖拽） | `MLabel`，content=固定文字 |

---

## 题目数据示例

```json
{
  "levels": [
    {
      "text": "make a snowman",
      "answer_area": [
        {"type": "slot", "content": "m"},
        {"type": "slot", "content": "ake"},
        {"type": "space"},
        {"type": "fixed", "content": "a"},
        {"type": "space"},
        {"type": "slot", "content": "sn"},
        {"type": "slot", "content": "ow"},
        {"type": "slot", "content": "man"}
      ],
      "items": ["sn", "ake", "m", "ow", "man"],
      "word_audio_url": "https://...mp3",
      "word_image_url": "https://...png"
    }
  ]
}
```

正式生成命令：

```bash
python3 scripts/generate_spelling_config.py \
  --input data/spelling_questions.json \
  --output output/spelling_configs/<游戏名>.json \
  --meta output/spelling_configs/<游戏名>.build-meta.json
```

脚本内固定的背景、桌子、fin 动效、喇叭 spine、状态 key、组件 id、词卡皮肤图等属于模板固定资源，可以保留为常量；`text/answer_area/items/word_audio_url/word_image_url` 属于题目相关信息，正式任务必须来自 `--input`。

---

## 组件渲染顺序

**⚠️ 渲染层级 = `components[]` 数组顺序（越靠后越在上层），zIndex 字段仅作编辑器排序参考，不影响运行时渲染。**

组装组件时必须严格按以下顺序（从底层→顶层）：

```
[背景] → [桌子] → [拖拽放置区] → [英语空格] → [固定文本]
→ [遮挡背景] → [fin动效] → [文本-fin] → [节点_37(配图)]
→ [关卡数组件] → [烟雾动效] → [喇叭]
→ [拖拽物品]  ← 最后 = 最顶层，保证可拖拽交互
```

> 脚本中 `generate_level()` 函数已按此顺序组装 components 数组。

---

## 与魔法拼拼乐的数据复用关系

同一份题目数据可同时生成单词拼拼乐和魔法拼拼乐两种游戏配置：

| 字段 | 单词拼拼乐 | 魔法拼拼乐 |
|---|---|---|
| `slot` | 生成 LDragPlace | 生成 LDragPlace |
| `space` | 生成隐藏占位 MSprite | **跳过** |
| `fixed` | 生成 MLabel | **跳过**（画进图里） |
| `word_image_url` | 题目配图 | 题目配图 |
| `word_audio_url` | 喇叭音频 | 喇叭音频 |

---

## 校验基准文件

`reference_configs/spelling_validation_ref.json`

- 从线上单词拼拼乐游戏抓取
- 包含完整 component 结构，用于校验生成配置的结构和资源 URL

---

## 相关文件

| 文件 | 说明 |
|---|---|
| `scripts/generate_spelling_config.py` | 主生成脚本（输出内层 cfg） |
| `scripts/fetch_spelling_configs.js` | 抓取线上配置备份/对比 |
| `reference_configs/spelling_validation_ref.json` | 校验基准 |


---
## 组件渲染顺序

**⚠️ 渲染层级 = `components[]` 数组顺序（越靠后越在上层），zIndex 字段仅作编辑器排序参考，不影响运行时渲染。**

标准层级顺序（从底层→顶层，即数组从前→后）：

```
[背景] → [桌子(装饰)] → [fin动效] → [遮挡烟雾动效] → [喇叭]
→ [节点_37(题目配图)] → [文本-fin(完整单词展示)] → [文本头] → [文本尾]
→ [拖拽放置区X] [英语空格] [文本-XX(固定字母)]  ← 作答区
→ [遮挡背景]
→ [拖拽物品X]  ← 最后 = 最顶层，保证可拖拽交互
```

> 注意：拖拽物品虽在顶层，但通过 state 机制在开场时隐藏（K_ITEM_HIDE），遮挡背景隐藏后再显示。

---
## ⚠️ 重要规则（2026-05-11）

**句子和作答区排布必须按每题实际需求灵活处理，不能照搬结构模板！**
- 每题槽位数量、组件顺序、排布方式根据题目数据动态确定
- 模板仅作为组件类型和参数参考，不作为排布参考
