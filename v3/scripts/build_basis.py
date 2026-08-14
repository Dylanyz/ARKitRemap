"""P1: evaluate the 52-shape ARKit basis in joint-output space + conditioning.

For each ARKit pose j in the fresh PA extraction (v3/data/pa_mapping.json):

    c_j = pose j's CTRL_expressions raw records (absolute PoseAsset values)
    B_j = RigLogic(c_j) - RigLogic(c_Default)     (joint-output deltas, 7830-dim)

Using raw (not Default-adjusted) records on both sides keeps the nonlinear PSD
stages honest: the basis is the deformation delta between the pose and Epic's
own Default frame, evaluated through the real rig, not a subtraction of
control values pushed through separately.

Outputs:
    v3/data/arkit_basis_joints.npz     B, C (controls), M (animated-map deltas),
                                       names, baseline
    v3/reports/p1_basis_report.json    curve-mapping audit + conditioning
    v3/reports/p1_basis_report.md      human-readable summary

Run with Blender 5.2's python.exe (see p1_env.py).
"""

from __future__ import annotations

import json

import numpy as np

import p1_env
from riglogic_harness import RigHarness

EXPR_PREFIX = "ctrl_expressions_"
COSINE_FLAG = 0.5  # pairs above this share substantial deformation mass


def expression_controls(record: dict) -> dict:
    """Keep only CTRL_expressions curve records (drops wrinkle-map / mesh-shape
    output curves and the ctrl_riglogic_offon switch)."""
    return {k: v for k, v in record.items() if k.lower().startswith(EXPR_PREFIX)}


def main() -> None:
    rig = RigHarness()
    pa = json.loads((p1_env.DATA_DIR / "pa_mapping.json").read_text())
    live = json.loads((p1_env.DATA_DIR / "mha_live_subject_curves.json").read_text())

    pose_names = pa["poseNames"]
    arkit_names = pose_names[1:52]  # 0=Default, 1..51=ARKit (no MouthClose pose)
    assert len(arkit_names) == 51, f"expected 51 ARKit poses, got {len(arkit_names)}"

    # ---- live MHA curve <-> DNA raw control audit (ground-truth input set) ----
    live_expr = [n for n in live["curveNames"] if n.startswith("CTRL_expressions_")]
    live_map, live_unmatched = rig.resolve(live_expr)
    dna_keys_hit = {rig.raw_names[i] for i in live_map.values()}
    dna_unhit = [
        rig.raw_names[i]
        for i in rig.expr_indices
        if rig.raw_names[i] not in dna_keys_hit
    ]

    # ---- baseline: Epic's Default pose evaluated through the rig ----
    default_controls = expression_controls(pa["raw"]["Default"]["curves"])
    base_vec, base_unmatched = rig.control_vector(default_controls)
    base_joints, base_maps = rig.evaluate(base_vec)

    # ---- basis ----
    n = len(arkit_names)
    B = np.zeros((n, rig.n_joint_attrs))
    M = np.zeros((n, len(rig.map_names)))
    C = np.zeros((n, rig.n_raw))
    pose_audit = {}
    for j, name in enumerate(arkit_names):
        record = expression_controls(pa["raw"][name]["curves"])
        vec, unmatched = rig.control_vector(record)
        joints, maps = rig.evaluate(vec)
        B[j] = joints - base_joints
        M[j] = maps - base_maps
        C[j] = vec
        pose_audit[name] = {
            "controlCount": len(record),
            "unmatchedCurves": unmatched,
            "jointDeltaNorm": float(np.linalg.norm(B[j])),
            "activeJointCount": int(np.sum(rig.per_joint_norms(B[j]) > 1e-6)),
        }

    # ---- conditioning ----
    norms = np.linalg.norm(B, axis=1)
    unit = B / norms[:, None]
    cos = unit @ unit.T
    svals = np.linalg.svd(B, compute_uv=False)
    overlaps = [
        {"a": arkit_names[i], "b": arkit_names[k], "cosine": round(float(cos[i, k]), 4)}
        for i in range(n)
        for k in range(i + 1, n)
        if cos[i, k] > COSINE_FLAG
    ]
    overlaps.sort(key=lambda r: -r["cosine"])

    report = {
        "liveCurveAudit": {
            "liveExpressionCurves": len(live_expr),
            "matchedToDna": len(live_map),
            "liveCurvesWithNoDnaControl": live_unmatched,
            "dnaControlsNotInLiveStream": dna_unhit,
        },
        "baseline": {
            "defaultControlCount": len(default_controls),
            "unmatchedCurves": base_unmatched,
            "jointNorm": float(np.linalg.norm(base_joints)),
        },
        "poses": pose_audit,
        "conditioning": {
            "singularValues": [round(float(s), 4) for s in svals],
            "conditionNumber": float(svals[0] / svals[-1]),
            "rankAt1e-3RelTol": int(np.sum(svals > svals[0] * 1e-3)),
            "minPoseNorm": {
                "pose": arkit_names[int(np.argmin(norms))],
                "norm": float(norms.min()),
            },
            "maxPoseNorm": {
                "pose": arkit_names[int(np.argmax(norms))],
                "norm": float(norms.max()),
            },
            "overlappingPairs": overlaps,
        },
    }

    p1_env.REPORTS_DIR.mkdir(exist_ok=True)
    np.savez_compressed(
        p1_env.DATA_DIR / "arkit_basis_joints.npz",
        B=B.astype(np.float32),
        C=C.astype(np.float32),
        M=M.astype(np.float32),
        baseline_joints=base_joints.astype(np.float32),
        baseline_maps=base_maps.astype(np.float32),
        arkit_names=np.array(arkit_names),
        raw_control_names=np.array(rig.raw_names),
        joint_names=np.array(rig.joint_names),
        map_names=np.array(rig.map_names),
    )
    (p1_env.REPORTS_DIR / "p1_basis_report.json").write_text(json.dumps(report, indent=2))

    lines = [
        "# P1 basis report — ARKit-51 in joint-output space",
        "",
        f"Basis: {n} poses x {rig.n_joint_attrs} joint attrs "
        f"(870 joints x 9), archetype DNA `{p1_env.DNA_PATH.name}`.",
        "",
        "## Live curve audit",
        f"- {len(live_map)}/{len(live_expr)} live MHA expression curves resolve "
        "to DNA raw controls",
        f"- live-only (no DNA control): {live_unmatched or 'none'}",
        f"- DNA-only (never streamed): {dna_unhit or 'none'}",
        "",
        "## Conditioning",
        f"- singular value range: {svals[0]:.3f} .. {svals[-1]:.3f} "
        f"(condition number {svals[0]/svals[-1]:.1f})",
        f"- rank at 1e-3 rel tolerance: {int(np.sum(svals > svals[0]*1e-3))}/{n}",
        f"- pose norms: min {norms.min():.3f} ({arkit_names[int(np.argmin(norms))]}), "
        f"max {norms.max():.3f} ({arkit_names[int(np.argmax(norms))]})",
        "",
        f"## Overlapping pairs (cosine > {COSINE_FLAG})",
    ]
    lines += [f"- {r['a']} / {r['b']}: {r['cosine']}" for r in overlaps] or ["- none"]
    (p1_env.REPORTS_DIR / "p1_basis_report.md").write_text("\n".join(lines) + "\n")

    print(f"basis saved: {n} x {rig.n_joint_attrs}")
    print(f"condition number: {svals[0]/svals[-1]:.1f}")
    print(f"overlapping pairs > {COSINE_FLAG}: {len(overlaps)}")
    print(f"live curves unmatched: {len(live_unmatched)} | DNA controls unhit: {len(dna_unhit)}")


if __name__ == "__main__":
    main()
