"""Compare old vs calibrated params using the definitive alignment.

Also checks how often real ARKit has mouthClose > jawOpen (forward
constraint violation) to assess whether the constraint is too strict.
"""
import unreal
import json
import os

LIB = unreal.AnimationLibrary
RCT_FLOAT = unreal.RawCurveTrackTypes.RCT_FLOAT
TAG = "[ParamCmp]"

MHA_PATH = "/Game/3_FaceAnims/VEC_MHA/AgenticPy/AS_MP_VecDemo1-allkeys"
ARKIT_PATH = "/Game/3_FaceAnims/VecnaArkitFace/Vec-ARKITBAKED-T34_60fps-02"
OFFSET = 345.4

PARAM_SETS = {
    "old_hand_tuned": {"jawFactor": 0.75, "lipsPurseWeight": 0.5, "puckerFactor": 0.0},
    "new_calibrated": {"jawFactor": 0.155, "lipsPurseWeight": 0.735, "puckerFactor": 0.0},
    "hybrid_high_jaw_high_weight": {"jawFactor": 0.75, "lipsPurseWeight": 0.735, "puckerFactor": 0.0},
    "hybrid_moderate": {"jawFactor": 0.45, "lipsPurseWeight": 0.6, "puckerFactor": 0.0},
}

MHA_JAW = "ctrl_expressions_jawopen"
MHA_PURSE = ["ctrl_expressions_mouthlipspurseul", "ctrl_expressions_mouthlipspurseur",
             "ctrl_expressions_mouthlipspursedl", "ctrl_expressions_mouthlipspursedr"]
MHA_TOWARDS = ["ctrl_expressions_mouthlipstowardsul", "ctrl_expressions_mouthlipstowardsur",
               "ctrl_expressions_mouthlipstowardsdl", "ctrl_expressions_mouthlipstowardsdr"]


def _read(seq, name):
    for n in [name, name.lower()]:
        if LIB.does_curve_exist(seq, n, RCT_FLOAT):
            return LIB.get_float_keys(seq, n)
    return None


def _mean_group(seq, names):
    all_d = [_read(seq, n) for n in names]
    all_d = [(t, v) for x in all_d if x for t, v in [x]]
    if not all_d:
        return None, None
    n = max(len(v) for _, v in all_d)
    times = next((t for t, v in all_d if len(t) == n), all_d[0][0])
    means = [0.0] * n
    for _, v in all_d:
        for i in range(min(len(v), n)):
            means[i] += v[i]
    return list(times), [m / len(all_d) for m in means]


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


def _eval_params(pairs, p, clamp_max=0.5):
    jf, lw, pf = p["jawFactor"], p["lipsPurseWeight"], p["puckerFactor"]
    jaw_sse, mc_sse = 0.0, 0.0
    mc_gt_jaw = 0
    jaw_capped = 0
    for d in pairs:
        adj = max(0.0, d["mj"] - jf * d["mp"])
        lip_c = d["mt"] + lw * d["mp"]
        raw_mc = lip_c * d["mj"]
        eff_cap = max(0.0, adj - pf * d["ap"])
        mc = max(0.0, min(clamp_max, min(raw_mc, eff_cap)))
        jaw_sse += (adj - d["aj"]) ** 2
        mc_sse += (mc - d["amc"]) ** 2
        if raw_mc > eff_cap:
            jaw_capped += 1
        if mc > adj:
            mc_gt_jaw += 1
    n = len(pairs)
    return {
        "jawOpen_MSE": round(jaw_sse / n, 6),
        "mouthClose_MSE": round(mc_sse / n, 6),
        "combined_MSE": round((jaw_sse + mc_sse) / n, 6),
        "jaw_capped_pct": round(100 * jaw_capped / n, 1),
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
    ark_mc = list(ark_mc_d[1]) if ark_mc_d else [0.0] * len(ark_t)
    ark_pk = list(ark_pk_d[1]) if ark_pk_d else [0.0] * len(ark_t)
    ark_t = list(ark_t)

    pairs = []
    for i in range(len(mha_t)):
        ta = mha_t[i] + OFFSET
        aj = _interp(ark_t, ark_j, ta)
        if aj is None: continue
        amc = _interp(ark_t, ark_mc, ta) or 0.0
        ap = _interp(ark_t, ark_pk, ta) or 0.0
        pairs.append({"i": i, "mj": mha_j[i], "mp": mha_p[i], "mt": mha_tw[i],
                       "aj": aj, "amc": amc, "ap": ap})

    unreal.log(f"{TAG} {len(pairs)} matched pairs")

    # Real ARKit: how often mouthClose > jawOpen?
    real_mc_gt_jaw = sum(1 for d in pairs if d["amc"] > d["aj"])
    unreal.log(f"{TAG} Real ARKit: mouthClose > jawOpen in "
               f"{real_mc_gt_jaw}/{len(pairs)} frames "
               f"({100*real_mc_gt_jaw/len(pairs):.1f}%)")

    results = {"matched_pairs": len(pairs),
               "real_arkit_mouthClose_gt_jawOpen_pct":
                   round(100 * real_mc_gt_jaw / len(pairs), 1)}

    for name, params in PARAM_SETS.items():
        metrics = _eval_params(pairs, params)
        results[name] = {"params": params, "metrics": metrics}
        unreal.log(f"{TAG} {name}: jawMSE={metrics['jawOpen_MSE']:.4f}, "
                   f"mcMSE={metrics['mouthClose_MSE']:.4f}, "
                   f"combined={metrics['combined_MSE']:.4f}")

    # Key frame diagnostics for each param set
    key_frames = [0, 276, 362, 725, 956, 1087]
    for name, params in PARAM_SETS.items():
        jf, lw, pf = params["jawFactor"], params["lipsPurseWeight"], params["puckerFactor"]
        diags = []
        for fi in key_frames:
            match = [d for d in pairs if d["i"] == fi]
            if not match: continue
            d = match[0]
            adj = max(0.0, d["mj"] - jf * d["mp"])
            lip_c = d["mt"] + lw * d["mp"]
            raw_mc = lip_c * d["mj"]
            eff_cap = max(0.0, adj - pf * d["ap"])
            mc = max(0.0, min(0.5, min(raw_mc, eff_cap)))
            diags.append({
                "frame": fi,
                "our_jaw": round(adj, 4), "real_jaw": round(d["aj"], 4),
                "our_mc": round(mc, 4), "real_mc": round(d["amc"], 4),
                "real_mc_gt_jaw": d["amc"] > d["aj"],
            })
        results[name]["key_frames"] = diags

    out = os.path.join(unreal.Paths.project_dir(), ".cursor", "arkit-remap",
                       "reports", "param_comparison.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f:
        json.dump(results, f, indent=2)
    unreal.log(f"{TAG} Report: {out}")


main()
