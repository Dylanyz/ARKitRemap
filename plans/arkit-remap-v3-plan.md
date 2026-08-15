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
- [x] Sample set: real MHA takes + synthetic control sweeps (2026-08-14). Synthetic: `v3/scripts/synth_sweeps.py` → `v3/data/samples/synthetic_sweeps.npz` — 1870 solved samples (1255 single-control ramps, 255 pose ramps, 60 overlap-pair grids, 300 random pose mixes) + `v3/reports/p2_single_control_routing.{md,json}` = per-control ARKit routing at full activation (the definition's seed: clean 1:1s solve exact — eyeBlinkL→EyeBlinkLeft 1.0 resid 0; 76 of 251 controls have NO ARKit response, pure out-of-span: pupils, eyelid press, tongue detail, neck). Real takes solved: arkittest (1472f) + mirrortest (1601f).
  - [x] First paired ground-truth take solved (2026-08-14): Blip `20260814_DefaultSlate_2` — iPhone recorded ARKit CSV + mono video simultaneously; video processed through MHA → `AS_mp_arkittest` (demo env `/Game/ARKitRemap/arkittest` with side-by-side MetaHuman/cyclops comparison). `v3/scripts/solve_take.py` solves all 1472 frames (QR-reduced BVLS, ~1.5 min) → `v3/data/samples/arkittest_solved_weights.npz`, scored vs the calibrated iPhone CSV in `v3/reports/p2_take_comparison.{json,md}`. **Findings:** zero-lag alignment, JawOpen r=0.958; mean Pearson 0.576 over 51 active curves vs the L/R-swapped reference — **the Blip mono video is mirrored (selfie convention)**, proven data-side (gaze curves match swapped partners at +0.98, smile-asymmetry signal anti-correlates at −0.80), so MHA solves a mirror image; ARKit CSV is true face space. Strong: brows-down/outer, jaw, smile, blink, pucker (r 0.77–0.96). Weak/diagnostic: BrowInnerUp starves (LSQ gives its mass to BrowOuterUp/BrowDown), CheekSquint over-fires vs EyeSquint (cosine-0.67 pair) → fit needs regularization; mouth detail shapes (RollUpper, Funnel, Dimple, Press, JawForward) weak; MouthLeft/Right correlate better UN-mirrored (tiny amplitudes, p95<0.1 — open convention question). Mean solve residual 0.45: ~half of MHA deformation lies outside the ARKit-52 span (format ceiling). Gotcha: UE "Remove Redundant Curve Keys" strips within ~1e-3 tolerance (not lossless; fine in practice — canonical sample uses all-keys export).
- [x] Fit a sparse WS/SDK feature graph per ARKit output (2026-08-14): `v3/scripts/fit_definition.py` — per-output NNLS over routing+pose candidates, pruned, SDK shaping on nonlinear ramps; 52 outputs = 47 weighted_sum + 4 passthrough + 1 calibrated, 55 feature nodes, 164 input curves, fit R² mean 0.92. **MouthClose finding: the planned exact ABP inversion (mean lipsTogether × jawOpen) provably FAILS on MHA-origin curves** — MHA's jawOpen ≈ 0 exactly when lips are pressed (it solves appearance); the relation only holds for curves produced BY the forward ABP. MHA encodes MouthClose moments as mouthLipsThick/Push/Purse (r up to +0.76 raw). Replaced with a data-driven fit vs the measured iPhone MouthClose of the paired take, L/R-symmetrized lip-region pairs: **r=0.81, amplitude matched** (calibrated on one take — refine with more paired data).
- [x] Export `v3/RM_MHA_to_ARKit.json` (2026-08-14). JSON schema verified against Epic's own `ExportAsJsonString` of `/RigMapper/Definitions/Baked/RM_CDL_FNL`: features = name-keyed dict `{type: weighted_sum|sdk|multiply, input_features:[...], input_params:[], params:{weights|in_val/out_val|{}}}`; top-level `inputs/features/parameters/outputs/null_outputs`; ws weights may be negative/>1; no range serialization. **End-to-end score** (`score_definition.py`, arkittest take): definition vs per-frame solve r=0.943 (static graph ≈ solver); definition vs mirrored iPhone reference **mean r=0.640** — better than the raw solver's 0.576 (sparsity regularizes). Null outputs: none active-missing (all 52 emitted).

### P3 — In-engine assembly + validation
- [x] Load JSON → `/Game/ARKitRemap/RM_MHA_to_ARKit` (2026-08-14): `load_from_json_string` accepted the fitted JSON (LoadFromJsonFile wants an `unreal.FilePath` struct, string fails); round-trip via `export_as_json_string` is byte-equivalent modulo float formatting (`1.0`→`1`); v2-era draft contents replaced; asset saved. Still to do in-editor: open once, validate, re-import inputs from the face SKM.
- [~] Consumption paths: **batch Convert proven** (2026-08-14): `RigMapperEditorSubsystem.convert_anim_sequence_new(src, SK_cyclops_base_morph, [RM_MHA_to_ARKit], dir, name)` → `/Game/ARKitRemap/arkittest/AS_arkittest_V3remap` — 52 ARKit curves, per-frame keys, saved (benign warning: RCT_Vector curves skipped). Remaining: IK Retargeter Single RigMapper op + UserData discovery + live RigMapper anim node.
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

## Resolved conventions (2026-08-14, asymmetry calibration take)

Blip take `20260814_DefaultSlate_3` (wink/look/smirk/mouth-slide/jaw-shift, left block then right block; UE asset `/Game/ARKitRemap/arkittest/mirror-test/as_mirrortest`). Analysis: `v3/scripts/mirror_convention_analysis.py` → `v3/reports/p2_convention_verdicts.{json,md}`.

- **Apple ARKit naming is performer-relative for eyes/brows/smile** (EyeBlinkLeft fires on a performer-left wink) **but observer-relative for MouthLeft/MouthRight** (MouthLeft fires on a performer-RIGHT mouth slide — Apple's documented-in-the-wild quirk, confirmed on-device). JawLeft/JawRight: unverdicted, Apple's lateral-jaw signal is too weak to form events (p95 ≈ 0.03 in both takes).
- **Blip mono video is mirrored** (selfie convention) — proven three ways (gaze swap +0.98, smile asymmetry −0.80, calibration-take event order). MHA output from Blip video is therefore mirror-space; ARKit CSV is true face space. Take-2's MouthLeft/Right "contradiction" was a double flip: mirror × Apple's observer-relative mouth naming cancel out.
- **Wild ARKit rigs are NAME-CONSISTENT, not Apple-quirk-consistent** (2026-08-14, five-way demo test: video + MHA MetaHuman + Fab ARKit man + Fab cyclops + woman MH via Epic's ABP_MH_LiveLink, all playing the same take). Apple's true-space eye/wink data looked reversed against the mirrored video on ALL consumers, while mouth slides looked correct — which is only possible if the consumer shapes interpret `mouthLeft` as the character's own left (Apple's observer-relative mouth data coincides with mirror/screen space). Epic's PA convention is also name-consistent.
- **Definition-export rule (REVISED — supersedes the cross-wiring rule from earlier the same day):** emit name-consistent (Epic PA name space) outputs with NO Apple-quirk cross-wiring. The solver already produces this natively: remapped output matches the MHA MetaHuman by construction, uniformly and self-consistently, whatever the capture orientation. Dylan's directive: the remap must match the MHA balance — never replicate Apple's mixed conventions.
- **Apple-quirk handling lives on the REFERENCE side only:** when scoring solved output against Apple-recorded CSVs, L/R-swap the reference for the performer-relative shapes (what `solve_take.py` does for the mirror) and remember MouthLeft/Right in Apple data is observer-relative. Never apply these corrections to the definition output.
- **Ingest rule for ground-truth work:** either unmirror the video before MHA, or L/R-swap the ARKit reference when scoring.
- **Demo-env note:** the pure-Apple lane (cyclops et al. playing the CSV) will always show reversed eyes next to the mirrored Blip video — that is correct behavior, not a bug; ignore it or unmirror future reference video.

## Open questions

- DNA per-character vs archetype: does the remap definition need per-character fitting, or is the archetype rig close enough? (Expectation: archetype is fine — RigLogic behavior is shared; DNA differences are mostly geometry/joint placement.)
- Eye-look curves: bone-driven in MetaHuman; decide whether V3 ships weighted approximations (as v2 did) or leaves eyes to a documented Live Link passthrough.
- TongueOut and other shapes with no reliable MHA source signal: emit as NullOutputs or approximate?
