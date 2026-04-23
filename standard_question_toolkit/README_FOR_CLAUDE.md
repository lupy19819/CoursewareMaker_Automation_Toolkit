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
5. `data/component_skin_inventory.md`
6. `data/skin_resource_table.tsv`
7. `data/skin_text_color_usage.tsv`

## 核心文件

- `templates/base_choice_fill_template.json`
  - 选择题、普通填空题的基础组件模板。
- `templates/vertical_multiplication_template.json`
  - 竖式填空题模板。
- `docs/layout_generation_method.md`
  - 标准题整关布局生成方法；生成坐标前必须先建立内容模型。
- `data/component_skin_inventory.json`
  - 机器可读皮肤清单，按背景图分组。
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
- `practice` 非诊断练习模式：去掉倒计时和草稿；区分正确/错误反馈音效；关闭错误后跳关，必须答对后才能切换关卡；选择题选项、拖拽题选项、填空题填空框必须有可区分的正确/错误状态资源。

匹配到原配置或模板后，只复用可运行组件骨架、状态结构、答案判定和必需字段；当前题的坐标、字号、对齐、配图、输入框、拖拽物、放置区、选项和键盘位置必须按内容模型重新计算。

生成完必须校验：

- JSON 可解析。
- `game` 关卡数正确。
- `purpose` 已明确，诊断/非诊断的倒计时、草稿、反馈音效、错题切关和状态资源策略正确。
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
- 文本按角色处理：短题干居中，长题干左对齐，条件句/答案句/算式行/选项各用自己的字号和对齐规则。
- 小中诊断题优先从三套新增布局选版：视觉选择/规律判断用 `diagnostic_visual_choice`，短题干计算填空用 `diagnostic_compute_fill`，长文本或主配图推理用 `diagnostic_image_reasoning`。
- 行内填空/拖拽不要用空格占位；拆成前文文本 + 输入框/放置区 + 后文文本，后文起点接在框右边缘。
- 有配图/表格题必须整体考虑题干、图示、答案区和操作区。
- 不在题干文本里写题号。
- 分值使用整数且合计 100。

## 皮肤名称

- 皮肤 1：沙滩皮肤
- 皮肤 2：图纸皮肤
- 皮肤 3：紫色星空皮肤
- 小中诊断皮肤：诊断紫色皮肤、诊断黄色皮肤、诊断蓝色皮肤

皮肤应优先通过背景图 URL 匹配。匹配后再取同组里的输入框、放置区、拖拽选项、题干背景和文字色号。
