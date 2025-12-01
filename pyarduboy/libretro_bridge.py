"""
LibRetro 桥接层

负责与 arduous_libretro 核心进行交互，封装 libretro.py 的复杂性
"""
import os
import sys
import numpy as np
from typing import Optional, Callable
from PIL import Image

try:
    from libretro import SessionBuilder, ArrayVideoDriver, ArrayAudioDriver, DEFAULT
    from libretro.drivers.input import IterableInputDriver
    from libretro.api.input import JoypadState
except ImportError as e:
    raise ImportError(
        "libretro.py library not found. Please install it using: pip3 install libretro.py"
    ) from e


class LibretroBridge:
    """
    LibRetro 桥接类

    负责管理 libretro session 的生命周期，提供简化的接口给上层调用
    """

    def __init__(self, core_path: str, game_path: str):
        """
        初始化 LibRetro 桥接层

        Args:
            core_path: libretro 核心文件路径（.so 文件）
            game_path: 游戏 ROM 文件路径（.hex 文件）
        """
        if not os.path.exists(core_path):
            raise FileNotFoundError(f"Core file not found: {core_path}")

        if not os.path.exists(game_path):
            raise FileNotFoundError(f"Game file not found: {game_path}")

        self.core_path = core_path
        self.game_path = game_path

        # LibRetro 组件
        self.builder = None
        self.session = None
        self.video_driver = None
        self.audio_driver = None
        self.input_driver = None

        # 输入状态管理
        self.input_state = {
            'b': False,      # Button B
            'y': False,
            'select': False,
            'start': False,
            'up': False,
            'down': False,
            'left': False,
            'right': False,
            'a': False,      # Button A
            'x': False,
            'l': False,
            'r': False,
            'l2': False,
            'r2': False,
            'l3': False,
            'r3': False,
        }

        # 会话状态
        self._initialized = False
        self._running = False

    def set_input_state(self, button_states: dict) -> None:
        """
        设置输入状态

        Args:
            button_states: 按键状态字典，例如：
                {
                    'up': True,
                    'down': False,
                    'a': True,
                    ...
                }
        """
        self.input_state.update(button_states)

    def _input_generator(self):
        """生成器函数，持续产生当前输入状态"""
        while self._running:
            yield JoypadState(**self.input_state)

    def initialize(self) -> bool:
        """
        初始化 LibRetro 会话

        Returns:
            初始化成功返回 True，失败返回 False
        """
        if self._initialized:
            return True

        try:
            # 创建 session builder
            self.builder = SessionBuilder()
            self.builder.with_core(self.core_path)
            self.builder.with_content(self.game_path)
            self.builder.with_content_driver(DEFAULT)

            # 启用性能优化（在某些 Python 版本可能失败，忽略错误继续）
            try:
                self.builder.with_jit_capable(True)
                self.builder.with_perf(DEFAULT)
                self.builder.with_timing(DEFAULT)
            except Exception as e:
                # 某些优化在新版本 Python 中可能不可用，但不影响核心功能
                print(f"Warning: Could not enable all optimizations: {e}")
                pass

            # 设置视频驱动
            self.video_driver = ArrayVideoDriver()
            self.builder.with_video(self.video_driver)

            # 设置音频驱动
            self.audio_driver = ArrayAudioDriver()
            self.builder.with_audio(self.audio_driver)

            # 设置输入驱动
            self.input_driver = IterableInputDriver(lambda: self._input_generator())
            self.builder.with_input(self.input_driver)

            # 构建会话
            self.session = self.builder.build()

            self._initialized = True
            return True

        except Exception as e:
            print(f"Failed to initialize LibRetro bridge: {e}")
            import traceback
            traceback.print_exc()
            return False

    def start(self) -> bool:
        """
        启动 LibRetro 会话

        Returns:
            启动成功返回 True，失败返回 False
        """
        if not self._initialized:
            if not self.initialize():
                return False

        if self._running:
            return True

        try:
            # 进入会话上下文
            self.session.__enter__()
            self._running = True
            return True
        except Exception as e:
            print(f"Failed to start LibRetro session: {e}")
            return False

    def run_frame(self) -> None:
        """运行一帧模拟"""
        if not self._running:
            raise RuntimeError("Session not started. Call start() first.")

        self.session.run()

    def get_frame(self) -> Optional[np.ndarray]:
        """
        获取当前帧的图像数据

        Returns:
            numpy 数组，shape 为 (height, width, 3)，RGB 格式
            如果没有帧数据则返回 None
        """
        if not self.video_driver or not hasattr(self.video_driver, '_frame'):
            return None

        if self.video_driver._frame is None:
            return None

        try:
            frame_data = bytes(self.video_driver._frame)
            width = self.video_driver._last_width
            height = self.video_driver._last_height
            pitch = self.video_driver._last_pitch

            # 提取实际帧数据
            actual_size = height * pitch
            frame_bytes = frame_data[:actual_size]

            # Arduboy 使用 RGB565 格式
            img_array = np.frombuffer(frame_bytes, dtype=np.uint16).reshape((height, width))

            # 转换 RGB565 到 RGB888
            r = ((img_array & 0xF800) >> 11) << 3
            g = ((img_array & 0x07E0) >> 5) << 2
            b = (img_array & 0x001F) << 3

            rgb_array = np.stack([r, g, b], axis=2).astype(np.uint8)
            return rgb_array

        except Exception as e:
            print(f"Error getting frame: {e}")
            return None

    def get_audio_samples(self) -> Optional[np.ndarray]:
        """
        获取音频采样数据

        Returns:
            numpy 数组，包含音频采样
            如果没有音频数据则返回 None
        """
        if not self.audio_driver:
            return None

        try:
            # ArrayAudioDriver 将音频数据存储在 _buffer 属性中（array("h") 类型）
            if hasattr(self.audio_driver, '_buffer'):
                buffer = self.audio_driver._buffer

                if len(buffer) == 0:
                    return None

                # 转换 array("h") 到 numpy int16 数组
                samples_int16 = np.array(buffer, dtype=np.int16)

                # 转换 int16 [-32768, 32767] 到 float32 [-1.0, 1.0]
                samples_float = samples_int16.astype(np.float32) / 32768.0

                # 调试：只在有非零音频时打印（避免刷屏）
                # if samples_float.min() != 0.0 or samples_float.max() != 0.0:
                #     print(f"[Audio] Got {len(samples_int16)} samples (int16), "
                #           f"converted to {len(samples_float)} float32 samples, "
                #           f"range=[{samples_float.min():.3f}, {samples_float.max():.3f}]")

                # 清空缓冲区（避免重复播放）
                self.audio_driver._buffer = self.audio_driver._buffer.__class__(self.audio_driver._buffer.typecode)

                return samples_float if len(samples_float) > 0 else None

            return None
        except Exception as e:
            print(f"[Audio] Error getting samples: {e}")
            import traceback
            traceback.print_exc()
            return None

    def stop(self) -> None:
        """停止 LibRetro 会话"""
        if self._running and self.session:
            try:
                self.session.__exit__(None, None, None)
            except Exception as e:
                print(f"Error stopping session: {e}")
            finally:
                self._running = False

    def reset(self) -> bool:
        """
        重置游戏（重新加载）

        Returns:
            重置成功返回 True，失败返回 False
        """
        print("Resetting game...")
        self.cleanup()

        # 重新初始化并启动
        if not self.initialize():
            print("Failed to reinitialize after reset")
            return False

        if not self.start():
            print("Failed to restart after reset")
            return False

        print("Game reset complete")
        return True

    def cleanup(self) -> None:
        """清理资源"""
        self.stop()
        self.session = None
        self.builder = None
        self.video_driver = None
        self.audio_driver = None
        self.input_driver = None
        self._initialized = False

    @property
    def is_running(self) -> bool:
        """检查会话是否正在运行"""
        return self._running

    @property
    def video_info(self) -> dict:
        """获取视频信息"""
        if self.video_driver:
            return {
                'width': getattr(self.video_driver, '_last_width', 0),
                'height': getattr(self.video_driver, '_last_height', 0),
                'pixel_format': getattr(self.video_driver, '_pixel_format', None),
            }
        return {}

    def __enter__(self):
        """上下文管理器入口"""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.cleanup()
