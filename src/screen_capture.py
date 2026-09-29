"""Screen capture helpers that produce image blocks for the Claude API."""

import base64
import io

import mss
from PIL import Image

# Longest side (in pixels) of the image sent to Claude. Current models accept
# up to 2576 px, but image token cost grows with area; 1920 keeps a 1080p
# screen untouched while shrinking larger ones (1440p, 4K) to 1920x1080.
MAX_EDGE = 1920


def capture_screen(monitor: int = 1) -> dict:
    """Capture a monitor and return it as a base64 PNG image block for the Claude API.

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
    # The API decodes it back to the original image on its side.
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    data = base64.standard_b64encode(buffer.getvalue()).decode("utf-8")

    # Image content block in the format the Messages API expects.
    return {
        "type": "image",
        "source": {"type": "base64", "media_type": "image/png", "data": data},
    }
