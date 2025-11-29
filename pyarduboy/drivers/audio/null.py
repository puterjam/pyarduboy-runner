"""
空音频驱动 - 不播放任何声音，用于无声模式或测试
"""
import numpy as np
from .base import AudioDriver


class NullAudioDriver(AudioDriver):
    """空音频驱动，不输出任何声音"""

    def init(self, sample_rate: int = 44100) -> bool:
        self._sample_rate = sample_rate
        self._running = True
        return True

    def play_samples(self, samples: np.ndarray) -> None:
        # 不做任何事情
        pass

    def close(self) -> None:
        self._running = False
