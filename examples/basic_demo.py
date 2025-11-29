#!/usr/bin/env python3
"""
PyArduboy 基础示例

展示如何使用 PyArduboy 库运行 Arduboy 游戏
这个示例使用空驱动（不显示、不播放声音），用于测试核心功能
"""
import sys
import os

# 添加父目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from pyarduboy import PyArduboy
from pyarduboy.drivers.video.null import NullVideoDriver
from pyarduboy.drivers.audio.null import NullAudioDriver


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

    # 设置驱动（使用空驱动，仅测试核心功能）
    print("Setting up drivers...")
    arduboy.set_video_driver(NullVideoDriver())
    arduboy.set_audio_driver(NullAudioDriver())

    # 运行游戏（运行 600 帧后自动停止，约 10 秒）
    print("\nRunning game for 600 frames (10 seconds)...")
    print("Press Ctrl+C to stop early.\n")

    try:
        arduboy.run(max_frames=600)
    except KeyboardInterrupt:
        print("\n\nStopped by user")

    print("\nDemo completed!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
