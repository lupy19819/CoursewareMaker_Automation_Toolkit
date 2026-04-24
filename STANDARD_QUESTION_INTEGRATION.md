# 标准化题型工具集成指南

> **版本**: 1.3.0  
> **更新时间**: 2026-04-24  
> **新增内容**: 图层顺序强制规则、组件命名唯一性、算式右对齐、文本-填空一致性、序号处理、validate_config.js 字段路径修正

---

## 📋 概述

本文档说明如何将**标准化题型生成工具**集成到CoursewareMaker自动化工作流中。

标准化题型工具支持：
- ✅ 选择题 (`AloneClickChoice`)
- ✅ 填空题 (`QuestionForBlank`)
- ✅ 拖拽题 (`MDraggbale` + `LDragPlace`)
- ✅ 竖式/算式填空题（网格布局）
- ✅ 使用目的模式：诊断模式 / 非诊断练习模式
- ✅ 小中诊断三套布局：视觉选择、计算填空、图文推理
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
    │   ├── layout_constants.json          # 布局常量 + 皮肤-关卡映射（机器可读，校验脚本读取）← 新增！
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

### 任务类型：修改已有配置使其符合最新规范

当需要把存量游戏更新到最新皮肤/布局规范时，使用此专用流程，**不要复用"生成配置"流程**。

```
Step 1. 读取规范（必须先于任何改动）
        node -e "读取 layout_constants.json + component_skin_inventory.json"
        重点确认：skin_level_mapping、choice 坐标、keyboard.y、disabled 共用 URL

Step 2. 获取游戏现有 JSON（通过 CDP 或 API）
        fetch https://sszt-gateway.speiyou.com/beibo/game/config/game?game_id=<ID>

Step 3. 生成差异报告（先列再改）
        node scripts/validate_config.js <game_id>
        — 输出每关的不合规项，与操作者确认后再进行下一步

Step 4. 应用修改
        按差异报告逐项修改，每类问题改完后立即重验该类

Step 5. 再次运行校验脚本确认 0 错误
        node scripts/validate_config.js <game_id>

Step 6. 导入并保存
        node scripts/save_game_config_via_cdp.js <game_id> <patched_config.json>
```

> **关键原则：先列差异再动手，改完立刻再验。不允许跳过 Step 3 和 Step 5。**

---

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
  "stem": "搭配方案问题",
  "conditions": ["上衣3种，裙子2种，鞋子2种。"],
  "answerPrefix": "田田共有",
  "answerSuffix": "种搭配方案。",
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
  "conditions": ["观察下面的关系图。"],
  "dragItems": [
    {"text": "12", "answerKey": "a"},
    {"text": "16", "answerKey": "b"}
  ],
  "dropZones": [
    {"label": "第一个空", "accept": "a"},
    {"label": "第二个空", "accept": "b"}
  ],
  "layout": "drag"
}
```

**生成要求**：
- 先排 `LDragPlace`，再排 `MDraggbale`。
- 行内拖拽使用 `answerPrefix + LDragPlace + answerSuffix`，不使用空格占位。
- 拖拽项和放置区必须保留 answer/judge 信息。
- 皮肤需要覆盖拖拽物默认/拖拽中/已放置，以及放置区默认/可吸附/已放置。

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
   - 如果输入是 PDF 或图片，先逐题转写原题文本，再整理结构化格式
   - 题干、条件、选项、算式标签、作答句必须忠实保留原题，不得概括、简化、润色或改写

2. **给AI提供完整上下文**
   ```
   请根据以下题目生成CoursewareMaker配置：
   - 阅读: standard_question_toolkit/README_FOR_CLAUDE.md
   - 遵循: standard_question_toolkit/docs/standard_workflow.md
   - 布局: standard_question_toolkit/docs/layout_generation_method.md
   - 参考: standard_question_toolkit/docs/question_input_template.md
   ```

3. **使用模板生成配置**
   - 先确认使用目的：`diagnostic` 诊断模式或 `practice` 非诊断练习模式
   - 诊断模式：保留倒计时和草稿；正确/错误反馈音效可统一；答错一次后允许切关；选项/拖拽物/填空框正确错误状态可相同
   - 非诊断练习模式：去掉倒计时和草稿；区分正确/错误反馈音效；关闭错误后跳关，必须答对后才能切关；选项/拖拽物/填空框正确错误状态必须可区分；整关正确后播放撒花动效
   - 撒花动效使用 `MSpine` 组件的 `passSuccess` / `闯关成功` 状态监听全局判定成功，默认隐藏，成功后显示并播放动画和成功音效
   - 撒花资源和状态动作读取 `standard_question_toolkit/data/success_effect_assets.tsv` 或 `component_skin_inventory.json > global_assets.success_fireworks`
   - 选择合适的模板（base_choice_fill、vertical_multiplication 或拖拽题模板/参考关）
   - 模板只作为组件骨架，不能直接继承原坐标
   - 按当前题内容重新计算题干、配图、输入框、选项、拖拽物、放置区、键盘位置
   - 根据题目类型替换关卡数组
   - 应用皮肤资源和各状态资源

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

生成或修改配置后，**先运行自动校验脚本**，再执行人工清单：

```bash
# 自动校验（覆盖：皮肤 hash、选项坐标、键盘 y、disabled 共用 URL、填空框尺寸、z层级、命名唯一性）
node scripts/validate_config.js <game_id>
# 或指定本地文件
node scripts/validate_config.js --file generated_config.json
```

> **脚本字段路径**（修改或新增脚本时必须遵守，路径写错会导致修改静默失效）：
> - 组件真实名称：`component_data.name`（`component_name` 对大多数组件显示 `"节点"`，不可用于识别）
> - 组件 layout（位置/尺寸）：`component_data.states[0].transform`
> - 组件图片/资源 URL：`component_data.states[0].source.MSprite.value`
> - 组件 zIndex：`component_data.zIndex`

校验通过后，再做下列人工检查：

### 基础检查
- [ ] JSON格式可解析
- [ ] `game` 数组长度正确
- [ ] 每关有唯一的 `id`
- [ ] 所有资源URL有效
- [ ] PDF/图片输入已逐题转写原文，用户可见题目文字没有被简化或改写
- [ ] 已明确 `purpose`：诊断模式或非诊断练习模式
- [ ] 诊断模式：倒计时、草稿、统一反馈音效、错误后切关策略符合诊断要求
- [ ] 非诊断练习模式：无倒计时、无草稿，正确/错误音效区分，错误后不跳关，必须答对后切关
- [ ] 非诊断练习模式：选择题选项、拖拽题选项、填空题填空框有可区分的正确/错误状态资源
- [ ] 非诊断练习模式：配置撒花动效，`default` 隐藏，`passSuccess` 显示并播放 Spine 动画和成功音效

### 题型检查
- [ ] **选择题**：只有一个正确项（`anwserRadio = 1`）
- [ ] **选择题**：手动判定（`autoJudge = 0`, `judgeRule = 0`）
- [ ] **填空题**：同题所有输入框 `numberUnit` 一致
- [ ] **填空题**：输入框尺寸不变形（`scaleX = 1`, `scaleY = 1`）
- [ ] **竖式题**：右对齐，已知数用文本，未知数用输入框
- [ ] **拖拽题**：保留 answer/judge 信息
- [ ] **拖拽题**：使用 `MDraggbale` + `LDragPlace`，不是选择题/填空题替代
- [ ] **拖拽题**：每个拖拽物 `answerKey` 与放置区 `accept` 绑定正确
- [ ] **拖拽题**：拖拽物默认/拖拽中/已放置，放置区默认/可吸附/已放置状态资源正确

### 布局检查
- [ ] 已按整关内容模型检查：题干/条件/作答句/算式/图表/输入框/选项/键盘/提交
- [ ] 原配置/模板只复用组件骨架和交互字段，坐标按当前题内容重新排版
- [ ] 已按认知区、关系区、操作区做整体布局
- [ ] 小中诊断题已按 `diagnostic_visual_choice` / `diagnostic_compute_fill` / `diagnostic_image_reasoning` 三套之一选版
- [ ] 短题干居中，长题干左对齐
- [ ] 行内填空/拖拽使用前文 + 输入框/放置区 + 后文三段结构，后文接在框右边缘
- [ ] 有配图/表格题：题干、配图、答案区、操作区整体不冲突
- [ ] 算式行：文本和输入框作为一组居中
- [ ] 算式类文本 `alignType: right`，文本框右边缘对齐输入框左边缘（gap ≤ 8px）
- [ ] 同类选择按钮九宫格一致
- [ ] 题干不包含独立题号，但保留原题完整表达
- [ ] 选项不额外添加A/B/C/D
- [ ] 文本内容无 `（1）（2）（3）` 序号前缀，多条件已拆为独立文本组件
- [ ] 同行 `文本–填空框–文本` 字号和行间距一致；换行情况下已按行手动拆分为独立文本组件
- [ ] 每关坐标独立按本关内容计算，非模板直接套用
- [ ] 配图与题干、填空框、键盘无 bounding box 重叠

### 图层检查

- [ ] `【题型说明】` `zIndex = 0`（最低）
- [ ] `【勿动】背景图片` `zIndex = 1`
- [ ] 配图 `zIndex = 3`
- [ ] 所有 `文本-*` 组件 `zIndex = 4`
- [ ] 输入框、键盘、选项、拖拽物等交互组件 `zIndex ≥ 5`

### 组件命名检查

- [ ] 同一游戏内所有关卡所有组件 `component_data.name` 无重复

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

# Step 1: 读取规范常量（必须在生成前完成）
# 阅读 standard_question_toolkit/data/layout_constants.json
# 确认皮肤-关卡映射、选项坐标、键盘 y 等规范值

# Step 2: 生成配置（使用标准化工具）
python standard_question_toolkit/scripts/generate_grade4_config.py

# Step 3: 自动合规校验（必须通过，0 错误后再进行下一步）
node scripts/validate_config.js --file generated_config.json

# Step 4: 创建游戏
node scripts/create_game_auto.js "四年级数学诊断" "模板ID" ""

# Step 5: 导入配置
GAME_ID=$(cat latest_game_id.txt)
node scripts/save_game_config_via_cdp.js "$GAME_ID" "generated_config.json"

# Step 6: 导入后再验一次（确认写入内容一致）
node scripts/validate_config.js "$GAME_ID"

# Step 7: 生成分享链接
node scripts/generate_share_link.js "$GAME_ID"

# Step 8: 发布游戏
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

### v1.3.0 (2026-04-24)
- ✅ 新增图层顺序强制规则：题型说明=z0 / 背景=z1 / 配图=z3 / 文本=z4 / 交互=z5+
- ✅ 新增组件命名唯一性要求：`component_data.name` 全游戏无重复，生成时保证
- ✅ 新增算式文本右对齐规则：`alignType: right`，右边缘对齐输入框左边缘
- ✅ 新增文本–填空–文本一致性规则：同行字号/行距一致，换行时按行拆分
- ✅ 新增序号处理规则：文本内不出现 `（1）（2）（3）`，条件拆为独立组件
- ✅ 新增每关独立排版要求：配图/文本宽度/行数按本关内容单独计算
- ✅ 修正 `validate_config.js` 字段路径备注，防止脚本静默失效（`component_data.name` / `states[0].transform` / `states[0].source.MSprite.value`）
- ✅ 校验清单新增图层检查和命名唯一性检查

### v1.2.0 (2026-04-23)
- ✅ 新增 `layout_constants.json`：布局规范 + 皮肤-关卡映射的机器可读单一来源
- ✅ 新增 `scripts/validate_config.js`：自动合规校验（皮肤 hash、选项坐标、键盘 y、disabled URL、填空框尺寸）
- ✅ 新增"修改已有配置"任务类型的标准流程（先列差异、再改、再验）
- ✅ 在集成流程和校验清单中加入校验步骤（生成前 + 导入后）
- ✅ 修复 standard_workflow.md 皮肤选择章节，明确三皮肤关卡强制映射

### v1.1.0 (2026-04-16)
- ✅ 集成标准化题型生成工具
- ✅ 新增选择题、填空题、拖拽题支持
- ✅ 新增三种皮肤系统
- ✅ 新增多关拆单关功能
- ✅ 更新完整工作流文档

---

**最后更新**: 2026-04-24  
**版本**: 1.3.0
