"""Probe frame count, fps, and duration of key sequences for alignment."""
import unreal
import json
import os

LIB = unreal.AnimationLibrary
TAG = "[FrameProbe]"

SEQS = [
    "/Game/3_FaceAnims/VecnaArkitFace/Vec-ARKITBAKED-T34_60fps-02",
    "/Game/3_FaceAnims/VEC_MHA/AS_EL01-v01_VEC",
    "/Game/3_FaceAnims/VEC_MHA/AgenticPy/AS_MP_VecDemo1-allkeys",
    "/Game/3_FaceAnims/VEC_MHA/AgenticPy/AS_MP_VecDemo1-allkeys3",
]

results = {}
for path in SEQS:
    asset = unreal.load_asset(path)
    if asset is None or not isinstance(asset, unreal.AnimSequence):
        unreal.log_warning(f"{TAG} Cannot load: {path}")
        continue

    n_frames = LIB.get_num_frames(asset)
    length = asset.get_editor_property("sequence_length")
    try:
        rate = asset.get_editor_property("sampling_frame_rate")
        fps_num = rate.numerator
        fps_den = rate.denominator
        fps = fps_num / fps_den if fps_den else 0
    except Exception:
        fps = n_frames / length if length > 0 else 0
        fps_num, fps_den = int(round(fps)), 1

    jaw_data = None
    for curve_name in ["jawOpen", "ctrl_expressions_jawopen"]:
        if LIB.does_curve_exist(asset, curve_name, unreal.RawCurveTrackTypes.RCT_FLOAT):
            times, vals = LIB.get_float_keys(asset, curve_name)
            jaw_data = {
                "curve": curve_name,
                "key_count": len(times),
                "first_time": round(float(times[0]), 6) if times else None,
                "last_time": round(float(times[-1]), 6) if times else None,
            }
            break

    info = {
        "number_of_frames": n_frames,
        "sequence_length_s": round(float(length), 6),
        "sampling_fps": f"{fps_num}/{fps_den} = {fps:.4f}",
        "fps_float": round(fps, 4),
        "jaw_curve": jaw_data,
    }
    results[path] = info
    unreal.log(f"{TAG} {path.split('/')[-1]}: {n_frames} frames, "
               f"{length:.3f}s, {fps:.2f}fps")

# Compute alignment
arkit_path = "/Game/3_FaceAnims/VecnaArkitFace/Vec-ARKITBAKED-T34_60fps-02"
if arkit_path in results:
    arkit_fps = results[arkit_path]["fps_float"]
    offset_time = 20724.0 / arkit_fps if arkit_fps > 0 else 0
    results["alignment"] = {
        "arkit_frame_at_mha_frame0": 20724,
        "arkit_fps": arkit_fps,
        "offset_seconds": round(offset_time, 6),
        "note": "ARKit time at frame 20724 = MHA frame 0 time"
    }
    unreal.log(f"{TAG} Alignment: frame 20724 @ {arkit_fps}fps = {offset_time:.4f}s")

out = os.path.join(unreal.Paths.project_dir(),
                   ".cursor", "arkit-remap", "reports",
                   "frame_alignment_probe.json")
os.makedirs(os.path.dirname(out), exist_ok=True)
with open(out, "w") as f:
    json.dump(results, f, indent=2)
unreal.log(f"{TAG} Report: {out}")
