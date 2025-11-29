# PyArduboy 快速开始

5 分钟快速上手 PyArduboy！

## 前提条件

- ✅ 树莓派（已安装 Raspberry Pi OS）
- ✅ OLED 显示屏（SSD1309，SPI 接口）
- ✅ USB 键盘（用于游戏控制）
- ✅ 音频输出（HDMI 或 3.5mm 耳机孔，可选）
- ✅ Arduboy 游戏 (.hex 文件)

## 一、安装依赖

```bash
# 1. 系统依赖
sudo apt-get update
sudo apt-get install -y build-essential cmake python3-pip

# 2. 核心 Python 库
pip3 install -r requirements.txt

# 或者手动安装：
pip3 install libretro.py pillow numpy

# 3. OLED 支持（SPI 显示屏）
pip3 install luma.oled

# 4. 键盘输入支持
sudo apt-get install python3-evdev

# 5. 音频支持（可选）
sudo apt-get install python3-alsaaudio

# 6. 启用 SPI（用于 OLED）
sudo raspi-config
# 选择：Interface Options -> SPI -> Yes
sudo reboot
```

## 二、编译核心

```bash
cd /home/pi/workspace/arduboy_pi

# 使用提供的编译脚本
chmod +x build_core.sh
./build_core.sh
```

或者手动编译：

```bash
cd core
mkdir -p build && cd build

# 配置（Release 模式，性能优化）
cmake -DCMAKE_BUILD_TYPE=Release \
      -DCMAKE_C_FLAGS='-O3 -march=native -mtune=native -ffast-math' \
      -DCMAKE_CXX_FLAGS='-O3 -march=native -mtune=native -ffast-math' \
      ..

# 编译（多核加速）
make -j4

# 复制到项目根目录
cp arduous_libretro.so ../../
```

验证编译结果：

```bash
ls -lh core/arduous_libretro.so
# 应该看到一个 .so 文件
```

## 三、获取游戏

### 方式 1：下载免费游戏

访问 [itch.io](https://itch.io/games/tag-arduboy) 下载 `.hex` 文件。

### 方式 2：使用示例游戏

```bash
# 如果 roms 目录有游戏，直接使用
ls roms/
```

将游戏文件放到 `roms/` 目录：

```bash
cp /path/to/your/game.hex roms/
```

## 四、运行完整模拟器

### 主程序：完整硬件支持

使用物理 OLED 显示、USB 键盘和音频：

```bash
# 需要 root 权限访问键盘设备
sudo python3 run_arduboy.py roms/your_game.hex
```

**控制按键**（物理 USB 键盘）：
- **W / S / A / D** - 方向键（上/下/左/右）
- **K** - A 按钮
- **J** - B 按钮
- **R** - Reset（重新加载游戏）
- **Ctrl+C** - 退出

应该看到输出：

```
✓ OLED video driver configured (SPI)
✓ Audio driver configured (ALSA)
✓ Input driver configured (evdev keyboard)

Controls (Physical Keyboard):
  W / S / A / D  - Direction
  J              - A Button
  K              - B Button
  R              - Reset (Reload Game)

Starting Arduboy emulation...
Frame 300: FPS=59.8
```

### 硬件连接

**OLED 显示屏（SSD1309，SPI）：**
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

**音频输出：**
- HDMI 音频：自动输出到 HDMI 显示器
- 3.5mm 耳机孔：插入耳机或音箱
- 调整音量：`alsamixer`

### 测试示例（可选）

**示例 1：测试键盘输入**
```bash
sudo python3 test_keyboard.py
# 按键测试，验证键盘映射
```

**示例 2：测试原始输入事件**
```bash
sudo python3 test_evdev_raw.py
# 查看底层 evdev 事件
```

**示例 3：列出所有输入设备**
```bash
sudo python3 list_devices.py
# 显示所有输入设备详情
```

## 五、编写你的第一个程序

创建文件 `my_game.py`：

```python
#!/usr/bin/env python3
import sys
sys.path.insert(0, '..')

from pyarduboy import PyArduboy
from pyarduboy.drivers.video.luma_oled import LumaOLED32Driver
from pyarduboy.drivers.input.keyboard import KeyboardInputDriver

# 创建实例
arduboy = PyArduboy(
    core_path="../arduous_libretro.so",
    game_path="../roms/your_game.hex",
    target_fps=60
)

# 设置驱动
arduboy.set_video_driver(LumaOLED32Driver())
arduboy.set_input_driver(KeyboardInputDriver())

# 运行
print("Starting game...")
arduboy.run()
```

运行：

```bash
chmod +x my_game.py
python3 my_game.py
```

## 六、OLED 硬件连接

如果使用 I2C OLED 显示屏：

```
树莓派引脚        OLED 模块
Pin 3  (GPIO2)  → SDA
Pin 5  (GPIO3)  → SCL
Pin 1  (3.3V)   → VCC
Pin 6  (GND)    → GND
```

验证连接：

```bash
# 检查 I2C 设备
i2cdetect -y 1

# 应该看到设备地址（通常是 0x3C）
#      0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f
# 00:          -- -- -- -- -- -- -- -- -- -- -- -- --
# 10: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
# 20: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
# 30: -- -- -- -- -- -- -- -- -- -- -- -- 3c -- -- --
```

## 七、常见问题快速解决

### 问题 1：libretro.py not found

```bash
pip3 install libretro.py
```

### 问题 2：Core file not found

```bash
# 确保核心文件存在
ls -lh arduous_libretro.so

# 如果不存在，回到第二步重新编译
```

### 问题 3：OLED 无显示

```bash
# 1. 检查 I2C
i2cdetect -y 1

# 2. 检查接线
# 3. 检查设备类型（ssd1305 或 ssd1306）

# 4. 测试 OLED
python3 << EOF
from luma.core.interface.serial import i2c
from luma.oled.device import ssd1305
from PIL import Image, ImageDraw

serial = i2c(port=1, address=0x3C)
device = ssd1305(serial, width=128, height=32)

img = Image.new('1', (128, 32))
draw = ImageDraw.Draw(img)
draw.text((10, 10), "Hello!", fill=1)
device.display(img)
EOF
```

### 问题 4：Game file not found

确保游戏文件路径正确：

```bash
# 检查文件是否存在
ls -lh roms/your_game.hex

# 或使用绝对路径
arduboy = PyArduboy(
    core_path="/home/pi/workspace/arduboy_pi/arduous_libretro.so",
    game_path="/home/pi/workspace/arduboy_pi/roms/your_game.hex"
)
```

### 问题 5：帧率太低

```bash
# 1. 确保使用 Release 模式编译
# 2. 检查 CPU 负载
top

# 3. 降低目标帧率
arduboy = PyArduboy(..., target_fps=30)

# 4. 关闭其他程序
```

## 八、下一步

✅ **恭喜！** 你已经成功运行了 PyArduboy！

接下来可以：

1. 📖 阅读完整文档：[README_NEW.md](README_NEW.md)
2. 🏗️ 了解架构设计：[ARCHITECTURE.md](ARCHITECTURE.md)
3. 🔧 创建自定义驱动：参考 [custom_driver_demo.py](examples/custom_driver_demo.py)
4. 🎮 下载更多游戏：[itch.io](https://itch.io/games/tag-arduboy)
5. 💡 集成到你的项目：PyArduboy 可以作为库嵌入

## 九、快速参考

### 最小代码示例

```python
from pyarduboy import PyArduboy

PyArduboy("./arduous_libretro.so", "./game.hex").run()
```

### 完整代码示例

```python
from pyarduboy import PyArduboy
from pyarduboy.drivers.video.luma_oled import LumaOLED32Driver
from pyarduboy.drivers.audio.null import NullAudioDriver
from pyarduboy.drivers.input.keyboard import KeyboardInputDriver

arduboy = PyArduboy(
    core_path="./arduous_libretro.so",
    game_path="./game.hex",
    target_fps=60
)

arduboy.set_video_driver(LumaOLED32Driver(device_type='ssd1305'))
arduboy.set_audio_driver(NullAudioDriver())
arduboy.set_input_driver(KeyboardInputDriver())

arduboy.run()
```

### 目录结构

```
arduboy_pi/
├── arduous_libretro.so     # 编译好的核心
├── pyarduboy/              # Python 库
├── examples/               # 示例代码
├── roms/                   # 游戏文件
└── README_NEW.md           # 完整文档
```

### 有用的命令

```bash
# 编译核心（在 arduous_rebuild/build 目录）
cmake .. && make -j4 && cp arduous_libretro.so ../../

# 检查 I2C
i2cdetect -y 1

# 运行示例
cd examples && python3 oled_demo.py ../roms/game.hex

# 查看日志
python3 your_script.py 2>&1 | tee log.txt
```

## 获取帮助

- 📖 文档：查看 `README_NEW.md`、`ARCHITECTURE.md`
- 💬 问题：创建 GitHub Issue
- 📧 联系：见项目 README

---

**祝你玩得开心！** 🎮
