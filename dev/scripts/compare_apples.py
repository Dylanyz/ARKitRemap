"""Apples-to-Apples Comparison Report

Reads three ctrl_expressions AnimSequences on the MetaHuman face and produces:
  - Per-curve differences (A vs B, A vs C, B vs C)
  - Aggregate MSE per family (jaw, mouth, brow, eye, cheek, nose, tongue)
  - Diagnostics at user-requested key frames

A = MHA ground truth (OnMH)
B = Our remap round-trip (allkeys_ARKit_OnMH)
C = Real iPhone ARKit forward-passed (Vec-ARKITBAKED-excerpt_OnMH)

Run inside Unreal via:
    py exec(open(unreal.Paths.project_dir() + ".cursor/arkit-remap/scripts/compare_apples.py").read())
"""

import unreal
import json
import os
import math
from datetime import datetime, timezone

RCT_FLOAT = unreal.RawCurveTrackTypes.RCT_FLOAT
LIB = unreal.AnimationLibrary
TAG = "[Apples Compare]"

APPLES = "/Game/3_FaceAnims/VEC_MHA/AgenticPy/apples"
SEQ_A = f"{APPLES}/AS_MP_VecDemo1-OnMH"
SEQ_B = f"{APPLES}/AS_MP_VecDemo1-allkeys_ARKit_OnMH"
SEQ_C = f"{APPLES}/Vec-ARKITBAKED-T34_60fps-02_OnMH"

KEY_FRAMES = [0, 276, 362, 725, 956, 1087]

CURVE_FAMILIES = {
    "jaw":    ["jawopen", "jawfwd", "jawleft", "jawright", "jawchin"],
    "mouth":  ["mouth", "lips"],
    "brow":   ["brow"],
    "eye":    ["eye"],
    "cheek":  ["cheek"],
    "nose":   ["nose", "wrinkle"],
    "tongue": ["tongue"],
}


def _classify_family(curve_name):
    lower = curve_name.lower()
    for family, prefixes in CURVE_FAMILIES.items():
        for prefix in prefixes:
            if prefix in lower:
                return family
    return "other"


def _load_seq(path):
    asset = unreal.load_asset(path)
    if asset is None or not isinstance(asset, unreal.AnimSequence):
        unreal.log_error(f"{TAG} Could not load AnimSequence: {path}")
        return None
    return asset


def _read_ctrl_curves(seq):
    """Read all ctrl_expressions curves from a sequence.

    Returns dict: lowercase_name -> values_list
    Since UE Python doesn't enumerate curve names, we probe a known set
    built from the payload.
    """
    project_dir = unreal.Paths.project_dir()
    payload_path = os.path.join(
        project_dir, ".cursor", "arkit-remap",
        "mapping-pose-asset", "data",
        "AM_ArKitRemap_v02.mapping_payload.json",
    )
    with open(payload_path, "r") as f:
        payload = json.load(f)

    ctrl_names = set()
    for entry in payload["arkit52"]:
        for c in entry["contributors"]:
            ctrl_names.add(c["source"].lower())
    for suffix in ["dl", "dr", "ul", "ur"]:
        ctrl_names.add(f"ctrl_expressions_mouthlipstogether{suffix}")

    curves = {}
    for name in sorted(ctrl_names):
        if LIB.does_curve_exist(seq, name, RCT_FLOAT):
            times, values = LIB.get_float_keys(seq, name)
            curves[name] = (list(times), list(values))

    return curves


def _compute_mse(vals_a, vals_b, n):
    """Mean squared error over min(n, len) frames."""
    total = 0.0
    count = min(n, len(vals_a), len(vals_b))
    if count == 0:
        return 0.0
    for i in range(count):
        diff = vals_a[i] - vals_b[i]
        total += diff * diff
    return total / count


def _compute_max_abs_diff(vals_a, vals_b, n):
    count = min(n, len(vals_a), len(vals_b))
    if count == 0:
        return 0.0
    return max(abs(vals_a[i] - vals_b[i]) for i in range(count))


def _frame_snapshot(curves, frame_idx):
    """Get values of all curves at a specific frame index."""
    snap = {}
    for name, (times, values) in curves.items():
        if frame_idx < len(values):
            snap[name] = values[frame_idx]
        else:
            snap[name] = None
    return snap


def main():
    unreal.log(f"{TAG} === Apples-to-Apples Comparison ===")

    seq_a = _load_seq(SEQ_A)
    seq_b = _load_seq(SEQ_B)
    seq_c = _load_seq(SEQ_C)
    if not all([seq_a, seq_b, seq_c]):
        return

    unreal.log(f"{TAG} Reading curves from A (MHA ground truth)...")
    curves_a = _read_ctrl_curves(seq_a)
    unreal.log(f"{TAG} Reading curves from B (remap round-trip)...")
    curves_b = _read_ctrl_curves(seq_b)
    unreal.log(f"{TAG} Reading curves from C (real iPhone ARKit)...")
    curves_c = _read_ctrl_curves(seq_c)

    unreal.log(f"{TAG} Curves found: A={len(curves_a)}, B={len(curves_b)}, C={len(curves_c)}")

    all_names = sorted(set(curves_a.keys()) | set(curves_b.keys()) | set(curves_c.keys()))
    n_a = max((len(v) for _, v in curves_a.values()), default=0)
    n_b = max((len(v) for _, v in curves_b.values()), default=0)
    n_c = max((len(v) for _, v in curves_c.values()), default=0)
    n_common = min(n_a, n_b, n_c)
    unreal.log(f"{TAG} Frame counts: A={n_a}, B={n_b}, C={n_c}, common={n_common}")

    # Per-curve MSE
    per_curve = {}
    for name in all_names:
        entry = {"family": _classify_family(name)}
        if name in curves_a and name in curves_b:
            va, vb = curves_a[name][1], curves_b[name][1]
            entry["mse_ab"] = _compute_mse(va, vb, n_common)
            entry["max_ab"] = _compute_max_abs_diff(va, vb, n_common)
        if name in curves_a and name in curves_c:
            va, vc = curves_a[name][1], curves_c[name][1]
            entry["mse_ac"] = _compute_mse(va, vc, n_common)
            entry["max_ac"] = _compute_max_abs_diff(va, vc, n_common)
        if name in curves_b and name in curves_c:
            vb, vc = curves_b[name][1], curves_c[name][1]
            entry["mse_bc"] = _compute_mse(vb, vc, n_common)
            entry["max_bc"] = _compute_max_abs_diff(vb, vc, n_common)
        per_curve[name] = entry

    # Per-family aggregate MSE
    family_mse = {}
    for name, entry in per_curve.items():
        fam = entry["family"]
        if fam not in family_mse:
            family_mse[fam] = {"ab": [], "ac": [], "bc": []}
        if "mse_ab" in entry:
            family_mse[fam]["ab"].append(entry["mse_ab"])
        if "mse_ac" in entry:
            family_mse[fam]["ac"].append(entry["mse_ac"])
        if "mse_bc" in entry:
            family_mse[fam]["bc"].append(entry["mse_bc"])

    family_summary = {}
    for fam, data in family_mse.items():
        family_summary[fam] = {}
        for pair in ["ab", "ac", "bc"]:
            vals = data[pair]
            if vals:
                family_summary[fam][pair] = {
                    "mean_mse": sum(vals) / len(vals),
                    "max_mse": max(vals),
                    "n_curves": len(vals),
                }

    # Key-frame snapshots
    key_frame_data = {}
    for fidx in KEY_FRAMES:
        if fidx >= n_common:
            continue
        snap_a = _frame_snapshot(curves_a, fidx)
        snap_b = _frame_snapshot(curves_b, fidx)
        snap_c = _frame_snapshot(curves_c, fidx)

        frame_diffs = {}
        for name in all_names:
            va = snap_a.get(name)
            vb = snap_b.get(name)
            vc = snap_c.get(name)
            if va is not None and vb is not None and vc is not None:
                frame_diffs[name] = {
                    "A": round(va, 6),
                    "B": round(vb, 6),
                    "C": round(vc, 6),
                    "diff_AB": round(abs(va - vb), 6),
                    "diff_AC": round(abs(va - vc), 6),
                    "diff_BC": round(abs(vb - vc), 6),
                }
        key_frame_data[fidx] = frame_diffs

    # Write JSON report
    project_dir = unreal.Paths.project_dir()
    reports_dir = os.path.join(
        project_dir, ".cursor", "arkit-remap", "reports"
    )
    os.makedirs(reports_dir, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%S")

    json_path = os.path.join(reports_dir, f"apples_comparison_{ts}.json")
    json_data = {
        "timestamp": ts,
        "sequences": {"A": SEQ_A, "B": SEQ_B, "C": SEQ_C},
        "frame_counts": {"A": n_a, "B": n_b, "C": n_c, "common": n_common},
        "per_curve": {
            name: {k: round(v, 8) if isinstance(v, float) else v
                   for k, v in entry.items()}
            for name, entry in per_curve.items()
        },
        "family_summary": {
            fam: {pair: {k: round(v, 8) if isinstance(v, float) else v
                         for k, v in data.items()}
                  for pair, data in pairs.items()}
            for fam, pairs in family_summary.items()
        },
        "key_frames": {str(k): v for k, v in key_frame_data.items()},
    }
    with open(json_path, "w") as f:
        json.dump(json_data, f, indent=2)

    # Write markdown report
    md_path = os.path.join(reports_dir, f"apples_comparison_{ts}.md")
    lines = [
        "# Apples-to-Apples Comparison Report",
        "",
        f"**Generated:** {ts}  ",
        f"**A:** `{SEQ_A}` (MHA ground truth, {n_a} frames)  ",
        f"**B:** `{SEQ_B}` (remap round-trip, {n_b} frames)  ",
        f"**C:** `{SEQ_C}` (real iPhone ARKit, {n_c} frames)  ",
        f"**Common frames for comparison:** {n_common}  ",
        "",
        "## Family-Level MSE Summary",
        "",
        "| Family | A vs B (mean MSE) | A vs C (mean MSE) | B vs C (mean MSE) | # Curves |",
        "|--------|-------------------|--------------------|--------------------|----------|",
    ]

    for fam in ["jaw", "mouth", "brow", "eye", "cheek", "nose", "tongue", "other"]:
        if fam not in family_summary:
            continue
        fs = family_summary[fam]
        ab = fs.get("ab", {})
        ac = fs.get("ac", {})
        bc = fs.get("bc", {})
        n = ab.get("n_curves", ac.get("n_curves", bc.get("n_curves", 0)))
        lines.append(
            f"| {fam} | "
            f"{ab.get('mean_mse', 0):.6f} | "
            f"{ac.get('mean_mse', 0):.6f} | "
            f"{bc.get('mean_mse', 0):.6f} | "
            f"{n} |"
        )
    lines.append("")

    # Top 20 worst round-trip curves (A vs B)
    lines.append("## Top 20 Round-Trip Error Curves (A vs B)")
    lines.append("")
    lines.append("| Curve | MSE | Max Diff | Family |")
    lines.append("|-------|-----|----------|--------|")
    sorted_ab = sorted(
        [(n, e) for n, e in per_curve.items() if "mse_ab" in e],
        key=lambda x: x[1]["mse_ab"], reverse=True
    )[:20]
    for name, entry in sorted_ab:
        lines.append(
            f"| {name} | {entry['mse_ab']:.6f} | "
            f"{entry.get('max_ab', 0):.4f} | {entry['family']} |"
        )
    lines.append("")

    # Top 20 worst A vs C curves
    lines.append("## Top 20 MHA vs iPhone ARKit Curves (A vs C)")
    lines.append("")
    lines.append("| Curve | MSE | Max Diff | Family |")
    lines.append("|-------|-----|----------|--------|")
    sorted_ac = sorted(
        [(n, e) for n, e in per_curve.items() if "mse_ac" in e],
        key=lambda x: x[1]["mse_ac"], reverse=True
    )[:20]
    for name, entry in sorted_ac:
        lines.append(
            f"| {name} | {entry['mse_ac']:.6f} | "
            f"{entry.get('max_ac', 0):.4f} | {entry['family']} |"
        )
    lines.append("")

    # Key-frame diagnostics
    for fidx in KEY_FRAMES:
        if fidx >= n_common:
            continue
        lines.append(f"## Frame {fidx}")
        lines.append("")
        lines.append("| Curve | A | B | C | |A-B| | |A-C| | |B-C| |")
        lines.append("|-------|---|---|---|-------|-------|-------|")
        diffs = key_frame_data.get(fidx, {})
        sorted_diffs = sorted(
            diffs.items(),
            key=lambda x: max(x[1]["diff_AB"], x[1]["diff_AC"]),
            reverse=True,
        )[:30]
        for name, d in sorted_diffs:
            lines.append(
                f"| {name} | {d['A']:.4f} | {d['B']:.4f} | {d['C']:.4f} | "
                f"{d['diff_AB']:.4f} | {d['diff_AC']:.4f} | {d['diff_BC']:.4f} |"
            )
        lines.append("")

    with open(md_path, "w") as f:
        f.write("\n".join(lines))

    unreal.log(f"{TAG} JSON report: {json_path}")
    unreal.log(f"{TAG} Markdown report: {md_path}")
    unreal.log(f"{TAG} === Comparison complete ===")


main()
