"""Carga y cachea el modelo de clasificacion real/fake usado sobre frames de video.

En modo mock (VIDEO_ML_MOCK=1) nunca se importa torch/transformers, para poder
correr tests e integracion sin descargar pesos ni tener GPU disponible.
"""
from __future__ import annotations

import os
import threading
from typing import Callable, Optional

DEFAULT_MODEL_ID = os.environ.get(
    "VIDEO_ML_MODEL_ID", "dima806/deepfake_vs_real_image_detection"
)
DEVICE = os.environ.get("VIDEO_ML_DEVICE", "cpu")
MOCK_MODE = os.environ.get("VIDEO_ML_MOCK", "0") == "1"

FramePredictor = Callable[["object"], dict]

_lock = threading.Lock()
_predictor: Optional[FramePredictor] = None


class _MockPredictor:
    """Predictor determinista basado en el brillo medio del frame.

    No tiene valor de deteccion real: solo existe para que el resto del
    pipeline (extraccion de frames, agregacion, API, tests) sea verificable
    sin depender de descargar pesos ni de una GPU.
    """

    FAKE_LABEL = "Fake"

    def __call__(self, image) -> dict:
        import numpy as np

        arr = np.asarray(image.convert("L"))
        fake_score = float(min(max((128 - arr.mean()) / 128, 0.0), 1.0))
        return {"label": self.FAKE_LABEL, "score": fake_score}


def get_predictor(force_mock: Optional[bool] = None) -> FramePredictor:
    """Devuelve el predictor de frames (singleton, carga perezosa).

    Args:
        force_mock: si se pasa, ignora la variable de entorno VIDEO_ML_MOCK.
    """
    global _predictor
    use_mock = MOCK_MODE if force_mock is None else force_mock

    if use_mock:
        return _MockPredictor()

    with _lock:
        if _predictor is None:
            _predictor = _load_hf_predictor()
        return _predictor


def _load_hf_predictor() -> FramePredictor:
    from transformers import pipeline

    clf = pipeline("image-classification", model=DEFAULT_MODEL_ID, device=_resolve_device())

    def predictor(image) -> dict:
        results = clf(image)
        best = max(results, key=lambda r: r["score"])
        return {"label": best["label"], "score": float(best["score"])}

    return predictor


def _resolve_device() -> int:
    if DEVICE == "cpu":
        return -1
    try:
        return int(DEVICE)
    except ValueError:
        return -1
