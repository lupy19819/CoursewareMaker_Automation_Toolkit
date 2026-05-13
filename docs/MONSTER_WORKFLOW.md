# 贪吃小怪兽配置生成工作流

## 概览

从 Excel 题目表 + 资源库 JSON，生成贪吃小怪兽游戏配置，并导入 CoursewareMaker。

---

## 完整流程

```
1. 上传素材
   └─ 将图片/音频放到本地目录
   └─ node scripts/courseware_bulk_upload_assets.mjs <folder> --category image/audio
   └─ 上传完成后 URL 写入 output/upload_log.jsonl，同步到知音楼资源表

2. 拉取最新资源库（可选，获取已有素材 URL）
   └─ python3 scripts/sync_courseware_resources.py
   └─ 输出：latest_resources.json

3. 生成配置 JSON
   └─ python3 scripts/build_sj6_monster_config.py
   └─ 输入：
       - QUESTION_XLSX: 题目 Excel（Sheet: Sj6贪吃小怪兽）
       - RESOURCE_JSON: latest_resources.json
       - TEMPLATE_JSON: monster_template_from_localstorage.json
   └─ 输出：Sj6贪吃小怪兽.config.json

4. 校验配置（可选）
   └─ python3 scripts/validate_monster_config.py
   └─ python3 scripts/check_monster_vs_ref.py

5. 创建游戏
   └─ node scripts/create_game_auto.js → 获得 game_id

6. 导入配置
   └─ python3 scripts/upload_game_config.py <game_id> Sj6贪吃小怪兽.config.json

7. 发布
   └─ node scripts/publish_game_auto.js
```

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

## 关键参数

```python
# 选项节点名（最多3个选项）
NODE_NAME_BY_OPTION = {1: "节点", 2: "节点_104", 3: "节点_103"}
RIGHT_ANIMATION_BY_OPTION = {1: "right_1_2", 2: "right_2_2", 3: "right_3_2"}
```

---

## 校验脚本说明

- `validate_monster_config.py`：检查配置结构完整性
- `check_monster_vs_ref.py`：对比参考配置与生成配置，找出差异

---

## 组件渲染顺序

**⚠️ 渲染层级 = `components[]` 数组顺序（越靠后越在上层），zIndex 字段仅作编辑器排序参考，不影响运行时渲染。**

贪吃小怪兽为「复制替换型」游戏，所有组件顺序来自参考模板 deepcopy，**不在生成脚本中重排**。只要基准模板的 `components[]` 顺序正确，生成结果即正确。

标准层级顺序（从底层→顶层，即数组从前→后）：

```
[背景] → [装饰层] → [TitleStem(题干)] → [关卡数组件]
→ [节点/节点_103/节点_104(选项节点)] → [AloneClickChoice(点击判定)]
→ [节点_102(小怪兽反馈动效)]
```

> 选项图片/文字通过 `节点` 组件展示，点击逻辑通过 `AloneClickChoice` 组件判定，两者在数中先后配对。

---
## 组件渲染顺序

**⚠️ 渲染层级 = `components[]` 数组顺序（越靠后越在上层），zIndex 字段仅作编辑器排序参考，不影响运行时渲染。**

贪吃小怪兽为「复制替换型」游戏：从模板 JSON deepcopy 完整关卡后，仅替换内容字段（音频、图片、文字、正确项标记），**不重排 components 数组**。因此渲染顺序完全由模板 JSON 决定，生成脚本不干预。

如果模板的 components 顺序有问题（如选项节点被其他组件遮挡），需在模板源头修复，而非在生成脚本中处理。

---

## 相关文件

| 文件 | 说明 |
|---|---|
| `scripts/build_sj6_monster_config.py` | 主生成脚本 |
| `scripts/validate_monster_config.py` | 结构校验 |
| `scripts/check_monster_vs_ref.py` | 与参考对比 |
| `scripts/fix_j8_monster.py` | 修复特定版本配置问题 |
