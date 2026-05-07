# CoursewareMaker 自动化工作流程

## 游戏配置写入修复 (2026-05-07)

### 问题根源
脚本 `save_game_config_via_cdp.js` 一直返回 500 错误，根本原因是 fetch 调用没有发送 cookies（session），导致服务端认证失败。

### 关键修复
在所有 fetch 调用中添加 `credentials: 'include'`：

```javascript
fetch(url, {
  credentials: "include",  // ← 必须
  headers: { beibotoken: token }
})
```

### CoursewareMaker 保存 API 细节

**GET 游戏详情**：
```
GET https://sszt-gateway.speiyou.com/beibo/game/config/game?game_id={game_id}
Headers: { beibotoken: <token> }
```

**保存配置**：
```
POST https://sszt-gateway.speiyou.com/beibo/game/config/game
Headers: { 
  "Content-Type": "application/json;charset=UTF-8",
  beibotoken: <token>
}
Body: {
  user: "用户名",
  game_type: 2,
  game_name: "游戏名称",
  parent_id: "父游戏ID",  // 从服务端返回的 detail 获取
  year, term_id, subject_id, grade, cnum_id,
  configuration: { ... }  // ← 对象，不是字符串
}
```

### 「修改」入口 vs 「新建」入口
- **游戏列表 → 点击「修改」**：打开的是草稿版本（不同的 game_id），保存会更新草稿
- **游戏列表 → 点击「预览」→ 「编辑」**：打开的是已发布版本，保存会创建新版本（parent_id 指向原游戏）
- **直接访问 `#/editor?game_id=xxx`**：如果该游戏是你创建的，等同于修改入口

### 工作流总结
1. **新建游戏**：通过「新建游戏」或 API 创建
2. **配置导入**：用修复后的脚本直接写入配置
3. **验证**：打开编辑器检查是否正常加载
4. **发布**：手动点击发布按钮

### 相关脚本
- `create_game_auto.js` - 创建新游戏（带模板初始化）
- `save_game_config_via_cdp.js` - 更新现有游戏配置（已修复 credentials 问题）
- `publish_game_auto.js` - 发布游戏
