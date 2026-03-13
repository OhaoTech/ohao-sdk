"""
Basic retargeting — BVH onto a Mixamo character.

Usage:
    pip install ohao
    python basic_retarget.py dance.bvh XBot.fbx
"""

import sys
from ohao.mogen3d import retarget

if len(sys.argv) < 3:
    print("Usage: python basic_retarget.py <bvh_file> <character_file>")
    sys.exit(1)

bvh_file = sys.argv[1]
char_file = sys.argv[2]

output = retarget(bvh_file, char_file)
print(f"Retargeted animation saved to: {output}")
