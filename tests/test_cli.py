"""Tests for ohao CLI."""

from click.testing import CliRunner
from ohao._cli import main


def test_version():
    runner = CliRunner()
    result = runner.invoke(main, ["--version"])
    assert result.exit_code == 0
    assert "0.1.0" in result.output


def test_mogen3d_help():
    runner = CliRunner()
    result = runner.invoke(main, ["mogen3d", "--help"])
    assert result.exit_code == 0
    assert "process" in result.output
    assert "retarget" in result.output
    assert "sparks" in result.output
    assert "claim" in result.output
    assert "status" in result.output
    assert "bundles" in result.output


def test_process_missing_api_key():
    runner = CliRunner()
    result = runner.invoke(main, ["mogen3d", "process", "nonexistent.mp4"], env={"OHAO_API_KEY": ""})
    assert result.exit_code != 0


def test_retarget_missing_files():
    runner = CliRunner()
    result = runner.invoke(main, ["mogen3d", "retarget", "nonexistent.bvh", "nonexistent.fbx"])
    assert result.exit_code != 0
