"""Tests for ohao.mogen3d.retarget."""

import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

from ohao._exceptions import BlenderNotFoundError, RetargetError
from ohao.mogen3d.retarget import _find_blender, retarget, KNOWN_PRESETS


def test_find_blender_explicit_path(tmp_path):
    fake = tmp_path / "blender.exe"
    fake.write_text("fake")
    assert _find_blender(str(fake)) == str(fake)


def test_find_blender_explicit_path_missing():
    with pytest.raises(BlenderNotFoundError, match="not found"):
        _find_blender("/nonexistent/blender")


def test_find_blender_on_path():
    with patch("shutil.which", return_value="/usr/bin/blender"):
        assert _find_blender() == "/usr/bin/blender"


def test_find_blender_not_found():
    with patch("shutil.which", return_value=None):
        with patch("pathlib.Path.exists", return_value=False):
            with pytest.raises(BlenderNotFoundError, match="Install Blender"):
                _find_blender()


def test_retarget_missing_bvh(tmp_path):
    char = tmp_path / "char.fbx"
    char.write_text("fake")
    with pytest.raises(FileNotFoundError, match="BVH"):
        retarget("/nonexistent/anim.bvh", str(char))


def test_retarget_missing_char(tmp_path):
    bvh = tmp_path / "anim.bvh"
    bvh.write_text("fake")
    with pytest.raises(FileNotFoundError, match="Character"):
        retarget(str(bvh), "/nonexistent/char.fbx")


def test_retarget_unknown_preset(tmp_path):
    bvh = tmp_path / "anim.bvh"
    bvh.write_text("fake")
    char = tmp_path / "char.fbx"
    char.write_text("fake")
    with patch("ohao.mogen3d.retarget._find_blender", return_value="/usr/bin/blender"):
        with pytest.raises(RetargetError, match="Unknown preset"):
            retarget(str(bvh), str(char), preset="nonexistent_preset")


def test_retarget_success(tmp_path):
    bvh = tmp_path / "anim.bvh"
    bvh.write_text("fake")
    char = tmp_path / "char.fbx"
    char.write_text("fake")
    out = tmp_path / "output.blend"

    mock_result = MagicMock()
    mock_result.returncode = 0

    with patch("ohao.mogen3d.retarget._find_blender", return_value="/usr/bin/blender"):
        with patch("subprocess.run", return_value=mock_result) as mock_run:
            # Create the output file to simulate Blender creating it
            out.write_text("blend")
            path = retarget(str(bvh), str(char), output_path=str(out))
            assert path == out
            # Verify Blender was called with correct args
            cmd = mock_run.call_args[0][0]
            assert "/usr/bin/blender" in cmd
            assert "--background" in cmd
            assert str(bvh) in cmd
            assert str(char) in cmd


def test_retarget_blender_error(tmp_path):
    bvh = tmp_path / "anim.bvh"
    bvh.write_text("fake")
    char = tmp_path / "char.fbx"
    char.write_text("fake")

    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_result.stderr = "Blender crashed"
    mock_result.stdout = ""

    with patch("ohao.mogen3d.retarget._find_blender", return_value="/usr/bin/blender"):
        with patch("subprocess.run", return_value=mock_result):
            with pytest.raises(RetargetError, match="code 1"):
                retarget(str(bvh), str(char))


def test_known_presets_exist():
    for name, path in KNOWN_PRESETS.items():
        assert path.exists(), f"Preset {name} not found at {path}"
