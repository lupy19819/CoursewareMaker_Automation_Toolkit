# CoursewareMaker 自动化工具 - 迁移指南

版本：v2.1 | 更新日期：2026-04-21

---

## 需要传输的文件清单

### 【必须】文件 1：工具包主体 zip

```
D:/codexProject/CoursewareMaker_Automation_Toolkit_v2.1.zip
```
包含所有脚本、文档、模板，**新设备解压后即可使用**。

---

### 【必须】文件 2：知音楼认证配置

```
C:/Users/cyuan/.openclaw/workspace/.yach-config.json
```
包含读取知音楼文档的 appkey/appsecret，不传则无法读取题目数据源。

---

### 【必须】文件 3：OpenClaw Skills 目录

```
C:/Users/cyuan/.codex/skills/
```
包含以下专用 skill（直接复制整个目录到新设备同路径）：

| Skill 名 | 用途 |
|---------|------|
| `courseware-resource-sync` | 同步资源库 |
| `yundong-pk-config-generator` | 运动PK配置生成 |
| `monster-config-generator` | 贪吃小怪兽配置生成 |
| `k12-edu-game-designer` | 游戏设计辅助 |
| `game-config-parser-pro` | 配置解析 |
| `interactive-game-data-analyst` | 数据分析 |
| `road-adventure-config-generator` | 路途冒险配置 |
| `develop-web-game` | Web游戏开发辅助 |
| `spreadsheet` | 表格处理 |
| `h264-video-compress` | 视频压缩 |

---

### 【可选】题目数据源 xlsx（如继续做相同项目）

```
D:/迅雷下载/*.xlsx        # 各讲次题目表
```
如果新设备需要继续处理同一批题目，需要一并传输。

---

## 新设备初始化步骤

### 第一步：解压工具包

```
解压 CoursewareMaker_Automation_Toolkit_v2.1.zip
放到任意目录，建议 D:/codexProject/CoursewareMaker_Automation_Toolkit/
```

### 第二步：安装 Node.js 依赖

```bash
cd CoursewareMaker_Automation_Toolkit/
npm install
```
依赖只有一个：`puppeteer`（用于 CDP 控制浏览器）

### 第三步：安装 Python 依赖

```bash
pip install requests openpyxl pillow
```

### 第四步：放置认证配置

```bash
# 将 .yach-config.json 放到以下路径
C:/Users/<用户名>/.openclaw/workspace/.yach-config.json
```

### 第五步：复制 Skills 目录

```bash
# 将 skills/ 目录放到以下路径
C:/Users/<用户名>/.codex/skills/
```

### 第六步：启动 Edge/Chrome 调试模式

```bash
"C:/Program Files/Microsoft/Edge/Application/msedge.exe" \
  --remote-debugging-port=9222 \
  --user-data-dir=C:/tmp/edge-debug-profile \
  --no-first-run
```
**注意**：需要先在浏览器中登录 CoursewareMaker（https://coursewaremaker.speiyou.com），后续脚本才能复用登录态。

### 第七步：验证环境

```bash
bash CoursewareMaker_Automation_Toolkit/docs/check_environment.sh
```

---

## 工具包内容说明

```
CoursewareMaker_Automation_Toolkit/
├── VERSION.txt                        ← 版本说明
├── README.md                          ← 总览
├── package.json                       ← Node.js 依赖
│
├── docs/
│   ├── COURSEWAREMAKER_AUTOMATION_GUIDE.md  ← ⭐ 核心文档（完整工作流v2.1）
│   ├── QUICK_START.md                       ← 快速入门
│   ├── STANDARD_QUESTION_INTEGRATION.md     ← 标准化题型说明
│   ├── yundongpk_game_creation_workflow.md  ← 运动PK新建流程
│   ├── game_creation_workflow_analysis.md   ← 通用新建分析
│   ├── game_publish_workflow_analysis.md    ← 发布流程分析
│   ├── share_link_workflow_analysis.md      ← 分享链接流程
│   └── asset_upload_workflow_analysis.md    ← 素材上传分析
│
├── scripts/
│   ├── create_game_auto.js            ← 通用游戏新建（非运动PK）
│   ├── save_game_config_via_cdp.js    ← 导入配置并保存
│   ├── publish_game_auto.js           ← 发布游戏
│   ├── generate_share_link.js         ← 生成分享链接
│   ├── courseware_bulk_upload_assets.mjs  ← 批量素材上传
│   ├── build_yundong_pk_config.py     ← 运动PK配置生成
│   ├── build_sj6_monster_config.py    ← 贪吃小怪兽配置生成
│   ├── fetch_yach_doc_final.py        ← 读取知音楼文档
│   ├── batch_create_games.js          ← 批量新建游戏
│   ├── batch_publish_all_games.js     ← 批量发布
│   ├── batch_generate_share_links.js  ← 批量生成分享链接
│   └── monitors/                      ← CDP 监听脚本（学习新流程用）
│       ├── monitor_chrome_activity.js
│       ├── monitor_create_yundongpk.js
│       ├── monitor_game_publish.js
│       └── monitor_share_link.js
│
├── configs/
│   └── config.template.json           ← 发布参数ID对照表
│
├── templates/
│   └── detail_jsons/                  ← 游戏骨架模板
│       ├── swim_detail.json           ← 游泳皮肤骨架
│       ├── run_detail.json            ← 跑酷/赛跑皮肤骨架
│       ├── racecar_detail.json        ← 赛车皮肤骨架
│       └── monster_detail.json        ← 贪吃小怪兽骨架
│
└── standard_question_toolkit/         ← 标准化题型工具集
    ├── README_FOR_CLAUDE.md
    ├── docs/（4个文档）
    ├── data/（6个数据文件）
    ├── scripts/（5个脚本）
    └── templates/（2个模板）
```

---

## 不需要传输的文件

| 文件类型 | 原因 |
|---------|------|
| `latest_resources.json` (3MB) | 目标设备登录后重新 sync 即可 |
| `chrome_monitoring_logs/` | 历史监听日志，新设备不需要 |
| `generated_configs/` | 历史生成结果，新设备重新生成 |
| `node_modules/` | npm install 即可重建 |
| `*.build-meta.json` | 历史构建记录，仅供参考 |
| `batch_publish_results_*.json` | 历史发布结果 |

---

## 关键参数速查（无需连网查询）

### 发布参数 ID 对照

| 参数 | 值 | ID |
|------|----|----|
| 学期：春季 | spring | 1 |
| 学期：暑期 | summer | 2 |
| 学期：秋季 | autumn | 3 |
| 学科：数学 | math | 1 |
| 学科：语文 | chinese | 2 |
| 学科：英语 | english | 3 |
| 年级：小班 | | 7 |
| 年级：中班 | | 8 |
| 年级：大班 | | 9 |
| 年级：一年级 | | 1 |
| 年级：二年级 | | 2 |
| 年级：三年级 | | 3 |
| 年级：四年级 | | 4 |
| 年级：五年级 | | 5 |
| 年级：六年级 | | 6 |

### 模板 ID

| 游戏类型 | 模板 ID |
|---------|--------|
| 运动PK赛（赛跑/游泳/赛车） | `47995925-fb37-11ef-8c1b-ce918f8037e8` |
| 通用组件化游戏 | `70a3010b-0b7a-11ef-b3a3-fa7902489df6` |

---

## 快速验证（迁移后检查）

```bash
# 1. 检查浏览器调试端口
curl http://localhost:9222/json/version

# 2. 检查Node.js
node -e "const p = require('puppeteer'); console.log('puppeteer ok')"

# 3. 检查Python
python -c "import requests, openpyxl; print('python deps ok')"

# 4. 检查知音楼认证
python fetch_yach_doc_final.py HZapCIhp6dJcbZoz 2>&1 | head -5
```
