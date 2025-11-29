# PyArduboy - Arduboy 模拟器 Python 库

在树莓派上运行 Arduboy 游戏的 Python 库，支持 OLED 显示屏输出。

## 项目特点

- 🎮 **易用的 API**：简单的 Python 接口，几行代码即可运行 Arduboy 游戏
- 🔌 **插件式驱动系统**：支持自定义视频、音频、输入驱动
- 📺 **OLED 支持**：原生支持 Luma.OLED 库，适配常见 OLED 显示屏
- 🚀 **高性能**：基于 arduous_libretro 核心，优化的模拟器性能
- 🛠️ **易扩展**：清晰的架构设计，便于扩展到其他平台

## 目录结构

```
arduboy_pi/
├── pyarduboy/                    # 核心 Python 库
│   ├── __init__.py              # 库初始化
│   ├── core.py                  # PyArduboy 核心类
│   ├── libretro_bridge.py       # LibRetro 桥接层
│   └── drivers/                 # 驱动插件系统
│       ├── video/               # 视频驱动
│       │   ├── luma_oled.py    # Luma.OLED 驱动
│       │   └── null.py         # 空驱动（测试用）
│       ├── audio/               # 音频驱动
│       │   └── null.py         # 空驱动
│       └── input/               # 输入驱动
│           └── keyboard.py     # 键盘驱动
├── examples/                     # 示例代码
│   ├── basic_demo.py            # 基础示例
│   ├── oled_demo.py             # OLED 显示示例
│   └── custom_driver_demo.py    # 自定义驱动示例
├── arduous/                     # arduous_libretro git 子模块
├── core/                        # 编译好的核心文件目录
├── roms/                        # 游戏 ROM 目录
├── venv/                        # Python 虚拟环境
└── tests/                       # 单元测试
```

## 模块流程

```
┌─────────────┐
│   Demo      │  用户应用程序
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  PyArduboy  │  核心 API（core.py）
└──────┬──────┘
       │
       ├──────────┐
       │          │
       ▼          ▼
┌──────────┐  ┌────────────┐
│  驱动插件  │  │ LibRetro   │  桥接层（libretro_bridge.py）
│  (Drivers)│  │  Bridge    │
└──────────┘  └──────┬─────┘
                     │
                     ▼
              ┌─────────────┐
              │  arduous_   │  C++ 模拟器核心
              │  libretro   │
              └─────────────┘
```

## 游戏执行流程

1. **Demo 加载游戏** → 指定游戏 ROM 文件路径
2. **PyArduboy 提供驱动** → 设置视频/音频/输入驱动
3. **LibRetro Bridge 桥接** → 连接 Python 和 C++ 核心
4. **arduous_libretro 模拟** → 运行 AVR 指令模拟

## 快速安装

### 方式 1：一键安装（推荐）

```bash
# 克隆项目
cd /home/pi/workspace
git clone <your-repo-url> arduboy_pi
cd arduboy_pi

# 运行一键安装脚本
chmod +x install.sh
./install.sh

# 设置 Python 虚拟环境
chmod +x setup_venv.sh
./setup_venv.sh
```

### 方式 2：手动安装

#### 1. 系统依赖

```bash
sudo apt-get update
sudo apt-get install -y \
    build-essential \
    cmake \
    python3-dev \
    python3-pip \
    python3-venv \
    i2c-tools \
    libi2c-dev
```

#### 2. 创建虚拟环境并安装 Python 依赖

```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

#### 3. 编译 arduous_libretro 核心

```bash
# 克隆子模块（如果还没有）
git clone https://github.com/libretro/arduous.git

cd arduous
mkdir -p build && cd build

# 配置构建（Release 模式，性能优化）
cmake -DCMAKE_BUILD_TYPE=Release \
      -DCMAKE_C_FLAGS='-O3 -march=native -mtune=native -ffast-math' \
      -DCMAKE_CXX_FLAGS='-O3 -march=native -mtune=native -ffast-math' \
      ..

# 编译（使用 4 核加速）
make -j4

# 复制到 core 目录
mkdir -p ../../core
cp arduous_libretro.so ../../core/
```

#### 4. 配置 I2C（如果使用 OLED）

```bash
# 启用 I2C
sudo raspi-config
# 选择：Interfacing Options -> I2C -> Enable

# 重启
sudo reboot

# 检查 I2C 设备
i2cdetect -y 1
```

## 快速开始

### 基础示例（无显示输出）

```python
from pyarduboy import PyArduboy
from pyarduboy.drivers.video.null import NullVideoDriver

# 创建实例
arduboy = PyArduboy(
    core_path="./core/arduous_libretro.so",
    game_path="./roms/2048.hex"
)

# 设置驱动
arduboy.set_video_driver(NullVideoDriver())

# 运行游戏（600 帧后自动停止）
arduboy.run(max_frames=600)
```

### OLED 显示示例

```python
from pyarduboy import PyArduboy
from pyarduboy.drivers.video.luma_oled import LumaOLED32Driver
from pyarduboy.drivers.input.keyboard import KeyboardInputDriver

# 创建实例
arduboy = PyArduboy(
    core_path="./core/arduous_libretro.so",
    game_path="./roms/2048.hex"
)

# 设置 OLED 驱动（128x32 显示屏）
video_driver = LumaOLED32Driver(
    device_type='ssd1305',  # 或 'ssd1306'
    interface='i2c',
    rotate=2
)
arduboy.set_video_driver(video_driver)

# 设置键盘输入
arduboy.set_input_driver(KeyboardInputDriver())

# 运行游戏
arduboy.run()
```

### 运行预置示例

```bash
# 激活虚拟环境
source venv/bin/activate

# 基础示例（无显示）
cd examples
python basic_demo.py ../roms/your_game.hex

# OLED 显示示例
python oled_demo.py ../roms/your_game.hex

# 自定义驱动示例（保存帧为图片）
python custom_driver_demo.py ../roms/your_game.hex

# 退出虚拟环境
deactivate
```

## 控制按键

默认键盘映射：

- **W** - 上
- **S** - 下
- **A** - 左
- **D** - 右
- **H** - A 按钮
- **J** - B 按钮
- **Enter** - Start
- **Space** - Select
- **Ctrl+C** - 退出

## 自定义驱动开发

PyArduboy 使用插件式驱动系统，可以轻松创建自定义驱动。

### 创建自定义视频驱动

```python
import numpy as np
from pyarduboy import VideoDriver

class MyCustomDriver(VideoDriver):
    """自定义视频驱动"""

    def init(self, width: int, height: int) -> bool:
        """初始化驱动"""
        self._width = width
        self._height = height
        self._running = True
        # 你的初始化代码
        return True

    def render(self, frame_buffer: np.ndarray) -> None:
        """渲染一帧"""
        # frame_buffer 是 (height, width, 3) 的 RGB 数组
        # 在这里实现你的渲染逻辑
        pass

    def close(self) -> None:
        """关闭驱动"""
        self._running = False
        # 清理资源

    @property
    def is_running(self) -> bool:
        return self._running
```

### 使用自定义驱动

```python
from pyarduboy import PyArduboy

arduboy = PyArduboy(
    core_path="./core/arduous_libretro.so",
    game_path="./game.hex"
)

# 使用自定义驱动
arduboy.set_video_driver(MyCustomDriver())
arduboy.run()
```

## API 文档

### PyArduboy 类

主要接口类，用于管理游戏运行。

```python
PyArduboy(
    core_path: str,      # libretro 核心路径
    game_path: str,      # 游戏 ROM 路径
    target_fps: int = 60 # 目标帧率
)
```

**方法：**

- `set_video_driver(driver)` - 设置视频驱动
- `set_audio_driver(driver)` - 设置音频驱动
- `set_input_driver(driver)` - 设置输入驱动
- `run(max_frames=None)` - 运行游戏主循环
- `stop()` - 停止运行
- `cleanup()` - 清理资源

**属性：**

- `is_running` - 是否正在运行
- `frame_count` - 当前帧数
- `fps` - 实际帧率

### 驱动基类

所有驱动必须继承以下基类：

- `VideoDriver` - 视频驱动基类
- `AudioDriver` - 音频驱动基类
- `InputDriver` - 输入驱动基类

## 获取 Arduboy 游戏

- [itch.io - Arduboy 游戏](https://itch.io/games/tag-arduboy)
- [Arduboy 官方网站](https://www.arduboy.com/)
- [Arduboy 社区论坛](https://community.arduboy.com/)
- [ArduboyCollection](https://github.com/eried/ArduboyCollection)

游戏文件格式为 `.hex` 文件。

## 故障排除

### libretro.py 未找到

```bash
pip3 install libretro.py
```

### OLED 显示异常

1. 检查 I2C 是否启用：`i2cdetect -y 1`
2. 确认设备地址（通常是 0x3C）
3. 检查 luma.oled 安装：`pip3 install luma.oled`

### 核心加载失败

检查核心文件是否存在：

```bash
ls -lh arduous_libretro.so
```

如果不存在，重新编译核心。

### 性能问题

1. 确保使用 Release 模式编译核心
2. 启用 JIT 优化（默认已启用）
3. 降低目标帧率：`PyArduboy(..., target_fps=30)`

## 许可证

本项目基于开源许可证发布。

- PyArduboy 库：MIT License
- arduous_libretro 核心：遵循原项目许可证

## 贡献

欢迎贡献代码、报告问题或提出建议！

## 相关链接

- [arduous_libretro](https://github.com/libretro/arduous)
- [libretro.py](https://github.com/JesseTG/libretro.py)
- [Luma.OLED](https://github.com/rm-hull/luma.oled)
- [Arduboy](https://www.arduboy.com/)

