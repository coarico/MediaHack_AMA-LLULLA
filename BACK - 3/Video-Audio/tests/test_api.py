"""Tests de integracion del endpoint POST /api/v1/analyze/video, usando la app
FastAPI minima definida en conftest.py (monta solo el router de video).
"""
from __future__ import annotations

import time


def test_analyze_video_accepts_valid_file_and_returns_job(client, sample_video_path):
    with open(sample_video_path, "rb") as f:
        response = client.post(
            "/api/v1/analyze/video",
            files={"file": ("sample.mp4", f, "video/mp4")},
        )

    assert response.status_code == 202
    body = response.json()
    assert body["status"] == "queued"
    assert "job_id" in body


def test_analyze_video_rejects_unsupported_content_type(client, sample_video_path):
    with open(sample_video_path, "rb") as f:
        response = client.post(
            "/api/v1/analyze/video",
            files={"file": ("sample.txt", f, "text/plain")},
        )

    assert response.status_code == 415


def test_job_status_unknown_id_returns_404(client):
    response = client.get("/api/v1/analyze/video/does-not-exist")
    assert response.status_code == 404


def test_full_flow_job_reaches_done(client, sample_video_path):
    with open(sample_video_path, "rb") as f:
        response = client.post(
            "/api/v1/analyze/video",
            files={"file": ("sample.mp4", f, "video/mp4")},
        )
    job_id = response.json()["job_id"]

    body = {}
    for _ in range(20):
        body = client.get(f"/api/v1/analyze/video/{job_id}").json()
        if body["status"] in {"done", "failed"}:
            break
        time.sleep(0.1)

    assert body["status"] == "done"
    assert body["result"] is not None
    assert 0.0 <= body["result"]["confidence"] <= 1.0
    assert body["result"]["metadata"]["format"] == "mp4"
