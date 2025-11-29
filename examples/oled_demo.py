#!/usr/bin/env python3
"""
PyArduboy OLED 示例

展示如何在 OLED 显示屏上运行 Arduboy 游戏
支持 SSD1305/SSD1306 等常见 OLED 显示屏
"""
import sys
import os

# 添加父目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from pyarduboy import PyArduboy
from pyarduboy.drivers.video.luma_oled import LumaOLEDDriver, LumaOLED32Driver
from pyarduboy.drivers.audio.null import NullAudioDriver
from pyarduboy.drivers.input.evdev_keyboard import EvdevKeyboardDriver


def main():
    """主函数"""
    # 配置
    CORE_PATH = "../core/arduous_libretro.so"

    # 从命令行获取游戏路径
    if len(sys.argv) > 1:
        GAME_PATH = sys.argv[1]
    else:
        GAME_PATH = "../roms/2048.hex"
        print(f"No game specified, using default: {GAME_PATH}")
        print(f"Usage: {sys.argv[0]} <game.hex>\n")

    # 检查文件是否存在
    if not os.path.exists(CORE_PATH):
        print(f"Error: Core file not found: {CORE_PATH}")
        return 1

    if not os.path.exists(GAME_PATH):
        print(f"Error: Game file not found: {GAME_PATH}")
        return 1

    # 创建 PyArduboy 实例
    print("Creating PyArduboy instance...")
    arduboy = PyArduboy(
        core_path=CORE_PATH,
        game_path=GAME_PATH,
        target_fps=60
    )

    # 设置驱动
    print("Setting up drivers...")

    # 视频驱动：128x64 OLED with SPI
    # 手动创建 SPI 设备以指定 GPIO 引脚
    try:
        from luma.core.interface.serial import spi
        from luma.oled.device import ssd1309
        import RPi.GPIO as GPIO

        # 设置 GPIO 引脚编号模式为 BCM
        GPIO.setmode(GPIO.BCM)

        # 使用 RPi.GPIO (backed by lgpio) 作为 GPIO 后端（树莓派 5 需要）
        # SPI 配置：rst=27, dc=25, bl=18
        serial = spi(port=0, device=0, gpio_DC=25, gpio_RST=27, gpio=GPIO)
        device = ssd1309(serial, width=128, height=64)

        # 创建驱动并传入已配置的设备
        video_driver = LumaOLEDDriver(device=device, width=128, height=64)
        arduboy.set_video_driver(video_driver)

        print("OLED display configured: 128x64 SSD1309 (SPI)")
    except Exception as e:
        print(f"Failed to configure OLED: {e}")
        return 1

    # 音频驱动（暂时使用空驱动，不播放声音）
    arduboy.set_audio_driver(NullAudioDriver())

    # 输入驱动（物理键盘 - evdev）
    input_driver = EvdevKeyboardDriver()
    arduboy.set_input_driver(input_driver)

    # 打印控制说明
    print("\n" + "="*50)
    print("Controls (Physical Keyboard):")
    print("  W - Up")
    print("  S - Down")
    print("  A - Left")
    print("  D - Right")
    print("  J - A Button")
    print("  K - B Button")
    print("  Enter - Start")
    print("  Space - Select")
    print("\nPress Ctrl+C to stop.")
    print("="*50 + "\n")

    # 运行游戏
    try:
        arduboy.run()
    except KeyboardInterrupt:
        print("\n\nStopped by user")
    finally:
        # 清理 OLED 显示屏和 GPIO
        print("Cleaning up...")
        try:
            # 清空 OLED 显示
            if 'device' in locals() and device is not None:
                device.clear()
                print("OLED display cleared")

            # 清理 GPIO
            if 'GPIO' in locals():
                GPIO.cleanup()
                print("GPIO cleanup completed")
        except Exception as e:
            print(f"Error during cleanup: {e}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
