# ARKit Remap Tool — Improvement Log

Master hub for tracking improvements to the ARKit remap pipeline (`arkit_remap.py`).

## Source Analysis

All improvement work stems from the deep QA analysis:
- **[Architecture QA Deep Analysis](../arkit-remap/reports/2026-03-12_architecture-qa-deep-analysis.md)** — 7 gaps, 5 improvement opportunities, 4 research unknowns.

## Implementation Status

| # | Item | Source | Effort | Impact | Status | Notes |
|---|------|--------|--------|--------|--------|-------|
| 1 | **minWeight threshold filter** | GAP 1 / IMP 1 | Low | Medium | **DONE** | Filters `browlaterall` 0.031 from 10 targets + `mouthdimpler` 0.003. Default threshold: 0.05 |
| 2 | **Raise MouthClose clampMax** | GAP 3 | Trivial | Medium | **DONE** | 0.3→0.5 in payload and code fallback. Was hitting ceiling on expressive performances |
| 3 | **Clamp-boundary QA alerting** | IMP 3 | Low | Low-Med | **DONE** | QA reports now flag targets at clamp boundaries with a dedicated table |
| 4 | **Coupled 2-target solve** | GAP 2 / GAP 6 | Medium | High | **DONE** | Pucker↔Funnel (Funnel err: 125%→0%), RollLower↔RollUpper (RollLower err: 53%→0%). Verified with standalone tests |
| 5 | **Round-trip validation framework** | GAP 4 | Medium | High | **DONE** | `roundtrip_validation.py` — tests isolation, pairs, speech combo, full activation. Quantified cross-contamination severity for all 51 targets |
| 6 | **Temporal smoothing (1-euro)** | IMP 4 | Medium | Medium | **DONE** | `temporal_smoothing.py` — 1-euro filter + EMA. Disabled by default. Per-curve overrides for MouthClose/Pucker/Funnel |
| 7 | Verify MHA bakes for `head_lod0_mesh__*` | UNK 1 | Low | Low-Med | BACKLOG | Check if mesh-level curves exist in baked AnimSequences |
| 8 | Full 52-target simultaneous solve | GAP 2 | High | High | BACKLOG | Complete linear system solve; only if coupled solve insufficient |
| 9 | Diagnostic mode (`--diagnostic`) | IMP 5 | Medium | Med | BACKLOG | Per-frame dump of intermediate values for debugging |
| 10 | Verify ABP post-PoseAsset processing | UNK 2 | Low | Low | **DONE** | `verify_abp_post_poseasset.py`: representative bake lacks post-PA jaw/teeth override curves; `ABP_MH_LiveLink` CDO defaults `JawOpenAlpha=0.0`, `TeethShowAlpha=0.0` |
| 11 | Verify eye-look quality in MHA bakes | UNK 3 | Low | Low | BACKLOG | Are eye-look curves from monocular capture meaningful? |
| 12 | Verify PoseAsset linearity | UNK 4 | Medium | Med | PARTIAL | `verify_pose_asset_linearity.py`: runtime `AnimSingleNodeInstance` readback inconclusive, but source animation is non-additive (`AAT_NONE`) with linear interpolation and the first clean segment (`EyeBlinkLeft`) samples exactly linearly at 0.25/0.5/0.75/1.0 |
| 13 | BrowInnerUp ↔ BrowOuterUp grouped solve | GAP 2 | Low | Medium | **DONE** | Implemented as 3-target grouped solve for `BrowInnerUp`, `BrowOuterUpLeft`, `BrowOuterUpRight`. Offline round-trip now exact under current payload/minWeight config |
| 14 | Curve-family QA classification from Control Rig | IMP 6 | Low-Med | Medium | BACKLOG | Use `Face_ControlBoard_CtrlRig` to tag source curves as direct, signed/vector-split, or phased/helper so QA can flag when reverse-solve evidence comes from non-independent helper curves |
| 15 | **MouthClose LipsPurse contribution** | USER BUG | Medium | **Critical** | **DONE** | MHA uses LipsPurse (~0.5) to close mouth at high JawOpen. Old formula only used LipsTowards (~0.01) → MouthClose ≈ 0. New: `lip_closure = LipsTowards + 0.5 * LipsPurse`. Frame 956 fix: 0.006 → 0.140 |
| 16 | **JawOpen purse compensation** | USER BUG | Low | **Critical** | **DONE** | Reduces JawOpen when LipsPurse is active. MHA jawOpen=0.53 at closed-mouth frames passes through to FaceIt, but MetaHuman compensates via mesh. New post-pass: `adjustedJawOpen = max(0, jawOpen - 0.75 * mean(LipsPurse))`. Frame 956: JawOpen 0.53→0.15. Combined with #15, closed frames now match real ARKit closely |
| 17 | **Unified visual-opening model** | PLAN | Medium | **High** | **DONE** | Merged `_compute_mouth_close` + `_apply_jaw_purse_compensation` into `_compute_mouth_pair`. Definitive alignment (ARKit frame 20724 = MHA frame 0, offset 345.4s) enabled proper calibration. Relaxed forward constraint (1.5×) + lipsPurseWeight=0.735. Frame 956: mc=0.202 (ref 0.203, err 0.0004) |

## Completed Changes (2026-03-12)

### 1. minWeight Threshold Filter (GAP 1 / IMP 1)
- **Files:** `arkit_remap.py` (`_build_target_index`), payload JSON (`calibrationDefaults.minWeight`)
- **Effect:** Removes 11 sub-threshold contributors across targets. `browlaterall` at 0.031 no longer pollutes CheekPuff, TongueOut, NoseSneer, CheekSquint, BrowDown, BrowOuterUp. `mouthdimpler` at 0.003 no longer pollutes MouthSmileRight.
- **Risk:** Negligible — only affects contributors contributing <0.25% of dominant weight.

### 2. MouthClose clampMax Raise (GAP 3)
- **Files:** payload JSON (`calibrationDefaults.mouthClose.clampMax`), `arkit_remap.py` (fallback default)
- **Effect:** MouthClose can now reach 0.5 instead of being capped at 0.3. The old cap was hitting the ceiling on expressive performances (lip closure during wide jaw open).

### 3. Coupled 2-Target Solve (GAP 2 / GAP 6)
- **Files:** `arkit_remap.py` (`_coupled_solve_pair`, updated `_weighted_synthesis`), payload JSON (`coupledPairs`)
- **Math:** 2×2 Gram matrix W^T*W precomputed per pair, Cramer's rule per frame. Non-negative clamp on outputs.
- **Verification:** `coupled_solve.py` standalone tests — all 4 test cases pass:
  - Pucker=0.5 + Funnel=0.3 → exact recovery (was 26%/125% error)
  - RollLower=0.6 + RollUpper=0.8 → exact recovery (was 53%/38% error)
  - Pucker-only=0.7 → exact (no false Funnel ghost)
  - Backwards compatibility → identical to independent solve when no pairs configured

### 4. Round-Trip Validation Framework (GAP 4)
- **File:** `roundtrip_validation.py` (standalone, no UE dependency)
- **Scenarios:** Isolation (51×30 frames), 3 pair tests, speech combo, full activation
- **Key findings:**
  - 34/51 targets have perfect round-trip (exclusive source curves)
  - 17 targets affected by cross-contamination
  - Worst ghost: MouthPucker=1.0 → MouthFunnel ghost at 0.752
  - `browlaterall` artifact confirmed: BrowInnerUp=1.0 leaks 0.031 into 10 targets
  - JSON report at `reports/roundtrip_validation_*.json`

### 5. Temporal Smoothing (IMP 4)
- **File:** `temporal_smoothing.py` (separate module, graceful import)
- **Algorithms:** 1-euro filter (adaptive) + EMA (fixed-weight)
- **Config:** payload `smoothing` section (disabled by default)
- **Per-curve defaults:** MouthClose (minCutoff=0.8, beta=0.3), MouthPucker/Funnel (1.0, 0.4)
- **Integration:** Applied after synthesis + MouthClose, before curve writing. Top-5 affected curves logged.

### 6. QA Clamp-Boundary Alerting (IMP 3)
- **File:** `arkit_remap.py` (`_write_qa_report`)
- **Effect:** Markdown run reports include a "Clamp-Boundary Alerts" table listing targets where min or max values touch the clamp floor/ceiling.

### 7. Grouped Brow Solve (Item 13 / GAP 2)
- **Files:** `arkit_remap.py` (generic grouped solve), payload JSON (`coupledGroups`), `roundtrip_validation.py`, `coupled_solve.py`
- **Math:** Generalized NxN Gram-matrix least-squares solve using Gauss-Jordan inversion. Current grouped solve: `["BrowInnerUp", "BrowOuterUpLeft", "BrowOuterUpRight"]`.
- **Why grouped instead of chained pairs:** `BrowInnerUp` shares `browraiseinl` with `BrowOuterUpLeft` and `browraiseinr` with `BrowOuterUpRight`, so sequential 2-target solves would be order-dependent and could double-spend the inner-brow signal.
- **Verification:** `roundtrip_validation.py` now honors both `minWeight` and configured grouped solves from the payload. Current result: all 51 targets round-trip perfectly across isolation, mouth pair, brow pair, brow trio, speech combo, and full-activation scenarios. JSON report: `reports/roundtrip_validation_2026-03-12T030820.json`
- **Runtime note:** UE test run on `/Game/3_FaceAnims/VEC_MHA/AgenticPy/AS_MP_VecDemo1-allkeys` completed successfully and wrote `/Game/3_FaceAnims/VEC_MHA/AgenticPy/AS_MP_VecDemo1-allkeys_ARKit`. Brow ranges on that clip skew heavily outer (`BrowOuterUpLeft max=1.0`, `BrowOuterUpRight max=0.9988`, `BrowInnerUp max=0.0115`), which looks mathematically consistent with the shared-source solve but should be visually reviewed in-editor.

### 8. ABP Post-PoseAsset Verification (Item 10 / UNK 2)
- **Files:** `verify_abp_post_poseasset.py`, `abp_post_poseasset_verification.{json,md}`
- **Verification:** On `/Game/3_FaceAnims/VEC_MHA/AgenticPy/AS_MP_VecDemo1-allkeys`, none of the post-PoseAsset jaw/teeth override curves (`ctrl_expressions_jaw_open`, lower/upper lip depress/raise, corner pull, stretch) exist on the baked sequence. The generated class default object for `/Game/MetaHumans/Common/Animation/ABP_MH_LiveLink` reports `JawOpenAlpha = 0.0` and `TeethShowAlpha = 0.0`.
- **Conclusion:** These nodes behave like runtime/manual override paths, not extra baked signals the reverse remapper must reconstruct. This closes Item 10 for the current pipeline assumptions.

### 9. PoseAsset Linearity Verification (Item 12 / UNK 4)
- **Files:** `mapping-pose-asset/scripts/verify_pose_asset_linearity.py`, `mapping-pose-asset/data/PA_MetaHuman_ARKit_Mapping.linearity_verification.json`, `mapping-pose-asset/reports/PA_MetaHuman_ARKit_Mapping_linearity_verification.md`
- **Runtime probe:** A transient `AnimSingleNodeInstance` can be created on `/Game/MetaHumans/Common/Face/SKM_Face`, but `get_all_curve_names()` returns no active curves and `get_curve_value()` stays at 0.0 after `set_preview_curve_override('JawOpen', weight, False)`. So Python still does not expose a reliable live-curve readback path for the PoseAsset node in this setup.
- **Source-animation probe:** The PoseAsset's source animation reports `additive_anim_type = AAT_NONE`, `ref_pose_type = ABPT_NONE`, and `interpolation = LINEAR`. The first uncontaminated segment (`Default` -> `EyeBlinkLeft`) samples exactly linearly at `0.25 / 0.5 / 0.75 / 1.0` with zero measured error on its contributor curve (`ctrl_expressions_eyeblinkl`).
- **Conclusion:** The linearity risk is materially reduced, but not fully eliminated for all poses until a stronger runtime readback path is found.

### 10. MouthClose LipsPurse Contribution (Item 15 / USER BUG)
- **Files:** `arkit_remap.py` (`_compute_mouth_close`, `_mean_source_group`, `_build_target_index`), payload JSON (`mouthClose.lipsPurseSourceCurves`, `mouthClose.lipsPurseWeight`)
- **Root cause:** MHA represents "closed mouth" with high JawOpen (~0.53) plus high LipsPurse (~0.50), relying on MetaHuman mesh-level interaction where LipsPurse shapes physically close the lips across the jaw gap. The old MouthClose formula `mean(LipsTowards) * JawOpen` only used LipsTowards (~0.01 at closed-mouth frames), producing MouthClose ≈ 0.006 — essentially zero. FaceIt characters need MouthClose to counteract JawOpen since MouthPucker alone only puckers without closing the gap.
- **Fix:** Added LipsPurse as an additional lip-closure signal: `lip_closure = mean(LipsTowards) + lipsPurseWeight * mean(LipsPurse)`, then `MouthClose = lip_closure * JawOpen`. Default `lipsPurseWeight = 0.5`, calibratable in payload.
- **Diagnostic evidence:** Frame 956 of AS_MP_VecDemo1-allkeys (MetaHuman mouth visually closed): MouthClose improved from **0.006** (old) to **0.140** (new, weight=0.5).
- **Diagnostic script:** `.cursor/arkit-remap/scripts/diagnose_mouth_close.py` — reads curve values at a specific frame from multiple sequences for comparative analysis.

## Insights from Face_ControlBoard_CtrlRig

Analysis of **Face_ControlBoard_CtrlRig** (`/Game/MetaHumans/Common/Face/Face_ControlBoard_CtrlRig`) via MCP `get_detailed_blueprint_summary`, cross-checked against `ABP_Face_PostProcess` and `CR_MetaHuman_HeadMovement_IK_Proc` — relevant to how MHA face curves relate to the rig and to Item 12 (linearity).

- **What it is:** Control Rig Blueprint (Parent: ControlRig), ~11 MB on disk. Referenced by 3 assets; depends on `CRSL_MetaHuman_Gizmo` and `DefaultGizmoLibrary`. Single instance variable: `eyes_aim_rig` (bool).
- **Two layers in the rig:**
  - **Curve layer:** The rig reads/writes the same curve namespace the pipeline uses: **CTRL_expressions_*** (253 unique curve names in the graph; Unreal uses mixed case in the rig, we use lowercase in payload/AnimSequences).
  - **Control layer:** **418 rig control elements** (e.g. `CTRL_L_brow_down`, `CTRL_L_mouth_purseD`, `CTRL_C_jaw`, `CTRL_C_tongue_roll`) — the actual rig controls that drive the mesh. These are *not* the same as curve names; they are the Control Rig’s internal “bones”/gizmos.
- **Graph structure:** One main **Rig Graph** with both **Backwards Solve** and **Forwards Solve**, so the rig is bidirectional rather than a one-way driver. Node counts (approximate): **263 Get Curve Value**, **260 Set Curve Value**, **154 Get Control Float**, **152 Set Control Float**, **15 Get / 13 Set Control Vector2D**, plus **93 Remap**, **89 Add**, **9 Interpolate**, **9 Evaluate Curve**, and transform nodes (Set/Get Transform - Control/Bone, Aim, etc.). There is a **Construction Event** (Set Transform - Control Initial) and a comment block `// Setup_Eye_Controls`.
- **Deeper behavioral breakdown:**
  - **Direct scalar families:** brow (`browRaiseIn*`, `browRaiseOuter*`, `browLateral*`), many funnel/purse/stretch/corner curves, and several jaw/chin curves appear as near-direct curve-to-control pass-throughs.
  - **Signed/vector-split families:** `mouthLeft` / `mouthRight`, `jawLeft` / `jawRight`, and cheek suck/blow behave like shared latent controls split through `Vector2D`, `Add`, `Remap`, and clamp logic rather than fully independent source channels.
  - **Phased/helper families:** `mouthLipsSticky*Ph1/2/3` and `neckSwallowPh1..5` are generated with `Evaluate Curve` phasing and threshold-style logic.
  - **Eye-look family:** eye look curves are explicitly derived through `Remap`, `Interpolate`, and clamp behavior, making them one of the clearest non-linear/helper families in the rig.
  - **Mesh-layer absence:** no `head_lod0_mesh__*` curves were found in the Control Board graph.
- **Relevance to ARKit remap:**
  1. **Use as reference / QA oracle, not primary source:** The Control Board is valuable for understanding what each `CTRL_expressions_*` curve semantically represents, but it should not replace PoseAsset-derived weights as the main reverse-mapping source.
  2. **Linearity risk is narrower than "the whole rig is non-linear":** Many channels are direct. The main non-linear/helper risk is concentrated in eye-look, sticky, swallow, and signed split families. This sharpens **Item 12 (Verify PoseAsset linearity)** rather than replacing it.
  3. **Brow findings are supported:** Brow families look mostly direct in the rig, which supports the conclusion that `browlaterall` contamination is primarily a PoseAsset/shared-weight artifact rather than a Control Rig transform artifact.
  4. **Potential QA improvement:** The rig suggests a useful future classification of source curves into **direct**, **signed/vector-split**, and **phased/helper** families so validation reports can distinguish "independent evidence" from helper curves derived from shared latent controls.
  5. **Two curve layers (KB / UNK 1):** The knowledge base already notes that the PoseAsset uses both `ctrl_expressions_*` and `head_lod0_mesh__*`. The Control Board only showed `CTRL_expressions_*`; `ABP_Face_PostProcess` confirmed a runtime stack involving `CR_MetaHuman_HeadMovement_IK_Proc` and `RigLogic`, which makes it more likely that any missing mesh-layer behavior lives elsewhere. No change to pipeline scope from this analysis; UNK 1 (verify MHA bakes for mesh curves) remains the right follow-up.

*Sources: MCP `get_detailed_blueprint_summary` on `Face_ControlBoard_CtrlRig`; MCP `get_asset_summary` on `ABP_Face_PostProcess` and `CR_MetaHuman_HeadMovement_IK_Proc`; 2026-03-12. Full summaries stored in agent-tools output (large text dumps).*

## Research Documents

| Topic | Path | Status |
|-------|------|--------|
| Architecture QA deep analysis | `.cursor/arkit-remap/reports/2026-03-12_architecture-qa-deep-analysis.md` | Complete |
| Coupled solve implementation report | `.cursor/arkit-remap/reports/2026-03-12_coupled-solve-implementation.md` | Complete |
| Temporal smoothing parameters | `.cursor/arkit-remap/reports/2026-03-12_temporal-smoothing-parameters.md` | Complete |
| Round-trip validation JSON report | `.cursor/arkit-remap/reports/roundtrip_validation_2026-03-12T030820.json` | Complete |
| ABP post-PoseAsset verification | `.cursor/arkit-remap/reports/abp_post_poseasset_verification.md` | Complete |
| PoseAsset linearity verification | `.cursor/arkit-remap/mapping-pose-asset/reports/PA_MetaHuman_ARKit_Mapping_linearity_verification.md` | Partial / runtime probe inconclusive |

## Files Modified

| File | Changes | Date |
|------|---------|------|
| `arkit_remap.py` | minWeight filter, coupled pair solve, grouped brow solve, MouthClose clamp, QA alerts, smoothing integration, unified `_compute_mouth_pair`, relaxed forward constraint (`forwardConstraintRatio`) | 2026-03-12 |
| `AM_ArKitRemap_v02.mapping_payload.json` | `minWeight`, `coupledPairs`, `coupledGroups`, `smoothing`, MouthClose clampMax, `puckerFactor`, `forwardConstraintRatio=1.5`, `lipsPurseWeight=0.735`, notes | 2026-03-12 |
| `calibrate_mouth_params.py` | Grid-search calibration with definitive alignment (offset 345.4s, ARKit frame 20724 = MHA frame 0) | 2026-03-12 |
| `calibrate_with_relaxed_constraint.py` | New file — 3D sweep (jawFactor × lipsPurseWeight × forwardConstraintRatio) with candidate comparison | 2026-03-12 |
| `compare_param_sets.py` | New file — evaluates multiple param sets against matched ARKit reference | 2026-03-12 |
| `probe_frame_alignment.py` | New file — reads fps/frame-count/duration from key sequences to verify alignment | 2026-03-12 |
| `validate_mouth_pair.py` | New file — runs remap on a target sequence and checks key frames + clipping metrics | 2026-03-12 |
| `temporal_smoothing.py` | New file — 1-euro + EMA filter module | 2026-03-12 |
| `coupled_solve.py` | New file — standalone verification tests for pair + grouped solves | 2026-03-12 |
| `roundtrip_validation.py` | New file — round-trip accuracy test framework honoring payload minWeight and grouped solves | 2026-03-12 |
| `arkit_remap_menu.py` | New file — context-menu smoothing prompt and one-shot runtime override launcher | 2026-03-12 |
| `verify_abp_post_poseasset.py` | New file — verifies ABP_MH_LiveLink jaw/teeth post-PoseAsset override assumptions against a baked sequence and blueprint defaults | 2026-03-12 |
| `mapping-pose-asset/scripts/verify_pose_asset_linearity.py` | New file — runtime probe + source-animation fractional linearity check for PA_MetaHuman_ARKit_Mapping | 2026-03-12 |
| `knowledge-base.md` | Section E.6 updated with new features, revision log entry | 2026-03-12 |
| `mapping-pose-asset/AGENT_INDEX.md` | Payload/validation docs updated for `coupledGroups` | 2026-03-12 |
| `SKILL.md` | Updated key technical points and artifacts table | 2026-03-12 |

## Key Artifacts

- **Script:** `.cursor/arkit-remap/scripts/arkit_remap.py`
- **Payload:** `.cursor/arkit-remap/mapping-pose-asset/data/AM_ArKitRemap_v02.mapping_payload.json`
- **SKILL:** `.cursor/skills/arkit-remap/SKILL.md`
- **Knowledge Base:** `.cursor/arkit-remap/knowledge-base.md`
- **QA Run Logs:** `.cursor/arkit-remap/reports/run-logs/`

## Backlog Notes for Future Agents

### Item 8: Full 52-target simultaneous solve
Only pursue if real-animation QA proves the current grouped solves insufficient. With the brow trio now covered, the offline round-trip validator shows exact reconstruction under the current payload/minWeight configuration. Escalate to a full 52-target solve only if new shared-curve problem groups emerge on real performances.

### Item 13: BrowInnerUp ↔ BrowOuterUp coupled solve
Implemented on 2026-03-12 as a grouped 3-target solve via `coupledGroups`. The payload/runtime now solve `["BrowInnerUp", "BrowOuterUpLeft", "BrowOuterUpRight"]` in one pass, avoiding order-dependent chained-pair behavior and eliminating the offline brow ghosting that remained after `minWeight` filtering.

### Item 12: PoseAsset linearity verification
Partially de-risked on 2026-03-12. The new verifier shows:
- direct runtime readback from a transient `AnimSingleNodeInstance` remains inconclusive,
- source animation is non-additive with linear interpolation,
- the first clean segment (`EyeBlinkLeft`) is exactly linear at `0.25 / 0.5 / 0.75 / 1.0`.

Keep this item open only if a future pass can read live PoseAsset output curves or bone deltas for a wider set of poses.

### Item 14: Curve-family QA classification from Control Rig
The deeper `Face_ControlBoard_CtrlRig` analysis suggests the `CTRL_expressions_*` namespace is a mix of:
- direct scalar channels (`browRaise*`, many funnel/purse/stretch/jaw/chin curves)
- signed/vector-split channels (`mouthLeft` / `mouthRight`, `jawLeft` / `jawRight`, cheek suck/blow)
- phased/helper channels (`mouthLipsSticky*Ph*`, `neckSwallowPh*`, eye-look helper behavior)

Future QA could annotate payload contributors by family so validation reports can distinguish:
- direct evidence from baked curves
- helper curves derived from shared latent controls
- families where independent-target solving is more likely to over-interpret correlated channels

This is a **QA / interpretability improvement**, not a change to synthesis math by itself. It becomes most useful if future real-animation tests reveal errors in eye-look, sticky, swallow, or antagonistic left/right families that the current grouped solves do not explain.

### 11. Unified Visual-Opening Model (Item 17 / Pipeline-Grounded Mouth Fix)
- **Files:** `arkit_remap.py` (`_compute_mouth_pair` replaces `_compute_mouth_close` + `_apply_jaw_purse_compensation`), payload JSON (`puckerFactor`, `forwardConstraintRatio` fields added), `calibrate_mouth_params.py` (new), `calibrate_with_relaxed_constraint.py` (new), `validate_mouth_pair.py` (new), `compare_param_sets.py` (new)
- **Structural change:** JawOpen and MouthClose are now computed jointly in a single function. MouthClose is derived from raw (un-compensated) JawOpen for signal fidelity, then capped against the *adjusted* JawOpen scaled by `forwardConstraintRatio` (default 1.5).
- **Definitive alignment found:** User confirmed ARKit baked frame 20724 @ 60fps = MHA frame 0, giving offset = **345.4s**. All 1450 frame pairs of `AS_MP_VecDemo1-allkeys` matched against `Vec-ARKITBAKED-T34_60fps-02`.
- **Calibration:** 3D grid search (jawFactor × lipsPurseWeight × forwardConstraintRatio) across 1450 matched frame pairs. Real ARKit data shows mouthClose > jawOpen in **25%** of frames, proving the original strict forward constraint was too tight.
- **Calibrated params (applied):** `jawFactor=0.75`, `lipsPurseWeight=0.735`, `forwardConstraintRatio=1.5`. Combines the proven jaw reduction (factor=0.75) with the calibrated lip-closure weight (0.735) and a relaxed constraint that allows MouthClose to reach its correct level.
- **Validation (allkeys3, 1450 frames):**
  - Frame 956 (closed mouth): jawOpen=0.155, mouthClose=**0.202** (ref: 0.203, error: 0.0004) — near-perfect
  - Frame 276: jawOpen=0.0, mouthClose=0.0 — no clipping
  - MouthClose > JawOpen: 437/1450 (30.1%) — close to real ARKit's 25%
  - Hard clipping (mc > 1.51× jaw): 0 frames — safe
- **Improvement over previous:** MouthClose at frame 956 went from 0.140 (31% below reference) to 0.202 (within 0.2% of reference). JawOpen unchanged at 0.155.
- **Release copy synced:** `.cursor/arkit-remap/release/arkit_remap.py`

### Item 16: JawOpen purse compensation
- **Files:** `arkit_remap.py` (`_apply_jaw_purse_compensation`), payload JSON (`calibrationDefaults.jawPurseCompensation`)
- **Root cause:** MHA's `ctrl_expressions_jawopen` = 0.53 on closed-mouth frames passes through 1:1 to FaceIt's jawOpen morph target. On MetaHuman, LipsPurse shapes physically counteract the jaw opening at the mesh level, so the mouth appears closed despite the high jawOpen control value. On FaceIt, MouthPucker only puckers without closing the jaw gap — the high jawOpen keeps the mouth visibly open.
- **Fix:** Post-pass after MouthClose computation: `adjustedJawOpen = max(0, jawOpen - factor * mean(LipsPurse))`. MouthClose is computed first using the original JawOpen so it retains full lip-closure signal, then JawOpen is reduced for the output.
- **Calibration:** `factor` (default 0.75) controls compensation strength. Higher = more jaw reduction when pursing.
- **Expected result at frame 956:** jawOpen 0.53→0.15, mouthClose≈0.14. Real ARKit ref: jawOpen≈0.11, mouthClose≈0.13.
- **Risk:** On frames where the jaw is genuinely open with some pucker (e.g., "oooo" sound), jawOpen will be somewhat reduced. The linear compensation is a reasonable first approximation. If overcorrection is observed, reduce `factor`.
