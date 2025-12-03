#!/bin/bash
# PyArduboy 一键安装脚本
# 自动设置虚拟环境、安装依赖、下载 libretro 核心

set -e

echo "========================================="
echo "   PyArduboy 树莓派模拟器环境安装"
echo "========================================="
echo ""

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 打印成功消息
print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

# 打印警告消息
print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# 打印错误消息
print_error() {
    echo -e "${RED}✗${NC} $1"
}

# 步骤 1: 检测操作系统
echo ">>> 步骤 1/5: 检测操作系统"
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
    print_success "检测到 Linux 系统"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS="mac"
    print_success "检测到 macOS 系统"
else
    print_error "不支持的操作系统: $OSTYPE"
    exit 1
fi
echo ""

# 步骤 2: 检查 Python 版本
echo ">>> 步骤 2/5: 检查 Python 环境"
if ! command -v python3 &> /dev/null; then
    print_error "未找到 Python 3"
    echo "请先安装 Python 3.10-3.12:"
    if [ "$OS" == "mac" ]; then
        echo "  brew install python@3.12"
    else
        echo "  sudo apt-get install python3.12"
    fi
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

print_success "检测到 Python 版本: $PYTHON_VERSION"

# 验证 Python 版本
if [ "$PYTHON_MAJOR" -ne 3 ] || [ "$PYTHON_MINOR" -lt 10 ] || [ "$PYTHON_MINOR" -ge 13 ]; then
    print_error "Python 版本不兼容"
    echo "  当前版本: Python $PYTHON_VERSION"
    echo "  要求版本: Python 3.10 ~ 3.12"
    exit 1
fi

print_success "Python 版本检查通过"
echo ""

# 步骤 3: 创建并激活虚拟环境
echo ">>> 步骤 3/5: 设置 Python 虚拟环境"
if [ ! -d "venv" ]; then
    echo "创建虚拟环境..."
    python3 -m venv venv
    print_success "虚拟环境创建成功"
else
    print_success "虚拟环境已存在"
fi

# 激活虚拟环境
source venv/bin/activate

# 升级 pip
echo "升级 pip..."
pip install --upgrade pip > /dev/null 2>&1
print_success "pip 已升级到最新版本"

# 安装依赖
echo "安装 Python 依赖..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt > /dev/null 2>&1
    print_success "Python 依赖安装完成"
else
    print_warning "未找到 requirements.txt"
fi
echo ""

# 步骤 4: 选择并下载 libretro 核心
echo ">>> 步骤 4/5: 下载 LibRetro 核心"
echo ""
echo "可用的 Arduboy 模拟器核心:"
echo "  1) ardens   - ardens 模拟器 (推荐)"
echo "  2) arduous  - Arduboy 模拟器"
echo "  3) 跳过      - 稍后手动下载"
echo ""

# 默认选择
CORE_CHOICE="1"

# 如果是交互式终端，询问用户
if [ -t 0 ]; then
    read -p "请选择 [1-3] (默认: 1): " CORE_CHOICE
    CORE_CHOICE=${CORE_CHOICE:-1}
fi

case $CORE_CHOICE in
    1)
        CORE_NAME="ardens"
        ;;
    2)
        CORE_NAME="arduous"
        ;;
    3)
        print_warning "跳过核心下载"
        CORE_NAME=""
        ;;
    *)
        print_warning "无效选择，使用默认: arduous"
        CORE_NAME="arduous"
        ;;
esac

if [ ! -z "$CORE_NAME" ]; then
    echo ""
    echo "正在下载 $CORE_NAME 核心..."

    # 检查 core 目录下是否已存在该核心
    if [ "$OS" == "mac" ]; then
        CORE_FILE="core/${CORE_NAME}_libretro.dylib"
    else
        CORE_FILE="core/${CORE_NAME}_libretro.so"
    fi

    if [ -f "$CORE_FILE" ]; then
        print_warning "核心文件已存在: $CORE_FILE"
        echo ""
        read -p "是否重新下载? [y/N]: " REDOWNLOAD
        if [[ ! "$REDOWNLOAD" =~ ^[Yy]$ ]]; then
            print_success "使用现有核心文件"
            CORE_NAME=""
        fi
    fi

    if [ ! -z "$CORE_NAME" ]; then
        python download_core.py "$CORE_NAME"

        if [ $? -eq 0 ]; then
            print_success "$CORE_NAME 核心下载成功"
        else
            print_error "核心下载失败"
            echo ""
            echo "你可以稍后手动下载:"
            echo "  python download_core.py $CORE_NAME"
        fi
    fi
fi
echo ""

# 步骤 5: 验证安装
echo ">>> 步骤 5/5: 验证安装"

# 检查是否有核心文件
if [ "$OS" == "mac" ]; then
    CORE_PATTERN="core/*_libretro.dylib"
else
    CORE_PATTERN="core/*_libretro.so"
fi

if ls $CORE_PATTERN 1> /dev/null 2>&1; then
    CORE_COUNT=$(ls $CORE_PATTERN | wc -l)
    print_success "找到 $CORE_COUNT 个 libretro 核心文件"
    echo ""
    echo "已安装的核心:"
    for core in $CORE_PATTERN; do
        echo "  - $(basename $core)"
    done
else
    print_warning "未找到 libretro 核心文件"
    echo ""
    echo "请运行以下命令下载核心:"
    echo "  python download_core.py arduous"
    echo "  或"
    echo "  python download_core.py ardens"
fi
echo ""

# 完成
echo "========================================="
print_success "安装完成！"
echo "========================================="
echo ""
echo "快速开始:"
echo ""
echo "  1. 激活虚拟环境（如果还未激活）:"
echo "     source venv/bin/activate"
echo ""
echo "  2. 运行示例程序:"
echo "     python run.py"
echo ""
echo "  3. 列出可用的核心:"
echo "     python download_core.py --list"
echo ""
echo "  4. 下载其他核心:"
echo "     python download_core.py ardens"
echo ""
echo "  5. 退出虚拟环境:"
echo "     deactivate"
echo ""
echo "更多信息请参考 README.md"
echo ""
