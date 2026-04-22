# CoursewareMaker 自动化文档索引

> **文档导航中心 - 快速找到您需要的文档**

---

## 📖 入门文档

### 🚀 [README.md](README.md) - 项目概览
**阅读时间**: 5分钟  
**适合人群**: 所有用户  
**内容**:
- 项目概述和核心功能
- 快速开始指南
- 工具和脚本列表
- 常见问题速查
- 完整工作流示例

---

### ⚡ [QUICK_START.md](QUICK_START.md) - 快速入门
**阅读时间**: 5分钟  
**适合人群**: 新用户  
**内容**:
- 5分钟环境准备
- 2分钟快速测试
- 实战场景示例
- 常见问题速查
- 一键命令速查

**推荐**: 第一次使用时先阅读此文档！

---

## 📚 详细文档

### 📘 [COURSEWAREMAKER_AUTOMATION_GUIDE.md](COURSEWAREMAKER_AUTOMATION_GUIDE.md) - 完整自动化指南
**阅读时间**: 30分钟  
**适合人群**: 需要深入了解的用户、AI助手  
**内容**:
- 完整的环境要求和配置
- 详细的目录结构说明
- 认证配置详解
- 7步完整工作流（每步都有详细说明）
- 所有工具和脚本的详细说明
- 完整的API参考
- 故障排除指南
- 附录（ID对照表、命令速查、扩展指南等）

**推荐**: 
- 需要配置新环境时
- 遇到问题需要排查时
- 需要扩展功能时
- 给其他AI助手使用时

---

## 🛠️ 工具和脚本

### 🔍 [check_environment.sh](check_environment.sh) - 环境检查脚本
**用途**: 自动检查环境配置  
**使用**:
```bash
bash check_environment.sh
```

**检查内容**:
- ✅ Node.js、Python、Chrome等核心软件
- ✅ npm和pip依赖包
- ✅ Chrome调试端口
- ✅ 必需的脚本文件
- ✅ 生成检查报告

---

### ⚙️ [config.template.json](config.template.json) - 配置模板
**用途**: 项目配置参考模板  
**使用**:
```bash
cp config.template.json config.json
# 然后编辑 config.json
```

**包含配置**:
- Chrome调试配置
- CoursewareMaker平台配置
- 知音楼API配置
- 游戏模板ID
- 发布参数
- 路径配置
- 批量操作配置

---

## 📊 工作流程图

### 完整流程

```
开始
  ↓
┌─────────────────────┐
│ 1. 环境准备          │ → check_environment.sh
│   - 安装依赖         │   README.md
│   - 启动Chrome      │   QUICK_START.md
│   - 登录平台        │
└──────────┬──────────┘
           ↓
┌─────────────────────┐
│ 2. 资源同步 (可选)   │ → sync_courseware_resources.py
│   - 拉取资源库       │
└──────────┬──────────┘
           ↓
┌─────────────────────┐
│ 3. 生成配置          │ → build_yundong_pk_config.py
│   - 从Excel生成JSON  │   build_sj6_monster_config.py
└──────────┬──────────┘
           ↓
┌─────────────────────┐
│ 4. 创建游戏          │ → create_game_auto.js
│   - 调用API创建      │   batch_create_games.js
│   - 获取game_id     │
└──────────┬──────────┘
           ↓
┌─────────────────────┐
│ 5. 导入配置          │ → save_game_config_via_cdp.js
│   - 通过CDP注入      │
│   - 保存配置         │
└──────────┬──────────┘
           ↓
┌─────────────────────┐
│ 6. 生成分享链接      │ → generate_share_link.js
│   - 调用API生成      │   batch_generate_share_links.js
│   - 获取预览链接     │
└──────────┬──────────┘
           ↓
┌─────────────────────┐
│ 7. 发布游戏          │ → publish_game_auto.js
│   - 4步发布流程      │   batch_publish_all_games.js
│   - 游戏上线         │
└──────────┬──────────┘
           ↓
          完成
```

---

## 📁 文档分类

### 按用户类型

| 用户类型 | 推荐文档 | 顺序 |
|---------|---------|------|
| **新手用户** | QUICK_START.md → README.md | 1. 快速入门 → 2. 概览 |
| **开发人员** | README.md → COURSEWAREMAKER_AUTOMATION_GUIDE.md | 1. 概览 → 2. 详细指南 |
| **AI助手** | COURSEWAREMAKER_AUTOMATION_GUIDE.md → config.template.json | 1. 完整指南 → 2. 配置模板 |
| **运维人员** | check_environment.sh → COURSEWAREMAKER_AUTOMATION_GUIDE.md (故障排除) | 1. 环境检查 → 2. 故障排除 |

---

### 按任务类型

| 任务 | 参考文档 | 章节 |
|------|---------|------|
| **首次配置环境** | QUICK_START.md | 第一步：环境准备 |
| **创建单个游戏** | QUICK_START.md | 场景A |
| **批量创建游戏** | QUICK_START.md | 场景B |
| **配置生成** | COURSEWAREMAKER_AUTOMATION_GUIDE.md | 步骤2：生成游戏配置 |
| **发布游戏** | COURSEWAREMAKER_AUTOMATION_GUIDE.md | 步骤6：发布游戏 |
| **生成分享链接** | COURSEWAREMAKER_AUTOMATION_GUIDE.md | 步骤5：生成预览分享链接 |
| **API调用** | COURSEWAREMAKER_AUTOMATION_GUIDE.md | API参考 |
| **故障排除** | COURSEWAREMAKER_AUTOMATION_GUIDE.md | 故障排除 |
| **扩展功能** | COURSEWAREMAKER_AUTOMATION_GUIDE.md | 附录E：扩展和自定义 |

---

## 🔍 快速查找

### 命令查找

| 需要 | 位置 |
|------|------|
| 环境检查命令 | QUICK_START.md → 第一步 |
| 启动Chrome命令 | QUICK_START.md → 第一步<br>COURSEWAREMAKER_AUTOMATION_GUIDE.md → 环境要求 |
| 单个游戏流程 | QUICK_START.md → 场景A<br>README.md → 完整工作流示例 |
| 批量操作命令 | README.md → 批量12关游戏流程 |
| 一键命令 | QUICK_START.md → 一键命令速查 |

---

### 配置查找

| 需要 | 位置 |
|------|------|
| 学期/年级ID | COURSEWAREMAKER_AUTOMATION_GUIDE.md → 附录A |
| 模板ID | config.template.json → gameTemplates<br>README.md → 支持的游戏类型 |
| API端点 | COURSEWAREMAKER_AUTOMATION_GUIDE.md → API参考<br>config.template.json → coursewaremaker.endpoints |
| Excel格式 | COURSEWAREMAKER_AUTOMATION_GUIDE.md → 步骤2<br>README.md → Excel题目表格式 |

---

### 错误解决查找

| 错误类型 | 位置 |
|---------|------|
| Chrome连接失败 | README.md → 常见问题<br>COURSEWAREMAKER_AUTOMATION_GUIDE.md → 故障排除 → 问题1 |
| Token认证失败 | README.md → 常见问题<br>COURSEWAREMAKER_AUTOMATION_GUIDE.md → 故障排除 → 问题2 |
| 配置双重编码 | COURSEWAREMAKER_AUTOMATION_GUIDE.md → 故障排除 → 问题3 |
| 资源匹配失败 | COURSEWAREMAKER_AUTOMATION_GUIDE.md → 故障排除 → 问题4 |
| 发布失败 | COURSEWAREMAKER_AUTOMATION_GUIDE.md → 故障排除 → 问题5 |

---

## 📦 文档版本

| 文档 | 版本 | 更新时间 |
|------|------|----------|
| README.md | 1.0.0 | 2026-04-16 |
| QUICK_START.md | 1.0.0 | 2026-04-16 |
| COURSEWAREMAKER_AUTOMATION_GUIDE.md | 1.0 | 2026-04-16 |
| config.template.json | 1.0.0 | 2026-04-16 |
| check_environment.sh | 1.0.0 | 2026-04-16 |

---

## 🎯 使用建议

### 第一次使用
1. ⭐ 阅读 [QUICK_START.md](QUICK_START.md)（5分钟）
2. 运行 `bash check_environment.sh`
3. 按提示完成环境配置
4. 运行快速测试命令

### 日常使用
- 需要命令时查看 [README.md](README.md)
- 遇到问题时查看 [COURSEWAREMAKER_AUTOMATION_GUIDE.md](COURSEWAREMAKER_AUTOMATION_GUIDE.md) 的故障排除章节

### 配置新环境
1. 阅读 [COURSEWAREMAKER_AUTOMATION_GUIDE.md](COURSEWAREMAKER_AUTOMATION_GUIDE.md) 的环境要求章节
2. 复制 [config.template.json](config.template.json) 为 `config.json`
3. 运行 `bash check_environment.sh` 验证

### 给AI助手使用
直接提供 [COURSEWAREMAKER_AUTOMATION_GUIDE.md](COURSEWAREMAKER_AUTOMATION_GUIDE.md)，它包含了完整的上下文和详细说明。

---

## 📝 更新日志

### v1.0.0 (2026-04-16)
- ✅ 创建完整文档体系
- ✅ 添加环境检查脚本
- ✅ 添加配置模板
- ✅ 创建文档索引

---

## 🔗 相关资源

- **CoursewareMaker平台**: https://coursewaremaker.speiyou.com/
- **知音楼API**: https://yach.openclaw.cn/
- **项目目录**: D:/codexProject/

---

**最后更新**: 2026-04-16  
**维护者**: CoursewareMaker自动化工具团队
