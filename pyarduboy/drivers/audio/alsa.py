"""
ALSA 音频驱动
使用 pyalsaaudio 库播放音频
适合在树莓派等 Linux 系统上使用
"""
import numpy as np
from typing import Optional
from .base import AudioDriver

try:
    import alsaaudio
    ALSA_AVAILABLE = True
except ImportError:
    ALSA_AVAILABLE = False


class AlsaAudioDriver(AudioDriver):
    """
    ALSA 音频驱动

    使用 pyalsaaudio 库播放音频，适合树莓派等 Linux 系统

    Args:
        device: ALSA 设备名称，默认 'default'
        sample_rate: 采样率，默认 44100 Hz
        channels: 声道数，默认 2（立体声）
        period_size: 周期大小，默认 1024
    """

    def __init__(
        self,
        device: str = 'default',
        sample_rate: int = 44100,
        channels: int = 2,
        period_size: int = 1024
    ):
        """
        初始化 ALSA 音频驱动

        Args:
            device: ALSA 设备名称
            sample_rate: 采样率
            channels: 声道数（1=单声道，2=立体声）
            period_size: 周期大小（缓冲区大小）
        """
        if not ALSA_AVAILABLE:
            raise ImportError(
                "alsaaudio library not found. Please install it:\n"
                "  sudo apt-get install python3-pyaudio python3-alsaaudio\n"
                "or\n"
                "  pip3 install pyalsaaudio"
            )

        self.device_name = device
        self._sample_rate = sample_rate  # 使用 _sample_rate（基类定义为 property）
        self.channels = channels
        self.period_size = period_size
        self.pcm: Optional[alsaaudio.PCM] = None
        self._running = False

    def init(self, sample_rate: int = 44100) -> bool:
        """
        初始化 ALSA 音频设备

        Args:
            sample_rate: 采样率，默认 44100 Hz

        Returns:
            初始化成功返回 True，失败返回 False
        """
        if self._running:
            return True

        self._sample_rate = sample_rate  # 使用 _sample_rate（基类定义为 property）

        try:
            # 创建 PCM 对象（使用非阻塞模式）
            self.pcm = alsaaudio.PCM(
                type=alsaaudio.PCM_PLAYBACK,
                mode=alsaaudio.PCM_NONBLOCK,  # 非阻塞模式，避免阻塞主循环
                device=self.device_name
            )

            # 配置音频参数
            self.pcm.setchannels(self.channels)
            self.pcm.setrate(self._sample_rate)
            self.pcm.setformat(alsaaudio.PCM_FORMAT_S16_LE)  # 16-bit signed little-endian
            self.pcm.setperiodsize(self.period_size)

            self._running = True

            print(f"ALSA Audio initialized:")
            print(f"  Device: {self.device_name}")
            print(f"  Sample rate: {self._sample_rate} Hz")
            print(f"  Channels: {self.channels}")
            print(f"  Format: 16-bit signed LE")
            print(f"  Period size: {self.period_size}")

            return True

        except alsaaudio.ALSAAudioError as e:
            print(f"Failed to initialize ALSA audio: {e}")
            print("\nTroubleshooting:")
            print("  1. Check if ALSA is properly configured: aplay -l")
            print("  2. Test audio: speaker-test -t wav -c 2")
            print("  3. Adjust volume: alsamixer")
            return False
        except Exception as e:
            print(f"Unexpected error initializing ALSA audio: {e}")
            import traceback
            traceback.print_exc()
            return False

    def play_samples(self, samples: np.ndarray) -> None:
        """
        播放音频采样

        Args:
            samples: 音频采样数据，numpy 数组格式
                    通常是 float32 格式，范围 [-1.0, 1.0]
        """
        if not self._running or self.pcm is None:
            return

        if samples is None or len(samples) == 0:
            return

        try:
            # 快速转换：float32 -> int16（优化性能）
            # 使用 numpy 内置函数，避免中间变量
            samples_clipped = np.clip(samples, -1.0, 1.0)
            samples_int16 = (samples_clipped * 32767).astype(np.int16)

            # 如果是单声道且需要立体声，快速转换
            if samples_int16.ndim == 1 and self.channels == 2:
                # 使用 repeat 和 reshape 优化内存访问
                samples_int16 = np.repeat(samples_int16, 2)

            # 直接写入 ALSA（非阻塞模式，不会阻塞主循环）
            self.pcm.write(samples_int16.tobytes())

        except Exception as e:
            print(f"[ALSA] Error playing samples: {e}")
            import traceback
            traceback.print_exc()

    def close(self) -> None:
        """关闭 ALSA 音频设备"""
        self._running = False

        if self.pcm:
            try:
                self.pcm.close()
            except Exception:
                pass
            self.pcm = None

        print("ALSA Audio closed")
