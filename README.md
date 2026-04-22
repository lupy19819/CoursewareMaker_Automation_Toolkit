# CoursewareMaker 自动化工具包

> **版本**: 1.1.0  
> **发布日期**: 2026-04-16  
> **适用平台**: Windows / macOS / Linux  
> **新增**: 标准化题型生成工具 ⭐

---

## 📦 工具包内容

本工具包包含CoursewareMaker平台游戏创建、配置、发布的完整自动化解决方案。

### 📁 目录结构

```
CoursewareMaker_Automation_Toolkit/
├── README.md                            # 本文件（快速入门）
├── STANDARD_QUESTION_INTEGRATION.md     # 标准化题型集成指南 ⭐ 新增
│
├── scripts/                             # 核心脚本
│   ├── create_game_auto.js              # 创建游戏
│   ├── save_game_config_via_cdp.js      # 导入配置
│   ├── publish_game_auto.js             # 发布游戏
│   ├── generate_share_link.js           # 生成分享链接
│   ├── batch_create_games.js            # 批量创建
│   ├── batch_publish_all_games.js       # 批量发布
│   ├── batch_generate_share_links.js    # 批量生成链接
│   ├── courseware_bulk_upload_assets.mjs # 素材上传
│   ├── build_yundong_pk_config.py       # 运动PK配置生成
│   ├── build_sj6_monster_config.py      # 贪吃小怪兽配置生成
│   └── sync_courseware_resources.py     # 资源同步
│
├── docs/                                # 完整文档
│   ├── QUICK_START.md                   # 5分钟快速入门
│   ├── COURSEWAREMAKER_AUTOMATION_GUIDE.md  # 完整技术指南
│   ├── DOCUMENTATION_INDEX.md           # 文档导航
│   ├── CHANGELOG.md                     # 版本更新日志
│   ├── check_environment.sh             # 环境检查脚本
│   ├── config.template.json             # 配置模板
│   └── *_workflow_analysis.md           # 各流程详细分析
│
├── standard_question_toolkit/           # 标准化题型工具 ⭐ 新增
│   ├── README_FOR_CLAUDE.md             # Claude入口文档
│   ├── docs/                            # 题型文档
│   │   ├── standard_workflow.md         # 标准化生成流程
│   │   ├── question_input_template.md   # 题目输入模板
│   │   └── claude_prompt.md             # Claude提示词
│   ├── data/                            # 皮肤数据
│   │   ├── component_skin_inventory.json # 皮肤清单
│   │   ├── skin_resource_table.tsv      # 皮肤资源表
│   │   └── skin_text_color_usage.tsv    # 颜色用途表
│   ├── scripts/                         # 生成脚本
│   │   ├── generate_grade3_config.py    # 三年级示例
│   │   ├── generate_grade4_config.py    # 四年级示例
│   │   ├── split_xiner_games.py         # 多关拆单关
│   │   └── extract_component_skins.py   # 提取皮肤
│   └── templates/                       # 配置模板
│       ├── base_choice_fill_template.json  # 选择/填空模板
│       └── vertical_multiplication_template.json # 竖式模板
│
├── examples/                            # 示例配置
└── utils/                               # 辅助工具
```

---

## 🚀 快速开始（3步）

### 1. 安装依赖

```bash
# Node.js依赖
npm install puppeteer-core playwright

# Python依赖
pip install pandas openpyxl requests pyyaml
```

### 2. 启动Chrome调试模式

```bash
# Windows
"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="C:\temp\chrome-debug"

# macOS
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --remote-debugging-port=9222 --user-data-dir="/tmp/chrome-debug"

# Linux
google-chrome --remote-debugging-port=9222 --user-data-dir="/tmp/chrome-debug"
```

### 3. 登录CoursewareMaker

在刚启动的Chrome中访问并登录：
```
https://coursewaremaker.speiyou.com/
```

---

## 📖 完整工作流（8步）

```bash
# Step 0: 同步资源库（可选）
python scripts/sync_courseware_resources.py

# Step 1: 批量上传素材（如有自定义素材）
node scripts/courseware_bulk_upload_assets.mjs "素材文件夹路径"

# Step 2: 再次同步资源库
python scripts/sync_courseware_resources.py

# Step 3: 生成配置
python scripts/build_yundong_pk_config.py 题目表.xlsx

# Step 4: 创建游戏
node scripts/create_game_auto.js "游戏名称" "模板ID" ""

# Step 5: 导入配置
GAME_ID=$(cat latest_game_id.txt)
node scripts/save_game_config_via_cdp.js "$GAME_ID" "配置.json"

# Step 6: 生成分享链接（可选）
node scripts/generate_share_link.js "$GAME_ID"

# Step 7: 发布游戏
node scripts/publish_game_auto.js "$GAME_ID" 2026 "2" "1"
```

---

## 📚 文档指南

### 从哪里开始？

1. **第一次使用** → 阅读 `docs/QUICK_START.md`
2. **需要详细说明** → 阅读 `docs/COURSEWAREMAKER_AUTOMATION_GUIDE.md`
3. **查找特定功能** → 查看 `docs/DOCUMENTATION_INDEX.md`
4. **遇到问题** → 查看文档的"故障排除"章节

### 文档结构

| 文档 | 用途 | 阅读时间 |
|------|------|----------|
| `QUICK_START.md` | 快速入门 | 5分钟 |
| `README.md` (本文件) | 工具包概览 | 3分钟 |
| `COURSEWAREMAKER_AUTOMATION_GUIDE.md` | 完整技术指南 | 30分钟 |
| `DOCUMENTATION_INDEX.md` | 文档导航 | 5分钟 |
| `*_workflow_analysis.md` | 各流程详细分析 | 10分钟 |

---

## 🎯 核心功能

| 功能 | 脚本 | 说明 |
|------|------|------|
| **创建游戏** | `create_game_auto.js` | 使用API创建空游戏，获取game_id |
| **导入配置** | `save_game_config_via_cdp.js` | 通过CDP将配置注入到游戏 |
| **发布游戏** | `publish_game_auto.js` | 4步API流程发布游戏 |
| **分享链接** | `generate_share_link.js` | 生成7天有效期的预览链接 |
| **素材上传** | `courseware_bulk_upload_assets.mjs` | 批量上传PNG/音频到COS |
| **配置生成** | `build_*.py` | 从Excel生成游戏配置JSON |
| **批量操作** | `batch_*.js` | 批量创建/发布/生成链接 |

---

## ✅ 环境检查

运行环境检查脚本（推荐）：

```bash
bash docs/check_environment.sh
```

会自动检查：
- ✅ Node.js、Python、Chrome
- ✅ npm/pip依赖包
- ✅ Chrome调试端口
- ✅ 必需的脚本文件

---

## 🎓 支持的游戏类型

### 运动PK系列
- ✅ **运动PK系列**（赛跑、赛车、游泳）
- ✅ **贪吃小怪兽**

### 标准化题型（新增！v1.1.0）
- ✅ **选择题** (`AloneClickChoice`)
- ✅ **填空题** (`QuestionForBlank`)
- ✅ **拖拽题** (`MDraggbale` + `LDragPlace`)
- ✅ **竖式/算式填空题**（网格布局）
- ✅ **内嵌填空题**
- ✅ **配图题目**

### 皮肤系统（新增！）
- ✅ **沙滩皮肤** - 暖色调，适合低年级
- ✅ **图纸皮肤** - 工程风格，适合理科题
- ✅ **紫色星空皮肤** - 科技感，适合高年级

### 其他
- ✅ **多关拆单关** - 将12关游戏拆为12个独立游戏
- ✅ 其他组件化游戏模板

---

## 📊 已验证的使用案例

- ✅ 新一年级12关游戏（批量创建+发布）
- ✅ 新二年级12关游戏（批量创建+发布）
- ✅ 素材批量上传（3个测试文件）
- ✅ 共计24个游戏的完整自动化流程

---

## 🔧 配置说明

### 1. 修改批量脚本配置

编辑 `scripts/batch_create_games.js`：

```javascript
const CONFIG = {
  gameNamePrefix: "2026新一思维全能力诊断",
  templateId: "70a3010b-0b7a-11ef-b3a3-fa7902489df6",
  configDir: "./generated_configs/xinyi_split_12_games",
  startIndex: 1,
  endIndex: 12
};
```

### 2. 发布参数

- **学期ID**: "1"=春季, "2"=暑期, "3"=秋季, "4"=寒假
- **年级ID**: "1"=一年级, "2"=二年级, "3"=三年级...
- **学科ID**: "31"=数学, "32"=语文, "33"=英语
- **课次ID**: "31"=通用

详见 `docs/COURSEWAREMAKER_AUTOMATION_GUIDE.md` 的附录A。

---

## 💡 使用提示

### 最佳实践

1. ✅ 先运行环境检查脚本
2. ✅ 批量操作前先测试1-2个游戏
3. ✅ 保留所有操作结果JSON文件
4. ✅ 定期备份游戏ID列表
5. ✅ 素材上传后立即同步资源库

### 注意事项

- ⚠️ Chrome必须保持调试模式运行
- ⚠️ 所有路径使用绝对路径
- ⚠️ 批量操作有延迟（避免API限流）
- ⚠️ 配置必须是JSON对象，不是字符串

---

## 🐛 常见问题

### Q: Chrome连接失败？
```bash
# 重启Chrome调试模式
taskkill /F /IM chrome.exe  # Windows
# 然后重新启动调试模式
```

### Q: Token认证失败？
```bash
# 在Chrome控制台检查
localStorage.GAMEMAKER_TOKEN
# 如果为空，重新登录CoursewareMaker
```

### Q: 找不到脚本？
```bash
# 确保在工具包根目录运行
cd CoursewareMaker_Automation_Toolkit
# 使用相对路径
node scripts/create_game_auto.js ...
```

更多问题请查看 `docs/COURSEWAREMAKER_AUTOMATION_GUIDE.md` 的"故障排除"章节。

---

## 📦 版本信息

- **当前版本**: 1.0.0
- **发布日期**: 2026-04-16
- **测试状态**: ✅ 全部通过
- **适用平台**: Windows 10/11, macOS 10.15+, Linux (Ubuntu 20.04+)

---

## 🔗 相关资源

- **CoursewareMaker平台**: https://coursewaremaker.speiyou.com/
- **知音楼API**: https://yach.openclaw.cn/

---

## 📄 许可证

MIT License

---

## 🙏 致谢

感谢所有参与测试和验证的用户。

---

## 📮 反馈与支持

如有问题或建议，请查阅完整文档或联系技术支持。

---

**开始使用**: 请阅读 `docs/QUICK_START.md` 开始您的自动化之旅！

**最后更新**: 2026-04-16
