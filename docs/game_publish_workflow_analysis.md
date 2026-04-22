# CoursewareMaker 游戏发布流程分析

## 📊 概述

通过监控浏览器实际操作，完整捕获了发布游戏的API调用流程。

**监控时间**: 2026-04-16 15:54:01  
**测试游戏**: 2026新二思维全能力诊断1 (b82175b7-395f-11f1-bdd1-76b63c7cf458)

---

## 🔄 发布流程（4步）

### 步骤1: 设置发布信息
**API**: `PUT https://sszt-gateway.speiyou.com/beibo/game/config/gamePublish`

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
  "year": 2026,
  "term_id": "2",           // 学期ID（1=春季, 2=秋季）
  "subject_id": "1",        // 学科ID（1=数学）
  "grade": "5",             // 年级（1-6）
  "cnum_id": "31",          // 课程编号ID
  "is_experiential_game": 0, // 是否体验游戏
  "is_diagnose": 1,         // 是否诊断游戏
  "engine_version": "3.X",  // 引擎版本
  "desc": "",               // 描述（可选）
  "source": 1,              // 来源
  "knowledge": [],          // 知识点（数组）
  "skill_tag": 0,           // 技能标签
  "is_level": 0,            // 是否分级
  "settlement_type": 0,     // 结算类型
  "is_play": 1,             // 是否可玩
  "is_syn": 1,              // 是否同步
  "game_id": "游戏ID"
}
```

**响应**:
```json
{
  "code": 0,
  "result": null,
  "msg": "success"
}
```

---

### 步骤2: 更新游戏描述
**API**: `PUT https://sszt-gateway.speiyou.com/beibo/game/config/gameDesc`

**请求体**:
```json
{
  "game_id": "游戏ID",
  "desc": ""               // 游戏描述（可选）
}
```

**响应**:
```json
{
  "code": 0,
  "result": null,
  "msg": "success"
}
```

---

### 步骤3: 加入构建队列（实际发布）
**API**: `POST https://sszt-gateway.speiyou.com/beibo/game/config/build_queue`

**请求体**:
```json
{
  "game_id": "游戏ID"
}
```

**响应**:
```json
{
  "code": 0,
  "result": null,
  "msg": "success"
}
```

> **重要**: 这一步是真正的发布操作，游戏会进入构建队列并最终发布上线。

---

### 步骤4: 解锁游戏
**API**: `POST https://sszt-gateway.speiyou.com/beibo/game/config/unlock`

**请求体**:
```json
{
  "game_id": "游戏ID"
}
```

**响应**:
```json
{
  "code": 0,
  "result": null,
  "msg": "success"
}
```

> **说明**: 解锁游戏，允许其他用户编辑。在发布完成后自动调用。

---

## 🔑 认证方式

所有API请求都需要在请求头中携带 `beibotoken`：

```javascript
// 从 Chrome 的 localStorage 获取
const token = localStorage.getItem('GAMEMAKER_TOKEN');

// 请求头格式
headers: {
  'beibotoken': token,
  'content-type': 'application/json;charset=UTF-8'
}
```

---

## 📝 关键字段说明

| 字段 | 说明 | 示例值 |
|------|------|--------|
| `year` | 年份 | 2026 |
| `term_id` | 学期ID | "2" (秋季) |
| `subject_id` | 学科ID | "1" (数学) |
| `grade` | 年级 | "5" (五年级) |
| `cnum_id` | 课程编号 | "31" |
| `is_diagnose` | 是否诊断游戏 | 1 (是) |
| `engine_version` | 引擎版本 | "3.X" |
| `is_play` | 是否可玩 | 1 (是) |
| `is_syn` | 是否同步 | 1 (是) |

---

## 🚀 自动化思路

### 批量发布脚本流程

```
1. 读取游戏ID列表
2. 对每个游戏ID:
   a. 获取 GAMEMAKER_TOKEN
   b. 调用 gamePublish API 设置发布信息
   c. 调用 gameDesc API 更新描述
   d. 调用 build_queue API 加入构建队列
   e. 调用 unlock API 解锁游戏
3. 记录发布结果
```

### 注意事项

1. **Token 过期**: Token 有效期为 960 分钟（16小时），需要定期刷新
2. **并发控制**: 建议串行发布，避免触发服务器限流
3. **错误处理**: 每个API调用都需要检查返回的 `code` 字段
4. **发布状态**: 发布成功后游戏会进入构建队列，可能需要等待几分钟才能真正上线

---

## 📁 相关文件

- **监控日志**: `D:/codexProject/chrome_monitoring_logs/game_publish_1776325984561.log`
- **网络日志**: `D:/codexProject/chrome_monitoring_logs/network_publish_1776325984561.jsonl`
- **自动化脚本**: `D:/codexProject/publish_game_auto.js`（待创建）

---

## 🔗 API Base URL

```
https://sszt-gateway.speiyou.com/beibo/game/config/
```

所有API端点：
- `PUT /gamePublish` - 设置发布信息
- `PUT /gameDesc` - 更新描述
- `POST /build_queue` - 加入构建队列
- `POST /unlock` - 解锁游戏
