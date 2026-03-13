"""
Retarget and open in Blender GUI for visual inspection.

Usage:
    pip install ohao
    python inspect_in_blender.py dance.bvh XBot.fbx
"""

import sys
from ohao.mogen3d import retarget

if len(sys.argv) < 3:
    print("Usage: python inspect_in_blender.py <bvh_file> <character_file>")
    sys.exit(1)

bvh_file = sys.argv[1]
char_file = sys.argv[2]

# background=False opens Blender with the retargeted result
output = retarget(bvh_file, char_file, background=False)
print(f"Saved to: {output}")
