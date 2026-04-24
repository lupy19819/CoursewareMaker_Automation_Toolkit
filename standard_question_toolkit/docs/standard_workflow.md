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

如果输入是 PDF 或图片：

- 先逐题转写原题文本，再做结构化拆分。
- `stem`、`conditions`、`rows.label`、`answerPrefix`、`answerSuffix`、`options` 等用户可见文字必须忠实来自原题，不允许概括、简化、润色、改写或补充题意。
- 允许为了组件布局拆成多个文本组件、去掉独立题号、规范空格和标点的半角/全角形式，但不能改变原题语义、删减条件或替换表达。
- 如果原题文字识别不清，必须标记为待确认，不要凭理解重写。

## 2. 使用目的模式

生成配置前必须先确认 `purpose`，再选择交互和反馈策略。当前沉淀的范例配置默认都是 `diagnostic` 诊断模式；如果用户没有说明，但配置有倒计时和草稿功能，应先按诊断模式处理。

### 诊断模式 `diagnostic`

用于测评、诊断、闯关检测，强调快速作答和记录结果。常见特征：

- 保留倒计时。
- 保留草稿功能。
- 正确和错误反馈音效可以统一，不强制区分。
- 答错一次后允许切换到下一关。
- 选择题选项、拖拽题选项、填空题填空框可以没有正确/错误状态，或正确/错误状态资源相同。
- 适配小中诊断三套布局：`diagnostic_visual_choice`、`diagnostic_compute_fill`、`diagnostic_image_reasoning`。

### 非诊断模式 `practice`

用于练习、教学互动、巩固训练，强调答对再过关和明确反馈。生成时必须：

- 去掉倒计时。
- 去掉草稿功能。
- 区分正确和错误反馈音效。
- 关闭“错误后跳关”，必须答对后才能切换关卡。
- 选择题选项、拖拽题选项、填空题填空框必须有可区分的正确/错误状态资源。
- 整关全部正确后必须播放撒花动效。使用 `passSuccess` / `闯关成功` 状态承接全局判定成功：撒花组件默认隐藏，`passSuccess` 状态显示并播放 Spine 动画和成功音效。
- 撒花资源和每个状态下播放的动作见 `data/component_skin_inventory.json` 的 `global_assets.success_fireworks`，或 `data/success_effect_assets.tsv`。
- 如果模板只提供诊断状态，不能直接复用为最终状态；需要补齐或替换正确/错误状态资源。

## 3. 题型归类

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

## 4. 布局规则

布局规范值的机器可读摘要在 `data/layout_constants.json`，生成或修改配置前先读取：

```json
// 关键常量（来自 layout_constants.json）
// 3 选项：x=[-548,-38,472], y=-464, w=474, h=132
// 4 选项：x=[-526,-176,174,524], y=-464, w=264, h=132
// 键盘 y：-464
// 提交按钮：x=818, y=-464, w=140, h=140
// 填空框：218×131, scaleX=1, scaleY=1
```

- 先阅读并遵循 `docs/layout_generation_method.md`。
- 匹配到原配置或模板后，只复用组件骨架、状态结构、答案判定和必需字段；题干、配图、输入框、选项、拖拽物、放置区、键盘等坐标必须按当前题内容重新计算。
- 不要按题型直接排版，先建立整关内容模型：题干、条件、作答句、算式、配图/表格、输入框、选项、键盘、提交。
- 使用三段式区域：认知区放题干/条件，关系区放图表/算式/答案句，操作区放选项/键盘/确认。
- 小中诊断资源新增三套标准布局：`diagnostic_visual_choice`、`diagnostic_compute_fill`、`diagnostic_image_reasoning`；先按整关内容密度选版，再落坐标。
- 视觉选择/规律判断：题干在上，主图/规律关系在中，3/4 个选项固定底部操作区，适合紫色选择题。
- 短题干计算填空：短标题可用大字号，算式组/竖式作为关系对象居中，数字键盘固定底部，适合黄色计算题。
- 长文本图文推理：长条件最多两行并左对齐，主配图/表格优先占关系区，答案区贴近图示关系，适合蓝色应用题和含主图的黄色题。
- 无配图题：不是简单“题干居中”，而是先判断是否有算式组、挖空句、选项或键盘，再做整体布局。
- 有配图题：题干/条件放上方，配图/表格放关系区，答案框靠近图示关系但不遮挡配图。
- 题干不要写题号。
- 选项本身已有文字时，不额外加 `A/B/C/D`。
- 文本字号和对齐按角色统一：短题干 60 居中，长题干 50 左对齐，条件句 50，答案句 54，选项 38。
- 题干文本按 `layout_constants.json > question_text_labels` 执行：未超过单行最大字数时只生成 1 个居中 label；超过后拆成 2 个独立 label，两个 label 同宽、整组居中、内部左对齐。
- 不允许把题干换行写进同一个 `MLabel.value`；每一行题干必须是单独组件，组件名用 `-行1`、`-行2` 区分。
- 算式题文本框宽度按算式长度计算，文本框和输入框作为一个整体居中。
- 单文本填空题：不要用空格占位；拆成 `answer_prefix + QuestionForBlank + answer_suffix`，后文文本起点接在输入框右侧。
- 长文本填空题：拆成条件句和作答组合；如果放不下，整体换行，不让单个文本组件自动换行包住输入框。
- 竖式填空题：按列网格布局，右对齐；已知数和符号都用文本组件，未知数用输入框。
- 拖拽题如果放置区嵌在句子中，也拆成 `answer_prefix + LDragPlace + answer_suffix`，后文接在放置区右侧。
- 拖拽题必须作为独立生成路径处理：先排 `LDragPlace` 放置区，再排 `MDraggbale` 拖拽物；保留拖拽物和放置区的 answer/judge 信息；多拖拽物在操作区横排或两行排列，不能用选择题或填空题替代。
- 选择题同类按钮使用统一九宫格；如果用户调整了某个标准按钮的 `MSprite.nineGrid`，后续同资源按钮复制九宫格元数据。

### 4.1 图层顺序（zIndex）——生成时即写正确

每个组件的 `zIndex` 必须在生成阶段显式赋值，不能继承模板默认值：

| zIndex | 组件类型 |
|--------|---------|
| `0` | `【题型说明】` |
| `1` | `【勿动】背景图片` |
| `3` | `【可修改】配图`、图表等装饰层 |
| `4` | 所有 `【可修改】文本-*`（题干、条件、算式标签等） |
| `5+` | 输入框、键盘、选项按钮、拖拽物、放置区、提交按钮 |

> `【勿动】` 组件的 zIndex 不得修改。文本组件（含题干）的 zIndex 必须低于交互组件。

### 4.2 组件命名唯一性

- `component_data.name` 在同一游戏内所有关卡中不得重复。
- 命名格式：`【可修改】文本-题干-L1`、`【可修改】文本-条件-L2-行1` 等，以关卡号和行号区分。
- 生成阶段即保证唯一，不依赖后期检查。

### 4.3 算式文本对齐

- 算式类文本（含 `□`、`_`、`=` 的算式前缀行）必须设 `alignType: right`。
- 文本框右边缘对齐输入框左边缘，gap ≤ 8px。
- 文本框宽度按算式字符数估算（中文字符 ~54px，英文/数字 ~30px），不能过窄导致换行，也不能过宽偏移对齐。

### 4.4 文本–填空框–文本 一致性

- 同一行的 `前文本 + 输入框 + 后文本` 结构中，所有文本组件字号和行间距必须一致。
- 如果某行文本内容较长、单一组件会换行导致字号不一致，则**按行手动拆分**为独立文本组件，每个组件只包含一行内容。
- 拆分后每行独立定位，不使用自动换行。

### 4.5 文本序号处理

- 题目文本内容中不得出现 `（1）（2）（3）` 等独立序号前缀。
- 如果原题通过序号区分多个条件，改为将每条独立拆分为单独的文本组件，组件名中用 `行1`、`行2` 区分。

### 4.6 每关独立排版

- 每关坐标必须按当前关内容独立计算，不得直接复制上一关坐标。
- 同类题的坐标基准（如键盘 y=-464、选项 y=-464）相同，但文本框宽度、行数、配图尺寸和位置必须按本关内容单独确定。
- 配图存在时，必须检查其与题干、填空框、键盘的 bounding box 是否重叠；重叠时先缩放配图，再调整答案区位置。

## 5. 皮肤选择

### 5.1 诊断三皮肤关卡强制映射（最高优先级）

**在生成或修改 15 关诊断游戏配置前，必须先确认每关的皮肤归属。** 皮肤不由题型决定，由关卡编号决定：

| 关卡范围 | 皮肤 | 背景图 hash 前缀 | 题型 |
|---------|------|----------------|------|
| Q1–Q5   | 紫色界面 | `fc9fbc3b` | 选择题 |
| Q6–Q10  | 黄色界面 | `e91dcb10` | Q6–Q9 填空/计算，Q10 拖拽 |
| Q11–Q15 | 蓝色界面 | `291cc642` | 填空/计算 |

> 此映射在 `data/layout_constants.json` 的 `skin_level_mapping` 字段中有机器可读版本，
> `validate_config.js` 自动比对此字段，不一致时报错。

换皮肤时必须同步更新该关卡的：
1. 背景图 URL
2. 输入框四态 URL（default / answering / correct / wrong）
3. 数字键盘 normal/pressed 六态 URL（disabled 三态跨皮肤共用，不替换）

### 5.2 其他皮肤识别

根据 `【勿动】背景图片` 的 URL 识别：

- `a0d71ef21cdf...`：沙滩皮肤
- `df49c4739e95...`：图纸皮肤
- `edb8ccb1e5ae...`：紫色星空皮肤

### 5.3 皮肤资源参考

机器可读（生成脚本和校验脚本读取）：

- `data/layout_constants.json` — 皮肤-关卡映射 + 布局常量 + disabled 共用 URL
- `data/component_skin_inventory.json` — 按皮肤分组的完整资源 URL

人类可读（手工查阅）：

- `data/component_skin_inventory.md`
- `data/skin_component_state_assets.tsv`
- `data/skin_text_color_usage.tsv`

三套皮肤都必须按组件状态取资源：背景图、选择题按钮/正确错误反馈标记、填空框 `default/answering/correct/wrong`、数字键盘各态、拖拽物 `default/dragging/placed`、放置框 `default/adsorb/adsorbed/placed`。不要只按当前题实际用到的组件保存局部资源。

## 6. 分值规则

多关整套配置：

- 尽量平均。
- 必须是整数。
- 总和必须等于 100。

单关拆分配置：

- 每个单关游戏 `score = [100]`。

## 7. 校验清单

**生成或修改配置后，先运行自动校验脚本：**

```bash
# 自动校验：皮肤 hash、选项坐标、键盘 y、disabled URL、填空框尺寸、z层级
node scripts/validate_config.js <game_id>
# 或本地文件
node scripts/validate_config.js --file config.json
```

自动校验现在以 `data/courseware_workflow_rules.json` 作为工作流基准文件：

- `validation_baselines` 保存每种标准玩法题型、每套皮肤的正确 `expected_config`。
- 选择题、填空/计算题、拖拽题分别与紫色、黄色、蓝色皮肤形成独立 baseline。
- 运动 PK 不按模板 ID 路由，而按 `custom_game` 数据结构和 run / swim / racecar 具体 baseline JSON 校验。
- 生成后的关卡会先识别组件类型，再按 `题型 + 皮肤` 找 baseline 校验背景图、组件互斥关系、交互组件资源、题干 label 规则和固定布局。
- 修改皮肤资源、题型组件或 workflow 顺序时，先改 `courseware_workflow_rules.json`，再改生成脚本；不要把校验规则散落在多个脚本里。

> **脚本字段路径备忘**（写脚本时必须使用正确路径，否则修改静默失效）：
> - 组件真实名称：`component_data.name`（顶层 `component_name` 对大多数组件显示 `"节点"`，不可用）
> - 组件 layout（位置/尺寸）：`component_data.states[0].transform`
> - 组件图片/资源 URL：`component_data.states[0].source.MSprite.value`
> - 组件 zIndex：`component_data.zIndex`

自动校验通过（0 错误）后，再手动检查：

- JSON 能否解析。
- `len(game)` 是否等于目标关卡数。
- `score_config.score` 合计是否等于 100。
- PDF/图片输入是否已经按原题逐字转写，题干、条件、选项、算式标签和作答句没有被简化或改写。
- 是否已声明并应用 `purpose`：诊断模式或非诊断模式。
- 诊断模式是否保留倒计时和草稿，允许统一反馈音效，允许答错后切关。
- 非诊断模式是否去掉倒计时和草稿，区分正确/错误音效，关闭错误后跳关，并要求答对后切关。
- 非诊断模式下选项、拖拽物、放置区、填空框是否有可区分的正确/错误状态资源。
- 非诊断模式是否配置撒花动效：`MSpine` 礼花默认隐藏，`passSuccess` 状态显示，播放动画和成功音效。
- 填空框尺寸是否保持不变形。
- 同题输入框 `numberUnit` 是否一致。
- 选择题是否只有一个正确项。
- 拖拽题是否保留拖拽项和放置区的 answer/judge 信息。
- 拖拽题是否有正确数量的 `MDraggbale` 和 `LDragPlace`，且每个拖拽物与放置区 answerKey/accept 绑定正确。
- 拖拽题皮肤状态是否正确：拖拽物默认/拖拽中/已放置，放置区默认/可吸附/已放置。
- 引用资源 URL 是否为空。
- 是否按 `docs/layout_generation_method.md` 做了整关内容模型检查。
- 是否对小中诊断题选择了合适的新三套布局，而不是只按选择/填空/拖拽题型排版。
- 长文本换行是否左对齐，短文本是否仍居中。
- 行内填空/拖拽是否使用前文 + 框/放置区 + 后文三段结构，且后文跟随框右边缘。
- 配图/表格题是否按题干 + 图示 + 答案区整体布局。
