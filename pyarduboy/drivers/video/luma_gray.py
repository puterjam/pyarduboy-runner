"""
自定义 Luma.OLED 驱动 - 绕过 SPI 频率限制

直接使用 spidev 设置任意 SPI 频率,然后传给 luma.oled 设备
"""
import numpy as np
import time
from PIL import Image
from .base import VideoDriver


class SPISerial:
    """
    自定义 SPI 串口类,支持任意频率

    兼容 luma.core.interface.serial.spi 接口,但绕过频率限制
    """
    def __init__(self, bus=0, device=0, gpio_DC=25, gpio_RST=27, spi_speed_hz=10000000, gpio=None):
        import spidev

        self._spi = spidev.SpiDev()
        self._spi.open(bus, device)
        self._spi.max_speed_hz = spi_speed_hz  # 直接设置任意频率!
        self._spi.mode = 0

        self._gpio = gpio
        self._DC = gpio_DC
        self._RST = gpio_RST

        # 设置 GPIO 引脚
        if self._gpio:
            self._gpio.setup(self._DC, self._gpio.OUT)
            self._gpio.setup(self._RST, self._gpio.OUT)

            # 复位 OLED
            self._gpio.output(self._RST, self._gpio.LOW)
            import time
            time.sleep(0.01)
            self._gpio.output(self._RST, self._gpio.HIGH)

            # 等待复位稳定
            time.sleep(0.1)

    def command(self, *cmd):
        """发送命令到 OLED"""
        if self._gpio:
            self._gpio.output(self._DC, self._gpio.LOW)  # 命令模式
        self._spi.writebytes(list(cmd))

    def data(self, data):
        """发送数据到 OLED"""
        if self._gpio:
            self._gpio.output(self._DC, self._gpio.HIGH)  # 数据模式

        # 转换数据格式
        if isinstance(data, (list, tuple)):
            self._spi.writebytes(list(data))
        else:
            self._spi.writebytes(list(data))

    def cleanup(self):
        """清理资源"""
        self._spi.close()


class LumaCustomSPIDriver(VideoDriver):
    """
    使用自定义 SPI 的 Luma.OLED 驱动

    支持任意 SPI 频率,绕过 luma 的频率限制

    Args:
        device_type: 设备类型 'ssd1309', 'ssd1306' 等
        width: 显示宽度
        height: 显示高度
        spi_speed_hz: SPI 频率(Hz),支持任意值! 例如 10000000 (10MHz)
        gpio_DC: DC 引脚
        gpio_RST: RST 引脚
        rotate: 旋转角度
        dither_mode: 抖动模式 'none', 'floyd', 'threshold'
    """

    def __init__(
        self,
        device_type: str = 'ssd1309',
        width: int = 128,
        height: int = 64,
        spi_speed_hz: int = 10000000,
        gpio_DC: int = 25,
        gpio_RST: int = 27,
        rotate: int = 0,
        dither_mode: str = 'none',
        gray_mode: bool = True,
        planes: int = 3,
        refresh_hz: int = 300
    ):
        super().__init__()
        self.device_type = device_type
        self.display_width = width
        self.display_height = height
        self.spi_speed_hz = spi_speed_hz
        self.gpio_DC = gpio_DC
        self.gpio_RST = gpio_RST
        self.rotate = rotate
        self.dither_mode = dither_mode
        
        # 新增参数
        self.gray_mode = gray_mode
        self.planes = planes
        self.refresh_hz = refresh_hz
        
        self.device = None
        self._serial = None

        # 灰度模式状态
        self._plane_counter = 0  # 当前 plane 索引 (0..planes-1)
        self._cached_levels = None  # 缓存的灰度 level 数组
        self._last_frame_id = None  # 用于检测帧是否更新

    def init(self, width: int, height: int) -> bool:
        """初始化 OLED 显示设备"""
        self._width = width
        self._height = height

        try:
            import RPi.GPIO as GPIO
            from luma.oled.device import ssd1309, ssd1306

            # 设置 GPIO
            GPIO.setmode(GPIO.BCM)

            # 创建自定义 SPI 串口(支持任意频率!)
            self._serial = SPISerial(
                bus=0,
                device=0,
                gpio_DC=self.gpio_DC,
                gpio_RST=self.gpio_RST,
                spi_speed_hz=self.spi_speed_hz,
                gpio=GPIO
            )

            # 创建 luma 设备
            if self.device_type == 'ssd1309':
                self.device = ssd1309(
                    self._serial,
                    width=self.display_width,
                    height=self.display_height,
                    rotate=self.rotate
                )
            elif self.device_type == 'ssd1306':
                self.device = ssd1306(
                    self._serial,
                    width=self.display_width,
                    height=self.display_height,
                    rotate=self.rotate
                )
            else:
                print(f"Unsupported device type: {self.device_type}")
                return False
            
            print(f"✓ Custom OLED initialized: {self.display_width}x{self.display_height} @ {self.spi_speed_hz/1e6:.1f} MHz")
            self._running = True
            return True

        except ImportError as e:
            print(f"Failed to import dependencies: {e}")
            return False
        except Exception as e:
            print(f"Failed to initialize OLED: {e}")
            import traceback
            traceback.print_exc()
            return False

    def render(self, frame_buffer: np.ndarray) -> None:
        """渲染一帧到 OLED"""
        if not self._running or self.device is None:
            return

        try:
            # 先统一做成灰度 ndarray
            # frame_buffer: H x W x 3, uint8
            rgb = frame_buffer.astype(np.uint8)
            # 简单加权：0.299R + 0.587G + 0.114B
            gray = (0.299 * rgb[..., 0] +
                    0.587 * rgb[..., 1] +
                    0.114 * rgb[..., 2]).astype(np.uint8)
            
            if self.gray_mode and self.planes >= 2:
                # ------ 时间灰度模式（ArduboyG 风格）------
                # 先把灰度映射到 0..3
                # 0..63 → 0, 64..127 → 1, 128..191 → 2, 192..255 → 3
                levels = (gray.astype(np.uint16) * 4 // 256).astype(np.uint8)  # 2bit 灰度
                
                plane_dt = 1.0 / max(self.refresh_hz, 1)

                for plane in range(self.planes):
                    # 对应 ArduboyG 的 planeColor：
                    # L4_Triplane: bit = (color > plane)
                    mask = (levels > plane)
                    
                    # 转成 0/255 的 2D 数组，再转成 1bit Image
                    plane_bytes = (mask.astype(np.uint8) * 255)
                    bw_img = Image.fromarray(plane_bytes, mode='L').convert('1')

                    self.device.display(bw_img)
                    time.sleep(plane_dt)

            else:
                # 转换为 PIL Image
                img = Image.fromarray(frame_buffer, 'RGB')

                # 转换为灰度
                gray_img = img.convert('L')
                bw_img = gray_img.point(lambda x: 255 if x > 128 else 0, mode='1')

            # 显示到 OLED
            self.device.display(bw_img)

        except Exception as e:
            if not hasattr(self, '_error_printed'):
                print(f"Error rendering frame: {e}")
                self._error_printed = True

    def close(self) -> None:
        """关闭显示设备"""
        self._running = False
        if self.device:
            try:
                self.device.clear()
            except Exception:
                pass
        if self._serial:
            try:
                self._serial.cleanup()
            except Exception:
                pass
