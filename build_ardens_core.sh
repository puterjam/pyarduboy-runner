#!/bin/bash
#
# 编译 Ardens libretro 核心（禁用时间域滤波版本）
# 这个版本关闭了 display.enable_filter，画面更清晰，无余辉效果
#

set -e  # 遇到错误立即退出

echo "=========================================="
echo "编译 Ardens Libretro 核心"
echo "版本: 禁用时间域滤波（更清晰的画面）"
echo "=========================================="
echo ""

# 获取当前目录
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# 进入 Ardens 源码目录
echo "进入 Ardens 源码目录..."
cd Ardens

# 清理旧的构建
echo "清理旧的构建目录..."
rm -rf build_libretro
mkdir -p build_libretro

# 配置 CMake
echo ""
echo "配置 CMake..."
cmake -B build_libretro \
    -DCMAKE_BUILD_TYPE=Release \
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
echo "开始编译..."
cmake --build build_libretro --config Release -j$(sysctl -n hw.ncpu)

# 返回项目根目录
cd "$SCRIPT_DIR"

# 复制到 core 目录
echo ""
echo "复制核心文件到 core/ 目录..."
mkdir -p core
cp Ardens/build_libretro/ardens_libretro.dylib core/

echo ""
echo "=========================================="
echo "✓ 编译完成！"
echo "核心文件: core/ardens_libretro.dylib"
echo "=========================================="
echo ""
echo "修改说明："
echo "  - 关闭了时间域滤波（enable_filter = false）"
echo "  - 画面更清晰，无余辉效果"
echo "  - 类似 Arduous 的渲染方式"
echo ""
