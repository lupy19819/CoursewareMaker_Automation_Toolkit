# CoursewareMaker 游戏自动化完整指南

> **版本**: 2.1  
> **更新时间**: 2026-04-21  
> **适用于**: Claude Code / Codex / OpenClaw / 其他AI助手  

---

## 📋 目录

1. [概述](#概述)
2. [环境要求](#环境要求)
3. [目录结构](#目录结构)
4. [认证配置](#认证配置)
5. [⚠️ 创建流程路由规则（必读）](#创建流程路由规则)
6. [完整工作流总览](#完整工作流总览)
7. [通用游戏完整流程](#通用游戏完整流程)
8. [运动PK游戏完整流程（赛跑/游泳/赛车）](#运动pk游戏完整流程)
9. [模板游戏专用流程（公路大冒险/贪吃小怪兽等）](#模板游戏专用流程)
10. [单词拼拼乐专用流程](#单词拼拼乐专用流程)
11. [画板组件资源替换流程](#画板组件资源替换流程)
11. [工具和脚本说明](#工具和脚本说明)
12. [API参考](#api参考)
13. [故障排除](#故障排除)
14. [附录](#附录)

---

## 概述

本指南提供 CoursewareMaker 平台游戏的**完整自动化流程**，从创建游戏到发布上线的全流程自动化方案。

### 支持的游戏类型

| 类别 | 具体类型 | 创建流程 |
|------|---------|---------|
| **运动PK类** | 赛跑、游泳、赛车 | 运动PK专用流程 |
| **单词拼拼乐** | 字母拖拽拼词游戏 | 单词拼拼乐专用流程 |
| **模板游戏类** | 贪吃小怪兽、公路大冒险（绿地/沙漠）等 | 模板游戏专用流程 |
| **通用组件化** | 自动排版算术题（填空、选择、拖拽等） | 通用组件化流程 |
| **画板类游戏** | 含"画板-XX"组件的游戏 | 通用组件化流程 + 资源替换 |

---

## 环境要求

### 必需软件

| 软件 | 版本要求 | 用途 |
|------|---------|------|
| **Node.js** | ≥ 16.0.0 | 运行JavaScript脚本 |
| **Python** | ≥ 3.8 | 配置生成脚本 |
| **Chrome 或 Edge** | 最新版 | CDP控制和Token获取 |
| **npm** | ≥ 8.0 | Node.js包管理 |
| **pip** | ≥ 21.0 | Python包管理 |

### 安装依赖

```bash
# Node.js 依赖
npm install puppeteer-core playwright

# Python 依赖
pip install pandas openpyxl requests pyyaml
```

### 启动浏览器远程调试（CDP）

**Chrome 或 Edge 均可，端口统一使用 9222。**

```bash
# Windows - Edge（推荐，系统自带）
"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" \
  --remote-debugging-port=9222 \
  --user-data-dir="C:\temp\edge-debug-profile"

# Windows - Chrome
"C:\Program Files\Google\Chrome\Application\chrome.exe" \
  --remote-debugging-port=9222 \
  --user-data-dir="C:\temp\chrome-debug-profile"
```

验证启动成功：
```bash
curl http://localhost:9222/json/version
```

---

## 目录结构

```
D:/codexProject/
├── 核心脚本
│   ├── create_game_auto.js                   # 创建游戏（通用/运动PK均适用）
│   ├── save_game_config_via_cdp.js           # 导入配置并保存
│   ├── publish_game_auto.js                   # 发布游戏
│   ├── generate_share_link.js                 # 生成预览分享链接
│   ├── batch_create_games.js                  # 批量创建游戏
│   ├── batch_create_xinyi_games.js            # 批量创建新一年级游戏
│   ├── batch_publish_all_games.js             # 批量发布
│   └── batch_generate_share_links.js          # 批量生成链接
│
├── scripts/
│   └── courseware_bulk_upload_assets.mjs      # 素材批量上传
│
├── 配置生成脚本
│   ├── build_yundong_pk_config.py             # 运动PK配置生成（含游泳/赛车/赛跑）
│   ├── build_road_adventure_config.py        # ⚠️ TODO: 公路大冒险配置生成（待开发）
│   ├── build_sj6_monster_config.py           # 贪吃小怪兽配置生成
│   └── build_sj6_monster_config.py            # 贪吃小怪兽配置生成
│
├── standard_question_toolkit/                 # 标准化题型工具集
│   ├── README_FOR_CLAUDE.md                   # ← 入口文档
│   ├── MANIFEST.md
│   ├── docs/                                  # 详细文档
│   ├── data/                                  # 模板数据
│   ├── scripts/                               # 生成脚本（填空/选择/拖拽）
│   └── templates/                             # 题型模板
│
├── 监控脚本
│   ├── monitor_chrome_activity.js             # 通用流程监控
│   ├── monitor_game_publish.js                # 发布流程监控
│   ├── monitor_share_link.js                  # 分享链接监控
│   └── monitor_create_yundongpk.js            # 运动PK创建监控
│
├── 配置文件
│   ├── latest_game_id.txt                     # 最新创建的游戏ID
│   ├── xinyi_game_id_list.json                # 新一年级游戏ID列表
│   ├── xiner_game_id_list.json                # 新二年级游戏ID列表
│   ├── latest_resources.json                  # 资源库缓存
│   └── .yach-config.json                      # 知音楼认证配置
│
└── 日志和结果
    ├── chrome_monitoring_logs/                # 监控日志
    ├── batch_publish_results_*.json           # 发布结果
    └── share_link_*.json                      # 分享链接结果
```

---

## 认证配置

### GAMEMAKER_TOKEN（beibotoken）

所有 API 调用均需此 Token，存储在浏览器 localStorage 中，脚本通过 CDP 自动获取。

**手动获取**（调试用，浏览器控制台执行）：
```javascript
console.log(localStorage.GAMEMAKER_TOKEN);
```

**API 请求方式**：
```http
GET/POST/PUT https://sszt-gateway.speiyou.com/beibo/game/config/...
Headers:
  beibotoken: <TOKEN>
  Content-Type: application/json
```

### ⚠️ API网关说明（重要）

| 域名 | 可用性 | 说明 |
|------|--------|------|
| `https://sszt-gateway.speiyou.com` | ✅ **可用** | 直接API访问，需要 `beibotoken` 请求头 |
| `https://coursewaremaker.speiyou.com` | ❌ **不可用** | 被 brizoo 安全网关拦截，返回405 |

**所有脚本只使用 `sszt-gateway.speiyou.com`。**

### 知音楼认证（题目获取）

配置文件：`D:/codexProject/.yach-config.json`

```json
{
  "apiBaseUrl": "https://yach.openclaw.cn/api",
  "accessToken": "your-yach-access-token"
}
```

---

## ⚠️ 创建流程路由规则

**接到任务先判断配置数据结构和 baseline JSON，两套流程不可混用。模板 ID 只用于平台创建参数，不作为路由标准。**

```
游戏名称/类型包含以下关键词？
    ├─ "赛跑" / "游泳" / "赛车" / "运动PK"
    │       ↓
    │   → 使用【运动PK专用流程】
    │     数据结构: custom_game
    │     基准JSON: run_detail.json / swim_detail.json / racecar_detail.json
    │
    ├─ "单词拼拼乐" / "spelling"
    │       ↓
    │   → 使用【单词拼拼乐专用流程】
    │     数据结构: game
    │     基准JSON: reference_configs/spelling_ref_new.json
    │     生成脚本: scripts/generate_spelling_config.py
    │     上传脚本: scripts/upload_spelling_config.js
    │
    ├─ "公路大冒险" / "贪吃小怪兽" / 其他有固定基准配置的模板游戏
    │       ↓
    │   → 使用【模板游戏专用流程】
    │     数据结构: game（非 custom_game）
    │     基准JSON: 对应游戏类型的基准配置（绿地/沙漠/怪兽版本等）
    │
    └─ 自动排版算术题（填空/选择/拖拽题等）
            ↓
        → 使用【通用组件化流程】
          数据结构: game
          基准JSON: 标准算术题对应具体 JSON
```

| 游戏类型 | 路由标准 | 备注 |
|---------|----------|------|
| **运动PK赛（赛跑/游泳/赛车）** | `custom_game` + `templates/detail_jsons/{run,swim,racecar}_detail.json` | 赛跑/游泳/赛车必须拆成三套皮肤 baseline |
| **单词拼拼乐** | `game` + `reference_configs/spelling_ref_new.json` | slot/space/fixed答题区 + 拖拽物品；生成脚本输出内层cfg |
| **模板游戏（公路大冒险/贪吃小怪兽等）** | `game` + 对应游戏类型基准 JSON | ⚠️必须基于正确模板基准，禁止跨模板替换 |
| **通用组件化（算术题）** | `game` + 标准题型具体 JSON | 专用于自动排版算术题（填空/选择/拖拽） |

---

## 完整工作流总览

### 机器可读工作流与校验基准

完整流程路由和生成后校验基准统一保存在：

```text
standard_question_toolkit/data/courseware_workflow_rules.json
```

该文件是自动化流程的最高优先级工作流文件，包含：

- `workflow.route_first`：先按具体 baseline JSON 和根数据结构判断运动 PK / 通用组件化，避免混用结构。
- `workflow.stages`：素材、生成、校验、创建、保存、分享/发布的顺序。
- `validation_baselines`：正确 `expected_config`，覆盖运动 PK 的赛跑/游泳/赛车三套皮肤，以及标准题型的选择题、填空/计算题、拖拽题 × 紫/黄/蓝三套皮肤。
- `template_baseline_paths`：运动 PK、贪吃小怪兽、标准题型的原始基准 JSON 路径。

生成配置 JSON 后必须先执行：

```bash
node scripts/validate_config.js --file <config.json>
```

校验脚本会读取 `courseware_workflow_rules.json`。运动 PK 按 `custom_game` 结构和 run/swim/racecar baseline JSON 校验；组件化标准题按 `game` 结构逐关识别题型和皮肤，并校验背景、组件互斥关系、题干 label、输入框、键盘、选择按钮、拖拽物和放置框资源。

### ⚠️ 强制执行顺序（所有游戏类型均适用）

```
【准备】公路大冒险：询问用户使用哪种背景
   ├─ 🌿 绿地 → 选用绿地基准配置（如春15）
   └─ 🏜 沙漠 → 选用沙漠基准配置（如2024国际demo课level1层）
   ↓
Step 1: 新建游戏（获取 game_id）
   ├─ 运动PK：template_id = 47995925-fb37-11ef-8c1b-ce918f8037e8
   │           game_type = 2，编辑器入口 customEditor?game_id=...
   └─ 模板游戏 / 通用组件化：template_id = 70a3010b-0b7a-11ef-b3a3-fa7902489df6
   ↓
Step 2: 上传素材资源到平台
   ↓
Step 3: 获取已上传资源的 URL 等信息（必须确认获取成功后才能继续）
   ↓
Step 4: 生成配置 JSON（使用 Step 3 获取的真实资源 URL）
   ├─ 运动PK → build_yundong_pk_config.py
   ├─ 模板游戏（公路大冒险）→ build_road_adventure_config.py（⚠️ TODO: 脚本待开发，当前手动替换）
   ├─ 模板游戏（贪吃小怪兽）→ build_sj6_monster_config.py
   └─ 通用组件化（算术题）→ 标准题型脚本
   ↓
   【Step 4 校验】（生成后必检，失败则回 Step 4 修正）
   ├─ JSON 可解析
   ├─ 每关结构完整（选项数量/唯一正确项/音效字段不为空）
   ├─ 模板游戏额外：动效映射正确、纯文字题不换行
   └─ node scripts/validate_config.js --file <config.json>
   ↓
Step 5: 导入配置到游戏并保存
   ├─ 更新已有游戏统一使用 PUT /beibo/game/config/game
   ├─ fetch 必须带 credentials: "include"
   └─ configuration 必须是对象，不是字符串；写回前排除 components 大字段
   ↓
Step 6: 生成预览分享链接（测试确认）
   ↓
Step 7: 发布游戏
```

**为什么是这个顺序？**
- 必须先新建游戏才有 game_id，后续操作都依赖它
- 必须先上传资源并**确认获取到资源 URL** 后才能生成配置，否则配置中会出现无效的资源引用
- 配置中所有图片/音频的 URL 必须是平台已存在的真实 URL

---

## 通用游戏完整流程

适用于：贪吃小怪兽、标准化题型（填空/选择/拖拽）、画板游戏、其他组件化游戏。

---

### Step 1: 新建游戏

```bash
node D:/codexProject/create_game_auto.js \
  "游戏名称" \
  "70a3010b-0b7a-11ef-b3a3-fa7902489df6" \
  ""
```

**参数**：
1. 游戏名称（必填）
2. 模板ID（通用类用 `70a3010b-0b7a-11ef-b3a3-fa7902489df6`）
3. 配置路径（传空字符串创建空游戏）

**输出**：
- 返回并打印 `game_id`
- 自动保存到 `latest_game_id.txt`

```bash
# 读取 game_id
GAME_ID=$(cat D:/codexProject/latest_game_id.txt)
```

**批量创建**：
```bash
node D:/codexProject/batch_create_games.js
```

---

### Step 2: 上传素材资源

```bash
# 上传图片（默认PNG）
node D:/codexProject/scripts/courseware_bulk_upload_assets.mjs "D:\素材文件夹"

# 上传音频
node D:/codexProject/scripts/courseware_bulk_upload_assets.mjs "D:\音频文件夹" \
  --category audio \
  --ext .mp3

# 完整参数说明
node D:/codexProject/scripts/courseware_bulk_upload_assets.mjs <文件夹路径> \
  [--category image]    # 素材类别: image/audio/video/spine
  [--ext .png]          # 文件扩展名过滤
  [--topic-id 1]        # 主题ID: 1=通用
  [--tag-id 7]          # 标签ID: 7=贴画, 8=音效
  [--concurrency 5]     # 并发上传数量
```

**内部工作原理**：
1. 通过 CDP 从浏览器读取 Token
2. 获取腾讯云 COS 临时凭证
3. 并发上传文件到 COS
4. 调用平台 API 注册资源，返回资源 URL

---

### Step 3: 获取资源信息（确认 URL）

上传完成后，必须确认资源已注册并获取到真实 URL，才能进入下一步。

**方式一：通过上传脚本输出**  
上传脚本执行成功后会直接输出每个资源的 URL，记录备用。

**方式二：通过 API 查询**（如需补充信息）
```bash
node D:/codexProject/sync_courseware_resources.py
# 输出: latest_resources.json（包含所有资源的id/name/url）
```

或直接调用查询 API：
```http
POST https://sszt-gateway.speiyou.com/beibo/game/config/resource/list
beibotoken: <TOKEN>

{
  "page": 1,
  "pageSize": 50,
  "name": "资源名称关键词",
  "type": "image"
}
```

返回格式：
```json
{
  "data": {
    "list": [
      {
        "id": "资源ID",
        "name": "资源名称",
        "url": "https://courseware-maker-xxx.cos.../xxx.png",
        "type": "image"
      }
    ]
  }
}
```

**⚠️ 确认资源 URL 都已获取到后，才能进行 Step 4。**

---

### Step 4: 生成配置 JSON

使用 Step 3 获取的真实资源 URL 生成配置。

#### 4.1 贪吃小怪兽

```bash
python D:/codexProject/build_sj6_monster_config.py \
  D:/codexProject/zhiyinlou_monster_test_latest.xlsx \
  --output-dir D:/codexProject/generated_configs/monster_games
```

#### 4.2 标准化题型（填空/选择/拖拽）

参考 `D:/codexProject/standard_question_toolkit/README_FOR_CLAUDE.md` 获取完整用法。

支持题型：
- 填空题（竖式、算式）
- 选择题（单选、多选）
- 拖拽题

生成脚本位于 `standard_question_toolkit/scripts/`。

---

### Step 5: 导入配置并保存

```bash
node D:/codexProject/save_game_config_via_cdp.js \
  "game_id" \
  "D:/codexProject/config.json"
```

**⚠️ 关键**：配置必须是合法 JSON 对象，脚本自动 `JSON.parse()` 后传递。绝不能传字符串（双重编码会导致游戏无法打开）。

验证保存成功：响应中 `code: 0` 且 `msg: "success"`。

---

### Step 6: 生成预览分享链接

```bash
# 单个游戏
node D:/codexProject/generate_share_link.js "game_id"

# 批量
node D:/codexProject/batch_generate_share_links.js game_id_list.json
```

**输出**：
```
https://coursewaremaker.speiyou.com/#/share-preview?pw=xxx
有效期：7天
```

在浏览器中打开链接确认游戏正常后，再进行 Step 7。

---

### Step 7: 发布游戏

```bash
node D:/codexProject/publish_game_auto.js \
  "game_id" \
  <year> \
  "<term_id>" \
  "<grade>" \
  "<subject_id>" \
  "<cnum_id>"
```

示例（2026年/暑期/一年级/数学/第6讲）：
```bash
node D:/codexProject/publish_game_auto.js "game_id" 2026 "2" "1" "1" "6"
```

参数 ID 详见 [附录 A：发布参数ID对照表](#a-发布参数id对照表)。

**批量发布**：
```bash
node D:/codexProject/batch_publish_all_games.js
```

---

## 运动PK游戏完整流程

适用于：赛跑、游泳、赛车。

**与通用流程的区别**：
- 使用 `custom_game` 数据结构，不使用组件化 `game` 结构。
- `build_yundong_pk_config.py` 按赛跑/游泳/赛车拆成三套皮肤 baseline，读取 `courseware_workflow_rules.json > yundong_pk_skins`。
- 新建时必须使用 `game_type: 2`，并打开 `customEditor`；导入保存使用 `PUT + credentials: include` 更新原 `game_id`。

---

### Step 1: 新建运动PK游戏

```bash
node D:/codexProject/create_game_auto.js \
  "游戏名称（含赛跑/游泳/赛车关键词）" \
  "47995925-fb37-11ef-8c1b-ce918f8037e8" \
  ""
```

**运动PK专属信息**：
- 平台创建参数 template_id: `47995925-fb37-11ef-8c1b-ce918f8037e8`（仅用于创建接口，不作为玩法路由或校验标准）
- `create_game_auto.js` 会识别该模板并使用 `game_type: 2`
- 组件ID: `21dcca07-c1e6-11ef-895a-4eb2c30c826b`（运动PK赛 v0.1.0）
- 创建后编辑器入口: `customEditor?game_id=<game_id>`
- 配置路径可传空字符串，先创建空壳 `{}`，后续用 `save_game_config_via_cdp.js` 导入完整配置

---

### Step 2: 上传素材资源

```bash
# 上传图片素材
node D:/codexProject/scripts/courseware_bulk_upload_assets.mjs "D:\游泳图片素材"

# 上传音频素材
node D:/codexProject/scripts/courseware_bulk_upload_assets.mjs "D:\游泳音频" \
  --category audio \
  --ext .mp3
```

---

### Step 3: 获取资源信息（确认 URL）

与通用流程完全相同，参见 [通用流程 Step 3](#step-3-获取资源信息确认-url)。

**⚠️ 必须确认所有图片和音频的 URL 都已获取后才能继续。**

---

### Step 4: 生成运动PK配置

```bash
python D:/codexProject/build_yundong_pk_config.py \
  "SheetName" \
  "目标游戏的detail.json" \
  "题目表.xlsx"
```

**皮肤自动识别规则**（根据 SheetName 或题目表 Sheet 名）：

| Sheet名包含 | 皮肤 | 模板文件 |
|------------|------|---------|
| `游泳` | swim（游泳） | `1034b0ba-...detail.json` |
| `赛车` | racecar（赛车） | `赛车玩法_测试配置_单行版.json` |
| 其他 | run（跑酷赛跑） | `8fbe9ab9-...detail.json` |

**Excel格式要求**（知音楼导出格式）：
- 题干、答案、选项1~3：必填
- 题干音频、选项音频、题干图片：可选

**输出**：
- `<SheetName>.config.json`：导入用配置
- `<SheetName>.build-meta.json`：构建元数据

---

### Step 5~7: 导入配置、预览、发布

导入命令：

```bash
node D:/codexProject/save_game_config_via_cdp.js "$GAME_ID" "<SheetName>.config.json"
```

当前已验证的导入方式：

- 先 `GET /beibo/game/config/game?game_id=<game_id>` 获取元数据。
- 写回时排除 `components` 大字段。
- 使用 `PUT /beibo/game/config/game` 更新原 `game_id`。
- 所有 fetch 都必须带 `credentials: "include"`，否则可能 500。
- `configuration` 必须是 JSON 对象，不得双重编码为字符串。

导入后必须重新 GET 游戏详情并比对 `configuration`。2026-05-08 已用 `测试运动PK新建` 跑通：新建 `game_type=2`，导入 10 关赛跑配置后线上与本地配置 `exact_equal=true`。

预览和发布参见 [通用流程 Step 6~7](#step-6-生成预览分享链接)。

---


## 模板游戏专用流程

适用于：**贪吃小怪兽、公路大冒险**（绿地/沙漠）等有固定基准配置的模板型游戏。

**与通用组件化流程的区别**：
- 通用组件化专用于自动排版算术题；模板游戏是基于已有游戏配置做资源替换和内容更新。
- 数据结构均为 `game[]`，但**必须基于对应游戏类型和背景的基准配置**，禁止跨模板替换。
- 不同模板游戏有各自的关键字段规则（见下方各子类说明）。

---

### 子类：公路大冒险

**特有规则**：
- 选项组件为 `AloneClickChoice`，按三态规则（待机/正确/错误）替换图片，并更新 `anwserRadio`。
- 正确反馈动效（小鹿开车）的 `animation` 值由正确选项 y 坐标决定，**名称与位置直觉相反，必须从基准配置实际验证**。
- 支持音频题（题干为语音）与纯文字题混排。
- 绿地用绿地基准，沙漠用沙漠基准，禁止跨背景替换。

### 子类：贪吃小怪兽

**特有规则**：
- 基于贪吃小怪兽专属基准配置，参见 `build_sj6_monster_config.py`。
- 具体字段规则参见 `monster-config-generator` skill 文档。

---

---

### Step 1: 新建公路大冒险游戏

```bash
node scripts/create_game_auto.js "游戏名称" "70a3010b-0b7a-11ef-b3a3-fa7902489df6" ""
```

**公路大冒险专属信息**：
- 平台创建参数 template_id: `70a3010b-0b7a-11ef-b3a3-fa7902489df6`（与通用组件化相同，仅用于创建接口）
- 模板选择规则（**Step 1 前必问用户想用哪种背景**）：

| 背景类型 | 背景图特征 | 背景图哈希（COS） | 基准配置示例 |
|---|---|---|---|
| 🌿 绿地/普通公路 | 绿色草地公路场景 | `d75b02701cca4274a4cca1363cfc9195.png` | 国际Level1公路大冒险春15 |
| 🏜 沙漠 | 黄色沙漠公路场景 | `4104069a6e8e72df65fef474c6ec9e70.png` / `91795a5e6c660f116006772884559772.png` | 2024国际demo课公路大冒险level1层（任意版本） |

> ⚠️ **禁止跨背景替换**：绿地基准只能生成绿地配置，沙漠基准只能生成沙漠配置。背景图属于关卡底层资源，替换配置时不得修改。

- 创建后记录 `game_id`，后续替换配置时使用。

---

### Step 2: 上传素材资源

```bash
# 上传图片（选项三态图）
node scripts/courseware_bulk_upload_assets.mjs "./图片目录"

# 上传音频（音频题干）
node scripts/courseware_bulk_upload_assets.mjs "./音频目录" --category audio --ext .mp3
```

**资源命名规范**（图片三态）：

```
{前缀}{题号}{选项字母}{状态}
示例：26春L1公路15p1a待机 / 26春L1公路15p1b正确 / 26春L1公路15p1c错误
```

| 状态 | 含义 |
|---|---|
| `待机` | 默认/未选中 |
| `正确` | 正确选项在全局正确时展示 |
| `错误` | 错误选项在全局错误时展示 |

---

### Step 3: 获取资源信息（确认 URL）

与通用流程完全相同，参见 [通用流程 Step 3](#step-3-获取资源信息确认-url)。

**⚠️ 必须确认所有图片（三态×所有选项）和音频的 URL 都已获取后才能继续。**

---

### Step 4: 生成公路大冒险配置

**4.1 从基准配置验证小鹿动效映射（必做，勿跳过）**

```python
import json
with open('基准配置.json') as f:
    cfg = json.load(f)
for i, level in enumerate(cfg['game']):
    for comp in level.get('components', []):
        cdata = comp.get('component_data', {})
        tools = cdata.get('components', {}).get('tools', {})
        if '小鹿' in cdata.get('name', ''):
            for st in cdata.get('states', []):
                if st.get('label') == '全局正确':
                    print(f"关{i+1} 小鹿动效:", st['source']['MSpine']['animation'])
        if 'AloneClickChoice' in tools:
            if tools['AloneClickChoice']['anwserConfig'].get('anwserRadio') == 1:
                y = cdata.get('states', [{}])[0].get('transform', {}).get('y', 0)
                print(f"关{i+1} 正确项 y={y}")
```

**⚠️ 动效映射规则**（从春15实际验证得出，名称与位置直觉相反）：

| 正确选项 y 坐标 | 位置 | animation 值 |
|---|---|---|
| y < -200 | 顶部（a） | **`xia`** |
| -200 ≤ y ≤ 100 | 中部（b） | `zhong` |
| y > 100 | 底部（c） | **`shang`** |

**4.2 选项图片三态配置规则**

每个 `AloneClickChoice` 的 `states` 数组（共3项）：

| index | label | 正确选项图 | 错误选项图 |
|---|---|---|---|
| 0 | 默认 | `{前缀}待机` | `{前缀}待机` |
| 1 | 全局正确 | `{前缀}正确` | `{前缀}待机`（保持不变） |
| 2 | 全局错误 | `{前缀}待机`（保持不变） | `{前缀}错误` |

**4.3 正确项标记**

`AloneClickChoice.anwserConfig.anwserRadio`：正确选项 = `1`，错误选项 = `2`

**4.4 题干配置**

- **音频题**：在 `语音按钮` 组件的 `播放语音` state 中设置 `MAudio.value` 为音频 URL。
- **纯文字题**：在 `节点` 组件的 `默认` state 中设置 `MLabel.value` 为题干文本；字号需估算容器宽度确保单行不换行。

> 📝 **TODO**: 开发 `scripts/build_road_adventure_config.py`，输入：题目关系表 + 资源导出表；输出：可直接导入的配置 JSON，自动完成三态图替换、anwserRadio 标记、小鹿动效映射、题干配置。参考 `build_sj6_monster_config.py` 实现模式。

---

### Step 5: 导入配置并保存

```python
import json, urllib.request
TOKEN = "<beibotoken>"
GAME_ID = "<game_id>"
with open('road_adventure_config.json') as f:
    config = json.load(f)
data = {"game_id": GAME_ID, "game_name": "游戏名称", "configuration": config}
req = urllib.request.Request(
    'https://sszt-gateway.speiyou.com/beibo/game/config/game',
    data=json.dumps(data, ensure_ascii=False).encode('utf-8'),
    headers={'beibotoken': TOKEN, 'Content-Type': 'application/json'},
    method='PUT'
)
with urllib.request.urlopen(req) as r:
    print(json.loads(r.read()))
```

**校验清单（导入前必检）**：
- [ ] JSON 可解析
- [ ] 每关恰好 3 个 AloneClickChoice
- [ ] 每关恰好 1 个 `anwserRadio=1`
- [ ] 小鹿动效 animation 已通过基准配置验证
- [ ] 所有选项 correct/wrong 反馈音效字段不为空
- [ ] 纯文字题题干单行不换行

---

### Step 6~7: 发布、生成预览链接

与通用流程完全相同，参见 [通用流程 Step 6~7](#step-6-生成预览分享链接)。

**触发构建**（保存配置后必须执行）：

```python
req = urllib.request.Request(
    'https://sszt-gateway.speiyou.com/beibo/game/config/build_queue',
    data=json.dumps({"game_id": GAME_ID}).encode(),
    headers={'beibotoken': TOKEN, 'Content-Type': 'application/json'},
    method='POST'
)
with urllib.request.urlopen(req) as r:
    print(json.loads(r.read()))
```

---

## 单词拼拼乐专用流程

### 游戏简介

单词拼拼乐是一类字母拖拽拼词游戏，每关包含一个目标词组（如 "make a snowman"），玩家将字母块拖入答题区完成拼写。

### 答题区组件类型

| 类型 | 说明 |
|------|------|
| `slot` | 可放置字母的拖拽放置区，zIndex 从 19 开始递减 |
| `space` | 英语空格（默认隐藏，active.switch=true, value=hide） |
| `fixed` | 固定字母（不可拖拽，背景图+九宫格） |
| `drag_item` | 可拖拽的字母块，数量 = slot 数量 |
| `text_fin` | 答题区背景+词组文本，宽度按字数自适应，背景图+九宫格 |

### 九宫格参数（固定文本 & text_fin 通用）

```json
{
  "enable": true,
  "top": 30.7522,
  "right": 22.8713,
  "bottom": 33.0302,
  "left": 32.0198
}
```

### 完整流程

```
Step 1: 准备题目数据
  - 每关需要：text（词组）、slots（可拖拽字母列表）、items（答题区元素顺序）
  - items 元素类型：{"type": "slot"} / {"type": "space"} / {"type": "fixed", "content": "a"}

Step 2: 上传素材（图片 + 音频）并确认 CDN URL

Step 3: 生成配置
  cd CoursewareMaker_Automation_Toolkit
  python3 scripts/generate_spelling_config.py

Step 4: 校验（参考 reference_configs/spelling_ref_new.json）
  - 检查每关 slot zIndex 从 19 递减
  - 检查 text_fin / fixed_text 的 MSprite.nineGrid.enable == true
  - 无 text_head / text_tail 组件
  - space 组件 active.switch=true, value=hide
  - drag_item 数量 == slot 数量

Step 5: 上传
  node scripts/upload_spelling_config.js
  # 验证 double_encoded=false
```

### 关键常量

```python
IMG_FIXED_TEXT_BG = "https://courseware-maker-1252161091.cos.ap-beijing.myqcloud.com/assets/image/345733/2026-04-28/70428cf856e3acb0aebcd929d60c4c6b.png"
ITEM_X_OFFSET = -150   # 拖拽物品整体左移
SLOT_W = 237           # 放置区宽度
SLOT_H = 161           # 放置区高度
```

---

## 画板组件资源替换流程

用于替换游戏中"画板-XX"组件里的图片/音频（不重新创建游戏，在原游戏基础上替换资源）。

```
Step 1: 分析原游戏配置（找出所有画板-XX组件的资源引用）
   ↓
Step 2: 上传新素材资源
   ↓
Step 3: 获取新资源 URL（确认获取成功）
   ↓
Step 4: 生成替换后的新配置
   ↓
Step 5: 导入新配置到原游戏并保存
```

### Step 1: 分析原游戏配置

从游戏编辑器导出或通过 API 获取当前配置，找出画板组件的资源 URL 结构：

**画板组件典型结构**：
```json
{
  "componentName": "画板-01",
  "type": "canvas",
  "props": {
    "backgroundImage": "https://...原背景图URL",
    "elements": [
      { "type": "image", "src": "https://...原图片URL" },
      { "type": "audio", "src": "https://...原音频URL" }
    ]
  }
}
```

### Step 2~3: 上传新素材并获取 URL

与通用流程 Step 2~3 完全相同。

### Step 4: 生成替换配置

将原配置中所有画板组件的 URL 替换为新资源 URL，保持其他结构不变。

### Step 5: 导入并保存

```bash
node D:/codexProject/save_game_config_via_cdp.js \
  "原游戏game_id" \
  "新配置.json"
```

---

## 工具和脚本说明

### 1. create_game_auto.js

创建新游戏，获取 game_id。

```http
POST https://sszt-gateway.speiyou.com/beibo/game/config/game
beibotoken: <TOKEN>

{
  "user": "用户名",
  "game_type": 1 或 2,
  "game_name": "游戏名称",
  "template_id": "模板ID",
  "configuration": { ... }
}
```

脚本规则：

- 普通组件化游戏：`game_type=1`，打开 `#/editor?game_id=...`
- 运动PK模板 `47995925-fb37-11ef-8c1b-ce918f8037e8`：`game_type=2`，打开 `#/customEditor?game_id=...`
- 第三个参数可传空字符串，创建空壳后再导入配置

---

### 2. save_game_config_via_cdp.js

通过 CDP 将配置注入并保存到游戏。

```http
PUT https://sszt-gateway.speiyou.com/beibo/game/config/game
beibotoken: <TOKEN>
credentials: include

{
  "...": "GET /game 返回的元数据（排除 components 大字段）",
  "configuration": { ...配置对象，必须是对象不是字符串... }
}
```

注意：`POST /game` 在部分已有 `game_id` 上会被平台当成新建/另存版本，可能返回“游戏名字重复”。更新已有游戏配置统一使用 `PUT + credentials: include`。

---

### 3. publish_game_auto.js

发布游戏，4步完整流程：

| 步骤 | API | 方法 |
|------|-----|------|
| 1 | `/beibo/game/config/gamePublish` | PUT |
| 2 | `/beibo/game/config/gameDesc` | PUT |
| 3 | `/beibo/game/config/build_queue` | POST |
| 4 | `/beibo/game/config/unlock` | **POST**（⚠️必须是POST，PUT会404） |

---

### 4. generate_share_link.js

生成7天有效的预览链接。

```http
POST https://sszt-gateway.speiyou.com/beibo/game/config/createPreviewUrl

{
  "game_id": "xxx",
  "base_preview_url": "https://coursewaremaker.speiyou.com/#/share-preview"
}
```

---

### 5. courseware_bulk_upload_assets.mjs

批量上传素材，内部3步：
1. CDP 获取 Token
2. 获取腾讯云 COS 临时凭证
3. 并发上传 + 调用平台 API 注册资源

---

### 6. build_yundong_pk_config.py

从 Excel 生成运动PK配置，支持游泳/赛车/赛跑三种皮肤，根据 Sheet 名自动识别。

---

### 8. generate_spelling_config.py

生成单词拼拼乐配置。输入题目数据（text/slots/items），输出内层 cfg（common/game/additional/components 结构）。

**用法：**
```bash
python3 scripts/generate_spelling_config.py
# 输出：output/spelling_test_config.json
```

**题目数据格式（在脚本顶部 QUESTIONS 列表修改）：**
```python
QUESTIONS = [
  {
    "text": "make a snowman",
    "slots": ["m","a","k","e","n"],          # 可拖拽字母
    "items": [                                 # 答题区元素顺序（左→右）
      {"type":"slot"},{"type":"slot"},{"type":"slot"},{"type":"slot"},
      {"type":"space"},{"type":"fixed","content":"a"},{"type":"space"},
      {"type":"slot"},{"type":"slot"},{"type":"slot"},{"type":"slot"},{"type":"slot"},
    ]
  },
  ...
]
```

---

### 9. upload_spelling_config.js

通过 CDP 将单词拼拼乐配置上传到编辑器。自动扫描 9222/9223 端口，上传后验证 `double_encoded=false`。

```bash
node scripts/upload_spelling_config.js
# 默认读取 output/spelling_test_config.json
# 需要先启动 Chrome 远程调试（--remote-debugging-port=9222）并打开对应游戏
```

---

### 10. fetch_spelling_configs.js

从编辑器抓取已保存的单词拼拼乐配置（用于备份或对比校验）。

```bash
node scripts/fetch_spelling_configs.js
```

---

### 7. 监控脚本使用方式

在学习新流程时，启动对应监控脚本记录操作：

```bash
# 通用操作监控
nohup node D:/codexProject/monitor_chrome_activity.js > monitor_stdout.log 2>&1 &

# 专项：发布流程监控
nohup node D:/codexProject/monitor_game_publish.js > monitor_publish.log 2>&1 &

# 专项：运动PK创建监控
nohup node D:/codexProject/monitor_create_yundongpk.js > monitor_yundong.log 2>&1 &
```

监控日志：`D:/codexProject/chrome_monitoring_logs/`

---

## API参考

### Base URL

```
https://sszt-gateway.speiyou.com
```

### 打开游戏的两种模式

在 CoursewareMaker 编辑器中打开一个组件化游戏时，有两种模式：

| 模式 | 说明 | 可写入？ |
|------|------|---------|
| **引用** | 只读方式打开，无法修改内容 | ❌ 不可写入 |
| **修改** | 编辑原游戏，直接修改原始配置 | ✅ 可写入 |

**⚠️ 自动化脚本注意**：`save_game_config_via_cdp.js` 写入配置前，必须确保游戏是以**修改**模式打开的。如果以引用模式打开，写入操作会静默失效或报错。

#### 网络层识别特征（通过 CDP 可检测）

| 特征 | 引用（只读） | 修改（可写） |
|------|------------|------------|
| 编辑器 URL 参数 | `?openType=1` | 无 `openType` 参数 |
| `POST /beibo/game/config/lock` | ❌ 不出现 | ✅ 出现 |
| `POST /beibo/game/config/unlock` | ✅ 出现（解除上次锁） | ❌ 不出现 |
| `PUT /beibo/game/config/game` | ❌ 不出现 | ✅ 出现（写入配置） |

**检测方法**：监听编辑器加载时的 URL，若包含 `openType=1` 则为引用模式，脚本应中止并提示用户重新以修改模式打开。

---

### 完整 API 一览

| API端点 | 方法 | 说明 |
|---------|------|------|
| `/beibo/game/config/game` | POST | 创建游戏 |
| `/beibo/game/config/game` | PUT | 保存游戏配置 |
| `/beibo/game/config/lock` | POST | 锁定游戏（编辑时） |
| `/beibo/game/config/unlock` | **POST** | 解锁游戏（⚠️必须POST，不是PUT） |
| `/beibo/game/config/gamePublish` | PUT | 设置发布信息（年份/学期/年级/学科/讲次） |
| `/beibo/game/config/gameDesc` | PUT | 更新游戏描述 |
| `/beibo/game/config/build_queue` | POST | 加入构建队列（真正触发发布） |
| `/beibo/game/config/searchPreviewUrl` | POST | 查询已有分享链接 |
| `/beibo/game/config/createPreviewUrl` | POST | 创建新分享链接 |
| `/beibo/game/config/resource/list` | POST | 查询资源列表（获取资源URL） |
| `/beibo/game/config/resource/upload` | POST | 注册资源（上传脚本内部使用） |

---

## 故障排除

### CDP连接失败

```
Error: connect ECONNREFUSED 127.0.0.1:9222
```

确认浏览器已用 `--remote-debugging-port=9222` 启动，验证：
```bash
curl http://localhost:9222/json/version
```

---

### API返回405或HTML登录页

使用了 `coursewaremaker.speiyou.com` 而非 `sszt-gateway.speiyou.com`（brizoo拦截）。  
改用 `sszt-gateway.speiyou.com` + `beibotoken` 请求头。

---

### 配置双重编码（游戏无法打开）

传配置时传了字符串而不是对象：
```javascript
// ❌ 错误
data: JSON.stringify(config)

// ✅ 正确
data: config  // 已经是对象
```

---

### unlock 返回404

使用了 PUT 方法。unlock 必须用 **POST**，Body 为 `{ id, version, type }`。

---

### 游泳/赛车皮肤未正确识别

Excel 的 Sheet 名没有包含"游泳"或"赛车"关键词。修改 Sheet 名后重新运行。

---

### 资源 URL 为空或无效

跳过了 Step 3 资源确认。上传后必须通过 API 或脚本输出确认获取到真实 URL，才能进行配置生成。

---

## 附录

### A. 发布参数ID对照表

**⚠️ 以下为实际测试验证的正确值。**

#### 学期 (term_id)
| 值 | 说明 |
|----|------|
| `"1"` | 春季 |
| `"2"` | 暑期 |
| `"3"` | 秋季 |
| `"4"` | 寒假 |

#### 年级 (grade)
| 值 | 说明 |
|----|------|
| `"1"` | 一年级 |
| `"2"` | 二年级 |
| `"3"` | 三年级 |
| `"4"` | 四年级 |
| `"5"` | 五年级 |
| `"6"` | 六年级 |
| `"7"` | 小班（幼儿园） |

#### 学科 (subject_id)
| 值 | 说明 | 验证状态 |
|----|------|---------|
| `"1"` | 数学 | ✅ 已验证 |
| `"2"` | 语文 | 待验证 |
| `"3"` | 英语 | ✅ 已验证 |

#### 讲次 (cnum_id)
数字字符串，`"1"` = 第1讲，`"6"` = 第6讲，以此类推。通用课次也直接传对应数字。

---

### B. 完整流程速查卡

#### 通用游戏（7步）

```bash
# Step 1: 新建游戏
node D:/codexProject/create_game_auto.js "游戏名称" "70a3010b-0b7a-11ef-b3a3-fa7902489df6" ""
GAME_ID=$(cat D:/codexProject/latest_game_id.txt)

# Step 2: 上传素材
node D:/codexProject/scripts/courseware_bulk_upload_assets.mjs "D:\素材文件夹"

# Step 3: 确认获取资源URL（检查脚本输出或查询API）
python D:/codexProject/sync_courseware_resources.py

# Step 4: 生成配置
python D:/codexProject/build_sj6_monster_config.py 题目表.xlsx

# Step 5: 导入配置
node D:/codexProject/save_game_config_via_cdp.js "$GAME_ID" config.json

# Step 6: 生成预览链接
node D:/codexProject/generate_share_link.js "$GAME_ID"

# Step 7: 发布
node D:/codexProject/publish_game_auto.js "$GAME_ID" 2026 "2" "1" "1" "6"
```

#### 运动PK游戏-游泳（7步）

```bash
# Step 1: 新建游戏（运动PK专属模板）
# create_game_auto.js 会自动使用 game_type=2，并打开 customEditor
node D:/codexProject/create_game_auto.js "国际小班游泳暑J6" "47995925-fb37-11ef-8c1b-ce918f8037e8" ""
GAME_ID=$(cat D:/codexProject/latest_game_id.txt)

# Step 2: 上传素材
node D:/codexProject/scripts/courseware_bulk_upload_assets.mjs "D:\游泳图片"
node D:/codexProject/scripts/courseware_bulk_upload_assets.mjs "D:\游泳音频" --category audio --ext .mp3

# Step 3: 确认获取资源URL
python D:/codexProject/sync_courseware_resources.py

# Step 4: 生成配置（Sheet名含"游泳"自动识别swim皮肤）
python D:/codexProject/build_yundong_pk_config.py "国际小班游泳暑J6" "swim_detail.json" "题目表.xlsx"

# Step 5: 导入配置
# save_game_config_via_cdp.js 使用 PUT + credentials: include 更新原 game_id
node D:/codexProject/save_game_config_via_cdp.js "$GAME_ID" "国际小班游泳暑J6.config.json"

# Step 6: 生成预览链接
node D:/codexProject/generate_share_link.js "$GAME_ID"

# Step 7: 发布（英语/小班/暑期/第6讲）
node D:/codexProject/publish_game_auto.js "$GAME_ID" 2026 "2" "7" "3" "6"
```

---

### C. 环境检查

```bash
bash D:/codexProject/docs/check_environment.sh
```

---

**版本历史**：
- v1.0 (2026-04-16): 初始版本，7步通用流程
- v1.1 (2026-04-16): 新增素材批量上传，集成标准化题型工具集
- v2.0 (2026-04-20): 新增运动PK专用创建流程；修正发布参数ID（英语=3，小班=7）；修正unlock为POST；新增brizoo网关说明；新增画板资源替换流程
- v2.1 (2026-04-21): **修正工作流顺序**：改为"新建游戏→上传资源→获取资源信息→生成配置→导入→预览→发布"，整合所有流程，强制明确Step 3资源确认节点
- v2.2 (2026-04-27): 新增**模板游戏专用流程**章节（含公路大冒险子类）；修正小鹿动效映射（a→xia / b→zhong / c→shang，与位置直觉相反）；明确通用组件化专用于算术题；更新路由规则、游戏类型表和目录

> 📝 待办：后续可在 `save_game_config_via_cdp.js` 加前置检查，检测 Tab URL 是否含 `openType=1`，有则中止并提示用户以修改模式重新打开。
