# CoursewareMaker 自动化工作流程

## 最新全局执行入口（2026-05-18）

完整工作流以 `workflow/` 机器可读规则和确定性 CLI 为执行入口，`docs/WORKFLOW_DEBUG_FLOWCHART.md` 和 `docs/workflow_debug_interactive.html` 作为排查与预览说明。

跨端、跨模型执行时，必须先让脚本决定流程，AI 只负责转述脚本结果、补问缺失信息和解释错误。

跨设备兼容要求：

- 所有新增脚本必须使用相对项目路径、`Path.home()`、`Path.cwd()` 或环境变量，不得写死 `D:/codexProject`、`/Users/...`、`/home/...`。
- CoursewareMaker 登录态统一从已开启 CDP 的浏览器读取，端口默认 `9222`，可用 `CHROME_PORT` 覆盖。
- Yach/OpenClaw 配置查找顺序为 `--config`、`YACH_CONFIG_FILE`、项目根 `.yach-config.json`、`~/.openclaw/workspace/.yach-config.json`。
- 输出文件默认写入项目内 `output/`，可用脚本参数或 `COURSEWARE_OUTPUT_DIR` 覆盖。

```bash
# 1. 用户消息 -> 结构化路由
python3 workflow/workflow_router.py -m "把配置上传到 game_id=... 的过桥大冒险游戏里试试 config.json" --pretty

# 2. 路由结果 -> 确定性任务单；缺信息时返回 status=blocked
python3 workflow/workflow_router.py -m "..." | python3 workflow/workflow_planner.py --pretty

# 3. 执行动作前校验是否越权
python3 workflow/workflow_router.py -m "..." \
  | python3 workflow/workflow_planner.py \
  | python3 workflow/workflow_guard.py --action save_existing --pretty
```

确定性规则文件：

- `workflow/intent_rules.json`：意图识别优先级、允许/禁止动作。
- `workflow/game_type_rules.json`：三大类和实际游戏类型关键字、baseline、`game_type`、编辑器入口。
- `workflow/stage_policy.json`：每个环节的必填输入、阻塞条件、动作白名单/黑名单。
- `workflow/script_registry.json`：各环节固定脚本入口。
- `workflow/validation_policy.json`：按 `game_family` 分流的校验策略。
- `workflow/execution_registry.json`：统一执行器使用的实际命令模板和 validator。
- `workflow/game_input_schemas.json`：每个游戏的输入字段、资源字段、动态/固定资源边界。
- `workflow/audit_workflow.py`：执行前静态审计，发现缺 adapter、缺模板、缺 validator 时阻断。

当前执行顺序的硬规则：

1. 先跑 `workflow_router.py`，由规则表判定用户意图和游戏类型；不得让 AI 自由选择环节。
2. 目标游戏解析支持 `game_id` 和具体游戏名。`game_id` 优先；游戏名必须精确查询到唯一目标，同名或多结果先确认。
3. 游戏类型只分三大类：运动PK、模板游戏、标准组件化题。任务清单必须锁定 `game_family`、baseline、脚本、输出路径、`game_type` 和编辑器入口。
4. “新建/创建新游戏”且没有 `game_id` 时，显式新建意图优先于“上传过素材/导入素材”等资源描述，避免误走已有游戏导入环节。
5. 素材确认在任务拆分前完成；上传前查项目内 `resources/latest_resources.json`，同名资源必须先让提需用户确认使用现有资源还是改名上传；同步资源时也必须合并回这个 git 内资源清单。生成阶段只校验当前题目表实际引用的资源名，不让历史全库重复名阻断无关任务。
6. 校验按 `game_family` 分流，并采用“三层主校验 + 两个主流程收口”：规则脚本校验为主，参考配置不变量对比为辅，案例回归用于防止脚本退化；保存后由主流程统一做回读比对和预览。模板游戏统一增加 `scripts/validate_template_game_config.py` 作为生成后规则校验入口。
7. 模板游戏允许固定模板资源写死或从参考配置继承，例如背景、皮肤、spine、组件 bundle、状态 key、公共层和布局骨架；题目相关信息必须来自锁定输入文件或素材确认结果，例如题干、句子、答题区、选项、正确答案、题图、场景图、题干音频和选项音频。
8. 配置返修只改用户反馈项和直接依赖，禁止顺手重排、换模板、替换无关资源或新建游戏。
9. 保存统一使用 `GET 完整元信息 → 只替换 configuration → PUT /beibo/game/config/game`，`components` 保留原数组或补 `[]`。
10. `workflow_planner.py` 返回 `status=blocked` 时必须停止，向用户补问信息；AI 不得绕过阻塞继续执行。新制作任务必须先锁定题目/配置输入文件和游戏类型，不能只凭一句“生成某游戏配置”进入执行。

## 唯一执行入口

弱模型或跨端执行时，统一使用 `workflow_executor.py`。它不是第二套“快速入口”，也不自行定义流程；它只做三件事：

1. 调用 `workflow_router.py` 和 `workflow_planner.py` 获取唯一任务单。
2. 先跑 `workflow/audit_workflow.py --allow-warnings`，缺 adapter、缺脚本、缺 validator、缺模板时直接阻断。
3. 按 planner 输出的 steps 执行，并在关键动作前调用 `workflow_guard.py`。
4. 从 `workflow/execution_registry.json` 读取具体游戏的固定命令模板，禁止 AI 临场拼接生成命令。

```bash
python3 workflow/workflow_executor.py \
  --message "新建并生成一个贪吃小怪兽游戏，题目配置在 https://... 《游戏名》 表格的【SheetName】sheet 中"
```

`workflow/run_courseware_task.py` 仅作为旧命令兼容壳，内部直接转发到 `workflow_executor.py`，不得在其中新增流程逻辑。

当前 executor 已通过 `execution_registry.json` 固定以下生成适配：

- 运动PK：赛跑、游泳、赛车。
- 模板游戏：贪吃小怪兽、公路大冒险、过桥大冒险、开心游乐园、单词拼拼乐、魔法拼拼乐、阅读小帆船、阅读小火车。
- 标准组件化题：当前为确定性 passthrough，只接受已有 `game[]` 配置或 CoursewareMaker detail wrapper；不允许 AI 临场从题目描述生成标准组件化配置。

执行器按任务类型组合以下确定性步骤：

1. `workflow_router.py` / `workflow_planner.py` 锁定意图、游戏类型、Yach doc id、sheet、游戏名。
2. `scripts/fetch_yach_sheet.py` 导出在线表格，或使用 `--xlsx` 指定的本地 Excel。
3. Excel 输入使用 `scripts/resolve_sheet_resources.py`，JSON 输入使用 `scripts/resolve_input_resources.py`，并按 `workflow/game_input_schemas.json` 中每个游戏的资源字段解析当前任务引用的资源。
4. 按 `game_family/game_subtype` 从 `execution_registry.json` 选择固定生成脚本和参数。
5. 执行专项校验或生成脚本内置校验；模板类游戏统一补跑 `scripts/validate_template_game_config.py`，贪吃小怪兽仍使用更强的 `scripts/validate_monster_config.py`。
6. 新建任务用 `scripts/create_game_auto.js` 新建游戏。
7. 已有游戏导入任务用 `scripts/save_game_config_via_cdp.js` 统一保存；执行器不再要求 AI 自行拼导入命令。
8. 返修任务保存前必须执行 `scripts/validate_patch_scope.py`，需要 `--before-config` 和至少一个 `--allow-patch-prefix`。
9. `scripts/roundtrip_compare_config.js` 回读线上配置并做 canonical JSON 对比。
10. `scripts/create_preview_url.js` 生成预览链接。

如果某个游戏的适配还没有写入 `execution_registry.json`，executor 必须阻塞并要求补适配，不能让模型临场发挥。

配置返修/调整还必须额外执行范围护栏：

```bash
python3 scripts/validate_patch_scope.py \
  --before <修改前.config.json> \
  --after <修改后.config.json> \
  --allow '$.game[2]' \
  --report <patch-scope-report.json>
```

用户只反馈某一题、某个资源或某个放置区时，允许路径必须收敛到对应 JSON 前缀；出现无关关卡、无关组件或模板骨架变化时阻断保存。

## 校验职责边界

主工作流只负责调度和阻断，不把单个游戏规则写死在主流程里：

1. 根据 `game_family/game_subtype` 从 `workflow/validation_policy.json` 选择校验层。
2. 确认当前任务单里的 `config_path/input/meta/reference` 没有串到上一批任务。
3. 按顺序执行 `rules_validator -> reference_invariants -> fixture_regression -> roundtrip_compare -> preview`。
4. `rules_validator` 和 `reference_invariants` 失败时阻断保存/发布；`fixture_regression` 暂为可选回归，缺案例只记 warning。
5. 保存后回读比对和浏览器预览永远属于主工作流，不下放给单游戏脚本。

具体单个游戏负责：

- 定义输入 schema、字段映射、正确项、tag/itemList、资源类型、组件层级等规则脚本。
- 定义哪些模板资源允许固定，哪些题目字段必须来自输入。
- 定义参考配置不变量清单。
- 维护 `validation_fixtures/<game_family>/<game_subtype>/` 下的代表性案例，用于脚本回归，不作为唯一校验依据。

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

1. 先用 `workflow_router.py` 解析用户消息。
2. 用 `workflow_planner.py` 生成任务单；若 `status=blocked`，先补齐缺失信息。
3. 用 `workflow_guard.py` 在关键动作前拦截越权操作。
4. 启动 Chrome/Edge CDP `9222` 并登录 CoursewareMaker。
5. 运动PK用 `create_game_auto.js` 创建，脚本会识别模板并使用 `game_type: 2`。
6. 导入配置优先用 `save_game_config_via_cdp.js`，走浏览器 CDP 通道；`upload_game_config.py` 作为 API 直传通道。两者保存 payload 结构一致：GET 完整元信息，仅替换 `configuration` 后 PUT。
7. 导入后重新 GET 游戏详情，严格比对线上 `configuration` 与本地配置。
8. 预览确认后再发布。

## 相关脚本

- `workflow/workflow_router.py` - 确定性意图和游戏类型路由。
- `workflow/workflow_planner.py` - 根据路由生成任务单或阻塞原因。
- `workflow/workflow_guard.py` - 执行动作前检查是否违反当前环节策略。
- `scripts/create_game_auto.js` - 创建新游戏；运动PK自动使用 `game_type: 2` 和 customEditor。
- `scripts/save_game_config_via_cdp.js` - CDP 浏览器通道更新已有游戏配置；使用 `PUT + credentials: include`，保留完整元信息。
- `scripts/upload_game_config.py` - API 直传通道更新已有游戏配置；需 token/cookie，payload 结构与 CDP 脚本一致。
- `scripts/build_yundong_pk_config.py` - 生成运动PK配置。
- `scripts/validate_yundong_pk_config.py` - 校验运动PK配置结构。
- `scripts/publish_game_auto.js` - 发布游戏。
