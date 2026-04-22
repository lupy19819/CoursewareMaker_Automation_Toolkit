# CoursewareMaker 游戏自动化工具集

> **完整的CoursewareMaker游戏创建、配置、发布自动化解决方案**

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Node](https://img.shields.io/badge/node-%3E%3D16.0-brightgreen.svg)](https://nodejs.org/)
[![Python](https://img.shields.io/badge/python-%3E%3D3.8-blue.svg)](https://www.python.org/)

---

## 📖 概述

本工具集提供了从题目到上线的**完整自动化流程**，支持批量创建、配置、发布CoursewareMaker平台的组件化游戏。

### 核心功能

- ✅ **自动创建游戏** - API创建空游戏并获取game_id
- ✅ **配置生成** - 从Excel题目表生成游戏配置JSON
- ✅ **配置注入** - 通过CDP将配置注入到游戏编辑器
- ✅ **分享链接** - 生成7天有效期的预览链接
- ✅ **游戏发布** - 一键发布游戏到平台
- ✅ **批量处理** - 支持批量创建、发布、生成链接
- ✅ **资源同步** - 自动同步CoursewareMaker资源库

### 支持的游戏类型

| 游戏类型 | 配置脚本 | 模板ID |
|---------|---------|--------|
| 运动PK（赛跑/赛车/游泳） | `build_yundong_pk_config.py` | 70a3010b-0b7a-11ef-b3a3-fa7902489df6 |
| 贪吃小怪兽 | `build_sj6_monster_config.py` | 同上 |
| 其他拖拽类游戏 | 通用 | 同上 |

---

## 🚀 快速开始

### 1. 环境检查（5分钟）

```bash
# 运行环境检查脚本
bash check_environment.sh
```

如果有缺失项，按照提示安装：

```bash
# Node.js依赖
npm install puppeteer-core playwright

# Python依赖
pip install pandas openpyxl requests pyyaml
```

### 2. 启动Chrome调试模式

**Windows**:
```bash
"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="C:\temp\chrome-debug"
```

**macOS**:
```bash
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --remote-debugging-port=9222 --user-data-dir="/tmp/chrome-debug"
```

### 3. 登录CoursewareMaker

在启动的Chrome中访问并登录：
```
https://coursewaremaker.speiyou.com/
```

### 4. 快速测试

```bash
# 创建测试游戏
node create_game_auto.js "测试游戏1" "70a3010b-0b7a-11ef-b3a3-fa7902489df6" ""

# 生成分享链接
GAME_ID=$(cat latest_game_id.txt)
node generate_share_link.js "$GAME_ID"
```

---

## 📚 文档

| 文档 | 说明 |
|------|------|
| **[QUICK_START.md](QUICK_START.md)** | 5分钟快速入门指南 |
| **[COURSEWAREMAKER_AUTOMATION_GUIDE.md](COURSEWAREMAKER_AUTOMATION_GUIDE.md)** | 完整的自动化指南（推荐） |
| **[check_environment.sh](check_environment.sh)** | 环境检查脚本 |

---

## 🛠️ 工具和脚本

### 游戏管理

| 脚本 | 功能 | 用法 |
|------|------|------|
| `create_game_auto.js` | 创建游戏 | `node create_game_auto.js "游戏名" "模板ID" ""` |
| `save_game_config_via_cdp.js` | 导入配置 | `node save_game_config_via_cdp.js <game_id> <config.json>` |
| `publish_game_auto.js` | 发布游戏 | `node publish_game_auto.js <game_id> 2026 "2" "1"` |
| `generate_share_link.js` | 生成分享链接 | `node generate_share_link.js <game_id>` |

### 批量处理

| 脚本 | 功能 | 用法 |
|------|------|------|
| `batch_create_games.js` | 批量创建 | `node batch_create_games.js` |
| `batch_publish_all_games.js` | 批量发布 | `node batch_publish_all_games.js` |
| `batch_generate_share_links.js` | 批量生成链接 | `node batch_generate_share_links.js <list.json>` |

### 配置生成

| 脚本 | 功能 | 用法 |
|------|------|------|
| `build_yundong_pk_config.py` | 运动PK配置 | `python build_yundong_pk_config.py <excel>` |
| `build_sj6_monster_config.py` | 贪吃小怪兽配置 | `python build_sj6_monster_config.py <excel>` |
| `sync_courseware_resources.py` | 同步资源库 | `python sync_courseware_resources.py` |

### 监控工具

| 脚本 | 功能 | 用法 |
|------|------|------|
| `monitor_chrome_activity.js` | 监控所有操作 | `node monitor_chrome_activity.js` |
| `monitor_game_publish.js` | 监控发布流程 | `node monitor_game_publish.js` |
| `monitor_share_link.js` | 监控分享链接 | `node monitor_share_link.js` |

---

## 📋 完整工作流示例

### 单个游戏流程

```bash
# 1. 创建游戏
node create_game_auto.js "2026新一思维诊断1" "70a3010b-0b7a-11ef-b3a3-fa7902489df6" ""

# 2. 获取game_id
GAME_ID=$(cat latest_game_id.txt)

# 3. 导入配置
node save_game_config_via_cdp.js "$GAME_ID" "关卡01_配置.json"

# 4. 生成分享链接（可选）
node generate_share_link.js "$GAME_ID"

# 5. 发布游戏
node publish_game_auto.js "$GAME_ID" 2026 "2" "1"
```

### 批量12关游戏流程

```bash
# 1. 准备配置文件（generated_configs/xinyi_split_12_games/）

# 2. 修改批量创建脚本配置
# 在 batch_create_games.js 中设置：
# - gameNamePrefix: "2026新一思维诊断"
# - configDir: 配置文件目录
# - startIndex/endIndex: 1-12

# 3. 批量创建
node batch_create_games.js

# 4. 批量发布
node batch_publish_all_games.js

# 5. 批量生成分享链接
node batch_generate_share_links.js xinyi_game_id_list.json
```

---

## 🔧 配置说明

### 发布参数

| 参数 | 说明 | 可选值 |
|------|------|--------|
| 年份 | 学年 | 2026, 2027... |
| 学期ID | 学期 | "1"=春季, "2"=暑期, "3"=秋季, "4"=寒假 |
| 年级ID | 年级 | "1"=一年级, "2"=二年级... |
| 学科ID | 学科 | "31"=数学, "32"=语文, "33"=英语 |
| 课次ID | 课次 | "31"=通用 |

### Excel题目表格式

| 列名 | 必填 | 说明 |
|------|------|------|
| 题干 | ✅ | 题目文本 |
| 答案 | ✅ | 正确答案 |
| 选项1 | ✅ | 第一个选项 |
| 选项2 | ✅ | 第二个选项 |
| 选项3 | ❌ | 第三个选项（如有） |
| 题干音频 | ❌ | 题干音频资源名 |
| 选项音频 | ❌ | 选项音频（逗号分隔） |

---

## 📁 目录结构

```
D:/codexProject/
├── README.md                           # 本文件
├── QUICK_START.md                      # 快速入门
├── COURSEWAREMAKER_AUTOMATION_GUIDE.md # 完整指南
├── check_environment.sh                # 环境检查
│
├── 脚本文件/
│   ├── create_game_auto.js
│   ├── save_game_config_via_cdp.js
│   ├── publish_game_auto.js
│   ├── generate_share_link.js
│   ├── batch_*.js
│   └── build_*.py
│
├── 配置文件/
│   ├── latest_game_id.txt
│   ├── *_game_id_list.json
│   └── latest_resources.json
│
├── 数据源/
│   └── *.xlsx
│
├── 生成的配置/
│   └── generated_configs/
│
└── 日志和结果/
    ├── chrome_monitoring_logs/
    ├── batch_*_results_*.json
    └── share_link_*.json
```

---

## 🐛 常见问题

### Q: Chrome连接失败？

**错误**: `connect ECONNREFUSED 127.0.0.1:9222`

**解决**:
```bash
# 关闭Chrome
taskkill /F /IM chrome.exe  # Windows
killall Chrome              # macOS/Linux

# 重新启动调试模式
# 使用上面的启动命令
```

### Q: Token认证失败？

**错误**: `{"code": 401, "msg": "未授权"}`

**解决**:
1. 确保已登录CoursewareMaker
2. 在控制台检查: `localStorage.GAMEMAKER_TOKEN`
3. 如果为空，重新登录

### Q: 配置导入后游戏无法打开？

**原因**: 配置双重编码

**解决**: 确保传递的是对象而不是字符串：
```javascript
// ✅ 正确
data: JSON.parse(configString)

// ❌ 错误
data: JSON.stringify(config)
```

更多问题请查看 [完整指南的故障排除章节](COURSEWAREMAKER_AUTOMATION_GUIDE.md#故障排除)。

---

## 🔗 相关链接

- **CoursewareMaker平台**: https://coursewaremaker.speiyou.com/
- **知音楼API**: https://yach.openclaw.cn/

---

## 📝 许可证

MIT License

---

## 🤝 贡献

欢迎提交Issue和Pull Request！

---

## 📧 联系

如有问题或建议，请通过Issue联系。

---

**最后更新**: 2026-04-16  
**版本**: 1.0.0
