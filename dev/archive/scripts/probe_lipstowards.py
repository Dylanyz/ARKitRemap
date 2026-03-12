"""Probe LipsTowards and LipsPurse curves on AS_MP_VecDemo1-allkeys.

Reads curve data and computes per-curve statistics plus cross-curve
correlations to determine the best MouthClose derivation formula.
Writes results to .cursor/arkit-remap/data/probe_lipstowards_results.json
"""

import unreal
import json
import os
import math

RCT_FLOAT = unreal.RawCurveTrackTypes.RCT_FLOAT
LIB = unreal.AnimationLibrary
TAG = "[LipsTowards Probe]"

ANIM_PATH = "/Game/3_FaceAnims/VEC_MHA/AgenticPy/AS_MP_VecDemo1-allkeys"

LIPS_TOWARDS = [
    "ctrl_expressions_mouthlipstowardsul",
    "ctrl_expressions_mouthlipstowardsur",
    "ctrl_expressions_mouthlipstowardsdl",
    "ctrl_expressions_mouthlipstowardsdr",
]

LIPS_PURSE = [
    "ctrl_expressions_mouthlipspurseul",
    "ctrl_expressions_mouthlipspurseur",
    "ctrl_expressions_mouthlipspursedl",
    "ctrl_expressions_mouthlipspursedr",
]

JAW_OPEN = "ctrl_expressions_jawopen"

LIPS_TOGETHER = [
    "ctrl_expressions_mouth_lips_together_ul",
    "ctrl_expressions_mouth_lips_together_ur",
    "ctrl_expressions_mouth_lips_together_dl",
    "ctrl_expressions_mouth_lips_together_dr",
]


def _stats(values):
    if not values:
        return {"count": 0}
    n = len(values)
    mn = min(values)
    mx = max(values)
    mean = sum(values) / n
    var = sum((v - mean) ** 2 for v in values) / n
    std = math.sqrt(var)
    nonzero = sum(1 for v in values if abs(v) > 1e-6)
    return {
        "count": n,
        "min": round(mn, 6),
        "max": round(mx, 6),
        "mean": round(mean, 6),
        "std": round(std, 6),
        "nonzeroFrames": nonzero,
        "nonzeroPct": round(100.0 * nonzero / n, 2),
    }


def _pearson(a, b):
    """Pearson correlation coefficient between two lists of equal length."""
    n = len(a)
    if n == 0:
        return 0.0
    mean_a = sum(a) / n
    mean_b = sum(b) / n
    cov = sum((a[i] - mean_a) * (b[i] - mean_b) for i in range(n))
    var_a = sum((v - mean_a) ** 2 for v in a)
    var_b = sum((v - mean_b) ** 2 for v in b)
    denom = math.sqrt(var_a * var_b)
    if denom < 1e-12:
        return 0.0
    return round(cov / denom, 6)


def _read_curve(seq, name):
    if not LIB.does_curve_exist(seq, name, RCT_FLOAT):
        return None
    times, values = LIB.get_float_keys(seq, name)
    return list(times), list(values)


def main():
    seq = unreal.load_asset(ANIM_PATH)
    if seq is None:
        unreal.log_error(f"{TAG} Could not load: {ANIM_PATH}")
        return
    unreal.log(f"{TAG} Loaded: {ANIM_PATH}")

    results = {
        "animPath": ANIM_PATH,
        "curves": {},
        "correlations": {},
        "candidateFormulas": {},
        "highLipsTowardsFrames": [],
    }

    all_data = {}

    for group_name, curve_list in [
        ("lipsTowards", LIPS_TOWARDS),
        ("lipsPurse", LIPS_PURSE),
        ("lipsTogether", LIPS_TOGETHER),
    ]:
        for curve_name in curve_list:
            data = _read_curve(seq, curve_name)
            if data is None:
                results["curves"][curve_name] = {"exists": False}
                unreal.log(f"{TAG} {curve_name}: NOT FOUND")
            else:
                times, values = data
                all_data[curve_name] = values
                s = _stats(values)
                s["exists"] = True
                s["group"] = group_name
                results["curves"][curve_name] = s
                unreal.log(f"{TAG} {curve_name}: min={s['min']}, max={s['max']}, "
                           f"mean={s['mean']}, std={s['std']}, "
                           f"nonzero={s['nonzeroFrames']}/{s['count']}")

    jaw_data = _read_curve(seq, JAW_OPEN)
    if jaw_data is None:
        results["curves"][JAW_OPEN] = {"exists": False}
        unreal.log_error(f"{TAG} {JAW_OPEN}: NOT FOUND")
    else:
        times, values = jaw_data
        all_data[JAW_OPEN] = values
        s = _stats(values)
        s["exists"] = True
        s["group"] = "jawOpen"
        results["curves"][JAW_OPEN] = s
        unreal.log(f"{TAG} {JAW_OPEN}: min={s['min']}, max={s['max']}, "
                   f"mean={s['mean']}, nonzero={s['nonzeroFrames']}/{s['count']}")

    # Cross-correlations between LipsTowards variants
    lt_keys = [k for k in LIPS_TOWARDS if k in all_data]
    for i in range(len(lt_keys)):
        for j in range(i + 1, len(lt_keys)):
            r = _pearson(all_data[lt_keys[i]], all_data[lt_keys[j]])
            label = f"{lt_keys[i].split('mouthlipstowards')[1]} vs {lt_keys[j].split('mouthlipstowards')[1]}"
            results["correlations"][label] = r
            unreal.log(f"{TAG} Corr({label}) = {r}")

    # Correlation of each LipsTowards with JawOpen
    if JAW_OPEN in all_data:
        for k in lt_keys:
            suffix = k.split("mouthlipstowards")[1]
            r = _pearson(all_data[k], all_data[JAW_OPEN])
            results["correlations"][f"lipsTowards_{suffix} vs jawOpen"] = r
            unreal.log(f"{TAG} Corr(lipsTowards_{suffix} vs jawOpen) = {r}")

    # Correlation of each LipsPurse with JawOpen
    lp_keys = [k for k in LIPS_PURSE if k in all_data]
    if JAW_OPEN in all_data:
        for k in lp_keys:
            suffix = k.split("mouthlipspurse")[1]
            r = _pearson(all_data[k], all_data[JAW_OPEN])
            results["correlations"][f"lipsPurse_{suffix} vs jawOpen"] = r
            unreal.log(f"{TAG} Corr(lipsPurse_{suffix} vs jawOpen) = {r}")

    # Candidate formula evaluation
    if lt_keys and JAW_OPEN in all_data:
        jaw = all_data[JAW_OPEN]
        n = len(jaw)

        lt_mean_per_frame = []
        for i in range(n):
            vals = [all_data[k][i] for k in lt_keys]
            lt_mean_per_frame.append(sum(vals) / len(vals))

        # Formula A: MouthClose = scale * mean(LipsTowards)
        formula_a = list(lt_mean_per_frame)
        results["candidateFormulas"]["A_lipsTowardsMean"] = _stats(formula_a)

        # Formula B: MouthClose = scale * mean(LipsTowards) * JawOpen
        formula_b = [lt_mean_per_frame[i] * jaw[i] for i in range(n)]
        results["candidateFormulas"]["B_lipsTowardsMean_x_jawOpen"] = _stats(formula_b)

        # Formula C: weighted combo LipsTowards + LipsPurse
        if lp_keys:
            lp_mean_per_frame = []
            for i in range(n):
                vals = [all_data[k][i] for k in lp_keys]
                lp_mean_per_frame.append(sum(vals) / len(vals))

            formula_c = [0.7 * lt_mean_per_frame[i] + 0.3 * lp_mean_per_frame[i]
                         for i in range(n)]
            results["candidateFormulas"]["C_weighted_LT07_LP03"] = _stats(formula_c)

            formula_c2 = [(0.7 * lt_mean_per_frame[i] + 0.3 * lp_mean_per_frame[i]) * jaw[i]
                          for i in range(n)]
            results["candidateFormulas"]["C2_weighted_LT07_LP03_x_jawOpen"] = _stats(formula_c2)

        # Correlation between formula outputs and JawOpen
        results["correlations"]["formulaA_vs_jawOpen"] = _pearson(formula_a, jaw)
        results["correlations"]["formulaB_vs_jawOpen"] = _pearson(formula_b, jaw)

        # Find frames where LipsTowards is high (>0.1) to check if jaw is open
        high_lt_frames = []
        for i in range(n):
            if lt_mean_per_frame[i] > 0.1:
                high_lt_frames.append({
                    "frame": i,
                    "lipsTowardsMean": round(lt_mean_per_frame[i], 4),
                    "jawOpen": round(jaw[i], 4),
                })
        results["highLipsTowardsFrames"] = high_lt_frames[:50]
        results["highLipsTowardsFrameCount"] = len(high_lt_frames)
        unreal.log(f"{TAG} Frames with high LipsTowards (>0.1): {len(high_lt_frames)}")

    # Write results
    project_dir = unreal.Paths.project_dir()
    out_dir = os.path.join(project_dir, ".cursor", "arkit-remap", "data")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "probe_lipstowards_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    unreal.log(f"{TAG} Results written to: {out_path}")
    unreal.log(f"{TAG} === Probe complete ===")


main()
