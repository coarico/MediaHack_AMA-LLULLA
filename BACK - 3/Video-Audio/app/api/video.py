"""Endpoint de analisis de video: POST /api/v1/analyze/video con procesamiento
asincrono y seguimiento de progreso via GET /api/v1/analyze/video/{job_id}.

Este router es independiente de main.py (aun no existe / es responsabilidad
del companero). Cuando exista, se monta con:

    from app.api.video import router as video_router
    app.include_router(video_router)
"""
from __future__ import annotations

import tempfile
import uuid
from pathlib import Path
from typing import Dict

from fastapi import APIRouter, BackgroundTasks, File, HTTPException, UploadFile

from app.models.video_schemas import (
    JobStatus,
    VideoAnalysisDetail,
    VideoAnalysisMetadata,
    VideoAnalysisResponse,
    VideoJobAcceptedResponse,
    VideoJobStatusResponse,
)
from app.services.video_analyzer import analyze_video

router = APIRouter(prefix="/api/v1/analyze", tags=["video"])

MAX_UPLOAD_BYTES = 50 * 1024 * 1024  # 50MB, alineado con el limite mostrado en el front
ALLOWED_CONTENT_TYPES = {"video/mp4", "video/quicktime", "video/x-matroska", "video/webm"}

# Almacen de jobs en memoria: suficiente para un solo proceso (hackathon).
# Si se necesita escalar a varios workers, mover a Redis/DB.
_jobs: Dict[str, dict] = {}


def _run_analysis(job_id: str, video_path: str) -> None:
    job = _jobs[job_id]
    job["status"] = JobStatus.PROCESSING
    try:
        def on_progress(pct: int) -> None:
            job["progress"] = pct

        result = analyze_video(video_path, progress_callback=on_progress)

        job["result"] = VideoAnalysisResponse(
            is_ai_generated=result.is_ai_generated,
            confidence=result.confidence,
            analysis=VideoAnalysisDetail(
                video_score=result.video_score,
                ml_score=result.ml_score,
                heuristic_score=result.heuristic_score,
                artifacts_detected=result.artifacts_detected,
            ),
            metadata=VideoAnalysisMetadata(
                duration=result.duration_seconds,
                format=result.format,
                fps=result.fps,
                frames_analyzed=result.frames_analyzed,
            ),
        )
        job["status"] = JobStatus.DONE
        job["progress"] = 100
    except Exception as exc:  # se reporta al cliente via polling, no se relanza
        job["status"] = JobStatus.FAILED
        job["error"] = str(exc)
    finally:
        Path(video_path).unlink(missing_ok=True)


@router.post("/video", response_model=VideoJobAcceptedResponse, status_code=202)
async def analyze_video_endpoint(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
) -> VideoJobAcceptedResponse:
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(415, f"Tipo de archivo no soportado: {file.content_type}")

    suffix = Path(file.filename or "").suffix or ".mp4"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        size = 0
        while chunk := await file.read(1024 * 1024):
            size += len(chunk)
            if size > MAX_UPLOAD_BYTES:
                Path(tmp.name).unlink(missing_ok=True)
                raise HTTPException(413, "El archivo excede el limite de 50MB")
            tmp.write(chunk)
        video_path = tmp.name

    job_id = str(uuid.uuid4())
    _jobs[job_id] = {"status": JobStatus.QUEUED, "progress": 0, "result": None, "error": None}
    background_tasks.add_task(_run_analysis, job_id, video_path)

    return VideoJobAcceptedResponse(job_id=job_id, status=JobStatus.QUEUED)


@router.get("/video/{job_id}", response_model=VideoJobStatusResponse)
async def get_video_job_status(job_id: str) -> VideoJobStatusResponse:
    job = _jobs.get(job_id)
    if job is None:
        raise HTTPException(404, "job_id no encontrado")

    return VideoJobStatusResponse(
        job_id=job_id,
        status=job["status"],
        progress=job["progress"],
        result=job["result"],
        error=job["error"],
    )
