# 树莓派 Arduboy 模拟器

在树莓派上运行 Arduboy 游戏的完整硬件模拟器。

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.7+-green.svg)
![Platform](https://img.shields.io/badge/platform-Raspberry%20Pi-red.svg)

## ✨ 特性

- 🎮 **完整硬件支持** - OLED 显示屏、USB 键盘、音频输出
- 🖥️ **真实 OLED 显示** - 支持 SSD1309 SPI 显示屏（128x64）
- ⌨️ **物理键盘输入** - 使用 evdev 直接读取键盘事件
- 🔊 **ALSA 音频** - 支持 HDMI/耳机孔音频输出
- ⚡ **高性能** - 优化后稳定 60 FPS
- 🔧 **插件化架构** - 可自定义视频、音频、输入驱动
- 🎯 **即插即用** - 简单的 Python API

## 📋 硬件要求

| 组件 | 规格 | 备注 |
|------|------|------|
| **树莓派** | Pi 4/5 推荐 | Pi 3 也可运行，性能稍低 |
| **OLED 显示屏** | SSD1309, 128x64, SPI | 用于游戏显示 |
| **USB 键盘** | 任意标准键盘 | 用于游戏控制 |
| **音频输出** | HDMI 或 3.5mm | 可选，用于声音 |
| **存储空间** | 500MB+ | 用于依赖和游戏 |

## 🚀 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/your-username/arduboy_pi.git
cd arduboy_pi
```

### 2. 安装依赖

```bash
# 安装系统依赖
sudo apt-get update
sudo apt-get install -y build-essential cmake python3-pip \
                        python3-evdev python3-alsaaudio

# 安装 Python 库
pip3 install -r requirements.txt
```

### 3. 编译核心

```bash
chmod +x build_core.sh
./build_core.sh
```

### 4. 连接硬件

**OLED 显示屏（SPI 接口）：**
```
树莓派          OLED
Pin 19 (MOSI) → SDA
Pin 23 (SCLK) → SCL
Pin 24 (CE0)  → CS
Pin 22 (GPIO25) → DC
Pin 13 (GPIO27) → RST
Pin 1  (3.3V) → VCC
Pin 6  (GND)  → GND
```

**启用 SPI：**
```bash
sudo raspi-config
# Interface Options → SPI → Yes
sudo reboot
```

### 5. 运行游戏

```bash
sudo python3 run_arduboy.py roms/your_game.hex
```

## 🎮 控制说明

| 按键 | 功能 |
|------|------|
| **W / S / A / D** | 方向键 |
| **K** | A 按钮 |
| **J** | B 按钮 |
| **R** | Reset（重置游戏）|
| **Ctrl+C** | 退出 |

## 📁 项目结构

```
arduboy_pi/
├── pyarduboy/              # Python 库
│   ├── core.py             # 核心类
│   ├── libretro_bridge.py  # LibRetro 桥接
│   └── drivers/            # 驱动插件
│       ├── video/          # 视频驱动
│       │   └── luma_oled.py
│       ├── audio/          # 音频驱动
│       │   ├── alsa.py     # ALSA 音频
│       │   └── null.py
│       └── input/          # 输入驱动
│           └── evdev_keyboard.py
├── core/                   # LibRetro 核心
│   └── arduous_libretro.so
├── roms/                   # 游戏文件
├── run_arduboy.py          # 主程序
├── test_*.py               # 测试脚本
└── docs/                   # 文档
    ├── QUICKSTART.md       # 快速开始
    ├── AUDIO_SETUP.md      # 音频设置
    └── ARCHITECTURE.md     # 架构文档
```

## 🔧 配置

### 音频配置

默认使用 ALSA 音频驱动。如果遇到问题：

```bash
# 测试音频
speaker-test -t wav -c 2

# 调整音量
alsamixer

# 详细配置见文档
cat docs/AUDIO_SETUP.md
```

### 键盘配置

自动检测带 LED 的主键盘设备。如果需要手动指定：

```python
# 在 run_arduboy.py 中修改
input_driver = EvdevKeyboardDriver(device_path="/dev/input/event5")
```

## 📖 文档

- [快速开始指南](docs/QUICKSTART.md) - 5 分钟上手教程
- [音频设置指南](docs/AUDIO_SETUP.md) - ALSA 音频配置
- [架构文档](docs/ARCHITECTURE.md) - 系统设计说明
- [项目总结](docs/PROJECT_SUMMARY.md) - 完整技术文档

## 🎯 性能

| 指标 | 数值 |
|------|------|
| **帧率** | 稳定 60 FPS |
| **音频延迟** | ~93ms (可调) |
| **内存占用** | ~50MB |
| **CPU 占用** | ~15% (Pi 4) |

## 🐛 常见问题

### 没有权限访问键盘

```bash
# 需要 root 权限
sudo python3 run_arduboy.py
```

### OLED 无显示

```bash
# 检查 SPI 是否启用
ls /dev/spidev*

# 检查接线
# 确认使用正确的 GPIO 引脚
```

### 音频没有声音

```bash
# 检查音量
alsamixer

# 测试音频输出
speaker-test -t wav -c 2

# 查看详细配置
cat docs/AUDIO_SETUP.md
```

## 🛠️ 开发

### 测试工具

```bash
# 测试键盘输入
sudo python3 test_keyboard.py

# 测试原始 evdev 事件
sudo python3 test_evdev_raw.py

# 列出所有输入设备
sudo python3 list_devices.py
```

### 自定义驱动

PyArduboy 支持插件化驱动：

```python
from pyarduboy import PyArduboy
from pyarduboy.drivers.video.luma_oled import LumaOLEDDriver
from pyarduboy.drivers.audio.alsa import AlsaAudioDriver
from pyarduboy.drivers.input.evdev_keyboard import EvdevKeyboardDriver

arduboy = PyArduboy(core_path="...", game_path="...")
arduboy.set_video_driver(LumaOLEDDriver(...))
arduboy.set_audio_driver(AlsaAudioDriver(...))
arduboy.set_input_driver(EvdevKeyboardDriver(...))
arduboy.run()
```

## 📜 许可证

MIT License

## 🙏 致谢

- [Arduboy](https://arduboy.com/) - 原始硬件和生态
- [Arduous](https://github.com/rossumur/arduous) - LibRetro 核心
- [libretro.py](https://github.com/JesseTG/libretro.py) - Python 绑定
- [Luma.OLED](https://github.com/rm-hull/luma.oled) - OLED 驱动库

## 📧 联系

- **作者**: PuterJam
- **Email**: puterjam@gmail.com
- **项目**: [GitHub](https://github.com/your-username/arduboy_pi)

---

**享受游戏！** 🎮✨
