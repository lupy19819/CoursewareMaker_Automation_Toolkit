# Claude Component Game Standard Toolkit

这个包用于分析和生成 CoursewareMaker 组件化数学题游戏配置，覆盖当前已经沉淀的标准题型：

- 选择题：`AloneClickChoice`
- 填空题：`QuestionForBlank`
- 拖拽题：`MDraggbale` + `LDragPlace`
- 竖式/算式填空题：文本、横线、符号、填空框按网格自动组装
- 单关拆分：把一个多关游戏拆成多个完整单关游戏
- 皮肤复用：按背景图识别沙滩皮肤、图纸皮肤、紫色星空皮肤

## 推荐读取顺序

1. `docs/standard_workflow.md`
2. `docs/layout_generation_method.md`
3. `docs/question_input_template.md`
4. `notes/component_game_generation_notes.md`
5. **`data/layout_constants.json`** ← 布局规范 + 皮肤-关卡映射的机器可读摘要，生成前必读
6. `data/component_skin_inventory.json` ← 完整皮肤资源 URL
7. `data/component_skin_inventory.md`
8. `data/skin_component_state_assets.tsv`
9. `data/success_effect_assets.tsv`
10. `data/skin_text_color_usage.tsv`

## 任务类型

### 生成新配置

按推荐读取顺序阅读文档，从模板生成配置，生成后运行 `validate_config.js`。

### 修改已有配置使其合规（必须遵循此流程）

```
1. 读取 data/layout_constants.json + data/component_skin_inventory.json
2. 获取游戏现有 JSON（CDP 或 API）
3. 运行 validate_config.js <game_id> → 生成差异清单
4. 按差异清单逐项修改（不允许跳过差异清单直接动手）
5. 再次运行 validate_config.js，确认 0 错误
6. 调用 save_game_config_via_cdp.js 导入保存
```

**关键约束**：皮肤归属由关卡编号决定，与题型无关：

| 关卡 | 皮肤 | background hash |
|------|------|----------------|
| Q1–Q5 | 紫色 | `fc9fbc3b` |
| Q6–Q10 | 黄色 | `e91dcb10` |
| Q11–Q15 | 蓝色 | `291cc642` |

`disabled` 键盘三态跨皮肤共用（2026-04-13 资源），换皮肤时**不替换**。

---

## 组件字段说明（必读，脚本读错会导致修改静默失效）

组件的显示名称**不在顶层 `component_name`**，该字段对大多数组件显示的是 `"节点"`，无法用于识别。**真实名称在 `component_data.name`**。所有脚本（生成/校验/修复）查找、匹配组件时必须读 `component_data.name`。

---

## 图层顺序规则（必须遵守）

每关所有组件的 `zIndex` 必须严格按以下层级设置，**生成时即正确，不依赖后期修复**：

| 图层 | zIndex | 组件类型 |
|------|--------|---------|
| 最底层 | `0` | `【题型说明】` |
| 背景层 | `1` | `【勿动】背景图片` |
| 配图层 | `3` | `【可修改】配图`、`【可修改】图表` |
| 文本层 | `4` | `【可修改】文本-题干`、`【可修改】文本-条件`、所有其他文本 |
| 交互层 | `5+` | 输入框、键盘、选项按钮、拖拽物、放置区、提交按钮 |

> `【勿动】` 组件（背景图、撒花动效、键盘）的 zIndex 不得修改。

**生成文本组件时必须显式写入 `zIndex: 4`，不能依赖模板默认值继承。**

---

## 组件命名规则

- 同一游戏内所有关卡的所有组件，`component_data.name` 不得重复。
- 命名格式建议：`【可修改】文本-题干-L{关卡号}`，如 `【可修改】文本-题干-L1`。
- 生成脚本必须在生成阶段保证唯一性，不能依赖后期检查发现重复。

---

## 核心文件

- `data/layout_constants.json`
  - **布局规范 + 皮肤-关卡映射的机器可读摘要**，生成/修改前必须读取。
  - `validate_config.js` 和生成脚本从这里读取常量，只需在此维护一份。
- `templates/base_choice_fill_template.json`
  - 选择题、普通填空题的基础组件模板。
- `templates/vertical_multiplication_template.json`
  - 竖式填空题模板。
- `docs/layout_generation_method.md`
  - 标准题整关布局生成方法；生成坐标前必须先建立内容模型。
- `data/component_skin_inventory.json`
  - 机器可读皮肤清单，按背景图分组。
- `data/skin_component_state_assets.tsv`
  - 三套皮肤按组件状态展开的完整资源表，覆盖背景、选择题按钮/反馈标记、填空框、数字键盘、拖拽物、放置框。
- `data/success_effect_assets.tsv`
  - 非诊断模式闯关成功撒花动效资源，包含 `default` 和 `passSuccess` 状态动作、Spine 包、成功音效。
- `scripts/extract_component_skins.py`
  - 从范例配置重新提取皮肤素材。
- `scripts/generate_grade3_config.py`
  - 已实现的整套题生成脚本，可参考普通填空、算式填空、内嵌填空、两列布局；这些坐标只适用于对应题集，新增题必须按布局方法重排。
- `scripts/generate_grade4_config.py`
  - 已实现的整套题生成脚本，可参考配图题、选择题音效、皮肤/模板复用；新增拖拽题需要补充 `MDraggbale + LDragPlace` 实例生成路径。
- `scripts/split_xiner_games.py`
  - 把 12 关游戏拆为 12 个单关游戏。
- `scripts/split_xinyi_games.py`
  - 把 12 关游戏拆为 12 个单关游戏，并从另一套配置复制草稿功能。

## 生成配置的最低要求

用户给题目后，Claude 应先整理成结构化题目清单，再复制模板中的完整根结构，只替换 `game` 关卡数组和必要的 `common.global_config.score_config`。

生成前必须确认使用目的 `purpose`：

- `diagnostic` 诊断模式：当前范例配置默认模式。保留倒计时和草稿；正确/错误反馈音效可统一；答错一次后允许切换下一关；选择题选项、拖拽题选项、填空题填空框可以没有正确/错误状态，或正确/错误状态资源相同。
- `practice` 非诊断练习模式：去掉倒计时和草稿；区分正确/错误反馈音效；关闭错误后跳关，必须答对后才能切换关卡；选择题选项、拖拽题选项、填空题填空框必须有可区分的正确/错误状态资源；整关全部正确后播放撒花动效。

非诊断模式的撒花动效使用 `passSuccess` / `闯关成功` 状态：组件默认隐藏，`passSuccess` 显示并播放 Spine 动画和成功音效。`passSuccess` 是组件监听全局判定成功的状态钩子，不需要给提交按钮或选项额外写触发事件。

撒花动效资源以 `data/component_skin_inventory.json` 的 `global_assets.success_fireworks` 为准；人工查看可读 `data/component_skin_inventory.md` 或 `data/success_effect_assets.tsv`。

匹配到原配置或模板后，只复用可运行组件骨架、状态结构、答案判定和必需字段；当前题的坐标、字号、对齐、配图、输入框、拖拽物、放置区、选项和键盘位置必须按内容模型重新计算。

生成完必须校验：

- JSON 可解析。
- `game` 关卡数正确。
- `purpose` 已明确，诊断/非诊断的倒计时、草稿、反馈音效、错题切关和状态资源策略正确。
- 非诊断模式已配置撒花动效，且 `passSuccess` 状态会在整关正确后显示并播放。
- 如果输入来自 PDF/图片，所有用户可见题目文字必须忠实转写原题，不得概括、简化、润色或改写；布局只能拆分组件，不能改写内容。
- 每关题型说明组件与实际题型一致。
- 选择题正确项为 `anwserRadio = 1`，错误项为 `2`。
- 选择题为手动判定：`levelData.judge.autoJudge = 0`，`judgeRule = 0`。
- 填空题每关内所有输入框 `numberUnit` 一致，取本题最大答案长度。
- 填空框尺寸不变形：普通输入框 `218 x 131`，`scaleX = 1`，`scaleY = 1`。
- 拖拽题使用 `MDraggbale` + `LDragPlace`，不能用选择题或填空题假替代。
- 拖拽题先排放置区，再排拖拽物；保留拖拽物和放置区的 answer/judge 信息。
- 拖拽题必须校验 `dragItems.answerKey` 和 `dropZones.accept` 的绑定关系。
- 行内拖拽使用 `answer_prefix + LDragPlace + answer_suffix`，不使用空格占位。
- 竖式题右对齐，已知数字、符号、横线均为文本组件，空位才使用输入框。
- 布局必须先建立整关内容模型，不能只按题型或只调题干。
- 文本按角色处理：题干先查 `layout_constants.json > question_text_labels`；未超过单行最大字数时只生成 1 个居中 label，超过时拆成 2 个同宽独立 label，整组居中、内部左对齐。条件句/答案句/算式行/选项各用自己的字号和对齐规则。
- 题干换行必须靠多个 `MLabel` 组件完成，不允许在同一个 `MLabel.value` 中写 `\n`。
- 小中诊断题优先从三套新增布局选版：视觉选择/规律判断用 `diagnostic_visual_choice`，短题干计算填空用 `diagnostic_compute_fill`，长文本或主配图推理用 `diagnostic_image_reasoning`。
- 行内填空/拖拽不要用空格占位；拆成前文文本 + 输入框/放置区 + 后文文本，后文起点接在框右边缘。
- 有配图/表格题必须整体考虑题干、图示、答案区和操作区。
- 不在题干文本里写独立题号；但题干、条件、选项、算式标签和作答句必须保留原题表达。
- 分值使用整数且合计 100。
- 所有文本组件 `zIndex = 4`；交互组件 `zIndex >= 5`；背景图 `zIndex = 1`；题型说明 `zIndex = 0`。
- 同一游戏内所有关卡的所有组件 `component_data.name` 不得重复，生成时即保证唯一。
- 算式类文本（如 `4+□=`、`_÷3=`）必须设 `alignType: right`，文本框右边缘精确对齐输入框左边缘（gap ≤ 8px），避免重叠。
- `文本–填空框–文本` 同行结构中，字号和行间距必须一致；若文本内容换行会破坏一致性，则按行手动拆分为独立文本组件，每组件只放一行内容。
- 文本内容不得出现 `（1）（2）（3）` 等独立序号前缀；原题序号用于区分条件时，改为拆成独立文本组件，而非在同一文本组件内用序号区分。
- 每关内容必须独立按题目重新排版，不能只做模板坐标套用；同类题的坐标基准相同，但文本宽度、行数、配图位置必须按当前关内容单独计算。

## 皮肤名称

- 皮肤 1：沙滩皮肤
- 皮肤 2：图纸皮肤
- 皮肤 3：紫色星空皮肤
- 小中诊断皮肤：诊断紫色皮肤、诊断黄色皮肤、诊断蓝色皮肤

皮肤应优先通过背景图 URL 匹配。匹配后再取同组里的输入框、放置区、拖拽选项、题干背景和文字色号。
