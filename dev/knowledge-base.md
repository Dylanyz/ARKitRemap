# ARKit Remap Knowledge Base

Detailed reference for the MHA-to-ARKit facial animation remapping pipeline. This document is read by future chats when the arkit-remap skill directs them here. It is designed to be updated incrementally as new data is discovered.

---

## Revision Log

| Date | Change | Source |
|------|--------|--------|
| 2026-03-12 | Added `import_arkit_animsequence_as_livelinkface.py` helper to convert a remapped ARKit `AnimSequence` into a Live Link Face-imported `LevelSequence` for direct MetaHuman ARKit-pipeline playback. Verified on `/Game/3_FaceAnims/arkit-remap-demo/AS_arkitremap-demo-main_ARKit`: wrote CSV at ~59.94 fps, imported `/Game/3_FaceAnims/arkit-remap-demo/arkitremap-demo-main_ARKit_cal`, and confirmed subject name `arkitremap-demo-main_ARKit`. | MetaHuman ARKit playback helper |
| 2026-03-12 | Release-prep cleanup pass: added `.cursor/arkit-remap/README.md` as the workspace entry point, refreshed `release/README.md` and `PUBLISH_TO_PUBLIC_REPO.md` for the Python-first package, corrected stale LipsPurse / clamp references in active docs, and began moving deprecated probes/one-off diagnostics into archive locations. | Release preparation + workspace cleanup |
| 2026-03-12 | **Apples-to-Apples visual comparison completed (A vs B).** Built `forward_remap_to_mh.py` (transposes PoseAsset weights, ARKit→ctrl_expressions, MouthClose→LipsTogether). Round-trip test: remap allkeys→ARKit→forward back to ctrl_expressions. Visual review on MetaHuman at frames 0/276/956/1087 confirms B tracks A well. Numerics: eye/nose MSE=0 (perfect 1:1 round-trip); jaw MSE=0.013 (purse comp); mouth MSE=0.043 (LipsTogether path); brow MSE=0.019; tongue MSE=0.105 (shared contributors). Top round-trip error: `mouthlipstogether` (0.45 MSE) from MouthClose lossy derivation. Real iPhone ARKit forward-pass (C) was attempted but broken: template duplication leaves ~220 residual ctrl_expressions curves from A that contaminate C's output. Fixing C would require clearing ALL curves from template or using PoseAsset node at runtime — deferred as low priority since A vs B is the actionable comparison. Reports: `.cursor/arkit-remap/reports/apples_comparison_*.{json,md}`. Scripts: `forward_remap_to_mh.py`, `run_apples_pipeline.py`, `compare_apples.py`. | Apples-to-apples MH comparison |
| 2026-03-12 | Unified "visual opening" model with calibrated params. Definitive alignment: ARKit baked frame 20724 @ 60fps = MHA frame 0 (offset 345.4s). 3D grid search across 1450 matched frame pairs found real ARKit has mouthClose > jawOpen 25% of the time, so forward constraint relaxed to 1.5× (`forwardConstraintRatio`). Calibrated: `lipsPurseWeight=0.735`, `forwardConstraintRatio=1.5`, `jawFactor=0.75` retained. Frame 956 mouthClose: 0.140→**0.202** (ref 0.203, error 0.0004). | Definitive alignment + calibration |
| 2026-03-12 | JawOpen purse compensation: reduces JawOpen when LipsPurse is active. On MetaHuman, LipsPurse physically counteracts JawOpen at the mesh level; FaceIt characters treat them independently, so high JawOpen (~0.53) stays visible. New post-pass: `adjustedJawOpen = max(0, jawOpen - factor * mean(LipsPurse))`. With factor=0.75 at frame 956: JawOpen 0.53→0.15 (real ARKit ~0.1). Runs after MouthClose computation so MouthClose retains original JawOpen signal. Combined with MouthClose LipsPurse fix, closed-mouth frames now produce jawOpen≈0.15 + mouthClose≈0.14 instead of jawOpen≈0.53 + mouthClose≈0.006. | Continued mouth-not-closing fix |
| 2026-03-12 | MouthClose derivation fix: added LipsPurse curves as contributor (lipsPurseWeight now calibrated to 0.735). MHA achieves mouth closure through LipsPurse (~0.5) even at high JawOpen (~0.53), but the old formula only used LipsTowards (~0.01), producing near-zero MouthClose on closed-mouth frames. New formula: `lip_closure = mean(LipsTowards) + lipsPurseWeight * mean(LipsPurse)`. Frame 956 of AS_MP_VecDemo1-allkeys: MouthClose improved from 0.006 → 0.140 (weight=0.5) → **0.202** (weight=0.735, ref 0.203). | Mouth-not-closing diagnostic investigation + calibration |
| 2026-03-12 | Closed UNKNOWN 2 for the current reverse pipeline assumptions and partially de-risked UNKNOWN 4. Added `verify_abp_post_poseasset.py` plus `abp_post_poseasset_verification.md`/`.json`: representative baked MHA sequence lacks the post-PoseAsset jaw/teeth override curves, and `ABP_MH_LiveLink` defaults `JawOpenAlpha = 0.0`, `TeethShowAlpha = 0.0`, so these nodes behave like runtime/manual overrides rather than baked signals. Added `mapping-pose-asset/scripts/verify_pose_asset_linearity.py` plus matching report/data outputs: source animation is `AAT_NONE` with `LINEAR` interpolation and the first clean segment (`EyeBlinkLeft`) samples exactly linearly at `0.25 / 0.5 / 0.75 / 1.0`, while transient runtime curve readback remains inconclusive from Python. | ABP + PoseAsset verification pass |
| 2026-03-12 | Expanded Section D.3 (`Face_ControlBoard_CtrlRig`) with deeper Control Rig findings: confirmed the rig is bidirectional (Backwards Solve and Forwards Solve), identified direct-vs-derived curve families (direct scalar, signed/vector splits, phased helper curves), cross-checked `ABP_Face_PostProcess` runtime context, and clarified that the Control Board is best used as a curve-layer QA/reference source rather than a new primary reverse-mapping source. | Deeper Face_ControlBoard_CtrlRig + ABP_Face_PostProcess analysis |
| 2026-03-12 | Added grouped brow solve to the Python remapper: `BrowInnerUp`, `BrowOuterUpLeft`, and `BrowOuterUpRight` now solve jointly via `coupledGroups` instead of independent/chained pair logic. `roundtrip_validation.py` now honors payload `minWeight`, `coupledPairs`, and `coupledGroups`; current payload reconstructs all 51 targets exactly in the built-in synthetic scenarios. In-editor run on `/Game/3_FaceAnims/VEC_MHA/AgenticPy/AS_MP_VecDemo1-allkeys` completed successfully and wrote updated QA logs. | Grouped brow solve implementation |
| 2026-03-12 | Added Section D.3: Face_ControlBoard_CtrlRig. Documents the MetaHuman face Control Rig (curve layer vs control layer, Get/Set Curve Value, Remap/Interpolate nodes). Relevance: pipeline stays on curve layer; non-linearity risk supports Item 12; mesh curves (UNK 1) unchanged. Asset added to Asset Index. | Face_ControlBoard_CtrlRig MCP analysis |
| 2026-03-12 | Context-menu launcher updated: `Run ARKit Remap` now opens a smoothing selection dialog for the current run (`None`, `One-Euro`, `EMA`) and passes a one-shot runtime override into `arkit_remap.py` without modifying the payload file. UI note: the entry currently appears in the main Content Browser context menu rather than under `Asset Actions`. Epic/MetaHuman note added: these smoothing modes are custom remapper post-process options, not Epic's built-in MetaHuman smoothing mode. | Context-menu smoothing prompt |
| 2026-03-12 | Major pipeline update: (1) minWeight threshold filter removes browlaterall 0.031 artifact from 10+ targets, (2) coupled 2x2 least-squares solve for MouthPucker↔MouthFunnel and MouthRollLower↔MouthRollUpper eliminates cross-contamination (Funnel error: 125%→0%, RollUpper error: 53%→0%), (3) MouthClose clampMax raised from 0.3 to 0.5, (4) clamp-boundary alerting in QA reports, (5) optional temporal smoothing via 1-euro filter or EMA, (6) round-trip validation framework created. See improvement log. | Architecture QA improvement implementation |
| 2026-03-12 | Python ARKit remap run logs now default to `.cursor/arkit-remap/reports/run-logs/` instead of the parent `reports/` folder. Updated script, release mirror, and canonical docs to match. | Run-log path update |
| 2026-03-12 | UNKNOWN 1 resolved: PoseAsset DOES have negative weights, confirmed via Editor UI. Negative values (-0.079874) found on `head_lod0_mesh__*` curves (e.g., MouthPressRight suppresses chin-raise shapes). Extraction only captured `ctrl_expressions_*` curves, which remain all-positive. Follow-up: verify MHA bakes don't contain mesh-level curves. Report and scorecard updated. | User confirmation via Editor |
| 2026-03-12 | Deep QA analysis completed: 7 substantive gaps identified (browlaterall 0.031 artifact, Pucker↔Funnel cross-contamination, MouthClose clamp too conservative, no round-trip validation, EyeSquint outer missing, RollLower/Upper cross-coupling, community mapping discrepancies). 5 improvement opportunities documented. Report at `.cursor/arkit-remap/reports/2026-03-12_architecture-qa-deep-analysis.md` | Architecture QA deep analysis |
| 2026-03-12 | MouthClose derivation fixed: replaced broken `ctrl_expressions_mouth_lips_together_ul` source with `mean(ctrl_expressions_mouthlipstowards{ul,ur,dl,dr}) * JawOpen`. Empirically validated on AS_MP_VecDemo1-allkeys (min=0.0004, max=0.3, mean=0.092). Pipeline now outputs 52/52 ARKit curves. | MouthClose reverse engineering plan |
| 2026-03-12 | Added Python ARKit Remap v2 pipeline (Section E.6). Replaces Blueprint AnimModifier as primary remap method. Marked AM_ArKitRemap / AM_ArKitRemap_v02 as legacy/fallback. | Python pipeline documentation |
| 2026-03-11 | Documented working hypothesis that `MouthClose` is not a direct PoseAsset output and is likely derived in `ABP_MH_LiveLink` post-PoseAsset graph math (`SafeDivide(MouthClose, JawOpen)` -> lips-together controls) | MouthClose derivation hypothesis |
| 2026-03-11 | Added explicit v01 vs v02 animation-modifier comparison summary in Section E.5, including data inputs and known remaining gaps | AM_ArKitRemap version-tracking update |
| 2026-03-11 | Executed AM_ArKitRemap_v02 revision workflow: scope-lock run brief, compact AM_v02 payload generation, non-destructive QA report, and initial weighted/calibrated OnApply logic pass in AM_ArKitRemap_v02 | arkit_v02_full_revision_5c2582b0 |
| 2026-03-11 | Added reverse-map validation step/report and marked Step 1 ready with structural checks (while tracking missing `MouthClose` as data gap) | mapping-pose-asset reverse map validation |
| 2026-03-11 | Added reverse-map derivative workflow guidance: split core-vs-extended output structure, AGENT_INDEX usage, and maintenance sync protocol for index/KB/skill updates | mapping-pose-asset reverse map organization |
| 2026-03-11 | Section D/J updated with extracted pose-asset mapping workspace, concise extraction summary, and navigation guide for using AGENT_INDEX + folder artifacts | mapping-pose-asset extraction workspace |
| 2026-03-11 | Initial creation: all sections A-J populated from research chat | Initial analysis chat |

---

## Table of Contents

- [A. Asset Index](#a-asset-index)
- [B. The 52 ARKit Blendshapes](#b-the-52-arkit-blendshapes)
- [C. Forward Pipeline: ARKit to MetaHuman (ABP_MH_LiveLink)](#c-forward-pipeline)
- [D. PA_MetaHuman_ARKit_Mapping](#d-pa_metahuman_arkit_mapping)
  - [D.3 Face_ControlBoard_CtrlRig](#d3-face_controlboard_ctrlrig)
- [E. Reverse Pipeline: MHA to ARKit](#e-reverse-pipeline)
  - [E.6 Python ARKit Remap v2 (primary method)](#e6-python-arkit-remap-v2-primary-method)
- [F. FaceIt Integration](#f-faceit-integration)
- [G. Known Mapping Challenges](#g-known-mapping-challenges)
- [H. Scrutiny and Gap Analysis](#h-scrutiny-and-gap-analysis)
- [I. Quality Issues and Improvement Roadmap](#i-quality-issues-and-improvement-roadmap)
- [J. Ways to Extract PA Data](#j-ways-to-extract-pa-data)

---

## A. Asset Index

| Asset | Type | Unreal Path | Role |
|-------|------|-------------|------|
| ABP_MH_LiveLink | AnimBlueprint (AnimInstance) | `/Game/MetaHumans/Common/Animation/ABP_MH_LiveLink` | Epic's forward converter: ARKit via LiveLink to MHA CTRL_expressions. Reference for reverse engineering. |
| PA_MetaHuman_ARKit_Mapping | PoseAsset | `/Game/MetaHumans/Common/Face/ARKit/PA_MetaHuman_ARKit_Mapping` | Stores per-ARKit-curve to MHA weighted mappings. Used by ABP_MH_LiveLink AnimGraph. Opaque to MCP summary tool. |
| Face_ControlBoard_CtrlRig | Control Rig Blueprint | `/Game/MetaHumans/Common/Face/Face_ControlBoard_CtrlRig` | MetaHuman face Control Rig: maps CTRL_expressions curves to rig controls (CTRL_L_* / CTRL_C_*). Summarizable via MCP. See Section D.3. |
| AM_ArKitRemap | AnimationModifier | `/Game/3_FaceAnims/AM_ArKitRemap` | Our reverse converter. Applied to baked MHA animation sequences to produce ARKit-named curves for FaceIt characters. |
| arkitremap-demo-main_ARKit_cal | LevelSequence | `/Game/3_FaceAnims/arkit-remap-demo/arkitremap-demo-main_ARKit_cal` | Live Link Face-imported playback asset generated from the remapped ARKit AnimSequence. Publishes subject `arkitremap-demo-main_ARKit` so `ABP_MH_LiveLink` can consume the remap through the standard MetaHuman ARKit path. |
| metahuman_base_skel | Skeleton | `/Game/MetaHumans/Common/Female/Medium/NormalWeight/Body/metahuman_base_skel` | MetaHuman skeleton referenced by ABP_MH_LiveLink. |
| MH_Arkit_Mapping.txt | Reference file | `.cursor/arkit-remap/MH_Arkit_Mapping.txt` | Community-sourced 1:1 mapping table (52 entries). Not authoritative; for reference only. Credits: Csaba Kiss, Tomhalpin8. |

---

## B. The 52 ARKit Blendshapes

```
eyeBlinkLeft           eyeLookDownLeft        eyeLookInLeft
eyeLookOutLeft         eyeLookUpLeft          eyeSquintLeft
eyeWideLeft            eyeBlinkRight          eyeLookDownRight
eyeLookInRight         eyeLookOutRight        eyeLookUpRight
eyeSquintRight         eyeWideRight           jawForward
jawLeft                jawRight               jawOpen
mouthClose             mouthFunnel            mouthPucker
mouthLeft              mouthRight             mouthSmileLeft
mouthSmileRight        mouthFrownLeft         mouthFrownRight
mouthDimpleLeft        mouthDimpleRight       mouthStretchLeft
mouthStretchRight      mouthRollLower         mouthRollUpper
mouthShrugLower        mouthShrugUpper        mouthPressLeft
mouthPressRight        mouthLowerDownLeft     mouthLowerDownRight
mouthUpperUpLeft       mouthUpperUpRight      browDownLeft
browDownRight          browInnerUp            browOuterUpLeft
browOuterUpRight       cheekPuff              cheekSquintLeft
cheekSquintRight       noseSneerLeft          noseSneerRight
tongueOut
```

MetaHuman uses ~130+ `CTRL_expressions` curves. The PA_MetaHuman_ARKit_Mapping PoseAsset maps between these two systems with weights.

---

## C. Forward Pipeline

### ABP_MH_LiveLink: ARKit to MetaHuman

**Parent class:** AnimInstance
**On-disk size:** ~336 KB
**References:** metahuman_base_skel, PA_MetaHuman_ARKit_Mapping

### C.1 Event Graph

Runs on `Event Blueprint Update Animation`:

1. **Evaluate Live Link Frame** using `LLink_Face_Subj` (LiveLink subject name).
2. On valid frame:
   - **MHFDS detection:** Gets `CTRL_expressions_mouthUp` from LiveLink data. If present (OR `ForceMHFDS` is true), sets `IsMHFDS = true`. This detects whether the input is MetaHuman Facial Description Standard format.
   - **Head rotation** (out of scope for our reverse pipeline): Extracts `headYaw`, `headRoll`, `headPitch` from LiveLink frame. Multiplies yaw by -50, roll by 50, pitch by 50. Makes a Rotator and stores in `ARKit_HeadRotation`. Only applies if `IsMHFDS` is false AND `LLink_Face_Head` is true.

### C.2 AnimGraph

Flow (for the non-MHFDS / ARKit path, which is what we reverse):

1. **Copy Pose From Mesh** -> Save cached pose `BodyPose`
2. **Live Link Pose** (input: BodyPose, subject: LLink_Face_Subj, evaluation: true) -> applies LiveLink curves
3. **PA_MetaHuman_ARKit_Mapping** node -> converts ARKit-named curves into MHA CTRL_expressions
4. **Modify Curve (CustomControlValues)** -> applies any user-set custom control overrides
5. **Mouth Close block:**
   - Get Curve Value `MouthClose` and `JawOpen`
   - `SafeDivide(MouthClose, JawOpen)` -> `Clamp(0, 1)`
   - Writes result to `CTRL_Expressions_Mouth_Lips_Together_DL`, `DR`, `UL`, `UR` (all four get the same value)
6. **Slot 'DefaultSlot'** (animation slot)
7. **Modify Curve: CTRL_Expressions_Jaw_Open = 1.0** with alpha from `JawOpenAlpha`
8. **Modify Curve (Teeth):** Sets `CTRL_Expressions_Mouth_Lower_Lip_Depress_L/R`, `Upper_Lip_Raise_L/R`, `Corner_Pull_L/R`, `Stretch_L/R` all to 1.0 with alpha from `TeethShowAlpha`
9. **Layered blend per bone** (Base: BodyPose, Blend: face curves from above)
10. **Modify Curve: Head Control Switch = 1.0**
11. **Modify Curve: Head Roll/Yaw/Pitch** from `ARKit_HeadRotation` (converted via Rotator -> Quaternion -> Euler -> Break Vector)
12. **Blend Poses by bool (IsMHFDS):** If MHFDS=true, uses raw LiveLink pose (True branch). If false, uses the processed chain above (False branch). **Our reverse targets the False (processed) branch.**

### C.3 Key formulas

**Forward (what Epic does):**
- `LipsTogether = SafeDivide(MouthClose, JawOpen)` clamped [0, 1]
- `CTRL_Expressions_Mouth_Lips_Together_DL = DR = UL = UR = LipsTogether`
- Jaw, Teeth, Head curves are set with runtime alphas (JawOpenAlpha, TeethShowAlpha)

**Reverse (what we need to invert):**
- `MouthClose = LipsTogether * JawOpen` (AM_ArKitRemap implements this)
- `JawOpenAlpha` / `TeethShowAlpha` do not currently require inversion in the reverse pipeline. Verification pass (`verify_abp_post_poseasset.py`) found the representative baked MHA sequence lacks the jaw/teeth override curves written by those nodes, while the `ABP_MH_LiveLink` class defaults both alphas to `0.0`. Treat them as runtime/manual override paths rather than baked remap signals unless future evidence shows otherwise.

### C.4 Variables

| Variable | Type | Purpose |
|----------|------|---------|
| LLink_Face_Subj | LiveLinkSubjectName | LiveLink face subject |
| ARKit_HeadRotation | Rotator | Head rotation from LiveLink (out of scope) |
| JawOpenAlpha | float | Scales CTRL_Expressions_Jaw_Open |
| TeethShowAlpha | float | Scales teeth curves |
| LLink_Face_Head | bool | Whether to apply head rotation |
| CustomControlValues | Map<Name, float> | User override curves |
| IsMHFDS | bool | Is MetaHuman Facial Description Standard |
| ForceMHFDS | bool | Force MHFDS mode |

---

## D. PA_MetaHuman_ARKit_Mapping

**Type:** PoseAsset
**Path:** `/Game/MetaHumans/Common/Face/ARKit/PA_MetaHuman_ARKit_Mapping`
**Referenced by:** ABP_MH_LiveLink AnimGraph (node #1732672494)

This PoseAsset is the core mapping layer. It takes a pose with ARKit-named curves and outputs MHA CTRL_expressions curves. The MCP summary tool cannot read PoseAssets (only Blueprints, Materials, Behavior Trees).

### What we know

- It is used as an AnimGraph node immediately after the Live Link Pose node
- It converts ARKit-style curve names (e.g. MouthClose, JawOpen) into CTRL_expressions
- The conversion is **not 1:1**: each ARKit curve likely drives multiple MHA curves with weights, and multiple MHA curves may contribute to a single ARKit semantic
- The Pose Asset stores this as named poses with curve weights

### D.1 PA Weight Data (TO BE FILLED)

**Status:** extracted and available in a dedicated workspace.

- Canonical extraction workspace:
  - `.cursor/arkit-remap/mapping-pose-asset`
- Canonical index for humans/agents:
  - `.cursor/arkit-remap/mapping-pose-asset/AGENT_INDEX.md`

**What was extracted (concise):**

- Pose count: `66` (includes `Default`, ARKit poses, and additional `Pose_4`-`Pose_17`)
- Relevant sampled source curves: `274` (`ctrl_expressions_*`)
- Baseline-adjusted non-zero records: `168`
- Raw non-zero records: `300`
- Main raw-vs-adjusted difference: persistent default offsets (primarily `ctrl_expressions_nosewrinkleupperl/r`) are removed by baseline subtraction

**Where the mapping records live:**

- Adjusted mapping dataset (recommended for remap logic):  
  `.cursor/arkit-remap/mapping-pose-asset/data/PA_MetaHuman_ARKit_Mapping.posemap.json`
- Raw mapping dataset (audit/debug):  
  `.cursor/arkit-remap/mapping-pose-asset/data/PA_MetaHuman_ARKit_Mapping.posemap.raw.json`
- Derived reverse mapping table (weighted reverse input):  
  `.cursor/arkit-remap/mapping-pose-asset/data/PA_MetaHuman_ARKit_Mapping.reverse_map.json`
- Linearity verification dataset (runtime probe + source-animation fractional sample):  
  `.cursor/arkit-remap/mapping-pose-asset/data/PA_MetaHuman_ARKit_Mapping.linearity_verification.json`

Each mapping record is represented as:
- `arkitPoseName`
- `sourceMhaCurveName`
- `weight`
- `sampleTimeOrFrame`

This is now the primary source to move AM_ArKitRemap from a 1:1 rename approach to weighted reverse mapping.

The reverse mapping JSON provides both:
- `reverseMappingTable` (full combined list), and
- `reverseMappingTableByClass`:
  - `arkit52` (core remap targets),
  - `extended_pose` (`Pose_4` to `Pose_17`),
  - `other_targets`.

Working hypothesis (2026-03-11, **confirmed 2026-03-12**):
- Missing `MouthClose` in extracted reverse-map rows is expected, not an extraction defect.
- `MouthClose` is handled as runtime/post-PoseAsset logic in `ABP_MH_LiveLink` (via `SafeDivide(MouthClose, JawOpen)` -> lips-together controls), not as a direct PoseAsset target.
- **Resolution:** the Python pipeline now derives MouthClose using `mean(ctrl_expressions_mouthlipstowards{ul,ur,dl,dr}) * JawOpen` as a proxy. Empirically validated on AS_MP_VecDemo1-allkeys; all 52/52 ARKit curves are now produced.
- Confidence: **high** — empirical probe confirmed LipsTowards curves exist on baked animations, correlate properly, and produce physically plausible MouthClose values.

### D.2 Community-sourced 1:1 mapping (reference only)

A community-sourced mapping table exists at `.cursor/arkit-remap/MH_Arkit_Mapping.txt`. This was compiled from a YouTube video by Csaba Kiss and forum posts by Tomhalpin8. **This is subjective/approximate and NOT from Epic.** It maps each of the 52 ARKit names to a single "best guess" MHA curve. Notable entries:

- MouthClose -> ctrl_expressions_mouthlipspurseul (note: this is Lips Purse, not Lips Together)
- MouthPucker -> ctrl_expressions_mouthlipspurseur
- MouthFunnel -> ctrl_expressions_mouthfunnelul
- EyeLookOutLeft -> ctrl_expressions_eyelookleftl (note: Out maps to Left, In maps to Right; cross-mapping)
- EyeLookInLeft -> ctrl_expressions_eyelookrightl

These naming choices affect whether the AM_ArKitRemap CurveMap produces correct results.

### D.3 Face_ControlBoard_CtrlRig

**Type:** Control Rig Blueprint (Parent: ControlRig)  
**Path:** `/Game/MetaHumans/Common/Face/Face_ControlBoard_CtrlRig`  
**On-disk size:** ~11 MB  
**Referenced by:** 3 other assets. **References:** CRSL_MetaHuman_Gizmo, DefaultGizmoLibrary.  
**Instance variable:** `eyes_aim_rig` (bool).

This asset is the MetaHuman face Control Rig. It was analyzed via MCP `get_detailed_blueprint_summary` and cross-checked against `ABP_Face_PostProcess`. MCP cannot read PoseAssets, but it can read Control Rig Blueprints and AnimBlueprint summaries, which makes this rig useful as a semantic reference for the `CTRL_expressions_*` layer.

**Two layers in the rig:**

- **Curve layer:** The rig reads and writes the same curve namespace the pipeline uses: **CTRL_expressions_***. The graph contains 253 unique curve names (Unreal uses mixed case in the rig, e.g. `CTRL_expressions_mouthFunnelUR`; we use lowercase in payload and AnimSequences).
- **Control layer:** 418 rig control elements (e.g. `CTRL_L_brow_down`, `CTRL_L_mouth_purseD`, `CTRL_C_jaw`, `CTRL_C_tongue_roll`). These are the Control Rig’s internal controls (gizmos/bones) that drive the mesh — *not* the same as curve names.

**Graph structure:** One main Rig Graph. Execution includes both **Backwards Solve** and **Forwards Solve**, which means the rig is bidirectional rather than a one-way driver. Approximate node counts: **263 Get Curve Value**, **260 Set Curve Value**, **154 Get Control Float**, **152 Set Control Float**, 15 Get / 13 Set Control Vector2D, plus **93 Remap**, 89 Add, **9 Interpolate**, **9 Evaluate Curve**, and transform nodes (Set/Get Transform - Control/Bone, Aim, etc.). There is a Construction Event (Set Transform - Control Initial) and a `// Setup_Eye_Controls` block.

**What the deeper graph read shows:**

- **Many curves are direct scalar pass-throughs.** Brow (`browRaiseIn*`, `browRaiseOuter*`, `browLateral*`), many mouth funnel/purse/stretch/corner curves, and several jaw/chin curves are read from `CTRL_expressions_*` and written straight into corresponding control floats with no visible remap in between.
- **Some curves are signed/vector splits rather than independent channels.** `mouthLeft` / `mouthRight` and `jawLeft` / `jawRight` are derived from signed Vector2D controls (`CTRL_C_mouth`, `CTRL_C_jaw`) using clamp/remap logic. `mouthCheekSuck*` / `mouthCheekBlow*` similarly behave like antagonistic pairs derived from a shared latent control.
- **Some curves are clearly helper/phase curves.** `mouthLipsSticky*Ph1/2/3` and `neckSwallowPh1..5` are generated through `Evaluate Curve` nodes and threshold-style phasing rather than simple linear pass-through.
- **Eye-look is derived, not a pure baked scalar family.** Eye look curves are created through `Remap`, `Interpolate`, and clamp logic tied to eye controls and `lookAtSwitch`.
- **No `head_lod0_mesh__*` curves were found in this rig graph.** The Control Board appears to live entirely in the `CTRL_expressions_*` namespace.

**Runtime context cross-check (`ABP_Face_PostProcess`):**

- `ABP_Face_PostProcess` does **not** directly reference `Face_ControlBoard_CtrlRig` in the summary obtained through MCP.
- The confirmed post-process stack there is: input pose -> optional `CR_MetaHuman_HeadMovement_IK_Proc` Control Rig (gated by `HeadControlSwitch` and `EnableHeadMovementIK`) -> `AnimNode_RigLogic`.
- This suggests the final facial deformation path is not simply "Control Board drives face mesh directly." For reverse-mapping purposes, the Control Board is best treated as a **reference for the curve/control semantic layer**, not proof of the final runtime deformation equation.

**Relevance to ARKit remap:**

1. **Useful as a QA oracle, not a new primary source:** The Control Board helps explain what kind of signal each `CTRL_expressions_*` curve represents, but it should not replace PoseAsset-derived weights as the primary reverse source.
2. **Curve-family classification opportunity:** The rig makes it possible to categorize source curves as:
   - direct scalar channels,
   - signed/vector split channels,
   - phased/helper channels.
   This is useful for future QA and interpretation of shared-source errors.
3. **Linearity risk is narrower than it first appeared:** The rig is not uniformly non-linear. Many channels are direct. The non-linear risk is concentrated in specific families (eye look, sticky, swallow, signed splits). This sharpens Item 12: the question is less "is the whole rig non-linear?" and more "which families should not be treated as independent primary evidence?"
4. **Brow findings are supported, not contradicted:** Brows appear mostly direct in the Control Board. That supports the conclusion that `browlaterall` contamination is primarily a PoseAsset/shared-weight issue, not a Control-Rig-induced transform artifact.
5. **Two curve layers (UNK 1) still stand:** The PoseAsset uses both `ctrl_expressions_*` and `head_lod0_mesh__*`. The Control Board only showed `CTRL_expressions_*`; no mesh-level curves were found here. The most likely remaining location for mesh-layer behavior is elsewhere in the face runtime stack (for example around RigLogic), so UNK 1 remains the correct follow-up.

*Sources: MCP `get_detailed_blueprint_summary` on `Face_ControlBoard_CtrlRig`, MCP `get_asset_summary` on `ABP_Face_PostProcess` and `CR_MetaHuman_HeadMovement_IK_Proc`, 2026-03-12. Summary also recorded in `.cursor/plans/arkit-remap-improvementlog.md` (Insights from Face_ControlBoard_CtrlRig).*

---

## E. Reverse Pipeline

> **Primary method is now Section E.6 (Python ARKit Remap v2).** Sections E.1–E.5
> below document the legacy Blueprint AnimModifier approach (`AM_ArKitRemap` /
> `AM_ArKitRemap_v02`), retained as fallback reference.

### AM_ArKitRemap: MHA to ARKit (legacy)

**Type:** AnimationModifier (applied to animation sequences via right-click -> Add Modifier)
**Path:** `/Game/3_FaceAnims/AM_ArKitRemap`
**Parent class:** AnimationModifier
**On-disk size:** ~131 KB
**Referenced by:** 11 other assets (animation sequences using this modifier)
**Status:** Legacy/fallback — superseded by the Python pipeline (E.6).

### E.1 Variables

| Variable | Type | Purpose |
|----------|------|---------|
| CurveMap | Map<Name, Name> | Source (MH) curve name -> Target (ARKit) curve name. Instance editable. |
| ProcessedValues | Array<float> | Temp storage for MouthClose fix computation |
| MC_Times | Array<float> | MouthClose keyframe times |
| MC_Values | Array<float> | MouthClose keyframe values |
| JO_Values | Array<float> | JawOpen keyframe values |

### E.2 Event Graph: On Apply

**Block A - Transfer Curves (rename):**

1. For each entry in CurveMap:
   - Check if source curve exists in the animation sequence (`Does Curve Exist`)
   - If yes: `Get Float Keys` (times + values) from the source curve
   - `Add Curve` with the **target** (ARKit) name
   - `Add Float Curve Keys` with the same times and values
2. This is a 1:1 copy with a name change. No value transformation.

**Block B - Fix MouthClose and JawOpen:**

3. After all CurveMap entries are processed (loop Completed):
   - `Get Float Keys` for curve named `MouthClose` (now the ARKit-named curve from Block A)
   - Store times in `MC_Times`, values in `MC_Values`
   - `Get Float Keys` for curve named `JawOpen`
   - Store values in `JO_Values`
4. For each frame (For Each Loop over MC_Values):
   - Get the JawOpen value at the same index
   - `processed = MouthClose_value * JawOpen_value`
   - `Clamp(processed, 0.0, 0.3)` (comment in blueprint: "Play with this max value if your mouth is deformed!")
   - Add to `ProcessedValues` array
5. Remove the existing `MouthClose` curve
6. Add a new `MouthClose` curve
7. Write `MC_Times` and `ProcessedValues` as the new keys

**Execution order matters:** Block A runs first (populating ARKit-named curves including MouthClose and JawOpen), then Block B overwrites MouthClose with the processed values. So Block B reads the already-renamed curves.

### E.3 Key formula

Inverse of Epic's forward:
- Forward: `LipsTogether = SafeDivide(MouthClose, JawOpen)` clamped [0, 1]
- Reverse: `MouthClose = LipsTogether * JawOpen` clamped [0, 0.3]

The 0.3 upper clamp is conservative (vs the forward's 1.0 range) to prevent mouth deformation on FaceIt characters. It is tunable.

### E.4 AM_ArKitRemap_v02 revision snapshot (2026-03-11)

Target asset:
- `/Game/3_FaceAnims/AM_ArKitRemap_v02`

New controls added in v02 pass:
- `bUseWeightedCoreRemap`
- `bEnableExtendedPoseTargets`
- `GlobalScale`, `GlobalOffset`, `GlobalClampMin`, `GlobalClampMax`
- `MouthCloseScale`, `MouthCloseClampMax`

v02 behavior currently implemented:
- Keeps base transfer path from `CurveMap`.
- Adds weighted synthesis branch (guarded by `bUseWeightedCoreRemap`) for at least one core multi-contributor target path (`MouthFunnel`) with global calibration.
- Adds explicit `MouthClose` branch using lips-together semantics:
  - `CTRL_Expressions_Mouth_Lips_Together_UL * JawOpen`,
  - scaled by `MouthCloseScale`,
  - offset by `GlobalOffset`,
  - clamped to `0..MouthCloseClampMax`.

Verification caveat:
- MCP summary output shows generated `OnApply` graph plus legacy EventGraph nodes. Runtime execution order should be validated in-editor on a test sequence before claiming full parity.

### E.5 Animation Modifier Versions: v01 vs v02

This section is the canonical change log for `AM_ArKitRemap` behavior across modifier versions.

#### v01 (`/Game/3_FaceAnims/AM_ArKitRemap`)

Core behavior:
- Uses `CurveMap` as a 1:1 rename/copy from MHA source curves to ARKit target curves.
- Applies a post-pass `MouthClose` rewrite:
  - reads ARKit `MouthClose` and `JawOpen`,
  - computes `MouthClose = MouthClose * JawOpen`,
  - clamps to `0..0.3`.

Strengths:
- Simple and fast.
- Easy to reason about for direct name-matched curves.

Limitations:
- Ignores multi-contributor weighting from PoseAsset behavior.
- Limited calibration/tuning controls.
- Mouth behavior quality depends heavily on source-curve semantics being correct.

#### v02 (`/Game/3_FaceAnims/AM_ArKitRemap_v02`)

Key improvements over v01:
- Adds a weighted synthesis path (guarded by `bUseWeightedCoreRemap`) so selected ARKit targets can be reconstructed from multiple MHA contributors rather than strict 1:1 copy.
- Adds explicit calibration controls:
  - global: `GlobalScale`, `GlobalOffset`, `GlobalClampMin`, `GlobalClampMax`
  - mouth-specific: `MouthCloseScale`, `MouthCloseClampMax`
- Adds explicit `MouthClose` branch aligned to lips-together semantics:
  - source `CTRL_Expressions_Mouth_Lips_Together_UL` combined with `JawOpen`,
  - then scaled/offset/clamped via v02 controls.
- Adds control flags for staged rollout:
  - `bUseWeightedCoreRemap`
  - `bEnableExtendedPoseTargets`

How PoseAsset and extracted data were used:
- Primary input came from extracted PoseAsset derivative artifacts:
  - `.cursor/arkit-remap/mapping-pose-asset/data/PA_MetaHuman_ARKit_Mapping.reverse_map.json`
  - `.cursor/arkit-remap/mapping-pose-asset/reports/PA_MetaHuman_ARKit_Mapping_reverse_map_validation.md`
- Reverse-map class splits (`arkit52`, `extended_pose`, `other_targets`) informed implementation boundaries.
- Missing ARKit core target metadata (`MouthClose`) directly motivated explicit MouthClose logic rather than waiting for inferred contributor extraction.
- Compact implementation payload was generated for v02 execution planning:
  - `.cursor/arkit-remap/mapping-pose-asset/data/AM_ArKitRemap_v02.mapping_payload.json`
  - `.cursor/arkit-remap/mapping-pose-asset/reports/AM_ArKitRemap_v02_mapping_payload_summary.md`

Current v02 status and remaining work:
- v02 is improved over v01 through weighted + calibrated + explicit-mouth architecture.
- Weighted coverage is currently partial and should be expanded across the full arkit52 set.
- Runtime execution-order verification remains required because MCP summaries show generated `OnApply` content alongside legacy EventGraph nodes.

### E.6 Python ARKit Remap v2 (primary method)

This section documents the Python-based remap pipeline that replaces the
Blueprint AnimModifier approach as the primary method for converting MHA
`CTRL_expressions` curves to ARKit 52 blendshapes.

#### Artifacts

| Artifact | Path |
|----------|------|
| Remap script | `.cursor/arkit-remap/scripts/arkit_remap.py` |
| Mapping payload | `.cursor/arkit-remap/mapping-pose-asset/data/AM_ArKitRemap_v02.mapping_payload.json` |
| Coupled solve verification | `.cursor/arkit-remap/scripts/coupled_solve.py` |
| Round-trip validation | `.cursor/arkit-remap/scripts/roundtrip_validation.py` |
| Mouth calibration script | `.cursor/arkit-remap/scripts/calibrate_mouth_params.py` |
| Relaxed-constraint calibration | `.cursor/arkit-remap/scripts/calibrate_with_relaxed_constraint.py` |
| Param-set comparison | `.cursor/arkit-remap/scripts/compare_param_sets.py` |
| Frame alignment probe | `.cursor/arkit-remap/scripts/probe_frame_alignment.py` |
| Mouth pair validation | `.cursor/arkit-remap/scripts/validate_mouth_pair.py` |
| ABP post-PoseAsset verification | `.cursor/arkit-remap/scripts/verify_abp_post_poseasset.py` |
| PoseAsset linearity verification | `.cursor/arkit-remap/mapping-pose-asset/scripts/verify_pose_asset_linearity.py` |
| Context-menu launcher | `.cursor/arkit-remap/scripts/arkit_remap_menu.py` |
| Context-menu registration | `.cursor/arkit-remap/scripts/init_unreal.py` |
| QA run logs | `.cursor/arkit-remap/reports/run-logs/` |
| Release package | `.cursor/arkit-remap/release/` |
| Forward remap (ARKit→MH) | `.cursor/arkit-remap/scripts/forward_remap_to_mh.py` |
| LLF playback importer | `.cursor/arkit-remap/scripts/import_arkit_animsequence_as_livelinkface.py` |
| Apples pipeline orchestrator | `.cursor/arkit-remap/scripts/run_apples_pipeline.py` |
| Apples comparison script | `.cursor/arkit-remap/scripts/compare_apples.py` |
| Comparison data (JSON+MD) | `.cursor/arkit-remap/reports/apples_comparison_*.{json,md}` |

#### How to run

1. Select one or more AnimSequence assets in the Content Browser.
2. Run via **either** method:
   - UE Output Log: `py import arkit_remap`
   - Right-click selected assets → **Run ARKit Remap**
     (registered by `init_unreal.py` via the `ToolMenus` API; currently shown in
     the main Content Browser context menu rather than under `Asset Actions`).
     This opens a smoothing prompt for the current run:
     - `None` = raw output, best for QA/validation
     - `One-Euro` = adaptive smoothing, recommended default for noisy MHA capture
     - `EMA` = simpler fixed smoothing, useful when tuning or debugging smoothing behavior
     The choice is a one-shot runtime override and does not edit the payload JSON.

#### MetaHuman playback helper

When the target is a **MetaHuman** (not FaceIt) and you want the remapped ARKit
animation to flow through `ABP_MH_LiveLink` exactly like a normal Live Link Face
import, use `.cursor/arkit-remap/scripts/import_arkit_animsequence_as_livelinkface.py`.

What it does:

- reads the ARKit-named curves from a remapped `AnimSequence`
- writes a Live Link Face-style CSV with the 52 blendshape columns plus the
  9 head/eye rotation columns (zero-filled if absent)
- imports that CSV with `LiveLinkFaceImporterFactory` into a `LevelSequence`

Verified demo output:

- Source anim: `/Game/3_FaceAnims/arkit-remap-demo/AS_arkitremap-demo-main_ARKit`
- Imported sequence: `/Game/3_FaceAnims/arkit-remap-demo/arkitremap-demo-main_ARKit_cal`
- Subject name used by `ABP_MH_LiveLink`: `arkitremap-demo-main_ARKit`

Usage note: the Live Link Face importer strips the `_cal` suffix from the CSV /
asset basename when deriving the runtime subject name.

#### Key APIs and internals

- **UE Python module:** uses `unreal.AnimationLibrary` (not
  `AnimationBlueprintLibrary`). Tested on UE 5.7.
- **Controller bracket batching:** wraps all curve writes inside
  `seq.controller.open_bracket()` / `.close_bracket()`, collapsing ~40 min of
  unbatched per-key writes down to ~0.5 s per sequence.
- **Normalization:** `sum(weight²)` (least-squares inverse projection). For each
  ARKit target, the output value is:

  ```
  arkitValue = Σ (weight_i * mhaCurveValue_i) / Σ (weight_i²)
  ```

  This replaces v1's `absWeightSum` divisor and produces more physically
  plausible blendshape values.

- **Unified JawOpen + MouthClose ("visual opening" model):** the
  `_compute_mouth_pair` function jointly determines JawOpen and MouthClose
  in a single pass, replacing the former `_compute_mouth_close` +
  `_apply_jaw_purse_compensation` two-step approach:

  ```
  lip_closure    = mean(LipsTowards) + lipsPurseWeight * mean(LipsPurse)
  visual_opening = max(0, raw_jawOpen - jawFactor * mean(LipsPurse))

  arkit_jawOpen   = visual_opening
  raw_mouthClose  = lip_closure * raw_jawOpen     (signal fidelity)
  forward_cap     = min(raw_mouthClose, visual_opening)
  effective_cap   = max(0, visual_opening - puckerFactor * MouthPucker)
  arkit_mouthClose = clamp(min(forward_cap, effective_cap))
  ```

  Key properties:
  - MouthClose is derived from the *original* JawOpen (preserves full
    lip-closure signal strength).
  - JawOpen is adjusted for the output via the purse compensation factor.
  - Forward constraint: MouthClose never exceeds adjusted JawOpen (0%
    clipping in validation).
  - Pucker-aware cap: `puckerFactor` (default 0.0) reduces MouthClose
    when MouthPucker is already providing visual closure. Available as a
    tuning knob if combined MouthClose + MouthPucker exceeds the jaw gap
    on FaceIt characters (72% of frames in validation).

  **Why LipsPurse matters for MouthClose:** MHA achieves visual mouth
  closure through LipsPurse (~0.5) even when JawOpen is high (~0.5). On
  MetaHuman, the LipsPurse shapes physically close the lips across the
  jaw gap. On FaceIt, MouthPucker only puckers without closing — MouthClose
  is needed. Without LipsPurse contribution, MouthClose was near-zero.

  **Why JawOpen compensation:** MHA `ctrl_expressions_jawopen` stays high
  (~0.53) on closed-mouth frames. On MetaHuman, LipsPurse mesh shapes
  counteract this. On FaceIt, they're independent, so the jaw stays open.

  Source curves:
  - LipsTowards: `ctrl_expressions_mouthlipstowards{ul,ur,dl,dr}`
  - LipsPurse: `ctrl_expressions_mouthlipspurse{ul,ur,dl,dr}`

  Falls back to legacy `ctrl_expressions_mouth_lips_together_ul` path if
  neither LipsTowards nor LipsPurse curves are found.

  Calibratable parameters (payload JSON):
  - `jawPurseCompensation.factor` (default 0.75)
  - `jawPurseCompensation.puckerFactor` (default 0.0)
  - `mouthClose.lipsPurseWeight` (default 0.735, calibrated)
  - `mouthClose.forwardConstraintRatio` (default 1.5, calibrated — allows MouthClose up to 1.5× adjusted JawOpen, matching real ARKit behavior where mouthClose > jawOpen in ~25% of frames)
  - `mouthClose.clampMax` (default 0.5)

  Definitive alignment: ARKit baked frame 20724 @ 60fps = MHA frame 0
  (offset = 345.4s). All 1450 frames of `AS_MP_VecDemo1-allkeys` match
  `Vec-ARKITBAKED-T34_60fps-02` at this offset.

  Calibration scripts: `calibrate_mouth_params.py` fits jawFactor,
  puckerFactor, and lipsPurseWeight via grid-search.
  `calibrate_with_relaxed_constraint.py` sweeps the full 3D space
  (jawFactor × lipsPurseWeight × forwardConstraintRatio).
  Note: MHA and iPhone ARKit are from the **same take** (same reference
  mono video; MHA is a trimmed portion). The 345.4s offset reflects a
  temporal offset within one continuous capture, not a cross-session
  alignment. Calibrated factors are fitted against matched ground truth.

  Validation on allkeys3 (1450 frames):
  - Frame 956 (closed): jawOpen=0.155, mouthClose=0.140 (correct)
  - Frame 276: jawOpen=0.0, mouthClose=0.0 (no clip)
  - MouthClose > JawOpen: 0 frames (0%)
  - Jaw-capped (forward constraint active): 602/1450 frames (41.5%)
  - Combined MC+Pucker > JawOpen: 1046/1450 (72%) — visual review needed

- **Calibration:** payload JSON contains `global` (scale/offset/clamp),
  `mouthClose` (scale/clampMax/lipsTowardsSourceCurves), and optional
  `perCurveOverrides`, `coupledPairs`, and `coupledGroups` sections.

- **minWeight filtering:** contributors with `|weight| < minWeight` are
  excluded during target index construction. Default 0.05. Removes the
  `browlaterall` 0.031 artifact that polluted 10 unrelated targets (CheekPuff,
  TongueOut, NoseSneer, etc.) and `mouthdimpler` 0.003 from MouthSmileRight.

- **Coupled/grouped solve:** configured target pairs or small groups are solved
  jointly instead of independently. Eliminates cross-contamination from shared
  source curves. Configured solves:
  - **`coupledPairs`**
  - **MouthPucker ↔ MouthFunnel**: share `mouthfunnel{dl,dr,ul,ur}` curves.
    Independent solve overestimated Funnel by 125% and Pucker by 26% when both
    active. Coupled solve: exact recovery.
  - **MouthRollLower ↔ MouthRollUpper**: share `mouthupperliprollin{l,r}`.
    Independent solve overestimated RollLower by 53%. Coupled solve: exact.
  - **`coupledGroups`**
  - **BrowInnerUp + BrowOuterUpLeft + BrowOuterUpRight**: after `minWeight`
    filtering removes the bogus 0.031 `browlaterall` outer-brow leak, the real
    remaining overlap is `browraiseinl/r` shared between the inner and outer
    brow targets. Solving the brow trio together avoids order-dependent chained
    pair behavior and yields exact synthetic reconstruction under the current payload.

  The grouped solver uses a small dense Gram matrix with Gauss-Jordan inversion
  and falls back gracefully to independent solve when no config is present or
  when a group's matrix is singular.

- **Round-trip validation:** `roundtrip_validation.py` now honors payload
  `minWeight`, `coupledPairs`, and `coupledGroups` so it reflects current
  production behavior rather than raw reverse-map overlap. Latest result under
  the current payload: all 51 targets round-trip perfectly across isolation,
  shared-mouth pair, shared-brow pair, brow trio, speech combo, and full
  activation scenarios. Report:
  `.cursor/arkit-remap/reports/roundtrip_validation_2026-03-12T030820.json`

- **In-editor validation:** remap run completed successfully on
  `/Game/3_FaceAnims/VEC_MHA/AgenticPy/AS_MP_VecDemo1-allkeys`, writing
  `/Game/3_FaceAnims/VEC_MHA/AgenticPy/AS_MP_VecDemo1-allkeys_ARKit` and QA log
  `.cursor/arkit-remap/reports/run-logs/arkit_remap_run_2026-03-12T030845.md`.
  Observed brow ranges on that clip:
  - `BrowInnerUp`: max `0.0115`
  - `BrowOuterUpLeft`: max `1.0000`
  - `BrowOuterUpRight`: max `0.9988`
  This appears mathematically consistent with the grouped solve on that source
  animation, but should still be visually reviewed when evaluating brow quality.

- **Temporal smoothing (optional):** post-synthesis low-pass filtering via
  1-euro filter (adaptive) or EMA (fixed-weight). Disabled by default; enable
  via `smoothing.enabled: true` in payload. Per-curve overrides supported for
  noisier curves like MouthClose. Module: `temporal_smoothing.py`.

- **QA clamp-boundary alerting:** QA reports flag targets where min or max
  values hit the calibration clamp boundaries, indicating under-ranged
  calibration that may be silently compressing peaks.

#### Curve coverage

- **51 ARKit curves** are synthesized from payload contributor weights.
- **1 derived curve** (`MouthClose`) via the unified mouth-pair model
  (`LipsTowards + lipsPurseWeight * LipsPurse`, constrained against adjusted
  `JawOpen`).
- **52 total ARKit curves** written per sequence.
- **1 missing source curve** (absent from input animations tested so far):
  - `ctrl_expressions_tonguerolldown`

  This produces zero-value output for `tongueOut`. If future MHA captures
  include it, the pipeline handles it automatically.
- `ctrl_expressions_mouth_lips_together_ul` is no longer required (replaced
  by the LipsTowards + LipsPurse mouth-pair derivation).

#### Known limitations

- Eye-look curves (`eyeLookDownLeft`, etc.) are bone-driven in MetaHuman and do
  not have clean curve-only inverses. The pipeline writes contributor-weighted
  approximations, but accuracy depends on the source animation.
- `tongueOut` relies on `ctrl_expressions_tonguerolldown`, which is typically
  absent from MHA captures (produces zero output).
- Extended pose targets (`Pose_4`–`Pose_17`) are not written by this pipeline;
  only the core ARKit 52 set is emitted.
- `MouthClose` clamp at 0.5 (raised from 0.3 after identifying ceiling hits on
  expressive sequences). Configurable via `calibrationDefaults.mouthClose.clampMax`.

#### Relationship to legacy AnimModifier

The Python pipeline supersedes `AM_ArKitRemap` (v01) and `AM_ArKitRemap_v02`
(Sections E.1–E.5). Advantages:

- Full weighted synthesis across all 51 payload targets (vs partial coverage in v02).
- Least-squares normalization (vs simple sum or single-contributor copy).
- Sub-second execution per sequence (vs minutes for Blueprint `OnApply`).
- Calibration and QA reporting built in.
- No Unreal asset dependencies — runs from plain Python + JSON payload.

The Blueprint modifiers remain available at `/Game/3_FaceAnims/AM_ArKitRemap`
and `/Game/3_FaceAnims/AM_ArKitRemap_v02` as fallback for workflows that
require a modifier-based approach.

---

## F. FaceIt Integration

**FaceIt** is a Blender addon that rigs custom characters with ARKit-compatible morph targets (shape keys). The workflow:

1. Rig character in Blender using FaceIt -> creates 52 ARKit-named shape keys on the mesh
2. Export character to Unreal with morph targets
3. Process facial capture in Unreal using MetaHuman Animator (MHA) -> produces MHA-format animation sequence
4. Apply AM_ArKitRemap modifier to the sequence -> converts MHA curves to ARKit names
5. In Sequencer, add the modified animation to the FaceIt character's animation track
6. Use **Layered Blend Per Bone** (or slot system) to combine face animation (above head bone) with body mocap (below head bone)

**Slot system setup (from README):**
1. Create AnimBlueprint for character
2. Add slot in Anim Slot Manager (e.g. "FaceSlot")
3. Add Layered Blend Per Bone node: body slot -> Base Pose, face slot -> Blend Poses 0
4. Set Bone Name to "head", Blend Depth to 1 (face animation only affects head bone and children)
5. In Sequencer, right-click animation section -> Animation -> Slot -> type slot name

---

## G. Known Mapping Challenges

From the Blip doc and analysis:

| Challenge | Detail | Impact on reverse pipeline |
|-----------|--------|---------------------------|
| **Asymmetric controls** | MHA uses `CTRL_L_` / `CTRL_R_` naming vs ARKit `Left`/`Right` suffix | CurveMap keys must match exactly; wrong names = dropped curves |
| **Additive vs absolute** | Some MHA curves are additive; direct passthrough causes double-transforms | Copying additive values as absolute can over-drive expressions |
| **Missing ARKit equivalents** | MHA controls like lip curl, nostril flare may not have clean ARKit counterparts | Some facial detail is lost in conversion |
| **jawOpen vs mouth controls** | ARKit jawOpen affects multiple MHA controls simultaneously | Reverse: jawOpen should be derived from multiple MHA curves, not one |
| **Eye look directions** | ARKit eye look curves drive bone rotations in MHA, not morph targets | Curve-only modifier cannot properly invert eye look (bone data needed) |
| **Range remapping** | ARKit is 0-1; MHA controls may expect different ranges or have additive offsets | Values copied as-is may look weak or overdriven on FaceIt side |
| **1:1 vs weighted** | PA uses weighted combinations; CurveMap uses single source per target | Biggest quality gap; expressions look flat |

---

## H. Scrutiny and Gap Analysis

Findings from the initial analysis chat:

1. **PA_MetaHuman_ARKit_Mapping is opaque.** Cannot be read by MCP tools. CurveMap was inferred from curve names and community sources, not from the PA itself.

2. **Historical note:** the early pipeline used a conservative `MouthClose`
   clamp of `0..0.3`. The current Python remapper uses `0..0.5` after
   identifying ceiling hits on expressive sequences. Keep tunable.

3. **Head rotation: out of scope.** Body mocap handles head. No head curves in the modifier.

4. **JawOpenAlpha / TeethShowAlpha:** Current verification supports treating these as runtime/manual override controls, not baked remap signals. `verify_abp_post_poseasset.py` found the representative baked MHA sequence contains none of the jaw/teeth curves written by those nodes, and the `ABP_MH_LiveLink` class defaults both alpha variables to `0.0`. Not replicating them in the reverse remapper is correct under the current evidence.

5. **MHFDS branch:** ABP_MH_LiveLink uses Blend Poses by bool to choose between raw LiveLink (MHFDS=true) and processed (MHFDS=false). AM_ArKitRemap reverses the processed path, which is correct for ARKit-style input.

6. **CurveMap MouthClose source must be a Lips Together curve** (one of CTRL_Expressions_Mouth_Lips_Together_DL/DR/UL/UR) for the MouthClose fix formula to be the correct inverse. If sourced from a different MHA curve, the formula breaks. **Verify this in the editor.**

7. **Execution order is correct:** Block A (rename) runs before Block B (fix MouthClose), so Block B reads the already-renamed ARKit curves.

8. **Community mapping table (MH_Arkit_Mapping.txt) maps MouthClose to `ctrl_expressions_mouthlipspurseul`** (Lips Purse UL), not Lips Together. This is a different curve from what the ABP_MH_LiveLink formula uses. **This discrepancy should be investigated** -- the CurveMap in the actual AM_ArKitRemap asset may differ from the community table.

9. **Working hypothesis: `MouthClose` is derived outside PoseAsset in ABP logic.** This explains why reverse-map extraction reports `MouthClose` missing while forward graph behavior still uses it through post-PoseAsset math (`SafeDivide(MouthClose, JawOpen)` -> lips-together controls). Treat this as likely but not final until runtime graph validation is completed.

10. **PoseAsset has negative weights on mesh-level curves (CONFIRMED).** Editor inspection of `MouthPressRight` reveals `head_lod0_mesh__*` curves with values of -0.079874 (chin-raise suppression). The extraction script only captured `ctrl_expressions_*` curves, which are all positive. The PoseAsset operates on two curve layers: control-rig expressions (`ctrl_expressions_*`) and mesh blendshapes (`head_lod0_mesh__*`). The reverse pipeline only uses the former. **Follow-up needed:** verify that MHA baked AnimSequences do not contain `head_lod0_mesh__*` curves; if they do, the pipeline is missing a data layer.

---

## I. Quality Issues and Improvement Roadmap

### Why animations don't look great (ordered by likely impact)

1. **1:1 copy vs PA weighted mapping:** Each ARKit curve is probably a weighted blend of several MHA curves. Picking one loses the rest. Expressions look flat, smiles look wrong, brows lack nuance.

2. **jawOpen from single MHA curve:** Forward path has jawOpen driving multiple MHA controls. Reverse should combine them. Single 1:1 can under- or over-drive jaw.

3. **No range/scale/offset:** MHA and FaceIt may not use the same value range. Copying as-is can produce weak or overdriven expressions.

4. **Additive MHA curves copied as absolute:** Can cause double-transform or incorrect baseline.

5. **MouthClose source curve mismatch:** If CurveMap uses Lips Purse instead of Lips Together, the MouthClose fix formula computes the wrong value.

### Improvement roadmap (ordered)

| Priority | Action | Requires |
|----------|--------|----------|
| 1 | Extract PA weight data (see Section J) | Editor access, possibly Python/C++ |
| 2 | Implement weighted combination per ARKit curve in modifier | PA data from step 1 |
| 3 | Verify/fix CurveMap MouthClose source (Lips Together vs Lips Purse) | Editor inspection of AM_ArKitRemap defaults |
| 4 | Handle jawOpen as multi-curve computation | PA data showing which MHA curves jawOpen drives |
| 5 | Add optional per-curve scale/offset parameters | Testing with FaceIt characters |
| 6 | Handle additive curves (baseline subtract) | Identification of which MHA curves are additive |

---

## J. Ways to Extract PA Data

The extraction workflow is now established and should be reused, not reinvented.

### J.0 Current canonical workflow (use this first)

- Workspace: `.cursor/arkit-remap/mapping-pose-asset`
- Start here: `.cursor/arkit-remap/mapping-pose-asset/AGENT_INDEX.md`
- Regeneration order:
  1. `scripts/extract_pose_asset_mapping.py`
  2. `scripts/introspect_pose_asset.py`
  3. `scripts/compare_posemaps.py`
  4. `scripts/build_reverse_mapping_table.py`
  5. `scripts/validate_reverse_mapping_table.py`
  6. `scripts/build_am_v02_payload.py`

### J.0.1 How to use the folder quickly

- Need "what ARKit pose maps to which MHA curves and weights"?  
  Open `data/PA_MetaHuman_ARKit_Mapping.posemap.json`
- Need machine-readable weighted reverse mapping input?  
  Open `data/PA_MetaHuman_ARKit_Mapping.reverse_map.json`
- Need compact AM_ArKitRemap_v02 implementation payload?  
  Open `data/AM_ArKitRemap_v02.mapping_payload.json`
- Need compact payload generation snapshot/coverage summary?  
  Open `reports/AM_ArKitRemap_v02_mapping_payload_summary.md`
- Need core-vs-extended reverse-map overview for fast review?  
  Open `reports/PA_MetaHuman_ARKit_Mapping_reverse_map_summary.md`
- Need confidence that reverse map is structurally valid before implementation?  
  Open `reports/PA_MetaHuman_ARKit_Mapping_reverse_map_validation.md`
- Need to inspect baseline offsets / potential bias contributors?  
  Compare against `data/PA_MetaHuman_ARKit_Mapping.posemap.raw.json`
- Need a human-readable summary of what changed between raw and adjusted?  
  Open `reports/PA_MetaHuman_ARKit_Mapping_raw_vs_adjusted.md`
- Need extraction context, assumptions, and quick facts?  
  Open `AGENT_INDEX.md` and `reports/PA_MetaHuman_ARKit_Mapping_extraction_results.md`
- Need API/probing details for UE Python access troubleshooting?  
  Open `data/PA_MetaHuman_ARKit_Mapping.introspection.json`

### J.0.2 Practical guidance for remap work

- Use **adjusted** data as default input for remap logic design.
- Use **reverse_map** as the direct implementation input for weighted remap development.
- Run reverse-map validation after generation; treat FAIL as blocking and WARN as investigation items.
- Use **raw** data only when validating offsets or extraction behavior.
- Keep reports/datasets in `mapping-pose-asset` as the canonical source; avoid duplicating large tables into this KB.

### J.0.3 Index and knowledge sync protocol

- Treat `.cursor/arkit-remap/mapping-pose-asset/AGENT_INDEX.md` as the canonical navigation index.
- When adding/changing artifacts under `mapping-pose-asset`, update all three in the same pass:
  1. `mapping-pose-asset/AGENT_INDEX.md`,
  2. this KB (Section D/J navigation + usage),
  3. `.cursor/skills/arkit-remap/SKILL.md`.
- Future agents should start at `AGENT_INDEX.md` before exploring files ad hoc.

---

Strategies to read PA_MetaHuman_ARKit_Mapping and get the per-ARKit-curve MHA curve lists + weights (fallback/alternative paths):

### J.1 Editor UI (simplest)
Open the asset in Content Browser (double-click). Check Details panel for pose names, source animation, curve lists. May only show pose names, not internal weights.

### J.2 Editor Python
With Editor Scripting Utilities enabled:
- `unreal.load_asset(path)` to get PoseAsset
- `asset.get_pose_names()` returns pose name list
- Check `source_animation` and `asset_mapping_table` properties
- Dump to file for analysis

### J.3 C++ Plugin
Load via `LoadObject<UPoseAsset>`. Inspect `PoseAsset.h` source for methods like `GetPoseNames()`, `GetCurveNames()`, internal pose/curve/weight arrays. Log or write to JSON/CSV.

### J.4 Parse .uasset on disk
Use UAssetAPI (C#/.NET) or similar tool on the `.uasset`/`.uexp` files. Walk exports and properties looking for name/weight arrays. Engine-version-specific.

### J.5 Runtime hook
In a test AnimBlueprint using the PA node, log curve names and values after the PA runs. Vary inputs and observe outputs to infer weights. More observational than direct.

### J.6 Epic documentation / community
Check Epic docs for PoseAsset internals, ARKit mapping docs, or community projects that have already extracted this data.

**Recommended order:** J.1 (editor UI) -> J.2 (Python) -> J.3 (C++) -> J.4 (.uasset parsing)
