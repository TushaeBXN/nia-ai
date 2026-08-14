"""Text-to-speech for Nia — Piper (offline, free) + macOS afplay."""
import os
import re
import sys
import shutil
import tempfile
import subprocess
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


def speak(text, emotion="neutral"):
    if not text:
        return
    print(f"\nNia ({emotion}): {text}")
    if not os.path.exists(VOICE):
        return
    if not re.sub(r'[^\w]', '', text):
        return

    wav = None
    try:
        wav = tempfile.NamedTemporaryFile(suffix=".wav", delete=False).name
        subprocess.run(
            [sys.executable, "-m", "piper", "-m", VOICE,
             "--length-scale", LENGTH_SCALE, "-f", wav],
            input=_phonetic(text).encode(), check=True,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        player = _player()
        if player:
            r = subprocess.run(player + [wav], check=False,
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if r.returncode != 0:
                time.sleep(0.3)
                subprocess.run(player + [wav], check=False,
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:
        print(f"  [voice] tts failed: {e}")
    finally:
        if wav and os.path.exists(wav):
            os.remove(wav)
