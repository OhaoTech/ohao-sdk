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

**ohao** retargets BVH / FBX animations onto your characters them onto your characters — Mixamo, UE5 Mannequin, or any humanoid rig.

## Install

```bash
pip install ohao
```

> Retargeting requires [Blender](https://www.blender.org/download/) (3.6+) installed locally.

## Quick Start

### Python

```python
from ohao.mogen3d import retarget


# 2. Retarget onto your character
retarget(str(bvh_path), "MyCharacter.fbx")
```

### CLI

```bash

# Retarget onto a character
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
| Character: `.fbx`, `.glb`, `.gltf` | Retargeted `.blend` file |

## API Reference

### `MoGen3DClient`

```python
```

| Method | Description |
|--------|-------------|

### `Job`

```python
job = job.wait(timeout=600)       # Block until done
path = job.download(format="bvh") # Download result
```

| Property | Type | Description |
|----------|------|-------------|
| `job.id` | `str` | Job ID |
| `job.status` | `str` | `pending`, `processing`, `completed`, `failed` |
| `job.error` | `str?` | Error message (if failed) |

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

## Environment Variables

| Variable | Description |
|----------|-------------|

## Get an API Key


## License

MIT
