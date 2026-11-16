"""Screen capture helper: takes a screenshot and returns it as base64 PNG text for the backend."""

import base64
import io

import mss
from PIL import Image

# Longest side (in pixels) of the image sent to the AI. Current models accept
# up to 2576 px, but image token cost grows with area; 1920 keeps a 1080p
# screen untouched while shrinking larger ones (1440p, 4K) to 1920x1080.
MAX_EDGE = 1920


def capture_screen(monitor: int = 1) -> str:
    """Capture a monitor and return it as a base64 PNG string, ready to send in a JSON request.

    Args:
        monitor: mss monitor index. 1 = main monitor, 2+ = others, 0 = all monitors combined.
    """
    # sct.monitors[monitor] only describes the monitor's position and size;
    # grab() takes the actual screenshot as raw BGRA pixels.
    with mss.mss() as sct:
        shot = sct.grab(sct.monitors[monitor])

    # Wrap the raw bytes in a Pillow image so it can be resized and encoded.
    # "BGRX" reads mss's BGRA bytes and drops the unused alpha byte.
    img = Image.frombytes("RGB", shot.size, shot.bgra, "raw", "BGRX")

    # Fit inside MAX_EDGE x MAX_EDGE: keeps the aspect ratio and never upscales.
    img.thumbnail((MAX_EDGE, MAX_EDGE))

    # Encode to PNG in memory, then to base64 text so it fits in the JSON request.
    # The backend passes it to the AI, which decodes it back to the image.
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return base64.standard_b64encode(buffer.getvalue()).decode("utf-8")
