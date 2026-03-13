<p align="center">
  <img src="https://raw.githubusercontent.com/OhaoTech/ohao-sdk/master/logo.png" alt="ohao" width="80" />
</p>

<h1 align="center">ohao</h1>

<p align="center">
  <strong>Process animations and retarget them onto any humanoid character</strong><br>
  CLI & Python SDK for game developers
</p>

<p align="center">
  <a href="https://github.com/OhaoTech/ohao-sdk/actions"><img src="https://img.shields.io/github/actions/workflow/status/OhaoTech/ohao-sdk/test.yml?style=flat-square" alt="CI"></a>
  <a href="https://pypi.org/project/ohao/"><img src="https://img.shields.io/pypi/v/ohao?style=flat-square&color=blue" alt="PyPI"></a>
  <a href="https://pypi.org/project/ohao/"><img src="https://img.shields.io/pypi/pyversions/ohao?style=flat-square" alt="Python"></a>
  <a href="LICENSE"><img src="https://img.shields.io/github/license/OhaoTech/ohao-sdk?style=flat-square" alt="License"></a>
</p>

---

**ohao** is the SDK for [MoGen3D](https://mogen3d.ohao.tech) — process videos into animation files (BVH / FBX) and retarget them onto your characters.

## Install

```bash
pip install ohao
```

> Retargeting requires [Blender](https://www.blender.org/download/) (3.6+) installed locally.

## Quick Start

```bash
# Set your API key once
export OHAO_API_KEY=mg_your_key_here
```

```python
from ohao.mogen3d import MoGen3DClient, retarget

client = MoGen3DClient(api_key="mg_your_key")

# Check sparks balance (each job costs 1 spark)
sparks = client.sparks()
print(f"{sparks.balance} sparks available")

# Claim daily free sparks
if sparks.can_claim:
    client.claim_sparks()

# Process a video → download BVH
job = client.process("dance.mp4", wait=True)
bvh = job.download(format="bvh")

# Retarget onto your character (runs locally via Blender)
retarget(str(bvh), "MyCharacter.fbx")
```

### CLI

```bash
# Check balance & claim daily sparks
ohao mogen3d sparks
ohao mogen3d claim

# Process a video (costs 1 spark)
ohao mogen3d process dance.mp4 --format bvh -o dance.bvh

# Retarget onto a character (free, runs locally)
ohao mogen3d retarget dance.bvh MyCharacter.fbx --preset mixamo

# Account info
ohao mogen3d status
ohao mogen3d bundles
```

## Sparks

Sparks are the credits that power processing jobs. **1 spark = 1 job.** Retargeting is free (runs locally).

| | Free | Pro |
|---|---|---|
| Daily sparks | 1/day | 15/day (accumulates up to 100) |
| Exports | BVH | BVH + FBX |
| Daily job limit | 5 | 50 |

Need more? Purchase spark bundles:

| Bundle | Price |
|--------|-------|
| 30 sparks | $3.99 |
| 100 sparks | $9.99 |
| 1,000 sparks | $59.99 |

```python
# Check available bundles
for bundle in client.bundles():
    print(f"{bundle.label}: {bundle.price}")

# Purchase (opens Stripe checkout)
url = client.purchase_bundle("sparks_100")
```

Sparks are refunded automatically if a job fails.

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
| Video: `.mp4`, `.mov`, `.webm` | `.bvh`, `.fbx` (via cloud processing) |
| Animation: `.bvh`, `.fbx` | Retargeted `.blend` file (local) |
| Character: `.fbx`, `.glb`, `.gltf` | |

## API Reference

### `MoGen3DClient`

```python
client = MoGen3DClient(api_key="mg_...", base_url="https://...")
```

| Method | Description |
|--------|-------------|
| `client.sparks()` | Get sparks balance and claim status |
| `client.claim_sparks()` | Claim daily sparks |
| `client.bundles()` | List purchasable spark bundles |
| `client.purchase_bundle(id)` | Start Stripe checkout for a bundle |
| `client.status()` | Account tier, usage, subscription info |
| `client.process(path, *, wait=False)` | Upload video, start processing (1 spark) |
| `client.list_jobs()` | List all jobs |
| `client.get_job(id)` | Get job by ID |
| `client.download(id, format="bvh")` | Download result file |
| `client.delete_job(id)` | Delete a job |

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

## Environment Variables

| Variable | Description |
|----------|-------------|
| `OHAO_API_KEY` | API key (alternative to `api_key=` param) |
| `OHAO_BASE_URL` | API base URL override |

## Get an API Key

1. Go to [mogen3d.ohao.tech](https://mogen3d.ohao.tech)
2. Sign in and navigate to **Settings > API Keys**
3. Create a new key (starts with `mg_`)

## License

MIT
