"""Tests unitarios de app/services/video_analyzer.py y app/ml/*.

Corren siempre en modo mock (VIDEO_ML_MOCK=1, fijado en conftest.py) para no
requerir descargar pesos de HuggingFace ni GPU.
"""
from __future__ import annotations

import numpy as np
import pytest

from app.ml.inference import classify_frames
from app.ml.model_loader import get_predictor
from app.services.video_analyzer import (
    VideoAnalyzer,
    _blur_variance,
    _face_jitter_score,
    _flicker_score,
    detect_faces,
    extract_frames,
)


def test_get_predictor_mock_is_deterministic():
    from PIL import Image

    predictor = get_predictor(force_mock=True)
    image = Image.new("RGB", (32, 32), color=(10, 10, 10))

    result_a = predictor(image)
    result_b = predictor(image)

    assert result_a == result_b
    assert 0.0 <= result_a["score"] <= 1.0


def test_classify_frames_empty_returns_zero_scores():
    result = classify_frames([])
    assert result.mean_fake_score == 0.0
    assert result.max_fake_score == 0.0
    assert result.frame_predictions == []


def test_classify_frames_uses_injected_predictor():
    frames = [np.zeros((10, 10, 3), dtype=np.uint8) for _ in range(3)]
    calls = []

    def fake_predictor(image):
        calls.append(image)
        return {"label": "Fake", "score": 0.9}

    result = classify_frames(frames, predictor=fake_predictor)

    assert len(calls) == 3
    assert result.mean_fake_score == pytest.approx(0.9)


def test_classify_frames_normalizes_real_label_to_low_fake_score():
    frames = [np.zeros((10, 10, 3), dtype=np.uint8)]

    def real_predictor(image):
        return {"label": "Real", "score": 0.95}

    result = classify_frames(frames, predictor=real_predictor)

    assert result.mean_fake_score == pytest.approx(0.05)


def test_extract_frames_returns_requested_count(sample_video_path):
    frames, meta = extract_frames(sample_video_path, max_frames=5)

    assert 1 <= len(frames) <= 5
    assert meta["fps"] > 0
    assert meta["width"] > 0 and meta["height"] > 0


def test_extract_frames_invalid_path_raises():
    with pytest.raises(ValueError):
        extract_frames("ruta/que/no_existe.mp4")


def test_detect_faces_returns_list_on_blank_frame():
    frame = np.zeros((100, 100, 3), dtype=np.uint8)
    faces = detect_faces(frame)
    assert isinstance(faces, list)


def test_face_jitter_score_zero_when_no_faces():
    assert _face_jitter_score([[], [], []]) == 0.0


def test_face_jitter_score_high_when_face_jumps():
    faces_per_frame = [[(0, 0, 20, 20)], [(70, 70, 20, 20)], [(5, 5, 20, 20)]]
    score = _face_jitter_score(faces_per_frame)
    assert score > 0.0


def test_blur_variance_higher_for_sharp_edges():
    flat = np.full((50, 50, 3), 128, dtype=np.uint8)
    checker_pattern = (np.indices((50, 50)).sum(axis=0) % 2) * 255
    checker = np.stack([checker_pattern] * 3, axis=-1).astype(np.uint8)

    assert _blur_variance(checker) > _blur_variance(flat)


def test_flicker_score_zero_for_single_frame():
    frame = np.zeros((20, 20, 3), dtype=np.uint8)
    assert _flicker_score([frame]) == 0.0


@pytest.mark.asyncio
async def test_video_analyzer_end_to_end(sample_video_path):
    analyzer = VideoAnalyzer()
    result = await analyzer.analyze(sample_video_path)

    assert 0.0 <= result.confidence <= 1.0
    assert result.analysis_type == "video"
    assert result.video_details is not None
    assert result.metadata.format == "mp4"
    assert isinstance(result.video_details.artifacts, list)


@pytest.mark.asyncio
async def test_video_analyzer_no_frames_raises(tmp_path):
    empty_path = tmp_path / "empty.mp4"
    empty_path.write_bytes(b"")

    analyzer = VideoAnalyzer()
    with pytest.raises(ValueError):
        await analyzer.analyze(empty_path)
