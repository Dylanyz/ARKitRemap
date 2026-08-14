# ARKit Remap V3 — Build Plan

**Status:** active (started 2026-08-14). Supersedes the v2 pipeline entirely.

## Ground rules (Dylan's direction, 2026-08-14)

1. **V2's mapping numbers are dead.** The v2 payload (`release/arkit_remap_payload.json`) was AI-guessed reverse engineering with subjective hand calibration. It is NOT a source for V3. Do not port its weights, constants, or calibrations (`lipsPurseWeight=0.735`, `jawFactor=0.75`, etc.).
2. **Only authoritative engine sources feed the mapping:**
   - `PA_MetaHuman_ARKit_Mapping` / `AS_MetaHuman_ARKit_Mapping` — Epic's actual ARKit→MHA table (re-extract fresh from the 5.8 asset with reproducible scripts; do not reuse v2's extraction files without re-verification)
   - `ABP_MH_LiveLink` runtime formulas (MouthClose = clamp(MouthClose/JawOpen) → LipsTogether controls; head rotation scaling) — mechanical facts read from the Blueprint
   - **OpenRigLogic** (github.com/EpicGames/OpenRigLogic, branch `5.8`) + a real MetaHuman head DNA — numerical evaluation of the actual rig for solving the inverse
3. **V2 research is still valid as *process* knowledge** (what the pipeline layers are, where MouthClose lives, curve name spaces, pitfalls) — that's `dev/knowledge-base.md`. Its mapping *conclusions* are not.
4. **The deliverable is a `RigMapperDefinition`** (`RM_MHA_to_ARKit`), authored/versioned as JSON in this repo, consumed via UE 5.8's RigMapper stack (see knowledge base Section K). No custom runtime code.

## Why the inverse must be solved, not transposed

Epic's PA mapping is **forward** (ARKit→MHA): each ARKit curve turns on a pose of MHA control values. Going MHA→ARKit is an inverse problem: many MHA control combinations map to the same visual result, and naive weight transposition (v2's approach) ignores how controls actually combine on the mesh. The correct inversion happens in **deformation space**:

```
Basis:  for each ARKit shape j:
          c_j = MHA control vector of PA pose j          (from fresh PA extraction)
          B_j = RigLogic(c_j)                            (blendshape + joint outputs via OpenRigLogic)

Solve:  for any MHA frame with controls c:
          d = RigLogic(c)
          w* = argmin over w in [0,1]^52 of || Σ_j w_j·B_j − d ||²   (bounded least squares / NNLS)
```

`w*` is the best ARKit-52 approximation of what the MetaHuman face is actually doing. The static definition is then **fitted** to reproduce `c → w*` over a large sample set.

## Phases

### P0 — Ground truth extraction
- [x] Fresh, scripted extraction of `PA_MetaHuman_ARKit_Mapping` (2026-08-14): `v3/data/pa_mapping.json` + `v3/scripts/extract_pa_mapping.py`. Verified pose↔frame rule (24fps grid; 0=Default, 1..51=ARKit, 52=Pose_4; Pose_5..17 off-grid, dumped unassigned). 1172 curves, 570 raw / 422 adjusted nonzero records. Confirms: NO MouthClose pose; Default carries nosewrinkleupper offsets + `ctrl_riglogic_offon` switch (exclude from fitting).
- [x] `ABP_MH_LiveLink` runtime formulas recorded mechanically from the 5.8 asset (2026-08-14): `v3/data/abp_runtime_rules.json` — full anim graph chain, MouthClose→LipsTogether×4 clamp(SafeDivide) rule, jaw/teeth alpha overrides (defaults 0), head-rotation wiring (literal MakeRotator slot assignment — corrects v2's paraphrase), MHFDS switch (sniffs `CTRL_expressions_mouthUp`; TRUE bypasses the PoseAsset entirely — strong evidence MHA real-time streams CTRL_expressions curves).
- [x] Head DNA source found (2026-08-14) — no export needed: engine ships the standard archetype at `UE_5.8/Engine/Plugins/MetaHuman/MetaHumanCoreTechLib/Content/ArchetypeDNA/SKM_Face.dna` (11MB, name "Archetype"). Loads via Poly Hammer bindings in Blender: 263 raw controls (`CTRL_expressions.browDownL` = MHA space with `.`→`_`), 174 GUI controls (`CTRL_L_brow_down.ty` = RigMapper MH-family space!), 545 PSDs, 870 joints, 8 LODs. RESOLVED (same day): the archetype rig is **joints-only** — blendShapeChannelCount / meshBlendShapeChannelMapping / per-mesh blendShapeTargets all 0; PSD correctives drive joint rows (7830×814 joint matrix), plus 82 animated maps and full geometry (24,049 verts LOD0 head). **P1 basis = joint-output space** (compare 7830-dim joint delta vectors; no skinning reconstruction needed).
- [x] MHA real-time curve names verified LIVE (2026-08-14, Dylan streaming webcam → subject "webcam"): `v3/data/mha_live_subject_curves.json`. 260 curves: 251 `CTRL_expressions_*` + `MHFDSVersion`(=1.0) + `DisableFaceOverride` + HeadYaw/Pitch/Roll + HeadTranslationX/Y/Z + HeadControlSwitch. New 5.8 MetaHumans consume it via `LiveLinkInstance` (set_subject/set_retarget_asset/enable_live_link_evaluation — NOT ABP_MH_LiveLink), which is also the model for V3's live ABP template. **This curve list is the ground-truth input set for RM_MHA_to_ARKit.**

**P0 COMPLETE (2026-08-14).**

### P1 — OpenRigLogic harness (offline Python, no UE needed)
- [x] Bindings: no build needed — the Poly Hammer Character DNA addon ships prebuilt RigLogic 13.2.5 py313 bindings; they run standalone under Blender 5.2's bundled python.exe (the P1 reference interpreter). scipy installed repo-locally to `v3/.pydeps` (gitignored) via `pip install --target`. Bootstrap/paths: `v3/scripts/p1_env.py`.
- [x] Harness (2026-08-14): `v3/scripts/riglogic_harness.py` — loads archetype DNA, evaluates raw-control vectors → joint outputs (870×9 flat: t cm / r deg euler / s, deltas from rest) + 82 animated maps. Name audit: **251/251 live MHA `CTRL_expressions_*` curves ↔ DNA raw controls, both directions clean** (case-insensitive; PA extraction lowercased FNames). Remaining 12 raw controls are neck/head `.q*` quat channels (bone-driven, not curves).
- [x] Basis (2026-08-14): `v3/scripts/build_basis.py` → `v3/data/arkit_basis_joints.npz` (B 51×7830 + control vectors + animated-map deltas) + `v3/reports/p1_basis_report.{json,md}`. B_j = RigLogic(raw pose j) − RigLogic(raw Default), evaluated through the real rig (gotcha: `raw[pose]` records are nested `{frame, curves}`). **Conditioning: full rank 51, condition number 21.8, σ 122.6→5.6** — comfortably invertible. 15 cosine>0.5 overlap pairs, all anatomically expected (Smile/Dimple .85, Funnel/Pucker .84, RollLower/Press .76, EyeSquint/CheekSquint .67, UpperUp/NoseSneer .62, Blink/LookDown .57, LookUp/EyeWide .55).
- [x] Sanity probes (2026-08-14): rig is near-linear along basis directions — JawOpen/MouthSmileLeft/EyeBlinkLeft deformation norm deviates 0.000 from linear ramp; CheekPuff worst at 1.8% (PSD correctives). Solved self-weight tracks scale.

**P1 COMPLETE (2026-08-14).**

### P2 — Inverse solve + definition fitting
- [x] Bounded least-squares per-frame solver (2026-08-14): `v3/scripts/inverse_solver.py` (`InverseSolver`, scipy BVLS on the joint-space basis, w∈[0,1]^51). Identity validation: **51/51 basis poses recovered exactly** (self weight 1.0, crosstalk 0.0, residual 0.0) — `v3/reports/p1_solver_validation.{json,md}`.
- [ ] Sample set: real MHA takes (MDR_58_tester has several) + synthetic control sweeps.
- [ ] Fit a sparse WS/SDK/MathOp feature graph per ARKit output from the samples; MouthClose/JawOpen handled by inverting the ABP formula exactly, not by tuned constants.
- [ ] Export `v3/RM_MHA_to_ARKit.json` (RigMapperDefinition JSON schema).

### P3 — In-engine assembly + validation
- [ ] Load JSON → `/Game/ARKitRemap/RM_MHA_to_ARKit` (replace the 2026-06 draft asset, which was built with v2-derived thinking), validate in the 5.8 definition editor, re-import inputs from the face SKM.
- [ ] Wire the three consumption paths: right-click Convert action, IK Retargeter Single RigMapper op, and confirm UserData discovery.
- [ ] Comparison harness: same take as (a) V3 definition output vs (b) raw iPhone ARKit reference (Live Link Face recording). Metrics per curve + visual passes. **No v2 output in the comparison baseline** — v2 is not a reference.

### P4 — Live preview + packaging
- [ ] Template AnimBP: Live Link Pose (MHA subject) → Rig Mapper node → output; Alpha as blend; implement `BPI_RigMapper` (EnableRigMapper / OverrideDefinitions) for the toggle.
- [ ] UserData stamping helper (one-click "tag this character").
- [ ] Guides: how the MetaHuman LiveLink/AnimBP system works; setting up an ARKit-52 character (generic — FaceIt as documented example) for baked + live use.
- [ ] Repo restructure: v2 `release/` + payload → `legacy/`; V3 package = definition JSON + ABP template + guides.

## Key technical references

- `dev/knowledge-base.md` Section K — full UE 5.8 RigMapper system survey (data model, JSON, anim node, retarget ops, editor subsystem, utilities, shipped defs)
- `dev/knowledge-base.md` Sections C/D — forward pipeline + PA asset (process knowledge; re-verify data before use)
- OpenRigLogic docs: https://EpicGames.github.io/OpenRigLogic + `docs/design/design.md` in the repo (RigLogic 4 design: PSD → linear → conditional stages)
- RigLogic whitepaper PDF (DNA format, runtime strategy)

## Open questions

- DNA per-character vs archetype: does the remap definition need per-character fitting, or is the archetype rig close enough? (Expectation: archetype is fine — RigLogic behavior is shared; DNA differences are mostly geometry/joint placement.)
- Eye-look curves: bone-driven in MetaHuman; decide whether V3 ships weighted approximations (as v2 did) or leaves eyes to a documented Live Link passthrough.
- TongueOut and other shapes with no reliable MHA source signal: emit as NullOutputs or approximate?
