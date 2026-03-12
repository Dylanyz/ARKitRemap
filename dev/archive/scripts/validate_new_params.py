"""Run the remap on allkeys3 with updated params and validate key frames.

Compares the output against the matched ARKit reference using the
definitive alignment (offset = 345.4s).
"""
import unreal
import json
import os
import sys

TAG = "[Validate]"
LIB = unreal.AnimationLibrary
RCT_FLOAT = unreal.RawCurveTrackTypes.RCT_FLOAT

MHA_PATH = "/Game/3_FaceAnims/VEC_MHA/AgenticPy/AS_MP_VecDemo1-allkeys3"
ARKIT_REF_PATH = "/Game/3_FaceAnims/VecnaArkitFace/Vec-ARKITBAKED-T34_60fps-02"
OFFSET = 345.4

script_dir = os.path.join(unreal.Paths.project_dir(),
                          ".cursor", "arkit-remap", "scripts")
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

import arkit_remap


def _read(seq, name):
    for n in [name, name.lower()]:
        if LIB.does_curve_exist(seq, n, RCT_FLOAT):
            return list(LIB.get_float_keys(seq, n)[0]), list(LIB.get_float_keys(seq, n)[1])
    return None


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


def main():
    # ── Run the remap ────────────────────────────────────────────────────
    unreal.log(f"{TAG} Running remap on {MHA_PATH}...")
    arkit_remap.main(asset_paths=[MHA_PATH])

    # ── Load the output ──────────────────────────────────────────────────
    out_path = MHA_PATH + "_ARKit"
    out_seq = unreal.load_asset(out_path)
    if not out_seq:
        unreal.log_error(f"{TAG} Cannot load output: {out_path}")
        return

    out_jaw = _read(out_seq, "jawOpen")
    out_mc = _read(out_seq, "mouthClose")
    out_pk = _read(out_seq, "mouthPucker")

    if not out_jaw:
        unreal.log_error(f"{TAG} No jawOpen on output"); return

    out_t = out_jaw[0]
    n_frames = len(out_t)
    unreal.log(f"{TAG} Output: {n_frames} frames, {out_t[-1]:.2f}s")

    # ── Load ARKit reference for comparison ──────────────────────────────
    ref = unreal.load_asset(ARKIT_REF_PATH)
    ref_jaw = _read(ref, "jawOpen")
    ref_mc = _read(ref, "mouthClose")
    ref_pk = _read(ref, "mouthPucker")

    # ── Key frame analysis ───────────────────────────────────────────────
    key_frames = [0, 276, 362, 725, 956, 1087, 1200]
    diags = []

    for fi in key_frames:
        if fi >= n_frames:
            continue
        t_mha = out_t[fi]
        t_ark = t_mha + OFFSET

        d = {
            "frame": fi,
            "our_jawOpen": round(out_jaw[1][fi], 4),
            "our_mouthClose": round(out_mc[1][fi], 4) if out_mc else None,
            "our_mouthPucker": round(out_pk[1][fi], 4) if out_pk else None,
        }

        if ref_jaw:
            d["ref_jawOpen"] = round(_interp(ref_jaw[0], ref_jaw[1], t_ark) or 0, 4)
        if ref_mc:
            d["ref_mouthClose"] = round(_interp(ref_mc[0], ref_mc[1], t_ark) or 0, 4)
        if ref_pk:
            d["ref_mouthPucker"] = round(_interp(ref_pk[0], ref_pk[1], t_ark) or 0, 4)

        diags.append(d)
        unreal.log(f"{TAG} Frame {fi}: jaw={d['our_jawOpen']:.3f} "
                   f"(ref={d.get('ref_jawOpen','?')}), "
                   f"mc={d.get('our_mouthClose','?'):.3f} "
                   f"(ref={d.get('ref_mouthClose','?')})")

    # ── Global metrics ───────────────────────────────────────────────────
    if out_mc:
        mc_vals = out_mc[1]
        jaw_vals = out_jaw[1]
        mc_gt_jaw = sum(1 for i in range(n_frames) if mc_vals[i] > jaw_vals[i])
        clipping = sum(1 for i in range(n_frames)
                       if mc_vals[i] > jaw_vals[i] * 1.51)
        mc_max = max(mc_vals)
        mc_mean = sum(mc_vals) / n_frames

        unreal.log(f"{TAG} MouthClose > JawOpen: {mc_gt_jaw}/{n_frames} "
                   f"({100*mc_gt_jaw/n_frames:.1f}%)")
        unreal.log(f"{TAG} Clipping (mc > 1.51x jaw): {clipping}/{n_frames}")
        unreal.log(f"{TAG} MouthClose range: [{min(mc_vals):.4f}, {mc_max:.4f}], "
                   f"mean={mc_mean:.4f}")
    else:
        mc_gt_jaw = 0
        clipping = 0

    report = {
        "source": MHA_PATH,
        "output": out_path,
        "reference": ARKIT_REF_PATH,
        "offset_seconds": OFFSET,
        "frames": n_frames,
        "key_frames": diags,
        "mc_gt_jaw_frames": mc_gt_jaw,
        "mc_gt_jaw_pct": round(100 * mc_gt_jaw / n_frames, 1) if n_frames else 0,
        "hard_clipping_frames": clipping,
    }

    out_file = os.path.join(unreal.Paths.project_dir(), ".cursor", "arkit-remap",
                            "reports", "validation_new_params.json")
    os.makedirs(os.path.dirname(out_file), exist_ok=True)
    with open(out_file, "w") as f:
        json.dump(report, f, indent=2)
    unreal.log(f"{TAG} Report: {out_file}")


main()
