"""P2: score RM_MHA_to_ARKit.json end-to-end on the arkittest take.

Evaluates the definition JSON offline (numpy reimplementation of the
weighted_sum / sdk / multiply node semantics) over the take's MHA curves and
compares:

  (a) definition output vs the per-frame BVLS solve  (fit fidelity)
  (b) definition output vs the mirrored iPhone ARKit reference (end metric,
      including MouthClose, which the per-frame solve cannot produce)

Outputs: v3/reports/p2_definition_score.{json,md}

Run with Blender 5.2's python.exe (see p1_env.py).
"""

from __future__ import annotations

import json

import numpy as np

import p1_env

p1_env.bootstrap()

from solve_take import FPS, IPHONE_CSV, MHA_JSON, load_iphone, load_mha, mirror_name  # noqa: E402


class DefinitionEvaluator:
    """Numpy evaluator for the RigMapperDefinition JSON graph.

    Missing curves are treated as 0.0 here (the take supplies every input);
    the in-engine processor propagates them as unset instead — do not reuse
    this evaluator to reason about partial curve sets.
    """

    def __init__(self, definition: dict):
        self.d = definition

    def evaluate(self, curves: dict[str, np.ndarray], n: int) -> dict[str, np.ndarray]:
        values: dict[str, np.ndarray] = {}

        def get(name: str) -> np.ndarray:
            if name in values:
                return values[name]
            if name in self.d["features"]:
                values[name] = self._node(name, get)
                return values[name]
            return curves.get(name, np.zeros(n))

        return {out: get(src).copy() for out, src in self.d["outputs"].items()}

    def _node(self, name: str, get) -> np.ndarray:
        f = self.d["features"][name]
        kind = f["type"]
        ins = [get(i) for i in f["input_features"]]
        if kind == "weighted_sum":
            w = f["params"]["weights"]
            return np.sum([x * wi for x, wi in zip(ins, w)], axis=0)
        if kind == "sdk":
            return np.interp(ins[0], f["params"]["in_val"], f["params"]["out_val"])
        if kind == "multiply":
            out = ins[0].copy()
            for x in ins[1:]:
                out = out * x
            return out
        raise ValueError(f"unknown node type {kind}")


def metrics(a: np.ndarray, b: np.ndarray) -> dict:
    cc = None
    if a.std() > 1e-6 and b.std() > 1e-6:
        cc = round(float(np.corrcoef(a, b)[0, 1]), 4)
    return {
        "pearson": cc,
        "rmse": round(float(np.sqrt(np.mean((a - b) ** 2))), 4),
        "p95": round(float(np.percentile(a, 95)), 4),
        "refP95": round(float(np.percentile(b, 95)), 4),
    }


def main() -> None:
    definition = json.loads((p1_env.V3_DIR / "RM_MHA_to_ARKit.json").read_text())
    grid, mha = load_mha(MHA_JSON)
    n = len(grid)

    out = DefinitionEvaluator(definition).evaluate(mha, n)

    take = np.load(p1_env.DATA_DIR / "samples" / "arkittest_solved_weights.npz")
    W = take["W"].astype(np.float64)
    solve_names = [str(s) for s in take["arkit_names"]]

    it, iphone = load_iphone(IPHONE_CSV)
    iph = {k: np.interp(grid, it, v) for k, v in iphone.items()}

    vs_solve = {}
    for k, name in enumerate(solve_names):
        if name in out:
            vs_solve[name] = metrics(out[name], W[:, k])

    vs_iphone = {}
    for name, v in out.items():
        ref = iph.get(mirror_name(name))
        if ref is None:
            continue
        vs_iphone[name] = metrics(v, ref)

    def mean_r(ms: dict, active_only=True) -> float:
        vals = [
            m["pearson"]
            for m in ms.values()
            if m["pearson"] is not None and (not active_only or m["p95"] > 0.05 or m["refP95"] > 0.05)
        ]
        return round(float(np.mean(vals)), 4)

    report = {
        "take": "20260814_DefaultSlate_2",
        "definitionVsSolve": {"meanPearson": mean_r(vs_solve), "perCurve": vs_solve},
        "definitionVsIphoneMirrored": {"meanPearson": mean_r(vs_iphone), "perCurve": vs_iphone},
        "mouthCloseVsIphone": vs_iphone.get("MouthClose"),
    }
    (p1_env.REPORTS_DIR / "p2_definition_score.json").write_text(json.dumps(report, indent=2))

    ranked = sorted(
        ((nm, m) for nm, m in vs_iphone.items() if m["pearson"] is not None and (m["p95"] > 0.05 or m["refP95"] > 0.05)),
        key=lambda kv: kv[1]["pearson"],
        reverse=True,
    )
    lines = [
        "# P2 definition score — RM_MHA_to_ARKit.json on the arkittest take",
        "",
        f"- vs per-frame BVLS solve: mean Pearson **{report['definitionVsSolve']['meanPearson']}** "
        "(how faithfully the static graph reproduces the solver)",
        f"- vs mirrored iPhone reference: mean Pearson **{report['definitionVsIphoneMirrored']['meanPearson']}** "
        "(end-to-end quality; solver itself scored 0.576)",
        f"- MouthClose vs iPhone: {report['mouthCloseVsIphone']}",
        "",
        "| curve | vs iPhone r | rmse | def p95 | iphone p95 |",
        "|---|---|---|---|---|",
    ]
    for nm, m in ranked:
        lines.append(f"| {nm} | {m['pearson']} | {m['rmse']} | {m['p95']} | {m['refP95']} |")
    (p1_env.REPORTS_DIR / "p2_definition_score.md").write_text("\n".join(lines) + "\n")

    print("def vs solve mean r:", report["definitionVsSolve"]["meanPearson"])
    print("def vs iPhone (mirrored) mean r:", report["definitionVsIphoneMirrored"]["meanPearson"])
    print("MouthClose vs iPhone:", report["mouthCloseVsIphone"])


if __name__ == "__main__":
    main()
