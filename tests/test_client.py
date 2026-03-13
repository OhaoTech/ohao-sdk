"""Tests for ohao.mogen3d.client."""

import pytest
import httpx

from ohao._exceptions import MoGenError
from ohao.mogen3d.client import MoGen3DClient, Job, Sparks, Bundle


API_KEY = "mg_test_key_123"
BASE = "https://mogen3dwham-production.up.railway.app"


def test_invalid_api_key():
    with pytest.raises(ValueError, match="mg_"):
        MoGen3DClient(api_key="bad_key")


def test_client_context_manager():
    with MoGen3DClient(api_key=API_KEY) as client:
        assert client._http is not None


# ── Sparks ────────────────────────────────────────────────────────────

def test_sparks(httpx_mock):
    httpx_mock.add_response(
        url=f"{BASE}/api/sparks",
        json={"balance": 5, "can_claim": True, "daily_amount": 1, "tier": "free"},
    )
    with MoGen3DClient(api_key=API_KEY) as client:
        s = client.sparks()
        assert s.balance == 5
        assert s.can_claim is True
        assert s.tier == "free"
        assert s.daily_amount == 1
        assert "5" in repr(s)


def test_claim_sparks(httpx_mock):
    httpx_mock.add_response(
        url=f"{BASE}/api/sparks/claim",
        json={"balance": 2, "claimed": 1, "message": "+1 sparks!"},
    )
    with MoGen3DClient(api_key=API_KEY) as client:
        result = client.claim_sparks()
        assert result["claimed"] == 1
        assert result["balance"] == 2


def test_bundles(httpx_mock):
    httpx_mock.add_response(
        url=f"{BASE}/api/sparks/bundles",
        json={"bundles": [
            {"id": "sparks_30", "sparks": 30, "price_cents": 399, "label": "30 Sparks"},
            {"id": "sparks_100", "sparks": 100, "price_cents": 999, "label": "100 Sparks"},
        ]},
    )
    with MoGen3DClient(api_key=API_KEY) as client:
        bs = client.bundles()
        assert len(bs) == 2
        assert bs[0].sparks == 30
        assert bs[0].price == "$3.99"
        assert bs[1].id == "sparks_100"
        assert "30 Sparks" in repr(bs[0])


def test_purchase_bundle(httpx_mock):
    httpx_mock.add_response(
        url=f"{BASE}/api/sparks/purchase",
        json={"url": "https://checkout.stripe.com/pay/test123"},
    )
    with MoGen3DClient(api_key=API_KEY) as client:
        url = client.purchase_bundle("sparks_30")
        assert "stripe.com" in url


# ── Account ───────────────────────────────────────────────────────────

def test_status(httpx_mock):
    httpx_mock.add_response(
        url=f"{BASE}/api/billing/status",
        json={
            "tier": "pro", "daily_limit": 50, "daily_used": 3,
            "sparks_balance": 42, "sparks_can_claim": False,
            "sparks_daily_amount": 15,
            "subscription": {"status": "active", "current_period_end": "2026-04-13"},
        },
    )
    with MoGen3DClient(api_key=API_KEY) as client:
        s = client.status()
        assert s["tier"] == "pro"
        assert s["sparks_balance"] == 42
        assert s["daily_used"] == 3


# ── Jobs ──────────────────────────────────────────────────────────────

def test_list_jobs(httpx_mock):
    httpx_mock.add_response(
        url=f"{BASE}/api/jobs?limit=50&offset=0",
        json={"jobs": [
            {"id": "j1", "status": "completed", "filename": "test.mp4", "created_at": "2026-01-01"},
        ], "total": 1},
    )
    with MoGen3DClient(api_key=API_KEY) as client:
        jobs = client.list_jobs()
        assert len(jobs) == 1
        assert jobs[0].id == "j1"


def test_get_job(httpx_mock):
    httpx_mock.add_response(
        url=f"{BASE}/api/jobs/j1",
        json={"id": "j1", "status": "completed", "filename": "test.mp4", "created_at": "2026-01-01"},
    )
    with MoGen3DClient(api_key=API_KEY) as client:
        job = client.get_job("j1")
        assert job.id == "j1"


def test_api_error(httpx_mock):
    httpx_mock.add_response(
        url=f"{BASE}/api/jobs?limit=50&offset=0",
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


def test_process_file_not_found():
    with MoGen3DClient(api_key=API_KEY) as client:
        with pytest.raises(FileNotFoundError):
            client.process("/nonexistent/video.mp4")


def test_process_flow(httpx_mock, tmp_path):
    video = tmp_path / "dance.mp4"
    video.write_bytes(b"fake video data")

    httpx_mock.add_response(
        url=f"{BASE}/api/upload",
        json={"video_id": "v1", "upload_url": "https://r2.example.com/upload", "input_key": "k1"},
    )
    httpx_mock.add_response(url="https://r2.example.com/upload", status_code=200)
    httpx_mock.add_response(
        url=f"{BASE}/api/videos/v1/jobs",
        json={"id": "j1", "status": "pending", "filename": "dance.mp4", "created_at": "2026-01-01"},
    )

    with MoGen3DClient(api_key=API_KEY) as client:
        job = client.process(str(video))
        assert job.id == "j1"
        assert job.status == "pending"


def test_delete_job(httpx_mock):
    httpx_mock.add_response(
        url=f"{BASE}/api/jobs/j1",
        status_code=200,
        content=b"",
    )
    with MoGen3DClient(api_key=API_KEY) as client:
        client.delete_job("j1")
