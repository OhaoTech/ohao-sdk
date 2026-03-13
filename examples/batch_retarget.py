"""
Batch retargeting — apply one BVH to multiple characters.

Usage:
    pip install ohao
    python batch_retarget.py dance.bvh characters/
"""

import sys
from pathlib import Path
from ohao.mogen3d import retarget

if len(sys.argv) < 3:
    print("Usage: python batch_retarget.py <bvh_file> <characters_dir>")
    sys.exit(1)

bvh_file = sys.argv[1]
char_dir = Path(sys.argv[2])
output_dir = Path("retargeted")
output_dir.mkdir(exist_ok=True)

extensions = {".fbx", ".glb", ".gltf"}
characters = [f for f in char_dir.iterdir() if f.suffix.lower() in extensions]

print(f"Found {len(characters)} characters in {char_dir}")

for char in characters:
    out = output_dir / f"{Path(bvh_file).stem}_{char.stem}.blend"
    print(f"  {char.name}...", end=" ", flush=True)
    try:
        retarget(bvh_file, str(char), output_path=str(out))
        print("done")
    except Exception as e:
        print(f"FAILED: {e}")

print(f"\nResults saved to {output_dir}/")
