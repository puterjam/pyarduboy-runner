#!/usr/bin/env python3
"""
测试 evdev 键盘驱动
单独运行此脚本来验证按键输入是否正常

运行方式: sudo python3 test_keyboard.py
"""
import sys
import time
import os

# 添加当前目录到 Python 路径
sys.path.insert(0, os.path.dirname(__file__))

from pyarduboy.drivers.input.evdev_keyboard import EvdevKeyboardDriver


def main():
    print("=" * 60)
    print("Evdev Keyboard Test")
    print("=" * 60)
    print()
    print("This script will test the evdev keyboard driver.")
    print("Press keys and see if they are detected.")
    print("Press Ctrl+C to exit.")
    print()
    print("=" * 60)
    print()

    # 创建键盘驱动
    try:
        driver = EvdevKeyboardDriver()
        print("✓ Driver created")
    except Exception as e:
        print(f"✗ Failed to create driver: {e}")
        return 1

    # 初始化驱动
    print("\nInitializing driver...")
    if not driver.init():
        print("✗ Failed to initialize driver")
        return 1

    print("\n" + "=" * 60)
    print("Driver initialized successfully!")
    print("Now monitoring keyboard input...")
    print("Press any mapped keys to test.")
    print("=" * 60)
    print()

    # 记录上一次的按键状态
    last_state = driver.poll()

    try:
        frame = 0
        while True:
            # 轮询当前状态
            current_state = driver.poll()

            # 检测状态变化
            changed = False
            for key, value in current_state.items():
                if value != last_state.get(key, False):
                    changed = True
                    status = "PRESSED" if value else "RELEASED"
                    print(f"[Frame {frame:06d}] Button '{key}': {status}")

            # 如果有变化，打印完整状态
            if changed:
                pressed_keys = [k for k, v in current_state.items() if v]
                if pressed_keys:
                    print(f"  → Currently pressed: {', '.join(pressed_keys)}")
                else:
                    print(f"  → All keys released")
                print()

            last_state = current_state.copy()
            frame += 1

            # 60 FPS 轮询
            time.sleep(1.0 / 60)

    except KeyboardInterrupt:
        print("\n\n" + "=" * 60)
        print("Test stopped by user")
        print("=" * 60)
    finally:
        print("\nClosing driver...")
        driver.close()
        print("✓ Driver closed")

    return 0


if __name__ == "__main__":
    sys.exit(main())
