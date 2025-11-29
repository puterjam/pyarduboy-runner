#!/usr/bin/env python3
"""
列出所有输入设备的详细信息
帮助选择正确的键盘设备
"""
from evdev import InputDevice, ecodes, list_devices


def main():
    print("=" * 70)
    print("All Input Devices")
    print("=" * 70)
    print()

    devices = [InputDevice(path) for path in list_devices()]

    if not devices:
        print("No input devices found!")
        return 1

    for i, device in enumerate(devices):
        print(f"[{i}] {device.path}")
        print(f"    Name: {device.name}")
        print(f"    Physical: {device.phys}")
        print(f"    Uniq: {device.uniq}")

        # 显示能力
        capabilities = device.capabilities()
        print(f"    Capabilities:")

        for ev_type, codes in capabilities.items():
            type_name = ecodes.EV.get(ev_type, f"UNKNOWN({ev_type})")
            print(f"      - {type_name}: ", end="")

            if ev_type == ecodes.EV_KEY:
                # 检查按键类型
                has_letters = any(code in codes for code in [
                    ecodes.KEY_A, ecodes.KEY_W, ecodes.KEY_J, ecodes.KEY_K
                ])
                has_arrows = any(code in codes for code in [
                    ecodes.KEY_UP, ecodes.KEY_DOWN, ecodes.KEY_LEFT, ecodes.KEY_RIGHT
                ])
                has_numbers = any(code in codes for code in [
                    ecodes.KEY_1, ecodes.KEY_2, ecodes.KEY_3
                ])
                has_mouse = any(code in codes for code in [
                    ecodes.BTN_LEFT, ecodes.BTN_RIGHT, ecodes.BTN_MIDDLE
                ])

                features = []
                if has_letters:
                    features.append("letters")
                if has_arrows:
                    features.append("arrows")
                if has_numbers:
                    features.append("numbers")
                if has_mouse:
                    features.append("mouse_buttons")

                print(f"{len(codes)} keys [{', '.join(features)}]")

                # 判断设备类型
                if has_letters and has_numbers:
                    print(f"      ★ This looks like a FULL KEYBOARD")
                elif has_letters or has_arrows:
                    print(f"      → This might be a keyboard")
                elif has_mouse:
                    print(f"      → This is a mouse")
            else:
                print(f"{len(codes)} codes")

        print()

    print("=" * 70)
    print("Recommendation:")
    print("  Look for devices marked with ★ (full keyboard)")
    print("  Use the device path (e.g., /dev/input/event0) in your tests")
    print("=" * 70)

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
