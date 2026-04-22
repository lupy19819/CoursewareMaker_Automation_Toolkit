# CoursewareMaker 游戏创建流程分析

**分析时间**: 2026-04-16 14:43-14:44  
**新建游戏ID**: `b82175b7-395f-11f1-bdd1-76b63c7cf458`  
**游戏名称**: `2026新二思维全能力诊断1`  
**使用模板ID**: `70a3010b-0b7a-11ef-b3a3-fa7902489df6`

---

## 🎯 完整流程步骤

### 步骤1: 导航到模板选择页
**URL**: `https://coursewaremaker.speiyou.com/#/list/template`

### 步骤2: 选择模板进入编辑器
**导航到**: `https://coursewaremaker.speiyou.com/#/editor?template_id=70a3010b-0b7a-11ef-b3a3-fa7902489df6`

### 步骤3: 创建游戏（POST请求）

**API端点**:
```
POST https://sszt-gateway.speiyou.com/beibo/game/config/game
```

**必需Headers**:
```json
{
  "beibotoken": "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ7XCJlbWFpbFwiOlwiamlhbmdoYW8xNkB0YWwuY29tXCIsXCJlbXBOb1wiOlwiMzQ1NzMzXCIsXCJsb2dpblRpbWVPdXRcIjo5NjAsXCJuYW1lXCI6XCLmsZ_mmIpcIixcInJlZnJlc2hUaW1lXCI6XCIyMDI2LTA0LTE2IDE0OjUwOjA4XCIsXCJyZWZyZXNoVGltZU91dFwiOjEwfSIsImV4cCI6MTc3NjM3OTIwOH0.z6maijPz2FNABEPzIEGnn8XwsrgnXpiSsFMXdCWc3mM",
  "Content-Type": "application/json;charset=UTF-8"
}
```

**请求体结构**:
```json
{
  "user": "江昊（jiang hao）",
  "game_type": 1,
  "game_name": "2026新二思维全能力诊断1",
  "template_id": "70a3010b-0b7a-11ef-b3a3-fa7902489df6",
  "configuration": {
    "common": {
      "settlement_component": { ... },
      "additional_settlement_component": { ... },
      "global_config": { ... },
      "levels": { ... },
      "level_settlement": { ... }
    },
    "game": [ ... ],
    "additional": [],
    "components": [ ... ]
  }
}
```

**响应**:
```json
{
  "code": 0,
  "result": {
    "game_id": "b82175b7-395f-11f1-bdd1-76b63c7cf458"
  },
  "msg": "success"
}
```

### 步骤4: 锁定游戏（POST请求）

**API端点**:
```
POST https://sszt-gateway.speiyou.com/beibo/game/config/lock
```

**请求体**:
```json
{
  "id": "b82175b7-395f-11f1-bdd1-76b63c7cf458",
  "version": "0.0",
  "type": "game"
}
```

### 步骤5: 导航到新游戏编辑页
**URL**: `https://coursewaremaker.speiyou.com/#/editor?game_id=b82175b7-395f-11f1-bdd1-76b63c7cf458`

---

## 🤖 自动化关键要素

### 1. 认证
- **Token来源**: Chrome localStorage 中的 `GAMEMAKER_TOKEN`
- **Token格式**: JWT (eyJhbGciOiJIUzI1NiJ9...)
- **Token位置**: HTTP Header `beibotoken`

### 2. 必需参数
| 参数 | 说明 | 示例 |
|------|------|------|
| `user` | 创建者名称 | "江昊（jiang hao）" |
| `game_name` | 游戏名称 | "2026新二思维全能力诊断1" |
| `game_type` | 游戏类型 | `1` |
| `template_id` | 模板ID | "70a3010b-0b7a-11ef-b3a3-fa7902489df6" |
| `configuration` | 游戏配置JSON | 完整配置对象 |

### 3. 配置结构关键点
- **组件列表**: `configuration.components` - 包含所有使用的组件ID和URL
- **关卡数据**: `configuration.game[]` - 每关的完整配置
- **结算组件**: `configuration.common.settlement_component` - 游戏结束界面
- **全局配置**: `configuration.common.global_config` - 字体、计时、计分等

---

## 📋 自动化脚本思路

### 方案A: 纯API方式（推荐）
```javascript
// 1. 从 Chrome localStorage 读取 token
const token = getTokenFromChrome();

// 2. 准备游戏配置（从模板或自定义）
const gameConfig = buildGameConfiguration({
  gameName: "游戏名称",
  templateId: "70a3010b-0b7a-11ef-b3a3-fa7902489df6",
  levels: [...]
});

// 3. 调用创建游戏API
const response = await fetch('https://sszt-gateway.speiyou.com/beibo/game/config/game', {
  method: 'POST',
  headers: {
    'beibotoken': token,
    'Content-Type': 'application/json;charset=UTF-8'
  },
  body: JSON.stringify({
    user: getUserName(),
    game_type: 1,
    game_name: gameName,
    template_id: templateId,
    configuration: gameConfig
  })
});

// 4. 提取游戏ID
const { game_id } = response.result;

// 5. 锁定游戏
await lockGame(game_id, token);

// 6. 返回游戏ID和编辑器URL
return {
  gameId: game_id,
  editorUrl: `https://coursewaremaker.speiyou.com/#/editor?game_id=${game_id}`
};
```

### 方案B: CDP浏览器控制方式
```javascript
// 1. 通过CDP打开编辑器
await page.goto(`https://coursewaremaker.speiyou.com/#/editor?template_id=${templateId}`);

// 2. 等待编辑器加载
await page.waitForSelector('.editor-container');

// 3. 注入配置
await page.evaluate((config) => {
  window.editor.setConfiguration(config);
}, configuration);

// 4. 触发保存按钮
await page.click('.save-button');

// 5. 从响应中捕获game_id
const gameId = await page.evaluate(() => {
  return window.currentGameId;
});
```

---

## ⚠️ 注意事项

1. **Token有效期**: JWT token包含过期时间，需定期刷新
2. **配置验证**: 游戏配置必须符合模板结构，否则创建失败
3. **组件依赖**: 配置中引用的组件必须在 `components` 数组中声明
4. **版本控制**: Lock API 中的 `version` 字段在初次创建时为 "0.0"
5. **CORS限制**: API调用需要正确的 Origin 头（`https://coursewaremaker.speiyou.com`）

---

## 🔗 相关API端点总结

| 端点 | 方法 | 用途 |
|------|------|------|
| `/beibo/game/config/game` | POST | 创建/更新游戏 |
| `/beibo/game/config/games` | GET | 获取游戏列表 |
| `/beibo/game/config/lock` | POST | 锁定/解锁游戏 |

---

## 📊 本次创建的游戏信息

**游戏ID**: `b82175b7-395f-11f1-bdd1-76b63c7cf458`  
**编辑器链接**: https://coursewaremaker.speiyou.com/#/editor?game_id=b82175b7-395f-11f1-bdd1-76b63c7cf458  
**创建时间**: 2026-04-16 14:44:30  
**模板**: 拖拽类游戏模板 (70a3010b-0b7a-11ef-b3a3-fa7902489df6)  
**组件数量**: 3个（OverTips、MDraggbale、LDragPlace）  
**关卡数量**: 1关
