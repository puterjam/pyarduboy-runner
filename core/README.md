# Core 目录

此目录用于存放编译好的 `arduous_libretro` 核心文件。

## 支持的平台

- **Linux (ARM)**: `arduous_libretro.so` - 树莓派等 ARM 设备
- **Linux (x86_64)**: `arduous_libretro.so` - PC Linux
- **Windows**: `arduous_libretro.dll` - Windows PC
- **macOS**: `arduous_libretro.dylib` - Mac

## 编译核心

### 自动编译（推荐）

在项目根目录运行：

```bash
./install.sh
```

这会自动编译并复制核心文件到此目录。

### 手动编译

```bash
# 从项目根目录
cd arduous
mkdir -p build && cd build

# 配置（Release 模式，性能优化）
cmake -DCMAKE_BUILD_TYPE=Release \
      -DCMAKE_C_FLAGS='-O3 -march=native -mtune=native -ffast-math' \
      -DCMAKE_CXX_FLAGS='-O3 -march=native -mtune=native -ffast-math' \
      ..

# 编译（使用 4 核）
make -j4

# 复制到 core 目录
cp arduous_libretro.so ../../core/
```

## 编译优化参数说明

- `-O3`: 最高优化级别
- `-march=native`: 针对当前 CPU 架构优化
- `-mtune=native`: 针对当前 CPU 调优
- `-ffast-math`: 快速数学运算（牺牲一些精度）
- `make -j4`: 使用 4 核并行编译

## 验证核心文件

```bash
# 检查文件是否存在
ls -lh arduous_libretro.so

# 应该看到类似输出：
# -rwxr-xr-x 1 pi pi 220K Nov 29 12:00 arduous_libretro.so
```

## 使用核心

在 Python 代码中：

```python
from pyarduboy import PyArduboy

arduboy = PyArduboy(
    core_path="./core/arduous_libretro.so",  # 指向此目录的核心文件
    game_path="./roms/game.hex"
)
arduboy.run()
```

## 跨平台编译

如果要为其他平台编译核心，需要使用交叉编译工具链。

### 在 PC 上为树莓派编译

```bash
# 安装交叉编译工具
sudo apt-get install gcc-arm-linux-gnueabihf g++-arm-linux-gnueabihf

# 配置 CMake
cmake -DCMAKE_SYSTEM_NAME=Linux \
      -DCMAKE_SYSTEM_PROCESSOR=arm \
      -DCMAKE_C_COMPILER=arm-linux-gnueabihf-gcc \
      -DCMAKE_CXX_COMPILER=arm-linux-gnueabihf-g++ \
      ..
```

## 故障排除

### 核心加载失败

1. 检查文件权限：`chmod +x arduous_libretro.so`
2. 检查依赖库：`ldd arduous_libretro.so`
3. 确保是正确的平台版本（ARM vs x86）

### 性能问题

1. 确保使用 Release 模式编译
2. 启用所有优化参数（-O3, -march=native 等）
3. 使用多核编译（make -j4）

## 更多信息

- [arduous GitHub](https://github.com/libretro/arduous)
- [LibRetro 文档](https://docs.libretro.com/)
