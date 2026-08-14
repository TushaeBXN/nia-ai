"""Webcam capture for Nia (macOS / AVFoundation via ffmpeg).

Grabs a single still from the FaceTime HD Camera. The frame is saved locally
and only ever handed to the LOCAL Ollama model — nothing leaves the machine.
"""
import subprocess
import os

DEVICE = os.environ.get("NIA_CAM", "0")
FRAME_PATH = os.environ.get("NIA_FRAME", "/tmp/nia_frame.jpg")


def capture(path=FRAME_PATH, device=DEVICE, warmup=8):
    """Capture one webcam frame. Returns the path, or None on failure."""
    cmd = [
        "ffmpeg", "-hide_banner", "-loglevel", "error",
        "-f", "avfoundation", "-framerate", "30", "-video_size", "1280x720",
        "-pixel_format", "nv12", "-i", device,
        "-frames:v", str(warmup), "-update", "1", "-y", path,
    ]
    try:
        subprocess.run(cmd, check=True, timeout=20)
    except subprocess.CalledProcessError as e:
        print(f"  [vision] capture failed (camera permission?): {e}")
        return None
    except FileNotFoundError:
        print("  [vision] ffmpeg not found")
        return None
    except subprocess.TimeoutExpired:
        print("  [vision] capture timed out")
        return None
    return path if os.path.exists(path) else None
