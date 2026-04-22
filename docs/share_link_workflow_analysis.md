# CoursewareMaker 生成分享链接流程分析

**监控时间**: 2026-04-16 16:20:11 - 16:20:53  
**测试游戏**: game_id = 89460aa0-3250-11f1-bdd1-76b63c7cf458

---

## 📊 流程概述

生成分享链接是一个**2步流程**：
1. 查询是否已有分享链接（可选）
2. 创建新的分享链接

---

## 🔄 详细流程

### 步骤1: 查询已有分享链接（可选）
**API**: `POST https://sszt-gateway.speiyou.com/beibo/game/config/searchPreviewUrl`

**请求头**:
```json
{
  "beibotoken": "从 Chrome localStorage 中的 GAMEMAKER_TOKEN 获取",
  "content-type": "application/json;charset=UTF-8"
}
```

**请求体**:
```json
{
  "game_id": "游戏ID"
}
```

**响应示例**:
```json
{
  "code": 0,
  "result": {
    "create_time": "2026-04-16 13:54:15",
    "preview_url": "https://coursewaremaker.speiyou.com/#/share-preview?pw=Z2FtZV9pZD04OTQ2MGFhMC0zMjUwLTExZjEtYmRkMS03NmI2M2M3Y2Y0NTgmdD0xNzc2MzE4ODU1",
    "pw": "Z2FtZV9pZD04OTQ2MGFhMC0zMjUwLTExZjEtYmRkMS03NmI2M2M3Y2Y0NTgmdD0xNzc2MzE4ODU1",
    "valid_date": "2026-04-23 13:54:15",
    "valid_time": "7"
  },
  "msg": "success"
}
```

**说明**:
- 如果游戏已有分享链接且未过期，返回已有链接
- 如果没有或已过期，`result` 可能为空

---

### 步骤2: 创建新的分享链接
**API**: `POST https://sszt-gateway.speiyou.com/beibo/game/config/createPreviewUrl`

**请求头**:
```json
{
  "beibotoken": "从 Chrome localStorage 中的 GAMEMAKER_TOKEN 获取",
  "content-type": "application/json;charset=UTF-8"
}
```

**请求体**:
```json
{
  "game_id": "游戏ID",
  "base_preview_url": "https://coursewaremaker.speiyou.com/#/share-preview"
}
```

**响应示例**:
```json
{
  "code": 0,
  "result": {
    "create_time": "2026-04-16 16:20:53",
    "preview_url": "https://coursewaremaker.speiyou.com/#/share-preview?pw=Z2FtZV9pZD04OTQ2MGFhMC0zMjUwLTExZjEtYmRkMS03NmI2M2M3Y2Y0NTgmdD0xNzc2MzI3NjUz",
    "pw": "Z2FtZV9pZD04OTQ2MGFhMC0zMjUwLTExZjEtYmRkMS03NmI2M2M3Y2Y0NTgmdD0xNzc2MzI3NjUz",
    "valid_date": "2026-04-23 16:20:53",
    "valid_time": "7"
  },
  "msg": "success"
}
```

**说明**:
- 每次调用都会生成新的分享链接
- 新链接会覆盖旧链接
- 默认有效期为7天

---

## 📦 响应字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `preview_url` | string | 完整的分享预览链接 |
| `pw` | string | 加密参数（base64编码，包含game_id和时间戳） |
| `create_time` | string | 创建时间（格式: YYYY-MM-DD HH:mm:ss） |
| `valid_date` | string | 有效期截止日期 |
| `valid_time` | string | 有效天数（默认"7"） |

---

## 🔐 pw参数解析

`pw` 参数是 base64 编码的字符串，解码后格式为：
```
game_id=89460aa0-3250-11f1-bdd1-76b63c7cf458&t=1776327653
```

其中：
- `game_id`: 游戏ID
- `t`: Unix时间戳（用于验证有效期）

---

## 🎯 自动化关键点

1. **认证**:
   - 从 Chrome `localStorage` 获取 `GAMEMAKER_TOKEN`
   - 请求头使用 `beibotoken` 字段

2. **简化流程**:
   - 可以直接调用 `createPreviewUrl` 生成新链接
   - 无需先调用 `searchPreviewUrl` 查询

3. **批量生成**:
   - 支持批量为多个游戏生成分享链接
   - 每个游戏需要单独调用API

4. **错误处理**:
   - 检查 `code` 是否为 0
   - 检查 `result` 是否存在

---

## 📝 使用场景

### 场景1: 单个游戏生成分享链接
```bash
node generate_share_link.js <game_id>
```

### 场景2: 批量生成分享链接
```bash
node batch_generate_share_links.js xinyi_game_id_list.json
node batch_generate_share_links.js xiner_game_id_list.json
```

### 场景3: 查询已有链接
```bash
node query_share_link.js <game_id>
```

---

## 🚀 完整工作流整合

```bash
# 步骤1: 创建游戏
node create_game_auto.js "游戏名称" "模板ID" "empty_config.json"
GAME_ID=$(cat latest_game_id.txt)

# 步骤2: 导入配置
node save_game_config_via_cdp.js $GAME_ID game_config.json

# 步骤3: 发布游戏
node publish_game_auto.js $GAME_ID 2026 "2" "1"

# 步骤4: 生成分享链接（新增！）
node generate_share_link.js $GAME_ID
```

---

## 🔍 监控记录

完整的操作已记录在：
```
D:/codexProject/chrome_monitoring_logs/
├── share_link_1776327611551.log       # 主日志（人类可读）
├── network_share_1776327611551.jsonl  # 完整的网络请求/响应
└── events_share_1776327611551.jsonl   # 页面事件流
```

---

## ✅ 总结

生成分享链接的流程非常简单，只需要：
1. 获取游戏ID
2. 调用 `createPreviewUrl` API
3. 返回的 `preview_url` 即为分享链接

**优势**:
- 流程简单，只需1个API调用
- 支持批量生成
- 链接有7天有效期
- 完全可自动化
