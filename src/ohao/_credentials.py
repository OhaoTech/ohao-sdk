"""Local credential storage — ~/.ohao/credentials.json"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

CREDENTIALS_DIR = Path.home() / ".ohao"
CREDENTIALS_FILE = CREDENTIALS_DIR / "credentials.json"


def save_api_key(api_key: str) -> Path:
    """Save API key to ~/.ohao/credentials.json."""
    CREDENTIALS_DIR.mkdir(parents=True, exist_ok=True)
    data = {}
    if CREDENTIALS_FILE.exists():
        try:
            data = json.loads(CREDENTIALS_FILE.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    data["api_key"] = api_key
    CREDENTIALS_FILE.write_text(json.dumps(data, indent=2) + "\n")
    # Restrict permissions on Unix
    try:
        CREDENTIALS_FILE.chmod(0o600)
    except OSError:
        pass
    return CREDENTIALS_FILE


def load_api_key() -> Optional[str]:
    """
    Load API key from (in order):
    1. OHAO_API_KEY env var
    2. ~/.ohao/credentials.json
    """
    import os
    key = os.environ.get("OHAO_API_KEY")
    if key:
        return key
    if CREDENTIALS_FILE.exists():
        try:
            data = json.loads(CREDENTIALS_FILE.read_text())
            return data.get("api_key")
        except (json.JSONDecodeError, OSError):
            pass
    return None


def clear_api_key() -> bool:
    """Remove saved credentials. Returns True if file existed."""
    if CREDENTIALS_FILE.exists():
        CREDENTIALS_FILE.unlink()
        return True
    return False
