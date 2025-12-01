"""
Luma.OLED 视频驱动

使用 luma.oled 库驱动 SSD1305/SSD1306 等 OLED 显示屏
"""
import numpy as np
from PIL import Image
from .base import VideoDriver


class LumaOLEDDriver(VideoDriver):
    """
    Luma.OLED 驱动实现

    支持常见的 I2C/SPI OLED 显示屏，如 SSD1305, SSD1306

    Args:
        device: luma.oled 设备实例（可选，如果不提供则自动创建）
        device_type: 设备类型，默认 'ssd1305'
        width: 显示宽度，默认 128
        height: 显示高度，默认 64（Arduboy 标准）
        rotate: 旋转角度（0, 1, 2, 3），默认 2
        interface: 接口类型 'i2c' 或 'spi'，默认 'i2c'
        crop_mode: 裁剪模式，用于适配不同高度的屏幕
                   - 'center': 裁剪中间部分（默认）
                   - 'top': 裁剪顶部
                   - 'bottom': 裁剪底部
                   - 'scale': 缩放以适应屏幕
    """

    def __init__(
        self,
        device=None,
        device_type: str = 'ssd1305',
        width: int = 128,
        height: int = 64,
        rotate: int = 2,
        interface: str = 'i2c',
        crop_mode: str = 'center'
    ):
        super().__init__()
        self.device = device
        self.device_type = device_type
        self.display_width = width
        self.display_height = height
        self.rotate = rotate
        self.interface = interface
        self.crop_mode = crop_mode

    def init(self, width: int, height: int) -> bool:
        """
        初始化 OLED 显示设备

        Args:
            width: Arduboy 屏幕宽度（128）
            height: Arduboy 屏幕高度（64）

        Returns:
            初始化成功返回 True
        """
        self._width = width
        self._height = height

        # 如果没有提供 device，尝试自动创建
        if self.device is None:
            try:
                if self.interface == 'i2c':
                    from luma.core.interface.serial import i2c
                    from luma.core.render import canvas
                    serial = i2c(port=1, address=0x3C)
                elif self.interface == 'spi':
                    from luma.core.interface.serial import spi
                    serial = spi(port=0, device=0)
                else:
                    print(f"Unknown interface: {self.interface}")
                    return False

                # 导入对应的设备类
                if self.device_type == 'ssd1305':
                    from luma.oled.device import ssd1305
                    self.device = ssd1305(
                        serial,
                        width=self.display_width,
                        height=self.display_height,
                        rotate=self.rotate
                    )
                elif self.device_type == 'ssd1306':
                    from luma.oled.device import ssd1306
                    self.device = ssd1306(
                        serial,
                        width=self.display_width,
                        height=self.display_height,
                        rotate=self.rotate
                    )
                else:
                    print(f"Unsupported device type: {self.device_type}")
                    return False

                print(f"OLED display initialized: {self.device.size}")

            except ImportError as e:
                print(f"Failed to import luma.oled: {e}")
                print("Please install: pip3 install luma.oled")
                return False
            except Exception as e:
                print(f"Failed to initialize OLED device: {e}")
                return False

        self._running = True
        return True

    def render(self, frame_buffer: np.ndarray) -> None:
        """
        渲染一帧到 OLED 显示屏

        Args:
            frame_buffer: 帧缓冲区，shape 为 (height, width, 3)，RGB 格式
        """
        if not self._running or self.device is None:
            return

        try:
            # 转换为 PIL Image
            img = Image.fromarray(frame_buffer, 'RGB')

            # 如果显示屏高度与 Arduboy 不同，需要裁剪或缩放
            if img.height != self.display_height:
                img = self._adjust_height(img)

            # 转换为灰度
            gray_img = img.convert('L')

            # 转换为 1-bit（黑白）
            bw_img = gray_img.convert('1')

            # 显示到 OLED
            self.device.display(bw_img)

        except Exception as e:
            # 只在第一次错误时打印，避免刷屏
            if not hasattr(self, '_error_printed'):
                print(f"Error rendering frame: {e}")
                self._error_printed = True

    def _adjust_height(self, img: Image.Image) -> Image.Image:
        """
        调整图像高度以适应显示屏

        Args:
            img: 原始图像

        Returns:
            调整后的图像
        """
        if self.crop_mode == 'scale':
            # 缩放以适应屏幕
            return img.resize((self.display_width, self.display_height), Image.LANCZOS)

        elif self.crop_mode == 'center':
            # 裁剪中间部分
            crop_y = (img.height - self.display_height) // 2
            return img.crop((0, crop_y, img.width, crop_y + self.display_height))

        elif self.crop_mode == 'top':
            # 裁剪顶部
            return img.crop((0, 0, img.width, self.display_height))

        elif self.crop_mode == 'bottom':
            # 裁剪底部
            crop_y = img.height - self.display_height
            return img.crop((0, crop_y, img.width, img.height))

        else:
            # 默认使用中心裁剪
            crop_y = (img.height - self.display_height) // 2
            return img.crop((0, crop_y, img.width, crop_y + self.display_height))

    def close(self) -> None:
        """关闭显示设备"""
        self._running = False
        if self.device:
            try:
                # 清空显示
                self.device.clear()
            except Exception:
                pass


class LumaOLED32Driver(LumaOLEDDriver):
    """
    专门用于 128x32 OLED 显示屏的驱动

    从 Arduboy 的 128x64 画面裁剪中间 32 像素高度
    """

    def __init__(self, device=None, device_type: str = 'ssd1305', **kwargs):
        kwargs['height'] = 32
        kwargs['crop_mode'] = 'center'
        super().__init__(device, device_type, **kwargs)
