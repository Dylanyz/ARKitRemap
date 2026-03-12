"""Diagnostic: dump mouth-related curve values at a specific frame across sequences.

Compares MHA source curves, remapped ARKit curves, and real ARKit reference
to understand why the mouth doesn't close properly after remap.

Usage (via remote execution):
  python .cursor/scripts/run_python_in_unreal.py --file .cursor/arkit-remap/scripts/diagnose_mouth_close.py
"""

import unreal
import json
import os

LIB = unreal.AnimationLibrary
RCT_FLOAT = unreal.RawCurveTrackTypes.RCT_FLOAT
TAG = "[MouthDiag]"

TARGET_FRAME = 956

SEQUENCES = {
    "mha_source_creature": "/Game/3_FaceAnims/VEC_MHA/AgenticPy/AS_MP_VecDemo1-allkeys",
    "remapped_arkit": "/Game/3_FaceAnims/VEC_MHA/AgenticPy/AS_MP_VecDemo1-allkeys1_ARKit",
    "mha_source_metahuman": "/Game/3_FaceAnims/VEC_MHA/AS_MP_VecDemo1-elevenmode",
    "real_arkit_reference": "/Game/3_FaceAnims/VecnaArkitFace/AS_Vec3Baked_v01",
}

ARKIT_MOUTH_CURVES = [
    "JawOpen", "JawForward", "JawLeft", "JawRight",
    "MouthClose", "MouthFunnel", "MouthPucker",
    "MouthLeft", "MouthRight",
    "MouthSmileLeft", "MouthSmileRight",
    "MouthFrownLeft", "MouthFrownRight",
    "MouthDimpleLeft", "MouthDimpleRight",
    "MouthStretchLeft", "MouthStretchRight",
    "MouthRollLower", "MouthRollUpper",
    "MouthShrugLower", "MouthShrugUpper",
    "MouthPressLeft", "MouthPressRight",
    "MouthLowerDownLeft", "MouthLowerDownRight",
    "MouthUpperUpLeft", "MouthUpperUpRight",
    "mouthClose", "jawOpen",
]

MHA_MOUTH_CURVES = [
    "ctrl_expressions_jawopen",
    "ctrl_expressions_jawfwd",
    "ctrl_expressions_jawleft",
    "ctrl_expressions_jawright",
    "ctrl_expressions_jawchinraisedl",
    "ctrl_expressions_jawchinraisedr",
    "ctrl_expressions_jawchinraiseul",
    "ctrl_expressions_jawchinraiseur",
    "ctrl_expressions_mouthlipstowardsul",
    "ctrl_expressions_mouthlipstowardsur",
    "ctrl_expressions_mouthlipstowardsdl",
    "ctrl_expressions_mouthlipstowardsdr",
    "ctrl_expressions_mouthlipspurseul",
    "ctrl_expressions_mouthlipspurseur",
    "ctrl_expressions_mouthlipspursedl",
    "ctrl_expressions_mouthlipspursedr",
    "ctrl_expressions_mouthfunnelul",
    "ctrl_expressions_mouthfunnelur",
    "ctrl_expressions_mouthfunneldl",
    "ctrl_expressions_mouthfunneldr",
    "ctrl_expressions_mouthcornerpulll",
    "ctrl_expressions_mouthcornerpullr",
    "ctrl_expressions_mouthcornerdepressl",
    "ctrl_expressions_mouthcornerdepressr",
    "ctrl_expressions_mouthstretchl",
    "ctrl_expressions_mouthstretchr",
    "ctrl_expressions_mouthlowerlipdepressl",
    "ctrl_expressions_mouthlowerlipdepressr",
    "ctrl_expressions_mouthupperlipraisel",
    "ctrl_expressions_mouthupperlipraiser",
    "ctrl_expressions_mouthlowerliprollinl",
    "ctrl_expressions_mouthlowerliprollinr",
    "ctrl_expressions_mouthupperliprollinl",
    "ctrl_expressions_mouthupperliprollinr",
    "ctrl_expressions_mouthpressdl",
    "ctrl_expressions_mouthpressdr",
    "ctrl_expressions_mouthpressul",
    "ctrl_expressions_mouthpressur",
    "ctrl_expressions_mouthdimplel",
    "ctrl_expressions_mouthdimpler",
    "ctrl_expressions_mouthleft",
    "ctrl_expressions_mouthright",
    "ctrl_expressions_mouthcheekblowl",
    "ctrl_expressions_mouthcheekblowr",
    "ctrl_expressions_mouthlipspurseul",
    "ctrl_expressions_mouthlipsblowr",
    "ctrl_expressions_mouthlipsblowl",
]

ALL_PROBE_CURVES = sorted(set(
    [c.lower() for c in ARKIT_MOUTH_CURVES] +
    [c.lower() for c in MHA_MOUTH_CURVES]
))


def get_value_at_frame(seq, curve_name, frame_idx):
    if not LIB.does_curve_exist(seq, curve_name, RCT_FLOAT):
        return None
    times, values = LIB.get_float_keys(seq, curve_name)
    times = list(times)
    values = list(values)
    if frame_idx < len(values):
        return {"value": round(values[frame_idx], 6), "time": round(times[frame_idx], 4)}
    return {"value": None, "frame_out_of_range": True, "total_frames": len(values)}


def get_all_curve_names(seq):
    """Get all curve names from a sequence by probing a wide set."""
    found = []
    for curve_name in ALL_PROBE_CURVES:
        if LIB.does_curve_exist(seq, curve_name, RCT_FLOAT):
            found.append(curve_name)
    return found


def scan_sequence(seq, label, frame_idx):
    result = {"label": label, "frame": frame_idx, "curves": {}}

    for curve_name in ALL_PROBE_CURVES:
        data = get_value_at_frame(seq, curve_name, frame_idx)
        if data is not None:
            result["curves"][curve_name] = data

    return result


def main():
    unreal.log(f"{TAG} === Mouth Close Diagnostic ===")
    unreal.log(f"{TAG} Target frame: {TARGET_FRAME}")

    report = {"target_frame": TARGET_FRAME, "sequences": {}}

    for key, path in SEQUENCES.items():
        seq = unreal.load_asset(path)
        if seq is None:
            unreal.log_warning(f"{TAG} Could not load: {path}")
            report["sequences"][key] = {"error": f"Could not load {path}"}
            continue

        if not isinstance(seq, unreal.AnimSequence):
            unreal.log_warning(f"{TAG} Not an AnimSequence: {path} ({type(seq).__name__})")
            report["sequences"][key] = {"error": f"Not AnimSequence: {type(seq).__name__}"}
            continue

        unreal.log(f"{TAG} Scanning: {key} -> {path}")
        data = scan_sequence(seq, key, TARGET_FRAME)
        report["sequences"][key] = data
        unreal.log(f"{TAG}   Found {len(data['curves'])} curves with data at frame {TARGET_FRAME}")

    # Also scan a few frames around 956 for context (955, 956, 957, 958)
    context_frames = [954, 955, 956, 957, 958, 959, 960]
    report["context_frames"] = {}
    key_curves_arkit = ["jawopen", "mouthclose", "mouthfunnel", "mouthpucker",
                        "mouthlowerdownleft", "mouthlowerdownright",
                        "mouthupperupleft", "mouthupperupright",
                        "mouthshruglower", "mouthshrugupper",
                        "mouthrolllower", "mouthrollupper",
                        "mouthpressleft", "mouthpressright"]
    key_curves_mha = ["ctrl_expressions_jawopen",
                      "ctrl_expressions_mouthlipstowardsul",
                      "ctrl_expressions_mouthlipstowardsur",
                      "ctrl_expressions_mouthlipstowardsdl",
                      "ctrl_expressions_mouthlipstowardsdr",
                      "ctrl_expressions_mouthlowerlipdepressl",
                      "ctrl_expressions_mouthlowerlipdepressr",
                      "ctrl_expressions_mouthupperlipraisel",
                      "ctrl_expressions_mouthupperlipraiser"]

    for seq_key in ["mha_source_creature", "remapped_arkit", "real_arkit_reference"]:
        path = SEQUENCES[seq_key]
        seq = unreal.load_asset(path)
        if seq is None or not isinstance(seq, unreal.AnimSequence):
            continue

        probe_curves = key_curves_arkit if seq_key != "mha_source_creature" else key_curves_mha
        report["context_frames"][seq_key] = {}

        for frame_idx in context_frames:
            frame_data = {}
            for curve_name in probe_curves:
                data = get_value_at_frame(seq, curve_name, frame_idx)
                if data is not None and data.get("value") is not None:
                    frame_data[curve_name] = data["value"]
            report["context_frames"][seq_key][str(frame_idx)] = frame_data

    out_path = os.path.join(
        unreal.Paths.project_dir(),
        ".cursor", "arkit-remap", "reports",
        "mouth_close_diagnostic_frame956.json"
    )
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(report, f, indent=2)

    unreal.log(f"{TAG} Report written to: {out_path}")

    # Print summary to log
    for key, data in report["sequences"].items():
        if "error" in data:
            unreal.log(f"{TAG} {key}: {data['error']}")
            continue
        curves = data.get("curves", {})
        jaw = curves.get("jawopen", curves.get("ctrl_expressions_jawopen", {}))
        mc = curves.get("mouthclose", {})
        unreal.log(f"{TAG} {key}: jawopen={jaw.get('value', 'N/A')}, "
                   f"mouthclose={mc.get('value', 'N/A')}, "
                   f"total_curves={len(curves)}")

    unreal.log(f"{TAG} === Diagnostic complete ===")


main()
