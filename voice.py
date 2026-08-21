"""Text-to-speech for Nia — Piper (offline, free) + macOS afplay.

speak()          — original single-shot synthesis (short replies, fallback)
speak_streamed() — sentence-pipelined: synthesizes next sentence while current
                   one plays. Significantly reduces perceived latency on long replies.
"""
import os
import queue
import re
import sys
import shutil
import tempfile
import subprocess
import threading
import time

_PRONUNCIATION = []


def _phonetic(text):
    for pat, repl in _PRONUNCIATION:
        text = pat.sub(repl, text)
    return text


_DEFAULT_VOICE = os.path.join(
    os.path.dirname(__file__), "voices", "en_US-lessac-high.onnx"
)
VOICE = os.environ.get("NIA_VOICE", _DEFAULT_VOICE)
LENGTH_SCALE = os.environ.get("NIA_SPEED", "0.9")


def _player():
    if shutil.which("afplay"):
        return ["afplay"]
    if shutil.which("ffplay"):
        return ["ffplay", "-autoexit", "-nodisp", "-loglevel", "quiet"]
    return None


def _synthesize_wav(text):
    """Synthesize one piece of text → temp WAV path, or None on failure."""
    if not text or not re.sub(r'[^\w]', '', text):
        return None
    if not os.path.exists(VOICE):
        return None
    try:
        wav = tempfile.NamedTemporaryFile(suffix=".wav", delete=False).name
        subprocess.run(
            [sys.executable, "-m", "piper", "-m", VOICE,
             "--length-scale", LENGTH_SCALE, "-f", wav],
            input=_phonetic(text).encode(), check=True,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        return wav
    except Exception as e:
        print(f"  [voice] synthesis failed: {e}")
        return None


def _play_wav(wav):
    """Play a WAV file and delete it."""
    player = _player()
    if player and wav and os.path.exists(wav):
        r = subprocess.run(player + [wav], check=False,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if r.returncode != 0:
            time.sleep(0.3)
            subprocess.run(player + [wav], check=False,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if wav and os.path.exists(wav):
        os.remove(wav)


def speak(text, emotion="neutral"):
    """Single-shot synthesis — used for short replies and as a fallback."""
    if not text:
        return
    print(f"\nNia ({emotion}): {text}")
    try:
        wav = _synthesize_wav(text)
        _play_wav(wav)
    except Exception as e:
        print(f"  [voice] tts failed: {e}")


_SENTENCE_RE = re.compile(r'(?<=[.!?])\s+')


def speak_streamed(text, emotion="neutral"):
    """Pipelined TTS: synthesize next sentence while current one plays.

    Starts speaking sooner and eliminates gaps between sentences.
    Falls back to speak() for single-sentence text.
    """
    if not text:
        return
    print(f"\nNia ({emotion}): {text}")
    if not os.path.exists(VOICE):
        return

    sentences = [s.strip() for s in _SENTENCE_RE.split(text) if s.strip()]
    sentences = [s for s in sentences if re.sub(r'[^\w]', '', s)]

    if len(sentences) <= 1:
        try:
            _play_wav(_synthesize_wav(text))
        except Exception as e:
            print(f"  [voice] tts failed: {e}")
        return

    wav_queue = queue.Queue(maxsize=2)

    def _synth_worker():
        for sentence in sentences:
            wav_queue.put(_synthesize_wav(sentence))
        wav_queue.put(None)

    synth_thread = threading.Thread(target=_synth_worker, daemon=True)
    synth_thread.start()

    while True:
        wav = wav_queue.get()
        if wav is None:
            break
        try:
            _play_wav(wav)
        except Exception as e:
            print(f"  [voice] playback failed: {e}")

    synth_thread.join(timeout=5)
