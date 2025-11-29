#!/usr/bin/env python3
"""
原始 evdev 事件测试
直接监听设备，显示所有原始事件，不经过任何过滤

运行方式: sudo python3 test_evdev_raw.py
"""
import sys
import select
from evdev import InputDevice, categorize, ecodes, list_devices


def find_keyboard():
    """查找键盘设备"""
    devices = [InputDevice(path) for path in list_devices()]

    print("Available input devices:")
    for i, device in enumerate(devices):
        print(f"  [{i}] {device.path}: {device.name}")
        capabilities = device.capabilities()
        if ecodes.EV_KEY in capabilities:
            keys = capabilities[ecodes.EV_KEY]
            if ecodes.KEY_A in keys or ecodes.KEY_W in keys:
                print(f"      ^ This looks like a keyboard")

    print()

    # 自动查找键盘
    for device in devices:
        capabilities = device.capabilities()
        if ecodes.EV_KEY in capabilities:
            keys = capabilities[ecodes.EV_KEY]
            if ecodes.KEY_A in keys or ecodes.KEY_W in keys:
                return device

    return None


def test_read_loop(device):
    """使用 read_loop() 测试"""
    print("\n" + "=" * 60)
    print("Method 1: Using device.read_loop()")
    print("=" * 60)
    print("Press any key... (Ctrl+C to stop)")
    print()

    event_count = 0
    try:
        for event in device.read_loop():
            event_count += 1
            print(f"[Event #{event_count}] time={event.sec}.{event.usec:06d}, "
                  f"type={event.type}, code={event.code}, value={event.value}")

            # 解析按键事件
            if event.type == ecodes.EV_KEY:
                key_name = ecodes.KEY.get(event.code, f"UNKNOWN({event.code})")
                state_name = {0: "RELEASED", 1: "PRESSED", 2: "REPEAT"}.get(event.value, "UNKNOWN")
                print(f"  → KEY: {key_name} {state_name}")
            print()

    except KeyboardInterrupt:
        print("\nStopped.")


def test_epoll(device):
    """使用 epoll + read() 测试"""
    print("\n" + "=" * 60)
    print("Method 2: Using epoll + device.read()")
    print("=" * 60)
    print("Press any key... (Ctrl+C to stop)")
    print()

    epoll = select.epoll()
    epoll.register(device.fileno(), select.EPOLLIN)

    event_count = 0
    poll_count = 0

    try:
        while True:
            poll_count += 1
            events = epoll.poll(timeout=1.0)

            if not events:
                print(f"[Poll #{poll_count}] No events (timeout)")
                continue

            print(f"[Poll #{poll_count}] Got {len(events)} epoll event(s)")

            # 读取所有待处理事件
            for event in device.read():
                event_count += 1
                print(f"  [Event #{event_count}] time={event.sec}.{event.usec:06d}, "
                      f"type={event.type}, code={event.code}, value={event.value}")

                # 解析按键事件
                if event.type == ecodes.EV_KEY:
                    key_name = ecodes.KEY.get(event.code, f"UNKNOWN({event.code})")
                    state_name = {0: "RELEASED", 1: "PRESSED", 2: "REPEAT"}.get(event.value, "UNKNOWN")
                    print(f"    → KEY: {key_name} {state_name}")
            print()

    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        epoll.unregister(device.fileno())
        epoll.close()


def main():
    print("=" * 60)
    print("Raw Evdev Event Test")
    print("=" * 60)
    print()

    # 列出所有设备
    all_devices = [InputDevice(path) for path in list_devices()]

    if not all_devices:
        print("✗ No input devices found!")
        return 1

    print("Available devices:")
    for i, dev in enumerate(all_devices):
        caps = dev.capabilities()
        is_kbd = ecodes.EV_KEY in caps and ecodes.KEY_A in caps.get(ecodes.EV_KEY, [])
        marker = "★ KEYBOARD" if is_kbd else ""
        print(f"  [{i}] {dev.path}: {dev.name} {marker}")
    print()

    # 让用户选择或自动选择
    choice = input("Select device number (or press Enter for auto-detect): ").strip()

    if choice.isdigit() and 0 <= int(choice) < len(all_devices):
        device = all_devices[int(choice)]
        print(f"✓ Using device: {device.name}")
    else:
        # 自动查找键盘设备
        device = find_keyboard()
        if not device:
            print("✗ No keyboard device found!")
            return 1
        print(f"✓ Auto-detected keyboard: {device.name}")

    print(f"  Path: {device.path}")
    print()

    # 尝试独占设备
    try:
        device.grab()
        print("✓ Device grabbed (exclusive access)")
    except Exception as e:
        print(f"✗ Could not grab device: {e}")
        print("  Events may leak to other programs")

    print()
    print("Select test method:")
    print("  1. read_loop() - blocking iterator")
    print("  2. epoll + read() - event polling (current implementation)")
    print()

    choice = input("Enter choice (1 or 2, default=2): ").strip()

    if choice == "1":
        test_read_loop(device)
    else:
        test_epoll(device)

    # 释放设备
    try:
        device.ungrab()
    except Exception:
        pass

    device.close()
    print("\n✓ Device closed")

    return 0


if __name__ == "__main__":
    sys.exit(main())
