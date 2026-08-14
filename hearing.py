"""Nia's ears — mic/system audio capture + whisper transcription.

Uses ffmpeg for audio capture and whisper-cli (whisper.cpp) for
speech-to-text. Supports mic input and BlackHole virtual audio
for capturing system audio.
"""
import os
import subprocess
import tempfile

HERE = os.path.dirname(__file__)
WHISPER_MODEL = os.path.join(HERE, "whisper-models", "ggml-base.en.bin")
WHISPER_BIN = "whisper-cli"

SAMPLE_RATE = 16000
CHANNELS = 1


def _find_audio_device(name_hint=None):
    result = subprocess.run(
        ["ffmpeg", "-f", "avfoundation", "-list_devices", "true", "-i", ""],
        capture_output=True, text=True, timeout=5
    )
    output = result.stderr
    devices = {}
    in_audio = False
    for line in output.splitlines():
        if "AVFoundation audio devices" in line:
            in_audio = True
            continue
        if in_audio:
            import re as _re
            m = _re.search(r"\[(\d+)\]\s*(.*)", line)
            if m:
                idx = m.group(1)
                dev_name = m.group(2).strip()
                devices[idx] = dev_name
                if name_hint and name_hint.lower() in dev_name.lower():
                    return idx, dev_name
    return devices


def find_blackhole():
    result = _find_audio_device("BlackHole")
    if isinstance(result, tuple):
        return result
    return None


def list_audio_devices():
    result = _find_audio_device()
    return result if isinstance(result, dict) else {}


def record(duration=5, device=":0", output_path=None):
    if output_path is None:
        fd, output_path = tempfile.mkstemp(suffix=".wav", prefix="nia_hear_")
        os.close(fd)

    cmd = [
        "ffmpeg", "-y",
        "-f", "avfoundation",
        "-i", device,
        "-t", str(duration),
        "-ar", str(SAMPLE_RATE),
        "-ac", str(CHANNELS),
        output_path
    ]
    subprocess.run(cmd, capture_output=True, timeout=duration + 10)
    return output_path


def transcribe(audio_path):
    if not os.path.exists(WHISPER_MODEL):
        return "(whisper model not found — run setup.sh)"

    cmd = [
        WHISPER_BIN,
        "-m", WHISPER_MODEL,
        "-f", audio_path,
        "--no-timestamps",
        "-t", "4",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

    text = ""
    for line in result.stdout.splitlines():
        line = line.strip()
        if line and line != "[BLANK_AUDIO]":
            text += line + " "
    return text.strip()


def listen(duration=5, device=":0"):
    wav = record(duration=duration, device=device)
    try:
        text = transcribe(wav)
        return text
    finally:
        try:
            os.unlink(wav)
        except OSError:
            pass


def listen_until_silence_vad(sample_rate=16000, chunk_duration_ms=30,
                              silence_timeout=0.8, max_duration=60.0):
    import webrtcvad
    import pyaudio
    import wave as _wave
    vad = webrtcvad.Vad(2)
    audio = pyaudio.PyAudio()
    chunk_size = int(sample_rate * chunk_duration_ms / 1000)
    stream = audio.open(format=pyaudio.paInt16, channels=1, rate=sample_rate,
                        input=True, frames_per_buffer=chunk_size)
    print("  [hearing] listening... (speak now)")
    frames = []
    silence_frames = 0
    silence_threshold = int(silence_timeout / (chunk_duration_ms / 1000))
    max_frames = int(max_duration / (chunk_duration_ms / 1000))
    while True:
        chunk = stream.read(chunk_size)
        if vad.is_speech(chunk, sample_rate):
            frames.append(chunk)
            break
    while True:
        chunk = stream.read(chunk_size)
        frames.append(chunk)
        if vad.is_speech(chunk, sample_rate):
            silence_frames = 0
        else:
            silence_frames += 1
        if silence_frames >= silence_threshold or len(frames) >= max_frames:
            break
    stream.stop_stream()
    stream.close()
    audio.terminate()
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        wf = _wave.open(f, 'wb')
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(b''.join(frames))
        wf.close()
        return f.name
