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
9. [画板组件资源替换流程](#画板组件资源替换流程)
10. [工具和脚本说明](#工具和脚本说明)
11. [API参考](#api参考)
12. [故障排除](#故障排除)
13. [附录](#附录)

---

## 概述

本指南提供 CoursewareMaker 平台游戏的**完整自动化流程**，从创建游戏到发布上线的全流程自动化方案。

### 支持的游戏类型

| 类别 | 具体类型 | 创建流程 |
|------|---------|---------|
| **运动PK类** | 赛跑、游泳、赛车 | 运动PK专用流程 |
| **贪吃小怪兽** | — | 通用流程 |
| **标准化题型** | 填空题、选择题、拖拽题 | 通用流程 |
| **画板类游戏** | 含"画板-XX"组件的游戏 | 通用流程 + 资源替换 |
| **其他组件化游戏** | — | 通用流程 |

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

**接到任务先判断游戏类型，两套流程不可混用！**

```
游戏名称/类型包含以下关键词？
    ├─ "赛跑" / "游泳" / "赛车" / "运动PK"
    │       ↓
    │   → 使用【运动PK专用流程】
    │     模板ID: 47995925-fb37-11ef-8c1b-ce918f8037e8
    │
    └─ 其他所有类型（贪吃小怪兽、标准题型、画板游戏等）
            ↓
        → 使用【通用组件化流程】
          模板ID: 70a3010b-0b7a-11ef-b3a3-fa7902489df6
```

| 游戏类型 | 模板ID | 备注 |
|---------|--------|------|
| **运动PK赛（赛跑/游泳/赛车）** | `47995925-fb37-11ef-8c1b-ce918f8037e8` | 专属模板，用错会导致游戏无法运行 |
| **通用组件化游戏** | `70a3010b-0b7a-11ef-b3a3-fa7902489df6` | 贪吃小怪兽、标准题型等 |

---

## 完整工作流总览

### ⚠️ 强制执行顺序（所有游戏类型均适用）

```
Step 1: 新建游戏（获取 game_id）
   ↓
Step 2: 上传素材资源到平台
   ↓
Step 3: 获取已上传资源的 URL 等信息（必须确认获取成功后才能继续）
   ↓
Step 4: 生成配置 JSON（使用 Step 3 获取的真实资源 URL）
   ↓
Step 5: 导入配置到游戏并保存
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
- Step 1 使用运动PK专属模板
- Step 4 使用 `build_yundong_pk_config.py`（含皮肤自动识别）

---

### Step 1: 新建运动PK游戏

```bash
node D:/codexProject/create_game_auto.js \
  "游戏名称（含赛跑/游泳/赛车关键词）" \
  "47995925-fb37-11ef-8c1b-ce918f8037e8" \
  ""
```

**运动PK专属信息**：
- 模板ID: `47995925-fb37-11ef-8c1b-ce918f8037e8`
- 组件ID: `21dcca07-c1e6-11ef-895a-4eb2c30c826b`（运动PK赛 v0.1.0）
- 编辑器入口: `customEditor?template_id=47995925-fb37-11ef-8c1b-ce918f8037e8`

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

与通用流程完全相同，参见 [通用流程 Step 5~7](#step-5-导入配置并保存)。

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

{ "game_name": "游戏名称", "template_id": "模板ID" }
```

返回：
```json
{ "code": 0, "data": { "game_id": "xxx", "id": 12345, "version": "0.0" } }
```

---

### 2. save_game_config_via_cdp.js

通过 CDP 将配置注入并保存到游戏。

```http
PUT https://sszt-gateway.speiyou.com/beibo/game/config/game
beibotoken: <TOKEN>

{
  "game_id": "xxx",
  "data": { ...配置对象，必须是对象不是字符串... }
}
```

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
