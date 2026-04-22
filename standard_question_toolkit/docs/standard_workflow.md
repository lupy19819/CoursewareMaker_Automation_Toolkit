# 标准化题型分析与生成流程

## 1. 读取输入

常见输入有三类：

- 原始 CoursewareMaker 配置 JSON。
- PDF 或图片题目，需要先人工/视觉识别题干、选项、答案、配图。
- 用户直接给出的题目清单。

如果输入是 JSON：

- 根结构通常包含 `common`、`game`、`additional`、`components`。
- 关卡数组在 `game`。
- 全局倒计时在 `common.global_config.time_countdown`。
- 分值在 `common.global_config.score_config`。

## 2. 题型归类

### 选择题

- 组件：`AloneClickChoice`
- `component_id`：`3b9b8ec3-f7d3-11ee-b9ef-8e2f78cd4bcd`
- 手动判定：
  - `levelData.judge.autoJudge = 0`
  - `levelData.judge.judgeRule = 0`
- 正确项：
  - `component_data.components.tools.AloneClickChoice.anwserConfig.anwserRadio = 1`
- 错误项：
  - `anwserRadio = 2`
- 选中态音效：
  - 复制填空框输入中状态 `QuestionForBlank` 第 2 个 state 的 `source.MAudio` 到选择项第 2 个 state。

### 填空题

- 组件：`QuestionForBlank`
- `component_id`：`0b26ef14-f7e0-11ee-b9ef-8e2f78cd4bcd`
- 答案字段：
  - `component_data.components.tools.QuestionForBlank.anwserConfig.anwser`
- 数字输入上限：
  - `fillInteractive.numberUnit`
- 同一题内所有输入框 `numberUnit` 统一为本题最大答案长度。
- 同一题内所有输入框字号统一。
- 普通输入框尺寸保持 `218 x 131`。

### 拖拽题

- 拖拽项：`MDraggbale`
- `component_id`：`d8b73bec-f719-11ee-b9ef-8e2f78cd4bcd`
- 放置区：`LDragPlace`
- `component_id`：`f9b49402-f73d-11ee-b9ef-8e2f78cd4bcd`
- 放置区响应态常见 state：
  - `adsorb`
  - `adsorbed`
  - `placed`
- 拖拽项常见 state：
  - `default`
  - `dragging`
  - `placed`

## 3. 布局规则

- 先阅读并遵循 `docs/layout_generation_method.md`。
- 不要按题型直接排版，先建立整关内容模型：题干、条件、作答句、算式、配图/表格、输入框、选项、键盘、提交。
- 使用三段式区域：认知区放题干/条件，关系区放图表/算式/答案句，操作区放选项/键盘/确认。
- 无配图题：不是简单“题干居中”，而是先判断是否有算式组、挖空句、选项或键盘，再做整体布局。
- 有配图题：题干/条件放上方，配图/表格放关系区，答案框靠近图示关系但不遮挡配图。
- 题干不要写题号。
- 选项本身已有文字时，不额外加 `A/B/C/D`。
- 文本字号和对齐按角色统一：短题干 60 居中，长题干 50 左对齐，条件句 50，答案句 54，选项 38。
- 算式题文本框宽度按算式长度计算，文本框和输入框作为一个整体居中。
- 单文本填空题：不要用空格占位；拆成 `answer_prefix + QuestionForBlank + answer_suffix`，后文文本起点接在输入框右侧。
- 长文本填空题：拆成条件句和作答组合；如果放不下，整体换行，不让单个文本组件自动换行包住输入框。
- 竖式填空题：按列网格布局，右对齐；已知数和符号都用文本组件，未知数用输入框。
- 拖拽题如果放置区嵌在句子中，也拆成 `answer_prefix + LDragPlace + answer_suffix`，后文接在放置区右侧。
- 选择题同类按钮使用统一九宫格；如果用户调整了某个标准按钮的 `MSprite.nineGrid`，后续同资源按钮复制九宫格元数据。

## 4. 皮肤选择

根据 `【勿动】背景图片` 的 URL 识别：

- `a0d71ef21cdf...`：沙滩皮肤
- `df49c4739e95...`：图纸皮肤
- `edb8ccb1e5ae...`：紫色星空皮肤

具体资源见：

- `data/component_skin_inventory.json`
- `data/skin_resource_table.tsv`
- `data/skin_text_color_usage.tsv`

## 5. 分值规则

多关整套配置：

- 尽量平均。
- 必须是整数。
- 总和必须等于 100。

单关拆分配置：

- 每个单关游戏 `score = [100]`。

## 6. 校验清单

生成后至少运行这些检查：

- JSON 能否解析。
- `len(game)` 是否等于目标关卡数。
- `score_config.score` 合计是否等于 100。
- 填空框尺寸是否保持不变形。
- 同题输入框 `numberUnit` 是否一致。
- 选择题是否只有一个正确项。
- 拖拽题是否保留拖拽项和放置区的 answer/judge 信息。
- 引用资源 URL 是否为空。
- 是否按 `docs/layout_generation_method.md` 做了整关内容模型检查。
- 长文本换行是否左对齐，短文本是否仍居中。
- 行内填空/拖拽是否使用前文 + 框/放置区 + 后文三段结构，且后文跟随框右边缘。
- 配图/表格题是否按题干 + 图示 + 答案区整体布局。
