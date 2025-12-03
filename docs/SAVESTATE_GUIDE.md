# Libretro 游戏存档功能集成指南

## 概述

本文档说明如何在 PyArduboy 项目中集成 libretro.py 的游戏存档（savestate）功能，实现游戏的保存和加载。

## Libretro 存档 API

### 核心 API

libretro.py 提供了以下核心存档 API（位于 `libretro.core.Core` 类）：

#### 1. `serialize_size() -> int`
获取存档所需的缓冲区大小（字节）。

```python
# 用法
size = session.core.serialize_size()
if size > 0:
    print(f"存档需要 {size} 字节")
else:
    print("核心不支持存档")
```

#### 2. `serialize(data: bytearray | memoryview) -> bool`
将游戏状态序列化到缓冲区。

```python
# 用法
size = session.core.serialize_size()
buffer = bytearray(size)
success = session.core.serialize(buffer)
if success:
    print("存档成功")
    # 可以保存 buffer 到文件
else:
    print("存档失败")
```

**参数**:
- `data`: 可写的 bytearray 或 memoryview，必须至少有 `serialize_size()` 返回的大小

**返回**:
- `True`: 序列化成功
- `False`: 序列化失败

#### 3. `unserialize(data: bytes | bytearray | memoryview) -> bool`
从缓冲区恢复游戏状态。

```python
# 用法
# 从文件读取存档数据
with open('savefile.sav', 'rb') as f:
    data = f.read()

success = session.core.unserialize(data)
if success:
    print("读档成功")
else:
    print("读档失败")
```

**参数**:
- `data`: 包含序列化数据的 bytes、bytearray 或 memoryview

**返回**:
- `True`: 反序列化成功
- `False`: 反序列化失败

### 存档上下文

libretro 支持不同的存档上下文（`SavestateContext`），用于不同场景：

```python
from libretro.api import SavestateContext

# 可用的上下文类型
SavestateContext.NORMAL              # 0: 正常存档（用户手动保存）
SavestateContext.RUNAHEAD_SAME_INSTANCE  # 1: 预运行优化（同一实例）
SavestateContext.RUNAHEAD_SAME_BINARY    # 2: 预运行优化（相同二进制）
SavestateContext.ROLLBACK_NETPLAY        # 3: 网络对战回滚
```

在 SessionBuilder 中设置存档上下文：

```python
builder = SessionBuilder()
builder.with_savestate_context(SavestateContext.NORMAL)
# 或使用默认值（NORMAL）
builder.with_savestate_context(DEFAULT)
```

### 存档目录

Session 提供了存档目录属性：

```python
# 获取存档目录路径
save_dir = session.save_directory  # bytes | None
# 或使用别名
save_dir = session.save_dir        # bytes | None

if save_dir:
    save_path = save_dir.decode('utf-8')
    print(f"存档目录: {save_path}")
```

## 集成到 LibretroBridge

### 方案 1: 添加存档方法

在 `LibretroBridge` 类中添加存档和读档方法：

```python
# 文件: pyarduboy/libretro_bridge.py

import os
from pathlib import Path
from typing import Optional

class LibretroBridge:
    """现有代码..."""

    def __init__(self, core_path: str, game_path: str, save_dir: Optional[str] = None):
        """
        Args:
            core_path: libretro 核心文件路径
            game_path: 游戏 ROM 文件路径
            save_dir: 存档目录路径（可选，默认为游戏文件所在目录）
        """
        # 现有初始化代码...

        # 存档目录设置
        if save_dir:
            self.save_dir = Path(save_dir)
        else:
            # 默认使用游戏文件所在目录
            self.save_dir = Path(game_path).parent / 'saves'

        # 确保存档目录存在
        self.save_dir.mkdir(parents=True, exist_ok=True)

    def get_savestate_size(self) -> int:
        """
        获取存档所需的缓冲区大小

        Returns:
            存档大小（字节），如果不支持存档则返回 0
        """
        if not self._running or not self.session:
            return 0

        try:
            return self.session.core.serialize_size()
        except Exception as e:
            print(f"Error getting savestate size: {e}")
            return 0

    def save_state(self, slot: int = 0) -> bool:
        """
        保存游戏状态到指定槽位

        Args:
            slot: 存档槽位（0-9），默认为 0

        Returns:
            保存成功返回 True，失败返回 False
        """
        if not self._running or not self.session:
            print("Session not running, cannot save state")
            return False

        try:
            # 获取存档大小
            size = self.session.core.serialize_size()
            if size == 0:
                print("Core does not support save states")
                return False

            # 分配缓冲区
            buffer = bytearray(size)

            # 序列化游戏状态
            success = self.session.core.serialize(buffer)
            if not success:
                print("Failed to serialize game state")
                return False

            # 生成存档文件名
            game_name = Path(self.game_path).stem
            save_file = self.save_dir / f"{game_name}.slot{slot}.sav"

            # 保存到文件
            with open(save_file, 'wb') as f:
                f.write(buffer)

            print(f"Game state saved to: {save_file}")
            print(f"  Size: {len(buffer)} bytes")
            return True

        except Exception as e:
            print(f"Error saving state: {e}")
            import traceback
            traceback.print_exc()
            return False

    def load_state(self, slot: int = 0) -> bool:
        """
        从指定槽位加载游戏状态

        Args:
            slot: 存档槽位（0-9），默认为 0

        Returns:
            加载成功返回 True，失败返回 False
        """
        if not self._running or not self.session:
            print("Session not running, cannot load state")
            return False

        try:
            # 生成存档文件名
            game_name = Path(self.game_path).stem
            save_file = self.save_dir / f"{game_name}.slot{slot}.sav"

            # 检查存档文件是否存在
            if not save_file.exists():
                print(f"Save file not found: {save_file}")
                return False

            # 读取存档数据
            with open(save_file, 'rb') as f:
                data = f.read()

            # 反序列化游戏状态
            success = self.session.core.unserialize(data)
            if not success:
                print("Failed to unserialize game state")
                return False

            print(f"Game state loaded from: {save_file}")
            print(f"  Size: {len(data)} bytes")
            return True

        except Exception as e:
            print(f"Error loading state: {e}")
            import traceback
            traceback.print_exc()
            return False

    def list_save_states(self) -> list[int]:
        """
        列出所有可用的存档槽位

        Returns:
            可用槽位列表，例如 [0, 1, 3] 表示槽位 0、1、3 有存档
        """
        game_name = Path(self.game_path).stem
        pattern = f"{game_name}.slot*.sav"

        slots = []
        for save_file in self.save_dir.glob(pattern):
            # 从文件名提取槽位号
            # 例如: "game.slot2.sav" -> 2
            try:
                slot_str = save_file.stem.split('.slot')[1]
                slot = int(slot_str)
                slots.append(slot)
            except (IndexError, ValueError):
                continue

        return sorted(slots)

    def delete_save_state(self, slot: int = 0) -> bool:
        """
        删除指定槽位的存档

        Args:
            slot: 存档槽位（0-9）

        Returns:
            删除成功返回 True，失败返回 False
        """
        try:
            game_name = Path(self.game_path).stem
            save_file = self.save_dir / f"{game_name}.slot{slot}.sav"

            if not save_file.exists():
                print(f"Save file not found: {save_file}")
                return False

            save_file.unlink()
            print(f"Deleted save state: {save_file}")
            return True

        except Exception as e:
            print(f"Error deleting save state: {e}")
            return False
```

### 方案 2: 快速存档/读档（内存）

如果只需要临时存档（例如快速保存/加载），可以使用内存缓冲区：

```python
class LibretroBridge:
    """现有代码..."""

    def __init__(self, ...):
        # 现有初始化代码...

        # 快速存档缓冲区（内存）
        self._quick_save_buffer: Optional[bytearray] = None

    def quick_save(self) -> bool:
        """
        快速保存到内存

        Returns:
            保存成功返回 True，失败返回 False
        """
        if not self._running or not self.session:
            return False

        try:
            size = self.session.core.serialize_size()
            if size == 0:
                return False

            self._quick_save_buffer = bytearray(size)
            success = self.session.core.serialize(self._quick_save_buffer)

            if success:
                print(f"Quick save: {len(self._quick_save_buffer)} bytes")
            return success

        except Exception as e:
            print(f"Error in quick save: {e}")
            return False

    def quick_load(self) -> bool:
        """
        快速加载（从内存）

        Returns:
            加载成功返回 True，失败返回 False
        """
        if not self._running or not self.session:
            return False

        if self._quick_save_buffer is None:
            print("No quick save available")
            return False

        try:
            success = self.session.core.unserialize(self._quick_save_buffer)
            if success:
                print("Quick load successful")
            return success

        except Exception as e:
            print(f"Error in quick load: {e}")
            return False

    def has_quick_save(self) -> bool:
        """检查是否有快速存档"""
        return self._quick_save_buffer is not None
```

## 使用示例

### 基本用法

```python
from pyarduboy import LibretroBridge

# 创建 bridge 实例
bridge = LibretroBridge(
    core_path="cores/arduous_libretro.so",
    game_path="roms/game.hex",
    save_dir="saves"  # 可选：自定义存档目录
)

# 初始化并启动
bridge.initialize()
bridge.start()

# 游戏循环
for frame in range(600):  # 10 秒 @ 60 FPS
    # 运行一帧
    bridge.run_frame()

    # 在第 300 帧保存游戏
    if frame == 300:
        print("保存游戏...")
        bridge.save_state(slot=0)

    # 在第 400 帧加载游戏
    if frame == 400:
        print("加载游戏...")
        bridge.load_state(slot=0)

# 清理
bridge.cleanup()
```

### 高级用法：多槽位管理

```python
# 查看可用的存档槽位
slots = bridge.list_save_states()
print(f"可用存档槽位: {slots}")

# 保存到多个槽位
for slot in range(3):
    bridge.save_state(slot=slot)
    print(f"已保存到槽位 {slot}")

# 加载指定槽位
bridge.load_state(slot=1)

# 删除旧存档
bridge.delete_save_state(slot=2)
```

### 快速存档/读档

```python
# 快速保存（内存）
bridge.quick_save()

# 做一些操作...
for _ in range(100):
    bridge.run_frame()

# 快速加载（恢复到保存点）
bridge.quick_load()
```

### 自动存档

```python
import time

last_autosave = time.time()
AUTOSAVE_INTERVAL = 60  # 每 60 秒自动保存

while running:
    bridge.run_frame()

    # 自动存档
    current_time = time.time()
    if current_time - last_autosave > AUTOSAVE_INTERVAL:
        bridge.save_state(slot=9)  # 使用槽位 9 作为自动存档
        last_autosave = current_time
        print("自动存档完成")
```

## 存档文件格式

### 文件命名规范

存档文件命名格式：`{游戏名称}.slot{槽位号}.sav`

示例：
- `arkanoid.slot0.sav` - Arkanoid 游戏的槽位 0 存档
- `arkanoid.slot1.sav` - Arkanoid 游戏的槽位 1 存档

### 文件内容

存档文件是二进制格式，由 libretro 核心直接生成，内容包括：
- 游戏 RAM 状态
- CPU 寄存器状态
- 其他核心相关状态

**注意**:
- 存档格式由核心决定，不同核心可能不兼容
- 存档大小由核心的 `serialize_size()` 决定
- 对于 Ardens 核心（Arduboy 模拟器），存档通常很小（几 KB）

### 存档兼容性

⚠️ **重要提示**:

1. **核心版本**: 存档可能与特定版本的核心绑定，更新核心后旧存档可能无效
2. **平台依赖**: 某些核心的存档可能依赖于平台（x86/ARM、big-endian/little-endian）
3. **ROM 版本**: 存档通常与特定的 ROM 版本绑定

### 存档元数据（可选）

为了提高存档管理的友好性，可以添加元数据文件：

```python
import json
from datetime import datetime

def save_state_with_metadata(bridge, slot: int, description: str = ""):
    """保存游戏状态并创建元数据文件"""

    # 保存游戏状态
    if not bridge.save_state(slot=slot):
        return False

    # 创建元数据
    game_name = Path(bridge.game_path).stem
    meta_file = bridge.save_dir / f"{game_name}.slot{slot}.meta.json"

    metadata = {
        'game': game_name,
        'slot': slot,
        'timestamp': datetime.now().isoformat(),
        'description': description,
        'core_version': '1.0.0',  # 可以从核心获取
    }

    with open(meta_file, 'w') as f:
        json.dump(metadata, f, indent=2)

    return True

# 使用
save_state_with_metadata(bridge, slot=0, description="关卡 3 开始位置")
```

## 测试存档功能

### 单元测试

```python
import unittest
from pyarduboy import LibretroBridge

class TestSaveState(unittest.TestCase):
    def setUp(self):
        self.bridge = LibretroBridge(
            core_path="cores/arduous_libretro.so",
            game_path="roms/test.hex"
        )
        self.bridge.initialize()
        self.bridge.start()

    def tearDown(self):
        self.bridge.cleanup()

    def test_save_and_load(self):
        """测试保存和加载功能"""
        # 运行几帧
        for _ in range(60):
            self.bridge.run_frame()

        # 保存状态
        self.assertTrue(self.bridge.save_state(slot=0))

        # 再运行几帧（状态会改变）
        for _ in range(60):
            self.bridge.run_frame()

        # 加载状态（应该恢复到之前的状态）
        self.assertTrue(self.bridge.load_state(slot=0))

    def test_quick_save_load(self):
        """测试快速保存/加载"""
        # 快速保存
        self.assertTrue(self.bridge.quick_save())
        self.assertTrue(self.bridge.has_quick_save())

        # 运行几帧
        for _ in range(60):
            self.bridge.run_frame()

        # 快速加载
        self.assertTrue(self.bridge.quick_load())

    def test_list_save_states(self):
        """测试列出存档槽位"""
        # 创建多个存档
        self.bridge.save_state(slot=0)
        self.bridge.save_state(slot=2)

        # 列出存档
        slots = self.bridge.list_save_states()
        self.assertIn(0, slots)
        self.assertIn(2, slots)
        self.assertNotIn(1, slots)

    def test_delete_save_state(self):
        """测试删除存档"""
        # 创建存档
        self.bridge.save_state(slot=0)
        self.assertTrue(0 in self.bridge.list_save_states())

        # 删除存档
        self.assertTrue(self.bridge.delete_save_state(slot=0))
        self.assertFalse(0 in self.bridge.list_save_states())
```

## 常见问题

### Q: 核心不支持存档怎么办？

A: 调用 `serialize_size()` 返回 0 表示核心不支持存档。对于 Ardens 核心（Arduboy），应该是支持的。

```python
size = bridge.get_savestate_size()
if size == 0:
    print("该核心不支持存档功能")
```

### Q: 存档文件很大怎么办？

A: 可以压缩存档文件：

```python
import gzip

def save_state_compressed(bridge, slot: int):
    # 获取原始存档
    size = bridge.session.core.serialize_size()
    buffer = bytearray(size)
    bridge.session.core.serialize(buffer)

    # 压缩保存
    game_name = Path(bridge.game_path).stem
    save_file = bridge.save_dir / f"{game_name}.slot{slot}.sav.gz"

    with gzip.open(save_file, 'wb') as f:
        f.write(buffer)

def load_state_compressed(bridge, slot: int):
    game_name = Path(bridge.game_path).stem
    save_file = bridge.save_dir / f"{game_name}.slot{slot}.sav.gz"

    with gzip.open(save_file, 'rb') as f:
        data = f.read()

    return bridge.session.core.unserialize(data)
```

### Q: 如何实现即时回放（倒带）？

A: 使用循环缓冲区定期保存状态：

```python
from collections import deque

class RewindManager:
    def __init__(self, bridge, max_frames=600):  # 10 秒 @ 60 FPS
        self.bridge = bridge
        self.buffer = deque(maxlen=max_frames)

    def capture_frame(self):
        """捕获当前帧状态"""
        size = self.bridge.session.core.serialize_size()
        if size == 0:
            return

        state = bytearray(size)
        if self.bridge.session.core.serialize(state):
            self.buffer.append(bytes(state))

    def rewind(self, frames=1):
        """倒带指定帧数"""
        if len(self.buffer) < frames:
            frames = len(self.buffer)

        if frames == 0:
            return False

        # 移除最近的 frames 个状态
        for _ in range(frames):
            self.buffer.pop()

        # 加载倒带后的状态
        if self.buffer:
            state = self.buffer[-1]
            return self.bridge.session.core.unserialize(state)

        return False
```

## 性能考虑

### 序列化性能

- **Ardens 核心**: 存档通常只有几 KB，序列化非常快（< 1ms）
- **建议**: 不要每帧都保存，会影响性能

### 文件 I/O

- **异步保存**: 可以使用线程异步保存到磁盘
- **缓存**: 对于快速保存/加载，优先使用内存缓冲区

```python
import threading

def save_state_async(bridge, slot: int):
    """异步保存存档"""
    def _save():
        bridge.save_state(slot=slot)

    thread = threading.Thread(target=_save, daemon=True)
    thread.start()
    return thread
```

## 参考资源

- [libretro.py 文档](https://pypi.org/project/libretro.py/)
- [libretro API 规范](https://docs.libretro.com/)
- [Ardens 模拟器源码](https://github.com/tiberiusbrown/Ardens)
