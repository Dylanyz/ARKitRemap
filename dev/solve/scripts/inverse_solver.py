"""P1/P2: bounded least-squares inverse solve, MHA controls -> ARKit-51 weights.

    d  = RigLogic(c) - baseline          (joint-output delta for an MHA frame)
    w* = argmin ||B^T w - d||^2  s.t.  w in [0,1]^51

Run as a script it validates itself on the basis poses (identity recovery:
feeding pose j's own controls must return ~one-hot e_j) and probes rig
linearity along scaled activations. Results land in
v3/reports/p1_solver_validation.{json,md}.

Run with Blender 5.2's python.exe (see p1_env.py).
"""

from __future__ import annotations

import json

import numpy as np

import p1_env

p1_env.bootstrap()

from scipy.optimize import lsq_linear  # noqa: E402

from riglogic_harness import RigHarness  # noqa: E402

LINEARITY_PROBES = ["JawOpen", "MouthSmileLeft", "EyeBlinkLeft", "CheekPuff"]
LINEARITY_STEPS = np.linspace(0.0, 1.0, 11)


class InverseSolver:
    """Solves ARKit-51 weights for MHA control vectors against the P1 basis."""

    def __init__(self, rig: RigHarness | None = None):
        self.rig = rig or RigHarness()
        npz = np.load(p1_env.DATA_DIR / "arkit_basis_joints.npz", allow_pickle=False)
        self.B = npz["B"].astype(np.float64)  # (51, 7830)
        self.C = npz["C"].astype(np.float64)  # (51, n_raw) basis control vectors
        self.baseline_joints = npz["baseline_joints"].astype(np.float64)
        self.arkit_names = [str(s) for s in npz["arkit_names"]]
        self.A = self.B.T  # (7830, 51) design matrix

    def solve_delta(self, joint_delta: np.ndarray) -> np.ndarray:
        res = lsq_linear(self.A, joint_delta, bounds=(0.0, 1.0), method="bvls")
        return res.x

    def solve_controls(self, control_vec: np.ndarray) -> tuple[np.ndarray, float]:
        """Full pipeline: raw-control vector -> (arkit_weights, relative_residual)."""
        joints, _ = self.rig.evaluate(control_vec)
        d = joints - self.baseline_joints
        w = self.solve_delta(d)
        dn = np.linalg.norm(d)
        rel = float(np.linalg.norm(self.A @ w - d) / dn) if dn > 0 else 0.0
        return w, rel

    def solve_curves(self, curve_values: dict) -> tuple[dict, float, list]:
        vec, unmatched = self.rig.control_vector(curve_values)
        w, rel = self.solve_controls(vec)
        return dict(zip(self.arkit_names, w)), rel, unmatched


def validate_identity(solver: InverseSolver) -> list[dict]:
    """Feed each basis pose's own controls back through the solver."""
    rows = []
    for j, name in enumerate(solver.arkit_names):
        w, rel = solver.solve_controls(solver.C[j])
        order = np.argsort(w)[::-1]
        rows.append(
            {
                "pose": name,
                "selfWeight": round(float(w[j]), 4),
                "topWeight": {
                    "name": solver.arkit_names[int(order[0])],
                    "value": round(float(w[order[0]]), 4),
                },
                "secondWeight": {
                    "name": solver.arkit_names[int(order[1])],
                    "value": round(float(w[order[1]]), 4),
                },
                "crosstalkL1": round(float(np.sum(w) - w[j]), 4),
                "relResidual": round(rel, 5),
                "recovered": bool(order[0] == j and w[j] > 0.9),
            }
        )
    return rows


def probe_linearity(solver: InverseSolver) -> list[dict]:
    """Scale a pose's controls 0->1; measure deformation-norm curvature and
    whether the solved self-weight tracks the scale (PSD stages are the
    expected source of any deviation)."""
    probes = []
    for name in LINEARITY_PROBES:
        j = solver.arkit_names.index(name)
        c = solver.C[j]
        full_norm = np.linalg.norm(solver.B[j])
        rows = []
        for t in LINEARITY_STEPS:
            joints, _ = solver.rig.evaluate(c * t)
            d = joints - solver.baseline_joints
            w = solver.solve_delta(d)
            rows.append(
                {
                    "t": round(float(t), 2),
                    "normRatio": round(float(np.linalg.norm(d) / full_norm), 4),
                    "selfWeight": round(float(w[j]), 4),
                }
            )
        max_dev = max(abs(r["normRatio"] - r["t"]) for r in rows)
        probes.append({"pose": name, "maxNormDeviationFromLinear": round(max_dev, 4), "steps": rows})
    return probes


def main() -> None:
    solver = InverseSolver()
    identity = validate_identity(solver)
    linearity = probe_linearity(solver)

    failed = [r for r in identity if not r["recovered"]]
    report = {
        "identity": {
            "recovered": len(identity) - len(failed),
            "total": len(identity),
            "meanSelfWeight": round(float(np.mean([r["selfWeight"] for r in identity])), 4),
            "meanCrosstalkL1": round(float(np.mean([r["crosstalkL1"] for r in identity])), 4),
            "failures": [r["pose"] for r in failed],
            "rows": identity,
        },
        "linearity": linearity,
    }
    p1_env.REPORTS_DIR.mkdir(exist_ok=True)
    (p1_env.REPORTS_DIR / "p1_solver_validation.json").write_text(json.dumps(report, indent=2))

    lines = [
        "# P1 solver validation — bounded LSQ identity recovery",
        "",
        f"- recovered (top weight = own pose, self > 0.9): "
        f"{len(identity) - len(failed)}/{len(identity)}",
        f"- mean self weight: {report['identity']['meanSelfWeight']}",
        f"- mean crosstalk (L1 of other weights): {report['identity']['meanCrosstalkL1']}",
        "",
    ]
    if failed:
        lines.append("## Poses not cleanly recovered")
        for r in failed:
            lines.append(
                f"- {r['pose']}: self={r['selfWeight']}, top={r['topWeight']['name']}"
                f"={r['topWeight']['value']}, second={r['secondWeight']['name']}"
                f"={r['secondWeight']['value']}, residual={r['relResidual']}"
            )
        lines.append("")
    lines.append("## Linearity probes (deformation norm vs control scale)")
    for p in linearity:
        lines.append(f"- {p['pose']}: max deviation from linear {p['maxNormDeviationFromLinear']}")
    (p1_env.REPORTS_DIR / "p1_solver_validation.md").write_text("\n".join(lines) + "\n")

    print(f"identity: {len(identity) - len(failed)}/{len(identity)} recovered")
    for r in failed:
        print(f"  MISS {r['pose']}: self={r['selfWeight']} top={r['topWeight']}")
    for p in linearity:
        print(f"linearity {p['pose']}: max dev {p['maxNormDeviationFromLinear']}")


if __name__ == "__main__":
    main()
