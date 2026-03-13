"""Tests for ohao.mogen3d.client."""

import json
import pytest
import httpx
from pathlib import Path

from ohao._exceptions import MoGenError
from ohao.mogen3d.client import MoGen3DClient, Job


API_KEY = "mg_test_key_123"


def test_invalid_api_key():
    with pytest.raises(ValueError, match="mg_"):
        MoGen3DClient(api_key="bad_key")


def test_client_context_manager():
    with MoGen3DClient(api_key=API_KEY) as client:
        assert client._http is not None


def test_list_jobs(httpx_mock):
    httpx_mock.add_response(
        url="https://mogen3dwham-production.up.railway.app/api/jobs",
        json={"jobs": [
            {"id": "j1", "status": "completed", "filename": "test.mp4", "created_at": "2026-01-01"},
        ]},
    )
    with MoGen3DClient(api_key=API_KEY) as client:
        jobs = client.list_jobs()
        assert len(jobs) == 1
        assert jobs[0].id == "j1"
        assert jobs[0].status == "completed"


def test_get_job(httpx_mock):
    httpx_mock.add_response(
        url="https://mogen3dwham-production.up.railway.app/api/jobs/j1",
        json={"id": "j1", "status": "completed", "filename": "test.mp4", "created_at": "2026-01-01"},
    )
    with MoGen3DClient(api_key=API_KEY) as client:
        job = client.get_job("j1")
        assert job.id == "j1"


def test_api_error(httpx_mock):
    httpx_mock.add_response(
        url="https://mogen3dwham-production.up.railway.app/api/jobs",
        status_code=401,
        json={"detail": "Unauthorized"},
    )
    with MoGen3DClient(api_key=API_KEY) as client:
        with pytest.raises(MoGenError, match="401"):
            client.list_jobs()


def test_job_repr():
    job = Job({"id": "j1", "status": "pending", "filename": "test.mp4", "created_at": "2026-01-01"}, None)
    assert "j1" in repr(job)
    assert "pending" in repr(job)


def test_job_frames():
    job = Job({"id": "j1", "status": "completed", "filename": "t.mp4", "created_at": "x", "result": {"frames": 120}}, None)
    assert job.frames == 120


def test_job_frames_none():
    job = Job({"id": "j1", "status": "pending", "filename": "t.mp4", "created_at": "x"}, None)
    assert job.frames is None


def test_upload_file_not_found():
    with MoGen3DClient(api_key=API_KEY) as client:
        with pytest.raises(FileNotFoundError):
            client.upload("/nonexistent/video.mp4")


def test_upload_flow(httpx_mock, tmp_path):
    video = tmp_path / "dance.mp4"
    video.write_bytes(b"fake video data")

    # Step 1: Upload endpoint returns video_id + upload_url
    httpx_mock.add_response(
        url="https://mogen3dwham-production.up.railway.app/api/upload",
        json={"video_id": "v1", "upload_url": "https://r2.example.com/upload", "input_key": "k1"},
    )
    # Step 2: R2 upload
    httpx_mock.add_response(url="https://r2.example.com/upload", status_code=200)
    # Step 3: Create job
    httpx_mock.add_response(
        url="https://mogen3dwham-production.up.railway.app/api/videos/v1/jobs",
        json={"id": "j1", "status": "pending", "filename": "dance.mp4", "created_at": "2026-01-01"},
    )

    with MoGen3DClient(api_key=API_KEY) as client:
        job = client.upload(str(video))
        assert job.id == "j1"
        assert job.status == "pending"


def test_delete_job(httpx_mock):
    httpx_mock.add_response(
        url="https://mogen3dwham-production.up.railway.app/api/jobs/j1",
        status_code=200,
        content=b"",
    )
    with MoGen3DClient(api_key=API_KEY) as client:
        client.delete_job("j1")
