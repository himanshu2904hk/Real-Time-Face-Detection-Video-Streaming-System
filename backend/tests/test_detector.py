"""Smoke tests for the FaceDetector wrapper.

We don't ship a face image with the repo, so this test only validates that:
  * a blank frame returns no detection
  * the API contract (numpy in / Detection|None out) is honored
  * malformed input raises
"""
from __future__ import annotations

import numpy as np
import pytest

# These tests need the heavy mediapipe runtime; skip cleanly if it's not installed.
pytest.importorskip("mediapipe")

from app.services.face_detector import FaceDetector  # noqa: E402


@pytest.fixture(scope="module")
def detector():
    d = FaceDetector(min_confidence=0.5)
    yield d
    d.close()


def test_blank_frame_no_detection(detector):
    frame = np.zeros((240, 320, 3), dtype=np.uint8)
    assert detector.detect(frame) is None


def test_white_frame_no_detection(detector):
    frame = np.full((240, 320, 3), 255, dtype=np.uint8)
    assert detector.detect(frame) is None


def test_wrong_shape_raises(detector):
    with pytest.raises(ValueError):
        detector.detect(np.zeros((10, 10), dtype=np.uint8))
    with pytest.raises(ValueError):
        detector.detect(np.zeros((10, 10, 4), dtype=np.uint8))
