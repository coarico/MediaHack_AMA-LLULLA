"""Fixtures compartidas para tests del modulo de video."""
from __future__ import annotations

import os

os.environ.setdefault("VIDEO_ML_MOCK", "1")

import cv2
import numpy as np
import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture()
def client():
    # Usar como context manager dispara los eventos de startup/shutdown
    # (crea temp/ y uploads/), igual que en un servidor real.
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
def sample_video_path(tmp_path) -> str:
    """Genera un video sintetico pequeno para no depender de assets externos."""
    path = tmp_path / "sample.mp4"
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(path), fourcc, 10.0, (160, 120))

    rng = np.random.default_rng(42)
    for _ in range(20):
        frame = rng.integers(0, 255, (120, 160, 3), dtype=np.uint8)
        cv2.rectangle(frame, (50, 30), (110, 90), (200, 180, 160), -1)
        writer.write(frame)
    writer.release()

    return str(path)
