"""
Use a specific Blender installation.

Useful when you have multiple Blender versions or a non-standard install path.

Usage:
    pip install ohao
    python custom_blender_path.py dance.bvh XBot.fbx /path/to/blender
"""

import sys
from ohao.mogen3d import retarget

if len(sys.argv) < 4:
    print("Usage: python custom_blender_path.py <bvh> <character> <blender_path>")
    sys.exit(1)

bvh_file = sys.argv[1]
char_file = sys.argv[2]
blender_path = sys.argv[3]

output = retarget(bvh_file, char_file, blender_path=blender_path)
print(f"Retargeted using {blender_path}: {output}")
