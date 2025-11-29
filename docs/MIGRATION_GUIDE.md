# PyArduboy 迁移指南

从旧版本 `run_arduboy.py` 迁移到新的 PyArduboy 库。

## 主要变化

### 旧版本（run_arduboy.py）

旧版本是一个单一的脚本文件，直接使用 libretro.py，不易复用和扩展：

```python
# 旧版本：run_arduboy.py
from libretro import SessionBuilder, ArrayVideoDriver
from drive.luma.ssd1305 import ssd1305

# 硬编码的配置
device = ssd1305(width=128, height=32, rotate=2)
builder = SessionBuilder()
builder.with_core("./arduous_libretro.so")
builder.with_content("./2048.hex")

# 复杂的主循环
while True:
    session.run()
    frame_data = bytes(video_driver._frame)
    # 手动处理 RGB565 转换
    # 手动裁剪画面
    # ...
```

**缺点：**
- 不易复用到其他项目
- 配置硬编码，不灵活
- 驱动无法更换
- 代码耦合度高

### 新版本（PyArduboy 库）

新版本是模块化的 Python 库，插件式驱动系统，易于集成和扩展：

```python
# 新版本：使用 PyArduboy 库
from pyarduboy import PyArduboy
from pyarduboy.drivers.video.luma_oled import LumaOLED32Driver
from pyarduboy.drivers.input.keyboard import KeyboardInputDriver

# 创建实例
arduboy = PyArduboy(
    core_path="./arduous_libretro.so",
    game_path="./game.hex"
)

# 设置驱动（可插拔）
arduboy.set_video_driver(LumaOLED32Driver(device_type='ssd1305'))
arduboy.set_input_driver(KeyboardInputDriver())

# 简洁的运行
arduboy.run()
```

**优点：**
- 清晰的 API，易于使用
- 插件式驱动，灵活扩展
- 可嵌入到其他项目
- 代码模块化，易于维护

## 迁移步骤

### 步骤 1：安装新库

确保 PyArduboy 库在 Python 路径中：

```bash
# 方式 1：添加到 PYTHONPATH
export PYTHONPATH="/home/pi/workspace/arduboy_pi:$PYTHONPATH"

# 方式 2：创建软链接
cd /usr/local/lib/python3.9/site-packages/
sudo ln -s /home/pi/workspace/arduboy_pi/pyarduboy pyarduboy

# 方式 3：安装为包（推荐）
cd /home/pi/workspace/arduboy_pi
pip3 install -e .  # 开发模式安装
```

### 步骤 2：更新代码

#### 旧代码示例：

```python
# old_code.py
from libretro import SessionBuilder, ArrayVideoDriver
import numpy as np
from PIL import Image

CORE_PATH = "./arduous_libretro.so"
GAME_PATH = "./game.hex"

builder = SessionBuilder()
builder.with_core(CORE_PATH)
builder.with_content(GAME_PATH)
# ... 复杂的设置 ...

video_driver = ArrayVideoDriver()
builder.with_video(video_driver)

session = builder.build()

with session:
    while True:
        session.run()
        # 手动处理帧数据
        frame_data = bytes(video_driver._frame)
        # RGB565 转换
        img_array = np.frombuffer(frame_data, dtype=np.uint16)
        # ...
```

#### 新代码示例：

```python
# new_code.py
from pyarduboy import PyArduboy
from pyarduboy.drivers.video.luma_oled import LumaOLED32Driver

CORE_PATH = "./arduous_libretro.so"
GAME_PATH = "./game.hex"

arduboy = PyArduboy(CORE_PATH, GAME_PATH)
arduboy.set_video_driver(LumaOLED32Driver())
arduboy.run()
```

### 步骤 3：自定义驱动迁移

如果你有自定义的显示逻辑，可以创建自定义驱动：

#### 旧版本自定义显示：

```python
# 在主循环中
while True:
    session.run()
    frame_data = bytes(video_driver._frame)

    # 自定义处理
    img = process_frame(frame_data)
    my_custom_display(img)
```

#### 新版本自定义驱动：

```python
from pyarduboy import VideoDriver
import numpy as np

class MyCustomDriver(VideoDriver):
    def init(self, width, height):
        self._width = width
        self._height = height
        self._running = True
        return True

    def render(self, frame_buffer):
        # frame_buffer 已经是 RGB888 格式
        # 直接使用你的自定义显示逻辑
        my_custom_display(frame_buffer)

    def close(self):
        self._running = False

    @property
    def is_running(self):
        return self._running

# 使用
arduboy.set_video_driver(MyCustomDriver())
```

### 步骤 4：输入处理迁移

#### 旧版本输入处理：

```python
# 复杂的输入管理
class InputStateManager:
    def __init__(self):
        self.buttons = {...}
    # 很多代码...

class KeyboardListener:
    # 线程管理
    # 终端设置
    # ...

input_state_manager = InputStateManager()
keyboard = KeyboardListener(input_state_manager)
```

#### 新版本输入处理：

```python
from pyarduboy.drivers.input.keyboard import KeyboardInputDriver

# 一行代码
arduboy.set_input_driver(KeyboardInputDriver())
```

## 对比表

| 特性 | 旧版本 (run_arduboy.py) | 新版本 (PyArduboy) |
|------|------------------------|-------------------|
| 代码行数 | ~330 行 | ~50 行（使用时） |
| 可复用性 | ❌ 难以复用 | ✅ 易于集成 |
| 驱动切换 | ❌ 需要修改代码 | ✅ 插件式切换 |
| OLED 支持 | ✅ 仅 SSD1305 | ✅ 多种型号 |
| 输入支持 | ✅ 键盘 | ✅ 可扩展多种输入 |
| 音频支持 | ❌ 无 | ✅ 插件式（待实现） |
| 配置灵活性 | ❌ 硬编码 | ✅ 参数化配置 |
| 错误处理 | ⚠️ 基础 | ✅ 完善 |
| 文档 | ❌ 无 | ✅ 完整文档 |
| 示例代码 | ⚠️ 1 个 | ✅ 3+ 个 |

## 兼容性说明

### 完全兼容

- arduous_libretro.so 核心文件
- 所有 .hex 游戏文件
- I2C/SPI OLED 显示屏硬件
- Raspberry Pi 所有型号

### API 变化

旧版本的 API 被完全替换，需要重写代码。但新 API 更简洁，通常代码量会减少 80% 以上。

### 性能

新版本性能与旧版本相当或更好：
- 相同的 LibRetro 核心
- 相同的编译优化
- 更少的 Python 开销（减少不必要的转换）

## 常见迁移问题

### Q1: 我的自定义 OLED 配置如何迁移？

**A:** 使用 LumaOLEDDriver 的参数：

```python
# 旧版本
device = ssd1305(width=128, height=32, rotate=2)

# 新版本
driver = LumaOLEDDriver(
    device_type='ssd1305',
    width=128,
    height=32,
    rotate=2,
    interface='i2c'
)
```

### Q2: 我使用了自定义的帧处理逻辑，如何迁移？

**A:** 创建自定义驱动，参考 [custom_driver_demo.py](examples/custom_driver_demo.py)。

### Q3: 我需要特定的帧率控制，如何设置？

**A:** 使用 target_fps 参数：

```python
arduboy = PyArduboy(
    core_path="...",
    game_path="...",
    target_fps=30  # 自定义帧率
)
```

### Q4: 我能同时使用旧版本和新版本吗？

**A:** 可以，它们是独立的：
- 旧版本：直接运行 `python3 run_arduboy.py`
- 新版本：使用 PyArduboy 库

建议逐步迁移到新版本。

### Q5: 新版本支持哪些 OLED 芯片？

**A:** 所有 Luma.OLED 支持的芯片：
- SSD1305 ✅
- SSD1306 ✅
- SH1106 ✅
- SSD1322 ✅
- SSD1325 ✅
- SSD1327 ✅
- SSD1331 ✅
- SSD1351 ✅

### Q6: 我的项目需要在没有 OLED 的环境运行，怎么办？

**A:** 使用空驱动或自定义驱动：

```python
from pyarduboy.drivers.video.null import NullVideoDriver

arduboy.set_video_driver(NullVideoDriver())
```

或保存为图片：

```python
from examples.custom_driver_demo import ImageSaveDriver

arduboy.set_video_driver(ImageSaveDriver())
```

## 推荐迁移顺序

1. ✅ **第一步**：测试基础功能
   - 运行 `examples/basic_demo.py`
   - 确保核心加载正常

2. ✅ **第二步**：测试 OLED 显示
   - 运行 `examples/oled_demo.py`
   - 确保显示正常

3. ✅ **第三步**：逐步迁移代码
   - 先迁移简单的部分
   - 使用新 API 替换旧代码

4. ✅ **第四步**：自定义驱动
   - 如果有特殊需求，创建自定义驱动
   - 参考现有驱动实现

5. ✅ **第五步**：测试和优化
   - 完整测试所有功能
   - 性能调优

## 获取帮助

- 查看示例：`examples/` 目录
- 阅读文档：`README_NEW.md`、`ARCHITECTURE.md`
- 检查代码：`pyarduboy/` 目录

## 总结

新版 PyArduboy 库提供了更好的架构、更清晰的 API 和更强的扩展性。虽然需要迁移代码，但新版本会让你的项目更易维护和扩展。

**迁移收益：**
- 📉 代码量减少 80%+
- 🔧 更易维护
- 🔌 可扩展性强
- 📚 完整文档
- 🚀 更好的性能

开始迁移吧！
