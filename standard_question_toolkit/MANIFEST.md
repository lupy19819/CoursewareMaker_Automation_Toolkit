# 文件清单

## 文档

- `README_FOR_CLAUDE.md`：Claude 入口说明。
- `docs/standard_workflow.md`：标准化题型分析与生成流程。
- `docs/layout_generation_method.md`：标准题整关布局生成方法。
- `docs/question_input_template.md`：建议的结构化题目输入格式。
- `docs/claude_prompt.md`：可直接给 Claude 的系统/任务提示词。
- `notes/component_game_generation_notes.md`：历史沉淀的生成规则。

## 数据

- `data/component_skin_inventory.json`：皮肤资源机器可读清单。
- `data/component_skin_inventory.md`：皮肤资源人工阅读版。
- `data/skin_resource_table.tsv`：皮肤资源表，可粘贴进表格。
- `data/success_effect_assets.tsv`：非诊断模式闯关成功动效资源表。
- `data/skin_text_color_usage.tsv`：文字色号用途表，可粘贴进表格。

## 脚本

- `scripts/extract_component_skins.py`：从范例配置提取皮肤资源。
- `scripts/generate_grade3_config.py`：三年级诊断题生成示例，包含普通填空、算式填空、内嵌填空和两列布局示例。
- `scripts/generate_grade4_config.py`：四年级诊断题生成示例，包含配图题、选择题音效、皮肤/模板复用示例。
- `scripts/split_xiner_games.py`：新二多关拆单关示例。
- `scripts/split_xinyi_games.py`：新一多关拆单关示例。

## 布局生成入口

- 模型/人工生成配置时，入口是 `README_FOR_CLAUDE.md`、`docs/standard_workflow.md`、`docs/layout_generation_method.md` 和 `docs/question_input_template.md`。
- 生成前必须先确认使用目的 `purpose`：`diagnostic` 诊断模式或 `practice` 非诊断练习模式；它决定倒计时、草稿、反馈音效、错误后切关和正确/错误状态资源策略。
- 非诊断练习模式必须配置撒花闯关成功反馈：`MSpine` 礼花默认隐藏，`passSuccess` / `闯关成功` 状态监听全局判定成功后显示并播放动画。
- PDF/图片输入必须先做原题转写；生成配置时只能拆分和布局原题文本，不能概括、简化、润色或改写老师给的题目。
- 脚本示例只能复用组件骨架、状态结构、答案判定和必要字段；不能把历史题目的坐标当作新题的最终坐标。
- 新增选择、填空、配图、竖式、内嵌填空、内嵌拖拽、普通拖拽题时，都先建立整关内容模型，再按认知区、关系区、操作区重新排版。
- 拖拽题必须有独立生成路径：`MDraggbale` 拖拽物 + `LDragPlace` 放置区，并校验 `answerKey/accept` 绑定与各状态皮肤。

## 模板

- `templates/base_choice_fill_template.json`：选择题/填空题基础模板。
- `templates/vertical_multiplication_template.json`：竖式填空模板。
