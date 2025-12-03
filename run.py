#!/usr/bin/env python3
"""
Arduboy 模拟器 - 使用 PyArduboy 架构
支持 Luma.OLED 驱动和 Pygame 桌面窗口

控制方式:
  W - 上
  S - 下
  A - 左
  D - 右
  J - A 按钮
  K - B 按钮
  R - Reset（重新加载游戏）

注意:
  - Luma.OLED 驱动需要 root 权限访问键盘设备
  - Pygame 驱动可以直接运行，使用键盘输入
"""
import sys
import os
import argparse

# 添加当前目录到 Python 路径
sys.path.insert(0, os.path.dirname(__file__))

from pyarduboy import PyArduboy
from pyarduboy.drivers.video.luma import LumaOLEDDriver
from pyarduboy.drivers.video.pygame import PygameDriver

from pyarduboy.drivers.audio.alsa import AlsaAudioDriver
from pyarduboy.drivers.audio.null import NullAudioDriver
from pyarduboy.drivers.audio.pyaudio import PyAudioDriver
from pyarduboy.drivers.audio.pygame_mixer import PygameMixerDriver

from pyarduboy.drivers.input.evdev import EvdevKeyboardDriver


def setup_luma_driver(arduboy):
    """设置 Luma.OLED 视频驱动"""
    try:
        # 尝试自动配置 OLED 设备
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

        print("✓ OLED video driver configured (SPI)")

        # 保存设备和 GPIO 引用以便清理
        arduboy._oled_device = device
        arduboy._gpio = GPIO

        return True

    except ImportError as e:
        print(f"Failed to import OLED dependencies: {e}")
        print("Please install: pip3 install luma.oled")
        print("Also ensure RPi.GPIO is available on Raspberry Pi")
        return False
    except Exception as e:
        print(f"Failed to configure OLED: {e}")
        print("\nPlease check:")
        print("  1. OLED is connected properly")
        print("  2. SPI is enabled (raspi-config)")
        print("  3. Running with sudo (required for GPIO access)")
        return False


def setup_pygame_driver(arduboy, scale=4, color_mode='mono'):
    """设置 Pygame 视频驱动"""
    try:
        video_driver = PygameDriver(scale=scale, color_mode=color_mode)
        arduboy.set_video_driver(video_driver)
        print(f"✓ Pygame video driver configured (scale={scale}x, color={color_mode})")
        return True
    except ImportError:
        print("Failed to import pygame")
        print("Please install: pip install pygame")
        return False
    except Exception as e:
        print(f"Failed to configure pygame: {e}")
        return False


def setup_evdev_input(arduboy):
    """设置 evdev 键盘输入驱动（Linux 物理键盘）"""
    try:
        input_driver = EvdevKeyboardDriver()
        arduboy.set_input_driver(input_driver)
        print("✓ Input driver configured (evdev keyboard)")
        return True
    except Exception as e:
        print(f"Failed to configure evdev keyboard: {e}")
        print("Make sure you:")
        print("  1. Install evdev: sudo pip3 install evdev")
        print("  2. Run with sudo: sudo python3 run.py")
        return False


def setup_pygame_input(arduboy):
    """设置 Pygame 键盘输入驱动（桌面）"""
    try:
        # 使用 WASD 模式的 pygame input 驱动
        from pyarduboy.drivers.input.pygame import PygameKeyboardDriverWASD
        input_driver = PygameKeyboardDriverWASD()
        arduboy.set_input_driver(input_driver)
        print("✓ Input driver configured (pygame keyboard - WASD mode)")
        return True
    except ImportError:
        print("Note: Pygame keyboard driver not found, controls may not work")
        print("      You can implement pyarduboy/drivers/input/pygame_keyboard.py")
        return False


def setup_alsa_audio(arduboy):
    """设置 ALSA 音频驱动"""
    try:
        audio_driver = AlsaAudioDriver(volume=1)
        arduboy.set_audio_driver(audio_driver)
        print("✓ Audio driver configured (ALSA)")
        return True
    except Exception as e:
        print(f"Failed to configure ALSA audio: {e}")
        print("Falling back to null audio driver...")
        arduboy.set_audio_driver(NullAudioDriver())
        print("✓ Audio driver configured (null - no sound)")
        return False


def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(
        description='PyArduboy - Arduboy emulator for Raspberry Pi and Desktop',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # 使用默认 Luma.OLED 驱动（需要 sudo）
  sudo python3 run.py game.hex

  # 使用 Pygame 桌面窗口
  python3 run.py game.hex -v pygame

  # Pygame 窗口，绿色主题，8x 缩放
  python3 run.py game.hex -v pygame --scale 8 --color green

  # 查看可用的颜色主题
  python3 run.py game.hex -v pygame --color amber
        """
    )

    parser.add_argument('game', nargs='?', default='./roms/2048.hex',
                        help='游戏 ROM 文件路径 (default: ./roms/2048.hex)')
    parser.add_argument('-v', '--video', choices=['luma', 'pygame'], default='luma',
                        help='视频驱动选择: luma (OLED显示屏) 或 pygame (桌面窗口) (default: luma)')
    parser.add_argument('--scale', type=int, default=4,
                        help='Pygame 窗口缩放倍数 (default: 4)')
    parser.add_argument('--color', choices=['mono', 'green', 'amber', 'blue'], default='mono',
                        help='Pygame 颜色主题 (default: mono)')

    args = parser.parse_args()

    GAME_PATH = args.game
    VIDEO_DRIVER = args.video

    # 检查游戏文件是否存在
    if not os.path.exists(GAME_PATH):
        print(f"Error: Game file not found: {GAME_PATH}")
        print(f"\nUsage: {sys.argv[0]} <game.hex> [options]")
        print(f"Example: {sys.argv[0]} ./roms/game.hex -v pygame")
        return 1

    # 创建 PyArduboy 实例(自动判断核心路径)
    print(f"Initializing Arduboy emulator...")
    print(f"Game: {GAME_PATH}")
    print(f"Video: {VIDEO_DRIVER}\n")

    try:
        arduboy = PyArduboy(
            game_path=GAME_PATH,
            # core_name="arduous",  # 使用 arduous 核心
            target_fps=60
        )
        print(f"Core: {arduboy.core_path} (auto-detected)\n")
    except ValueError as e:
        print(f"Error: {e}")
        return 1
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("\nPlease download the ardens core:")
        print("  python download_core.py ardens")
        return 1

    # 检查核心文件是否存在
    if not os.path.exists(arduboy.core_path):
        print(f"Error: Core file not found: {arduboy.core_path}")
        print(f"Please build the core first: cd core && ./build_core.sh")
        return 1

    # 设置驱动
    print("Setting up drivers...\n")

    # 视频驱动
    if VIDEO_DRIVER == 'luma':
        if not setup_luma_driver(arduboy):
            return 1
    elif VIDEO_DRIVER == 'pygame':
        if not setup_pygame_driver(arduboy, scale=args.scale, color_mode=args.color):
            return 1

    # 音频驱动
    if VIDEO_DRIVER == 'luma':
        # Linux 环境，尝试使用 ALSA
        setup_alsa_audio(arduboy)
    else:
        # 桌面环境，使用 PyAudio（非阻塞 callback 模式，不影响 FPS）
        # 使用 Ardens 标准配置：50kHz, 单声道
        try:
            audio_driver = PygameMixerDriver(volume=1)
            arduboy.set_audio_driver(audio_driver)
            print("✓ Audio driver configured (PyAudio - 50kHz)")
        except ImportError:
            print("PyAudio not available, using null audio driver")
            arduboy.set_audio_driver(NullAudioDriver())
            print("✓ Audio driver configured (null - no sound)")
        except Exception as e:
            print(f"Failed to initialize PyAudio: {e}")
            import traceback
            traceback.print_exc()
            arduboy.set_audio_driver(NullAudioDriver())
            print("✓ Audio driver configured (null - no sound)")

    # 输入驱动
    if VIDEO_DRIVER == 'luma':
        # Linux 环境，使用 evdev
        if not setup_evdev_input(arduboy):
            return 1
    else:
        # 桌面环境，尝试使用 pygame 键盘
        if not setup_pygame_input(arduboy):
            # 如果没有 pygame 输入驱动，使用 null 驱动
            from pyarduboy.drivers.input.null import NullInputDriver
            arduboy.set_input_driver(NullInputDriver())
            print("⚠ Using null input driver (no controls)")

    # 打印控制说明
    print("\n" + "="*60)
    if VIDEO_DRIVER == 'luma':
        print("Controls (Physical Keyboard - evdev):")
        print("  W / S / A / D  - Direction (Up/Down/Left/Right)")
        print("  J              - A Button")
        print("  K              - B Button")
        print("  R              - Reset (Reload Game)")
    else:
        print("Controls (Pygame Keyboard - WASD Mode):")
        print("  W / S / A / D  - Direction (Up/Down/Left/Right)")
        print("  J              - A Button")
        print("  K              - B Button")
        print("  R              - Reset (Reload Game)")
        print("  ESC            - Quit")
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
        # 清理 GPIO（如果使用了 Luma 驱动）
        if hasattr(arduboy, '_gpio'):
            try:
                print("Cleaning up GPIO...")
                arduboy._gpio.cleanup()
            except Exception as e:
                print(f"Error cleaning up GPIO: {e}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
