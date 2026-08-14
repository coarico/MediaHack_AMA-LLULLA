"""Tests de integracion del endpoint POST /api/v1/analyze/video sobre la app
FastAPI real (app.main), montada junto al endpoint de audio del companero.
"""
from __future__ import annotations


def test_analyze_video_returns_analysis_response(client, sample_video_path):
    with open(sample_video_path, "rb") as f:
        response = client.post(
            "/api/v1/analyze/video",
            files={"file": ("sample.mp4", f, "video/mp4")},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["analysis_type"] == "video"
    assert 0.0 <= body["confidence"] <= 1.0
    assert isinstance(body["is_ai_generated"], bool)
    assert body["video_details"] is not None
    assert body["metadata"]["format"] == "mp4"
    assert body["processing_time"] > 0.0


def test_analyze_video_rejects_unsupported_extension(client, tmp_path):
    bogus = tmp_path / "not_a_video.txt"
    bogus.write_text("hello")

    with open(bogus, "rb") as f:
        response = client.post(
            "/api/v1/analyze/video",
            files={"file": ("not_a_video.txt", f, "text/plain")},
        )

    assert response.status_code == 400


def test_health_check_still_works(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
