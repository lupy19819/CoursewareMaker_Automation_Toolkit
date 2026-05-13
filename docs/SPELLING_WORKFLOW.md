# 单词拼拼乐配置生成工作流

## 概览

从题目数据生成单词拼拼乐游戏配置，通过 CDP 注入编辑器保存。与魔法拼拼乐共用同一套题目数据格式。

---

## 完整流程

```
1. 上传素材（题目图片 + 单词音频）
   └─ node scripts/courseware_bulk_upload_assets.mjs <folder> --category image
   └─ node scripts/courseware_bulk_upload_assets.mjs <folder> --category audio
   └─ 上传完成后 URL 记录在 output/upload_log.jsonl

2. 同步上传记录到知音楼资源表（自动/手动）
   └─ python3 scripts/sync_uploads_to_sheet.py
   └─ 同步成功后 python3 scripts/mark_synced.py 标记已同步

3. 编辑题目数据
   └─ 在 generate_spelling_config.py 的 LEVELS 数组中填写：
       - text: 句子全文
       - answer_area: 答题区（slot/space/fixed 三类）
       - items: 拖拽选项列表（乱序）
       - word_audio_url: 单词音频 URL
       - word_image_url: 题目插图 URL

4. 生成配置 JSON（生成内层 cfg）
   └─ python3 scripts/generate_spelling_config.py
   └─ 输出：output/spelling_configs/<游戏名>.json

5. 上传配置到编辑器
   └─ python3 scripts/upload_game_config.py <game_id> <config.json>

6. 备份/对比（可选）
   └─ node scripts/fetch_spelling_configs.js
   └─ 抓取线上配置用于校验对比
```

---

## 答题区三种组件类型

| 类型 | 说明 | 生成组件 |
|---|---|---|
| `slot` | 拖拽放置区，学生需拖入正确音节 | `LDragPlace`，content=正确答案 |
| `space` | 词间空格（不可交互） | `MSprite` 透明占位图，默认隐藏 |
| `fixed` | 固定字母/单词（不可拖拽） | `MLabel`，content=固定文字 |

---

## 题目数据示例

```python
{
    "text": "make a snowman",
    "answer_area": [
        {"type": "slot", "content": "m"},
        {"type": "slot", "content": "ake"},
        {"type": "space"},          # "a" 前的空格
        {"type": "fixed", "content": "a"},
        {"type": "space"},          # "snowman" 前的空格
        {"type": "slot", "content": "sn"},
        {"type": "slot", "content": "ow"},
        {"type": "slot", "content": "man"},
    ],
    "items": ["sn", "ake", "m", "ow", "man"],  # 乱序选项
    "word_audio_url": "https://...mp3",
    "word_image_url": "https://...png",
}
```

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
| `scripts/upload_game_config.py` | 上传配置到 CoursewareMaker |
| `scripts/fetch_spelling_configs.js` | 抓取线上配置备份 |
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
