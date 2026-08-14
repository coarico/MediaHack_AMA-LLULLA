"""Inferencia ML sobre frames de video: clasificacion real/fake por frame y agregacion."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional, Sequence

import numpy as np
from PIL import Image

from app.ml.model_loader import get_predictor

FAKE_LABELS = {"fake", "deepfake", "ai", "synthetic", "ai-generated"}


@dataclass
class FramePrediction:
    frame_index: int
    fake_score: float


@dataclass
class InferenceResult:
    frame_predictions: list[FramePrediction]
    mean_fake_score: float
    max_fake_score: float


def _to_pil(frame: np.ndarray) -> Image.Image:
    """Convierte un frame BGR (OpenCV) a PIL RGB."""
    rgb = frame[:, :, ::-1]
    return Image.fromarray(rgb)


def _normalize_fake_score(label: str, score: float) -> float:
    """Normaliza la salida del clasificador a 'probabilidad de fake'.

    El pipeline de HF puede devolver como top-label tanto 'Real' como 'Fake'
    segun cual tenga mayor score; si el top-label es 'Real' invertimos el
    score para que siempre represente la probabilidad de contenido fake.
    """
    if label.strip().lower() in FAKE_LABELS:
        return score
    return 1.0 - score


def classify_frames(
    frames: Sequence[np.ndarray],
    predictor: Optional[Callable] = None,
) -> InferenceResult:
    predict = predictor or get_predictor()
    predictions: list[FramePrediction] = []

    for idx, frame in enumerate(frames):
        image = _to_pil(frame)
        raw = predict(image)
        fake_score = _normalize_fake_score(raw["label"], raw["score"])
        predictions.append(FramePrediction(frame_index=idx, fake_score=fake_score))

    if not predictions:
        return InferenceResult(frame_predictions=[], mean_fake_score=0.0, max_fake_score=0.0)

    scores = [p.fake_score for p in predictions]
    return InferenceResult(
        frame_predictions=predictions,
        mean_fake_score=sum(scores) / len(scores),
        max_fake_score=max(scores),
    )
