"""P2: L/R convention verdicts from the asymmetry calibration take.

Blip take 20260814_DefaultSlate_3: Dylan performed, in order,
wink LEFT, look LEFT, smirk LEFT, mouth-slide LEFT, jaw LEFT, then the same
five actions on the RIGHT. The action order is the ground truth: for any
Left/Right-labeled curve pair, whichever label fires in the FIRST block is
the one Apple/MHA attaches to the performer's anatomical left.

This settles, per feature region:
  1. Apple ARKit naming: performer-relative or observer-relative?
  2. MHA stream: mirrored relative to the iPhone stream (mirrored video)?
  3. Solved-space: does each solved pair match the reference as-recorded or
     L/R-swapped?  (completes the loop through the P1 basis)

Outputs: v3/reports/p2_convention_verdicts.{json,md}

Run with Blender 5.2's python.exe (see p1_env.py).
"""

from __future__ import annotations

import json

import numpy as np

import p1_env

p1_env.bootstrap()

from scipy.optimize import lsq_linear  # noqa: E402

from riglogic_harness import RigHarness  # noqa: E402
from solve_take import FPS, best_lag, load_iphone, load_mha  # noqa: E402

IPHONE_CSV = (
    r"C:\Users\DYLPC\Documents\Blip\20260814_DefaultSlate_3"
    r"\DefaultSlate_3_iPhone_cal.csv"
)
MHA_JSON = p1_env.DATA_DIR / "samples" / "mirrortest_mha_curves.json"
MIN_EVENT = 0.15  # laterality must exceed this to count as a real event

# (region, left-labeled signal, right-labeled signal) — signals may sum curves
IPHONE_PAIRS = [
    ("wink", ["EyeBlinkLeft"], ["EyeBlinkRight"]),
    ("gaze", ["EyeLookOutLeft", "EyeLookInRight"], ["EyeLookInLeft", "EyeLookOutRight"]),
    ("smirk", ["MouthSmileLeft"], ["MouthSmileRight"]),
    ("mouthSlide", ["MouthLeft"], ["MouthRight"]),
    ("jawShift", ["JawLeft"], ["JawRight"]),
]
MHA_PAIRS = [
    ("wink", ["CTRL_expressions_eyeBlinkL"], ["CTRL_expressions_eyeBlinkR"]),
    (
        "gaze",
        ["CTRL_expressions_eyeLookLeftL", "CTRL_expressions_eyeLookLeftR"],
        ["CTRL_expressions_eyeLookRightL", "CTRL_expressions_eyeLookRightR"],
    ),
    (
        "smirk",
        ["CTRL_expressions_mouthCornerPullL"],
        ["CTRL_expressions_mouthCornerPullR"],
    ),
    ("mouthSlide", ["CTRL_expressions_mouthLeft"], ["CTRL_expressions_mouthRight"]),
    ("jawShift", ["CTRL_expressions_jawLeft"], ["CTRL_expressions_jawRight"]),
]
SOLVED_PAIRS = [
    ("wink", "EyeBlinkLeft", "EyeBlinkRight"),
    ("gaze", "EyeLookOutLeft", "EyeLookInLeft"),
    ("smirk", "MouthSmileLeft", "MouthSmileRight"),
    ("mouthSlide", "MouthLeft", "MouthRight"),
    ("jawShift", "JawLeft", "JawRight"),
]


def first_event_order(left: np.ndarray, right: np.ndarray) -> dict:
    """Which side-labeled signal peaks first? Uses the laterality difference so
    symmetric motion (both-eye blinks etc.) can't fake an event."""
    lat_l, lat_r = left - right, right - left
    t_l, t_r = int(np.argmax(lat_l)), int(np.argmax(lat_r))
    m_l, m_r = float(lat_l[t_l]), float(lat_r[t_r])
    if m_l < MIN_EVENT or m_r < MIN_EVENT:
        return {"verdict": "no clear one-sided events", "peakLeft": round(m_l, 3), "peakRight": round(m_r, 3)}
    return {
        "leftLabelPeakFrame": t_l,
        "rightLabelPeakFrame": t_r,
        "leftLabelPeak": round(m_l, 3),
        "rightLabelPeak": round(m_r, 3),
        "firstBlockLabel": "Left" if t_l < t_r else "Right",
    }


def summed(curves: dict, names: list[str], n: int) -> np.ndarray:
    out = np.zeros(n)
    for nm in names:
        if nm in curves:
            out += curves[nm]
    return out


def main() -> None:
    grid, mha = load_mha(MHA_JSON)
    it, iphone = load_iphone(IPHONE_CSV)
    n = len(grid)
    iph = {k: np.interp(grid, it, v) for k, v in iphone.items()}

    # align on the mirror-invariant symmetric blink sum
    blink_i = iph["EyeBlinkLeft"] + iph["EyeBlinkRight"]
    blink_m = summed(mha, ["CTRL_expressions_eyeBlinkL", "CTRL_expressions_eyeBlinkR"], n)
    lag, corr = best_lag(blink_m, blink_i, 180)
    print(f"alignment (blink sum): lag {lag}f, corr {corr:.3f}")

    def shift(v: np.ndarray) -> np.ndarray:
        out = np.full(n, 0.0)
        if lag >= 0:
            out[: n - lag] = v[lag:]
        else:
            out[-lag:] = v[: n + lag]
        return out

    iph = {k: shift(v) for k, v in iph.items()}

    # ---- 1. absolute conventions from event order ----
    iphone_events = {}
    for region, ln, rn in IPHONE_PAIRS:
        iphone_events[region] = first_event_order(summed(iph, ln, n), summed(iph, rn, n))
    mha_events = {}
    for region, ln, rn in MHA_PAIRS:
        missing = [x for x in ln + rn if x not in mha]
        if missing:
            mha_events[region] = {"verdict": f"missing controls {missing}"}
            continue
        mha_events[region] = first_event_order(summed(mha, ln, n), summed(mha, rn, n))

    # ---- 2. solve the take, solved-space pair correlations ----
    rig = RigHarness()
    npz = np.load(p1_env.DATA_DIR / "arkit_basis_joints.npz")
    B = npz["B"].astype(np.float64)
    baseline = npz["baseline_joints"].astype(np.float64)
    arkit_names = [str(s) for s in npz["arkit_names"]]
    A = B.T
    Q, R = np.linalg.qr(A)

    expr = {k: v for k, v in mha.items() if k.startswith("CTRL_expressions_")}
    index_map, _ = rig.resolve(expr.keys())
    ctrl = np.zeros((n, rig.n_raw))
    for name, vals in expr.items():
        idx = index_map.get(name)
        if idx is not None:
            ctrl[:, idx] = np.clip(vals, 0.0, 1.0)
    W = np.zeros((n, len(arkit_names)))
    for f in range(n):
        joints, _ = rig.evaluate(ctrl[f])
        qd = Q.T @ (joints - baseline)
        W[f] = lsq_linear(R, qd, bounds=(0.0, 1.0), method="bvls").x
        if f % 400 == 0:
            print(f"  solve {f}/{n}")

    def col(name):
        return W[:, arkit_names.index(name)]

    solved_events = {}
    for region, ln_, rn_ in SOLVED_PAIRS:
        solved_events[region] = first_event_order(col(ln_), col(rn_))

    def corr2(a, b):
        if a.std() < 1e-6 or b.std() < 1e-6:
            return None
        return round(float(np.corrcoef(a, b)[0, 1]), 3)

    solved_vs_iphone = {}
    for region, ln_, rn_ in SOLVED_PAIRS:
        if ln_ not in iph:
            continue
        solved_vs_iphone[region] = {
            "sameLabel": corr2(col(ln_), iph[ln_]),
            "swappedLabel": corr2(col(ln_), iph[rn_ if not ln_.startswith("EyeLookOut") else "EyeLookOutRight"]),
        }

    # ---- verdicts ----
    def block_label(ev):
        return ev.get("firstBlockLabel")

    verdicts = {}
    for region in ("wink", "gaze", "smirk", "mouthSlide", "jawShift"):
        ie, me, se = iphone_events[region], mha_events[region], solved_events[region]
        row = {}
        if block_label(ie):
            row["appleNaming"] = (
                "performer-relative" if block_label(ie) == "Left" else "observer-relative"
            )
        if block_label(ie) and block_label(me):
            row["mhaMirroredVsIphone"] = block_label(me) != block_label(ie)
        if block_label(se):
            row["solvedFirstBlockLabel"] = block_label(se)
        verdicts[region] = row

    report = {
        "take": "20260814_DefaultSlate_3",
        "actionOrder": "L block then R block: wink, look, smirk, mouth-slide, jaw-shift",
        "alignment": {"lagFrames": lag, "blinkSumCorr": round(corr, 3)},
        "iphoneEvents": iphone_events,
        "mhaEvents": mha_events,
        "solvedEvents": solved_events,
        "solvedVsIphoneCorr": solved_vs_iphone,
        "verdicts": verdicts,
    }
    (p1_env.REPORTS_DIR / "p2_convention_verdicts.json").write_text(json.dumps(report, indent=2))

    lines = [
        "# P2 convention verdicts — asymmetry calibration take",
        "",
        "Ground truth: left-side actions performed first. A pair's Left-labeled",
        "curve peaking in the first block means that label is performer-left.",
        "",
        "| region | Apple naming | iPhone 1st block | MHA 1st block | mirrored? | solved 1st block |",
        "|---|---|---|---|---|---|",
    ]
    for region, v in verdicts.items():
        lines.append(
            f"| {region} | {v.get('appleNaming', '?')} | "
            f"{block_label(iphone_events[region]) or '—'} | "
            f"{block_label(mha_events[region]) or '—'} | "
            f"{v.get('mhaMirroredVsIphone', '?')} | "
            f"{v.get('solvedFirstBlockLabel', '—')} |"
        )
    (p1_env.REPORTS_DIR / "p2_convention_verdicts.md").write_text("\n".join(lines) + "\n")

    print(json.dumps(verdicts, indent=2))


if __name__ == "__main__":
    main()
