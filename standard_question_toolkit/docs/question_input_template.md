# 题目输入模板

建议 Claude 先把用户给的题目整理成下面的结构，再开始生成配置。

```json
{
  "purpose": "diagnostic",
  "skin": "图纸皮肤",
  "levels": [
    {
      "type": "choice",
      "stem": "长方形长16厘米，宽4厘米，面积是（  ）平方厘米。",
      "options": ["64", "40", "20", "60"],
      "answerIndex": 0,
      "image": null,
      "layout": "diagnostic_visual_choice"
    },
    {
      "type": "fill",
      "stem": "简便计算",
      "rows": [
        {"label": "4.47 + 2.38 + 4.53 + 4.62 =", "answer": "16"},
        {"label": "4.1 + 1.3 + 1.7 - 1.1 =", "answer": "6"}
      ],
      "image": null,
      "layout": "diagnostic_compute_fill"
    },
    {
      "type": "inline_fill",
      "stem": "搭配方案问题",
      "conditions": ["上衣3种，裙子2种，鞋子2种。"],
      "answerPrefix": "田田共有",
      "answerSuffix": "种搭配方案。",
      "answer": "12",
      "image": null,
      "layout": "inline_fill"
    },
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
    },
    {
      "type": "drag",
      "stem": "把合适的数拖到对应位置。",
      "conditions": ["观察下面的数量关系。"],
      "image": null,
      "dragItems": [
        {"text": "12", "answerKey": "a"},
        {"text": "16", "answerKey": "b"}
      ],
      "dropZones": [
        {"label": "第一个空", "accept": "a"},
        {"label": "第二个空", "accept": "b"}
      ],
      "layout": "drag"
    },
    {
      "type": "inline_drag",
      "stem": "把正确结果拖入句子。",
      "conditions": ["先根据图示完成推理。"],
      "answerPrefix": "所以答案是",
      "answerSuffix": "个。",
      "dragItems": [
        {"text": "24", "answerKey": "a"},
        {"text": "36", "answerKey": "b"}
      ],
      "dropZones": [
        {"accept": "a"}
      ],
      "layout": "drag"
    }
  ]
}
```

## 字段说明

- `purpose`：必填或生成前必须确认。可填 `diagnostic` 或 `practice`。
  - `diagnostic`：诊断模式，保留倒计时和草稿，正确/错误反馈音效可统一，答错后允许切换关卡，选项/拖拽物/填空框的正确错误状态可相同。
  - `practice`：非诊断练习模式，去掉倒计时和草稿，区分正确/错误反馈音效，关闭错误后跳关，必须答对后才能切换关卡，选项/拖拽物/填空框必须有可区分的正确错误状态。
- `skin`：可选 `沙滩皮肤`、`图纸皮肤`、`紫色星空皮肤`。
  - 小中诊断资源可选 `诊断紫色皮肤`、`诊断黄色皮肤`、`诊断蓝色皮肤`。
- `type`：
  - `choice`
  - `fill`
  - `inline_fill`
  - `vertical_fill`
  - `drag`
  - `inline_drag`
- `stem`：用户可见题干，不写题号。
- `options`：选择题选项，不自动加 A/B/C/D，除非选项本身就是 A/B/C/D。
- `rows`：多行填空、算式填空使用。
- `image`：可填资源 URL、资源 id 或本地图片路径。生成最终配置时必须转成可访问 URL。
- `conditions`：可选。应用题中的背景条件；生成时按 `condition` 文本角色布局。
- `answerPrefix`：可选。行内填空框或拖拽放置区前的文本。
- `answerSuffix`：可选。行内填空框或拖拽放置区后的文本；生成时从输入框/放置区右边缘起排，不依赖空格占位。
- `dragItems`：拖拽题必填。每个拖拽物至少包含 `text` 或 `image`，以及唯一 `answerKey`。
- `dropZones`：拖拽题必填。每个放置区至少包含 `accept`；可选 `label`、`answerPrefix`、`answerSuffix`、`imageAnchor`。
- `layout`：可选。可填 `choice_only`、`formula_fill`、`inline_fill`、`image_fill`、`vertical_fill`、`drag`、`diagnostic_visual_choice`、`diagnostic_compute_fill`、`diagnostic_image_reasoning`；不填时由内容块自动推断。
- `imageRole`：可选。可填 `supporting` 或 `primary_reasoning`；配图是主要推理对象时应给关系区更多空间。

## 拖拽题输入要求

- 普通拖拽：`dragItems.length` 通常等于或大于 `dropZones.length`，每个 `dropZones.accept` 必须能在 `dragItems.answerKey` 中找到。
- 行内拖拽：使用 `answerPrefix + LDragPlace + answerSuffix`，不要在文本中留空格占位。
- 图文拖拽：如果放置区依附配图，给 `imageRole = "primary_reasoning"`，并在 `dropZones` 中描述靠近哪个图示关系。
- 生成配置时必须保留 `MDraggbale` 和 `LDragPlace` 的 answer/judge 信息，不能只生成静态图片。

## 小中诊断布局选择

- `diagnostic_visual_choice`：有 3/4 个选项、不需要数字键盘，题目依赖图形、排列、规律或视觉比较。
- `diagnostic_compute_fill`：无主配图，核心是横式、竖式、多行算式、简便计算，答案通过数字键盘输入。
- `diagnostic_image_reasoning`：有主配图/表格/统计图/几何图/路线图，或长应用题条件需要和图示一起推理。
