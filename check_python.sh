#!/bin/bash
# Python 版本检查脚本

echo "=== PyArduboy Python Version Check ==="
echo ""

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "Current Python version: $PYTHON_VERSION"
echo ""

# 检查版本
if [[ "$PYTHON_VERSION" == "3.10" ]] || [[ "$PYTHON_VERSION" == "3.11" ]]; then
    echo "✓ Python version is compatible!"
    echo "  You can run: python3 run.py ./roms/2048.hex -v pygame"
elif [[ "$PYTHON_VERSION" == "3.12" ]] || [[ "$PYTHON_VERSION" == "3.13" ]] || [[ "$PYTHON_VERSION" == "3.14" ]]; then
    echo "✗ Python $PYTHON_VERSION is NOT fully compatible with libretro.py"
    echo ""
    echo "Solutions:"
    echo "  1. Install Python 3.11: brew install python@3.11"
    echo "  2. Create venv with Python 3.11:"
    echo "     python3.11 -m venv venv"
    echo "     source venv/bin/activate"
    echo "     pip install -r requirements.txt"
    echo ""
    echo "  Or use conda:"
    echo "     conda create -n pyarduboy python=3.11"
    echo "     conda activate pyarduboy"
    echo "     pip install -r requirements.txt"
else
    echo "⚠ Unknown Python version: $PYTHON_VERSION"
    echo "  Recommended: Python 3.11"
fi
