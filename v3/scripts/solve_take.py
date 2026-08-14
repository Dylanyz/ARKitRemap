"""P2: solve a real MHA take frame-by-frame and score it against iPhone ARKit.

Ground truth pairing (Blip take 20260814_DefaultSlate_2): the iPhone recorded
ARKit blendshapes (calibrated CSV) and mono video simultaneously; the video
was processed through MetaHuman Animator into AS_mp_arkittest. Same
performance, two capture paths — so the inverse solve of the MHA curves can be
compared 1:1 against what ARKit itself said the face was doing.

Pipeline per frame: MHA controls c -> RigLogic joint delta d -> BVLS solve
w in [0,1]^51 against the P1 basis. Alignment between the two streams is
recovered by cross-correlating JawOpen. Speed: the 7830-dim LSQ is reduced
once via QR (A = QR -> solve R w ~ Q^T d), making per-frame BVLS 51x51.

Outputs:
    v3/data/samples/arkittest_solved_weights.npz
    v3/reports/p2_take_comparison.{json,md}

Run with Blender 5.2's python.exe (see p1_env.py).
"""

from __future__ import annotations

import csv
import json

import numpy as np

import p1_env

p1_env.bootstrap()

from scipy.optimize import lsq_linear  # noqa: E402

from riglogic_harness import RigHarness  # noqa: E402

FPS = 59.94
IPHONE_CSV = (
    r"C:\Users\DYLPC\Documents\Blip\20260814_DefaultSlate_2"
    r"\DefaultSlate_2_iPhone_cal.csv"
)
MHA_JSON = p1_env.DATA_DIR / "samples" / "arkittest_mha_curves_allkeys.json"
MAX_LAG_FRAMES = 180  # +/- 3 s search window


def mirror_name(name: str) -> str:
    """Swap the Left/Right suffix of an ARKit curve name."""
    if name.endswith("Left"):
        return name[:-4] + "Right"
    if name.endswith("Right"):
        return name[:-5] + "Left"
    return name


def parse_timecode(tc: str) -> float:
    """HH:MM:SS:FF.fff (60 fps timecode) -> seconds."""
    h, m, s, f = tc.split(":")
    return int(h) * 3600 + int(m) * 60 + int(s) + float(f) / 60.0


def load_iphone(path: str) -> tuple[np.ndarray, dict[str, np.ndarray]]:
    with open(path, newline="") as fh:
        rows = list(csv.reader(fh))
    header, data = rows[0], rows[1:]
    names = header[2:]  # Timecode, BlendshapeCount, then shapes
    t = np.array([parse_timecode(r[0]) for r in data])
    t -= t[0]
    vals = np.array([[float(x) for x in r[2 : 2 + len(names)]] for r in data])
    return t, {n: vals[:, i] for i, n in enumerate(names)}


def load_mha(path) -> tuple[np.ndarray, dict[str, np.ndarray]]:
    """Resample the sparse-keyed curves onto a uniform FPS grid."""
    doc = json.loads(path.read_text())
    n_frames = doc["metadata"]["numFrames"]
    grid = np.arange(n_frames) / FPS
    curves = {}
    for name, c in doc["curves"].items():
        t, v = np.array(c["t"]), np.array(c["v"])
        curves[name] = np.interp(grid, t, v) if len(t) > 1 else np.full(n_frames, v[0] if len(v) else 0.0)
    return grid, curves


def best_lag(a: np.ndarray, b: np.ndarray, max_lag: int) -> tuple[int, float]:
    """Lag (frames) maximizing correlation of a vs b shifted; positive lag
    means b starts later than a."""
    best = (0, -np.inf)
    a = a - a.mean()
    for lag in range(-max_lag, max_lag + 1):
        if lag >= 0:
            x, y = a[: len(a) - lag], b[lag:len(a)]
        else:
            x, y = a[-lag:], b[: len(a) + lag]
        m = min(len(x), len(y))
        if m < 100:
            continue
        y = y[:m] - b.mean()
        denom = np.linalg.norm(x[:m]) * np.linalg.norm(y)
        c = float(x[:m] @ y / denom) if denom > 0 else -np.inf
        if c > best[1]:
            best = (lag, c)
    return best


def main() -> None:
    rig = RigHarness()
    npz = np.load(p1_env.DATA_DIR / "arkit_basis_joints.npz")
    B = npz["B"].astype(np.float64)
    baseline = npz["baseline_joints"].astype(np.float64)
    arkit_names = [str(s) for s in npz["arkit_names"]]

    A = B.T  # (7830, 51)
    Q, R = np.linalg.qr(A)  # reduce once; per-frame BVLS is then 51x51

    grid, mha = load_mha(MHA_JSON)
    it, iphone = load_iphone(IPHONE_CSV)

    expr = {n: v for n, v in mha.items() if n.startswith("CTRL_expressions_")}
    index_map, unmatched = rig.resolve(expr.keys())
    n_frames = len(grid)

    # frame-major control matrix
    ctrl = np.zeros((n_frames, rig.n_raw))
    for name, vals in expr.items():
        idx = index_map.get(name)
        if idx is not None:
            ctrl[:, idx] = np.clip(vals, 0.0, 1.0)

    W = np.zeros((n_frames, len(arkit_names)))
    resid = np.zeros(n_frames)
    for f in range(n_frames):
        joints, _ = rig.evaluate(ctrl[f])
        d = joints - baseline
        qd = Q.T @ d
        res = lsq_linear(R, qd, bounds=(0.0, 1.0), method="bvls")
        W[f] = res.x
        dn = np.linalg.norm(d)
        resid[f] = np.linalg.norm(A @ res.x - d) / dn if dn > 1e-9 else 0.0
        if f % 200 == 0:
            print(f"  frame {f}/{n_frames}")

    # ---- align via JawOpen ----
    j = arkit_names.index("JawOpen")
    iphone_on_grid = {
        n: np.interp(grid, it, v, left=np.nan, right=np.nan) for n, v in iphone.items()
    }
    lag, corr = best_lag(W[:, j], np.nan_to_num(iphone_on_grid["JawOpen"]), MAX_LAG_FRAMES)
    print(f"alignment: lag {lag} frames ({lag / FPS:.3f} s), JawOpen corr {corr:.4f}")

    def shifted(v: np.ndarray) -> np.ndarray:
        out = np.full(n_frames, np.nan)
        if lag >= 0:
            out[: n_frames - lag] = v[lag:]
        else:
            out[-lag:] = v[: n_frames + lag]
        return out

    # ---- per-curve metrics, against the reference as recorded AND with the
    # iPhone's Left/Right swapped. The Blip mono video is saved mirrored
    # (selfie convention), so the MHA solve is a mirror image of the ARKit
    # stream: gaze curves anti-correlate as recorded (+0.98 against their
    # swapped partners) and the smile asymmetry signal anti-correlates at
    # -0.80. The mirrored reference is the anatomically meaningful score. ----
    def score(swap: bool) -> dict:
        metrics = {}
        for k, name in enumerate(arkit_names):
            src = mirror_name(name) if swap else name
            ref = shifted(iphone_on_grid.get(src, np.full(n_frames, np.nan)))
            ok = ~np.isnan(ref)
            r_, s = ref[ok], W[ok, k]
            both_active = (r_.max() > 0.05) or (s.max() > 0.05)
            cc = float(np.corrcoef(s, r_)[0, 1]) if r_.std() > 1e-6 and s.std() > 1e-6 else None
            metrics[name] = {
                "pearson": None if cc is None or np.isnan(cc) else round(cc, 4),
                "rmse": round(float(np.sqrt(np.mean((s - r_) ** 2))), 4),
                "solvedP95": round(float(np.percentile(s, 95)), 4),
                "iphoneP95": round(float(np.percentile(r_, 95)), 4),
                "solvedMax": round(float(s.max()), 4),
                "iphoneMax": round(float(r_.max()), 4),
                "active": bool(both_active),
            }
        return metrics

    metrics_recorded = score(swap=False)
    metrics = score(swap=True)  # mirrored reference = headline
    missing_in_solver = [n for n in iphone if n not in arkit_names]

    def mean_pearson(ms: dict) -> float:
        vals = [m["pearson"] for m in ms.values() if m["active"] and m["pearson"] is not None]
        return float(np.mean(vals))

    active = {n: m for n, m in metrics.items() if m["active"] and m["pearson"] is not None}
    mean_r = mean_pearson(metrics)
    mean_r_recorded = mean_pearson(metrics_recorded)

    report = {
        "take": "20260814_DefaultSlate_2",
        "alignment": {"lagFrames": lag, "lagSeconds": round(lag / FPS, 4), "jawOpenCorr": round(corr, 4)},
        "solve": {
            "frames": n_frames,
            "meanRelResidual": round(float(resid.mean()), 5),
            "p95RelResidual": round(float(np.percentile(resid, 95)), 5),
            "unmatchedMhaCurves": unmatched,
        },
        "referenceOrientation": {
            "note": "Blip mono video is mirrored (selfie convention); MHA solve "
            "is therefore a mirror image of the ARKit stream. Headline metrics "
            "use the L/R-swapped iPhone reference.",
            "meanPearsonMirroredRef": round(mean_r, 4),
            "meanPearsonAsRecordedRef": round(mean_r_recorded, 4),
        },
        "activeCurveMeanPearson": round(mean_r, 4),
        "iphoneCurvesWithNoSolverOutput": missing_in_solver,
        "perCurve": metrics,
        "perCurveAsRecordedRef": metrics_recorded,
    }

    np.savez_compressed(
        p1_env.DATA_DIR / "samples" / "arkittest_solved_weights.npz",
        W=W.astype(np.float32),
        residual=resid.astype(np.float32),
        controls=ctrl.astype(np.float32),
        arkit_names=np.array(arkit_names),
        lag_frames=lag,
        fps=FPS,
    )
    (p1_env.REPORTS_DIR / "p2_take_comparison.json").write_text(json.dumps(report, indent=2))

    ranked = sorted(active.items(), key=lambda kv: kv[1]["pearson"], reverse=True)
    lines = [
        "# P2 take comparison — inverse solve vs iPhone ARKit (calibrated)",
        "",
        f"Take `{report['take']}`, {n_frames} frames @ {FPS} fps. "
        f"Alignment lag {lag}f ({lag / FPS:.3f}s), JawOpen corr {corr:.3f}.",
        "",
        "**Reference is L/R-swapped**: the Blip mono video is mirrored (selfie "
        "convention), so the MHA solve is a mirror image of the ARKit stream. "
        f"Mean Pearson vs mirrored ref **{mean_r:.3f}** vs as-recorded ref "
        f"{mean_r_recorded:.3f}.",
        "",
        f"Mean solve residual {report['solve']['meanRelResidual']}; "
        f"{len(active)} active curves.",
        "",
        "| curve | pearson | rmse | solved p95 | iphone p95 |",
        "|---|---|---|---|---|",
    ]
    for n, m in ranked:
        lines.append(
            f"| {n} | {m['pearson']} | {m['rmse']} | {m['solvedP95']} | {m['iphoneP95']} |"
        )
    inactive = [n for n, m in metrics.items() if not m["active"]]
    lines += [
        "",
        f"Inactive in both streams (nothing to compare): {', '.join(inactive) or 'none'}",
        "",
        f"iPhone curves the solver can't emit yet: {', '.join(missing_in_solver)}",
        "(MouthClose comes from the ABP formula inversion in the definition fit; "
        "head/eye rotations are bone channels, not part of the 51-shape basis.)",
    ]
    (p1_env.REPORTS_DIR / "p2_take_comparison.md").write_text("\n".join(lines) + "\n")

    print(f"mean Pearson (active curves): {mean_r:.4f}")
    print("weakest active curves:")
    for n, m in ranked[-8:]:
        print(f"  {n}: r={m['pearson']} rmse={m['rmse']}")


if __name__ == "__main__":
    main()
