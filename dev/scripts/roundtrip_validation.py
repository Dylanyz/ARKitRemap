"""Round-trip validation framework for ARKit remap pipeline.

Verifies correctness of the reverse weighted synthesis by:
  1. Defining known ARKit activations (ground truth)
  2. Forward-synthesizing MHA curves using payload weights
  3. Reverse-solving back to ARKit using the current production solver
     (independent, paired, and grouped solves from the payload)
  4. Comparing recovered values to ground truth

No Unreal dependency — pure Python + json + math.

Usage:
    python roundtrip_validation.py [path/to/payload.json]
"""

import json
import math
import os
import sys
from collections import defaultdict
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Payload loading
# ---------------------------------------------------------------------------

_DEV_PAYLOAD_REL = os.path.join(
    "..", "mapping-pose-asset", "data",
    "AM_ArKitRemap_v02.mapping_payload.json",
)


def load_payload(path=None):
    """Locate and load the mapping payload JSON."""
    if path and os.path.isfile(path):
        pass
    elif path is None:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        candidates = [
            os.path.join(script_dir, "arkit_remap_payload.json"),
            os.path.join(script_dir, _DEV_PAYLOAD_REL),
        ]
        for c in candidates:
            c = os.path.normpath(c)
            if os.path.isfile(c):
                path = c
                break
    if path is None or not os.path.isfile(path):
        print(f"ERROR: Payload not found. Provide path as first argument.")
        sys.exit(1)
    with open(path, "r") as f:
        return json.load(f), os.path.abspath(path)


# ---------------------------------------------------------------------------
# Build forward + reverse models
# ---------------------------------------------------------------------------

def build_models(payload):
    """Build index structures from the payload's arkit52 entries.

    Returns:
        targets:      {arkit_name: {contributors, sumWeightSquared}}
        forward_map:  {mha_source_lower: [(arkit_name, weight), ...]}
        target_names: ordered list of target names
    """
    targets = {}
    forward_map = defaultdict(list)
    target_names = []
    min_weight = payload.get("calibrationDefaults", {}).get("minWeight", 0.0)

    for entry in payload["arkit52"]:
        name = entry["target"]
        target_names.append(name)
        contribs = entry["contributors"]
        if min_weight > 0:
            contribs = [c for c in contribs if abs(c["weight"]) >= min_weight]
        sw2 = sum(c["weight"] ** 2 for c in contribs)
        targets[name] = {
            "contributors": contribs,
            "sumWeightSquared": sw2,
        }
        for c in contribs:
            forward_map[c["source"].lower()].append((name, c["weight"]))

    return targets, dict(forward_map), target_names


# ---------------------------------------------------------------------------
# Forward pass  (ARKit activations → MHA curves)
# ---------------------------------------------------------------------------

def forward_pass(arkit_activations, forward_map):
    """Simulate Epic's PoseAsset: mha[s] = Σ(arkit[t] × w) over all targets
    that list s as a contributor."""
    mha = {}
    for mha_source, tw_list in forward_map.items():
        total = 0.0
        for arkit_name, weight in tw_list:
            total += arkit_activations.get(arkit_name, 0.0) * weight
        mha[mha_source] = total
    return mha


# ---------------------------------------------------------------------------
# Reverse pass  (MHA curves → ARKit activations)
# ---------------------------------------------------------------------------

def reverse_pass_independent(mha_values, targets):
    """Independent least-squares inverse: arkit[t] = Σ(mha[s]×w) / Σ(w²)."""
    recovered = {}
    for arkit_name, tdata in targets.items():
        sw2 = tdata["sumWeightSquared"]
        if sw2 == 0:
            continue
        num = 0.0
        for c in tdata["contributors"]:
            num += mha_values.get(c["source"].lower(), 0.0) * c["weight"]
        recovered[arkit_name] = num / sw2
    return recovered


def _invert_matrix(matrix):
    """Invert a small dense matrix with Gauss-Jordan elimination."""
    n = len(matrix)
    if n == 0 or any(len(row) != n for row in matrix):
        return None

    aug = []
    for i, row in enumerate(matrix):
        aug.append([float(v) for v in row] + [
            1.0 if i == j else 0.0 for j in range(n)
        ])

    for col in range(n):
        pivot_row = max(range(col, n), key=lambda r: abs(aug[r][col]))
        pivot = aug[pivot_row][col]
        if abs(pivot) < 1e-12:
            return None
        if pivot_row != col:
            aug[col], aug[pivot_row] = aug[pivot_row], aug[col]

        pivot = aug[col][col]
        inv_pivot = 1.0 / pivot
        for j in range(2 * n):
            aug[col][j] *= inv_pivot

        for row in range(n):
            if row == col:
                continue
            factor = aug[row][col]
            if abs(factor) < 1e-12:
                continue
            for j in range(2 * n):
                aug[row][j] -= factor * aug[col][j]

    return [row[n:] for row in aug]


def _solve_group(mha_values, group_names, targets):
    """Solve a coupled target group jointly via NxN least-squares."""
    weight_map = {}
    for idx, name in enumerate(group_names):
        tdata = targets.get(name)
        if tdata is None:
            return None
        for c in tdata["contributors"]:
            key = c["source"].lower()
            if key not in weight_map:
                weight_map[key] = [0.0] * len(group_names)
            weight_map[key][idx] = c["weight"]

    active = [
        (src, weights) for src, weights in weight_map.items()
        if src in mha_values
    ]
    if not active:
        return None

    gram = []
    for i in range(len(group_names)):
        row = []
        for j in range(len(group_names)):
            row.append(sum(weights[i] * weights[j] for _, weights in active))
        gram.append(row)

    gram_inv = _invert_matrix(gram)
    if gram_inv is None:
        return None

    rhs = [0.0] * len(group_names)
    for src, weights in active:
        obs = mha_values[src]
        for i, weight in enumerate(weights):
            rhs[i] += obs * weight

    solved = {}
    for i, name in enumerate(group_names):
        value = sum(gram_inv[i][j] * rhs[j] for j in range(len(group_names)))
        solved[name] = max(0.0, value)
    return solved


def reverse_pass(mha_values, targets, coupled_pairs=None, coupled_groups=None):
    """Production reverse solve: grouped targets first, then independent."""
    recovered = {}
    solved_targets = set()
    solve_groups = [list(group) for group in (coupled_groups or []) if len(group) >= 2]
    solve_groups.extend([list(pair) for pair in (coupled_pairs or []) if len(pair) == 2])

    for group_names in solve_groups:
        if len(set(group_names)) != len(group_names):
            continue
        if any(name in solved_targets for name in group_names):
            continue
        solved = _solve_group(mha_values, group_names, targets)
        if solved is None:
            continue
        recovered.update(solved)
        solved_targets.update(group_names)

    for arkit_name, value in reverse_pass_independent(mha_values, targets).items():
        if arkit_name not in recovered:
            recovered[arkit_name] = value

    return recovered


def reverse_pass_clamped(mha_values, targets, coupled_pairs=None, coupled_groups=None,
                         lo=0.0, hi=1.0):
    """Reverse pass with [0, 1] clamp (matches production calibration)."""
    raw = reverse_pass(
        mha_values, targets, coupled_pairs=coupled_pairs,
        coupled_groups=coupled_groups
    )
    return {k: max(lo, min(hi, v)) for k, v in raw.items()}


# ---------------------------------------------------------------------------
# Error metrics
# ---------------------------------------------------------------------------

def compute_metrics(gt_frames, rec_frames, target_names):
    """Per-target error metrics across all frames.

    Returns {target: {max_abs_error, mae, rmse, frames_over_005,
                      frames_over_005_pct, n_frames}}.
    """
    n = len(gt_frames)
    out = {}
    for name in target_names:
        errs = []
        for i in range(n):
            errs.append(rec_frames[i].get(name, 0.0) - gt_frames[i].get(name, 0.0))
        ae = [abs(e) for e in errs]
        mx = max(ae) if ae else 0.0
        mae = sum(ae) / n if n else 0.0
        rmse = math.sqrt(sum(e * e for e in errs) / n) if n else 0.0
        over = sum(1 for e in ae if e > 0.05)
        out[name] = {
            "max_abs_error": round(mx, 9),
            "mae":           round(mae, 9),
            "rmse":          round(rmse, 9),
            "frames_over_005":     over,
            "frames_over_005_pct": round(100.0 * over / n, 2) if n else 0.0,
            "n_frames": n,
        }
    return out


# ---------------------------------------------------------------------------
# Test scenario generators
# ---------------------------------------------------------------------------

def _zero_frame(target_names):
    return {t: 0.0 for t in target_names}


def gen_isolation(target_names, n_ramp=30):
    """One target active at a time, ramp 0->1 over n_ramp frames.
    Total frames = len(target_names) * n_ramp."""
    frames = []
    for name in target_names:
        for i in range(n_ramp):
            f = _zero_frame(target_names)
            f[name] = i / (n_ramp - 1)
            frames.append(f)
    return frames


def gen_pair(target_names, t1, v1, t2, v2, n_frames=30):
    """Two targets held at constant activations for n_frames."""
    frames = []
    for _ in range(n_frames):
        f = _zero_frame(target_names)
        f[t1] = v1
        f[t2] = v2
        frames.append(f)
    return frames


def gen_speech_combo(target_names, n_frames=60):
    """JawOpen ramp 0->0.7, MouthSmileLeft oscillating around 0.3,
    MouthPucker oscillating 0->0.4.  Mimics simple speech."""
    frames = []
    for i in range(n_frames):
        t = i / max(n_frames - 1, 1)
        f = _zero_frame(target_names)
        f["JawOpen"] = t * 0.7
        f["MouthSmileLeft"] = 0.3 + 0.2 * math.sin(2 * math.pi * t * 2)
        f["MouthPucker"] = 0.4 * abs(math.sin(2 * math.pi * t * 3))
        frames.append(f)
    return frames


def gen_full_activation(target_names, level=0.5, n_frames=30):
    """All targets simultaneously at `level`."""
    f = {t: level for t in target_names}
    return [dict(f) for _ in range(n_frames)]


# ---------------------------------------------------------------------------
# Run one scenario
# ---------------------------------------------------------------------------

def run_scenario(label, gt_frames, forward_map, targets, target_names,
                 coupled_pairs=None, coupled_groups=None):
    rec_raw = []
    rec_clamp = []
    for frame in gt_frames:
        mha = forward_pass(frame, forward_map)
        rec_raw.append(reverse_pass(
            mha, targets, coupled_pairs=coupled_pairs,
            coupled_groups=coupled_groups
        ))
        rec_clamp.append(reverse_pass_clamped(
            mha, targets, coupled_pairs=coupled_pairs,
            coupled_groups=coupled_groups
        ))
    return {
        "label": label,
        "n_frames": len(gt_frames),
        "metrics_raw": compute_metrics(gt_frames, rec_raw, target_names),
        "metrics_clamped": compute_metrics(gt_frames, rec_clamp, target_names),
    }


# ---------------------------------------------------------------------------
# Shared-curve analysis
# ---------------------------------------------------------------------------

def find_shared_curves(targets):
    """Map each MHA source to all ARKit targets that use it.
    Returns only sources shared by 2+ targets."""
    src_map = defaultdict(list)
    for arkit_name, tdata in targets.items():
        for c in tdata["contributors"]:
            src_map[c["source"].lower()].append((arkit_name, c["weight"]))
    return {s: tw for s, tw in src_map.items() if len(tw) > 1}


# ---------------------------------------------------------------------------
# Pretty-print helpers
# ---------------------------------------------------------------------------

_SEP = "=" * 88


def _pct(n, d):
    return f"{100*n/d:.1f}%" if d else "0%"


def print_shared_report(shared):
    print(f"\n{_SEP}")
    print("  SHARED SOURCE CURVES  (cross-contamination vectors)")
    print(_SEP)
    if not shared:
        print("  None — every source curve is exclusive to one target.\n")
        return
    for src in sorted(shared):
        targets_str = ", ".join(f"{t} (w={w:.4f})" for t, w in shared[src])
        print(f"  {src}")
        print(f"    -> {targets_str}")
    print()


def print_scenario(result, verbose=False):
    label = result["label"]
    nf = result["n_frames"]
    mr = result["metrics_raw"]
    mc = result["metrics_clamped"]

    print(f"\n{_SEP}")
    print(f"  SCENARIO: {label}   ({nf} frames)")
    print(_SEP)

    perfect, imperfect = [], []
    for t in sorted(mr):
        (perfect if mr[t]["max_abs_error"] < 1e-9 else imperfect).append(t)

    if perfect and not verbose:
        names = perfect
        if len(names) > 10:
            names = names[:5] + ["..."] + names[-3:]
        print(f"\n  Perfect round-trip ({len(perfect)} targets): {', '.join(names)}")

    show = sorted(mr) if verbose else imperfect
    if show:
        hdr = (f"  {'Target':<28}{'MaxAbs':>10}{'MAE':>10}{'RMSE':>10}"
               f"{'|e|>.05':>14}{'Clamp MaxAbs':>14}")
        print(f"\n{hdr}")
        print(f"  {'-'*28}{'-'*10}{'-'*10}{'-'*10}{'-'*14}{'-'*14}")
        for t in show:
            m = mr[t]
            cm = mc[t]
            ov = f"{m['frames_over_005']}/{nf} ({_pct(m['frames_over_005'], nf)})"
            print(f"  {t:<28}{m['max_abs_error']:>10.6f}{m['mae']:>10.6f}"
                  f"{m['rmse']:>10.6f}{ov:>14}{cm['max_abs_error']:>14.6f}")
    elif not verbose:
        print(f"\n  ALL {len(perfect)} targets round-trip perfectly (max |e| < 1e-9).")
    print()


def print_aggregate(results):
    print(f"\n{_SEP}")
    print("  AGGREGATE SUMMARY")
    print(_SEP)
    hdr = f"  {'Scenario':<48}{'MaxErr':>10}{'AvgMAE':>10}{'Perfect':>8}{'Dirty':>8}{'Grade':>7}"
    print(hdr)
    print(f"  {'-'*48}{'-'*10}{'-'*10}{'-'*8}{'-'*8}{'-'*7}")
    for r in results:
        mr = r["metrics_raw"]
        mx = max(m["max_abs_error"] for m in mr.values())
        avg_mae = sum(m["mae"] for m in mr.values()) / len(mr) if mr else 0
        perfect = sum(1 for m in mr.values() if m["max_abs_error"] < 1e-9)
        dirty = len(mr) - perfect
        grade = "PASS" if mx < 0.001 else ("WARN" if mx < 0.05 else "FAIL")
        print(f"  {r['label']:<48}{mx:>10.6f}{avg_mae:>10.6f}"
              f"{perfect:>8}{dirty:>8}  [{grade}]")
    print()


# ---------------------------------------------------------------------------
# Cross-contamination detail for isolation test
# ---------------------------------------------------------------------------

def isolation_crosstalk_detail(targets, forward_map, target_names, top_n=10,
                               coupled_pairs=None, coupled_groups=None):
    """For each target activated alone at 1.0, find the worst ghost
    activations on other targets.  Returns a sorted list of
    (active, ghost_target, ghost_value) triples."""
    ghosts = []
    for active in target_names:
        frame = _zero_frame(target_names)
        frame[active] = 1.0
        mha = forward_pass(frame, forward_map)
        rec = reverse_pass(
            mha, targets, coupled_pairs=coupled_pairs,
            coupled_groups=coupled_groups
        )
        for other in target_names:
            if other == active:
                continue
            val = rec.get(other, 0.0)
            if abs(val) > 1e-9:
                ghosts.append((active, other, val))
    ghosts.sort(key=lambda x: abs(x[2]), reverse=True)
    return ghosts[:top_n] if top_n else ghosts


def print_crosstalk(ghosts):
    print(f"\n{_SEP}")
    print("  ISOLATION CROSS-TALK  (worst ghost activations when one target = 1.0)")
    print(_SEP)
    if not ghosts:
        print("  None detected.\n")
        return
    print(f"  {'Active Target':<28}{'Ghost Target':<28}{'Ghost Value':>12}")
    print(f"  {'-'*28}{'-'*28}{'-'*12}")
    for active, ghost, val in ghosts:
        print(f"  {active:<28}{ghost:<28}{val:>12.6f}")
    print()


# ---------------------------------------------------------------------------
# JSON report
# ---------------------------------------------------------------------------

def build_json_report(payload_path, payload, target_names, shared, results, ghosts):
    return {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "payload_path": payload_path,
        "payload_version": payload.get("payloadVersion", "?"),
        "n_targets": len(target_names),
        "target_names": target_names,
        "shared_curves": {
            s: [{"target": t, "weight": w} for t, w in tw]
            for s, tw in shared.items()
        },
        "top_isolation_ghosts": [
            {"active": a, "ghost": g, "value": round(v, 9)}
            for a, g, v in ghosts
        ],
        "scenarios": [
            {
                "name": r["label"],
                "n_frames": r["n_frames"],
                "metrics_raw": r["metrics_raw"],
                "metrics_clamped": r["metrics_clamped"],
            }
            for r in results
        ],
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    path = sys.argv[1] if len(sys.argv) > 1 else None
    payload, payload_path = load_payload(path)
    coupled_pairs = payload.get("coupledPairs", [])
    coupled_groups = payload.get("coupledGroups", [])

    print(f"\nPayload : {payload_path}")
    print(f"Version : {payload.get('payloadVersion', '?')}")
    print(f"minWeight: {payload.get('calibrationDefaults', {}).get('minWeight', 0.0)}")

    targets, fwd_map, names = build_models(payload)
    print(f"Targets : {len(names)}")
    print(f"MHA srcs: {len(fwd_map)}")
    if coupled_pairs:
        print(f"Pairs   : {coupled_pairs}")
    if coupled_groups:
        print(f"Groups  : {coupled_groups}")

    shared = find_shared_curves(targets)
    print_shared_report(shared)

    # -- scenarios ----------------------------------------------------------

    scenarios = [
        ("Isolation (ramp 0->1, each target solo)",
         gen_isolation(names, 30)),

        ("Pair: MouthPucker=0.5 + MouthFunnel=0.3",
         gen_pair(names, "MouthPucker", 0.5, "MouthFunnel", 0.3)),

        ("Pair: MouthRollLower=0.7 + MouthRollUpper=0.4",
         gen_pair(names, "MouthRollLower", 0.7, "MouthRollUpper", 0.4)),

        ("Pair: BrowInnerUp=0.6 + BrowOuterUpLeft=0.8",
         gen_pair(names, "BrowInnerUp", 0.6, "BrowOuterUpLeft", 0.8)),

        ("Group: BrowInnerUp=0.6 + BrowOuterUpLeft=0.8 + BrowOuterUpRight=0.4",
         [dict(_zero_frame(names), BrowInnerUp=0.6,
               BrowOuterUpLeft=0.8, BrowOuterUpRight=0.4) for _ in range(30)]),

        ("Speech combo (JawOpen + SmileL + Pucker)",
         gen_speech_combo(names, 60)),

        ("Full activation (all @ 0.5)",
         gen_full_activation(names, 0.5, 30)),
    ]

    results = []
    for label, frames in scenarios:
        r = run_scenario(
            label, frames, fwd_map, targets, names,
            coupled_pairs=coupled_pairs, coupled_groups=coupled_groups
        )
        results.append(r)
        print_scenario(r)

    print_aggregate(results)

    ghosts = isolation_crosstalk_detail(
        targets, fwd_map, names, top_n=20,
        coupled_pairs=coupled_pairs, coupled_groups=coupled_groups
    )
    print_crosstalk(ghosts)

    # -- JSON report --------------------------------------------------------

    report = build_json_report(payload_path, payload, names, shared, results, ghosts)
    report_dir = os.path.normpath(os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "reports",
    ))
    os.makedirs(report_dir, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%S")
    report_path = os.path.join(report_dir, f"roundtrip_validation_{ts}.json")
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"JSON report: {report_path}\n")


if __name__ == "__main__":
    main()
