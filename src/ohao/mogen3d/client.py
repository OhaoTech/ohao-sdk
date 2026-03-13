"""MoGen3D API client — process videos, manage sparks, download BVH/FBX."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

import httpx

from ohao._exceptions import MoGenError

DEFAULT_BASE_URL = "https://mogen3dwham-production.up.railway.app"
POLL_INTERVAL = 2.0


class Sparks:
    """Current sparks balance and claim status."""

    def __init__(self, data: Dict[str, Any]):
        self._data = data

    @property
    def balance(self) -> int:
        return self._data["balance"]

    @property
    def can_claim(self) -> bool:
        return self._data["can_claim"]

    @property
    def daily_amount(self) -> int:
        return self._data["daily_amount"]

    @property
    def tier(self) -> str:
        return self._data["tier"]

    def __repr__(self) -> str:
        return f"Sparks(balance={self.balance}, tier={self.tier!r}, can_claim={self.can_claim})"


class Bundle:
    """A purchasable spark bundle."""

    def __init__(self, data: Dict[str, Any]):
        self._data = data

    @property
    def id(self) -> str:
        return self._data["id"]

    @property
    def sparks(self) -> int:
        return self._data["sparks"]

    @property
    def price_cents(self) -> int:
        return self._data["price_cents"]

    @property
    def label(self) -> str:
        return self._data["label"]

    @property
    def price(self) -> str:
        return f"${self.price_cents / 100:.2f}"

    def __repr__(self) -> str:
        return f"Bundle({self.label!r}, {self.price})"


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

        # Check sparks balance
        sparks = client.sparks()
        print(f"{sparks.balance} sparks available")

        # Claim daily sparks
        if sparks.can_claim:
            client.claim_sparks()

        # Process a video (costs 1 spark)
        job = client.process("dance.mp4", wait=True)
        path = job.download(format="bvh")
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = 30.0,
    ):
        if api_key is None:
            from ohao._credentials import load_api_key
            api_key = load_api_key()
        if not api_key:
            raise ValueError(
                "No API key found. Run `ohao login` or pass api_key= explicitly."
            )
        if not api_key.startswith("mg_"):
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

    # ── Sparks ─────────────────────────────────────────────────────────

    def sparks(self) -> Sparks:
        """Get current sparks balance and claim status."""
        data = self._request("GET", "/api/sparks")
        return Sparks(data)

    def claim_sparks(self) -> Dict[str, Any]:
        """
        Claim daily sparks allocation.

        Returns dict with ``balance``, ``claimed``, and ``message``.
        """
        return self._request("POST", "/api/sparks/claim")

    def bundles(self) -> List[Bundle]:
        """List available spark bundles for purchase."""
        data = self._request("GET", "/api/sparks/bundles")
        return [Bundle(b) for b in data["bundles"]]

    def purchase_bundle(self, bundle_id: str) -> str:
        """
        Start a Stripe checkout for a spark bundle.

        Returns the checkout URL — open it in a browser to complete payment.
        """
        data = self._request("POST", "/api/sparks/purchase", json={
            "bundle_id": bundle_id,
        })
        return data["url"]

    # ── Account ────────────────────────────────────────────────────────

    def status(self) -> Dict[str, Any]:
        """
        Get account status: tier, daily limits, subscription, sparks.

        Returns dict with ``tier``, ``daily_limit``, ``daily_used``,
        ``sparks_balance``, ``sparks_can_claim``, ``subscription``, etc.
        """
        return self._request("GET", "/api/billing/status")

    # ── Jobs ───────────────────────────────────────────────────────────

    def list_jobs(self, limit: int = 50, offset: int = 0) -> List[Job]:
        data = self._request("GET", "/api/jobs", params={
            "limit": limit, "offset": offset,
        })
        return [Job(j, self) for j in data["jobs"]]

    def get_job(self, job_id: str) -> Job:
        data = self._request("GET", f"/api/jobs/{job_id}")
        return Job(data, self)

    def delete_job(self, job_id: str) -> None:
        self._request("DELETE", f"/api/jobs/{job_id}")

    # ── Process ────────────────────────────────────────────────────────

    def process(
        self,
        video_path: str,
        *,
        export_fbx: bool = False,
        fps: int = 30,
        stationary: bool = True,
        wait: bool = False,
        timeout: float = 600,
    ) -> Job:
        """
        Upload a video and start processing. Costs 1 spark.

        Args:
            video_path: Path to a video file (.mp4, .mov, .webm, .avi).
            export_fbx: Also generate FBX output.
            fps: Output frame rate (24, 30, or 60).
            stationary: Lock root position (no locomotion).
            wait: Block until job completes.
            timeout: Max wait time in seconds (if wait=True).

        Returns a Job object. Use ``job.wait()`` or pass ``wait=True`` to block.
        """
        path = Path(video_path)
        if not path.exists():
            raise FileNotFoundError(f"Video not found: {video_path}")

        # Step 1: Get presigned upload URL
        upload_data = self._request("POST", "/api/upload", json={
            "filename": path.name,
        })
        video_id = upload_data["video_id"]
        upload_url = upload_data["upload_url"]

        # Step 2: Upload to storage
        with open(path, "rb") as f:
            resp = httpx.put(upload_url, content=f.read(), timeout=300.0)
            if resp.status_code >= 400:
                raise MoGenError(resp.status_code, "Failed to upload file")

        # Step 3: Create job (deducts 1 spark)
        job_data = self._request("POST", f"/api/videos/{video_id}/jobs", json={
            "export_fbx": export_fbx,
            "fps": fps,
            "stationary": stationary,
        })
        job = Job(job_data, self)
        if wait:
            job = job.wait(timeout=timeout)
        return job

    # ── Download ───────────────────────────────────────────────────────

    def download(
        self,
        job_id: str,
        format: Literal["bvh", "fbx", "json"] = "bvh",
        output_path: Optional[str] = None,
    ) -> Path:
        """Download a completed job's output file."""
        data = self._request("GET", f"/api/jobs/{job_id}/download/{format}")
        url = data["url"]
        filename = data["filename"]

        dest = Path(output_path) if output_path else Path(filename)
        resp = httpx.get(url, timeout=120.0, follow_redirects=True)
        if resp.status_code >= 400:
            raise MoGenError(resp.status_code, "Failed to download file")
        dest.write_bytes(resp.content)
        return dest

    # ── API Keys ───────────────────────────────────────────────────────

    def list_keys(self) -> List[Dict[str, Any]]:
        data = self._request("GET", "/api/keys")
        return data["keys"]

    def create_key(self, name: str = "Default") -> Dict[str, Any]:
        return self._request("POST", "/api/keys", json={"name": name})

    def revoke_key(self, key_id: str) -> None:
        self._request("DELETE", f"/api/keys/{key_id}")

    # ── Lifecycle ──────────────────────────────────────────────────────

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> "MoGen3DClient":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()
