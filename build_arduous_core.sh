#!/bin/bash
set -e

# 检测操作系统
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS="mac"
else
    echo "不支持的操作系统: $OSTYPE"
    exit 1
fi

echo ">>> 检测到系统: $OS"
echo ""

# 检测 CPU 核心数（跨平台）
if [ "$OS" == "mac" ]; then
    NUM_CORES=$(sysctl -n hw.ncpu)
else
    NUM_CORES=$(nproc)
fi

# 检查系统依赖是否已安装
echo ">>> 检查系统依赖..."
if ! command -v cmake &> /dev/null || ! command -v git &> /dev/null; then
    echo "⚠ 警告: 系统依赖可能未安装。"
    echo "请先运行 'bash setup.sh' 安装所有依赖。"
    echo ""
    read -p "仍要继续? [y/N]: " CONTINUE
    if [[ ! "$CONTINUE" =~ ^[Yy]$ ]]; then
        echo "已中止。请先运行 'bash setup.sh'。"
        exit 1
    fi
else
    echo "✓ 系统依赖已安装"
fi
echo ""

echo ">>> 克隆 Arduous (Arduboy Libretro 核心)..."
if [ -d "arduous" ]; then
    echo "arduous 目录已存在，拉取最新更改..."
    cd arduous
    git pull
else
    git clone https://github.com/libretro/arduous.git
    cd arduous
fi

echo ">>> 克隆 simavr 依赖..."
if [ -d "simavr/.git" ]; then
    echo "simavr 已克隆，切换到指定版本..."
    cd simavr
    git fetch --unshallow 2>/dev/null || git fetch origin
    git checkout 2f136762ea1e9d7fdd84413c09503ae9920b42cc
    cd ..
else
    echo "从 GitHub 克隆 simavr（完整克隆以获取特定提交）..."
    rm -rf simavr
    git clone https://github.com/buserror/simavr.git simavr
    cd simavr
    git checkout 2f136762ea1e9d7fdd84413c09503ae9920b42cc
    cd ..
fi

echo ">>> 编译 Arduous 核心（启用性能优化）..."
mkdir -p build
cd build

# 配置 Release 模式和性能优化
# 添加 -DCMAKE_POLICY_VERSION_MINIMUM=3.5 以兼容 CMake 4.x
cmake -DCMAKE_BUILD_TYPE=Release \
      -DCMAKE_POLICY_VERSION_MINIMUM=3.5 \
      -DCMAKE_C_FLAGS='-O3 -march=native -mtune=native -ffast-math' \
      -DCMAKE_CXX_FLAGS='-O3 -march=native -mtune=native -ffast-math' \
      ..

# 使用多核编译（4 核心以提升性能）
make -j$NUM_CORES

echo ">>> 编译完成！"

# 根据操作系统确定库文件扩展名
if [ "$OS" == "mac" ]; then
    LIB_EXT="dylib"
else
    LIB_EXT="so"
fi

echo "核心文件位于: $(pwd)/arduous_libretro.$LIB_EXT"

# 复制到 core 目录以便统一管理
echo ">>> 复制核心文件到 core/ 目录..."
mkdir -p ../../core
cp arduous_libretro.$LIB_EXT ../../core/
echo "核心文件已复制到: $(cd ../..; pwd)/core/arduous_libretro.$LIB_EXT"
