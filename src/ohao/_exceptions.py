"""Shared exception hierarchy."""


class OhaoError(Exception):
    """Base exception for ohao SDK."""


class MoGenError(OhaoError):
    """Raised when the MoGen3D API returns an error."""

    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"HTTP {status_code}: {detail}")


class RetargetError(OhaoError):
    """Raised when Blender retargeting fails."""


class BlenderNotFoundError(RetargetError):
    """Raised when Blender executable cannot be found."""
