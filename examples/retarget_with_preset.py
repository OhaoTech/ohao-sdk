"""
Retarget with explicit preset — useful when auto-detection doesn't work.

Presets:
    "mixamo"  — Mixamo characters (XBot, YBot, Fuse characters, etc.)
    "ue5"     — UE5 Mannequin (Quinn, Manny, Quaternius models, etc.)

Usage:
    pip install ohao
    python retarget_with_preset.py dance.bvh Quinn.gltf ue5
"""

import sys
from ohao.mogen3d import retarget

if len(sys.argv) < 4:
    print("Usage: python retarget_with_preset.py <bvh> <character> <preset>")
    print("  preset: 'mixamo' or 'ue5'")
    sys.exit(1)

bvh_file = sys.argv[1]
char_file = sys.argv[2]
preset = sys.argv[3]

output = retarget(bvh_file, char_file, preset=preset)
print(f"Retargeted with '{preset}' preset: {output}")
