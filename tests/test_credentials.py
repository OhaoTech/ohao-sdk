"""Tests for ohao._credentials."""

import json
import pytest
from unittest.mock import patch
from pathlib import Path

from ohao._credentials import save_api_key, load_api_key, clear_api_key


@pytest.fixture
def cred_dir(tmp_path):
    """Redirect credentials to a temp dir."""
    cred_file = tmp_path / "credentials.json"
    with patch("ohao._credentials.CREDENTIALS_DIR", tmp_path), \
         patch("ohao._credentials.CREDENTIALS_FILE", cred_file):
        yield tmp_path, cred_file


def test_save_and_load(cred_dir):
    tmp_path, cred_file = cred_dir
    save_api_key("mg_test_key_123")
    assert cred_file.exists()

    data = json.loads(cred_file.read_text())
    assert data["api_key"] == "mg_test_key_123"

    key = load_api_key()
    assert key == "mg_test_key_123"


def test_load_returns_none_when_missing(cred_dir):
    key = load_api_key()
    assert key is None


def test_env_var_takes_priority(cred_dir):
    save_api_key("mg_saved_key")
    with patch.dict("os.environ", {"OHAO_API_KEY": "mg_env_key"}):
        key = load_api_key()
        assert key == "mg_env_key"


def test_clear(cred_dir):
    tmp_path, cred_file = cred_dir
    save_api_key("mg_test_key")
    assert cred_file.exists()
    assert clear_api_key() is True
    assert not cred_file.exists()
    assert clear_api_key() is False


def test_overwrite(cred_dir):
    save_api_key("mg_old_key")
    save_api_key("mg_new_key")
    assert load_api_key() == "mg_new_key"


def test_client_auto_loads(cred_dir, httpx_mock):
    """Client picks up saved credentials automatically."""
    save_api_key("mg_auto_key")
    httpx_mock.add_response(
        url="https://mogen3dwham-production.up.railway.app/api/sparks",
        json={"balance": 1, "can_claim": False, "daily_amount": 1, "tier": "free"},
    )
    from ohao.mogen3d.client import MoGen3DClient
    with MoGen3DClient() as client:
        s = client.sparks()
        assert s.balance == 1


def test_client_no_key_raises(cred_dir):
    """Client raises helpful error when no key found."""
    from ohao.mogen3d.client import MoGen3DClient
    with pytest.raises(ValueError, match="ohao login"):
        MoGen3DClient()
