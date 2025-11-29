# Arduboy 音频设置指南

## 安装 ALSA 音频库

在树莓派上运行以下命令安装音频库：

```bash
# 安装 ALSA 开发库
sudo apt-get update
sudo apt-get install libasound2-dev python3-alsaaudio

# 或者使用 pip 安装
pip3 install pyalsaaudio
```

## 测试音频系统

### 1. 检查音频设备

```bash
# 列出所有音频设备
aplay -l

# 列出所有 PCM 设备
aplay -L
```

### 2. 测试音频输出

```bash
# 播放测试音（左右声道）
speaker-test -t wav -c 2

# 播放测试音（持续 5 秒）
speaker-test -t wav -c 2 -l 1
```

### 3. 调整音量

```bash
# 打开音量控制界面
alsamixer

# 或者使用命令行设置音量（0-100%）
amixer set Master 80%
```

## 配置 Arduboy 音频

### 默认配置

`run_arduboy.py` 已经配置为使用 ALSA 音频驱动：

```python
from pyarduboy.drivers.audio.alsa import AlsaAudioDriver

# 使用默认设置
audio_driver = AlsaAudioDriver()
arduboy.set_audio_driver(audio_driver)
```

### 自定义配置

如果需要自定义音频参数：

```python
# 自定义 ALSA 设备和参数
audio_driver = AlsaAudioDriver(
    device='default',      # ALSA 设备名称
    sample_rate=44100,     # 采样率（Hz）
    channels=2,            # 声道数（1=单声道，2=立体声）
    period_size=1024       # 缓冲区大小
)
```

### 指定特定设备

如果有多个音频设备，可以指定使用哪个：

```python
# 使用 HDMI 音频输出
audio_driver = AlsaAudioDriver(device='hdmi')

# 使用耳机插孔
audio_driver = AlsaAudioDriver(device='headphones')

# 使用默认设备
audio_driver = AlsaAudioDriver(device='default')
```

## 常见问题

### 1. 没有声音

**检查音量：**
```bash
alsamixer
# 确保 Master 音量不是静音（MM），按 M 键取消静音
```

**检查默认设备：**
```bash
# 查看当前音频设备
aplay -l

# 设置默认设备（编辑 /etc/asound.conf 或 ~/.asoundrc）
cat > ~/.asoundrc << EOF
pcm.!default {
    type hw
    card 0
    device 0
}
EOF
```

### 2. 音频卡顿或爆音

**增加缓冲区大小：**
```python
audio_driver = AlsaAudioDriver(period_size=2048)  # 默认 1024
```

**降低采样率：**
```python
audio_driver = AlsaAudioDriver(sample_rate=22050)  # 默认 44100
```

### 3. 权限错误

确保用户在 `audio` 组中：
```bash
sudo usermod -a -G audio $USER
# 重新登录后生效
```

### 4. ALSA 库未安装

如果看到 "alsaaudio library not found" 错误：
```bash
sudo apt-get install python3-alsaaudio
# 或
pip3 install pyalsaaudio
```

## 树莓派音频输出选择

### 切换到 HDMI 音频

```bash
# 强制使用 HDMI 音频
sudo raspi-config
# 选择 System Options → Audio → HDMI
```

### 切换到耳机插孔

```bash
# 强制使用 3.5mm 耳机插孔
sudo raspi-config
# 选择 System Options → Audio → Headphones
```

### 自动选择

```bash
# 自动检测（优先 HDMI）
sudo raspi-config
# 选择 System Options → Audio → Auto
```

## 禁用音频

如果不需要音频，可以使用空驱动：

```python
from pyarduboy.drivers.audio.null import NullAudioDriver

arduboy.set_audio_driver(NullAudioDriver())
```

或者在 `run_arduboy.py` 中注释掉 ALSA 驱动部分。

## 性能优化

如果音频影响游戏性能：

1. **增加缓冲区大小**：减少 CPU 占用，但会增加延迟
   ```python
   AlsaAudioDriver(period_size=4096)
   ```

2. **降低采样率**：减少数据处理量
   ```python
   AlsaAudioDriver(sample_rate=22050)
   ```

3. **使用单声道**：减少一半数据量
   ```python
   AlsaAudioDriver(channels=1)
   ```

## 调试技巧

### 查看详细的 ALSA 信息

```bash
# 显示详细的设备信息
cat /proc/asound/cards

# 显示 PCM 设备信息
cat /proc/asound/pcm
```

### 录制音频进行测试

```bash
# 录制 5 秒音频并播放
arecord -d 5 -f cd test.wav
aplay test.wav
```

### 监控音频状态

```bash
# 实时查看音频状态
watch -n 1 cat /proc/asound/card0/pcm0p/sub0/status
```
