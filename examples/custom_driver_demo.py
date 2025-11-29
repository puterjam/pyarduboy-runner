#!/usr/bin/env python3
"""
PyArduboy 自定义驱动示例

展示如何创建自定义驱动插件
这个示例创建一个简单的 PIL 图像保存驱动
"""
import sys
import os
import numpy as np
from PIL import Image

# 添加父目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from pyarduboy import PyArduboy, VideoDriver
from pyarduboy.drivers.audio.null import NullAudioDriver


class ImageSaveDriver(VideoDriver):
    """
    自定义视频驱动：将每一帧保存为图像文件

    演示如何创建自定义驱动插件
    """

    def __init__(self, output_dir: str = "./frames", save_interval: int = 60):
        """
        初始化图像保存驱动

        Args:
            output_dir: 输出目录
            save_interval: 保存间隔（每 N 帧保存一次）
        """
        super().__init__()
        self.output_dir = output_dir
        self.save_interval = save_interval
        self.frame_count = 0

    def init(self, width: int, height: int) -> bool:
        """初始化驱动"""
        self._width = width
        self._height = height
        self._running = True

        # 创建输出目录
        os.makedirs(self.output_dir, exist_ok=True)
        print(f"Frames will be saved to: {self.output_dir}")
        print(f"Saving every {self.save_interval} frames")

        return True

    def render(self, frame_buffer: np.ndarray) -> None:
        """渲染一帧（保存为图像）"""
        self.frame_count += 1

        # 只保存指定间隔的帧
        if self.frame_count % self.save_interval == 0:
            # 转换为 PIL Image
            img = Image.fromarray(frame_buffer, 'RGB')

            # 保存文件
            filename = f"frame_{self.frame_count:06d}.png"
            filepath = os.path.join(self.output_dir, filename)
            img.save(filepath)

            print(f"Saved: {filename}")

    def close(self) -> None:
        """关闭驱动"""
        self._running = False
        print(f"\nTotal frames rendered: {self.frame_count}")
        print(f"Images saved: {self.frame_count // self.save_interval}")


def main():
    """主函数"""
    # 配置
    CORE_PATH = "../core/arduous_libretro.so"
    OUTPUT_DIR = "./output_frames"

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

    # 设置自定义驱动
    print("Setting up custom image save driver...")
    video_driver = ImageSaveDriver(
        output_dir=OUTPUT_DIR,
        save_interval=60  # 每 60 帧（1秒）保存一次
    )
    arduboy.set_video_driver(video_driver)
    arduboy.set_audio_driver(NullAudioDriver())

    # 运行游戏（运行 600 帧，保存 10 张图片）
    print("\nRunning game for 600 frames...")
    print("Press Ctrl+C to stop early.\n")

    try:
        arduboy.run(max_frames=600)
    except KeyboardInterrupt:
        print("\n\nStopped by user")

    print("\nDemo completed!")
    print(f"Check the '{OUTPUT_DIR}' directory for saved frames.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
