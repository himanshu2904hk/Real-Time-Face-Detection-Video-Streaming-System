"""Frame processing pipeline: decode -> detect -> draw -> encode.

All image work is done with Pillow + NumPy. **No OpenCV anywhere.**
"""
from __future__ import annotations

import io
from dataclasses import dataclass
from typing import Optional, Tuple

import numpy as np
from PIL import Image, ImageDraw, ImageFont, UnidentifiedImageError

from app.services.face_detector import Detection, FaceDetector


# Box style — kept consistent with what the frontend expects.
_BOX_COLOR = (0, 255, 0)        # green
_BOX_WIDTH = 3                  # px
_LABEL_FILL = (0, 0, 0, 160)    # semi-transparent black
_LABEL_TEXT = (255, 255, 255)   # white


@dataclass(frozen=True)
class ProcessedFrame:
    """Result of processing a single frame."""

    jpeg_bytes: bytes
    detection: Optional[Detection]
    width: int
    height: int


def _decode_jpeg(data: bytes) -> Image.Image:
    """Decode JPEG bytes into a PIL RGB image. Raises ValueError on bad input."""
    try:
        img = Image.open(io.BytesIO(data))
        img.load()  # force decode now so we surface errors early
    except (UnidentifiedImageError, OSError) as exc:
        raise ValueError("frame is not a valid image") from exc

    if img.mode != "RGB":
        img = img.convert("RGB")
    return img


def _encode_jpeg(img: Image.Image, quality: int = 80) -> bytes:
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=quality)
    return buf.getvalue()


def draw_roi(img: Image.Image, det: Detection) -> Image.Image:
    """Draw an axis-aligned minimal bounding box around the detected face.

    Pillow only — explicitly avoids OpenCV. Returns a new image; original is
    not mutated.
    """
    out = img.copy()
    draw = ImageDraw.Draw(out, mode="RGBA")

    x1, y1 = det.x, det.y
    x2, y2 = det.x + det.width, det.y + det.height

    # Pillow's `width=` arg draws on outside; we use it for crisp lines.
    draw.rectangle([(x1, y1), (x2, y2)], outline=_BOX_COLOR, width=_BOX_WIDTH)

    # Confidence label above the box (or inside if it would clip the top).
    label = f"face {det.confidence:.0%}"
    try:
        font = ImageFont.load_default()
    except Exception:  # pragma: no cover — font load should not fail
        font = None

    text_bbox = draw.textbbox((0, 0), label, font=font)
    tw = text_bbox[2] - text_bbox[0]
    th = text_bbox[3] - text_bbox[1]

    pad = 2
    label_y = y1 - th - 2 * pad
    if label_y < 0:
        label_y = y1 + pad
    label_x = x1

    draw.rectangle(
        [(label_x, label_y), (label_x + tw + 2 * pad, label_y + th + 2 * pad)],
        fill=_LABEL_FILL,
    )
    draw.text((label_x + pad, label_y + pad), label, fill=_LABEL_TEXT, font=font)

    return out


def process_frame(
    jpeg_bytes: bytes,
    detector: FaceDetector,
) -> ProcessedFrame:
    """Decode a JPEG frame, detect a face, draw the ROI, re-encode.

    Returns the encoded bytes plus detection metadata so callers can persist
    or forward the ROI without decoding again.
    """
    img = _decode_jpeg(jpeg_bytes)
    arr = np.asarray(img)  # HxWx3 RGB

    detection = detector.detect(arr)
    if detection is not None:
        img = draw_roi(img, detection)

    out = _encode_jpeg(img)
    return ProcessedFrame(
        jpeg_bytes=out,
        detection=detection,
        width=img.width,
        height=img.height,
    )


def image_size(jpeg_bytes: bytes) -> Tuple[int, int]:
    """Return (width, height) of a JPEG without fully decoding pixel data."""
    with Image.open(io.BytesIO(jpeg_bytes)) as img:
        return img.size
