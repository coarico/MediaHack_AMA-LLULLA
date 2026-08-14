"""Analisis de video: extraccion de frames, heuristicas OpenCV e inferencia ML combinada.

El score final combina dos senales independientes:
  - ml_score: probabilidad media de 'fake' segun el modelo de clasificacion (app.ml).
  - heuristic_score: senales clasicas de vision por computador (jitter facial,
    perdida de nitidez/artefactos de compresion, parpadeo/flicker de iluminacion).

Combinar ambas hace el resultado mas robusto que depender solo del modelo de ML.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

import cv2
import numpy as np

from app.ml.inference import classify_frames

# YuNet (DNN, OpenCV Zoo) reemplaza a los Haar Cascades clasicos: mas preciso
# y sigue disponible en OpenCV 5.x, donde cv2.CascadeClassifier fue removido.
FACE_DETECTOR_MODEL_PATH = os.environ.get(
    "VIDEO_FACE_DETECTOR_PATH",
    str(Path(__file__).resolve().parents[2] / "models" / "face_detection_yunet_2023mar.onnx"),
)
FACE_SCORE_THRESHOLD = 0.7
_face_detector: Optional[cv2.FaceDetectorYN] = None

ML_WEIGHT = 0.65
HEURISTIC_WEIGHT = 0.35

JITTER_THRESHOLD = 0.18
BLUR_VARIANCE_THRESHOLD = 60.0
FLICKER_THRESHOLD = 35.0
AI_GENERATED_THRESHOLD = 0.55


@dataclass
class VideoAnalysisResult:
    is_ai_generated: bool
    confidence: float
    video_score: float
    ml_score: float
    heuristic_score: float
    artifacts_detected: list[str]
    frames_analyzed: int
    duration_seconds: float
    fps: float
    format: str


def _get_face_detector() -> cv2.FaceDetectorYN:
    global _face_detector
    if _face_detector is None:
        _face_detector = cv2.FaceDetectorYN_create(FACE_DETECTOR_MODEL_PATH, "", (320, 320))
    return _face_detector


def extract_frames(video_path: str, max_frames: int = 16) -> tuple[list[np.ndarray], dict]:
    """Extrae hasta `max_frames` frames distribuidos uniformemente en el video."""
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"No se pudo abrir el video: {video_path}")

    try:
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS) or 0.0
        duration = total_frames / fps if fps else 0.0

        sampled: list[np.ndarray] = []
        if total_frames <= 0:
            ok, frame = cap.read()
            while ok and len(sampled) < max_frames:
                sampled.append(frame)
                ok, frame = cap.read()
        else:
            step = max(total_frames // max_frames, 1)
            indices = list(range(0, total_frames, step))[:max_frames]
            for idx in indices:
                cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
                ok, frame = cap.read()
                if ok:
                    sampled.append(frame)

        metadata = {"total_frames": total_frames, "fps": fps, "duration": duration}
        return sampled, metadata
    finally:
        cap.release()


def detect_faces(frame: np.ndarray) -> list[tuple[int, int, int, int]]:
    """Devuelve los bounding boxes (x, y, w, h) de las caras detectadas en el frame."""
    detector = _get_face_detector()
    height, width = frame.shape[:2]
    detector.setInputSize((width, height))

    _, detections = detector.detect(frame)
    if detections is None:
        return []

    faces = []
    for det in detections:
        score = float(det[14])
        if score < FACE_SCORE_THRESHOLD:
            continue
        x, y, w, h = det[:4]
        faces.append((int(x), int(y), int(w), int(h)))
    return faces


def _face_jitter_score(faces_per_frame: list[list[tuple[int, int, int, int]]]) -> float:
    """Mide que tan inconsistente es la posicion/tamano de la cara principal entre
    frames. Un deepfake mal compuesto suele mostrar saltos bruscos del bounding box."""
    centers = []
    sizes = []
    for faces in faces_per_frame:
        if not faces:
            continue
        x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
        centers.append((x + w / 2, y + h / 2))
        sizes.append(w * h)

    if len(centers) < 2:
        return 0.0

    center_arr = np.array(centers)
    deltas = np.linalg.norm(np.diff(center_arr, axis=0), axis=1)
    size_arr = np.array(sizes, dtype=float)
    size_deltas = np.abs(np.diff(size_arr)) / np.maximum(size_arr[:-1], 1.0)

    norm_position_jitter = np.mean(deltas) / max(np.mean(size_arr) ** 0.5, 1.0)
    norm_size_jitter = np.mean(size_deltas)
    return float(min((norm_position_jitter + norm_size_jitter) / 2, 1.0))


def _blur_variance(frame: np.ndarray) -> float:
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    return float(cv2.Laplacian(gray, cv2.CV_64F).var())


def _flicker_score(frames: list[np.ndarray]) -> float:
    """Mide cambios abruptos de histograma de color entre frames consecutivos:
    parpadeo/inconsistencia de iluminacion tipica de frames sintetizados."""
    if len(frames) < 2:
        return 0.0
    diffs = []
    prev_hist = None
    for frame in frames:
        hist = cv2.calcHist([frame], [0, 1, 2], None, [8, 8, 8], [0, 256] * 3)
        cv2.normalize(hist, hist)
        if prev_hist is not None:
            diffs.append(cv2.compareHist(prev_hist, hist, cv2.HISTCMP_CHISQR))
        prev_hist = hist
    return float(np.mean(diffs)) if diffs else 0.0


def _compute_heuristics(frames: list[np.ndarray]) -> tuple[float, list[str]]:
    artifacts: list[str] = []
    faces_per_frame = [detect_faces(f) for f in frames]

    jitter = _face_jitter_score(faces_per_frame)
    if jitter > JITTER_THRESHOLD:
        artifacts.append("facial_inconsistencies")

    blur_values = [_blur_variance(f) for f in frames]
    mean_blur = float(np.mean(blur_values)) if blur_values else 0.0
    if mean_blur < BLUR_VARIANCE_THRESHOLD:
        artifacts.append("compression_artifacts")

    flicker = _flicker_score(frames)
    if flicker > FLICKER_THRESHOLD:
        artifacts.append("temporal_flickering")

    faces_found_ratio = sum(1 for f in faces_per_frame if f) / max(len(faces_per_frame), 1)
    if faces_found_ratio == 0 and frames:
        artifacts.append("no_face_detected")

    jitter_component = min(jitter / max(JITTER_THRESHOLD, 1e-6), 1.0)
    blur_component = min(max((BLUR_VARIANCE_THRESHOLD - mean_blur) / BLUR_VARIANCE_THRESHOLD, 0.0), 1.0)
    flicker_component = min(flicker / max(FLICKER_THRESHOLD * 2, 1e-6), 1.0)

    heuristic_score = float(np.mean([jitter_component, blur_component, flicker_component]))
    return heuristic_score, artifacts


def analyze_video(
    video_path: str,
    max_frames: int = 16,
    progress_callback: Optional[Callable[[int], None]] = None,
) -> VideoAnalysisResult:
    def report(pct: int) -> None:
        if progress_callback:
            progress_callback(pct)

    report(5)
    frames, meta = extract_frames(video_path, max_frames=max_frames)
    if not frames:
        raise ValueError("No se pudieron extraer frames del video")
    report(30)

    heuristic_score, artifacts = _compute_heuristics(frames)
    report(55)

    inference_result = classify_frames(frames)
    report(85)

    video_score = ML_WEIGHT * inference_result.mean_fake_score + HEURISTIC_WEIGHT * heuristic_score
    is_ai_generated = video_score >= AI_GENERATED_THRESHOLD

    report(100)

    return VideoAnalysisResult(
        is_ai_generated=is_ai_generated,
        confidence=round(video_score, 4),
        video_score=round(video_score, 4),
        ml_score=round(inference_result.mean_fake_score, 4),
        heuristic_score=round(heuristic_score, 4),
        artifacts_detected=artifacts,
        frames_analyzed=len(frames),
        duration_seconds=round(meta["duration"], 2),
        fps=round(meta["fps"], 2),
        format=Path(video_path).suffix.lstrip(".").lower() or "unknown",
    )
