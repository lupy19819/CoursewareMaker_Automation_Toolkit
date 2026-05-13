# CoursewareMaker 自动化工作流程

## 最新全局执行入口（2026-05-13）

完整工作流以 `docs/WORKFLOW_DEBUG_FLOWCHART.md` 和 `docs/workflow_debug_interactive.html` 为准；本文件保留已经跑通的创建/保存关键链路。

当前执行顺序的硬规则：

1. 先判定用户意图，再判定游戏类型。反馈/修改/调整类请求进入配置返修；已有 `game_id` 或具体游戏名的上传/保存请求进入导入保存；只有明确“新建/创建新的”才创建游戏。
2. 目标游戏解析支持 `game_id` 和具体游戏名。`game_id` 优先；游戏名必须精确查询到唯一目标，同名或多结果先确认。
3. 游戏类型只分三大类：运动PK、模板游戏、标准组件化题。任务清单必须锁定 `game_family`、baseline、脚本、输出路径、`game_type` 和编辑器入口。
4. 素材确认在任务拆分前完成；上传前查资源 list，同名资源必须先让提需用户确认使用现有资源还是改名上传。
5. 校验按 `game_family` 分流：运动PK/标准组件化题可用 `validate_config.js`；模板游戏走专项规则、参考配置不变量、回读比对和预览。
6. 配置返修只改用户反馈项和直接依赖，禁止顺手重排、换模板、替换无关资源或新建游戏。
7. 保存统一使用 `GET 完整元信息 → 只替换 configuration → PUT /beibo/game/config/game`，`components` 保留原数组或补 `[]`。

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
  ...GET /game 返回的 result 元数据,
  components: [...原 components 数组，若不是数组则补 []],
  configuration: { ... }  // 对象，不是字符串
}
```

注意：为贴近手动保存流程，上传脚本统一保留 `GET /game` 返回的完整元信息，仅替换 `configuration`。`components` 字段保留原数组；如果 GET 结果里不是数组，则补 `[]`。

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
4. 导入配置优先用 `save_game_config_via_cdp.js`，走浏览器 CDP 通道；`upload_game_config.py` 作为 API 直传通道。两者保存 payload 结构一致：GET 完整元信息，仅替换 `configuration` 后 PUT。
5. 导入后重新 GET 游戏详情，严格比对线上 `configuration` 与本地配置。
6. 预览确认后再发布。

## 相关脚本

- `scripts/create_game_auto.js` - 创建新游戏；运动PK自动使用 `game_type: 2` 和 customEditor。
- `scripts/save_game_config_via_cdp.js` - CDP 浏览器通道更新已有游戏配置；使用 `PUT + credentials: include`，保留完整元信息。
- `scripts/upload_game_config.py` - API 直传通道更新已有游戏配置；需 token/cookie，payload 结构与 CDP 脚本一致。
- `scripts/build_yundong_pk_config.py` - 生成运动PK配置。
- `scripts/validate_yundong_pk_config.py` - 校验运动PK配置结构。
- `scripts/publish_game_auto.js` - 发布游戏。
