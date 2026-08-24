"""P2: synthetic control sweeps -> dense (c -> w*) sample set for the fit.

Four sweep families, all evaluated through the real rig and solved against
the P1 basis:

  single   each of the 251 expression controls ramped alone (5 steps)
  pose     each of the 51 PA pose control vectors ramped (5 steps)
  overlap  the 15 cosine>0.5 basis pairs combined on a small grid
  mix      random convex combinations of 2-4 PA poses (Dirichlet weights)

Outputs:
    v3/data/samples/synthetic_sweeps.npz      C, W, residual, tags
    v3/reports/p2_single_control_routing.md   control -> dominant ARKit
                                              weights at full activation
                                              (the seed of the definition)

Run with Blender 5.2's python.exe (see p1_env.py).
"""

from __future__ import annotations

import json

import numpy as np

import p1_env

p1_env.bootstrap()

from scipy.optimize import lsq_linear  # noqa: E402

from riglogic_harness import RigHarness  # noqa: E402

RAMP = [0.2, 0.4, 0.6, 0.8, 1.0]
PAIR_GRID = [(0.5, 0.5), (1.0, 0.5), (0.5, 1.0), (1.0, 1.0)]
N_MIX = 300
MIX_SEED = 58
COSINE_FLAG = 0.5


def main() -> None:
    rig = RigHarness()
    npz = np.load(p1_env.DATA_DIR / "arkit_basis_joints.npz")
    B = npz["B"].astype(np.float64)
    C_pose = npz["C"].astype(np.float64)
    baseline = npz["baseline_joints"].astype(np.float64)
    arkit_names = [str(s) for s in npz["arkit_names"]]
    A = B.T
    Q, R = np.linalg.qr(A)

    # overlapping pairs recomputed from the basis (same rule as build_basis)
    unit = B / np.linalg.norm(B, axis=1)[:, None]
    cos = unit @ unit.T
    pairs = [
        (i, k)
        for i in range(len(arkit_names))
        for k in range(i + 1, len(arkit_names))
        if cos[i, k] > COSINE_FLAG
    ]

    samples: list[np.ndarray] = []
    tags: list[str] = []

    for ci in rig.expr_indices:
        name = rig.raw_names[ci]
        for t in RAMP:
            vec = np.zeros(rig.n_raw)
            vec[ci] = t
            samples.append(vec)
            tags.append(f"single:{name}@{t}")

    for j, pname in enumerate(arkit_names):
        for t in RAMP:
            samples.append(C_pose[j] * t)
            tags.append(f"pose:{pname}@{t}")

    for i, k in pairs:
        for ta, tb in PAIR_GRID:
            samples.append(np.clip(C_pose[i] * ta + C_pose[k] * tb, 0.0, 1.0))
            tags.append(f"overlap:{arkit_names[i]}@{ta}+{arkit_names[k]}@{tb}")

    rng = np.random.default_rng(MIX_SEED)
    for m in range(N_MIX):
        k = int(rng.integers(2, 5))
        idx = rng.choice(len(arkit_names), size=k, replace=False)
        w = rng.dirichlet(np.ones(k)) * rng.uniform(0.8, 1.6)
        vec = np.clip((C_pose[idx] * w[:, None]).sum(axis=0), 0.0, 1.0)
        samples.append(vec)
        tags.append("mix:" + "+".join(f"{arkit_names[i]}@{w[n]:.2f}" for n, i in enumerate(idx)))

    C = np.array(samples)
    n = len(C)
    print(f"{n} sweep samples "
          f"({len(rig.expr_indices) * len(RAMP)} single, {len(arkit_names) * len(RAMP)} pose, "
          f"{len(pairs) * len(PAIR_GRID)} overlap, {N_MIX} mix)")

    W = np.zeros((n, len(arkit_names)))
    resid = np.zeros(n)
    for f in range(n):
        joints, _ = rig.evaluate(C[f])
        d = joints - baseline
        qd = Q.T @ d
        res = lsq_linear(R, qd, bounds=(0.0, 1.0), method="bvls")
        W[f] = res.x
        dn = np.linalg.norm(d)
        resid[f] = np.linalg.norm(A @ res.x - d) / dn if dn > 1e-9 else 0.0
        if f % 250 == 0:
            print(f"  {f}/{n}")

    np.savez_compressed(
        p1_env.DATA_DIR / "samples" / "synthetic_sweeps.npz",
        C=C.astype(np.float32),
        W=W.astype(np.float32),
        residual=resid.astype(np.float32),
        tags=np.array(tags),
        arkit_names=np.array(arkit_names),
        raw_control_names=np.array(rig.raw_names),
    )

    # ---- single-control routing table at full activation ----
    lines = [
        "# P2 single-control routing — solved ARKit weights at control = 1.0",
        "",
        "Draft of the definition's input->output routing, straight from the",
        "deformation-space solve. `residual` is the share of the control's",
        "deformation the ARKit basis cannot express.",
        "",
        "| control | top ARKit weights | residual |",
        "|---|---|---|",
    ]
    routing = {}
    for s, tag in enumerate(tags):
        if not tag.startswith("single:") or not tag.endswith("@1.0"):
            continue
        control = tag[len("single:"):-len("@1.0")]
        order = np.argsort(W[s])[::-1]
        top = [
            f"{arkit_names[i]}={W[s, i]:.3f}" for i in order[:3] if W[s, i] > 0.02
        ]
        routing[control] = {
            "weights": {arkit_names[int(i)]: round(float(W[s, i]), 4) for i in order[:5] if W[s, i] > 0.02},
            "residual": round(float(resid[s]), 4),
        }
        lines.append(f"| {control.split('.')[-1]} | {', '.join(top) or '—'} | {resid[s]:.3f} |")

    (p1_env.REPORTS_DIR / "p2_single_control_routing.md").write_text("\n".join(lines) + "\n")
    (p1_env.REPORTS_DIR / "p2_single_control_routing.json").write_text(json.dumps(routing, indent=2))

    dead = [c.split(".")[-1] for c, r in routing.items() if not r["weights"]]
    high_resid = sorted(routing.items(), key=lambda kv: -kv[1]["residual"])[:10]
    print(f"controls with no ARKit response: {len(dead)}")
    print("highest-residual controls:", [(c.split(".")[-1], r["residual"]) for c, r in high_resid[:5]])


if __name__ == "__main__":
    main()
