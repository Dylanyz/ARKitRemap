"""P2: fit the sparse feature graph and export RM_MHA_to_ARKit.json.

Per ARKit output, fits a sparse non-negative weighted sum of MHA input curves
over the solved sample set (synthetic sweeps + the arkittest take), with SDK
(piecewise-linear) shaping wherever a dominant input's ramp response is
measurably nonlinear. MouthClose: the planned exact ABP inversion (mean(lipsTogether) * jawOpen)
provably fails on MHA-origin curves — MHA's jawOpen is near zero exactly when
lips are pressed, because it solves what the face looks like; the relation
only holds for curves produced BY the forward ABP. Instead MouthClose is fit
data-driven against the measured iPhone MouthClose of the paired take
(calibration data, not a guessed constant), over L/R-symmetrized lip-region
candidate pairs (thick/push/purse/together/cornerDown), NNLS + pruning.
Calibrated on one take so far — refine when more paired takes exist.

JSON schema matches Epic's ExportAsJsonString exactly (verified against
/RigMapper/Definitions/Baked/RM_CDL_FNL in 5.8.1):

    features[name] = {type: weighted_sum|sdk|multiply,
                      input_features: [...], input_params: [],
                      params: {weights: [...]} | {in_val: [...], out_val: [...]} | {}}
    outputs[out] = feature name or direct input curve name

Convention (per plan): name-consistent Epic-PA space, no Apple-quirk
cross-wiring. Outputs with no expressible response are declared null_outputs.

Outputs:
    v3/RM_MHA_to_ARKit.json
    v3/reports/p2_fit_report.{json,md}

Run with Blender 5.2's python.exe (see p1_env.py).
"""

from __future__ import annotations

import json

import numpy as np

import p1_env

p1_env.bootstrap()

from scipy.optimize import nnls  # noqa: E402

PRUNE = 0.02
SDK_MIN_WEIGHT = 0.10  # only bother shaping inputs that matter this much
SDK_DEV = 0.03  # ramp deviation from proportional before an SDK is added
PASSTHROUGH_TOL = 0.02
RAMP = [0.2, 0.4, 0.6, 0.8, 1.0]

# L/R-symmetrized candidate pairs for the MouthClose fit (lip-press family)
MOUTHCLOSE_PAIRS = [
    ("CTRL_expressions_mouthLipsTogetherUL", "CTRL_expressions_mouthLipsTogetherUR"),
    ("CTRL_expressions_mouthLipsTogetherDL", "CTRL_expressions_mouthLipsTogetherDR"),
    ("CTRL_expressions_mouthLipsThickUL", "CTRL_expressions_mouthLipsThickUR"),
    ("CTRL_expressions_mouthLipsThickDL", "CTRL_expressions_mouthLipsThickDR"),
    ("CTRL_expressions_mouthLipsPushUL", "CTRL_expressions_mouthLipsPushUR"),
    ("CTRL_expressions_mouthLipsPushDL", "CTRL_expressions_mouthLipsPushDR"),
    ("CTRL_expressions_mouthLipsPurseUL", "CTRL_expressions_mouthLipsPurseUR"),
    ("CTRL_expressions_mouthLipsPurseDL", "CTRL_expressions_mouthLipsPurseDR"),
    ("CTRL_expressions_mouthCornerDownL", "CTRL_expressions_mouthCornerDownR"),
    ("CTRL_expressions_mouthLipsPressL", "CTRL_expressions_mouthLipsPressR"),
]


def curve_name(raw_name: str) -> str:
    return raw_name.replace(".", "_")


def r2(y: np.ndarray, yhat: np.ndarray) -> float:
    ss = float(np.sum((y - y.mean()) ** 2))
    return 1.0 - float(np.sum((y - yhat) ** 2)) / ss if ss > 0 else 1.0


def main() -> None:
    basis = np.load(p1_env.DATA_DIR / "arkit_basis_joints.npz")
    arkit_names = [str(s) for s in basis["arkit_names"]]
    raw_names = [str(s) for s in basis["raw_control_names"]]
    C_pose = basis["C"].astype(np.float64)

    routing = json.loads((p1_env.REPORTS_DIR / "p2_single_control_routing.json").read_text())

    sweeps = np.load(p1_env.DATA_DIR / "samples" / "synthetic_sweeps.npz")
    take = np.load(p1_env.DATA_DIR / "samples" / "arkittest_solved_weights.npz")
    C_all = np.vstack([sweeps["C"].astype(np.float64), take["controls"].astype(np.float64)])
    W_all = np.vstack([sweeps["W"].astype(np.float64), take["W"].astype(np.float64)])
    tags = [str(t) for t in sweeps["tags"]]

    # single-control ramp lookup: control curve name -> [(t, sample_row)]
    ramp_rows: dict[str, list[tuple[float, int]]] = {}
    for row, tag in enumerate(tags):
        if tag.startswith("single:"):
            body = tag[len("single:"):]
            nm, t = body.rsplit("@", 1)
            ramp_rows.setdefault(curve_name(nm), []).append((float(t), row))

    name_to_raw = {curve_name(n): i for i, n in enumerate(raw_names)}

    features: dict[str, dict] = {}
    outputs: dict[str, str] = {}
    null_outputs: list[str] = []
    report_rows = {}

    for j, out_name in enumerate(arkit_names):
        y = W_all[:, j]
        if y.max() < 0.02:
            null_outputs.append(out_name)
            report_rows[out_name] = {"kind": "null", "reason": "no solved activation anywhere"}
            continue

        # candidate inputs: routing hits + the PA pose's own controls
        cands: set[str] = set()
        for ctrl, r in routing.items():
            if r["weights"].get(out_name, 0.0) >= PRUNE:
                cands.add(curve_name(ctrl))
        for ci in np.nonzero(C_pose[j] > 1e-6)[0]:
            cands.add(curve_name(raw_names[ci]))
        cands = sorted(c for c in cands if c in name_to_raw)

        X = C_all[:, [name_to_raw[c] for c in cands]]
        beta, _ = nnls(X, y)
        keep = beta >= PRUNE
        if not keep.any():
            null_outputs.append(out_name)
            report_rows[out_name] = {"kind": "null", "reason": "all weights pruned"}
            continue
        cands = [c for c, k in zip(cands, keep) if k]
        X = C_all[:, [name_to_raw[c] for c in cands]]
        beta, _ = nnls(X, y)

        # SDK shaping for heavy inputs with nonlinear solo ramps
        node_inputs: list[str] = []
        columns = []
        for c, b in zip(cands, beta):
            use_sdk = False
            if b >= SDK_MIN_WEIGHT and c in ramp_rows:
                pts = sorted(ramp_rows[c])
                t = np.array([0.0] + [p[0] for p in pts])
                resp = np.array([0.0] + [float(W_all[p[1], j]) for p in pts])
                slope = float((t @ resp) / (t @ t))
                if np.abs(resp - slope * t).max() > SDK_DEV and resp.max() > PRUNE:
                    sdk_name = f"sdk:{c}:{out_name}"
                    features[sdk_name] = {
                        "type": "sdk",
                        "input_features": [c],
                        "input_params": [],
                        "params": {
                            "in_val": [round(float(x), 4) for x in t],
                            "out_val": [round(float(x), 4) for x in resp],
                        },
                    }
                    node_inputs.append(sdk_name)
                    columns.append(np.interp(C_all[:, name_to_raw[c]], t, resp))
                    use_sdk = True
            if not use_sdk:
                node_inputs.append(c)
                columns.append(C_all[:, name_to_raw[c]])

        Xf = np.column_stack(columns)
        beta, _ = nnls(Xf, y)
        keep = beta >= PRUNE
        node_inputs = [c for c, k in zip(node_inputs, keep) if k]
        Xf = Xf[:, keep]
        beta, _ = nnls(Xf, y)
        yhat = Xf @ beta
        fit_r2 = r2(y, yhat)

        if (
            len(node_inputs) == 1
            and not node_inputs[0].startswith("sdk:")
            and abs(beta[0] - 1.0) <= PASSTHROUGH_TOL
            and fit_r2 >= 0.995
        ):
            outputs[out_name] = node_inputs[0]
            report_rows[out_name] = {"kind": "passthrough", "input": node_inputs[0], "r2": round(fit_r2, 4)}
        else:
            ws_name = f"ws:{out_name}"
            features[ws_name] = {
                "type": "weighted_sum",
                "input_features": node_inputs,
                "input_params": [],
                "params": {"weights": [round(float(b), 4) for b in beta]},
            }
            outputs[out_name] = ws_name
            report_rows[out_name] = {
                "kind": "weighted_sum",
                "terms": {c: round(float(b), 4) for c, b in zip(node_inputs, beta)},
                "r2": round(fit_r2, 4),
            }

    # ---- MouthClose: data-driven fit vs measured iPhone MouthClose ----
    from solve_take import IPHONE_CSV, MHA_JSON, load_iphone, load_mha

    grid, take_curves = load_mha(MHA_JSON)
    it, iphone = load_iphone(IPHONE_CSV)
    mc_target = np.interp(grid, it, iphone["MouthClose"])

    pair_cols, pair_labels = [], []
    for l_name, r_name in MOUTHCLOSE_PAIRS:
        if l_name in take_curves and r_name in take_curves:
            pair_cols.append(take_curves[l_name] + take_curves[r_name])
            pair_labels.append((l_name, r_name))
    Xmc = np.column_stack(pair_cols)
    bmc, _ = nnls(Xmc, mc_target)
    keep = bmc >= PRUNE / 2
    pair_labels = [p for p, k in zip(pair_labels, keep) if k]
    Xmc = Xmc[:, keep]
    bmc, _ = nnls(Xmc, mc_target)
    mc_r2 = r2(mc_target, Xmc @ bmc)

    mc_inputs, mc_weights = [], []
    for (l_name, r_name), b in zip(pair_labels, bmc):
        mc_inputs += [l_name, r_name]
        mc_weights += [round(float(b), 4)] * 2
    features["ws:MouthClose"] = {
        "type": "weighted_sum",
        "input_features": mc_inputs,
        "input_params": [],
        "params": {"weights": mc_weights},
    }
    outputs["MouthClose"] = "ws:MouthClose"
    report_rows["MouthClose"] = {
        "kind": "iphone-calibrated",
        "r2": round(mc_r2, 4),
        "terms": {f"{l}+{r}".replace("CTRL_expressions_", ""): round(float(b), 4)
                  for (l, r), b in zip(pair_labels, bmc)},
        "note": "fit vs measured iPhone MouthClose (take 20260814_DefaultSlate_2); "
        "ABP inversion invalid on MHA-origin curves (jawOpen ~0 when lips pressed)",
    }

    # inputs = every curve referenced anywhere
    used: set[str] = set()
    for f in features.values():
        for i in f["input_features"]:
            if not (i.startswith("ws:") or i.startswith("sdk:") or i.startswith("mul:")):
                used.add(i)
    for o, src in outputs.items():
        if not (src.startswith("ws:") or src.startswith("sdk:") or src.startswith("mul:")):
            used.add(src)

    definition = {
        "inputs": sorted(used),
        "features": features,
        "parameters": {},
        "outputs": outputs,
        "null_outputs": sorted(null_outputs),
    }
    (p1_env.V3_DIR / "RM_MHA_to_ARKit.json").write_text(json.dumps(definition, indent="\t"))

    kinds = {}
    for r in report_rows.values():
        kinds[r["kind"]] = kinds.get(r["kind"], 0) + 1
    r2s = [r["r2"] for r in report_rows.values() if "r2" in r]
    report = {
        "summary": {
            "outputs": len(outputs),
            "nullOutputs": null_outputs,
            "kinds": kinds,
            "meanR2": round(float(np.mean(r2s)), 4),
            "minR2": round(float(np.min(r2s)), 4),
            "inputCurvesUsed": len(used),
            "featureNodes": len(features),
        },
        "perOutput": report_rows,
    }
    (p1_env.REPORTS_DIR / "p2_fit_report.json").write_text(json.dumps(report, indent=2))

    lines = [
        "# P2 definition fit — RM_MHA_to_ARKit.json",
        "",
        f"{len(outputs)} outputs ({kinds}), {len(features)} feature nodes, "
        f"{len(used)} input curves. Fit R2 mean {np.mean(r2s):.4f}, min {np.min(r2s):.4f}.",
        f"Null outputs: {', '.join(null_outputs) or 'none'}",
        "",
        "| output | kind | r2 | terms |",
        "|---|---|---|---|",
    ]
    for name in arkit_names + ["MouthClose"]:
        r = report_rows.get(name)
        if r is None:
            continue
        terms = r.get("terms") or ({r.get("input"): 1.0} if r.get("input") else {})
        tstr = ", ".join(f"{k.replace('CTRL_expressions_', '')}={v}" for k, v in terms.items()) or r.get("formula", r.get("reason", ""))
        lines.append(f"| {name} | {r['kind']} | {r.get('r2', '—')} | {tstr} |")
    (p1_env.REPORTS_DIR / "p2_fit_report.md").write_text("\n".join(lines) + "\n")

    print(f"outputs: {len(outputs)} | kinds: {kinds} | nodes: {len(features)} | inputs: {len(used)}")
    print(f"R2 mean {np.mean(r2s):.4f} min {np.min(r2s):.4f}")
    worst = sorted((r["r2"], n) for n, r in report_rows.items() if "r2" in r)[:6]
    print("worst fits:", [(n, round(v, 3)) for v, n in worst])


if __name__ == "__main__":
    main()
