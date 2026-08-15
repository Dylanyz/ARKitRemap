"""ARKit Remap v2 - Python Pipeline

Reads the precomputed mapping payload, processes selected animation sequences
by computing weighted ARKit curves from MHA source curves using least-squares
normalization (sum of weight^2), handles MouthClose explicitly, applies
calibration, and writes results to duplicated sequences.

Usage:
  Select AnimSequence(s) in Content Browser, then in UE Output Log:
    py exec(open(unreal.Paths.project_dir() + ".cursor/arkit-remap/scripts/arkit_remap.py").read())
  Or if bootstrapper is set up:
    py import arkit_remap
"""

import unreal
import json
import os
import csv
import sys
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Verified API references (from probe_ue_api.py results)
# ---------------------------------------------------------------------------
# unreal.AnimationLibrary            (NOT AnimationBlueprintLibrary)
# .does_curve_exist(seq, name, RCT_FLOAT)           -> bool
# .get_float_keys(seq, name)                         -> (times_array, values_array)
# .add_curve(seq, name, RCT_FLOAT, False)
# .add_float_curve_keys(seq, name, times, values)
# .remove_curve(seq, name, False)                    (no enum; bool = remove_from_skeleton)
# EditorAssetLibrary.duplicate_asset(src, dst)       -> asset or None if dst exists
# EditorAssetLibrary.save_asset(path)
# EditorUtilityLibrary.get_selected_assets()         -> Array of asset objects

RCT_FLOAT = unreal.RawCurveTrackTypes.RCT_FLOAT
LIB = unreal.AnimationLibrary
EAL = unreal.EditorAssetLibrary
TAG = "[ARKit Remap]"


# ---------------------------------------------------------------------------
# Payload loading
# ---------------------------------------------------------------------------

def _find_payload():
    """Locate the mapping payload JSON using a two-step search path."""
    # 1. Next to the script (distribution / release mode)
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
    except NameError:
        script_dir = None
    if script_dir:
        local = os.path.join(script_dir, "arkit_remap_payload.json")
        if os.path.isfile(local):
            return local

    # 2. .cursor workspace (development mode)
    project_dir = unreal.Paths.project_dir()
    dev = os.path.join(
        project_dir, ".cursor", "arkit-remap",
        "mapping-pose-asset", "data",
        "AM_ArKitRemap_v02.mapping_payload.json",
    )
    if os.path.isfile(dev):
        return dev

    return None


def _load_payload():
    path = _find_payload()
    if path is None:
        unreal.log_error(
            f"{TAG} Payload not found. Searched:\n"
            f"  1. <script_dir>/arkit_remap_payload.json\n"
            f"  2. <project>/.cursor/arkit-remap/mapping-pose-asset/data/"
            f"AM_ArKitRemap_v02.mapping_payload.json"
        )
        return None, None
    unreal.log(f"{TAG} Payload: {path}")
    with open(path, "r") as f:
        return json.load(f), path


# ---------------------------------------------------------------------------
# Build lookup structures from payload (once)
# ---------------------------------------------------------------------------

def _build_target_index(payload):
    """Pre-compute per-target lookup with sumWeightSquared.

    Applies minWeight filtering: contributors with |weight| below the
    threshold are excluded to remove data artifacts (e.g. browlaterall at
    0.031 polluting 10+ unrelated targets).
    """
    cal = payload.get("calibrationDefaults", {})
    min_weight = cal.get("minWeight", 0.0)
    targets = {}
    all_source_curves = set()
    filtered_count = 0

    for entry in payload["arkit52"]:
        name = entry["target"]
        contributors = entry["contributors"]
        if min_weight > 0:
            before = len(contributors)
            contributors = [c for c in contributors if abs(c["weight"]) >= min_weight]
            filtered_count += before - len(contributors)
        sw2 = sum(c["weight"] ** 2 for c in contributors)
        targets[name] = {
            "contributors": contributors,
            "sumWeightSquared": sw2,
        }
        for c in contributors:
            all_source_curves.add(c["source"].lower())

    if filtered_count > 0:
        unreal.log(
            f"{TAG} minWeight filter ({min_weight}): removed {filtered_count} "
            f"sub-threshold contributors across all targets."
        )

    mc = cal.get("mouthClose", {})
    for curve in mc.get("lipsTowardsSourceCurves", []):
        all_source_curves.add(curve.lower())
    for curve in mc.get("lipsPurseSourceCurves", []):
        all_source_curves.add(curve.lower())
    legacy_curve = mc.get("lipsTogetherSourceCurve", "")
    if legacy_curve:
        all_source_curves.add(legacy_curve.lower())

    return targets, all_source_curves


# ---------------------------------------------------------------------------
# Selection helpers
# ---------------------------------------------------------------------------

def _get_selected_sequences():
    selected = unreal.EditorUtilityLibrary.get_selected_assets()
    seqs = [a for a in selected if isinstance(a, unreal.AnimSequence)]
    if not seqs:
        unreal.log_error(
            f"{TAG} No AnimSequence selected in Content Browser. "
            f"Select one or more, then re-run."
        )
    return seqs


def _asset_path(asset):
    """Package path without the .ObjectName suffix."""
    return asset.get_path_name().rsplit(".", 1)[0]


def _asset_name(asset_path):
    return asset_path.rsplit("/", 1)[-1]


# ---------------------------------------------------------------------------
# Duplicate / reuse
# ---------------------------------------------------------------------------

def _prepare_duplicate(source_path, known_arkit_names):
    """Create an _ARKit duplicate, or reuse + clear if it already exists."""
    src_name = source_path.rsplit("/", 1)[-1]

    if src_name.endswith("_ARKit"):
        unreal.log_warning(
            f"{TAG} Source '{src_name}' already ends with _ARKit. Skipping to "
            f"avoid double-suffix."
        )
        return None, None

    folder = source_path.rsplit("/", 1)[0]
    dup_path = f"{folder}/{src_name}_ARKit"

    if EAL.does_asset_exist(dup_path):
        unreal.log(f"{TAG} Duplicate exists, clearing old ARKit curves: {dup_path}")
        dup_seq = unreal.load_asset(dup_path)
        if dup_seq is None:
            unreal.log_error(f"{TAG} Could not load existing duplicate: {dup_path}")
            return None, None

        controller = None
        try:
            controller = dup_seq.controller
            controller.open_bracket(unreal.Text("ARKit Remap Clear"))
        except Exception:
            controller = None

        cleared = 0
        for arkit_name in known_arkit_names:
            if LIB.does_curve_exist(dup_seq, arkit_name, RCT_FLOAT):
                LIB.remove_curve(dup_seq, arkit_name, False)
                cleared += 1

        if controller is not None:
            try:
                controller.close_bracket()
            except Exception:
                pass

        unreal.log(f"{TAG} Cleared {cleared} existing ARKit curves.")
    else:
        dup_asset = EAL.duplicate_asset(source_path, dup_path)
        if dup_asset is None:
            unreal.log_error(f"{TAG} Failed to duplicate: {source_path} -> {dup_path}")
            return None, None
        dup_seq = dup_asset
        unreal.log(f"{TAG} Created duplicate: {dup_path}")

    return dup_seq, dup_path


# ---------------------------------------------------------------------------
# Read source curves
# ---------------------------------------------------------------------------

def _read_source_curves(source_seq, required_curves_lower):
    """Read all needed MHA curves from the source sequence.

    Returns dict: lowercase_name -> (times_list, values_list)
    """
    cache = {}
    missing = []

    for curve_lower in sorted(required_curves_lower):
        if not LIB.does_curve_exist(source_seq, curve_lower, RCT_FLOAT):
            missing.append(curve_lower)
            continue
        times, values = LIB.get_float_keys(source_seq, curve_lower)
        cache[curve_lower] = (list(times), list(values))

    if missing:
        unreal.log_warning(
            f"{TAG} {len(missing)} source curves not found on sequence "
            f"(first 10): {missing[:10]}"
        )

    return cache, missing


# ---------------------------------------------------------------------------
# Validate key counts
# ---------------------------------------------------------------------------

def _validate_key_counts(source_cache):
    """Check all source curves share the same frame count.

    Returns (canonical_times, frame_count) or pads shorter curves.
    """
    if not source_cache:
        return [], 0

    counts = {name: len(vals) for name, (_, vals) in source_cache.items()}
    unique = set(counts.values())

    if len(unique) == 1:
        any_name = next(iter(source_cache))
        return list(source_cache[any_name][0]), next(iter(unique))

    unreal.log_warning(
        f"{TAG} Non-uniform key counts detected ({len(unique)} distinct). "
        f"Padding shorter curves."
    )
    max_count = max(unique)
    canonical_times = None
    for name, (t, v) in source_cache.items():
        if len(v) == max_count:
            canonical_times = list(t)
            break

    for name in list(source_cache.keys()):
        t, v = source_cache[name]
        if len(v) < max_count:
            pad_val = v[-1] if v else 0.0
            v.extend([pad_val] * (max_count - len(v)))
            t.extend([canonical_times[i] for i in range(len(t), max_count)])
            source_cache[name] = (t, v)

    return canonical_times, max_count


# ---------------------------------------------------------------------------
# Calibration helpers
# ---------------------------------------------------------------------------

def _clamp(val, lo, hi):
    return max(lo, min(hi, val))


def _apply_calibration(values, cal):
    scale = cal.get("scale", 1.0)
    offset = cal.get("offset", 0.0)
    lo = cal.get("clampMin", 0.0)
    hi = cal.get("clampMax", 1.0)
    return [_clamp(v * scale + offset, lo, hi) for v in values]


# ---------------------------------------------------------------------------
# Coupled/grouped solve helpers
# ---------------------------------------------------------------------------

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


def _solve_group_targets(target_names, target_index, source_cache, frame_count):
    """Solve a coupled target group jointly via NxN least-squares."""
    if len(target_names) < 2:
        return None

    target_data = []
    for name in target_names:
        tdata = target_index.get(name)
        if tdata is None:
            return None
        target_data.append(tdata)

    weight_map = {}
    for idx, tdata in enumerate(target_data):
        for c in tdata["contributors"]:
            key = c["source"].lower()
            if key not in weight_map:
                weight_map[key] = [0.0] * len(target_names)
            weight_map[key][idx] = c["weight"]

    active = [
        (src, weights) for src, weights in weight_map.items()
        if src in source_cache
    ]
    if not active:
        return None

    gram = []
    for i in range(len(target_names)):
        row = []
        for j in range(len(target_names)):
            row.append(sum(weights[i] * weights[j] for _, weights in active))
        gram.append(row)

    gram_inv = _invert_matrix(gram)
    if gram_inv is None:
        return None

    curve_data = [(source_cache[src][1], weights) for src, weights in active]
    outputs = [[0.0] * frame_count for _ in target_names]

    for frame_idx in range(frame_count):
        rhs = [0.0] * len(target_names)
        for vals, weights in curve_data:
            obs = vals[frame_idx]
            for i, weight in enumerate(weights):
                rhs[i] += obs * weight

        solved = []
        for row in gram_inv:
            solved.append(sum(row[j] * rhs[j] for j in range(len(target_names))))

        for i, value in enumerate(solved):
            outputs[i][frame_idx] = max(0.0, value)

    return outputs


def _coupled_solve_pair(name_a, name_b, target_index, source_cache, frame_count):
    """Solve two coupled ARKit targets jointly via 2x2 least-squares.

    When two targets share source curves, the independent solve conflates
    their contributions. This forms the Gram matrix W^T*W (constant per
    animation) and solves per frame via Cramer's rule.

    Returns (values_a, values_b) or (None, None) on failure.
    """
    outputs = _solve_group_targets(
        [name_a, name_b], target_index, source_cache, frame_count
    )
    if outputs is None:
        return None, None
    return outputs[0], outputs[1]

def _group_partner_label(group_names, current_name):
    return ", ".join(name for name in group_names if name != current_name)


def _weighted_synthesis(target_index, source_cache, calibration, frame_count,
                        coupled_pairs=None, coupled_groups=None):
    """Compute ARKit values for all 51 payload targets.

    Uses sum(w^2) normalization (least-squares inverse projection).
    When coupled_pairs or coupled_groups are provided, those targets are solved
    jointly to eliminate cross-contamination from shared source curves.
    All other targets use the independent solve.
    """
    global_cal = calibration.get("global", {})
    overrides = calibration.get("perCurveOverrides", {})
    arkit_output = {}
    stats = {}

    # --- Phase 1: Solve configured groups/pairs ---
    coupled_targets = set()
    solve_groups = [list(group) for group in (coupled_groups or []) if len(group) >= 2]
    solve_groups.extend([list(pair) for pair in (coupled_pairs or []) if len(pair) == 2])

    for group_names in solve_groups:
        if len(set(group_names)) != len(group_names):
            unreal.log_warning(
                f"{TAG} Coupled solve {group_names}: duplicate target names found, "
                f"skipping."
            )
            continue
        if any(name not in target_index for name in group_names):
            unreal.log_warning(
                f"{TAG} Coupled solve {group_names}: target not in "
                f"payload, falling back to independent."
            )
            continue
        overlap = sorted(set(group_names) & coupled_targets)
        if overlap:
            unreal.log_warning(
                f"{TAG} Coupled solve {group_names}: overlaps already-solved "
                f"targets {overlap}, skipping."
            )
            continue

        group_values = _solve_group_targets(
            group_names, target_index, source_cache, frame_count
        )
        if group_values is None:
            unreal.log_warning(
                f"{TAG} Coupled solve failed for {group_names} "
                f"(singular or no data), falling back to independent."
            )
            continue

        range_parts = []
        for idx, name in enumerate(group_names):
            vals = _apply_calibration(group_values[idx], overrides.get(name, global_cal))
            arkit_output[name] = vals
            coupled_targets.add(name)
            tdata = target_index[name]
            found = sum(1 for c in tdata["contributors"]
                        if c["source"].lower() in source_cache)
            stats[name] = {
                "found": found, "total": len(tdata["contributors"]),
                "sw2": tdata["sumWeightSquared"], "skipped": False,
                "coupled_with": _group_partner_label(group_names, name),
                "min": min(vals), "max": max(vals),
                "mean": sum(vals) / len(vals) if vals else 0,
            }
            range_parts.append(
                f"{name}=[{stats[name]['min']:.4f}, {stats[name]['max']:.4f}]"
            )

        unreal.log(
            f"{TAG} Coupled solve [{', '.join(group_names)}]: "
            f"{', '.join(range_parts)}"
        )

    # --- Phase 2: Independent solve for remaining targets ---
    for arkit_name, tdata in target_index.items():
        if arkit_name in coupled_targets:
            continue

        contributors = tdata["contributors"]
        sw2 = tdata["sumWeightSquared"]
        if sw2 == 0:
            unreal.log_warning(f"{TAG} sumWeightSquared==0 for {arkit_name}, skipping.")
            continue

        found = 0
        total = len(contributors)
        values = [0.0] * frame_count

        for c in contributors:
            src_lower = c["source"].lower()
            w = c["weight"]
            if src_lower not in source_cache:
                continue
            found += 1
            src_vals = source_cache[src_lower][1]
            for i in range(frame_count):
                values[i] += src_vals[i] * w

        if found == 0:
            unreal.log_warning(
                f"{TAG} All {total} contributors missing for {arkit_name}, skipping."
            )
            stats[arkit_name] = {
                "found": 0, "total": total, "sw2": sw2, "skipped": True
            }
            continue

        values = [v / sw2 for v in values]

        cal = overrides.get(arkit_name, global_cal)
        values = _apply_calibration(values, cal)

        arkit_output[arkit_name] = values
        stats[arkit_name] = {
            "found": found,
            "total": total,
            "sw2": sw2,
            "skipped": False,
            "min": min(values),
            "max": max(values),
            "mean": sum(values) / len(values) if values else 0,
        }

    return arkit_output, stats


# ---------------------------------------------------------------------------
# Unified JawOpen + MouthClose ("visual opening" model)
# ---------------------------------------------------------------------------

def _mean_source_group(source_cache, curve_names, frame_count):
    """Compute per-frame mean of a group of source curves."""
    found = [c.lower() for c in curve_names if c.lower() in source_cache]
    if not found:
        return None, 0
    vals = [0.0] * frame_count
    for curve_key in found:
        src = source_cache[curve_key][1]
        for i in range(frame_count):
            vals[i] += src[i]
    return [v / len(found) for v in vals], len(found)


def _compute_mouth_pair(arkit_output, source_cache, calibration, frame_count):
    """Jointly compute JawOpen (adjusted) and MouthClose in a single pass.

    Replaces the former two-step approach (_compute_mouth_close followed by
    _apply_jaw_purse_compensation) with a unified "visual opening" model:

      lip_closure    = mean(LipsTowards) + lipsPurseWeight * mean(LipsPurse)
      visual_opening = max(0, raw_jawOpen - jawFactor * mean(LipsPurse))

      arkit_jawOpen   = visual_opening
      raw_mouthClose  = lip_closure * raw_jawOpen          (signal fidelity)
      effective_cap   = max(0, visual_opening - puckerFactor * MouthPucker)
      arkit_mouthClose = clamp(min(raw_mouthClose, effective_cap))

    MouthClose is derived from the *original* JawOpen so the lip-closure
    signal is preserved at full strength, then capped against the *adjusted*
    JawOpen minus a pucker margin so combined MouthClose + MouthPucker never
    exceeds the visible jaw gap on FaceIt characters.

    Parameters come from the payload calibration section and can be tuned
    via the calibrate_mouth_params.py fitting script.
    """
    mc_config = calibration.get("mouthClose", {})
    jp_config = calibration.get("jawPurseCompensation", {})

    mc_enabled = mc_config.get("enabled", True)
    jp_enabled = jp_config.get("enabled", False)

    if not mc_enabled and not jp_enabled:
        return

    if "JawOpen" not in arkit_output:
        unreal.log_warning(
            f"{TAG} MouthPair: JawOpen not yet synthesized. Skipping."
        )
        return

    raw_jaw = list(arkit_output["JawOpen"])

    # ── Read LipsPurse source curves (shared by both jaw comp and MouthClose)
    lp_curves = jp_config.get(
        "lipsPurseSourceCurves",
        mc_config.get("lipsPurseSourceCurves", []),
    )
    lp_vals, lp_count = _mean_source_group(source_cache, lp_curves, frame_count)

    # ── Read MouthFunnel source curves (shared by jaw comp and MouthClose) ─
    funnel_curves = jp_config.get("funnelSourceCurves",
                                  mc_config.get("funnelSourceCurves", []))
    fn_vals, fn_count = (
        _mean_source_group(source_cache, funnel_curves, frame_count)
        if funnel_curves else (None, 0)
    )

    # ── Step 1: Adjust JawOpen ("visual opening") ──────────────────────────
    jaw_factor = jp_config.get("factor", 0.75)
    if jp_enabled and lp_vals is not None:
        funnel_gate_scale = jp_config.get("funnelGateScale", 0.0)
        use_funnel_gate = fn_vals is not None and funnel_gate_scale > 0

        adjusted_jaw = [0.0] * frame_count
        for i in range(frame_count):
            if use_funnel_gate:
                gate = max(0.0, 1.0 - funnel_gate_scale * fn_vals[i])
                eff_factor = jaw_factor * gate
            else:
                eff_factor = jaw_factor
            adjusted_jaw[i] = max(0.0, raw_jaw[i] - eff_factor * lp_vals[i])

        old_range = (min(raw_jaw), max(raw_jaw))
        new_range = (min(adjusted_jaw), max(adjusted_jaw))
        arkit_output["JawOpen"] = adjusted_jaw
        gate_msg = ""
        if use_funnel_gate:
            gate_msg = f", funnelGate={funnel_gate_scale} ({fn_count} curves)"
        unreal.log(
            f"{TAG} JawOpen purse compensation (factor={jaw_factor}{gate_msg}): "
            f"[{old_range[0]:.4f}, {old_range[1]:.4f}] → "
            f"[{new_range[0]:.4f}, {new_range[1]:.4f}]"
        )
    else:
        adjusted_jaw = raw_jaw

    # ── Step 2: Compute MouthClose ─────────────────────────────────────────
    if not mc_enabled:
        return

    lt_curves = mc_config.get("lipsTowardsSourceCurves", [])
    lp_weight = mc_config.get("lipsPurseWeight", 0.0)

    lt_vals, lt_count = _mean_source_group(source_cache, lt_curves, frame_count)

    has_lt = lt_vals is not None
    has_lp = lp_vals is not None and lp_weight > 0

    # Funnel gate for MouthClose: reuse funnel data from jaw compensation.
    # When funnel is high the mouth is in an open "O" shape and lip_closure
    # should contribute less to MouthClose.
    mc_funnel_gate_scale = mc_config.get("funnelGateScale", 0.0)
    mc_use_funnel = (
        mc_funnel_gate_scale > 0
        and fn_vals is not None  # fn_vals computed in Step 1
    )

    if has_lt or has_lp:
        lip_closure = [0.0] * frame_count
        if has_lt:
            for i in range(frame_count):
                lip_closure[i] += lt_vals[i]
        if has_lp:
            for i in range(frame_count):
                lip_closure[i] += lp_weight * lp_vals[i]

        if mc_use_funnel:
            for i in range(frame_count):
                gate = max(0.0, 1.0 - mc_funnel_gate_scale * fn_vals[i])
                lip_closure[i] *= gate

        src_parts = []
        if has_lt:
            src_parts.append(f"{lt_count} LipsTowards")
        if has_lp:
            src_parts.append(f"{lp_count} LipsPurse (weight={lp_weight})")
        if mc_use_funnel:
            src_parts.append(f"funnelGate={mc_funnel_gate_scale}")
        unreal.log(f"{TAG} MouthClose: using {', '.join(src_parts)}.")

        mc_vals = [lip_closure[i] * raw_jaw[i] for i in range(frame_count)]
    else:
        lips_key = mc_config.get(
            "lipsTogetherSourceCurve",
            "CTRL_Expressions_Mouth_Lips_Together_UL",
        ).lower()
        if lips_key not in source_cache:
            unreal.log_warning(
                f"{TAG} MouthClose: no LipsTowards, LipsPurse, or "
                f"LipsTogether curves found. Skipping."
            )
            return
        unreal.log(f"{TAG} MouthClose: falling back to legacy LipsTogether.")
        lips_vals = source_cache[lips_key][1]
        mc_vals = [lips_vals[i] * raw_jaw[i] for i in range(frame_count)]

    # ── Step 3: Cap against adjusted JawOpen (forward constraint) ──────────
    # Real ARKit data has mouthClose > jawOpen ~25% of the time.
    # forwardConstraintRatio > 1.0 relaxes the cap to allow this.
    fc_ratio = mc_config.get("forwardConstraintRatio", 1.0)
    jaw_capped = 0
    for i in range(frame_count):
        cap = adjusted_jaw[i] * fc_ratio
        if mc_vals[i] > cap:
            mc_vals[i] = cap
            jaw_capped += 1

    # ── Step 4: Pucker-aware cap ───────────────────────────────────────────
    pucker_factor = jp_config.get("puckerFactor", 0.0)
    pucker_capped = 0
    if pucker_factor > 0 and "MouthPucker" in arkit_output:
        pucker_vals = arkit_output["MouthPucker"]
        for i in range(frame_count):
            eff_cap = max(0.0, adjusted_jaw[i]
                         - pucker_factor * pucker_vals[i])
            if mc_vals[i] > eff_cap:
                mc_vals[i] = eff_cap
                pucker_capped += 1

    # ── Step 5: Final calibration clamp ────────────────────────────────────
    mc_vals = _apply_calibration(mc_vals, {
        "scale": mc_config.get("scale", 1.0),
        "offset": mc_config.get("offset", 0.0),
        "clampMin": mc_config.get("clampMin", 0.0),
        "clampMax": mc_config.get("clampMax", 0.5),
    })

    arkit_output["MouthClose"] = mc_vals

    mc_min, mc_max = min(mc_vals), max(mc_vals)
    mc_mean = sum(mc_vals) / len(mc_vals) if mc_vals else 0
    unreal.log(
        f"{TAG} MouthClose: min={mc_min:.4f}, max={mc_max:.4f}, "
        f"mean={mc_mean:.4f}  "
        f"(jaw-capped {jaw_capped}, pucker-capped {pucker_capped} frames)"
    )


# ---------------------------------------------------------------------------
# Temporal smoothing (optional import)
# ---------------------------------------------------------------------------

def _try_import_smoothing():
    """Import the temporal smoothing module from the same directory."""
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
    except NameError:
        script_dir = None

    if script_dir and script_dir not in sys.path:
        sys.path.insert(0, script_dir)

    try:
        from temporal_smoothing import apply_temporal_smoothing, compute_smoothing_comparison
        return apply_temporal_smoothing, compute_smoothing_comparison
    except ImportError:
        return None, None


def _get_runtime_options():
    """Consume one-shot runtime options injected by the menu launcher."""
    return globals().pop("_ARKIT_REMAP_RUNTIME_OPTIONS", None)


def _resolve_smoothing_config(payload, calibration, runtime_options=None):
    """Build smoothing config, optionally overriding mode for this run."""
    base = dict(calibration.get("smoothing", payload.get("smoothing", {})))
    runtime_options = runtime_options or {}
    mode = runtime_options.get("smoothingMode")
    if not mode:
        return base

    if mode == "none":
        base["enabled"] = False
    elif mode in ("one_euro", "ema"):
        base["enabled"] = True
        base["method"] = mode
    else:
        unreal.log_warning(f"{TAG} Unknown smoothing override '{mode}', ignoring.")
        return base

    unreal.log(f"{TAG} Runtime smoothing override: {mode}")
    return base


# ---------------------------------------------------------------------------
# Write curves to duplicate
# ---------------------------------------------------------------------------

def _write_arkit_curves(dup_seq, arkit_output, times):
    """Write all computed ARKit curves onto the duplicate sequence.

    Uses the IAnimationDataController bracket mechanism to batch all
    add/remove operations into a single transaction. UE only recompresses
    the animation once when the outermost bracket closes, instead of after
    every individual curve operation.
    """
    controller = None
    try:
        controller = dup_seq.controller
        controller.open_bracket(unreal.Text("ARKit Remap Batch Write"))
        unreal.log(f"{TAG} Opened controller bracket for batch write.")
    except Exception as e:
        unreal.log_warning(
            f"{TAG} Could not open controller bracket ({e}). "
            f"Falling back to unbatched writes -- this will be slow."
        )
        controller = None

    written = 0
    for name, values in arkit_output.items():
        if LIB.does_curve_exist(dup_seq, name, RCT_FLOAT):
            LIB.remove_curve(dup_seq, name, False)
        LIB.add_curve(dup_seq, name, RCT_FLOAT, False)
        LIB.add_float_curve_keys(dup_seq, name, times, values)
        written += 1

    if controller is not None:
        try:
            controller.close_bracket()
            unreal.log(f"{TAG} Closed controller bracket (single recompression).")
        except Exception as e:
            unreal.log_warning(f"{TAG} close_bracket failed: {e}")

    return written


# ---------------------------------------------------------------------------
# QA report
# ---------------------------------------------------------------------------

def _write_qa_report(run_data, payload_path, calibration=None):
    """Write per-run QA logs to .cursor/arkit-remap/reports/run-logs/."""
    calibration = calibration or {}
    project_dir = unreal.Paths.project_dir()
    reports_dir = os.path.join(
        project_dir, ".cursor", "arkit-remap", "reports", "run-logs"
    )
    os.makedirs(reports_dir, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%S")

    csv_path = os.path.join(reports_dir, f"arkit_remap_run_{ts}.csv")
    md_path = os.path.join(reports_dir, f"arkit_remap_run_{ts}.md")

    all_rows = []
    for entry in run_data:
        for target, s in entry["stats"].items():
            all_rows.append({
                "sequence": entry["source_path"],
                "target": target,
                "found": s.get("found", 0),
                "total": s.get("total", 0),
                "sumWeightSquared": round(s.get("sw2", 0), 6),
                "skipped": s.get("skipped", False),
                "min": round(s.get("min", 0), 6) if not s.get("skipped") else "",
                "max": round(s.get("max", 0), 6) if not s.get("skipped") else "",
                "mean": round(s.get("mean", 0), 6) if not s.get("skipped") else "",
                "frame_count": entry["frame_count"],
            })

    if all_rows:
        with open(csv_path, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(all_rows[0].keys()))
            w.writeheader()
            w.writerows(all_rows)

    total_seqs = len(run_data)
    total_curves = sum(e["curves_written"] for e in run_data)
    all_missing = set()
    for e in run_data:
        all_missing.update(e.get("missing_sources", []))
    skipped_targets = [r["target"] for r in all_rows if r["skipped"]]

    lines = [
        f"# ARKit Remap Run Report",
        f"",
        f"**Timestamp:** {ts}  ",
        f"**Payload:** `{payload_path}`  ",
        f"**Sequences processed:** {total_seqs}  ",
        f"**Total ARKit curves written:** {total_curves}  ",
        f"",
    ]

    for entry in run_data:
        lines.append(f"## {entry['source_path']}")
        lines.append(f"")
        lines.append(f"- Duplicate: `{entry['dup_path']}`")
        lines.append(f"- Frames: {entry['frame_count']}")
        lines.append(f"- Curves written: {entry['curves_written']}")
        lines.append(f"- Missing source curves: {len(entry.get('missing_sources', []))}")
        if entry.get("missing_sources"):
            for m in entry["missing_sources"][:15]:
                lines.append(f"  - `{m}`")
            if len(entry["missing_sources"]) > 15:
                lines.append(f"  - ... and {len(entry['missing_sources']) - 15} more")
        lines.append(f"")

    # Clamp-boundary alerting (IMP 3): flag targets where >10% of frames
    # hit the clamp floor or ceiling, indicating under-ranged calibration.
    clamp_alerts = []
    for entry in run_data:
        fc = entry["frame_count"]
        if fc == 0:
            continue
        for target, s in entry["stats"].items():
            if s.get("skipped"):
                continue
            mn, mx = s.get("min", 0), s.get("max", 0)
            coupled = s.get("coupled_with", "")

            cal_lo = 0.0
            cal_hi = 1.0
            if target == "MouthClose":
                cal_hi = calibration.get("mouthClose", {}).get("clampMax", 0.5)
            if mn <= cal_lo + 1e-6 or mx >= cal_hi - 1e-6:
                clamp_alerts.append({
                    "sequence": entry["source_path"],
                    "target": target,
                    "min": mn, "max": mx,
                    "clampMin": cal_lo, "clampMax": cal_hi,
                    "coupled": coupled,
                })

    if clamp_alerts:
        lines.append(f"## Clamp-Boundary Alerts")
        lines.append(f"")
        lines.append(f"Targets hitting calibration clamp boundaries (may indicate "
                     f"under-ranged calibration):")
        lines.append(f"")
        lines.append(f"| Target | Min | Max | Clamp Range | Coupled | Sequence |")
        lines.append(f"|--------|-----|-----|-------------|---------|----------|")
        for a in clamp_alerts:
            lines.append(
                f"| {a['target']} | {a['min']:.4f} | {a['max']:.4f} | "
                f"[{a['clampMin']}, {a['clampMax']}] | "
                f"{a['coupled'] or '—'} | "
                f"`{a['sequence'].rsplit('/', 1)[-1]}` |"
            )
        lines.append(f"")

    any_smoothing = any(e.get("smoothing_report") for e in run_data)
    if any_smoothing:
        lines.append(f"## Temporal Smoothing")
        lines.append(f"")
        for entry in run_data:
            sr = entry.get("smoothing_report")
            if not sr:
                continue
            lines.append(f"### {entry['source_path']}")
            lines.append(f"")
            lines.append(f"| Curve | Mean Δ | Max Δ | Altered % |")
            lines.append(f"|-------|--------|-------|-----------|")
            for cname, sm in sorted(sr.items(), key=lambda kv: kv[1]["meanDelta"], reverse=True):
                if sm["meanDelta"] < 0.0001:
                    continue
                lines.append(
                    f"| {cname} | {sm['meanDelta']:.5f} | "
                    f"{sm['maxDelta']:.5f} | {sm['alteredPct']:.1f}% |"
                )
            lines.append(f"")

    if skipped_targets:
        lines.append(f"## Skipped targets (all contributors missing)")
        lines.append(f"")
        for t in sorted(set(skipped_targets)):
            lines.append(f"- {t}")
        lines.append(f"")

    if all_missing:
        lines.append(f"## All missing source curves ({len(all_missing)})")
        lines.append(f"")
        for m in sorted(all_missing):
            lines.append(f"- `{m}`")
        lines.append(f"")

    with open(md_path, "w") as f:
        f.write("\n".join(lines))

    unreal.log(f"{TAG} QA CSV: {csv_path}")
    unreal.log(f"{TAG} QA MD:  {md_path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(asset_paths=None, runtime_options=None):
    """Run the ARKit remap pipeline.

    Args:
        asset_paths: Optional list of UE asset paths (e.g.
            ["/Game/.../MyAnim"]). If None, uses Content Browser selection.
    """
    unreal.log(f"{TAG} === ARKit Remap v2 starting ===")

    payload, payload_path = _load_payload()
    if payload is None:
        return

    runtime_options = runtime_options or _get_runtime_options() or {}

    target_index, required_sources = _build_target_index(payload)
    calibration = payload.get("calibrationDefaults", {})
    mc_config = calibration.get("mouthClose", {})
    coupled_pairs = payload.get("coupledPairs", [])
    coupled_groups = payload.get("coupledGroups", [])
    smoothing_config = _resolve_smoothing_config(payload, calibration, runtime_options)

    known_arkit_names = list(target_index.keys()) + ["MouthClose"]
    unreal.log(f"{TAG} Payload loaded: {len(target_index)} targets, "
               f"{len(required_sources)} unique source curves.")
    if coupled_pairs:
        unreal.log(f"{TAG} Coupled pairs: {len(coupled_pairs)} "
                   f"({', '.join(' <-> '.join(p) for p in coupled_pairs)})")
    if coupled_groups:
        unreal.log(f"{TAG} Coupled groups: {len(coupled_groups)} "
                   f"({'; '.join(', '.join(g) for g in coupled_groups)})")

    _apply_smoothing, _compare_smoothing = _try_import_smoothing()
    smoothing_enabled = smoothing_config.get("enabled", False)
    if smoothing_enabled and _apply_smoothing is None:
        unreal.log_warning(
            f"{TAG} Smoothing enabled in payload but temporal_smoothing module "
            f"not found. Smoothing will be skipped."
        )
        smoothing_enabled = False
    if smoothing_enabled:
        unreal.log(f"{TAG} Temporal smoothing: ON "
                   f"(method={smoothing_config.get('method', 'one_euro')})")

    if asset_paths:
        sequences = []
        for p in asset_paths:
            a = unreal.load_asset(p)
            if a is None:
                unreal.log_error(f"{TAG} Asset not found: {p}")
            elif not isinstance(a, unreal.AnimSequence):
                unreal.log_error(f"{TAG} Not an AnimSequence: {p} ({type(a).__name__})")
            else:
                sequences.append(a)
        if not sequences:
            unreal.log_error(f"{TAG} No valid AnimSequences from explicit paths.")
            return
    else:
        sequences = _get_selected_sequences()
        if not sequences:
            return

    run_data = []

    for seq_asset in sequences:
        source_path = _asset_path(seq_asset)
        source_name = _asset_name(source_path)
        unreal.log(f"{TAG} ── Processing: {source_name} ──")

        dup_seq, dup_path = _prepare_duplicate(source_path, known_arkit_names)
        if dup_seq is None:
            continue

        source_cache, missing_sources = _read_source_curves(seq_asset, required_sources)
        if not source_cache:
            unreal.log_error(f"{TAG} No source curves found on {source_name}. Skipping.")
            continue

        times, frame_count = _validate_key_counts(source_cache)
        unreal.log(f"{TAG} Read {len(source_cache)} source curves, {frame_count} frames.")

        arkit_output, stats = _weighted_synthesis(
            target_index, source_cache, calibration, frame_count,
            coupled_pairs=coupled_pairs,
            coupled_groups=coupled_groups,
        )
        unreal.log(f"{TAG} Synthesized {len(arkit_output)} ARKit curves.")

        _compute_mouth_pair(arkit_output, source_cache, calibration, frame_count)

        if "MouthClose" in arkit_output:
            mc_values = arkit_output["MouthClose"]
            lt_count = len(mc_config.get("lipsTowardsSourceCurves", []))
            stats["MouthClose"] = {
                "found": lt_count + 1, "total": lt_count + 1, "sw2": 0,
                "skipped": False,
                "min": min(mc_values), "max": max(mc_values),
                "mean": sum(mc_values) / len(mc_values) if mc_values else 0,
            }

        if "JawOpen" in arkit_output and "JawOpen" in stats:
            jaw = arkit_output["JawOpen"]
            stats["JawOpen"]["min"] = min(jaw)
            stats["JawOpen"]["max"] = max(jaw)
            stats["JawOpen"]["mean"] = sum(jaw) / len(jaw) if jaw else 0

        smoothing_report = None
        if smoothing_enabled:
            pre_smooth = {k: list(v) for k, v in arkit_output.items()}
            arkit_output = _apply_smoothing(arkit_output, times, smoothing_config)
            smoothing_report = _compare_smoothing(pre_smooth, arkit_output)
            top_affected = sorted(
                smoothing_report.items(),
                key=lambda kv: kv[1]["meanDelta"],
                reverse=True,
            )[:5]
            unreal.log(f"{TAG} Smoothing applied. Top affected curves:")
            for cname, sm in top_affected:
                unreal.log(
                    f"{TAG}   {cname}: meanΔ={sm['meanDelta']:.5f}, "
                    f"maxΔ={sm['maxDelta']:.5f}, "
                    f"altered={sm['alteredPct']:.1f}%"
                )

        written = _write_arkit_curves(dup_seq, arkit_output, times)
        unreal.log(f"{TAG} Wrote {written} curves to {_asset_name(dup_path)}.")

        EAL.save_asset(dup_path)
        unreal.log(f"{TAG} Saved: {dup_path}")

        run_data.append({
            "source_path": source_path,
            "dup_path": dup_path,
            "frame_count": frame_count,
            "curves_written": written,
            "missing_sources": missing_sources,
            "stats": stats,
            "smoothing_report": smoothing_report,
        })

    if run_data:
        _write_qa_report(run_data, payload_path, calibration)

    unreal.log(f"{TAG} === ARKit Remap v2 complete: "
               f"{len(run_data)}/{len(sequences)} sequences processed ===")


if not globals().get("_ARKIT_REMAP_NO_AUTO_RUN"):
    main()
