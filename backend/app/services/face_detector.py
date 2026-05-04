"""Face detection service.

We use Google's MediaPipe Face Detection (BlazeFace short-range model). It is:
  - Free / open source (Apache-2.0)
  - Fast enough for real-time webcam (>30 fps on a laptop)
  - Pure-Python wheels for major platforms
  - NOT dependent on OpenCV at the API level (we feed raw RGB pixels via numpy)

The detector returns an axis-aligned minimal bounding box (the ROI). The problem
states only one face will be present, so we keep the highest-confidence detection.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np


@dataclass(frozen=True)
class Detection:
    """Pixel-space ROI for the detected face."""

    x: int
    y: int
    width: int
    height: int
    confidence: float

    def as_dict(self) -> dict:
        return {
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "confidence": self.confidence,
        }


class FaceDetector:
    """Thin wrapper around MediaPipe FaceDetection.

    Not thread-safe; create one per worker / WebSocket connection.
    """

    def __init__(self, min_confidence: float = 0.5) -> None:
        # Imported lazily so the rest of the app (and unit tests for the
        # frame processor / DB / API) doesn't require mediapipe installed.
        import mediapipe as mp

        # model_selection=0 -> short-range (within ~2m), best for webcam.
        self._detector = mp.solutions.face_detection.FaceDetection(
            model_selection=0,
            min_detection_confidence=min_confidence,
        )

    def detect(self, rgb_image: np.ndarray) -> Optional[Detection]:
        """Detect a single face in an RGB image and return its bounding box.

        Args:
            rgb_image: HxWx3 uint8 ndarray in RGB order.

        Returns:
            A Detection clamped to image bounds, or None if no face found.
        """
        if rgb_image.ndim != 3 or rgb_image.shape[2] != 3:
            raise ValueError("expected HxWx3 RGB image")

        h, w = rgb_image.shape[:2]
        result = self._detector.process(rgb_image)

        if not result.detections:
            return None

        # Pick the highest-score detection (problem assumes one face).
        best = max(result.detections, key=lambda d: d.score[0] if d.score else 0.0)
        bbox = best.location_data.relative_bounding_box

        # MediaPipe returns relative [0,1] coordinates that can spill outside the
        # frame. Clamp to image bounds to produce a valid ROI.
        x = max(0, int(round(bbox.xmin * w)))
        y = max(0, int(round(bbox.ymin * h)))
        x2 = min(w, int(round((bbox.xmin + bbox.width) * w)))
        y2 = min(h, int(round((bbox.ymin + bbox.height) * h)))

        if x2 <= x or y2 <= y:
            return None  # Degenerate box after clamping.

        return Detection(
            x=x,
            y=y,
            width=x2 - x,
            height=y2 - y,
            confidence=float(best.score[0]) if best.score else 0.0,
        )

    def close(self) -> None:
        self._detector.close()

    def __enter__(self) -> "FaceDetector":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()
