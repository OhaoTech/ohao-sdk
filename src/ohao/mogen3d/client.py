"""MoGen3D API client — upload video, poll for completion, download BVH/FBX."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

import httpx

from ohao._exceptions import MoGenError

DEFAULT_BASE_URL = "https://mogen3dwham-production.up.railway.app"
POLL_INTERVAL = 2.0


class Job:
    """Represents a MoGen3D processing job."""

    def __init__(self, data: Dict[str, Any], client: "MoGen3DClient"):
        self._data = data
        self._client = client

    @property
    def id(self) -> str:
        return self._data["id"]

    @property
    def status(self) -> str:
        return self._data["status"]

    @property
    def filename(self) -> str:
        return self._data["filename"]

    @property
    def frames(self) -> Optional[int]:
        r = self._data.get("result")
        return r.get("frames") if r else self._data.get("frames")

    @property
    def error(self) -> Optional[str]:
        return self._data.get("error")

    @property
    def created_at(self) -> str:
        return self._data["created_at"]

    def refresh(self) -> "Job":
        return self._client.get_job(self.id)

    def wait(self, timeout: float = 600, poll: float = POLL_INTERVAL) -> "Job":
        """Block until job completes or fails."""
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            job = self.refresh()
            if job.status in ("completed", "failed"):
                return job
            time.sleep(poll)
        raise TimeoutError(f"Job {self.id} did not complete within {timeout}s")

    def download(
        self,
        format: Literal["bvh", "fbx", "json"] = "bvh",
        output_path: Optional[str] = None,
    ) -> Path:
        return self._client.download(self.id, format=format, output_path=output_path)

    def __repr__(self) -> str:
        return f"Job(id={self.id!r}, status={self.status!r}, filename={self.filename!r})"


class MoGen3DClient:
    """
    MoGen3D API client.

    Usage::

        from ohao.mogen3d import MoGen3DClient

        client = MoGen3DClient(api_key="mg_your_key_here")
        job = client.upload("dance.mp4")
        job = job.wait()
        path = job.download(format="bvh")
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = 30.0,
    ):
        if not api_key or not api_key.startswith("mg_"):
            raise ValueError("API key must start with 'mg_'")
        self._http = httpx.Client(
            base_url=base_url,
            headers={"X-API-Key": api_key},
            timeout=timeout,
        )

    def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        resp = self._http.request(method, path, **kwargs)
        if resp.status_code >= 400:
            detail = resp.text
            try:
                detail = resp.json().get("detail", resp.text)
            except Exception:
                pass
            raise MoGenError(resp.status_code, detail)
        return resp.json() if resp.content else None

    # ── Jobs ──────────────────────────────────────────────────────────

    def list_jobs(self) -> List[Job]:
        data = self._request("GET", "/api/jobs")
        return [Job(j, self) for j in data["jobs"]]

    def get_job(self, job_id: str) -> Job:
        data = self._request("GET", f"/api/jobs/{job_id}")
        return Job(data, self)

    def delete_job(self, job_id: str) -> None:
        self._request("DELETE", f"/api/jobs/{job_id}")

    # ── Upload & Process ──────────────────────────────────────────────

    def upload(
        self,
        video_path: str,
        *,
        pipeline: Literal["2d", "3d"] = "2d",
        export_fbx: bool = False,
        fps: int = 30,
        stationary: bool = True,
        wait: bool = False,
        timeout: float = 600,
    ) -> Job:
        """
        Upload a video and start processing.

        Returns a Job object. Use job.wait() or pass wait=True to block.
        """
        path = Path(video_path)
        if not path.exists():
            raise FileNotFoundError(f"Video not found: {video_path}")

        # Step 1: Get presigned upload URL (new workspace model)
        upload_data = self._request("POST", "/api/upload", json={
            "filename": path.name,
        })
        video_id = upload_data["video_id"]
        upload_url = upload_data["upload_url"]

        # Step 2: Upload video to R2
        with open(path, "rb") as f:
            resp = httpx.put(upload_url, content=f.read(), timeout=300.0)
            if resp.status_code >= 400:
                raise MoGenError(resp.status_code, "Failed to upload video to storage")

        # Step 3: Create job on the video
        job_data = self._request("POST", f"/api/videos/{video_id}/jobs", json={
            "pipeline": pipeline,
            "export_fbx": export_fbx,
            "fps": fps,
            "stationary": stationary,
        })
        job = Job(job_data, self)
        if wait:
            job = job.wait(timeout=timeout)
        return job

    # ── Download ──────────────────────────────────────────────────────

    def download(
        self,
        job_id: str,
        format: Literal["bvh", "fbx", "json"] = "bvh",
        output_path: Optional[str] = None,
    ) -> Path:
        data = self._request("GET", f"/api/jobs/{job_id}/download/{format}")
        url = data["url"]
        filename = data["filename"]

        dest = Path(output_path) if output_path else Path(filename)
        resp = httpx.get(url, timeout=120.0, follow_redirects=True)
        if resp.status_code >= 400:
            raise MoGenError(resp.status_code, "Failed to download file")
        dest.write_bytes(resp.content)
        return dest

    # ── API Keys ──────────────────────────────────────────────────────

    def list_keys(self) -> List[Dict[str, Any]]:
        data = self._request("GET", "/api/keys")
        return data["keys"]

    def create_key(self, name: str = "Default") -> Dict[str, Any]:
        return self._request("POST", "/api/keys", json={"name": name})

    def revoke_key(self, key_id: str) -> None:
        self._request("DELETE", f"/api/keys/{key_id}")

    # ── Lifecycle ─────────────────────────────────────────────────────

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> "MoGen3DClient":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()
