# 魔法拼拼乐配置生成工作流

## 概览

从「单词拼拼乐测试表格」的题目数据，生成可直接导入 CoursewareMaker 的魔法拼拼乐配置 JSON。

---

## 数据来源

| 来源 | 说明 |
|---|---|
| 题目表格 | 知音楼 Excel/Sheet，含题目序号、音频命名、题干图片、题干文本、答题区、选项 |
| 校验基准 | `reference_configs/spelling_validation_ref.json`（从单词拼拼乐游戏抓取，含题目图片/音频 URL） |
| 结构参考 | `output/mofappl_configs/77cb396a-babd-11f0-885a-ba4dce53cceb.json`（5槽模板） |

---

## 数据映射规则

| 表格字段 | 魔法拼拼乐对应 | 备注 |
|---|---|---|
| `拖拽放置区`（type） | `LDragPlace` 组件，itemList=[答题区内容] | 每关槽位数 = 拖拽放置区数量 |
| 选项文本 | `MDraggable` 组件，tag=选项文本 | |
| `英语空格`（type） | **跳过，不生成组件** | 由文本头/尾图片留白实现 |
| `文本(固定)` | **跳过，不生成组件** | 固定内容画进图里 |
| 题干图片 URL | `题目配图` 组件的 source.MSprite.value | 从校验基准文件提取 |
| 题目音频 URL | `喇叭` 组件的 source.MAudio.value | 从校验基准文件提取 |
| `文本-xx`（固定字母） | `MLabel` 组件，name=`文本-xx` | 如 `文本-a`、`文本-the` |

---

## 组件层级规则

> **关键**：渲染顺序由 JSON `components` 数组顺序决定，**不是 zIndex**。  
> 数组越靠后 = 面板越靠下 = 层级越高（渲染在上层）。

标准层级顺序（从底层到顶层，即数组从前到后）：

```
节点
题目配图
题图光效
投影1
投影2
IP角色
关卡数组件
喇叭
拖拽放置区1..N
英语空格1..M（占位，默认隐藏）
文本-xx（固定字母，如 文本-a）
英语空格（剩余）
文本-fin          ← 句子展示组件
IP角色烟雾遮挡    ← 必须在文本-fin 之后（层级高于 fin）
拖拽物品1..K      ← 最高层，在所有组件之上
```

---

## 组件 State 规则

### 拖拽放置区 / 文本-xx（固定字母）
- `default`：`active=show`
- `compLoadFinish`：`active=hide`，倒计时3秒→default（与文本-fin展示句子同步隐藏后显现）

### 文本-fin（句子展示）
- `default`：`active=hide`
- `compLoadFinish`：`active=show`，倒计时3秒→default（展示3秒后隐藏，gameplay出现）

### 拖拽物品
- `default`：隐藏（active=hide）
- 各答题状态：show/placed/dragging/correct/wrong

---

## 脚本

| 脚本 | 用途 |
|---|---|
| `scripts/generate_mofappl_config.py` | 从题目数据生成配置 JSON |
| `scripts/save_game_config_via_cdp.js` | 导入配置到 CoursewareMaker |
| `scripts/fix_mofappl_v3.py` | 修复坐标偏移、尺寸、state 等问题 |

---

## 生成流程

```bash
# 1. 生成配置
python3 scripts/generate_mofappl_config.py \
  --input data/题目数据.xlsx \
  --ref reference_configs/spelling_validation_ref.json \
  --template output/mofappl_configs/77cb396a-babd-11f0-885a-ba4dce53cceb.json \
  --output output/mofappl_configs/新游戏名.json

# 2. 修复坐标/尺寸/state
python3 scripts/fix_mofappl_v3.py output/mofappl_configs/新游戏名.json

# 3. 导入编辑器（需要 Chrome 9222 端口已开启）
node scripts/save_game_config_via_cdp.js <game_id> output/mofappl_configs/新游戏名.json
```

---

## 关键参数

```python
# 组件 component_id
SLOT_COMPONENT_ID  = 'f9b49402-f73d-11ee-b9ef-8e2f78cd4bcd'   # LDragPlace
ITEM_COMPONENT_ID  = 'd8b73bec-f719-11ee-b9ef-8e2f78cd4bcd'   # MDraggable

# 拖拽物品布局
ITEM_Y       = -342.35
ITEM_STEP_X  = 368         # 每个物品横向间距

# 坐标系
# 校验文件中心 x = -163.89，需 +163.89 对齐画布中心

# 文本颜色
TEXT_COLOR_LABEL  = '#5f5cd7'   # 文本-xx
ITEM_DEFAULT      = '#cc601b'
ITEM_CORRECT      = '#2f9b1f'
ITEM_WRONG        = '#f51515'

# 文本头背景图（固定不变）
TEXT_BG_URL = 'https://courseware-maker-1252161091.cos.ap-beijing.myqcloud.com/assets/image/345733/2026-04-29/fdae75aa5ed239208875fdd6a9810489.png'
```

---

## 校验检查项

生成后用 `spelling_validation_ref.json` 做如下校验：

- [ ] 每关槽位数量与表格一致
- [ ] 每关拖拽物品 tag 与表格选项列一致
- [ ] 题目配图 URL 与校验基准匹配
- [ ] 题目音频 URL 与校验基准匹配
- [ ] IP角色烟雾遮挡在数组中位于 文本-fin 之后、拖拽物品之前
- [ ] 文本-xx 有 compLoadFinish=hide+3s 状态
- [ ] 文本-fin 有 compLoadFinish=show+3s 状态


---
## ⚠️ 重要规则（2026-05-11）

**句子和作答区排布必须按每题实际需求灵活处理，不能照搬结构模板！**
- 每题槽位数量、组件顺序、排布方式根据题目数据动态确定
- 模板仅作为组件类型和参数参考，不作为排布参考
