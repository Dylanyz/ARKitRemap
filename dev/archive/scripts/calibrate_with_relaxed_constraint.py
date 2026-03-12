"""Calibrate mouth params with a relaxed forward constraint.

Uses the definitive alignment (ARKit frame 20724 @ 60fps = MHA frame 0)
and sweeps jawFactor, lipsPurseWeight, AND forwardConstraintRatio jointly
to find the parameter set that minimises combined (jawOpen + mouthClose) MSE.
"""
import unreal
import json
import os
import math

LIB = unreal.AnimationLibrary
RCT_FLOAT = unreal.RawCurveTrackTypes.RCT_FLOAT
TAG = "[RelaxCal]"

MHA_PATH = "/Game/3_FaceAnims/VEC_MHA/AgenticPy/AS_MP_VecDemo1-allkeys"
ARKIT_PATH = "/Game/3_FaceAnims/VecnaArkitFace/Vec-ARKITBAKED-T34_60fps-02"
OFFSET = 345.4  # ARKit frame 20724 / 60fps

MHA_JAW = "ctrl_expressions_jawopen"
MHA_PURSE = ["ctrl_expressions_mouthlipspurseul", "ctrl_expressions_mouthlipspurseur",
             "ctrl_expressions_mouthlipspursedl", "ctrl_expressions_mouthlipspursedr"]
MHA_TOWARDS = ["ctrl_expressions_mouthlipstowardsul", "ctrl_expressions_mouthlipstowardsur",
               "ctrl_expressions_mouthlipstowardsdl", "ctrl_expressions_mouthlipstowardsdr"]


def _read(seq, name):
    for n in [name, name.lower()]:
        if LIB.does_curve_exist(seq, n, RCT_FLOAT):
            return list(LIB.get_float_keys(seq, n)[0]), list(LIB.get_float_keys(seq, n)[1])
    return None


def _mean_group(seq, names):
    all_d = []
    for n in names:
        d = _read(seq, n)
        if d:
            all_d.append(d)
    if not all_d:
        return None, None
    k = max(len(v) for _, v in all_d)
    times = next((t for t, v in all_d if len(t) == k), all_d[0][0])
    means = [0.0] * k
    for _, v in all_d:
        for i in range(min(len(v), k)):
            means[i] += v[i]
    return times, [m / len(all_d) for m in means]


def _interp(times, vals, t):
    if not times or t < times[0] - 0.001 or t > times[-1] + 0.001:
        return None
    t = max(times[0], min(times[-1], t))
    lo, hi = 0, len(times) - 1
    while lo < hi - 1:
        mid = (lo + hi) // 2
        if times[mid] <= t:
            lo = mid
        else:
            hi = mid
    if lo == hi or abs(times[hi] - times[lo]) < 1e-10:
        return vals[lo]
    a = (t - times[lo]) / (times[hi] - times[lo])
    return vals[lo] * (1 - a) + vals[hi] * a


def _eval(pairs, jf, lw, fc_ratio, clamp_max=0.5):
    """Evaluate combined MSE for a parameter set with relaxed constraint."""
    jaw_sse, mc_sse = 0.0, 0.0
    jaw_capped, mc_gt_jaw = 0, 0
    for d in pairs:
        adj = max(0.0, d["mj"] - jf * d["mp"])
        lip_c = d["mt"] + lw * d["mp"]
        raw_mc = lip_c * d["mj"]
        cap = adj * fc_ratio
        mc = min(raw_mc, cap)
        mc = max(0.0, min(clamp_max, mc))
        jaw_sse += (adj - d["aj"]) ** 2
        mc_sse += (mc - d["amc"]) ** 2
        if raw_mc > cap:
            jaw_capped += 1
        if mc > adj:
            mc_gt_jaw += 1
    n = len(pairs)
    return {
        "jaw_mse": jaw_sse / n,
        "mc_mse": mc_sse / n,
        "combined": (jaw_sse + mc_sse) / n,
        "jaw_capped_pct": 100 * jaw_capped / n,
        "mc_gt_jaw_pct": 100 * mc_gt_jaw / n,
    }


def main():
    mha = unreal.load_asset(MHA_PATH)
    ark = unreal.load_asset(ARKIT_PATH)
    if not mha or not ark:
        unreal.log_error(f"{TAG} Cannot load sequences"); return

    mha_t, mha_j = [list(x) for x in _read(mha, MHA_JAW)]
    _, mha_p = _mean_group(mha, MHA_PURSE)
    _, mha_tw = _mean_group(mha, MHA_TOWARDS)
    ark_t, ark_j = [list(x) for x in _read(ark, "jawOpen")]
    ark_mc_d = _read(ark, "mouthClose")
    ark_pk_d = _read(ark, "mouthPucker")
    ark_mc = ark_mc_d[1] if ark_mc_d else [0.0] * len(ark_t)
    ark_pk = ark_pk_d[1] if ark_pk_d else [0.0] * len(ark_t)

    pairs = []
    for i in range(len(mha_t)):
        ta = mha_t[i] + OFFSET
        aj = _interp(ark_t, ark_j, ta)
        if aj is None:
            continue
        amc = _interp(ark_t, ark_mc, ta) or 0.0
        ap = _interp(ark_t, ark_pk, ta) or 0.0
        pairs.append({"i": i, "mj": mha_j[i], "mp": mha_p[i],
                       "mt": mha_tw[i], "aj": aj, "amc": amc, "ap": ap})

    unreal.log(f"{TAG} {len(pairs)} matched pairs")

    # ── Coarse 3D grid search ────────────────────────────────────────────
    best = {"combined": float('inf')}
    best_params = {}

    jf_range = [x * 0.05 for x in range(0, 31)]        # 0.00 - 1.50
    lw_range = [x * 0.05 for x in range(0, 21)]        # 0.00 - 1.00
    fc_range = [1.0, 1.25, 1.5, 2.0, 3.0, 999.0]      # constraint ratios

    for jf in jf_range:
        for lw in lw_range:
            for fc in fc_range:
                r = _eval(pairs, jf, lw, fc)
                if r["combined"] < best["combined"]:
                    best = r
                    best_params = {"jf": jf, "lw": lw, "fc": fc}

    unreal.log(f"{TAG} Coarse best: jf={best_params['jf']:.2f}, "
               f"lw={best_params['lw']:.2f}, fc={best_params['fc']}, "
               f"combined={best['combined']:.6f}")

    # ── Fine search around best ──────────────────────────────────────────
    jf_c, lw_c = best_params["jf"], best_params["lw"]
    fc_best = best_params["fc"]

    for jf_d in range(-10, 11):
        jf = max(0.0, jf_c + jf_d * 0.005)
        for lw_d in range(-10, 11):
            lw = max(0.0, min(1.0, lw_c + lw_d * 0.005))
            for fc in [fc_best * 0.8, fc_best * 0.9, fc_best,
                       fc_best * 1.1, fc_best * 1.2,
                       1.0, 1.25, 1.5, 2.0, 3.0, 999.0]:
                r = _eval(pairs, jf, lw, fc)
                if r["combined"] < best["combined"]:
                    best = r
                    best_params = {"jf": jf, "lw": lw, "fc": fc}

    unreal.log(f"{TAG} Fine best: jf={best_params['jf']:.4f}, "
               f"lw={best_params['lw']:.4f}, fc={best_params['fc']}, "
               f"combined={best['combined']:.6f}")

    # ── Also evaluate specific candidates ────────────────────────────────
    candidates = {
        "old_strict": {"jf": 0.75, "lw": 0.5, "fc": 1.0},
        "old_relaxed_1.5": {"jf": 0.75, "lw": 0.5, "fc": 1.5},
        "old_relaxed_2.0": {"jf": 0.75, "lw": 0.5, "fc": 2.0},
        "old_no_constraint": {"jf": 0.75, "lw": 0.5, "fc": 999.0},
        "cal_strict": {"jf": 0.155, "lw": 0.735, "fc": 1.0},
        "cal_relaxed_1.5": {"jf": 0.155, "lw": 0.735, "fc": 1.5},
        "high_jaw_high_lw_1.5": {"jf": 0.75, "lw": 0.735, "fc": 1.5},
        "high_jaw_high_lw_2.0": {"jf": 0.75, "lw": 0.735, "fc": 2.0},
        "moderate_1.5": {"jf": 0.45, "lw": 0.6, "fc": 1.5},
        "optimized": best_params,
    }

    results = {"matched_pairs": len(pairs), "candidates": {}}

    key_frames = [0, 276, 362, 725, 956, 1087]

    for name, p in candidates.items():
        metrics = _eval(pairs, p["jf"], p["lw"], p["fc"])
        diags = []
        for fi in key_frames:
            match = [d for d in pairs if d["i"] == fi]
            if not match:
                continue
            d = match[0]
            adj = max(0.0, d["mj"] - p["jf"] * d["mp"])
            lip_c = d["mt"] + p["lw"] * d["mp"]
            raw_mc = lip_c * d["mj"]
            cap = adj * p["fc"]
            mc = max(0.0, min(0.5, min(raw_mc, cap)))
            diags.append({
                "frame": fi,
                "our_jaw": round(adj, 4),
                "real_jaw": round(d["aj"], 4),
                "our_mc": round(mc, 4),
                "real_mc": round(d["amc"], 4),
            })
        results["candidates"][name] = {
            "params": {"jawFactor": p["jf"], "lipsPurseWeight": p["lw"],
                       "forwardConstraintRatio": p["fc"]},
            "metrics": {k: round(v, 6) for k, v in metrics.items()},
            "key_frames": diags,
        }
        unreal.log(f"{TAG} {name}: combined={metrics['combined']:.5f}, "
                   f"jaw={metrics['jaw_mse']:.5f}, mc={metrics['mc_mse']:.5f}")

    out = os.path.join(unreal.Paths.project_dir(), ".cursor", "arkit-remap",
                       "reports", "relaxed_constraint_calibration.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f:
        json.dump(results, f, indent=2)
    unreal.log(f"{TAG} Report: {out}")


main()
