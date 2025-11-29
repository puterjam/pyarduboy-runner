# PyArduboy - Arduboy 模拟器 Python 库

在树莓派上运行 Arduboy 游戏的 Python 库，支持 OLED 显示屏输出。

## 项目特点

- 🎮 **完整硬件支持**：OLED 显示屏、USB 键盘输入、音频输出
- 🔌 **插件式驱动系统**：支持自定义视频、音频、输入驱动
- 📺 **真实 OLED 显示**：支持 SSD1309 SPI 显示屏（128x64）
- ⌨️ **物理键盘输入**：基于 evdev 的低延迟键盘支持
- 🔊 **ALSA 音频**：支持 HDMI 和耳机孔音频输出
- 🚀 **高性能**：优化后稳定 60 FPS
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
│       │   ├── luma_oled.py    # Luma.OLED 驱动（SPI/I2C）
│       │   └── null.py         # 空驱动（测试用）
│       ├── audio/               # 音频驱动
│       │   ├── alsa.py         # ALSA 音频驱动 ⭐ NEW
│       │   └── null.py         # 空驱动
│       └── input/               # 输入驱动
│           ├── evdev_keyboard.py  # Evdev 键盘驱动 ⭐ NEW
│           └── base.py         # 输入驱动基类
├── examples/                     # 示例代码
│   ├── basic_demo.py            # 基础示例
│   ├── oled_demo.py             # OLED 显示示例
│   └── custom_driver_demo.py    # 自定义驱动示例
├── core/                        # 编译好的核心文件目录
├── roms/                        # 游戏 ROM 目录
├── docs/                        # 文档
│   ├── QUICKSTART.md           # 快速开始指南
│   ├── AUDIO_SETUP.md          # 音频设置指南 ⭐ NEW
│   └── PROJECT_SUMMARY.md      # 项目总结
├── run_arduboy.py               # 完整硬件模拟器主程序 ⭐ NEW
├── test_keyboard.py             # 键盘测试工具 ⭐ NEW
├── test_evdev_raw.py            # 原始输入测试 ⭐ NEW
├── list_devices.py              # 设备列表工具 ⭐ NEW
├── venv/                        # Python 虚拟环境
└── requirements.txt             # Python 依赖
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
    python3-evdev \
    python3-alsaaudio
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

#### 4. 配置 SPI（用于 OLED）

```bash
# 启用 SPI
sudo raspi-config
# 选择：Interface Options -> SPI -> Yes

# 重启
sudo reboot

# 检查 SPI 设备
ls /dev/spidev*
```

## 快速开始

### 完整硬件模拟器（推荐）

使用物理 OLED、USB 键盘和音频的完整体验：

```bash
# 需要 root 权限访问键盘设备
sudo python3 run_arduboy.py roms/your_game.hex
```

**硬件连接（SSD1309 SPI OLED）：**
```
树莓派引脚        OLED 模块
Pin 19 (MOSI)   → SDA/MOSI
Pin 23 (SCLK)   → SCL/SCK
Pin 24 (CE0)    → CS
Pin 22 (GPIO25) → DC
Pin 13 (GPIO27) → RST
Pin 1  (3.3V)   → VCC
Pin 6  (GND)    → GND
```

**控制按键：**
- W/S/A/D - 方向键
- K - A 按钮
- J - B 按钮
- R - Reset（重置游戏）
- Ctrl+C - 退出

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

### 物理键盘（evdev）

主程序 `run_arduboy.py` 使用的按键映射：

- **W / S / A / D** - 方向键（上/下/左/右）
- **K** - A 按钮
- **J** - B 按钮
- **R** - Reset（重新加载游戏）
- **Ctrl+C** - 退出

### 测试工具

```bash
# 测试键盘输入
sudo python3 test_keyboard.py

# 查看原始输入事件
sudo python3 test_evdev_raw.py

# 列出所有输入设备
sudo python3 list_devices.py
```

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

### 键盘无法输入

```bash
# 需要 root 权限
sudo python3 run_arduboy.py

# 或添加用户到 input 组
sudo usermod -a -G input $USER
# 重新登录后生效
```

### OLED 无显示

```bash
# 检查 SPI 是否启用
ls /dev/spidev*

# 应该看到：/dev/spidev0.0  /dev/spidev0.1

# 检查 luma.oled 安装
pip3 install luma.oled
```

### 音频没有声音

```bash
# 检查音量
alsamixer

# 测试音频
speaker-test -t wav -c 2

# 详细配置见文档
cat docs/AUDIO_SETUP.md
```

### libretro.py 未找到

```bash
pip3 install libretro.py
```

### 核心加载失败

检查核心文件是否存在：

```bash
ls -lh core/arduous_libretro.so
```

如果不存在，运行 `./build_core.sh` 重新编译。

### 性能问题（帧率低）

1. 确保使用 Release 模式编译核心
2. 音频缓冲区已优化（period_size=4096）
3. 使用非阻塞音频模式（已默认启用）
4. 如果仍然卡顿，禁用音频：编辑 `run_arduboy.py` 使用 `NullAudioDriver()`

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