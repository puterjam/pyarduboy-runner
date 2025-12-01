#!/bin/bash
# PyArduboy 虚拟环境设置脚本

set -e

echo "========================================="
echo "PyArduboy 虚拟环境设置"
echo "========================================="
echo ""

# 检查 Python 版本
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

echo "检测到 Python 版本: $PYTHON_VERSION"

# 验证 Python 版本（必须是 3.10 或 3.11）
if [ "$PYTHON_MAJOR" -ne 3 ]; then
    echo ""
    echo "✗ 错误: 需要 Python 3.x 版本"
    echo "  当前版本: Python $PYTHON_VERSION"
    exit 1
fi

if [ "$PYTHON_MINOR" -lt 10 ]; then
    echo ""
    echo "✗ 错误: Python 版本过低"
    echo "  当前版本: Python $PYTHON_VERSION"
    echo "  要求版本: Python 3.10 ~ 3.12"
    echo ""
    echo "请升级 Python:"
    echo "  brew install python@3.12"
    exit 1
elif [ "$PYTHON_MINOR" -ge 13 ]; then
    echo ""
    echo "✗ 错误: Python 版本过高，与 libretro.py 不兼容"
    echo "  当前版本: Python $PYTHON_VERSION"
    echo "  要求版本: Python 3.10 ~ 3.12 (推荐 3.12)"
    echo ""
    echo "解决方案:"
    echo "  1. 安装 Python 3.12:"
    echo "     brew install python@3.12"
    echo ""
    echo "  2. 使用 Python 3.12 创建虚拟环境:"
    echo "     python3.12 -m venv venv"
    echo ""
    echo "  3. 或使用 conda:"
    echo "     conda create -n pyarduboy python=3.12"
    echo "     conda activate pyarduboy"
    echo ""
    exit 1
fi

echo "✓ Python 版本检查通过: Python $PYTHON_VERSION"

# 创建虚拟环境
if [ ! -d "venv" ]; then
    echo ""
    echo ">>> 创建虚拟环境..."
    python3 -m venv venv
    echo "✓ 虚拟环境创建成功"
else
    echo ""
    echo "✓ 虚拟环境已存在"
fi

# 激活虚拟环境
echo ""
echo ">>> 激活虚拟环境..."
source venv/bin/activate

# 再次检查虚拟环境中的 Python 版本
VENV_PYTHON_VERSION=$(python --version 2>&1 | awk '{print $2}')
VENV_PYTHON_MINOR=$(echo $VENV_PYTHON_VERSION | cut -d. -f2)

echo "虚拟环境中的 Python 版本: $VENV_PYTHON_VERSION"

if [ "$VENV_PYTHON_MINOR" -ge 13 ]; then
    echo ""
    echo "✗ 错误: 虚拟环境使用了不兼容的 Python 版本"
    echo "  虚拟环境版本: Python $VENV_PYTHON_VERSION"
    echo "  要求版本: Python 3.10 ~ 3.12"
    echo ""
    echo "请删除虚拟环境并使用正确的 Python 版本重新创建:"
    echo "  rm -rf venv"
    echo "  python3.12 -m venv venv"
    echo "  source venv/bin/activate"
    echo "  pip install -r requirements.txt"
    echo ""
    deactivate
    exit 1
fi

echo "✓ 虚拟环境 Python 版本检查通过"

# 升级 pip
echo ""
echo ">>> 升级 pip..."
pip install --upgrade pip

# 安装依赖
echo ""
echo ">>> 安装 Python 依赖..."
pip install -r requirements.txt

echo ""
echo "========================================="
echo "✓ 虚拟环境设置完成！"
echo "========================================="
echo ""
echo "使用方法："
echo "  1. 激活虚拟环境："
echo "     source venv/bin/activate"
echo ""
echo "  2. 运行示例："
echo "     cd examples"
echo "     python basic_demo.py"
echo ""
echo "  3. 退出虚拟环境："
echo "     deactivate"
echo ""
