#!/bin/bash
# PyArduboy 虚拟环境设置脚本

set -e

echo "========================================="
echo "PyArduboy 虚拟环境设置"
echo "========================================="
echo ""

# 检查 Python 版本
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python 版本: $PYTHON_VERSION"

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
