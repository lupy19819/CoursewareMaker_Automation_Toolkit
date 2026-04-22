# 标准化题型工具集成指南

> **版本**: 1.1.0  
> **更新时间**: 2026-04-16  
> **新增内容**: 标准化选择题、填空题、拖拽题生成工具

---

## 📋 概述

本文档说明如何将**标准化题型生成工具**集成到CoursewareMaker自动化工作流中。

标准化题型工具支持：
- ✅ 选择题 (`AloneClickChoice`)
- ✅ 填空题 (`QuestionForBlank`)
- ✅ 拖拽题 (`MDraggbale` + `LDragPlace`)
- ✅ 竖式/算式填空题（网格布局）
- ✅ 单关拆分（多关→单关）
- ✅ 皮肤复用（沙滩/图纸/紫色星空）

---

## 📂 工具集位置

```
CoursewareMaker_Automation_Toolkit/
└── standard_question_toolkit/        ← 新增！
    ├── README_FOR_CLAUDE.md          # 工具集入口文档
    ├── MANIFEST.md                   # 文件清单
    │
    ├── docs/                         # 文档
    │   ├── standard_workflow.md      # 标准化题型生成流程
    │   ├── question_input_template.md # 结构化题目输入模板
    │   └── claude_prompt.md          # Claude提示词
    │
    ├── data/                         # 数据
    │   ├── component_skin_inventory.json  # 皮肤资源清单（机器可读）
    │   ├── component_skin_inventory.md    # 皮肤资源清单（人类可读）
    │   ├── skin_resource_table.tsv        # 皮肤资源表
    │   └── skin_text_color_usage.tsv      # 文字颜色用途表
    │
    ├── scripts/                      # 脚本
    │   ├── extract_component_skins.py     # 提取皮肤素材
    │   ├── generate_grade3_config.py      # 三年级配置生成示例
    │   ├── generate_grade4_config.py      # 四年级配置生成示例
    │   ├── split_xiner_games.py           # 新二多关拆单关
    │   └── split_xinyi_games.py           # 新一多关拆单关
    │
    └── templates/                    # 模板
        ├── base_choice_fill_template.json      # 选择题/填空题模板
        └── vertical_multiplication_template.json # 竖式填空题模板
```

---

## 🔄 更新后的完整工作流

### 原工作流（8步）
```
0. 资源同步（可选）
1. 素材批量上传
2. 再次同步资源库
3. 生成游戏配置 ← 这里增强！
4. 创建游戏
5. 导入配置
6. 生成分享链接
7. 发布游戏
```

### 增强的"步骤3: 生成游戏配置"

现在支持两种配置生成方式：

#### 方式A：运动PK/贪吃小怪兽（原有）
```bash
# 运动PK配置生成
python scripts/build_yundong_pk_config.py 题目表.xlsx

# 贪吃小怪兽配置生成
python scripts/build_sj6_monster_config.py 题目表.xlsx
```

#### 方式B：标准化题型（新增！）
```bash
# 使用标准化题型生成脚本
python standard_question_toolkit/scripts/generate_grade3_config.py

# 或使用AI辅助生成
# 1. 整理题目为结构化格式（见 question_input_template.md）
# 2. 使用模板生成配置
# 3. 校验配置完整性
```

---

## 🎯 支持的题型

### 1. 选择题 (`AloneClickChoice`)

**组件特征**：
- `component_id`: `3b9b8ec3-f7d3-11ee-b9ef-8e2f78cd4bcd`
- 手动判定：`autoJudge = 0`, `judgeRule = 0`
- 正确项：`anwserRadio = 1`
- 错误项：`anwserRadio = 2`

**配置示例**：
```json
{
  "type": "choice",
  "stem": "长方形长16厘米，宽4厘米，面积是（  ）平方厘米。",
  "options": ["64", "40", "20", "60"],
  "answerIndex": 0,
  "image": null
}
```

### 2. 填空题 (`QuestionForBlank`)

**组件特征**：
- `component_id`: `0b26ef14-f7e0-11ee-b9ef-8e2f78cd4bcd`
- 答案字段：`anwserConfig.anwser`
- 输入上限：`fillInteractive.numberUnit`
- 普通输入框尺寸：`218 x 131`

**配置示例**：
```json
{
  "type": "fill",
  "stem": "简便计算",
  "rows": [
    {"label": "4.47 + 2.38 + 4.53 + 4.62 =", "answer": "16"},
    {"label": "4.1 + 1.3 + 1.7 - 1.1 =", "answer": "6"}
  ],
  "image": null
}
```

### 3. 内嵌填空题

**配置示例**：
```json
{
  "type": "inline_fill",
  "stem": "田田共有    种搭配方案。",
  "answer": "12",
  "image": null
}
```

### 4. 竖式填空题

**配置示例**：
```json
{
  "type": "vertical_fill",
  "stem": "在方框里填上合适的数，使竖式成立",
  "grid": [
    ["blank", "2", "blank"],
    ["×", "", "7"],
    ["line", "line", "line"],
    ["blank", "0", "blank", "1"]
  ],
  "answers": ["6", "7", "7"]
}
```

### 5. 拖拽题 (`MDraggbale` + `LDragPlace`)

**组件特征**：
- 拖拽项：`d8b73bec-f719-11ee-b9ef-8e2f78cd4bcd`
- 放置区：`f9b49402-f73d-11ee-b9ef-8e2f78cd4bcd`

**配置示例**：
```json
{
  "type": "drag",
  "stem": "把正确答案拖到对应位置。",
  "dragItems": [
    {"text": "A", "answerKey": "a"},
    {"text": "B", "answerKey": "b"}
  ],
  "dropZones": [
    {"text": "", "accept": "a"},
    {"text": "", "accept": "b"}
  ]
}
```

---

## 🎨 皮肤系统

### 支持的皮肤

| ID | 名称 | 背景图URL特征 | 特点 |
|----|------|--------------|------|
| 1 | 沙滩皮肤 | `a0d71ef21cdf...` | 暖色调，适合低年级 |
| 2 | 图纸皮肤 | `df49c4739e95...` | 工程风格，适合理科题 |
| 3 | 紫色星空皮肤 | `edb8ccb1e5ae...` | 科技感，适合高年级 |

### 皮肤资源包含

每个皮肤包含：
- ✅ 背景图
- ✅ 输入框素材
- ✅ 放置区素材
- ✅ 拖拽项素材
- ✅ 题干背景
- ✅ 文字颜色方案

详见：`standard_question_toolkit/data/skin_resource_table.tsv`

---

## 📝 使用方法

### 方法1：使用现成脚本

```bash
# 三年级题目生成
python standard_question_toolkit/scripts/generate_grade3_config.py

# 四年级题目生成
python standard_question_toolkit/scripts/generate_grade4_config.py
```

**适用场景**：
- 快速生成标准格式的配置
- 参考具体实现示例
- 学习布局和皮肤应用

### 方法2：AI辅助生成（推荐）

**步骤**：

1. **整理题目为结构化格式**
   ```bash
   # 参考模板
   cat standard_question_toolkit/docs/question_input_template.md
   ```

2. **给AI提供完整上下文**
   ```
   请根据以下题目生成CoursewareMaker配置：
   - 阅读: standard_question_toolkit/README_FOR_CLAUDE.md
   - 遵循: standard_question_toolkit/docs/standard_workflow.md
   - 布局: standard_question_toolkit/docs/layout_generation_method.md
   - 参考: standard_question_toolkit/docs/question_input_template.md
   ```

3. **使用模板生成配置**
   - 选择合适的模板（base_choice_fill 或 vertical_multiplication）
   - 根据题目类型替换关卡数组
   - 应用皮肤资源

4. **校验配置**
   - JSON可解析
   - 关卡数正确
   - 分值合计100
   - 组件ID正确
   - 皮肤资源完整

### 方法3：多关拆单关

```bash
# 新二年级：拆分12关游戏
python standard_question_toolkit/scripts/split_xiner_games.py

# 新一年级：拆分12关游戏
python standard_question_toolkit/scripts/split_xinyi_games.py
```

**适用场景**：
- 已有多关完整配置
- 需要拆分为独立单关游戏
- 每关单独发布和分享

---

## ✅ 配置校验清单

生成配置后必须检查：

### 基础检查
- [ ] JSON格式可解析
- [ ] `game` 数组长度正确
- [ ] 每关有唯一的 `id`
- [ ] 所有资源URL有效

### 题型检查
- [ ] **选择题**：只有一个正确项（`anwserRadio = 1`）
- [ ] **选择题**：手动判定（`autoJudge = 0`, `judgeRule = 0`）
- [ ] **填空题**：同题所有输入框 `numberUnit` 一致
- [ ] **填空题**：输入框尺寸不变形（`scaleX = 1`, `scaleY = 1`）
- [ ] **竖式题**：右对齐，已知数用文本，未知数用输入框
- [ ] **拖拽题**：保留 answer/judge 信息

### 布局检查
- [ ] 已按整关内容模型检查：题干/条件/作答句/算式/图表/输入框/选项/键盘/提交
- [ ] 已按认知区、关系区、操作区做整体布局
- [ ] 短题干居中，长题干左对齐
- [ ] 行内挖空使用足够全角空格占位，输入框跟随实际换行位置
- [ ] 有配图/表格题：题干、配图、答案区、操作区整体不冲突
- [ ] 算式行：文本和输入框作为一组居中
- [ ] 同类选择按钮九宫格一致
- [ ] 题干不包含题号
- [ ] 选项不额外添加A/B/C/D

### 分值检查
- [ ] 每关分值为整数
- [ ] 所有分值合计 = 100
- [ ] 单关拆分：每关 score = [100]

---

## 🔧 高级功能

### 1. 提取皮肤素材

```bash
python standard_question_toolkit/scripts/extract_component_skins.py
```

**用途**：
- 从已有配置文件中提取皮肤资源
- 更新皮肤清单
- 添加新皮肤

### 2. 自定义皮肤

**步骤**：
1. 上传新的皮肤素材到COS
2. 更新 `component_skin_inventory.json`
3. 添加到 `skin_resource_table.tsv`
4. 在配置中引用新皮肤

### 3. 批量处理

结合原有批量工具：
```bash
# 1. 批量生成配置
for i in {1..12}; do
  python generate_standard_config.py --level $i
done

# 2. 批量创建游戏
node scripts/batch_create_games.js

# 3. 批量导入配置
# （使用生成的配置列表）

# 4. 批量发布
node scripts/batch_publish_all_games.js
```

---

## 📚 参考文档

### 核心文档（优先阅读）
1. **standard_question_toolkit/README_FOR_CLAUDE.md**
   - 工具集入口说明
   - 推荐阅读顺序

2. **standard_question_toolkit/docs/standard_workflow.md**
   - 标准化题型生成流程
   - 题型分类和规则

3. **standard_question_toolkit/docs/question_input_template.md**
   - 结构化题目输入模板
   - 字段说明和示例

### 数据文档
4. **standard_question_toolkit/data/component_skin_inventory.md**
   - 皮肤资源详细清单
   - 三种皮肤的所有资源URL

5. **standard_question_toolkit/data/skin_resource_table.tsv**
   - 皮肤资源表格版
   - 可直接复制到Excel

### 脚本示例
6. **standard_question_toolkit/scripts/generate_grade4_config.py**
   - 完整的配置生成示例
   - 包含选择题、填空题、配图题

7. **standard_question_toolkit/scripts/split_xiner_games.py**
   - 多关拆单关示例
   - 分值重新计算

---

## 💡 最佳实践

### 1. 题目准备
- ✅ 先整理成结构化格式
- ✅ 明确题型（选择/填空/拖拽）
- ✅ 准备配图素材
- ✅ 选择合适的皮肤

### 2. 配置生成
- ✅ 从模板开始（不要从零编写）
- ✅ 复用已验证的组件结构
- ✅ 保持皮肤资源一致
- ✅ 使用标准组件ID

### 3. 质量保证
- ✅ 生成后立即校验
- ✅ 在编辑器中预览
- ✅ 测试每个交互
- ✅ 验证音效和动画

### 4. 版本管理
- ✅ 保存原始题目清单
- ✅ 备份生成的配置
- ✅ 记录皮肤选择
- ✅ 文档化特殊处理

---

## 🔗 集成示例

### 完整流程：从题目到上线

```bash
# Step 0: 准备题目（结构化格式）
# 参考 question_input_template.md

# Step 1: 生成配置（使用标准化工具）
python standard_question_toolkit/scripts/generate_grade4_config.py

# Step 2: 校验配置
python -m json.tool generated_config.json > /dev/null && echo "JSON valid"

# Step 3: 创建游戏
node scripts/create_game_auto.js "四年级数学诊断" "模板ID" ""

# Step 4: 导入配置
GAME_ID=$(cat latest_game_id.txt)
node scripts/save_game_config_via_cdp.js "$GAME_ID" "generated_config.json"

# Step 5: 生成分享链接
node scripts/generate_share_link.js "$GAME_ID"

# Step 6: 发布游戏
node scripts/publish_game_auto.js "$GAME_ID" 2026 "2" "3"  # 三年级
```

---

## 🎓 适用场景

### 适合使用标准化题型工具的情况
- ✅ 数学题目（选择题、填空题、竖式题）
- ✅ 需要统一皮肤风格
- ✅ 批量生成相似结构的题目
- ✅ 多关游戏需要拆分

### 适合使用原有工具的情况
- ✅ 运动PK类游戏
- ✅ 贪吃小怪兽类游戏
- ✅ 特殊交互的自定义游戏

### 两者结合
可以混合使用两套工具：
1. 用标准化工具生成基础配置
2. 用原有工具调整和优化
3. 统一使用批量发布流程

---

## 🆕 版本更新

### v1.1.0 (2026-04-16)
- ✅ 集成标准化题型生成工具
- ✅ 新增选择题、填空题、拖拽题支持
- ✅ 新增三种皮肤系统
- ✅ 新增多关拆单关功能
- ✅ 更新完整工作流文档

---

**最后更新**: 2026-04-16  
**版本**: 1.1.0
