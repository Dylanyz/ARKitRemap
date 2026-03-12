"""Probe mouth-related curves at a specific frame."""

import unreal
import json
import os
from datetime import datetime, timezone

LIB = unreal.AnimationLibrary
RCT_FLOAT = unreal.RawCurveTrackTypes.RCT_FLOAT
TAG = "[MouthProbe]"

FRAME_INDICES = [1142, 1177]  # 0-based for display frames 1143, 1178

ORIGINAL_PATH = "/Game/3_FaceAnims/VEC_MHA/AgenticPy/AS_MP_VecDemo1-allkeys"
ARKIT_PATH    = "/Game/3_FaceAnims/VEC_MHA/AgenticPy/AS_MP_VecDemo1-allkeys_ARKit"
ROUNDTRIP_PATH = "/Game/3_FaceAnims/VEC_MHA/AgenticPy/apples/AS_MP_VecDemo1-allkeys_ARKit_OnMH"

ARKIT_MOUTH_CURVES = [
    "jawOpen", "jawForward", "jawLeft", "jawRight",
    "mouthClose", "mouthFunnel", "mouthPucker",
    "mouthLeft", "mouthRight",
    "mouthSmileLeft", "mouthSmileRight",
    "mouthFrownLeft", "mouthFrownRight",
    "mouthDimpleLeft", "mouthDimpleRight",
    "mouthStretchLeft", "mouthStretchRight",
    "mouthRollLower", "mouthRollUpper",
    "mouthShrugLower", "mouthShrugUpper",
    "mouthPressLeft", "mouthPressRight",
    "mouthLowerDownLeft", "mouthLowerDownRight",
    "mouthUpperUpLeft", "mouthUpperUpRight",
    "cheekPuff", "cheekSquintLeft", "cheekSquintRight",
    "noseSneerLeft", "noseSneerRight",
]

MHA_MOUTH_CURVES = [
    "ctrl_expressions_mouthlipspurseul", "ctrl_expressions_mouthlipspurseur",
    "ctrl_expressions_mouthlipspursedl", "ctrl_expressions_mouthlipspursedr",
    "ctrl_expressions_mouthlipstowardsul", "ctrl_expressions_mouthlipstowardsur",
    "ctrl_expressions_mouthlipstowardsdl", "ctrl_expressions_mouthlipstowardsdr",
    "ctrl_expressions_mouth_lips_together_ul", "ctrl_expressions_mouth_lips_together_ur",
    "ctrl_expressions_mouth_lips_together_dl", "ctrl_expressions_mouth_lips_together_dr",
    "ctrl_expressions_mouthfunnelul", "ctrl_expressions_mouthfunnelur",
    "ctrl_expressions_mouthfunneldl", "ctrl_expressions_mouthfunneldr",
    "ctrl_expressions_mouthpuckerul", "ctrl_expressions_mouthpuckerur",
    "ctrl_expressions_mouthpuckerdl", "ctrl_expressions_mouthpuckerdr",
    "ctrl_expressions_mouthpressul", "ctrl_expressions_mouthpressur",
    "ctrl_expressions_mouthpressdl", "ctrl_expressions_mouthpressdr",
    "ctrl_expressions_mouthlowerlipdepressdl", "ctrl_expressions_mouthlowerlipdepressdr",
    "ctrl_expressions_mouthupperlipraiseul", "ctrl_expressions_mouthupperlipraiseur",
    "ctrl_expressions_mouthcornerpulll", "ctrl_expressions_mouthcornerpullr",
    "ctrl_expressions_mouthcornerdepressdl", "ctrl_expressions_mouthcornerdepressdr",
    "ctrl_expressions_mouthstretchl", "ctrl_expressions_mouthstretchr",
    "ctrl_expressions_mouthdimplel", "ctrl_expressions_mouthdimpler",
    "ctrl_expressions_mouthrolll", "ctrl_expressions_mouthrollr",
    "ctrl_expressions_mouthshrugl", "ctrl_expressions_mouthshrugr",
    "ctrl_expressions_jawopen", "ctrl_expressions_jawforward",
    "ctrl_expressions_jawleft", "ctrl_expressions_jawright",
    "ctrl_expressions_mouthopen",
    "ctrl_expressions_mouthsmilel", "ctrl_expressions_mouthsmiler",
    "ctrl_expressions_mouthfrowndl", "ctrl_expressions_mouthfrowndr",
    "ctrl_expressions_mouthleft", "ctrl_expressions_mouthright",
    "ctrl_expressions_nosesneerl", "ctrl_expressions_nosesneerr",
    "ctrl_expressions_cheekpuffl", "ctrl_expressions_cheekpuffr",
    "ctrl_expressions_cheeksquintl", "ctrl_expressions_cheeksquintr",
    "ctrl_expressions_mouthup",
]


def _read_curve_at_frame(seq, curve_name, frame_idx):
    if not LIB.does_curve_exist(seq, curve_name, RCT_FLOAT):
        return None
    times, values = LIB.get_float_keys(seq, curve_name)
    if frame_idx < len(values):
        return float(values[frame_idx])
    return None


def _probe_sequence(seq, label, frame_idx, curve_names):
    results = {}
    for name in curve_names:
        val = _read_curve_at_frame(seq, name, frame_idx)
        if val is not None:
            results[name] = round(val, 6)
    return results


def main():
    report = {"frames": {}}

    for fi in FRAME_INDICES:
        fd = fi + 1
        unreal.log(f"{TAG} === Probing frame {fd} (index {fi}) ===")

        frame_report = {}

        seq_configs = [
            ("A_original", ORIGINAL_PATH, MHA_MOUTH_CURVES),
            ("arkit_remap", ARKIT_PATH, ARKIT_MOUTH_CURVES),
        ]

        for label, path, curves in seq_configs:
            seq = unreal.load_asset(path)
            if seq is None:
                frame_report[label] = {"error": f"not found: {path}"}
                continue

            times_ref, vals_ref = None, None
            for c in curves:
                if LIB.does_curve_exist(seq, c, RCT_FLOAT):
                    times_ref, vals_ref = LIB.get_float_keys(seq, c)
                    break
            nframes = len(vals_ref) if vals_ref is not None else 0

            if fi >= nframes:
                frame_report[label] = {"error": f"frame {fd} > {nframes}"}
                continue

            data = _probe_sequence(seq, label, fi, curves)
            frame_report[label] = {"path": path, "curves": data}

            for name in sorted(data.keys()):
                val = data[name]
                if abs(val) > 0.005:
                    unreal.log(f"{TAG}   [{fd}] {label}: {name} = {val:.4f}")

        report["frames"][str(fd)] = frame_report

    # ── Save ────────────────────────────────────────────────────────────────
    project_dir = unreal.Paths.project_dir()
    report_dir = os.path.join(project_dir, ".cursor", "arkit-remap", "reports")
    os.makedirs(report_dir, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%S")
    frames_str = "_".join(str(fi + 1) for fi in FRAME_INDICES)
    report_path = os.path.join(report_dir, f"mouth_probe_frames_{frames_str}_{ts}.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    unreal.log(f"{TAG} Report: {report_path}")


main()
