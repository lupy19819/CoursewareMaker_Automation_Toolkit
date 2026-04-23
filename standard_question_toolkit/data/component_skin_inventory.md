# 组件化游戏皮肤素材清单

分组规则：按每关 `【勿动】背景图片` 的 `MSprite.value` 区分皮肤。

> **皮肤 vs 题型 vs 题目 的区别**
> - **皮肤资产**：`【勿动】` 节点图片（背景图、数字键盘各态）+ 与该皮肤强绑定的输入框样式图。换皮肤时统一替换。
> - **题型资产**：同一题型内所有关卡共用的按钮外观图（如选择题按钮），换题型时替换，换皮肤时不动。
> - **题目配图**：各关独有、内容不同的配图/拖拽素材，每关单独填写，两者均不替换。

---

## 全局通用资产（所有关卡共用，皮肤/题型切换时均不替换）

- 重置按钮 default：https://courseware-maker-test-1252161091.cos.ap-beijing.myqcloud.com/assets/image/123498/2024-04-12/410533039841b863b95182dccd241322/reset_default.png
- 重置按钮 click：https://courseware-maker-test-1252161091.cos.ap-beijing.myqcloud.com/assets/image/123498/2024-04-12/dceecc120c84e78b491b77ffa8120cf4/reset_click.png
- 重置按钮 disable：https://courseware-maker-test-1252161091.cos.ap-beijing.myqcloud.com/assets/image/123498/2024-04-12/595da1171066c446c16fafdbc300fdde/reset_disable.png
- 提交按钮 default：https://courseware-maker-test-1252161091.cos.ap-beijing.myqcloud.com/assets/image/123498/2024-04-12/69ff415e09eae017c03f98519870cbef/submit_default.png
- 提交按钮 click：https://courseware-maker-test-1252161091.cos.ap-beijing.myqcloud.com/assets/image/123498/2024-04-12/a83c81138bd05ad689cd66110cf81a27/submit_click.png
- 提交按钮 disable：https://courseware-maker-test-1252161091.cos.ap-beijing.myqcloud.com/assets/image/123498/2024-04-12/56fdcf55e42828720c9f1071da957046/submit_disable.png
- 【勿动】关卡组件图：https://courseware-maker-1252161091.cos.ap-beijing.myqcloud.com/assets/image/V0025307/2025-06-23/e6eacbc91f79ba847869378d408b0f03.png

### 非诊断模式闯关成功撒花动效

用于 `practice` 非诊断练习模式。整关全部正确后，组件进入 `passSuccess` / `闯关成功` 状态并播放撒花动效。`passSuccess` 是组件监听全局判定成功的状态钩子，不需要手动绑定提交按钮或选项事件。

- 组件类型：`BaseComponent` / `MSpine`
- 组件名称：`撒花`
- 推荐层级：`zIndex = 7`
- 推荐位置尺寸：`x = 0`，`y = 0`，`w = 4196.01`，`h = 1909.72`，`scaleX = 1`，`scaleY = 1`
- Spine 资源：https://courseware-maker-1252161091.cos.ap-beijing.myqcloud.com/assets/spine/136920/2024-05-11/b25d6953490ba8456de8fe5af7877574.zip
- `spineId`：`2722`
- 成功音效：https://courseware-maker-1252161091.cos.ap-beijing.myqcloud.com/assets/audio/296026/2024-05-08/812b96218b5e8a3a4117ad391d6ea311.mp3

| 状态 | 标签 | 显隐 | Spine 动作 | 音效 |
| --- | --- | --- | --- | --- |
| `default` | 默认 | `hide` | 空字符串，不播放 | 无 |
| `passSuccess` | 闯关成功 | `show` | `animation` | 成功音效 |

---

## 数字键盘 — 跨皮肤共用（disabled 三态）

黄色界面和蓝色界面的 disabled 状态共用以下 3 张图（2026-04-13），换皮肤时**不替换**：

- number-button-disabled：https://courseware-maker-1252161091.cos.ap-beijing.myqcloud.com/assets/image/345733/2026-04-13/2ffa69204308a254d3f855eb6365c84b.png
- delete-button-disabled：https://courseware-maker-1252161091.cos.ap-beijing.myqcloud.com/assets/image/345733/2026-04-13/748be25c0d71159938aeb541a8691fbb.png
- confirm-button-disabled：https://courseware-maker-1252161091.cos.ap-beijing.myqcloud.com/assets/image/345733/2026-04-13/09509718385066484a0bb9ea392e6e2b.png

---

## 紫色界面 / fc9fbc3b（Q1–Q5）

- 题型：选择题
- 使用关卡：第1–5关

### 皮肤资产

- 背景图（【勿动】背景图片）：https://courseware-maker-1252161091.cos.ap-beijing.myqcloud.com/assets/image/345733/2026-04-22/fc9fbc3b0b55dc4437b75e7a2da0705c.png

### 题型资产（选择题按钮 — 跟题型绑定，不跟皮肤绑定）

- 点击选择按钮 default（未选中）：https://courseware-maker-1252161091.cos.ap-beijing.myqcloud.com/assets/image/345733/2026-04-22/7c040c641121266c3c82f3435ffb6793.png
- 点击选择按钮 choice（选中态）：https://courseware-maker-1252161091.cos.ap-beijing.myqcloud.com/assets/image/345733/2026-04-22/7fee2e4075d41cfc456c5e8ca8370f6a.png

### 文字色号

- `#EADFFF`：题型说明文字 / 题干文本（【题型说明】选择题 / 【可修改】文本-题干1）
- `#FFFFFF`：选择题按钮文字（【可修改】点击选择X / default & choice）

---

## 黄色界面 / e91dcb10（Q6–Q10）

- 题型：Q6–Q9 填空/计算题（带数字键盘）；Q10 拖拽题
- 使用关卡：第6–10关

### 皮肤资产

**背景图（【勿动】背景图片）：**
- https://courseware-maker-1252161091.cos.ap-beijing.myqcloud.com/assets/image/345733/2026-04-22/e91dcb1074e2690921f195bc88a07346.png

**输入框（【可修改】输入框X，仅 Q6–Q9 有）：**
- default 态：https://courseware-maker-1252161091.cos.ap-beijing.myqcloud.com/assets/image/345733/2026-04-22/52103843c58078ab5440e4671e218299.png
- answering / correct / wrong 态（共用同一张）：https://courseware-maker-1252161091.cos.ap-beijing.myqcloud.com/assets/image/345733/2026-04-22/674a213d6a38de357469b7c8917dc34a.png

**数字键盘专属态（【勿动】简易数字键盘，仅 Q6–Q9 有，2026-04-13）：**
- number-button-normal：https://courseware-maker-1252161091.cos.ap-beijing.myqcloud.com/assets/image/345733/2026-04-13/bc5b1d5790c7e68153b0d2f9d428e168.png
- delete-button-normal：https://courseware-maker-1252161091.cos.ap-beijing.myqcloud.com/assets/image/345733/2026-04-13/0c3f4ecd74a4c10d639fb332b458212a.png
- confirm-button-normal：https://courseware-maker-1252161091.cos.ap-beijing.myqcloud.com/assets/image/345733/2026-04-13/8289055a7c3c9361407d6b1f42c6a058.png
- number-button-pressed：https://courseware-maker-1252161091.cos.ap-beijing.myqcloud.com/assets/image/345733/2026-04-13/371e7a1a8ad7fb8771b0f7c66350be3d.png
- delete-button-pressed：https://courseware-maker-1252161091.cos.ap-beijing.myqcloud.com/assets/image/345733/2026-04-13/794f5f414e014de2ead9a1536a2bdc44.png
- confirm-button-pressed：https://courseware-maker-1252161091.cos.ap-beijing.myqcloud.com/assets/image/345733/2026-04-13/531ca85156153c4693605a334dd275e0.png
- disabled 三态：见「数字键盘跨皮肤共用」章节

### 文字色号

- `#8C3C0B`：题型说明文字 / 题干文本
- `#b15f2b`：数字键盘 number-button-normal 态文字
- `#ffffff`：数字键盘 pressed 态文字
- `#bcbcbc`：数字键盘 disabled 态文字

---

## 蓝色界面 / 291cc642（Q11–Q15）

- 题型：填空/计算题（带数字键盘）
- 使用关卡：第11–15关

### 皮肤资产

**背景图（【勿动】背景图片）：**
- https://courseware-maker-1252161091.cos.ap-beijing.myqcloud.com/assets/image/345733/2026-04-22/291cc642d06465540b7a25d3c3c1ff68.png

**输入框（【可修改】输入框X）：**
- default 态：https://courseware-maker-1252161091.cos.ap-beijing.myqcloud.com/assets/image/345733/2026-04-22/405c3617f7e6ef27bec1783b1e24f00d.png
- answering / correct / wrong 态（共用同一张）：https://courseware-maker-1252161091.cos.ap-beijing.myqcloud.com/assets/image/345733/2026-04-22/38d281b2bc32f4ec45bd0e6fc2f01279.png

**数字键盘专属态（【勿动】简易数字键盘，2026-04-22）：**
- number-button-normal：https://courseware-maker-1252161091.cos.ap-beijing.myqcloud.com/assets/image/345733/2026-04-22/e5512d503b36022cdf4f24b926b0a7b8.png
- delete-button-normal：https://courseware-maker-1252161091.cos.ap-beijing.myqcloud.com/assets/image/345733/2026-04-22/cc743b5b6ab63a8ac22714a7f92f8418.png
- confirm-button-normal：https://courseware-maker-1252161091.cos.ap-beijing.myqcloud.com/assets/image/345733/2026-04-22/b65750d3655ed121cb690097fdd4c884.png
- number-button-pressed：https://courseware-maker-1252161091.cos.ap-beijing.myqcloud.com/assets/image/345733/2026-04-22/f711f615f583064fc85c74c8e895e297.png
- delete-button-pressed：https://courseware-maker-1252161091.cos.ap-beijing.myqcloud.com/assets/image/345733/2026-04-22/8fcd2c1c0cfe50e0087ef47eb901722d.png
- confirm-button-pressed：https://courseware-maker-1252161091.cos.ap-beijing.myqcloud.com/assets/image/345733/2026-04-22/70c2b00cdaab71cbf1d6af596d9a3fae.png
- disabled 三态：见「数字键盘跨皮肤共用」章节

### 文字色号

- `#9EFAFF`：题型说明文字
- `#4450ca`：数字键盘 number-button-normal 态文字
- `#ffffff`：数字键盘 pressed 态文字 / 输入框文字（answering/correct/wrong）
- `#bcbcbc`：数字键盘 disabled 态文字
