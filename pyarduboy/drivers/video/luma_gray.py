"""
自定义 Luma.OLED 驱动 - 绕过 SPI 频率限制

直接使用 spidev 设置任意 SPI 频率,然后传给 luma.oled 设备
"""
import numpy as np
import time
import os
from datetime import datetime
from PIL import Image
from .base import VideoDriver


def save_image_debug(img, prefix="frame", save_dir="./tmp"):
    """
    调试用图像保存函数

    Args:
        img: PIL Image 对象或 numpy 数组
        prefix: 文件名前缀
        save_dir: 保存目录,默认 ./tmp

    Returns:
        保存的文件路径
    """
    try:
        # 确保保存目录存在
        os.makedirs(save_dir, exist_ok=True)

        # 生成带时间戳的文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"{prefix}.png"
        filepath = os.path.join(save_dir, filename)

        # 如果是 numpy 数组,先转换为 PIL Image
        if isinstance(img, np.ndarray):
            # 判断数组类型
            if img.ndim == 3:  # RGB/RGBA 彩色图像
                pil_img = Image.fromarray(img.astype(np.uint8), 'RGB')
            elif img.ndim == 2:  # 灰度图像
                pil_img = Image.fromarray(img.astype(np.uint8), 'L')
            else:
                print(f"[DEBUG] Unsupported array shape: {img.shape}")
                return None
        else:
            # 已经是 PIL Image
            pil_img = img

        # 保存图像
        pil_img.save(filepath)
        print(f"[DEBUG] Image saved: {filepath}")

        return filepath
    except Exception as e:
        print(f"[DEBUG] Failed to save image: {e}")
        import traceback
        traceback.print_exc()
        return None


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


class LumaGrayDriver(VideoDriver):
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
        refresh_hz: int = 180
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

        # 自适应阈值缓存（避免每帧剧烈变化）
        self._adaptive_thresholds = None

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
            if self.gray_mode and self.planes >= 2:
                # 先统一做成灰度 ndarray
                # frame_buffer: H x W x 3, uint8
                img = frame_buffer.astype(np.uint8)

                # [调试] 保存原始 RGB 图像
                # save_image_debug(img, prefix="rgb_original")
                
                gray = (0.299 * img[..., 0] +
                        0.587 * img[..., 1] +
                        0.114 * img[..., 2]).astype(np.uint8)

                # [调试] 保存灰度图像（0-255）
                # save_image_debug(gray, prefix="gray_0-255")

                # ------ 时间灰度模式（ArduboyG 风格）------
                # 先把灰度映射到 0..3

                # 策略 1: 线性映射
                # 0..63 → 0, 64..127 → 1, 128..191 → 2, 192..255 → 3
                # levels = (gray.astype(np.uint16) * 4 // 256).astype(np.uint8)

                # 策略 2: 调整阈值，增强中间灰度
                # 0..48 → 0, 49..112 → 1, 113..192 → 2, 193..255 → 3
                levels = np.zeros_like(gray)
                levels[gray > 48] = 1
                levels[gray > 112] = 2
                levels[gray > 192] = 3

                # 策略 3: 更激进的中间值增强
                # 0..32 → 0, 33..96 → 1, 97..160 → 2, 161..255 → 3
                # levels = np.zeros_like(gray)
                # levels[gray > 32] = 1
                # levels[gray > 96] = 2
                # levels[gray > 160] = 3

                # 策略 4: Gamma 校正后映射 (增强暗部细节)
                # gamma = 2.2
                # gray_gamma = np.power(gray / 255.0, 1.0/gamma) * 255
                # levels = (gray_gamma.astype(np.uint16) * 4 // 256).astype(np.uint8)

                # 策略 5: 自适应直方图均衡化（已禁用，会导致花屏）
                # 根据实际图像的灰度分布，让每个 level 包含大约 25% 的像素
                # sorted_gray = np.sort(gray.flatten())
                # q1 = sorted_gray[len(sorted_gray) // 4]
                # q2 = sorted_gray[len(sorted_gray) // 2]
                # q3 = sorted_gray[len(sorted_gray) * 3 // 4]
                # levels = np.zeros_like(gray)
                # levels[gray > q1] = 1
                # levels[gray > q2] = 2
                # levels[gray > q3] = 3
                # print(f"[DEBUG] Adaptive thresholds: {q1}, {q2}, {q3}")

                # 策略 6: 固定阈值，针对 Arduboy 游戏优化（当前使用）
                # Arduboy 游戏通常是黑底白字，使用固定阈值更稳定
                # levels = np.zeros_like(gray)
                # levels[gray > 85] = 1   # 33% 亮度 → 深灰
                # levels[gray > 170] = 2  # 67% 亮度 → 浅灰
                # levels[gray > 220] = 3  # 86% 亮度 → 白色

                # [调试] 保存 levels 图像（0-3，放大到 0-255 以便查看）
                # save_image_debug(levels * 85, prefix="levels_0-3")

                # [调试] 统计每个 level 的像素数量
                # unique, counts = np.unique(levels, return_counts=True)
                # total_pixels = levels.size
                # print(f"[DEBUG] Level distribution:")
                # for lv, cnt in zip(unique, counts):
                #     percentage = (cnt / total_pixels) * 100
                #     print(f"  Level {lv}: {cnt:5d} pixels ({percentage:5.1f}%)")

                plane_dt = 1.0 / max(self.refresh_hz, 1)

                for plane in range(self.planes):
                    # 对应 ArduboyG 的 planeColor：
                    # L4_Triplane: bit = (color > plane)
                    # plane=0: levels>0 → 显示 levels 为 1,2,3 的像素
                    # plane=1: levels>1 → 显示 levels 为 2,3 的像素
                    # plane=2: levels>2 → 显示 levels 为 3 的像素
                    mask = (levels > plane)

                    # 转成 0/255 的 2D 数组，再转成 1bit Image
                    plane_bytes = (mask.astype(np.uint8) * 255)
                    bw_img = Image.fromarray(plane_bytes, mode='L').convert('1')

                    # [调试] 保存每个 plane（注释掉以提高性能）
                    # save_image_debug(bw_img, prefix=f"plane{plane}")

                    self.device.display(bw_img)
                    time.sleep(plane_dt)
                    
            else:
                # 转换为 PIL Image
                img = Image.fromarray(frame_buffer, 'RGB')

                # [调试] 保存原始 RGB 图像 (需要时取消注释)
                # save_image_debug(img, prefix="rgb_frame")

                # 转换为灰度并二值化
                # convert('1') 自动使用阈值 128 进行二值化
                bw_img = img.convert('L').convert('1')

                # [调试] 保存二值化图像 (需要时取消注释)
                # save_image_debug(bw_img, prefix="bw_frame")

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
