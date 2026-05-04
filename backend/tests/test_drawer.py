"""Tests for the ROI drawing logic.

We don't use OpenCV here either — verification is done by inspecting raw
pixel values with NumPy + Pillow.
"""
from __future__ import annotations

import io

import numpy as np
import pytest
from PIL import Image

from app.services.face_detector import Detection
from app.services.frame_processor import (
    _decode_jpeg,
    _encode_jpeg,
    draw_roi,
    process_frame,
)


def _solid_image(w=200, h=150, color=(20, 20, 20)) -> Image.Image:
    return Image.new("RGB", (w, h), color)


def test_decode_rejects_non_image():
    with pytest.raises(ValueError):
        _decode_jpeg(b"this is not an image")


def test_decode_converts_to_rgb():
    # PNG with alpha — must come back as RGB.
    img = Image.new("RGBA", (32, 32), (10, 10, 10, 128))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    out = _decode_jpeg(buf.getvalue())
    assert out.mode == "RGB"


def test_draw_roi_does_not_mutate_input():
    img = _solid_image()
    det = Detection(x=20, y=30, width=60, height=40, confidence=0.9)
    out = draw_roi(img, det)
    # Original untouched — interior pixel still the background colour.
    assert np.array(img)[35, 25].tolist() == [20, 20, 20]
    assert out is not img


def test_draw_roi_paints_rectangle_outline():
    img = _solid_image(color=(0, 0, 0))
    det = Detection(x=20, y=30, width=60, height=40, confidence=0.95)
    out = np.array(draw_roi(img, det))

    # Top edge of the ROI should contain green pixels (the box colour).
    top_edge = out[det.y, det.x : det.x + det.width]
    assert (top_edge[:, 1] > 200).any(), "expected green outline along the top edge"

    # The center pixel inside the ROI should remain background (box is outline-only).
    cx, cy = det.x + det.width // 2, det.y + det.height // 2
    assert out[cy, cx, 1] == 0


def test_draw_roi_clips_to_image():
    img = _solid_image(w=100, h=100)
    # Box that runs off the image — should still draw without crashing.
    det = Detection(x=80, y=80, width=80, height=80, confidence=0.5)
    out = draw_roi(img, det)
    assert out.size == (100, 100)


def test_encode_roundtrip():
    img = _solid_image()
    data = _encode_jpeg(img, quality=85)
    assert data[:2] == b"\xff\xd8"  # JPEG SOI marker.
    decoded = _decode_jpeg(data)
    assert decoded.size == img.size


class _StubDetector:
    def __init__(self, det):
        self.det = det

    def detect(self, _):
        return self.det


def test_process_frame_with_detection():
    img = _solid_image()
    jpeg = _encode_jpeg(img)
    det = Detection(x=10, y=20, width=30, height=40, confidence=0.8)
    result = process_frame(jpeg, _StubDetector(det))
    assert result.detection == det
    assert result.jpeg_bytes[:2] == b"\xff\xd8"


def test_process_frame_without_detection():
    img = _solid_image()
    jpeg = _encode_jpeg(img)
    result = process_frame(jpeg, _StubDetector(None))
    assert result.detection is None
    # Still returns a re-encoded image.
    assert result.jpeg_bytes[:2] == b"\xff\xd8"


def test_process_frame_rejects_garbage():
    with pytest.raises(ValueError):
        process_frame(b"\x00\x01\x02not-an-image", _StubDetector(None))
