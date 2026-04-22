#!/bin/bash
# CoursewareMaker 自动化环境检查脚本
# 使用方法: bash check_environment.sh

echo "========================================="
echo "CoursewareMaker 自动化环境检查"
echo "========================================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查结果统计
PASS=0
FAIL=0
WARN=0

# 检查函数
check_command() {
    local cmd=$1
    local required_version=$2
    local name=$3

    echo -n "检查 $name ... "

    if command -v $cmd &> /dev/null; then
        version=$($cmd --version 2>&1 | head -n 1)
        echo -e "${GREEN}✓${NC} 已安装"
        echo "  版本: $version"
        ((PASS++))
        return 0
    else
        echo -e "${RED}✗${NC} 未安装"
        echo "  需要版本: $required_version"
        ((FAIL++))
        return 1
    fi
}

check_port() {
    local port=$1
    local name=$2

    echo -n "检查 $name (端口 $port) ... "

    if command -v nc &> /dev/null; then
        if nc -z localhost $port 2>/dev/null; then
            echo -e "${GREEN}✓${NC} 端口开放"
            ((PASS++))
            return 0
        else
            echo -e "${YELLOW}⚠${NC} 端口未开放"
            echo "  提示: 需要启动Chrome调试模式"
            ((WARN++))
            return 1
        fi
    else
        # fallback to curl
        if curl -s http://localhost:$port/json/version &> /dev/null; then
            echo -e "${GREEN}✓${NC} 端口开放"
            ((PASS++))
            return 0
        else
            echo -e "${YELLOW}⚠${NC} 端口未开放"
            echo "  提示: 需要启动Chrome调试模式"
            ((WARN++))
            return 1
        fi
    fi
}

check_file() {
    local file=$1
    local name=$2

    echo -n "检查 $name ... "

    if [ -f "$file" ]; then
        echo -e "${GREEN}✓${NC} 存在"
        ((PASS++))
        return 0
    else
        echo -e "${YELLOW}⚠${NC} 不存在"
        ((WARN++))
        return 1
    fi
}

echo "=== 1. 核心软件检查 ==="
echo ""

check_command "node" "≥16.0.0" "Node.js"
echo ""

check_command "npm" "≥8.0.0" "npm"
echo ""

check_command "python" "≥3.8.0" "Python"
echo ""

check_command "pip" "≥21.0.0" "pip"
echo ""

# 检查Chrome
echo -n "检查 Chrome浏览器 ... "
if command -v google-chrome &> /dev/null || command -v chrome &> /dev/null; then
    echo -e "${GREEN}✓${NC} 已安装"
    ((PASS++))
elif [ -f "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" ]; then
    echo -e "${GREEN}✓${NC} 已安装 (macOS)"
    ((PASS++))
elif [ -f "/c/Program Files/Google/Chrome/Application/chrome.exe" ]; then
    echo -e "${GREEN}✓${NC} 已安装 (Windows)"
    ((PASS++))
else
    echo -e "${RED}✗${NC} 未找到"
    ((FAIL++))
fi
echo ""

echo ""
echo "=== 2. Node.js 依赖检查 ==="
echo ""

echo -n "检查 puppeteer-core ... "
if npm list puppeteer-core &> /dev/null; then
    echo -e "${GREEN}✓${NC} 已安装"
    ((PASS++))
else
    echo -e "${RED}✗${NC} 未安装"
    echo "  安装命令: npm install puppeteer-core"
    ((FAIL++))
fi
echo ""

echo -n "检查 playwright ... "
if npm list playwright &> /dev/null; then
    echo -e "${GREEN}✓${NC} 已安装"
    ((PASS++))
else
    echo -e "${RED}✗${NC} 未安装"
    echo "  安装命令: npm install playwright"
    ((FAIL++))
fi
echo ""

echo ""
echo "=== 3. Python 依赖检查 ==="
echo ""

for pkg in pandas openpyxl requests pyyaml; do
    echo -n "检查 $pkg ... "
    if python -c "import $pkg" 2>/dev/null; then
        echo -e "${GREEN}✓${NC} 已安装"
        ((PASS++))
    else
        echo -e "${RED}✗${NC} 未安装"
        echo "  安装命令: pip install $pkg"
        ((FAIL++))
    fi
    echo ""
done

echo ""
echo "=== 4. Chrome 调试端口检查 ==="
echo ""

check_port 9222 "Chrome CDP"
echo ""

echo ""
echo "=== 5. 脚本文件检查 ==="
echo ""

SCRIPTS=(
    "create_game_auto.js"
    "save_game_config_via_cdp.js"
    "publish_game_auto.js"
    "generate_share_link.js"
    "batch_create_games.js"
    "batch_publish_all_games.js"
    "build_yundong_pk_config.py"
    "sync_courseware_resources.py"
)

for script in "${SCRIPTS[@]}"; do
    check_file "$script" "$script"
    echo ""
done

echo ""
echo "========================================="
echo "检查结果汇总"
echo "========================================="
echo ""
echo -e "${GREEN}✓ 通过: $PASS${NC}"
echo -e "${YELLOW}⚠ 警告: $WARN${NC}"
echo -e "${RED}✗ 失败: $FAIL${NC}"
echo ""

if [ $FAIL -eq 0 ] && [ $WARN -eq 0 ]; then
    echo -e "${GREEN}恭喜！环境检查全部通过！${NC}"
    echo ""
    echo "下一步:"
    echo "1. 启动Chrome调试模式（如果端口检查未通过）"
    echo "2. 登录 https://coursewaremaker.speiyou.com/"
    echo "3. 运行测试命令: node create_game_auto.js \"测试游戏\" \"70a3010b-0b7a-11ef-b3a3-fa7902489df6\" \"\""
    echo ""
    exit 0
elif [ $FAIL -eq 0 ]; then
    echo -e "${YELLOW}环境基本就绪，有一些警告项需要注意${NC}"
    echo ""
    echo "建议:"
    if [ $WARN -gt 0 ]; then
        echo "- 检查警告项并按提示操作"
    fi
    echo ""
    exit 0
else
    echo -e "${RED}环境检查失败，请安装缺失的依赖${NC}"
    echo ""
    echo "快速修复命令:"
    echo ""
    echo "# 安装Node.js依赖"
    echo "npm install puppeteer-core playwright"
    echo ""
    echo "# 安装Python依赖"
    echo "pip install pandas openpyxl requests pyyaml"
    echo ""
    exit 1
fi
