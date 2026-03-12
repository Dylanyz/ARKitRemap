"""Validate the unified _compute_mouth_pair refactor.

Runs arkit_remap on allkeys3, then inspects the output at key frames:
  - Frame 956: closed mouth — JawOpen should be low (~0.15), MouthClose ~0.14
  - Frame 276: should NOT clip — MouthClose should not exceed JawOpen

Also compares against the matched ARKit reference if available.

Usage:
  python .cursor/scripts/run_python_in_unreal.py --file .cursor/arkit-remap/scripts/validate_mouth_pair.py
"""

import unreal
import json
import os
import sys

LIB = unreal.AnimationLibrary
RCT_FLOAT = unreal.RawCurveTrackTypes.RCT_FLOAT
EAL = unreal.EditorAssetLibrary
TAG = "[MouthVal]"

MHA_SOURCE = "/Game/3_FaceAnims/VEC_MHA/AgenticPy/AS_MP_VecDemo1-allkeys3"
ARKIT_OUTPUT = "/Game/3_FaceAnims/VEC_MHA/AgenticPy/AS_MP_VecDemo1-allkeys3_ARKit"
ARKIT_REF = "/Game/3_FaceAnims/VecnaArkitFace/AS_Vec3Baked_v01"

KEY_FRAMES = [276, 500, 700, 956, 1000, 1200]

PROBE_CURVES_ARKIT = [
    "jawOpen", "mouthClose", "mouthPucker", "mouthFunnel",
    "mouthSmileLeft", "mouthSmileRight",
    "mouthFrownLeft", "mouthFrownRight",
    "mouthRollLower", "mouthRollUpper",
    "mouthShrugLower", "mouthShrugUpper",
]

PROBE_CURVES_MHA = [
    "ctrl_expressions_jawopen",
    "ctrl_expressions_mouthlipspurseul",
    "ctrl_expressions_mouthlipspurseur",
    "ctrl_expressions_mouthlipspursedl",
    "ctrl_expressions_mouthlipspursedr",
    "ctrl_expressions_mouthlipstowardsul",
    "ctrl_expressions_mouthlipstowardsur",
    "ctrl_expressions_mouthlipstowardsdl",
    "ctrl_expressions_mouthlipstowardsdr",
]


def _read_value(seq, curve_name, frame_idx):
    for try_name in [curve_name, curve_name.lower()]:
        if LIB.does_curve_exist(seq, try_name, RCT_FLOAT):
            times, values = LIB.get_float_keys(seq, try_name)
            vals = list(values)
            if frame_idx < len(vals):
                return round(vals[frame_idx], 5)
    return None


def _read_all_values(seq, curve_name):
    for try_name in [curve_name, curve_name.lower()]:
        if LIB.does_curve_exist(seq, try_name, RCT_FLOAT):
            _, values = LIB.get_float_keys(seq, try_name)
            return list(values)
    return None


def main():
    unreal.log(f"{TAG} === Mouth Pair Validation ===")

    # -- Step 1: Run the remap on allkeys3 --
    unreal.log(f"{TAG} Running arkit_remap on {MHA_SOURCE}...")

    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
    except NameError:
        script_dir = os.path.join(
            unreal.Paths.project_dir(),
            ".cursor", "arkit-remap", "scripts")

    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)

    # Prevent auto-run, then call main explicitly
    import importlib
    if "arkit_remap" in sys.modules:
        del sys.modules["arkit_remap"]

    old_flag = globals().get("_ARKIT_REMAP_NO_AUTO_RUN")
    import builtins
    builtins._ARKIT_REMAP_NO_AUTO_RUN = True

    # We need to set this in the module's globals, not ours
    arkit_remap_path = os.path.join(script_dir, "arkit_remap.py")
    arkit_ns = {"_ARKIT_REMAP_NO_AUTO_RUN": True, "__file__": arkit_remap_path}
    with open(arkit_remap_path) as f:
        exec(compile(f.read(), arkit_remap_path, "exec"), arkit_ns)

    arkit_ns["main"](asset_paths=[MHA_SOURCE])
    unreal.log(f"{TAG} Remap complete.")

    # -- Step 2: Load remapped output --
    output_seq = unreal.load_asset(ARKIT_OUTPUT)
    if output_seq is None or not isinstance(output_seq, unreal.AnimSequence):
        unreal.log_error(f"{TAG} Cannot load remap output: {ARKIT_OUTPUT}")
        return

    # -- Step 3: Load MHA source for comparison --
    mha_seq = unreal.load_asset(MHA_SOURCE)

    # -- Step 4: Load ARKit reference (optional) --
    ref_seq = unreal.load_asset(ARKIT_REF)
    has_ref = ref_seq is not None and isinstance(ref_seq, unreal.AnimSequence)
    if has_ref:
        unreal.log(f"{TAG} ARKit reference loaded: {ARKIT_REF}")
    else:
        unreal.log_warning(f"{TAG} ARKit reference not available.")

    # -- Step 5: Check key frames --
    results = {"key_frames": [], "global_stats": {}}

    for fi in KEY_FRAMES:
        frame_data = {"frame": fi, "output": {}, "mha": {}, "ref": {}}

        for curve in PROBE_CURVES_ARKIT:
            v = _read_value(output_seq, curve, fi)
            if v is not None:
                frame_data["output"][curve] = v

        if mha_seq:
            for curve in PROBE_CURVES_MHA:
                v = _read_value(mha_seq, curve, fi)
                if v is not None:
                    frame_data["mha"][curve] = v

        if has_ref:
            for curve in PROBE_CURVES_ARKIT:
                v = _read_value(ref_seq, curve, fi)
                if v is not None:
                    frame_data["ref"][curve] = v

        results["key_frames"].append(frame_data)

        jaw = frame_data["output"].get("jawOpen", "N/A")
        mc = frame_data["output"].get("mouthClose", "N/A")
        pk = frame_data["output"].get("mouthPucker", "N/A")
        ref_jaw = frame_data["ref"].get("jawOpen", "N/A")
        ref_mc = frame_data["ref"].get("mouthClose", "N/A")
        unreal.log(f"{TAG} Frame {fi}: jawOpen={jaw}, mouthClose={mc}, "
                   f"pucker={pk}  |  ref: jaw={ref_jaw}, mc={ref_mc}")

    # -- Step 6: Global stats --
    jaw_vals = _read_all_values(output_seq, "jawOpen") or []
    mc_vals = _read_all_values(output_seq, "mouthClose") or []
    pk_vals = _read_all_values(output_seq, "mouthPucker") or []

    if jaw_vals:
        results["global_stats"]["jawOpen"] = {
            "min": round(min(jaw_vals), 5),
            "max": round(max(jaw_vals), 5),
            "mean": round(sum(jaw_vals) / len(jaw_vals), 5),
            "frames": len(jaw_vals),
        }
    if mc_vals:
        results["global_stats"]["mouthClose"] = {
            "min": round(min(mc_vals), 5),
            "max": round(max(mc_vals), 5),
            "mean": round(sum(mc_vals) / len(mc_vals), 5),
        }
    if pk_vals:
        results["global_stats"]["mouthPucker"] = {
            "min": round(min(pk_vals), 5),
            "max": round(max(pk_vals), 5),
            "mean": round(sum(pk_vals) / len(pk_vals), 5),
        }

    # -- Step 7: Clipping check --
    clip_frames = 0
    if jaw_vals and mc_vals:
        n = min(len(jaw_vals), len(mc_vals))
        for i in range(n):
            if mc_vals[i] > jaw_vals[i] + 0.001:
                clip_frames += 1
        results["clipping"] = {
            "frames_where_mouthClose_exceeds_jawOpen": clip_frames,
            "total_frames": n,
            "percentage": round(clip_frames / n * 100, 2) if n > 0 else 0,
        }
        unreal.log(f"{TAG} Clipping: {clip_frames}/{n} frames "
                   f"({results['clipping']['percentage']}%)")

    # -- Step 8: Combined closure check (MouthClose + MouthPucker vs JawOpen) --
    combined_excess = 0
    if jaw_vals and mc_vals and pk_vals:
        n = min(len(jaw_vals), len(mc_vals), len(pk_vals))
        for i in range(n):
            combined = mc_vals[i] + pk_vals[i]
            if combined > jaw_vals[i] + 0.05:
                combined_excess += 1
        results["combined_closure"] = {
            "frames_where_mc_plus_pucker_exceeds_jawOpen": combined_excess,
            "total_frames": n,
            "percentage": round(combined_excess / n * 100, 2) if n > 0 else 0,
        }
        unreal.log(f"{TAG} Combined (MC+Pucker) > JawOpen: "
                   f"{combined_excess}/{n} frames "
                   f"({results['combined_closure']['percentage']}%)")

    # -- Write report --
    out_path = os.path.join(
        unreal.Paths.project_dir(),
        ".cursor", "arkit-remap", "reports",
        "mouth_pair_validation.json",
    )
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)

    unreal.log(f"{TAG} Report: {out_path}")
    unreal.log(f"{TAG} === Validation complete ===")


main()
