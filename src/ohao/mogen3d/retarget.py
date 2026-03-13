"""Blender-based BVH retargeting — invoke Blender as a subprocess."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional

from ohao._exceptions import BlenderNotFoundError, RetargetError

_BLENDER_SCRIPT = Path(__file__).parent / "_blender_script.py"

_PRESET_DIR = Path(__file__).parent / "presets"

KNOWN_PRESETS = {
    "mixamo": _PRESET_DIR / "mixamo.json",
    "ue5": _PRESET_DIR / "ue5_mannequin.json",
}


def _find_blender(blender_path: Optional[str] = None) -> str:
    """Locate the Blender executable."""
    if blender_path:
        p = Path(blender_path)
        if p.exists():
            return str(p)
        raise BlenderNotFoundError(f"Blender not found at: {blender_path}")

    # Try PATH first
    found = shutil.which("blender")
    if found:
        return found

    # Common install locations
    candidates = []
    if sys.platform == "win32":
        candidates = [
            Path.home() / "scoop/apps/blender/current/blender.exe",
            Path("C:/Program Files/Blender Foundation/Blender 4.0/blender.exe"),
            Path("C:/Program Files/Blender Foundation/Blender 3.6/blender.exe"),
            Path("C:/Program Files (x86)/Steam/steamapps/common/Blender/blender.exe"),
        ]
    elif sys.platform == "darwin":
        candidates = [
            Path("/Applications/Blender.app/Contents/MacOS/Blender"),
        ]
    else:
        candidates = [
            Path("/usr/bin/blender"),
            Path("/snap/bin/blender"),
        ]

    for c in candidates:
        if c.exists():
            return str(c)

    raise BlenderNotFoundError(
        "Blender not found. Install Blender or pass blender_path= explicitly."
    )


def retarget(
    bvh_path: str,
    character_path: str,
    *,
    output_path: Optional[str] = None,
    preset: Optional[str] = None,
    blender_path: Optional[str] = None,
    background: bool = True,
) -> Path:
    """
    Retarget a BVH animation onto a character model using Blender.

    Args:
        bvh_path: Path to the BVH file (from MoGen3D).
        character_path: Path to the character model (.fbx, .glb, .gltf).
        output_path: Where to save the retargeted .blend file.
                     Defaults to ``{bvh_stem}_{char_stem}.blend``.
        preset: Rig preset name ("mixamo", "ue5") or path to a JSON preset.
                If None, auto-detects from the character's bone names.
        blender_path: Explicit path to the Blender executable.
        background: Run Blender in background mode (no GUI). Default True.

    Returns:
        Path to the saved .blend file.

    Raises:
        BlenderNotFoundError: If Blender cannot be found.
        RetargetError: If Blender exits with an error.
    """
    bvh = Path(bvh_path)
    char = Path(character_path)
    if not bvh.exists():
        raise FileNotFoundError(f"BVH not found: {bvh_path}")
    if not char.exists():
        raise FileNotFoundError(f"Character not found: {character_path}")

    blender = _find_blender(blender_path)

    if output_path is None:
        output_path = str(Path.cwd() / f"{bvh.stem}_{char.stem}.blend")
    out = Path(output_path)

    # Build Blender command
    cmd = [blender]
    if background:
        cmd.append("--background")
    cmd.extend([
        "--python", str(_BLENDER_SCRIPT),
        "--",
        "--bvh", str(bvh),
        "--char", str(char),
        "--output", str(out),
    ])

    if preset:
        # If it's a known preset name, resolve to path
        if preset in KNOWN_PRESETS:
            cmd.extend(["--preset-file", str(KNOWN_PRESETS[preset])])
        elif Path(preset).exists():
            cmd.extend(["--preset-file", preset])
        else:
            raise RetargetError(f"Unknown preset: {preset}")

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        stderr = result.stderr or result.stdout
        raise RetargetError(f"Blender exited with code {result.returncode}:\n{stderr}")

    if not out.exists():
        raise RetargetError(f"Blender finished but output file not created: {out}")

    return out
