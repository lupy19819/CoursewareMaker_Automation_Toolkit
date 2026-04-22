# CoursewareMaker 自动化快速入门

> **5分钟快速上手指南**

---

## 📦 第一步：环境准备（5分钟）

### 1. 安装必需软件

```bash
# 检查Node.js（需要 ≥16.0）
node --version

# 检查Python（需要 ≥3.8）
python --version

# 检查Chrome浏览器
chrome --version
```

### 2. 安装依赖

```bash
# Node.js依赖
npm install puppeteer-core playwright

# Python依赖
pip install pandas openpyxl requests pyyaml
```

### 3. 启动调试Chrome

**Windows**:
```bash
"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="C:\temp\chrome-debug"
```

**macOS**:
```bash
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --remote-debugging-port=9222 --user-data-dir="/tmp/chrome-debug"
```

**Linux**:
```bash
google-chrome --remote-debugging-port=9222 --user-data-dir="/tmp/chrome-debug"
```

### 4. 登录CoursewareMaker

在刚启动的Chrome中访问：
```
https://coursewaremaker.speiyou.com/
```

登录后，Token会自动存储（脚本会自动获取）。

---

## 🚀 第二步：快速测试（2分钟）

### 测试1: 创建单个游戏

```bash
node create_game_auto.js "测试游戏1" "70a3010b-0b7a-11ef-b3a3-fa7902489df6" ""
```

**预期输出**:
```
✅ 游戏创建成功
游戏ID: xxx-xxx-xxx
已保存到: latest_game_id.txt
```

### 测试2: 获取分享链接

```bash
GAME_ID=$(cat latest_game_id.txt)
node generate_share_link.js "$GAME_ID"
```

**预期输出**:
```
✅ 分享链接生成成功
📋 分享链接: https://coursewaremaker.speiyou.com/#/share-preview?pw=xxx
```

---

## 📝 第三步：实战流程（按需选择）

### 场景A: 创建运动PK游戏

```bash
# 1. 准备题目Excel（格式见文档）
# 题目表: race_questions.xlsx

# 2. 生成配置
python build_yundong_pk_config.py race_questions.xlsx

# 3. 创建游戏
node create_game_auto.js "运动PK-赛跑" "70a3010b-0b7a-11ef-b3a3-fa7902489df6" ""

# 4. 导入配置
GAME_ID=$(cat latest_game_id.txt)
node save_game_config_via_cdp.js "$GAME_ID" "关卡01_配置.json"

# 5. 发布
node publish_game_auto.js "$GAME_ID" 2026 "2" "1"
```

### 场景B: 批量创建12关游戏

```bash
# 1. 准备12个配置文件（放在 generated_configs/目录）

# 2. 修改批量脚本配置（在 batch_create_games.js 中）
const CONFIG = {
  gameNamePrefix: "2026新一思维诊断",
  templateId: "70a3010b-0b7a-11ef-b3a3-fa7902489df6",
  configDir: "D:/codexProject/generated_configs/xinyi_split_12_games",
  startIndex: 1,
  endIndex: 12
};

# 3. 批量创建
node batch_create_games.js

# 4. 批量发布
node batch_publish_all_games.js

# 5. 批量生成分享链接
node batch_generate_share_links.js xinyi_game_id_list.json
```

---

## 🔧 常见问题速查

### Q1: Chrome连接失败？
```bash
# 重启Chrome调试模式
taskkill /F /IM chrome.exe  # Windows
# 或
killall Chrome              # macOS/Linux

# 重新启动（用上面的启动命令）
```

### Q2: Token认证失败？
```bash
# 在Chrome控制台检查
localStorage.GAMEMAKER_TOKEN

# 如果为空，重新登录CoursewareMaker
```

### Q3: 配置导入失败？
```bash
# 检查JSON格式
cat config.json | python -m json.tool

# 确认game_id正确
echo $GAME_ID
```

### Q4: 发布返回"参数有误"？
- 确认学期ID是字符串："1"/"2"/"3"/"4"
- 确认年级ID是字符串："1"/"2"/"3"...
- 确认game_id存在且配置已保存

---

## 📚 下一步

详细文档和高级功能，请查看：
```
D:/codexProject/COURSEWAREMAKER_AUTOMATION_GUIDE.md
```

包含：
- 完整API参考
- 配置生成详解
- 故障排除
- 扩展和自定义

---

## 🎯 一键命令速查

### 完整单游戏流程
```bash
# 设置变量
GAME_NAME="测试游戏"
TEMPLATE_ID="70a3010b-0b7a-11ef-b3a3-fa7902489df6"
CONFIG_FILE="game_config.json"

# 执行流程
node create_game_auto.js "$GAME_NAME" "$TEMPLATE_ID" "" && \
GAME_ID=$(cat latest_game_id.txt) && \
node save_game_config_via_cdp.js "$GAME_ID" "$CONFIG_FILE" && \
node generate_share_link.js "$GAME_ID" && \
node publish_game_auto.js "$GAME_ID" 2026 "2" "1"
```

### 查看最近结果
```bash
# 最新游戏ID
cat latest_game_id.txt

# 最新分享链接
ls -t share_link_*.json | head -1 | xargs cat | grep preview_url

# 最新发布结果
ls -t batch_publish_results_*.json | head -1 | xargs cat | grep -E "(success|failed)"
```

---

**快速入门完成！祝您使用愉快！** 🎉
