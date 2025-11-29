# PyArduboy 架构文档

## 设计思路

PyArduboy 是一个模块化的 Arduboy 模拟器库，设计目标是提供清晰、易用的 Python 接口来运行 Arduboy 游戏，同时支持灵活的驱动插件系统以适配不同的硬件平台。

## 核心架构

### 层次结构

```
┌─────────────────────────────────────────┐
│        User Application (Demo)          │  用户应用层
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│         PyArduboy Core API              │  核心 API 层
│    (pyarduboy/core.py)                  │
│  - 游戏生命周期管理                        │
│  - 驱动插件管理                           │
│  - 主循环控制                            │
└─────────┬──────────────────────┬────────┘
          │                      │
          ▼                      ▼
┌──────────────────┐   ┌──────────────────┐
│  Driver Plugins  │   │  LibRetro Bridge │  桥接层
│  (drivers/)      │   │  (libretro_      │
│  - Video         │   │   bridge.py)     │
│  - Audio         │   │                  │
│  - Input         │   │ - 输入状态管理      │
└──────────────────┘   │ - 帧数据转换       │
                       │ - 会话生命周期      │
                       └────────┬──────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │   libretro.py    │  Python LibRetro 绑定
                       │   (第三方库)      │
                       └────────┬──────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │ arduous_libretro │  C++ 模拟器核心
                       │   (.so 动态库)    │
                       └──────────────────┘
```

## 模块详解

### 1. PyArduboy Core (core.py)

**职责：**
- 管理游戏的加载和运行
- 协调各个驱动插件
- 控制游戏主循环和帧率
- 提供统一的 API 接口

**核心类：PyArduboy**

```python
class PyArduboy:
    def __init__(self, core_path, game_path, target_fps=60)
    def set_video_driver(driver)
    def set_audio_driver(driver)
    def set_input_driver(driver)
    def run(max_frames=None)
    def stop()
    def cleanup()
```

**工作流程：**

1. **初始化阶段**
   - 创建 LibretroBridge 实例
   - 初始化所有驱动插件

2. **运行阶段**（主循环）
   ```python
   while running:
       # 1. 轮询输入
       input_state = input_driver.poll()
       bridge.set_input_state(input_state)

       # 2. 运行一帧模拟
       bridge.run_frame()

       # 3. 渲染视频
       frame = bridge.get_frame()
       video_driver.render(frame)

       # 4. 播放音频
       samples = bridge.get_audio_samples()
       audio_driver.play_samples(samples)

       # 5. 帧率控制
       sleep_if_needed()
   ```

3. **清理阶段**
   - 关闭所有驱动
   - 清理 LibRetro 会话

### 2. LibRetro Bridge (libretro_bridge.py)

**职责：**
- 封装 libretro.py 的复杂性
- 管理 LibRetro 会话生命周期
- 转换数据格式（RGB565 → RGB888）
- 管理输入状态

**核心类：LibretroBridge**

```python
class LibretroBridge:
    def __init__(self, core_path, game_path)
    def initialize() -> bool
    def start() -> bool
    def run_frame()
    def get_frame() -> np.ndarray
    def set_input_state(button_states)
    def stop()
    def cleanup()
```

**数据转换：**

LibRetro 核心输出的是 RGB565 格式（2 字节/像素），需要转换为 RGB888：

```python
# RGB565 → RGB888 转换
r = ((img_array & 0xF800) >> 11) << 3  # 5 bits → 8 bits
g = ((img_array & 0x07E0) >> 5) << 2   # 6 bits → 8 bits
b = (img_array & 0x001F) << 3          # 5 bits → 8 bits
```

### 3. Driver Plugin System (drivers/)

采用抽象基类模式，定义统一接口，支持多种实现。

#### 3.1 视频驱动 (VideoDriver)

**接口：**

```python
class VideoDriver(ABC):
    @abstractmethod
    def init(width: int, height: int) -> bool
        """初始化显示设备"""

    @abstractmethod
    def render(frame_buffer: np.ndarray) -> None
        """渲染一帧 (height, width, 3) RGB 数组"""

    @abstractmethod
    def close() -> None
        """关闭设备"""

    @property
    @abstractmethod
    def is_running() -> bool
        """运行状态"""
```

**已实现驱动：**

- **NullVideoDriver** - 空驱动，不输出
- **LumaOLEDDriver** - Luma.OLED 驱动（支持 SSD1305/SSD1306）
- **LumaOLED32Driver** - 128x32 专用驱动（裁剪中间部分）

**OLED 驱动特性：**

- 自动初始化 I2C/SPI 接口
- 支持多种裁剪模式（center/top/bottom/scale）
- RGB → 灰度 → 1-bit 转换
- 自动适配不同分辨率

#### 3.2 音频驱动 (AudioDriver)

**接口：**

```python
class AudioDriver(ABC):
    @abstractmethod
    def init(sample_rate: int = 44100) -> bool
        """初始化音频设备"""

    @abstractmethod
    def play_samples(samples: np.ndarray) -> None
        """播放音频采样"""

    @abstractmethod
    def close() -> None
        """关闭设备"""
```

**已实现驱动：**

- **NullAudioDriver** - 空驱动，不播放声音

**TODO：** 实现实际音频驱动（PyAudio、SDL2 等）

#### 3.3 输入驱动 (InputDriver)

**接口：**

```python
class InputDriver(ABC):
    # 按键常量
    BUTTON_UP = 4
    BUTTON_DOWN = 5
    BUTTON_LEFT = 6
    BUTTON_RIGHT = 7
    BUTTON_A = 8
    BUTTON_B = 0

    @abstractmethod
    def init() -> bool
        """初始化输入设备"""

    @abstractmethod
    def poll() -> dict
        """轮询输入状态，返回按键字典"""

    @abstractmethod
    def close() -> None
        """关闭设备"""

    @property
    @abstractmethod
    def is_running() -> bool
        """运行状态"""
```

**已实现驱动：**

- **KeyboardInputDriver** - 键盘输入（切换模式）

**输入状态格式：**

```python
{
    'up': bool,
    'down': bool,
    'left': bool,
    'right': bool,
    'a': bool,
    'b': bool,
    'start': bool,
    'select': bool,
}
```

## 数据流

### 输入数据流

```
Keyboard
   │
   ▼
KeyboardInputDriver.poll()
   │
   ▼
PyArduboy.run() → convert_input_state()
   │
   ▼
LibretroBridge.set_input_state()
   │
   ▼
LibRetro Input Generator
   │
   ▼
arduous_libretro Core
```

### 视频数据流

```
arduous_libretro Core
   │
   ▼
ArrayVideoDriver (_frame buffer)
   │
   ▼
LibretroBridge.get_frame()
   │ (RGB565 → RGB888 转换)
   ▼
PyArduboy.run()
   │
   ▼
VideoDriver.render()
   │
   ▼
OLED Display (RGB → Gray → 1-bit)
```

### 音频数据流（TODO）

```
arduous_libretro Core
   │
   ▼
ArrayAudioDriver
   │
   ▼
LibretroBridge.get_audio_samples()
   │
   ▼
PyArduboy.run()
   │
   ▼
AudioDriver.play_samples()
   │
   ▼
Audio Output
```

## 性能优化

### 1. 编译优化

编译 arduous_libretro 核心时使用的优化选项：

```bash
-O3                    # 最高优化级别
-march=native          # 针对当前 CPU 架构优化
-mtune=native          # 针对当前 CPU 调优
-ffast-math            # 快速数学运算（牺牲精度）
```

### 2. LibRetro 优化

```python
builder.with_jit_capable(True)  # 启用 JIT
builder.with_perf(DEFAULT)      # 性能计数器
builder.with_timing(DEFAULT)    # 时序优化
```

### 3. 帧率控制

使用精确的时间控制来维持目标帧率：

```python
frame_time = 1.0 / target_fps
frame_elapsed = time.time() - frame_start
if frame_elapsed < frame_time:
    time.sleep(frame_time - frame_elapsed)
```

### 4. 并行编译

使用 `make -j4` 利用多核 CPU 加速编译。

## 扩展指南

### 添加新的视频驱动

1. 创建新文件：`pyarduboy/drivers/video/my_driver.py`

2. 继承 VideoDriver 基类：

```python
from .base import VideoDriver
import numpy as np

class MyVideoDriver(VideoDriver):
    def init(self, width: int, height: int) -> bool:
        self._width = width
        self._height = height
        self._running = True
        # 初始化你的硬件
        return True

    def render(self, frame_buffer: np.ndarray) -> None:
        # frame_buffer shape: (height, width, 3)
        # 实现渲染逻辑
        pass

    def close(self) -> None:
        self._running = False
        # 清理资源

    @property
    def is_running(self) -> bool:
        return self._running
```

3. 在 `__init__.py` 中导出：

```python
from .my_driver import MyVideoDriver

__all__ = [..., "MyVideoDriver"]
```

### 添加新的输入驱动

类似视频驱动，继承 `InputDriver` 基类并实现 `poll()` 方法。

### 集成到其他项目

PyArduboy 设计为可嵌入库：

```python
from pyarduboy import PyArduboy
from my_project.my_driver import MyCustomDriver

class MyGame:
    def __init__(self):
        self.arduboy = PyArduboy(
            core_path="./arduous_libretro.so",
            game_path="./game.hex"
        )
        self.arduboy.set_video_driver(MyCustomDriver())

    def run(self):
        self.arduboy.run()
```

## 硬件需求

### 树莓派

- **最低配置**：Raspberry Pi 3B
- **推荐配置**：Raspberry Pi 4B 或更高
- **OS**：Raspberry Pi OS (Bullseye 或更高)

### OLED 显示屏

支持的 OLED 芯片：
- SSD1305 (推荐)
- SSD1306
- SH1106
- 其他 Luma.OLED 支持的芯片

连接方式：
- I2C（推荐，简单）
- SPI（更快，需要更多引脚）

分辨率：
- 128x64（标准 Arduboy 分辨率）
- 128x32（会裁剪画面）

### GPIO 引脚分配（I2C）

```
树莓派          OLED 模块
GPIO2  (SDA) ─→ SDA
GPIO3  (SCL) ─→ SCL
3.3V         ─→ VCC
GND          ─→ GND
```

## 依赖关系

```
PyArduboy
├── libretro.py (Python LibRetro 绑定)
├── numpy (数组处理)
├── pillow (图像处理)
├── luma.oled (OLED 驱动，可选)
└── arduous_libretro.so (C++ 核心)
    ├── simavr (AVR 模拟器)
    └── libretro API
```

## 未来计划

- [ ] 实现音频驱动（PyAudio/SDL2）
- [ ] 添加 GPIO 按钮输入驱动
- [ ] 支持游戏保存/加载状态
- [ ] 添加性能分析工具
- [ ] 支持多人游戏（串口通信）
- [ ] 添加游戏截图功能
- [ ] 优化内存使用
- [ ] 添加配置文件支持

## 故障排除

### 常见问题

1. **ImportError: libretro.py not found**
   - 解决：`pip3 install libretro.py`

2. **Core load failure**
   - 检查核心是否编译：`ls -lh arduous_libretro.so`
   - 重新编译核心

3. **OLED 无显示**
   - 检查 I2C：`i2cdetect -y 1`
   - 确认设备地址（通常 0x3C）
   - 检查接线

4. **帧率过低**
   - 使用 Release 模式编译
   - 降低目标帧率
   - 检查 CPU 负载

## 调试技巧

### 启用详细日志

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### 保存帧到文件

使用 `ImageSaveDriver` 查看实际渲染内容：

```python
from examples.custom_driver_demo import ImageSaveDriver

arduboy.set_video_driver(ImageSaveDriver(
    output_dir="./debug_frames",
    save_interval=1  # 保存每一帧
))
```

### 性能分析

```python
import cProfile

cProfile.run('arduboy.run(max_frames=600)', 'profile.stats')
```

## 许可证

- PyArduboy: MIT License
- arduous_libretro: 遵循原项目许可证
- libretro.py: 遵循原项目许可证
- luma.oled: MIT License
