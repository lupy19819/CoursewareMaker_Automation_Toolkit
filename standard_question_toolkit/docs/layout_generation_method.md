# 标准题配置布局生成方法

用于生成或修改 CoursewareMaker 标准题型游戏 JSON。画布固定为 `2048 x 1152`，坐标系以画布中心为 `(0, 0)`。

核心原则：不要按题型直接排版，要先建立一关的整体内容模型。

## 1. 整关内容模型

生成坐标前，先把每一关里的可见组件归类：

| 内容块 | 含义 | 常见组件 |
| --- | --- | --- |
| `stem` | 主要题干/任务说明 | `【可修改】文本-题干` |
| `condition` | 背景条件、已知信息 | 应用题条件句 |
| `answer_prefix` | 填空框/放置区前的文本 | 独立文本组件 |
| `answer_target` | 行内填空框或拖拽放置区 | `QuestionForBlank` 或 `LDragPlace` |
| `answer_suffix` | 填空框/放置区后的文本 | 独立文本组件 |
| `formula_row` | 算式行 | 文本 + `QuestionForBlank` |
| `vertical_grid` | 竖式结构 | 数字文本、符号、横线、输入框 |
| `image_or_table` | 配图、表格、图示 | 非背景 `BaseComponent/MSprite` |
| `choice_option` | 选项按钮 | `AloneClickChoice` |
| `blank` | 填空输入框 | `QuestionForBlank` |
| `keyboard` | 数字键盘 | `SimpleNumericKeyboard` |
| `submit` | 确认/提交 | 提交按钮或键盘确认 |
| `utility` | 重置、音频、关卡号、倒计时 | 非作答路径组件 |

按内容块选择布局原型：

- `choice_only`：题干 + 选项 + 提交。
- `formula_fill`：题干 + 算式行 + 输入框 + 键盘。
- `inline_fill`：条件句 + 前文文本 + 行内输入框 + 后文文本 + 键盘。
- `image_fill`：题干/条件 + 配图/表格 + 答案区 + 键盘。
- `vertical_fill`：题干 + 竖式网格 + 键盘。
- `drag`：题干/条件 + 放置区 + 拖拽物 + 提交。

## 2. 三段式区域模型

```text
认知区：y 约 210..360
关系区：y 约 40..-300
操作区：y 约 -390..-535
```

- 认知区：题干、标题、条件摘要。
- 关系区：配图、表格、算式组、竖式、答案句。
- 操作区：选项、数字键盘、删除、确认。

先分配整关内容块，再处理字号、对齐和坐标。不要只放大题干，导致配图、算式或输入框被挤压。

## 3. 文本角色规范

| 角色 | 默认字号 | 对齐规则 |
| --- | ---: | --- |
| `stem` 短题干 | `60` | 居中 |
| `stem` 长题干 | `50` | 左对齐 |
| `condition` | `50` | 单行居中，换行左对齐 |
| `answer_prefix` / `answer_suffix` | `54` | 单行左到右拼接，必要时整组换行 |
| `formula_row` | `50` | 算式文本右对齐 |
| `choice_option` | `38` | 居中 |

判断规则：

- 先估算文本视觉宽度。
- 如果在文本框内会换行，改为左对齐并增加文本框高度。
- 短文本不要因为同关其他文本很长而被左对齐。

## 4. 行内填空/拖拽锚定规则

不要再使用“文本中留全角空格 + 输入框覆盖占位”的方式。不同设备分辨率、字体渲染和缩放会改变前文换行，导致文字和输入框/放置区错位。

新的稳定结构是：

```text
answer_prefix text  +  answer_target box  +  answer_suffix text
```

规则：

1. 把应用题拆成若干 `condition`，再把作答句拆成 `answer_prefix`、`answer_target`、`answer_suffix`。
2. `answer_prefix` 是输入框/放置区前的文本。
3. `answer_target` 是 `QuestionForBlank` 或 `LDragPlace`。
4. `answer_suffix` 是输入框/放置区后的文本。
5. `answer_suffix` 的起点必须由 `answer_target` 的右边缘计算，不依赖空格占位。
6. 普通输入框保持 `218 x 131`，`scaleX = 1`，`scaleY = 1`。
7. 放置区保持模板原始尺寸和状态，不拉伸，除非用户指定新尺寸。

单行拼接计算：

```text
prefix_width = visual_width(answer_prefix)
target_width = target.w
suffix_width = visual_width(answer_suffix)
gap = 16..28
group_width = prefix_width + gap + target_width + gap + suffix_width

prefix_x = group_center_x - group_width / 2 + prefix_width / 2
target_x = group_center_x - group_width / 2 + prefix_width + gap + target_width / 2
suffix_x = group_center_x - group_width / 2 + prefix_width + gap + target_width + gap + suffix_width / 2
```

换行规则：

- 如果 `group_width` 超过可用宽度，优先把 `condition` 再拆短。
- 如果必须换行，不让一个文本组件自动包住目标框；改成两行结构：
  - 第一行：`condition` 或较长的前文。
  - 第二行：较短的 `answer_prefix + answer_target + answer_suffix` 组合。
- `answer_suffix` 永远跟随 `answer_target` 的右边缘，不用空格占位。

拖拽题同理：如果放置区嵌在句中，使用 `answer_prefix + LDragPlace + answer_suffix` 的三段结构，后文接在放置区右侧。

## 5. 配图/表格整体布局

有配图、表格、图示时，不能只调整题干。

1. 题干/条件放认知区。
2. 配图/表格放关系区中心。
3. 答案标签/输入框靠近图示关系，但不遮挡图。
4. 键盘/选项固定在操作区。

判断布局时看题干 + 图示 + 答案区 + 操作区的整体组合。

## 6. 算式和多行填空

算式行属于关系区计算对象。

```text
group_width = formula_text_width + gap + blank_width
formula_x = -group_width / 2 + formula_text_width / 2
blank_x = -group_width / 2 + formula_text_width + gap + blank_width / 2
```

- 算式文本右对齐。
- 输入框和算式作为一组居中。
- 普通 `218 x 131` 输入框下，多行间距至少约 `155px`。

## 7. 选择题和九宫格

推荐选项位置：

```text
3 选项：x = -548, -38, 472; w = 474; y = -464; h = 132
4 选项：x = -526, -176, 174, 524; w = 264; y = -464; h = 132
```

如果用户把某个选择按钮的 `MSprite.nineGrid` 调成标准结构，以后同类资源的选择按钮都应复用该九宫格结构。只复制 `nineGrid` 元数据，不替换按钮图片 URL 和文字。

## 8. 提交、重置、键盘

- 数字键盘固定在操作区。
- 确认/提交固定在右下作答路径。
- 重置是工具功能，不是主作答路径；默认应隐藏或弱化，除非用户要求显示。

当前标准提交位：

```text
x = 818
y = -464
w = 140
h = 140
```

## 9. 校验清单

- JSON 可解析。
- 关卡数不变，除非明确要求增删。
- 答案和判定信息不变。
- 填空框答案、`numberUnit`、尺寸、`scaleX/scaleY` 不被破坏。
- 选择题正确项/错误项不变。
- 同类选择按钮九宫格一致。
- 不出现可见的重复题型说明。
- 长文本换行时左对齐，短文本保持居中。
- 行内填空/拖拽不使用空格占位。
- `answer_suffix` 是否由输入框/放置区右边缘计算。
- 如果作答句需要换行，是否拆成多行组件，而不是让单个文本组件自动换行包住目标框。
- 有配图/表格时按整关布局判断，而不是只看题干。
- 算式行和输入框作为整体居中。
