# 题目输入模板

建议 Claude 先把用户给的题目整理成下面的结构，再开始生成配置。

```json
{
  "skin": "图纸皮肤",
  "levels": [
    {
      "type": "choice",
      "stem": "长方形长16厘米，宽4厘米，面积是（  ）平方厘米。",
      "options": ["64", "40", "20", "60"],
      "answerIndex": 0,
      "image": null
    },
    {
      "type": "fill",
      "stem": "简便计算",
      "rows": [
        {"label": "4.47 + 2.38 + 4.53 + 4.62 =", "answer": "16"},
        {"label": "4.1 + 1.3 + 1.7 - 1.1 =", "answer": "6"}
      ],
      "image": null
    },
    {
      "type": "inline_fill",
      "stem": "搭配方案问题",
      "conditions": ["上衣3种，裙子2种，鞋子2种。"],
      "answerPrefix": "田田共有",
      "answerSuffix": "种搭配方案。",
      "answer": "12",
      "image": null
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
      "stem": "把正确答案拖到对应位置。",
      "conditions": ["观察下面的关系。"],
      "answerPrefix": "正确答案是",
      "answerSuffix": "。",
      "dragItems": [
        {"text": "A", "answerKey": "a"},
        {"text": "B", "answerKey": "b"}
      ],
      "dropZones": [
        {"text": "", "accept": "a"},
        {"text": "", "accept": "b"}
      ]
    }
  ]
}
```

## 字段说明

- `skin`：可选 `沙滩皮肤`、`图纸皮肤`、`紫色星空皮肤`。
- `type`：
  - `choice`
  - `fill`
  - `inline_fill`
  - `vertical_fill`
  - `drag`
- `stem`：用户可见题干，不写题号。
- `options`：选择题选项，不自动加 A/B/C/D，除非选项本身就是 A/B/C/D。
- `rows`：多行填空、算式填空使用。
- `image`：可填资源 URL、资源 id 或本地图片路径。生成最终配置时必须转成可访问 URL。
- `conditions`：可选。应用题中的背景条件；生成时按 `condition` 文本角色布局。
- `answerPrefix`：可选。行内填空框或拖拽放置区前的文本。
- `answerSuffix`：可选。行内填空框或拖拽放置区后的文本；生成时从输入框/放置区右边缘起排，不依赖空格占位。
- `layout`：可选。可填 `choice_only`、`formula_fill`、`inline_fill`、`image_fill`、`vertical_fill`、`drag`；不填时由内容块自动推断。
- `imageRole`：可选。可填 `supporting` 或 `primary_reasoning`；配图是主要推理对象时应给关系区更多空间。
