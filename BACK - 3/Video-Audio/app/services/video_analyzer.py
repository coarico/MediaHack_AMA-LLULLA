"""Analisis de video: extraccion de frames, heuristicas OpenCV e inferencia ML combinada.

Sigue el mismo contrato que AudioAnalyzer (analyze_audio.py): una clase con un
metodo async `analyze(file_path) -> AnalysisResponse`, usando los schemas
compartidos en app.models.

El score final combina dos senales independientes:
  - ml_score: probabilidad media de 'fake' segun el modelo de clasificacion (app.ml).
  - heuristicas OpenCV: jitter facial, perdida de nitidez/artefactos de compresion,
    parpadeo/flicker de iluminacion entre frames.

En los tres campos heuristicos, igual que en AudioAnalysisDetails, el score
representa "que tanto apunta esta senal a que el contenido es IA": mas alto =
mas sospechoso (no "que tan consistente/limpio se ve").
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import List, Optional

import cv2
import numpy as np

from app.config import settings
from app.ml.inference import classify_frames
from app.models import (
    AnalysisResponse,
    ArtifactDetection,
    MediaMetadata,
    VideoAnalysisDetails,
)

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
MAX_FRAMES = 16

JITTER_THRESHOLD = 0.18
BLUR_VARIANCE_THRESHOLD = 60.0
FLICKER_THRESHOLD = 35.0


def _get_face_detector() -> cv2.FaceDetectorYN:
    global _face_detector
    if _face_detector is None:
        _face_detector = cv2.FaceDetectorYN_create(FACE_DETECTOR_MODEL_PATH, "", (320, 320))
    return _face_detector


def extract_frames(video_path, max_frames: int = MAX_FRAMES) -> tuple[list[np.ndarray], dict]:
    """Extrae hasta `max_frames` frames distribuidos uniformemente en el video."""
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise ValueError(f"No se pudo abrir el video: {video_path}")

    try:
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS) or 0.0
        duration = total_frames / fps if fps else 0.0
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

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

        if sampled:
            height, width = sampled[0].shape[:2]

        metadata = {
            "total_frames": total_frames,
            "fps": fps,
            "duration": duration,
            "width": width,
            "height": height,
        }
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


class VideoAnalyzer:
    """
    Analyze video files for AI-generated content detection

    Combina un clasificador de imagenes real/fake (app.ml, corrido por frame)
    con heuristicas de OpenCV para detectar:
    - Inconsistencias faciales entre frames (jitter de posicion/tamano)
    - Artefactos de compresion (perdida de nitidez)
    - Parpadeo/flicker de iluminacion entre frames
    """

    async def analyze(self, file_path: Path) -> AnalysisResponse:
        """
        Analyze video file for AI-generated content

        Args:
            file_path: Path to video file

        Returns:
            AnalysisResponse with analysis results
        """
        frames, meta = extract_frames(file_path)
        if not frames:
            raise ValueError("No se pudieron extraer frames del video")

        facial_consistency, frame_artifacts, compression_anomalies, artifacts = (
            self._analyze_heuristics(frames)
        )

        inference_result = classify_frames(frames)
        ml_score = inference_result.mean_fake_score

        heuristic_score = (facial_consistency + frame_artifacts + compression_anomalies) / 3
        overall_score = ML_WEIGHT * ml_score + HEURISTIC_WEIGHT * heuristic_score
        is_ai_generated = overall_score >= settings.video_confidence_threshold

        video_details = VideoAnalysisDetails(
            facial_consistency=round(facial_consistency, 4),
            frame_artifacts=round(frame_artifacts, 4),
            compression_anomalies=round(compression_anomalies, 4),
            artifacts=artifacts,
        )

        metadata = self._extract_metadata(file_path, meta)

        return AnalysisResponse(
            is_ai_generated=is_ai_generated,
            confidence=round(overall_score, 4),
            analysis_type="video",
            video_details=video_details,
            metadata=metadata,
            processing_time=0.0,  # Will be set by main.py
        )

    def _extract_metadata(self, file_path: Path, meta: dict) -> MediaMetadata:
        file_path = Path(file_path)
        file_size = file_path.stat().st_size if file_path.exists() else None

        return MediaMetadata(
            duration=round(meta["duration"], 2),
            format=file_path.suffix[1:].lower() or "unknown",
            size=file_size,
            resolution=f"{meta['width']}x{meta['height']}" if meta.get("width") else None,
            fps=round(meta["fps"], 2),
        )

    def _analyze_heuristics(
        self, frames: list[np.ndarray]
    ) -> tuple[float, float, float, List[ArtifactDetection]]:
        artifacts: List[ArtifactDetection] = []
        faces_per_frame = [detect_faces(f) for f in frames]

        jitter = _face_jitter_score(faces_per_frame)
        facial_consistency = min(jitter / max(JITTER_THRESHOLD, 1e-6), 1.0)
        if jitter > JITTER_THRESHOLD:
            artifacts.append(ArtifactDetection(
                type="facial_inconsistencies",
                confidence=round(facial_consistency, 4),
                description="Saltos bruscos en la posicion/tamano del rostro entre frames",
            ))

        blur_values = [_blur_variance(f) for f in frames]
        mean_blur = float(np.mean(blur_values)) if blur_values else 0.0
        frame_artifacts = min(
            max((BLUR_VARIANCE_THRESHOLD - mean_blur) / BLUR_VARIANCE_THRESHOLD, 0.0), 1.0
        )
        if mean_blur < BLUR_VARIANCE_THRESHOLD:
            artifacts.append(ArtifactDetection(
                type="compression_artifacts",
                confidence=round(frame_artifacts, 4),
                description="Perdida de nitidez consistente con artefactos de compresion/generacion",
            ))

        flicker = _flicker_score(frames)
        compression_anomalies = min(flicker / max(FLICKER_THRESHOLD * 2, 1e-6), 1.0)
        if flicker > FLICKER_THRESHOLD:
            artifacts.append(ArtifactDetection(
                type="temporal_flickering",
                confidence=round(compression_anomalies, 4),
                description="Cambios abruptos de iluminacion/color entre frames consecutivos",
            ))

        faces_found_ratio = sum(1 for f in faces_per_frame if f) / max(len(faces_per_frame), 1)
        if faces_found_ratio == 0 and frames:
            artifacts.append(ArtifactDetection(
                type="no_face_detected",
                confidence=1.0,
                description="No se detecto ningun rostro en los frames analizados",
            ))

        return facial_consistency, frame_artifacts, compression_anomalies, artifacts
