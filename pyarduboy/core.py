"""
PyArduboy 核心类

提供高级 API 来运行 Arduboy 游戏，管理驱动插件
"""
import time
from typing import Optional
from .libretro_bridge import LibretroBridge
from .drivers.base import VideoDriver, AudioDriver, InputDriver


class PyArduboy:
    """
    PyArduboy 核心类

    这是主要的接口类，用于加载和运行 Arduboy 游戏。
    支持插拔式驱动系统，可以自定义视频、音频和输入驱动。

    Example:
        >>> from pyarduboy import PyArduboy
        >>> from pyarduboy.drivers.video.luma_oled import LumaOLEDDriver
        >>>
        >>> arduboy = PyArduboy(
        ...     core_path="./arduous_libretro.so",
        ...     game_path="./game.hex"
        ... )
        >>> arduboy.set_video_driver(LumaOLEDDriver())
        >>> arduboy.run()
    """

    # Arduboy 默认配置
    SCREEN_WIDTH = 128
    SCREEN_HEIGHT = 64
    TARGET_FPS = 60

    def __init__(
        self,
        core_path: str,
        game_path: str,
        target_fps: int = TARGET_FPS
    ):
        """
        初始化 PyArduboy

        Args:
            core_path: libretro 核心文件路径
            game_path: 游戏 ROM 文件路径
            target_fps: 目标帧率，默认 60 FPS
        """
        self.core_path = core_path
        self.game_path = game_path
        self.target_fps = target_fps
        self.frame_time = 1.0 / target_fps

        # LibRetro 桥接层
        self.bridge = LibretroBridge(core_path, game_path)

        # 驱动插件
        self.video_driver: Optional[VideoDriver] = None
        self.audio_driver: Optional[AudioDriver] = None
        self.input_driver: Optional[InputDriver] = None

        # 运行状态
        self._running = False
        self._frame_count = 0
        self._start_time = 0

    def set_video_driver(self, driver: VideoDriver) -> None:
        """
        设置视频驱动

        Args:
            driver: VideoDriver 实例
        """
        self.video_driver = driver

    def set_audio_driver(self, driver: AudioDriver) -> None:
        """
        设置音频驱动

        Args:
            driver: AudioDriver 实例
        """
        self.audio_driver = driver

    def set_input_driver(self, driver: InputDriver) -> None:
        """
        设置输入驱动

        Args:
            driver: InputDriver 实例
        """
        self.input_driver = driver

    def initialize(self) -> bool:
        """
        初始化所有组件

        Returns:
            初始化成功返回 True，失败返回 False
        """
        # 初始化 LibRetro 桥接层
        if not self.bridge.initialize():
            print("Failed to initialize LibRetro bridge")
            return False

        # 初始化视频驱动
        if self.video_driver:
            if not self.video_driver.init(self.SCREEN_WIDTH, self.SCREEN_HEIGHT):
                print("Failed to initialize video driver")
                return False

        # 初始化音频驱动
        if self.audio_driver:
            if not self.audio_driver.init():
                print("Failed to initialize audio driver")
                return False

        # 初始化输入驱动
        if self.input_driver:
            if not self.input_driver.init():
                print("Failed to initialize input driver")
                return False

        return True

    def run(self, max_frames: Optional[int] = None) -> None:
        """
        运行游戏主循环

        Args:
            max_frames: 最大运行帧数，None 表示无限运行
        """
        if not self.initialize():
            print("Initialization failed")
            return

        if not self.bridge.start():
            print("Failed to start emulation")
            return

        self._running = True
        self._frame_count = 0
        self._start_time = time.time()

        print(f"Starting Arduboy emulation...")
        print(f"Game: {self.game_path}")
        print(f"Target FPS: {self.target_fps}")
        if self.video_driver:
            print(f"Video Driver: {self.video_driver.__class__.__name__}")
        if self.audio_driver:
            print(f"Audio Driver: {self.audio_driver.__class__.__name__}")
        if self.input_driver:
            print(f"Input Driver: {self.input_driver.__class__.__name__}")
        print()

        try:
            while self._running:
                frame_start = time.time()

                # 处理输入
                if self.input_driver:
                    input_state = self.input_driver.poll()

                    # 检查 reset 按钮
                    if input_state.get('reset', False):
                        print("\n" + "="*60)
                        print("Reset button pressed!")
                        print("="*60 + "\n")
                        # 重置游戏
                        if self.bridge.reset():
                            self._frame_count = 0
                            self._start_time = time.time()
                        continue

                    # 转换输入状态到 LibRetro 格式
                    self.bridge.set_input_state(self._convert_input_state(input_state))

                # 运行一帧模拟
                self.bridge.run_frame()
                self._frame_count += 1

                # 渲染视频
                if self.video_driver:
                    frame = self.bridge.get_frame()
                    if frame is not None:
                        self.video_driver.render(frame)

                # 播放音频
                if self.audio_driver:
                    samples = self.bridge.get_audio_samples()
                    if samples is not None:
                        self.audio_driver.play_samples(samples)

                # 检查是否达到最大帧数
                if max_frames and self._frame_count >= max_frames:
                    break

                # 帧率控制
                frame_elapsed = time.time() - frame_start
                if frame_elapsed < self.frame_time:
                    time.sleep(self.frame_time - frame_elapsed)

                # 打印统计信息（每 300 帧）
                if self._frame_count % 300 == 0:
                    self._print_stats()

        except KeyboardInterrupt:
            print("\n\nStopping emulation...")
        except Exception as e:
            print(f"\nError during emulation: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.cleanup()

    def _convert_input_state(self, input_state: dict) -> dict:
        """
        将输入驱动的状态转换为 LibRetro 输入状态

        Args:
            input_state: 输入驱动返回的状态字典

        Returns:
            LibRetro 格式的输入状态
        """
        return {
            'up': input_state.get('up', False),
            'down': input_state.get('down', False),
            'left': input_state.get('left', False),
            'right': input_state.get('right', False),
            'a': input_state.get('a', False),
            'b': input_state.get('b', False),
            'select': input_state.get('select', False),
            'start': input_state.get('start', False),
            'x': False,
            'y': False,
            'l': False,
            'r': False,
            'l2': False,
            'r2': False,
            'l3': False,
            'r3': False,
        }

    def _print_stats(self) -> None:
        """打印运行统计信息"""
        elapsed = time.time() - self._start_time
        fps = self._frame_count / elapsed if elapsed > 0 else 0
        print(f"Frame {self._frame_count}: FPS={fps:.1f}")

    def stop(self) -> None:
        """停止运行"""
        self._running = False

    def cleanup(self) -> None:
        """清理资源"""
        self._running = False

        # 关闭驱动
        if self.video_driver:
            self.video_driver.close()
        if self.audio_driver:
            self.audio_driver.close()
        if self.input_driver:
            self.input_driver.close()

        # 清理 LibRetro 桥接层
        self.bridge.cleanup()

        print("Emulation stopped.")

    @property
    def is_running(self) -> bool:
        """检查是否正在运行"""
        return self._running

    @property
    def frame_count(self) -> int:
        """获取当前帧数"""
        return self._frame_count

    @property
    def fps(self) -> float:
        """获取当前实际帧率"""
        if not self._start_time or self._frame_count == 0:
            return 0.0
        elapsed = time.time() - self._start_time
        return self._frame_count / elapsed if elapsed > 0 else 0.0

    def __enter__(self):
        """上下文管理器入口"""
        self.initialize()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.cleanup()
