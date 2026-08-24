# V3 empirical findings

How `RM_MHA_to_ARKit` was built and how well it performs. Everything below was measured, not
assumed. Sources: archetype DNA through real RigLogic, the PoseAsset extraction, two paired
iPhone/MHA takes, and Epic's own asset round-trips. Scripts in
[dev/solve/scripts/](../dev/solve/scripts/), evidence in [dev/reports/](../dev/reports/).

## 1. Epic's ground-truth assets

| Asset | Unreal path | Role |
|---|---|---|
| `PA_MetaHuman_ARKit_Mapping` | `/Game/MetaHumans/Common/Face/ARKit/PA_MetaHuman_ARKit_Mapping` | Epic's ARKit→MetaHuman PoseAsset — the only Epic ARKit mapping data that exists |
| `ABP_MH_LiveLink` | `/Game/MetaHumans/Common/Animation/ABP_MH_LiveLink` | Epic's forward converter (ARKit via Live Link → CTRL_expressions); source of the forward MouthClose rule |
| `Face_ControlBoard_CtrlRig` | `/Game/MetaHumans/Common/Face/Face_ControlBoard_CtrlRig` | MetaHuman face Control Rig; used as a curve-semantics reference |

**Forward formulas** (from `ABP_MH_LiveLink`, the non-MHFDS path):
`LipsTogether = SafeDivide(MouthClose, JawOpen)` clamped [0,1], written to all four
`CTRL_Expressions_Mouth_Lips_Together_*` curves. `JawOpenAlpha` / `TeethShowAlpha` are
runtime/manual override paths (both default 0.0; baked MHA sequences carry none of the curves
they write) — correctly ignored by the remap.

**PoseAsset extraction** (workspace: [dev/pose-asset/](../dev/pose-asset/), start at its
README): 66 poses, 274 sampled `ctrl_expressions_*` source curves, 168 baseline-adjusted
non-zero mapping records. Key facts: no MouthClose pose exists (it's post-PoseAsset ABP math);
the PoseAsset also carries `head_lod0_mesh__*` curves with negative weights (mesh layer, not
used by the remap); persistent default offsets (`nosewrinkleupperl/r`) are removed by baseline
subtraction. The extracted mapping is the forward table the V3 basis was built from.

**Face_ControlBoard_CtrlRig** (curve-semantics reference only, not a mapping source): many
`CTRL_expressions_*` channels are direct scalar pass-throughs; `mouthLeft/Right` and
`jawLeft/Right` are signed Vector2D splits; sticky-lips and swallow are phased helper curves;
eye-look is derived through Remap/Interpolate logic. Useful for classifying which curve
families can't be treated as independent evidence.

## 2. Offline RigLogic harness (no UE, no Blender GUI)

- The Poly Hammer Character DNA addon bundles prebuilt OpenRigLogic py bindings (RigLogic
  13.2.5) that run **standalone** under Blender 5.2's bundled `python.exe` (CPython 3.13):
  `%APPDATA%\Blender Foundation\Blender\5.2\extensions\api_portal_polyhammer_com\character_dna\bindings\windows\x64\py313`.
  scipy installs repo-locally via `pip install --target dev/solve/.pydeps scipy`.
- Eval pattern: `riglogic.RigLogic(dnaReader, riglogic.Configuration(), None)` →
  `riglogic.RigInstance(rigLogic=…, memRes=None)` → `setRawControl(i, v)` → `calculate(inst)`
  → `getJointOutputs()`.
- Joint outputs: flat float array, **9 attrs/joint** `[tx ty tz (cm), rx ry rz (deg euler),
  sx sy sz]`, deltas from rest pose. Archetype: 870 joints → 7830 dims. Archetype rig is
  joints-only (zero blendshapes; PSDs drive joint rows); 82 animated maps separate.
- Archetype raw controls: 263 = 251 `CTRL_expressions.*` + 12 neck/head `.q*` quat channels.
  The 251 map 1:1 (case-insensitive, `.`→`_`) onto the 251 `CTRL_expressions_*` curves in a
  live MHA stream — verified both directions, zero gaps.

## 3. ARKit basis + inverse solve quality

Evidence: [dev/reports/p1_basis_report.md](../dev/reports/p1_basis_report.md),
[dev/reports/p1_solver_validation.md](../dev/reports/p1_solver_validation.md).

- Basis `B_j = RigLogic(PA pose j) − RigLogic(PA Default)` over the 51 ARKit poses (no
  MouthClose pose): **full rank, condition number 21.8** (σ 122.6→5.6). All cosine>0.5
  overlaps anatomically expected (Smile/Dimple .85, Funnel/Pucker .84, RollLower/Press .76,
  EyeSquint/CheekSquint .67, UpperUp/NoseSneer .62, Blink/LookDown .57, LookUp/Wide .55).
- Rig is near-linear along basis directions (JawOpen/Smile/Blink dev 0.000 from proportional;
  CheekPuff worst at 1.8% — PSD correctives).
- Bounded BVLS (w∈[0,1]^51) recovers all 51 basis poses exactly (self 1.0, crosstalk 0,
  residual 0). QR-reduce once (A=QR, solve R w ≈ Qᵀd) for ~50 ms/frame.
- On a real take, ~45% of MHA deformation norm lies **outside the ARKit-52 span** — the format
  ceiling, not an error. 76/251 controls have zero ARKit-expressible response (pupils, lid
  press, tongue detail).

## 4. Result summary (first take, mirrored-ref scoring)

Evidence: [dev/reports/p2_fit_report.md](../dev/reports/p2_fit_report.md),
[dev/reports/p2_definition_score.md](../dev/reports/p2_definition_score.md).

raw per-frame solve 0.576 → fitted static graph 0.622 → + calibrated MouthClose **0.640**
mean Pearson over active curves; definition reproduces the solver at 0.943. Fit: 52 outputs =
47 ws + 4 passthrough + 1 calibrated, 55 nodes, 164 inputs, R² mean 0.92. Weakest: BrowInnerUp
(collinear brow decomposition), Dimples, RollUpper, Funnel.

Per-curve vs. real iPhone ground truth: jaw 0.96, brows 0.94–0.96, smile 0.88, blink 0.87;
full tables in [dev/reports/p2_definition_score.md](../dev/reports/p2_definition_score.md).

**Purity rule** (Dylan's hard rule): the core definition contains only what follows from
Epic's assets, real device data, and math — zero hand-tuned numbers. v2's mapping numbers were
AI-guessed and must never feed the definition (see [history.md](history.md)). Any "to-taste"
polish ships as a separate, documented, optional layer.
