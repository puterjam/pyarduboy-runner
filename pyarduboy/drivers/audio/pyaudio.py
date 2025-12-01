"""
PyAudio 音频驱动

使用 PyAudio 库播放音频
适合桌面环境（macOS、Windows、Linux）
基于 PortAudio，跨平台低延迟音频库
"""
import numpy as np
from .base import AudioDriver

try:
    import pyaudio
    PYAUDIO_AVAILABLE = True
except ImportError:
    PYAUDIO_AVAILABLE = False


class PyAudioDriver(AudioDriver):
    """
    PyAudio 音频驱动

    使用 PyAudio (PortAudio) 播放音频流
    提供低延迟的跨平台音频输出

    Args:
        sample_rate: 采样率，默认 48000 Hz (Arduboy 标准)
        channels: 声道数，默认 2 (立体声)
        frames_per_buffer: 每次回调的帧数，默认 1024
        volume: 音量，0.0-1.0，默认 0.3
    """

    def __init__(
        self,
        sample_rate: int = 48000,
        channels: int = 2,
        frames_per_buffer: int = 1024,
        volume: float = 0.3
    ):
        super().__init__()

        if not PYAUDIO_AVAILABLE:
            raise ImportError("PyAudio is not installed. Please run: pip install pyaudio")

        # 使用 _sample_rate（基类属性）而不是 self.sample_rate
        self._sample_rate = sample_rate
        self.channels = channels
        self.frames_per_buffer = frames_per_buffer
        self.volume = max(0.0, min(1.0, volume))

        self._pyaudio = None
        self._stream = None
        self._initialized = False

    def init(self, sample_rate: int = 48000) -> bool:
        """
        初始化音频驱动

        Args:
            sample_rate: 采样率，默认 48000 Hz

        Returns:
            初始化成功返回 True
        """
        if self._initialized:
            return True

        # 更新采样率
        self._sample_rate = sample_rate

        try:
            # 创建 PyAudio 实例
            self._pyaudio = pyaudio.PyAudio()

            # 打开音频流（使用回调模式实现真正的非阻塞）
            # 创建音频缓冲队列
            import queue
            self._audio_queue = queue.Queue(maxsize=2)  # 最多缓存2帧，避免延迟过大

            def audio_callback(_in_data, frame_count, _time_info, _status):
                """音频回调函数，由 PortAudio 线程调用"""
                try:
                    # 从队列获取数据（非阻塞）
                    data = self._audio_queue.get_nowait()
                    return (data, pyaudio.paContinue)
                except:
                    # 队列为空，返回静音
                    return (bytes(frame_count * self.channels * 2), pyaudio.paContinue)

            self._stream = self._pyaudio.open(
                format=pyaudio.paInt16,  # 16-bit signed integer
                channels=self.channels,
                rate=self._sample_rate,
                output=True,
                frames_per_buffer=self.frames_per_buffer,
                stream_callback=audio_callback  # 使用回调模式（真正非阻塞）
            )

            self._stream.start_stream()
            self._initialized = True

            print(f"PyAudio initialized: {self._sample_rate}Hz, {self.channels} channels")
            return True

        except Exception as e:
            print(f"Failed to initialize PyAudio: {e}")
            if self._stream:
                self._stream.close()
            if self._pyaudio:
                self._pyaudio.terminate()
            return False

    def play_samples(self, samples: np.ndarray) -> None:
        """
        播放音频采样

        Args:
            samples: 音频采样数据，numpy 数组格式
                    通常是 float32 格式，范围 [-1.0, 1.0]
        """
        if not self._initialized or not self._stream:
            return

        if samples is None or len(samples) == 0:
            return

        try:
            # 参考 ALSA 驱动的实现：快速转换 float32 -> int16
            # 1. Clip 到 [-1.0, 1.0] 范围（防止爆音）
            samples_clipped = np.clip(samples, -1.0, 1.0)

            # 2. 应用音量
            samples_scaled = samples_clipped * self.volume

            # 3. 转换为 int16
            samples_int16 = (samples_scaled * 32767).astype(np.int16)

            # 4. 如果是单声道且需要立体声，快速转换
            if samples_int16.ndim == 1 and self.channels == 2:
                # 使用 repeat 优化内存访问
                samples_int16 = np.repeat(samples_int16, 2)

            # 5. 将数据放入队列（非阻塞模式）
            audio_data = samples_int16.tobytes()
            try:
                # 尝试将数据放入队列（不阻塞）
                self._audio_queue.put_nowait(audio_data)
            except:
                # 队列满，丢弃这一帧音频数据，避免阻塞
                pass

        except Exception as e:
            # 只在第一次错误时打印
            if not hasattr(self, '_error_printed'):
                print(f"Error playing audio: {e}")
                import traceback
                traceback.print_exc()
                self._error_printed = True

    def close(self) -> None:
        """关闭音频驱动"""
        self._initialized = False

        if self._stream:
            try:
                self._stream.stop_stream()
                self._stream.close()
            except:
                pass
            self._stream = None

        if self._pyaudio:
            try:
                self._pyaudio.terminate()
            except:
                pass
            self._pyaudio = None

    def set_volume(self, volume: float) -> None:
        """
        设置音量

        Args:
            volume: 音量，0.0-1.0
        """
        self.volume = max(0.0, min(1.0, volume))


class PyAudioDriverLowLatency(PyAudioDriver):
    """
    低延迟 PyAudio 音频驱动

    使用更小的缓冲区以降低延迟
    """

    def __init__(self, **kwargs):
        kwargs['frames_per_buffer'] = kwargs.get('frames_per_buffer', 512)
        super().__init__(**kwargs)


class PyAudioDriverHighQuality(PyAudioDriver):
    """
    高质量 PyAudio 音频驱动

    使用更大的缓冲区以提高音质和稳定性
    """

    def __init__(self, **kwargs):
        kwargs['frames_per_buffer'] = kwargs.get('frames_per_buffer', 2048)
        super().__init__(**kwargs)
