"""
Pygame 视频驱动

使用 pygame 库在桌面窗口中显示 Arduboy 游戏
适用于 macOS、Windows 和 Linux 桌面环境
"""
import numpy as np
from .base import VideoDriver


class PygameDriver(VideoDriver):
    """
    Pygame 驱动实现

    在桌面窗口中显示 Arduboy 游戏画面，支持缩放和多种显示模式

    Args:
        scale: 缩放倍数，默认 4 (即 128x64 -> 512x256)
        fullscreen: 是否全屏显示，默认 False
        caption: 窗口标题，默认 "PyArduboy"
        show_fps: 是否在窗口标题显示 FPS，默认 True
        color_mode: 显示颜色模式，可选：
                   - 'mono': 单色（黑白），默认
                   - 'green': 绿色单色（复古风格）
                   - 'amber': 琥珀色单色（复古风格）
                   - 'blue': 蓝色单色
    """

    # 颜色主题定义
    COLOR_THEMES = {
        'mono': {
            'background': (0, 0, 0),      # 黑色背景
            'foreground': (255, 255, 255)  # 白色前景
        },
        'green': {
            'background': (0, 20, 0),      # 深绿背景
            'foreground': (0, 255, 0)      # 亮绿前景
        },
        'amber': {
            'background': (20, 10, 0),     # 深琥珀背景
            'foreground': (255, 176, 0)    # 琥珀色前景
        },
        'blue': {
            'background': (0, 0, 20),      # 深蓝背景
            'foreground': (100, 200, 255)  # 亮蓝前景
        }
    }

    def __init__(
        self,
        scale: int = 4,
        fullscreen: bool = False,
        caption: str = "PyArduboy",
        show_fps: bool = True,
        color_mode: str = 'mono'
    ):
        super().__init__()
        self.scale = scale
        self.fullscreen = fullscreen
        self.caption = caption
        self.show_fps = show_fps
        self.color_mode = color_mode

        # 获取颜色主题
        if color_mode not in self.COLOR_THEMES:
            print(f"Warning: Unknown color mode '{color_mode}', using 'mono'")
            color_mode = 'mono'

        self.theme = self.COLOR_THEMES[color_mode]

        # 运行时属性
        self.screen = None
        self.clock = None
        self._running = False
        self._width = 0
        self._height = 0
        self._frame_count = 0

        # pygame 模块（延迟导入）
        self.pygame = None

    def init(self, width: int, height: int) -> bool:
        """
        初始化 pygame 显示窗口

        Args:
            width: Arduboy 屏幕宽度（128）
            height: Arduboy 屏幕高度（64）

        Returns:
            初始化成功返回 True
        """
        try:
            import pygame
            self.pygame = pygame
        except ImportError:
            print("Failed to import pygame")
            print("Please install: pip install pygame")
            return False

        try:
            # 初始化 pygame
            self.pygame.init()

            # 保存原始尺寸
            self._width = width
            self._height = height

            # 计算窗口尺寸
            window_width = width * self.scale
            window_height = height * self.scale

            # 创建窗口
            if self.fullscreen:
                self.screen = self.pygame.display.set_mode(
                    (window_width, window_height),
                    self.pygame.FULLSCREEN
                )
            else:
                self.screen = self.pygame.display.set_mode(
                    (window_width, window_height)
                )

            # 设置窗口标题
            self.pygame.display.set_caption(self.caption)

            # 创建时钟对象（用于 FPS 计算）
            self.clock = self.pygame.time.Clock()

            # 填充背景色
            self.screen.fill(self.theme['background'])
            self.pygame.display.flip()

            self._running = True
            self._frame_count = 0

            print(f"Pygame window initialized: {window_width}x{window_height}")
            print(f"Scale: {self.scale}x, Color mode: {self.color_mode}")

            return True

        except Exception as e:
            print(f"Failed to initialize pygame display: {e}")
            return False

    def render(self, frame_buffer: np.ndarray) -> None:
        """
        渲染一帧到 pygame 窗口

        Args:
            frame_buffer: 帧缓冲区，shape 为 (height, width, 3)，RGB 格式
        """
        if not self._running or self.screen is None:
            return

        try:
            # 处理 pygame 事件（必须调用，否则窗口无响应）
            for event in self.pygame.event.get():
                if event.type == self.pygame.QUIT:
                    self._running = False
                    return
                elif event.type == self.pygame.KEYDOWN:
                    if event.key == self.pygame.K_ESCAPE:
                        self._running = False
                        return

            # 将 RGB 帧转换为单色显示
            # 取 RGB 的平均值作为灰度
            gray = np.mean(frame_buffer, axis=2).astype(np.uint8)

            # 转换为单色（阈值 128）
            mono = gray > 128

            # 创建彩色图像
            colored = np.zeros_like(frame_buffer)
            bg = np.array(self.theme['background'], dtype=np.uint8)
            fg = np.array(self.theme['foreground'], dtype=np.uint8)

            # 应用颜色主题
            colored[~mono] = bg  # 背景色
            colored[mono] = fg   # 前景色

            # 创建 pygame surface
            surface = self.pygame.surfarray.make_surface(
                np.transpose(colored, (1, 0, 2))
            )

            # 缩放到窗口大小
            if self.scale != 1:
                window_size = (self._width * self.scale, self._height * self.scale)
                surface = self.pygame.transform.scale(surface, window_size)

            # 绘制到屏幕
            self.screen.blit(surface, (0, 0))

            # 更新显示
            self.pygame.display.flip()

            # 更新帧计数
            self._frame_count += 1

            # 更新窗口标题显示 FPS
            if self.show_fps and self._frame_count % 30 == 0:
                fps = self.clock.get_fps()
                self.pygame.display.set_caption(f"{self.caption} - FPS: {fps:.1f}")

            # 时钟 tick（不限制帧率，由主循环控制）
            self.clock.tick()

        except Exception as e:
            # 只在第一次错误时打印，避免刷屏
            if not hasattr(self, '_error_printed'):
                print(f"Error rendering frame: {e}")
                import traceback
                traceback.print_exc()
                self._error_printed = True

    def close(self) -> None:
        """关闭 pygame 窗口"""
        self._running = False
        if self.pygame:
            try:
                self.pygame.quit()
            except Exception:
                pass

    @property
    def is_running(self) -> bool:
        """检查驱动是否正在运行"""
        return self._running


class PygameDriverLarge(PygameDriver):
    """
    大尺寸 Pygame 驱动

    默认 8x 缩放，窗口更大，适合演示
    """

    def __init__(self, **kwargs):
        kwargs['scale'] = kwargs.get('scale', 8)
        super().__init__(**kwargs)


class PygameDriverFullscreen(PygameDriver):
    """
    全屏 Pygame 驱动

    默认全屏显示
    """

    def __init__(self, **kwargs):
        kwargs['fullscreen'] = True
        super().__init__(**kwargs)
