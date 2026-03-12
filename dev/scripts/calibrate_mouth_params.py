"""Calibrate mouth parameters from matched MHA + ARKit reference data.

Reads MHA source (ctrl_expressions curves) and a real ARKit reference
(ARKit-named curves) at corresponding frames, then computes optimal values
for jawCompensationFactor, puckerFactor, and lipsPurseWeight via grid-search
least-squares fitting.

Outputs a JSON report to .cursor/arkit-remap/reports/mouth_calibration_report.json.

Usage:
  python .cursor/scripts/run_python_in_unreal.py --file .cursor/arkit-remap/scripts/calibrate_mouth_params.py
"""

import unreal
import json
import os
import math

LIB = unreal.AnimationLibrary
RCT_FLOAT = unreal.RawCurveTrackTypes.RCT_FLOAT
TAG = "[MouthCal]"

# ── Configuration ───────────────────────────────────────────────────────────

MHA_PATH = "/Game/3_FaceAnims/VEC_MHA/AgenticPy/AS_MP_VecDemo1-allkeys"

ARKIT_REF_CANDIDATES = [
    "/Game/3_FaceAnims/VecnaArkitFace/Vec-ARKITBAKED-T34_60fps-02",
    "/Game/3_FaceAnims/VecnaArkitFace/AS_Vec3Baked_v01",
    "/Game/3_FaceAnims/VecnaArkitFace/Vecna_ARKIT-BAKE-i14",
    "/Game/3_FaceAnims/VecnaArkitFace/Vec-ARKITBAKED-Tx-60fps_01",
]

MHA_KNOWN_FRAME = 956
FULL_TAKE_KNOWN_FRAME = 10361

# Definitive alignment: ARKit baked frame 20724 @ 60fps = MHA frame 0.
# User-confirmed correspondence (2026-03-12).
ARKIT_FRAME_AT_MHA_ZERO = 20724
ARKIT_BAKED_FPS = 60.0
DEFINITIVE_OFFSET = ARKIT_FRAME_AT_MHA_ZERO / ARKIT_BAKED_FPS  # 345.4s

# Alignment curves: use eye blinks and smiles for temporal alignment since
# they pass through PoseAsset near-1:1 and should correlate between MHA and ARKit.
MHA_ALIGN_CURVES = [
    ("ctrl_expressions_eyeblinkl", "eyeBlinkLeft"),
    ("ctrl_expressions_eyeblinkr", "eyeBlinkRight"),
    ("ctrl_expressions_mouthcornerpulll", "mouthSmileLeft"),
    ("ctrl_expressions_mouthcornerpullr", "mouthSmileRight"),
]

MHA_JAW_OPEN_CURVE = "ctrl_expressions_jawopen"
MHA_LIPS_PURSE_CURVES = [
    "ctrl_expressions_mouthlipspurseul",
    "ctrl_expressions_mouthlipspurseur",
    "ctrl_expressions_mouthlipspursedl",
    "ctrl_expressions_mouthlipspursedr",
]
MHA_LIPS_TOWARDS_CURVES = [
    "ctrl_expressions_mouthlipstowardsul",
    "ctrl_expressions_mouthlipstowardsur",
    "ctrl_expressions_mouthlipstowardsdl",
    "ctrl_expressions_mouthlipstowardsdr",
]

ARKIT_JAW_OPEN_CURVE = "jawOpen"
ARKIT_MOUTH_CLOSE_CURVE = "mouthClose"
ARKIT_MOUTH_PUCKER_CURVE = "mouthPucker"


# ── Curve reading ───────────────────────────────────────────────────────────

def _read_curve(seq, name):
    """Read a single float curve, trying exact case then lowercase."""
    for try_name in [name, name.lower()]:
        if LIB.does_curve_exist(seq, try_name, RCT_FLOAT):
            times, values = LIB.get_float_keys(seq, try_name)
            return list(times), list(values)
    return None


def _read_mean_group(seq, curve_names):
    """Read multiple curves and return (times, per-frame-mean)."""
    all_data = []
    for name in curve_names:
        data = _read_curve(seq, name)
        if data is not None:
            all_data.append(data)
    if not all_data:
        return None, None

    n = max(len(d[1]) for d in all_data)
    times = next((d[0] for d in all_data if len(d[0]) == n), all_data[0][0])
    means = [0.0] * n
    for _, vals in all_data:
        for i in range(min(len(vals), n)):
            means[i] += vals[i]
    means = [m / len(all_data) for m in means]
    return times, means


# ── Time-based interpolation ────────────────────────────────────────────────

def _interp_at_time(times, values, target_time):
    """Linear interpolation at target_time. Returns None if out of range."""
    if not times or target_time < times[0] - 0.001 or target_time > times[-1] + 0.001:
        return None
    target_time = max(times[0], min(times[-1], target_time))

    lo, hi = 0, len(times) - 1
    while lo < hi - 1:
        mid = (lo + hi) // 2
        if times[mid] <= target_time:
            lo = mid
        else:
            hi = mid
    if lo == hi or abs(times[hi] - times[lo]) < 1e-10:
        return values[lo]
    alpha = (target_time - times[lo]) / (times[hi] - times[lo])
    return values[lo] * (1.0 - alpha) + values[hi] * alpha


# ── Time offset detection ──────────────────────────────────────────────────

def _multi_signal_mse(mha_signals, arkit_signals, mha_times, arkit_times,
                      offset, sample_step=1):
    """Combined MSE across multiple signal pairs at a given time offset."""
    total = 0.0
    count = 0
    for mha_vals, arkit_vals in zip(mha_signals, arkit_signals):
        for i in range(0, len(mha_times), sample_step):
            arkit_val = _interp_at_time(arkit_times, arkit_vals,
                                        mha_times[i] + offset)
            if arkit_val is not None:
                diff = mha_vals[i] - arkit_val
                total += diff * diff
                count += 1
    return (total / count) if count > 0 else float('inf'), count


def _find_time_offset(mha_seq, arkit_seq, mha_times, arkit_times):
    """Align MHA and ARKit using stable 1:1 signals (eye blinks, smiles).

    These curves pass through PoseAsset near-1:1, so the MHA and ARKit
    values should track each other once properly time-aligned.  Using them
    avoids the jawOpen correlation problem where MHA and ARKit represent
    different things.
    """
    mha_dur = mha_times[-1] - mha_times[0]
    arkit_dur = arkit_times[-1] - arkit_times[0]
    sample_step = max(1, len(mha_times) // 300)

    mha_signals, arkit_signals = [], []
    for mha_curve, arkit_curve in MHA_ALIGN_CURVES:
        m = _read_curve(mha_seq, mha_curve)
        a = _read_curve(arkit_seq, arkit_curve)
        if m is not None and a is not None:
            mha_signals.append(m[1])
            arkit_signals.append(a[1])
            unreal.log(f"{TAG} Alignment signal: {mha_curve} <-> {arkit_curve}")

    if not mha_signals:
        unreal.log_warning(f"{TAG} No alignment signals found; using jawOpen.")
        mha_jaw = _read_curve(mha_seq, MHA_JAW_OPEN_CURVE)
        arkit_jaw = _read_curve(arkit_seq, ARKIT_JAW_OPEN_CURVE)
        if mha_jaw and arkit_jaw:
            mha_signals = [mha_jaw[1]]
            arkit_signals = [arkit_jaw[1]]

    if not mha_signals:
        unreal.log_error(f"{TAG} Cannot align: no signals available.")
        return 0.0

    # -- Candidate offsets --
    mha_known_time = mha_times[min(MHA_KNOWN_FRAME, len(mha_times) - 1)]
    hint_offsets = [0.0]  # try direct alignment first (same frame range)
    for fps_guess in [60.0, 30.0, 58.5, 59.94, 29.97, 24.0]:
        arkit_known_time = FULL_TAKE_KNOWN_FRAME / fps_guess
        if arkit_known_time <= arkit_times[-1] + mha_dur:
            hint_offsets.append(arkit_known_time - mha_known_time)

    # -- Broad coarse search: 2-second steps across full range --
    max_off = arkit_dur
    best_offset = 0.0
    best_mse = float('inf')

    coarse_step = 2.0
    off = 0.0
    while off <= max_off:
        mse, cnt = _multi_signal_mse(
            mha_signals, arkit_signals, mha_times, arkit_times,
            off, sample_step)
        if cnt > 0 and mse < best_mse:
            best_mse, best_offset = mse, off
        off += coarse_step

    unreal.log(f"{TAG} Coarse search best: offset={best_offset:.1f}s, "
               f"MSE={best_mse:.6f}")

    # -- Also evaluate all hint offsets --
    for hint in hint_offsets:
        mse, cnt = _multi_signal_mse(
            mha_signals, arkit_signals, mha_times, arkit_times,
            hint, sample_step)
        if cnt > 0 and mse < best_mse:
            best_mse, best_offset = mse, hint
            unreal.log(f"{TAG} Hint offset {hint:.1f}s is better: "
                       f"MSE={best_mse:.6f}")

    # -- Fine search: 50ms steps in ±5s around best --
    fine_center = best_offset
    for delta_ms in range(-5000, 5001, 50):
        candidate = fine_center + delta_ms * 0.001
        if candidate < 0:
            continue
        mse, cnt = _multi_signal_mse(
            mha_signals, arkit_signals, mha_times, arkit_times,
            candidate, sample_step)
        if cnt > 0 and mse < best_mse:
            best_mse, best_offset = mse, candidate

    # -- Ultra-fine: 5ms in ±0.5s --
    fine_center = best_offset
    for delta_ms in range(-500, 501, 5):
        candidate = fine_center + delta_ms * 0.001
        if candidate < 0:
            continue
        mse, cnt = _multi_signal_mse(
            mha_signals, arkit_signals, mha_times, arkit_times,
            candidate, sample_step)
        if cnt > 0 and mse < best_mse:
            best_mse, best_offset = mse, candidate

    unreal.log(f"{TAG} Final offset: {best_offset:.4f}s (MSE={best_mse:.6f})")
    return best_offset


# ── Frame-pair building ─────────────────────────────────────────────────────

def _build_matched_pairs(mha_times, mha_data, arkit_times, arkit_data,
                         offset, sample_every=1):
    """Align MHA and ARKit by time offset and build per-frame data pairs."""
    pairs = []
    for i in range(0, len(mha_times), sample_every):
        t_arkit = mha_times[i] + offset

        arkit_jaw = _interp_at_time(arkit_times, arkit_data["jawOpen"], t_arkit)
        if arkit_jaw is None:
            continue

        arkit_mc = _interp_at_time(
            arkit_times, arkit_data["mouthClose"], t_arkit) or 0.0
        arkit_pk = _interp_at_time(
            arkit_times, arkit_data["mouthPucker"], t_arkit) or 0.0

        pairs.append({
            "mha_frame": i,
            "mha_time": mha_times[i],
            "arkit_time": t_arkit,
            "mha_jawOpen": mha_data["jawOpen"][i],
            "mha_lipsPurse": mha_data["lipsPurse"][i],
            "mha_lipsTowards": mha_data["lipsTowards"][i],
            "arkit_jawOpen": arkit_jaw,
            "arkit_mouthClose": arkit_mc,
            "arkit_mouthPucker": arkit_pk,
        })
    return pairs


# ── Calibration routines ────────────────────────────────────────────────────

def _calibrate_jaw_factor(pairs):
    """Grid-search for the jawCompensation factor that minimises jawOpen MSE.

    adjusted = max(0, mha_jawOpen - factor * mha_lipsPurse)
    Target: adjusted ≈ arkit_jawOpen
    """
    best_f, best_mse = 0.0, float('inf')

    for f_int in range(0, 301):
        factor = f_int * 0.01
        mse = sum(
            (p["arkit_jawOpen"] - max(0.0, p["mha_jawOpen"]
                                      - factor * p["mha_lipsPurse"])) ** 2
            for p in pairs
        ) / len(pairs)
        if mse < best_mse:
            best_mse, best_f = mse, factor

    center = best_f
    for f_int in range(max(0, int((center - 0.05) * 1000)),
                       int((center + 0.05) * 1000) + 1):
        factor = f_int * 0.001
        mse = sum(
            (p["arkit_jawOpen"] - max(0.0, p["mha_jawOpen"]
                                      - factor * p["mha_lipsPurse"])) ** 2
            for p in pairs
        ) / len(pairs)
        if mse < best_mse:
            best_mse, best_f = mse, factor

    return best_f, best_mse


def _eval_mouth_close(pairs, jaw_factor, pucker_factor, lp_weight, clamp_max=0.5):
    """Evaluate MouthClose MSE for a given set of parameters."""
    mse = 0.0
    for p in pairs:
        lip_closure = p["mha_lipsTowards"] + lp_weight * p["mha_lipsPurse"]
        raw_mc = lip_closure * p["mha_jawOpen"]
        adj_jaw = max(0.0, p["mha_jawOpen"] - jaw_factor * p["mha_lipsPurse"])
        eff_cap = max(0.0, adj_jaw - pucker_factor * p["arkit_mouthPucker"])
        final_mc = max(0.0, min(clamp_max, min(raw_mc, eff_cap)))
        diff = p["arkit_mouthClose"] - final_mc
        mse += diff * diff
    return mse / len(pairs) if pairs else float('inf')


def _calibrate_pucker_and_weight(pairs, jaw_factor):
    """Joint 2D grid-search over (pucker_factor, lipsPurseWeight)."""
    best_pf, best_w, best_mse = 0.0, 0.5, float('inf')

    # Coarse: step 0.05 over [0,2] x [0,1]
    for pf_int in range(0, 41):
        pf = pf_int * 0.05
        for w_int in range(0, 21):
            w = w_int * 0.05
            mse = _eval_mouth_close(pairs, jaw_factor, pf, w)
            if mse < best_mse:
                best_mse, best_pf, best_w = mse, pf, w

    # Fine: step 0.005 in ±0.1 window
    center_pf, center_w = best_pf, best_w
    for pf_int in range(max(0, int((center_pf - 0.1) * 200)),
                        int((center_pf + 0.1) * 200) + 1):
        pf = pf_int * 0.005
        for w_int in range(max(0, int((center_w - 0.1) * 200)),
                           min(200, int((center_w + 0.1) * 200) + 1)):
            w = w_int * 0.005
            mse = _eval_mouth_close(pairs, jaw_factor, pf, w)
            if mse < best_mse:
                best_mse, best_pf, best_w = mse, pf, w

    return best_pf, best_w, best_mse


# ── Diagnostic helpers ──────────────────────────────────────────────────────

def _compute_diagnostic(p, jaw_factor, pucker_factor, lp_weight):
    """Compute all intermediate values for a single frame pair."""
    lip_closure = p["mha_lipsTowards"] + lp_weight * p["mha_lipsPurse"]
    raw_mc = lip_closure * p["mha_jawOpen"]
    adj_jaw = max(0.0, p["mha_jawOpen"] - jaw_factor * p["mha_lipsPurse"])
    eff_cap = max(0.0, adj_jaw - pucker_factor * p["arkit_mouthPucker"])
    final_mc = max(0.0, min(0.5, min(raw_mc, eff_cap)))
    return {
        "mha_frame": p["mha_frame"],
        "mha_jawOpen": round(p["mha_jawOpen"], 5),
        "mha_lipsPurse": round(p["mha_lipsPurse"], 5),
        "mha_lipsTowards": round(p["mha_lipsTowards"], 5),
        "real_arkit_jawOpen": round(p["arkit_jawOpen"], 5),
        "real_arkit_mouthClose": round(p["arkit_mouthClose"], 5),
        "real_arkit_mouthPucker": round(p["arkit_mouthPucker"], 5),
        "our_adjusted_jawOpen": round(adj_jaw, 5),
        "our_lip_closure": round(lip_closure, 5),
        "our_raw_mouthClose": round(raw_mc, 5),
        "our_effective_cap": round(eff_cap, 5),
        "our_final_mouthClose": round(final_mc, 5),
        "jawOpen_error": round(adj_jaw - p["arkit_jawOpen"], 5),
        "mouthClose_error": round(final_mc - p["arkit_mouthClose"], 5),
    }


# ── Main ────────────────────────────────────────────────────────────────────

def main():
    unreal.log(f"{TAG} === Mouth Parameter Calibration ===")

    # -- Load MHA source --
    mha_seq = unreal.load_asset(MHA_PATH)
    if mha_seq is None or not isinstance(mha_seq, unreal.AnimSequence):
        unreal.log_error(f"{TAG} Cannot load MHA source: {MHA_PATH}")
        return

    # -- Load ARKit reference (first AnimSequence found) --
    arkit_seq, arkit_path = None, None
    for path in ARKIT_REF_CANDIDATES:
        asset = unreal.load_asset(path)
        if asset is not None and isinstance(asset, unreal.AnimSequence):
            arkit_seq, arkit_path = asset, path
            break
    if arkit_seq is None:
        unreal.log_error(f"{TAG} No usable ARKit AnimSequence reference found.")
        return

    unreal.log(f"{TAG} MHA source: {MHA_PATH}")
    unreal.log(f"{TAG} ARKit ref:  {arkit_path}")

    # -- Read MHA curves --
    mha_jaw_data = _read_curve(mha_seq, MHA_JAW_OPEN_CURVE)
    if mha_jaw_data is None:
        unreal.log_error(f"{TAG} Cannot read {MHA_JAW_OPEN_CURVE} from MHA")
        return
    mha_times, mha_jaw = mha_jaw_data

    _, mha_purse = _read_mean_group(mha_seq, MHA_LIPS_PURSE_CURVES)
    _, mha_towards = _read_mean_group(mha_seq, MHA_LIPS_TOWARDS_CURVES)
    if mha_purse is None or mha_towards is None:
        unreal.log_error(f"{TAG} Cannot read LipsPurse or LipsTowards from MHA")
        return

    n_mha = len(mha_times)
    mha_fps = n_mha / mha_times[-1] if mha_times[-1] > 0 else 30.0
    unreal.log(f"{TAG} MHA: {n_mha} frames, {mha_times[-1]:.2f}s, ~{mha_fps:.1f}fps")

    # -- Read ARKit reference curves --
    arkit_jaw_data = _read_curve(arkit_seq, ARKIT_JAW_OPEN_CURVE)
    if arkit_jaw_data is None:
        unreal.log_error(f"{TAG} Cannot read {ARKIT_JAW_OPEN_CURVE} from ARKit ref")
        return
    arkit_times, arkit_jaw = arkit_jaw_data

    arkit_mc_data = _read_curve(arkit_seq, ARKIT_MOUTH_CLOSE_CURVE)
    arkit_pk_data = _read_curve(arkit_seq, ARKIT_MOUTH_PUCKER_CURVE)
    arkit_mc = arkit_mc_data[1] if arkit_mc_data else [0.0] * len(arkit_times)
    arkit_pk = arkit_pk_data[1] if arkit_pk_data else [0.0] * len(arkit_times)

    n_arkit = len(arkit_times)
    arkit_fps = n_arkit / arkit_times[-1] if arkit_times[-1] > 0 else 60.0
    unreal.log(f"{TAG} ARKit: {n_arkit} frames, {arkit_times[-1]:.2f}s, "
               f"~{arkit_fps:.1f}fps")
    unreal.log(f"{TAG} ARKit mouthClose present: {arkit_mc_data is not None}")
    unreal.log(f"{TAG} ARKit mouthPucker present: {arkit_pk_data is not None}")

    # -- Determine time offset --
    # Use the definitive user-confirmed alignment: ARKit baked frame 20724
    # at 60fps = MHA frame 0.  For the primary baked reference, this gives
    # offset = 345.4s.  For other refs, fall back to cross-correlation.
    is_primary_ref = "Vec-ARKITBAKED-T34_60fps-02" in arkit_path
    if is_primary_ref:
        offset = DEFINITIVE_OFFSET
        unreal.log(f"{TAG} Using definitive offset: {offset:.4f}s "
                   f"(ARKit frame {ARKIT_FRAME_AT_MHA_ZERO} @ "
                   f"{ARKIT_BAKED_FPS}fps = MHA frame 0)")
    elif arkit_times[-1] < 60.0 or abs(arkit_times[-1] - mha_times[-1]) < 5.0:
        offset = 0.0
        unreal.log(f"{TAG} ARKit ref appears frame-aligned (short/matching "
                   f"duration), using offset=0.0s")
    else:
        offset = _find_time_offset(mha_seq, arkit_seq, mha_times, arkit_times)
    unreal.log(f"{TAG} Final time offset: {offset:.3f}s")

    # -- Build matched pairs --
    mha_data = {
        "jawOpen": mha_jaw, "lipsPurse": mha_purse,
        "lipsTowards": mha_towards,
    }
    arkit_data = {
        "jawOpen": arkit_jaw, "mouthClose": arkit_mc,
        "mouthPucker": arkit_pk,
    }
    pairs = _build_matched_pairs(mha_times, mha_data, arkit_times, arkit_data,
                                 offset)
    unreal.log(f"{TAG} Matched {len(pairs)} frame pairs")

    if len(pairs) < 20:
        unreal.log_error(f"{TAG} Too few matched pairs ({len(pairs)}) for "
                         f"reliable calibration. Check offset / sequences.")
        return

    # -- Calibrate jawCompensationFactor --
    unreal.log(f"{TAG} Calibrating jawCompensation factor...")
    jaw_factor, jaw_mse = _calibrate_jaw_factor(pairs)
    unreal.log(f"{TAG}   jawFactor = {jaw_factor:.4f}  (MSE = {jaw_mse:.6f})")

    # -- Calibrate puckerFactor + lipsPurseWeight jointly --
    unreal.log(f"{TAG} Calibrating puckerFactor + lipsPurseWeight (2D grid)...")
    pucker_factor, lp_weight, mc_mse = _calibrate_pucker_and_weight(
        pairs, jaw_factor)
    unreal.log(f"{TAG}   puckerFactor = {pucker_factor:.4f}")
    unreal.log(f"{TAG}   lipsPurseWeight = {lp_weight:.4f}")
    unreal.log(f"{TAG}   MouthClose MSE = {mc_mse:.6f}")

    # -- Compute old-params MSE for comparison --
    old_jaw_mse = sum(
        (p["arkit_jawOpen"] - max(0.0, p["mha_jawOpen"]
                                  - 0.75 * p["mha_lipsPurse"])) ** 2
        for p in pairs
    ) / len(pairs)
    old_mc_mse = _eval_mouth_close(pairs, 0.75, 0.0, 0.5)

    unreal.log(f"{TAG} Comparison: old jawFactor=0.75 MSE={old_jaw_mse:.6f}, "
               f"new MSE={jaw_mse:.6f}")
    unreal.log(f"{TAG} Comparison: old MC params MSE={old_mc_mse:.6f}, "
               f"new MSE={mc_mse:.6f}")

    # -- Diagnostics at key frames --
    key_frames = [956, 276, 0, n_mha // 4, n_mha // 2, n_mha * 3 // 4]
    diagnostics = []
    for fi in key_frames:
        matching = [p for p in pairs if p["mha_frame"] == fi]
        if matching:
            diagnostics.append(
                _compute_diagnostic(matching[0], jaw_factor,
                                    pucker_factor, lp_weight))

    # -- Per-frame error distribution --
    jaw_errors = []
    mc_errors = []
    for p in pairs:
        adj = max(0.0, p["mha_jawOpen"] - jaw_factor * p["mha_lipsPurse"])
        jaw_errors.append(abs(adj - p["arkit_jawOpen"]))

        lip_c = p["mha_lipsTowards"] + lp_weight * p["mha_lipsPurse"]
        raw_mc = lip_c * p["mha_jawOpen"]
        eff_cap = max(0.0, adj - pucker_factor * p["arkit_mouthPucker"])
        final_mc = max(0.0, min(0.5, min(raw_mc, eff_cap)))
        mc_errors.append(abs(final_mc - p["arkit_mouthClose"]))

    jaw_errors.sort()
    mc_errors.sort()

    def _percentile(arr, pct):
        idx = int(len(arr) * pct / 100.0)
        return arr[min(idx, len(arr) - 1)]

    # -- Build report --
    report = {
        "mha_source": MHA_PATH,
        "arkit_reference": arkit_path,
        "time_offset_seconds": round(offset, 4),
        "matched_pairs": len(pairs),
        "calibrated_params": {
            "jawCompensationFactor": round(jaw_factor, 4),
            "puckerFactor": round(pucker_factor, 4),
            "lipsPurseWeight": round(lp_weight, 4),
        },
        "fit_quality": {
            "jawOpen_MSE": round(jaw_mse, 6),
            "jawOpen_MAE_median": round(_percentile(jaw_errors, 50), 5),
            "jawOpen_MAE_p95": round(_percentile(jaw_errors, 95), 5),
            "mouthClose_MSE": round(mc_mse, 6),
            "mouthClose_MAE_median": round(_percentile(mc_errors, 50), 5),
            "mouthClose_MAE_p95": round(_percentile(mc_errors, 95), 5),
        },
        "old_params_comparison": {
            "old_jawFactor": 0.75,
            "old_lipsPurseWeight": 0.5,
            "old_puckerFactor": 0.0,
            "old_jawOpen_MSE": round(old_jaw_mse, 6),
            "old_mouthClose_MSE": round(old_mc_mse, 6),
        },
        "diagnostics_key_frames": diagnostics,
        "statistics": {
            "mha_jawOpen_range": [round(min(mha_jaw), 4),
                                  round(max(mha_jaw), 4)],
            "mha_lipsPurse_range": [round(min(mha_purse), 4),
                                    round(max(mha_purse), 4)],
            "mha_lipsTowards_range": [round(min(mha_towards), 4),
                                      round(max(mha_towards), 4)],
            "arkit_jawOpen_range": [round(min(arkit_jaw), 4),
                                    round(max(arkit_jaw), 4)],
            "arkit_mouthClose_range": [round(min(arkit_mc), 4),
                                       round(max(arkit_mc), 4)],
            "arkit_mouthPucker_range": [round(min(arkit_pk), 4),
                                        round(max(arkit_pk), 4)],
        },
    }

    out_path = os.path.join(
        unreal.Paths.project_dir(),
        ".cursor", "arkit-remap", "reports",
        "mouth_calibration_report.json",
    )
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(report, f, indent=2)

    unreal.log(f"{TAG} Report: {out_path}")
    unreal.log(f"{TAG} === Calibration summary ===")
    unreal.log(f"{TAG}   jawCompensationFactor: {jaw_factor:.4f}  "
               f"(was 0.75)")
    unreal.log(f"{TAG}   lipsPurseWeight:       {lp_weight:.4f}  "
               f"(was 0.5)")
    unreal.log(f"{TAG}   puckerFactor:          {pucker_factor:.4f}  "
               f"(was 0.0 / not used)")
    unreal.log(f"{TAG} === Calibration complete ===")


main()
