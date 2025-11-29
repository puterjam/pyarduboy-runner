#!/usr/bin/env python3
"""
Arduboy 模拟器 - 使用 PyArduboy 架构
支持 Luma.OLED 驱动和物理键盘输入（evdev）

控制方式:
  W - 上
  S - 下
  A - 左
  D - 右
  J - A 按钮
  K - B 按钮
  R - Reset（重新加载游戏）

注意: 需要 root 权限访问键盘设备
      运行方式: sudo python3 run_arduboy.py <game.hex>
"""
import sys
import os

# 添加当前目录到 Python 路径
sys.path.insert(0, os.path.dirname(__file__))

from pyarduboy import PyArduboy
from pyarduboy.drivers.video.luma_oled import LumaOLEDDriver
from pyarduboy.drivers.audio.alsa import AlsaAudioDriver
from pyarduboy.drivers.audio.null import NullAudioDriver
from pyarduboy.drivers.input.evdev_keyboard import EvdevKeyboardDriver


def main():
    """主函数"""
    # 配置
    CORE_PATH = "./core/arduous_libretro.so"

    # 解析命令行参数
    if len(sys.argv) > 1:
        GAME_PATH = sys.argv[1]
    else:
        GAME_PATH = "./roms/2048.hex"
        print(f"No game specified, using default: {GAME_PATH}")
        print(f"Usage: {sys.argv[0]} <game.hex>\n")

    # 检查文件是否存在
    if not os.path.exists(CORE_PATH):
        print(f"Error: Core file not found: {CORE_PATH}")
        print(f"Please build the core first: cd core && ./build.sh")
        return 1

    if not os.path.exists(GAME_PATH):
        print(f"Error: Game file not found: {GAME_PATH}")
        print(f"\nUsage: {sys.argv[0]} <game.hex>")
        print(f"Example: {sys.argv[0]} ./roms/game.hex")
        return 1

    # 创建 PyArduboy 实例
    print(f"Initializing Arduboy emulator...")
    print(f"Core: {CORE_PATH}")
    print(f"Game: {GAME_PATH}\n")

    arduboy = PyArduboy(
        core_path=CORE_PATH,
        game_path=GAME_PATH,
        target_fps=60
    )

    # 设置驱动
    print("Setting up drivers...")

    # 视频驱动：OLED 显示屏
    try:
        # 尝试自动配置 OLED 设备
        serial = spi(port=0, device=0, gpio_DC=25, gpio_RST=27, gpio=GPIO)
        device = ssd1309(serial, width=128, height=64)

          # 创建驱动并传入已配置的设备
        video_driver = LumaOLEDDriver(device=device, width=128, height=64)
        arduboy.set_video_driver(video_driver)
        print("✓ OLED video driver configured (auto-detect)")

    except Exception as e:
        print(f"Failed to configure OLED with auto-detect: {e}")
        print("\nTrying manual SPI configuration...")

        try:
            # 手动配置 SPI OLED
            from luma.core.interface.serial import spi
            from luma.oled.device import ssd1309
            import RPi.GPIO as GPIO

            # 设置 GPIO
            GPIO.setmode(GPIO.BCM)

            # SPI 配置：DC=25, RST=27
            serial = spi(port=0, device=0, gpio_DC=25, gpio_RST=27, gpio=GPIO)
            device = ssd1309(serial, width=128, height=64)

            # 创建驱动并传入已配置的设备
            video_driver = LumaOLEDDriver(device=device, width=128, height=64)
            arduboy.set_video_driver(video_driver)

            print("✓ OLED video driver configured (SPI manual)")

            # 保存设备和 GPIO 引用以便清理
            arduboy._oled_device = device
            arduboy._gpio = GPIO

        except Exception as e2:
            print(f"Failed to configure OLED with SPI: {e2}")
            print("\nPlease check:")
            print("  1. OLED is connected properly")
            print("  2. I2C/SPI is enabled (raspi-config)")
            print("  3. luma.oled is installed: pip3 install luma.oled")
            return 1

    # 音频驱动（ALSA）
    try:
        # 使用更大的缓冲区减少 CPU 占用
        audio_driver = AlsaAudioDriver(period_size=4096)
        arduboy.set_audio_driver(audio_driver)
        print("✓ Audio driver configured (ALSA)")
    except Exception as e:
        print(f"Failed to configure ALSA audio: {e}")
        print("Falling back to null audio driver...")
        arduboy.set_audio_driver(AlsaAudioDriver())
        print("✓ Audio driver configured (null - no sound)")

    # 输入驱动（物理键盘 - evdev）
    try:
        input_driver = EvdevKeyboardDriver()
        arduboy.set_input_driver(input_driver)
        print("✓ Input driver configured (evdev keyboard)")
    except Exception as e:
        print(f"Failed to configure evdev keyboard: {e}")
        print("Make sure you:")
        print("  1. Install evdev: sudo pip3 install evdev")
        print("  2. Run with sudo: sudo python3 run_arduboy.py")
        return 1

    # 打印控制说明
    print("\n" + "="*60)
    print("Controls (Physical Keyboard):")
    print("  W / S / A / D  - Direction (Up/Down/Left/Right)")
    print("  J              - A Button")
    print("  K              - B Button")
    print("  R              - Reset (Reload Game)")
    print("\nPress Ctrl+C to stop.")
    print("="*60 + "\n")

    # 运行游戏
    try:
        arduboy.run()
    except KeyboardInterrupt:
        print("\n\nStopped by user")
    except Exception as e:
        print(f"\nError during emulation: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        # 清理 GPIO（如果手动配置了）
        if hasattr(arduboy, '_gpio'):
            try:
                print("Cleaning up GPIO...")
                arduboy._gpio.cleanup()
            except Exception as e:
                print(f"Error cleaning up GPIO: {e}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
