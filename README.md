<p align="center">
  <img src="https://raw.githubusercontent.com/OhaoTech/ohao-sdk/master/logo.png" alt="ohao" width="80" />
</p>

<h1 align="center">ohao</h1>

<p align="center">
  <strong>Retarget animations onto any humanoid character</strong><br>
  CLI & Python SDK for game developers
</p>

<p align="center">
  <a href="https://github.com/OhaoTech/ohao-sdk/actions"><img src="https://img.shields.io/github/actions/workflow/status/OhaoTech/ohao-sdk/test.yml?style=flat-square" alt="CI"></a>
  <a href="https://pypi.org/project/ohao/"><img src="https://img.shields.io/pypi/v/ohao?style=flat-square&color=blue" alt="PyPI"></a>
  <a href="https://pypi.org/project/ohao/"><img src="https://img.shields.io/pypi/pyversions/ohao?style=flat-square" alt="Python"></a>
  <a href="LICENSE"><img src="https://img.shields.io/github/license/OhaoTech/ohao-sdk?style=flat-square" alt="License"></a>
</p>

---

**ohao** retargets BVH / FBX animations onto your characters — Mixamo, UE5 Mannequin, or any humanoid rig.

## Install

```bash
pip install ohao
```

> Retargeting requires [Blender](https://www.blender.org/download/) (3.6+) installed locally.

## Quick Start

### Python

```python
from ohao.mogen3d import retarget

retarget("dance.bvh", "MyCharacter.fbx")
```

### CLI

```bash
ohao mogen3d retarget dance.bvh MyCharacter.fbx --preset mixamo
```

## Retargeting

The SDK auto-detects your character's rig type and maps bones automatically.

| Rig Type | Detection | Characters |
|----------|-----------|------------|
| **Mixamo** | `Hips` bone (with optional prefix like `mixamorig:`) | X Bot, Y Bot, any Mixamo character |
| **UE5 Mannequin** | `pelvis` bone | Quinn, Manny, Quaternius models |

```python
# Auto-detect (works for most characters)
retarget("dance.bvh", "XBot.fbx")

# Explicit preset
retarget("dance.bvh", "Quinn.gltf", preset="ue5")

# Custom Blender path
retarget("dance.bvh", "MyChar.fbx", blender_path="/path/to/blender")

# Open in Blender GUI to inspect
retarget("dance.bvh", "MyChar.fbx", background=False)
```

### Supported Formats

| Input | Output |
|-------|--------|
| Animation: `.bvh`, `.fbx` | Retargeted `.blend` file |
| Character: `.fbx`, `.glb`, `.gltf` | |

## API Reference

### `retarget()`

```python
retarget(
    bvh_path,            # Path to BVH file
    character_path,      # Path to character (.fbx / .glb / .gltf)
    *,
    output_path=None,    # Output .blend path (default: auto-named)
    preset=None,         # "mixamo", "ue5", or path to JSON
    blender_path=None,   # Blender executable (default: auto-detect)
    background=True,     # Run headless (default: True)
)
```

## Examples

See the [`examples/`](examples/) directory for runnable scripts:

| Example | Description |
|---------|-------------|
| [`basic_retarget.py`](examples/basic_retarget.py) | Minimal one-liner retarget |
| [`batch_retarget.py`](examples/batch_retarget.py) | Apply one BVH to a folder of characters |
| [`retarget_with_preset.py`](examples/retarget_with_preset.py) | Force a specific rig preset |
| [`inspect_in_blender.py`](examples/inspect_in_blender.py) | Open result in Blender GUI |
| [`custom_blender_path.py`](examples/custom_blender_path.py) | Use a specific Blender install |

## Adding a Custom Rig Preset

If your character uses a non-standard skeleton, create a JSON preset:

```json
{
  "name": "My Rig",
  "bone_map": {
    "Hips": "my_pelvis",
    "Spine": "my_spine_01",
    "Head": "my_head",
    "LeftArm": "my_upper_arm_L",
    "LeftForeArm": "my_lower_arm_L",
    "RightArm": "my_upper_arm_R",
    "RightForeArm": "my_lower_arm_R",
    "LeftUpLeg": "my_thigh_L",
    "LeftLeg": "my_shin_L",
    "RightUpLeg": "my_thigh_R",
    "RightLeg": "my_shin_R"
  },
  "root_bone": "Hips"
}
```

Keys on the left are the BVH bone names. Values on the right are your character's bone names. Then pass it:

```python
retarget("dance.bvh", "MyRig.fbx", preset="my_rig.json")
```

```bash
ohao mogen3d retarget dance.bvh MyRig.fbx --preset my_rig.json
```

## License

MIT
