"""
Blender retarget script — bundled with the ohao SDK.
Works with Mixamo, UE5, or any supported rig.
Uses rest-pose compensated LOCAL transfer (M @ D @ M^-1 conjugation).

Invoked by ohao.mogen3d.retarget.retarget() — not meant to be run directly.
"""
import bpy
import json
import os
import sys
from pathlib import Path

# ── Parse CLI args ────────────────────────────────────────────────────
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []

bvh_file = None
char_file = None
output_file = None
preset_file = None

i = 0
while i < len(argv):
    if argv[i] == "--bvh" and i + 1 < len(argv):
        bvh_file = argv[i + 1]; i += 2
    elif argv[i] == "--char" and i + 1 < len(argv):
        char_file = argv[i + 1]; i += 2
    elif argv[i] == "--output" and i + 1 < len(argv):
        output_file = argv[i + 1]; i += 2
    elif argv[i] == "--preset-file" and i + 1 < len(argv):
        preset_file = argv[i + 1]; i += 2
    else:
        i += 1

if not bvh_file or not char_file:
    raise RuntimeError("Usage: blender --python _blender_script.py -- --bvh FILE --char FILE [--output FILE]")

print(f"Character: {char_file}")
print(f"BVH: {bvh_file}")

# ── Rig presets: BVH bone name -> target bone name ────────────────────
PRESETS = {
    "mixamo": {
        "Hips": "Hips", "Spine": "Spine", "Spine1": "Spine1", "Spine2": "Spine2",
        "Neck": "Neck", "Head": "Head",
        "LeftShoulder": "LeftShoulder", "LeftArm": "LeftArm",
        "LeftForeArm": "LeftForeArm", "LeftHand": "LeftHand",
        "LeftHandMiddle1": "LeftHandMiddle1",
        "RightShoulder": "RightShoulder", "RightArm": "RightArm",
        "RightForeArm": "RightForeArm", "RightHand": "RightHand",
        "RightHandMiddle1": "RightHandMiddle1",
        "LeftUpLeg": "LeftUpLeg", "LeftLeg": "LeftLeg",
        "LeftFoot": "LeftFoot", "LeftToeBase": "LeftToeBase",
        "RightUpLeg": "RightUpLeg", "RightLeg": "RightLeg",
        "RightFoot": "RightFoot", "RightToeBase": "RightToeBase",
    },
    "ue5": {
        "Hips": "pelvis", "Spine": "spine_01", "Spine1": "spine_02", "Spine2": "spine_03",
        "Neck": "neck_01", "Head": "head",
        "LeftShoulder": "clavicle_l", "LeftArm": "upperarm_l",
        "LeftForeArm": "lowerarm_l", "LeftHand": "hand_l",
        "LeftHandMiddle1": "middle_01_l",
        "RightShoulder": "clavicle_r", "RightArm": "upperarm_r",
        "RightForeArm": "lowerarm_r", "RightHand": "hand_r",
        "RightHandMiddle1": "middle_01_r",
        "LeftUpLeg": "thigh_l", "LeftLeg": "calf_l",
        "LeftFoot": "foot_l", "LeftToeBase": "ball_l",
        "RightUpLeg": "thigh_r", "RightLeg": "calf_r",
        "RightFoot": "foot_r", "RightToeBase": "ball_r",
    },
}

# Load external preset if provided
if preset_file:
    with open(preset_file) as f:
        ext_preset = json.load(f)
    if "bone_map" in ext_preset:
        PRESETS[ext_preset.get("name", "custom")] = ext_preset["bone_map"]

# ── Clean scene ───────────────────────────────────────────────────────
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()
for c in bpy.data.collections:
    bpy.data.collections.remove(c)

# ── Import character ──────────────────────────────────────────────────
ext = Path(char_file).suffix.lower()
if ext == ".fbx":
    bpy.ops.import_scene.fbx(filepath=char_file)
elif ext in (".glb", ".gltf"):
    bpy.ops.import_scene.gltf(filepath=char_file)
else:
    raise RuntimeError(f"Unsupported format: {ext}")

char_arm = None
for obj in bpy.context.scene.objects:
    if obj.type == 'ARMATURE':
        char_arm = obj
        break
if not char_arm:
    raise RuntimeError("No armature found in character file")
if char_arm.animation_data:
    char_arm.animation_data_clear()

bone_names = {b.name for b in char_arm.data.bones}
bone_names_lower = {b.name.lower(): b.name for b in char_arm.data.bones}
print(f"Character: {char_arm.name}, {len(bone_names)} bones")

# ── Auto-detect rig type ──────────────────────────────────────────────
def detect_rig(bone_names, bone_names_lower):
    # UE5 (distinctive names)
    if "pelvis" in bone_names or "pelvis" in bone_names_lower:
        print("Detected rig: UE5 Mannequin")
        preset = PRESETS["ue5"]
        bmap = {}
        for smpl_name, tgt_name in preset.items():
            if tgt_name in bone_names:
                bmap[smpl_name] = tgt_name
            elif tgt_name.lower() in bone_names_lower:
                bmap[smpl_name] = bone_names_lower[tgt_name.lower()]
        return "ue5", bmap

    # Mixamo (with optional prefix like "mixamorig:")
    prefix = ""
    for bone_name in bone_names:
        if "Hips" in bone_name:
            prefix = bone_name.replace("Hips", "")
            break
    if prefix or "Hips" in bone_names:
        print(f"Detected rig: Mixamo (prefix: '{prefix}')")
        preset = PRESETS["mixamo"]
        bmap = {}
        for smpl_name, tgt_name in preset.items():
            full_name = prefix + tgt_name
            if full_name in bone_names:
                bmap[smpl_name] = full_name
        return "mixamo", bmap

    # Fallback: case-insensitive Mixamo
    print("Detected rig: Unknown -- trying case-insensitive Mixamo match")
    preset = PRESETS["mixamo"]
    bmap = {}
    for smpl_name, tgt_name in preset.items():
        if tgt_name.lower() in bone_names_lower:
            bmap[smpl_name] = bone_names_lower[tgt_name.lower()]
    return "unknown", bmap

# ── Import BVH ────────────────────────────────────────────────────────
bpy.ops.import_anim.bvh(filepath=bvh_file, global_scale=0.01, frame_start=1, use_fps_scale=True)
bvh_arm = None
for obj in bpy.context.scene.objects:
    if obj.type == 'ARMATURE' and obj != char_arm:
        bvh_arm = obj
        break
if not bvh_arm:
    raise RuntimeError("No BVH armature found")
print(f"BVH: {bvh_arm.name}, {len(bvh_arm.data.bones)} bones")

# ── Build bone map ────────────────────────────────────────────────────
rig_type, bone_map = detect_rig(bone_names, bone_names_lower)

# Filter to bones that exist in both
final_map = {}
for bvh_name, char_name in bone_map.items():
    if bvh_name in bvh_arm.data.bones and char_name in char_arm.data.bones:
        final_map[bvh_name] = char_name
bone_map = final_map

print(f"Mapped {len(bone_map)} bones:")
for src, tgt in sorted(bone_map.items()):
    print(f"  {src} -> {tgt}")

if len(bone_map) < 10:
    print("WARNING: Less than 10 bones mapped -- retarget may look incomplete")

# ── Axis mapping M per bone ──────────────────────────────────────────
axis_maps = {}
for bvh_name, char_name in bone_map.items():
    R_bvh = (bvh_arm.matrix_world @ bvh_arm.data.bones[bvh_name].matrix_local).to_quaternion()
    R_char = (char_arm.matrix_world @ char_arm.data.bones[char_name].matrix_local).to_quaternion()
    axis_maps[bvh_name] = R_char.inverted() @ R_bvh

# ── Height ratio ─────────────────────────────────────────────────────
hips_char = bone_map.get("Hips")
head_char = bone_map.get("Head")
if hips_char and head_char:
    bvh_hips_rest = (bvh_arm.matrix_world @ bvh_arm.data.bones["Hips"].matrix_local).to_translation()
    bvh_head_rest = (bvh_arm.matrix_world @ bvh_arm.data.bones["Head"].matrix_local).to_translation()
    char_hips_rest = (char_arm.matrix_world @ char_arm.data.bones[hips_char].matrix_local).to_translation()
    char_head_rest = (char_arm.matrix_world @ char_arm.data.bones[head_char].matrix_local).to_translation()
    bvh_h = (bvh_head_rest - bvh_hips_rest).length
    char_h = (char_head_rest - char_hips_rest).length
    height_ratio = char_h / bvh_h if bvh_h > 0.001 else 1.0
else:
    height_ratio = 1.0

bvh_hips_rest = (bvh_arm.matrix_world @ bvh_arm.data.bones["Hips"].matrix_local).to_translation()
print(f"Height ratio: {height_ratio:.3f}")

# ── Frame range ──────────────────────────────────────────────────────
action = bvh_arm.animation_data.action
frame_start = int(action.frame_range[0])
frame_end = int(action.frame_range[1])
num_frames = frame_end - frame_start + 1
print(f"Frames: {frame_start}-{frame_end} ({num_frames})")

# ── Set bones to quaternion rotation mode ─────────────────────────────
bpy.context.view_layer.objects.active = char_arm
bpy.ops.object.mode_set(mode='POSE')
for char_name in bone_map.values():
    char_arm.pose.bones[char_name].rotation_mode = 'QUATERNION'
bpy.ops.object.mode_set(mode='OBJECT')

# ── Retarget: M @ D @ M^-1 ──────────────────────────────────────────
print("Retargeting...")
for frame in range(frame_start, frame_end + 1):
    bpy.context.scene.frame_set(frame)

    for bvh_name, char_name in bone_map.items():
        src = bvh_arm.pose.bones[bvh_name]
        tgt = char_arm.pose.bones[char_name]
        M = axis_maps[bvh_name]
        M_inv = M.inverted()

        D_bvh = src.matrix_basis.to_quaternion()
        D_char = M @ D_bvh @ M_inv

        tgt.rotation_quaternion = D_char
        tgt.keyframe_insert(data_path="rotation_quaternion", frame=frame)

        if bvh_name == "Hips":
            bvh_hips_world = (bvh_arm.matrix_world @ src.matrix).to_translation()
            world_delta = bvh_hips_world - bvh_hips_rest
            scaled_delta = world_delta * height_ratio
            R_char_rest_mat = (char_arm.matrix_world @ tgt.bone.matrix_local).to_3x3()
            local_delta = R_char_rest_mat.inverted() @ scaled_delta
            tgt.location = local_delta
            tgt.keyframe_insert(data_path="location", frame=frame)

    if frame % 30 == 0:
        print(f"  Frame {frame}/{frame_end}")

print("Retarget complete!")

# ── Cleanup ──────────────────────────────────────────────────────────
bpy.context.scene.frame_start = frame_start
bpy.context.scene.frame_end = frame_end
bpy.context.scene.frame_set(frame_start)

# Move BVH armature aside for visibility
bvh_arm.location.x = 2.0

# Hide leaf/end bones
for bone in char_arm.data.bones:
    n = bone.name.lower()
    if n.endswith("_end") or "leaf" in n or n.endswith("4"):
        bone.hide = True

char_arm.data.display_type = 'WIRE'
bpy.ops.object.select_all(action='DESELECT')
char_arm.select_set(True)
bpy.context.view_layer.objects.active = char_arm

# ── Save .blend file ─────────────────────────────────────────────────
if output_file:
    out = Path(output_file)
    out.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(out))
    print(f"Saved: {out}")

print(f"\nDone! {num_frames} frames on {Path(char_file).stem}.")
