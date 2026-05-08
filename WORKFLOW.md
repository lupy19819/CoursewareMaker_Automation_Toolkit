# CoursewareMaker 自动化工作流程

## 游戏配置写入修复（2026-05-08 实测版）

### 问题根源

`save_game_config_via_cdp.js` 之前出现过两类问题：

1. `fetch` 没有发送 cookies/session，只带 `beibotoken`，可能触发服务端 500。
2. 使用 `POST /beibo/game/config/game` 更新已有游戏时，部分 `game_id` 会被平台当作新建/另存版本处理，返回：

```text
游戏名字重复，请修改名字后再保存。（若期望修改原游戏，请从修改入口进入）
```

### 当前正确保存方式

更新已有游戏配置使用 `PUT`，并且所有请求都必须带 `credentials: "include"`：

```javascript
fetch(url, {
  method: "PUT",
  credentials: "include",
  headers: {
    "Content-Type": "application/json;charset=UTF-8",
    beibotoken: token
  },
  body: JSON.stringify(payload)
})
```

### CoursewareMaker 保存 API 细节

**GET 游戏详情：**

```http
GET https://sszt-gateway.speiyou.com/beibo/game/config/game?game_id={game_id}
Headers: { beibotoken: <token> }
Credentials: include
```

**PUT 更新配置：**

```http
PUT https://sszt-gateway.speiyou.com/beibo/game/config/game
Headers:
  Content-Type: application/json;charset=UTF-8
  beibotoken: <token>
Credentials: include

Body:
{
  ...GET /game 返回的 result 元数据（排除 components 大字段）,
  configuration: { ... }  // 对象，不是字符串
}
```

注意：`components` 是组件库大字段，可能达到几十 MB，写回前必须排除。

## 运动PK新建 + 导入流程（已跑通）

### 关键规则

- 运动PK模板 ID：`47995925-fb37-11ef-8c1b-ce918f8037e8`
- 运动PK组件 ID：`21dcca07-c1e6-11ef-895a-4eb2c30c826b`
- 新建时必须使用 `game_type: 2`
- 新建后打开 `#/customEditor?game_id=...`
- 可先创建空壳 `{}`，再用 `PUT` 导入完整 `custom_game` 配置

### 已验证命令

```bash
# 1. 新建运动PK空壳游戏
node scripts/create_game_auto.js \
  "测试运动PK新建" \
  "47995925-fb37-11ef-8c1b-ce918f8037e8" \
  ""

GAME_ID=$(cat latest_game_id.txt)

# 2. 导入运动PK配置并保存
node scripts/save_game_config_via_cdp.js "$GAME_ID" "配置.json"
```

### 2026-05-08 实测结果

- 新建游戏：`测试运动PK新建`
- 新建 `game_id`：`0ada627b-4a89-11f1-a80e-6effa3ce9c89`
- 创建元数据：`game_type: 2`
- 导入接口：`PUT /beibo/game/config/game`
- 保存结果：`code: 0, msg: success`
- 线上配置与本地配置标准化比对：`exact_equal: true`
- 关卡数：本地 10，线上 10
- 组件：`运动PK赛`

## 工作流总结

1. 启动 Chrome/Edge CDP `9222` 并登录 CoursewareMaker。
2. 运动PK用 `create_game_auto.js` 创建，脚本会识别模板并使用 `game_type: 2`。
3. 生成或准备 `custom_game` 运动PK配置。
4. 导入配置用 `save_game_config_via_cdp.js`，走 `PUT + credentials: include`。
5. 导入后重新 GET 游戏详情，严格比对线上 `configuration` 与本地配置。
6. 预览确认后再发布。

## 相关脚本

- `scripts/create_game_auto.js` - 创建新游戏；运动PK自动使用 `game_type: 2` 和 customEditor。
- `scripts/save_game_config_via_cdp.js` - 更新已有游戏配置；使用 `PUT + credentials: include`。
- `scripts/build_yundong_pk_config.py` - 生成运动PK配置。
- `scripts/validate_yundong_pk_config.py` - 校验运动PK配置结构。
- `scripts/publish_game_auto.js` - 发布游戏。
