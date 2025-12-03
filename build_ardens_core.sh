#!/bin/bash
#
# 编译 Ardens libretro 核心（禁用时间域滤波版本）
# 这个版本关闭了 display.enable_filter，画面更清晰，无余辉效果
#

set -e  # 遇到错误立即退出

# 检测操作系统
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS="mac"
else
    echo "不支持的操作系统: $OSTYPE"
    exit 1
fi

echo "=========================================="
echo "编译 Ardens Libretro 核心"
echo "版本: 禁用时间域滤波（更清晰的画面）"
echo "检测到系统: $OS"
echo "=========================================="
echo ""

# 获取当前目录
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# 检查并克隆 Ardens 仓库
if [ ! -d "Ardens" ]; then
    echo "Ardens 目录不存在，正在克隆仓库..."
    git clone https://github.com/tiberiusbrown/Ardens.git
    echo "✓ Ardens 仓库克隆完成"
else
    echo "✓ Ardens 目录已存在"
fi

# 进入 Ardens 源码目录
echo "进入 Ardens 源码目录..."
cd Ardens

# 更新子模块
echo ""
echo "初始化并更新 Git 子模块..."
git submodule update --init --recursive
echo "✓ 子模块更新完成"

# 清理旧的构建
echo "清理旧的构建目录..."
rm -rf build_libretro
mkdir -p build_libretro

# 配置 CMake（带性能优化）
echo ""
echo "配置 CMake（启用性能优化）..."

# 检测 CPU 核心数（跨平台）
if [ "$OS" == "mac" ]; then
    NUM_CORES=$(sysctl -n hw.ncpu)
else
    NUM_CORES=$(nproc)
fi

# 针对树莓派和 Mac 的优化编译参数
if [ "$OS" == "linux" ]; then
    # 树莓派 ARM64 优化（并行 LTO）
    OPTIMIZATION_FLAGS="-O3 -march=native -mtune=native -ffast-math -flto=$NUM_CORES"
else
    # Mac 优化
    OPTIMIZATION_FLAGS="-O3 -march=native -mtune=native -ffast-math"
fi

cmake -B build_libretro \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_C_FLAGS="$OPTIMIZATION_FLAGS" \
    -DCMAKE_CXX_FLAGS="$OPTIMIZATION_FLAGS" \
    -DCMAKE_POLICY_VERSION_MINIMUM=3.5 \
    -DARDENS_LLVM=OFF \
    -DARDENS_DEBUGGER=OFF \
    -DARDENS_PLAYER=OFF \
    -DARDENS_FLASHCART=OFF \
    -DARDENS_LIBRETRO=ON \
    -DARDENS_DIST=OFF \
    -DARDENS_BENCHMARK=OFF \
    -DARDENS_CYCLES=OFF

# 编译
echo ""
echo "开始编译（使用 $NUM_CORES 个核心）..."
cmake --build build_libretro --config Release -j$NUM_CORES

# 返回项目根目录
cd "$SCRIPT_DIR"

# 复制到 core 目录（根据系统选择不同的文件扩展名）
echo ""
echo "复制核心文件到 core/ 目录..."
mkdir -p core

# 根据操作系统确定库文件扩展名
if [ "$OS" == "mac" ]; then
    LIB_EXT="dylib"
else
    LIB_EXT="so"
fi

cp Ardens/build_libretro/ardens_libretro.$LIB_EXT core/

echo ""
echo "=========================================="
echo "✓ 编译完成！"
echo "核心文件: core/ardens_libretro.$LIB_EXT"
echo "=========================================="
echo ""
echo "修改说明："
echo "  - 关闭了时间域滤波（enable_filter = false）"
echo "  - 画面更清晰，无余辉效果"
echo "  - 类似 Arduous 的渲染方式"
echo ""
echo "性能优化："
echo "  - 编译优化级别: O3"
echo "  - 针对当前 CPU 架构优化: -march=native -mtune=native"
echo "  - 快速数学运算: -ffast-math"
if [ "$OS" == "linux" ]; then
    echo "  - 链接时优化 (LTO): -flto"
fi
echo ""
