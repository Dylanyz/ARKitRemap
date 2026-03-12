# ARKit Remap Architecture: Deep QA Analysis

**Date:** 2026-03-12
**Scope:** Full comparison of the Python ARKit Remap v2 pipeline against accumulated research on Epic's MHA-to-ARKit conversion process.
**Artifacts reviewed:** knowledge-base.md, SKILL.md, arkit_remap.py, AM_ArKitRemap_v02.mapping_payload.json, PA_MetaHuman_ARKit_Mapping.reverse_map.json, raw vs adjusted extraction data, MouthClose reverse engineering plan, Python v1 and v2 plans, community mapping reference (MH_Arkit_Mapping.txt), QA run reports, reverse map validation report, AGENT_INDEX.md.

---

## Executive Summary

The pipeline is architecturally sound and represents a significant advancement over the original 1:1 rename approach. The PoseAsset extraction, reverse-map construction, least-squares normalization, and MouthClose derivation are all well-researched. However, scrutiny reveals **7 substantive gaps** and **5 improvement opportunities** that could meaningfully increase output quality, ranging from a likely data artifact polluting many targets to missing round-trip validation.

**Overall Grade: B+** — Strong foundation, correct math, good engineering. Gaps are mostly in edge cases and refinement rather than fundamental errors.

---

## Part 1: What the Pipeline Gets Right

### 1.1 Correct Inverse Projection (sum of w²)

The v2 normalization formula `arkitValue = Σ(w_i * mhaCurve_i) / Σ(w_i²)` is the mathematically correct least-squares inverse of the PoseAsset's linear combination model `mhaCurve_i = activation * w_i`. This was a critical fix from v1's `absWeightSum` divisor, which produced up to 20% error on multi-tier targets like MouthPucker.

**Verified against research:** The plan documents a concrete proof using MouthPucker's 12 contributors across 3 weight tiers (1.0, 0.752, 0.412). For true ARKit value 0.5: v1 gives 0.40, v2 gives 0.50 (exact). This is solid.

### 1.2 MouthClose Derivation

The MouthClose reverse engineering was thorough:

- Correctly identified that `CTRL_Expressions_Mouth_Lips_Together_*` only exists during LiveLink forward-path execution, not in MHA bakes.
- Correctly identified `LipsTowards` curves as the appropriate proxy (semantically: "lips moving toward each other").
- Used mean of all 4 LipsTowards variants (inter-variant Pearson r > 0.93, but upper ~1.8x lower).
- Multiplied by synthesized JawOpen (matches the forward-path's `SafeDivide(MouthClose, JawOpen)` relationship).
- Empirically validated: min=0.0004, max=0.3, mean=0.092 on AS_MP_VecDemo1-allkeys (1450 frames).

**Verified against research:** Forward-path formula `LipsTogether = SafeDivide(MouthClose, JawOpen)` → Reverse: `MouthClose = LipsTogether * JawOpen`. Using LipsTowards as proxy for LipsTogether is well-justified since the actual LipsTogether controls don't exist on baked animations.

### 1.3 Baseline Subtraction Quality

The PoseAsset extraction cleanly removed persistent offsets. The raw-vs-adjusted comparison shows exactly 2 raw-only contributors per pose (`nosewrinkleupperl`, `nosewrinkleupperr`), and zero adjusted-only contributors. The Default pose itself had only these 2 curves as non-zero. This means the baseline subtraction was systematic and correct — these were constant offsets that appeared in every pose equally.

### 1.4 Controller Bracket Batching

Using `seq.controller.open_bracket()` / `.close_bracket()` for batch writes collapses ~40 min of unbatched per-key writes to ~0.5s. This is a genuine UE5 best practice that most community scripts miss.

### 1.5 MouthClose's Absence from PoseAsset: Confirmed

The working hypothesis that MouthClose is handled entirely in post-PoseAsset ABP graph logic (not as a PoseAsset target) was confirmed empirically. The extraction found 51/52 ARKit targets in the PoseAsset, with MouthClose being the sole missing entry. ABP_MH_LiveLink's AnimGraph step 5 shows the explicit `SafeDivide(MouthClose, JawOpen)` → LipsTogether write, confirming the PoseAsset never sees MouthClose.

---

## Part 2: Substantive Gaps Found

### GAP 1: `ctrl_expressions_browlaterall` at 0.031 — Likely Data Artifact (HIGH)

**The problem:** `ctrl_expressions_browlaterall` appears as a contributor to **11 different targets** all at the near-identical weight of ~0.031:


| Target           | Weight   | Semantic Relationship to Brow? |
| ------------------ | ---------- | -------------------------------- |
| BrowInnerUp      | **1.0**  | YES — primary target          |
| BrowDownLeft     | 0.031    | Plausible                      |
| BrowDownRight    | 0.031    | Plausible                      |
| BrowOuterUpLeft  | 0.031002 | Plausible                      |
| BrowOuterUpRight | 0.031    | Plausible                      |
| CheekPuff        | 0.031    | Unlikely                       |
| CheekSquintLeft  | 0.031    | Unlikely                       |
| CheekSquintRight | 0.031    | Unlikely                       |
| NoseSneerLeft    | 0.031    | Unlikely                       |
| NoseSneerRight   | 0.031    | Unlikely                       |
| TongueOut        | 0.031    | Extremely unlikely             |

**Why this is suspicious:** The same 0.031 weight appears in targets with no anatomical relationship to the brow (TongueOut, CheekPuff). The baseline subtraction correctly removed `nosewrinkleupperl/r` persistent offsets, but `browlaterall` at 0.031 survived. This suggests it's a second-order persistent offset — `browlaterall` has a value of exactly 0.031 above the Default pose baseline in every non-Default pose. It's not a genuine weight; it's noise in the PoseAsset's authoring.

**Critical asymmetry evidence:** `ctrl_expressions_browlateralr` only appears once (in BrowInnerUp at 1.0). If browlaterall's 0.031 were a genuine anatomical contribution, `browlateralr` should appear at similar weights in the same targets. It doesn't. This strongly confirms the 0.031 is an artifact specific to the left-side control.

**Impact on pipeline:**

- Direct: Small per-frame (~3% of dominant contributor) brow-lateral leakage into TongueOut, CheekPuff, etc.
- Reverse: More significant — any baked animation where browlaterall is active (any brow movement) will "leak" ~0.031 into CheekPuff, NoseSneer, TongueOut, etc. during synthesis.
- For BrowInnerUp specifically: browlaterall's sw² contribution (1.0² + other 3 at 1.0² = 4.0 for real contributors, plus 0.031² = 0.000961 overhead — negligible).

**Recommendation:** Add a minimum weight threshold filter. Contributors with |weight| < 0.05 (or a configurable threshold) should be excluded from synthesis. This would remove the browlaterall noise from 10 of its 11 appearances while preserving its genuine 1.0 contribution to BrowInnerUp. This was already noted as a future iteration item in the v2 plan but should be prioritized.

---

### GAP 2: Cross-Contamination in Shared Multi-Weight Targets (MEDIUM-HIGH)

**The problem:** The independent-target approximation assumes each ARKit target can be solved in isolation. In practice, MHA baked curves contain superimposed contributions from all simultaneously active ARKit expressions.

**Concrete example — MouthPucker vs MouthFunnel:**

MouthPucker uses 12 contributors, 4 of which are `mouthfunnel{dl,dr,ul,ur}` at weight 0.752. MouthFunnel uses the same 4 `mouthfunnel` curves at weight ~1.0.

When the original performance has MouthPucker=0.5 and MouthFunnel=0.3 simultaneously:

```
Baked mouthfunnelul = MouthPucker × 0.752 + MouthFunnel × 1.0
                    = 0.5 × 0.752 + 0.3 × 1.0
                    = 0.376 + 0.3 = 0.676
```

Reverse solve for MouthFunnel (independent-target):

```
MouthFunnel ≈ Σ(0.676 × 1.0 for all 4) / Σ(1.0² for all 4)
            = 0.676 (instead of correct 0.3)
```

MouthFunnel is overestimated by 2.25x because the Pucker contribution is conflated. Similarly, MouthPucker will be overestimated because it picks up the Funnel contribution through its 0.752-weight funnel terms.

**Affected target pairs (share contributors with significant mutual weight):**

- MouthPucker ↔ MouthFunnel (via `mouthfunnel{dl,dr,ul,ur}`)
- MouthRollLower ↔ MouthRollUpper (via `mouthupperliprollin{l,r}` at 0.499 and 0.998)
- BrowInnerUp ↔ BrowOuterUp{L,R} (via `browraisein{l,r}`)
- BrowInnerUp ↔ BrowDown{L,R} (via `browlaterall` if kept)

**Impact:** This is likely the single largest source of reconstruction error. Mouth expressions that combine pucker and funnel (common in speech — "oo" sounds) will be systematically overestimated on both targets.

**Recommendation:** Implement a constrained least-squares multi-target solve. Instead of solving each of 52 targets independently, solve all targets simultaneously per frame:

```
minimize ||W × activations - observed_mha_curves||²
```

where W is the 168×51 weight matrix from the payload. This eliminates cross-contamination entirely. It's the "full linear system solve per frame" noted as a future iteration item.

A lighter alternative: for known pairs that share contributors heavily, implement a 2-target coupled solve. Focus on MouthPucker/MouthFunnel and MouthRollLower/MouthRollUpper first — these are the most audibly/visually impactful.

---

### GAP 3: MouthClose Clamp at 0.3 Actively Compresses Peaks (MEDIUM)

**The evidence:** The most recent QA run on AS_MP_VecDemo1-allkeys shows MouthClose max=0.3000 — it is hitting the clamp ceiling. The empirical validation also shows max=0.3 (clamped). This means the unclamped value exceeded 0.3 on at least some frames.

**Forward path comparison:** Epic's forward path uses `SafeDivide(MouthClose, JawOpen)` with clamp [0, 1]. The ARKit MouthClose input ranges [0, 1]. Our reverse output is clamped to [0, 0.3], compressing 70% of the potential range.

**Why 0.3 was chosen:** The original v01 Blueprint modifier used 0.3 as a conservative cap to prevent "mouth deformation" on FaceIt characters. This was a reasonable safety choice for the 1:1 rename approach where values weren't properly weighted. With the v2 weighted synthesis and LipsTowards-based derivation, the values should be more calibrated.

**The mismatch:** LipsTowards values multiplied by JawOpen can exceed 0.3 when both are large. The clamp silently flattens the MouthClose peak, making lip closure look incomplete on expressive performances (wide jaw open + lips pressed together = high MouthClose).

**Recommendation:**

1. Run a diagnostic pass that logs unclamped MouthClose max to determine the natural range.
2. Consider raising clampMax to 0.5 or 0.7 initially, with per-character tuning.
3. The clamp IS configurable via payload JSON (`calibrationDefaults.mouthClose.clampMax`), so this is a tuning issue, not a code issue. But the default is too conservative given the new derivation quality.

---

### GAP 4: No Round-Trip Validation (MEDIUM)

**The problem:** The pipeline has never been tested against a known ground-truth ARKit input. The only validation is visual (does the FaceIt character look right?) and statistical (QA report min/max/mean values).

**What round-trip validation would prove:**

1. Take a pure ARKit 52-curve animation (e.g., from LiveLink iPhone recording).
2. Run it through Epic's forward path (PA_MetaHuman_ARKit_Mapping → MHA curves).
3. Bake the result to an AnimSequence.
4. Run the baked sequence through arkit_remap.py.
5. Compare output ARKit curves against the original input.
6. Per-target reconstruction error = |output - input| per frame.

This would quantify:

- Exact per-target accuracy (which targets reconstruct well vs poorly).
- The magnitude of cross-contamination errors (GAP 2).
- Whether MouthClose derivation is accurate.
- Whether calibration values need adjustment.

**Why this hasn't been done:** The project uses MHA (monocular video) rather than iPhone LiveLink as input, so there's no "ground truth" ARKit animation to compare against. Creating one would require:

- A MetaHuman character set up with LiveLink Face, OR
- Manually authoring a test animation with known ARKit curve values.

**Recommendation:** Author a synthetic test animation with simple, known curve activations:

- Frame 0-30: JawOpen ramp 0→1 (all others 0)
- Frame 30-60: MouthSmileLeft ramp 0→1 (all others 0)
- Frame 60-90: MouthPucker=0.5 + MouthFunnel=0.3 simultaneously
- Frame 90-120: BrowInnerUp ramp 0→1

Run this through the PoseAsset forward path (if accessible), bake, then reverse through arkit_remap.py. Even without the forward-path step, authoring MHA curve values that correspond to known ARKit activations (using the payload weights in reverse) would work.

---

### GAP 5: EyeSquint Maps Only to Inner Squint — Missing Outer (LOW-MEDIUM)

**The data:**

- `EyeSquintLeft` → `ctrl_expressions_eyesquintinnerl` (1.0)
- `EyeSquintRight` → `ctrl_expressions_eyesquintinnerr` (~1.0)

MetaHuman has both inner and outer squint controls. The PoseAsset only maps ARKit EyeSquint to the inner squint. This means:

- The outer squint contribution is lost in the reverse mapping.
- If the baked MHA animation has significant outer squint activity (driven by other MetaHuman controls), it won't be captured by ARKit EyeSquint.

**Possible explanations:**

1. ARKit EyeSquint intentionally only drives inner squint (CheekSquint handles the outer region).
2. The outer squint is driven by bones, not curves, in MetaHuman.
3. Our extraction missed it.

**Impact:** Squint expressions may look subtly incomplete — the crow's-feet / outer-eye tightening would be missing. For FaceIt characters where EyeSquint drives a full squint morph target (including outer), the amplitude may be lower than expected.

**Recommendation:** No code change needed. Document as a known limitation. If output squints look weak, consider adding `ctrl_expressions_eyesquintouterl/r` as optional contributors to EyeSquint{Left,Right} with a tunable weight in perCurveOverrides.

---

### GAP 6: MouthRollLower/Upper Cross-Coupling (LOW-MEDIUM)

**The data:**

- MouthRollLower: `lowerliprollin{l,r}` at 1.0 + `upperliprollin{l,r}` at 0.499
- MouthRollUpper: `upperliprollin{l,r}` at ~0.998

The upper lip roll-in curves contribute to BOTH targets. When the performer rolls their upper lip, the baked `upperliprollinl` will be high, and the independent solve will attribute:

- MouthRollUpper: large value (correct — it's the primary target)
- MouthRollLower: ~half as much (incorrect — upper lip rolling shouldn't drive lower lip roll)

This is a specific case of GAP 2 but worth calling out because lip roll is visually noticeable.

**Recommendation:** Implement a coupled solve for MouthRollLower/Upper, or subtract MouthRollUpper's estimated contribution to `upperliprollin` before computing MouthRollLower. A simple approximation:

```
MouthRollLower_corrected = MouthRollLower_raw - MouthRollUpper_raw × (0.499 / 0.998) × correction_factor
```

---

### GAP 7: Community Mapping Discrepancies Not Fully Reconciled (LOW)

**The data:** The community mapping (MH_Arkit_Mapping.txt) disagrees with the PoseAsset extraction in several non-trivial ways:


| ARKit Target    | Community Mapping  | PoseAsset Extraction                           | Discrepancy                                                        |
| ----------------- | -------------------- | ------------------------------------------------ | -------------------------------------------------------------------- |
| MouthClose      | `mouthlipspurseul` | Not in PoseAsset (derived)                     | Community used wrong control — LipsPurse is MouthPucker territory |
| MouthPucker     | `mouthlipspurseur` | 12 contributors (purse + funnel + lipstowards) | Community captured only 1 of 12 contributors                       |
| MouthFunnel     | `mouthfunnelul`    | 4 funnel variants (all ~1.0)                   | Community captured only 1 of 4 contributors                        |
| BrowInnerUp     | `browlaterall`     | 4 contributors (lateral{l,r} + raisein{l,r})   | Community captured only 1 of 4                                     |
| TongueOut       | `tongueout`        | 6 contributors (tonguedown dominant!)          | Community missed the dominant contributor                          |
| MouthRollLower  | `lowerliprollinl`  | 4 contributors (lower + upper rollin)          | Community missed cross-coupling                                    |
| MouthRollUpper  | `upperliprollinl`  | 2 upper lip rollin contributors                | Missing right-side                                                 |
| MouthShrugLower | `jawchinraisedl`   | 2 contributors (chinraise{dl,dr})              | Missing right-side                                                 |
| MouthShrugUpper | `jawchinraiseul`   | 2 contributors (chinraise{ul,ur})              | Missing right-side                                                 |

The community mapping is consistently picking ONE contributor per target (usually the most obviously named one) while the PoseAsset uses multiple. This confirms the research finding that 1:1 mapping is fundamentally inadequate.

**Notably correct community mappings:** Eye look cross-mapping (EyeLookOutLeft → eyelookleftl, EyeLookInLeft → eyelookrightl) matches the PoseAsset extraction exactly. The eye blink, wide, and basic jaw/mouth single-contributor targets are also correct.

**Impact:** The legacy AM_ArKitRemap v01 was based on this community mapping. The v2 Python pipeline correctly supersedes it. No action needed, but this validates the decision to move to weighted synthesis.

---

## Part 3: Improvement Opportunities

### IMP 1: Minimum Weight Threshold Filter

Add a configurable `minWeight` threshold (default 0.05) to the payload or calibration section. During synthesis, skip contributors with `|weight| < minWeight`. This eliminates the browlaterall 0.031 artifact (GAP 1) and similar noise.

**Cost:** One `if` check per contributor per frame. Negligible.

**Risk:** If a genuine small-weight contributor is filtered out, a tiny amount of expression nuance is lost. At 0.05, this only affects browlaterall's 0.031 appearances and MouthSmileRight's `mouthdimpler` at 0.003.

### IMP 2: Coupled Solve for High-Contamination Pairs

For MouthPucker↔MouthFunnel and MouthRollLower↔MouthRollUpper, implement a 2-target simultaneous solve instead of independent per-target solve. This resolves the most impactful cross-contamination without the complexity of a full 52-target linear system.

**The math for a 2-target coupled solve:**

```
Given shared source curve s with weight w_a for target A and w_b for target B:
observed_s = A_true × w_a + B_true × w_b

Solve the 2×2 system: W^T × W × [A, B]^T = W^T × observed
```

### IMP 3: Per-Target QA Metrics with Historical Comparison

Currently, QA reports show min/max/mean per target per run. Add:

- Frame-by-frame value distribution (histogram buckets or percentiles).
- Flag targets where >10% of frames are at clamp boundaries (indicates under-ranged calibration).
- Optionally store previous run stats and show diff (did a calibration change improve or regress specific targets?).

### IMP 4: Optional Temporal Smoothing Pass

MHA baked animations from monocular video can have frame-to-frame noise. A configurable low-pass filter (e.g., 1-euro filter or simple exponential moving average) applied after synthesis but before curve writing could improve visual quality. Make it opt-in with a `smoothing` section in the payload calibration.

**The community source video confirms this need:** At 6:04, Csaba Kiss notes the quality difference vs traditional mocap, and at 9:04 specifically mentions MouthClose needing smoothing: "it works way better without the mouth close curve... you have to at least smooth it out."

### IMP 5: Diagnostic Mode for Debugging Specific Targets

Add an optional `--diagnostic` flag (or payload setting) that, for specified targets, dumps per-frame intermediate values:

- Raw weighted sum before normalization
- Individual contributor values × weights
- Pre- and post-calibration values
- Clamp events

This would make it much faster to diagnose why a specific expression looks wrong without reading the full source animation curves manually.

---

## Part 4: Research Gaps — What We Don't Yet Know

### ~~UNKNOWN 1: Does the PoseAsset Have Negative Weights?~~ RESOLVED

**Status:** CONFIRMED — the PoseAsset **does** have negative weights.

**Evidence (2026-03-12, user-confirmed via Editor UI):** Selecting `MouthPressRight` (weight 1.0) in the PA_MetaHuman_ARKit_Mapping editor reveals `head_lod0_mesh__*` curves with values of **-0.079874** (e.g., `head_lod0_mesh__JlowerChinRaise_JupperC*` curves). This makes anatomical sense — pressing lips together should suppress chin-raise shapes.

**Critical nuance:** The negative weights appear on `head_lod0_mesh__*` (mesh-level blendshape) curves, **not** on `ctrl_expressions_*` curves. The extraction script (`extract_pose_asset_mapping.py` line 210) filters to `ctrl_expressions_*` only, so these negative-weight mesh curves were never examined. All 168 extracted `ctrl_expressions_*` records remain positive.

**Open follow-up questions:**
1. Are there `ctrl_expressions_*` curves with negative responses that the extraction missed (below the 0.0001 epsilon, or on a curve not in the source animation)? Likely no — -0.079874 is well above epsilon, so if it existed on a `ctrl_expressions_*` curve it would have been captured.
2. Do MHA baked animations contain `head_lod0_mesh__*` curves? If so, the pipeline is missing an entire data layer. If not (because mesh curves are resolved at the skeletal mesh level, not baked into AnimSequences), then the negative weights don't affect the reverse mapping.
3. Should the extraction be expanded to capture `head_lod0_mesh__*` curves for completeness?

**Impact on pipeline:** If MHA bakes only contain `ctrl_expressions_*` curves (which is the current working assumption and likely correct), the negative mesh-level weights do not affect the reverse mapping. The `ctrl_expressions_*` weight matrix remains all-positive. However, this should be verified by checking a baked MHA AnimSequence for `head_lod0_mesh__*` curve presence.

### UNKNOWN 2: Does ABP_MH_LiveLink Do Other Post-PoseAsset Processing?

We've confirmed MouthClose is handled post-PoseAsset. But ABP_MH_LiveLink's AnimGraph shows additional `Modify Curve` nodes:

- Step 7: `CTRL_Expressions_Jaw_Open = 1.0` with alpha from `JawOpenAlpha`
- Step 8: Multiple teeth-related curves set to 1.0 with alpha from `TeethShowAlpha`

These runtime alphas modulate the baked values. In baked sequences, the final values include whatever JawOpenAlpha and TeethShowAlpha were set to during recording. If these alphas were not 1.0 during MHA processing, the baked values could be scaled differently than expected.

**Current assumption:** "JawOpenAlpha and TeethShowAlpha are runtime-only; baked sequences have final values, so no inversion needed." This is probably correct for MHA bakes but hasn't been verified.

### UNKNOWN 3: Are Eye-Look Curves Meaningful in MHA Bakes?

The knowledge base notes: "Eye-look curves are bone-driven in MetaHuman and do not have clean curve-only inverses." The PoseAsset maps each eye-look direction to a single `ctrl_expressions_eyelook*` curve at weight 1.0. The pipeline synthesizes eye-look ARKit curves from these.

**Open question:** When MHA bakes a monocular video capture, do the eye-look MHA curves contain actual gaze data from the video, or are they placeholder/zero? If the monocular capture system doesn't track eye gaze reliably, the synthesized eye-look ARKit curves will be noise rather than signal.

### UNKNOWN 4: Linearity of PoseAsset Response

The extraction assumes that the PoseAsset responds linearly: setting ARKit input to 1.0 and measuring the MHA output gives the weight, and any intermediate input value produces `input × weight` as output.

UE PoseAssets support non-linear blending (via the "Additive" flag and blend mode settings). If the PoseAsset uses non-linear blending, the extracted weights are only valid at the sampling point (1.0) and may not accurately represent the weight at lower activation levels.

**How to verify:** Sample the PoseAsset at multiple activation levels (0.25, 0.5, 0.75, 1.0) and check if the response scales linearly.

---

## Part 5: Summary of Findings

### Scorecard


| Area                                | Status           | Confidence  | Notes                                                    |
| ------------------------------------- | ------------------ | ------------- | ---------------------------------------------------------- |
| Normalization math                  | CORRECT          | High        | sum(w²) least-squares verified                          |
| MouthClose derivation               | CORRECT          | High        | LipsTowards × JawOpen empirically validated             |
| PoseAsset extraction                | CORRECT          | High        | Baseline subtraction clean, 168 records                  |
| Missing MouthClose from PA          | CONFIRMED        | High        | Post-PoseAsset ABP logic, not extraction defect          |
| browlaterall 0.031 artifact         | LIKELY ARTIFACT  | Medium-High | Asymmetry with browlateralr is strong evidence           |
| Cross-contamination (Pucker/Funnel) | UNMITIGATED      | High        | Theoretical analysis clear; no round-trip validation yet |
| MouthClose clamp 0.3                | TOO CONSERVATIVE | Medium      | Hitting ceiling on test sequence                         |
| Round-trip validation               | NOT DONE         | —          | No ground truth available yet                            |
| Eye-look quality                    | UNCERTAIN        | Low         | Depends on MHA bake source data                          |
| Negative weight coverage            | CONFIRMED EXISTS | High        | Negative weights on `head_lod0_mesh__*` curves; `ctrl_expressions_*` remain all-positive |

### Priority-Ordered Recommendations


| # | Recommendation                                         | Addresses        | Effort              | Impact            |
| --- | -------------------------------------------------------- | ------------------ | --------------------- | ------------------- |
| 1 | Add minWeight threshold (0.05)                         | GAP 1            | Low                 | Medium            |
| 2 | Raise MouthClose clampMax to 0.5+                      | GAP 3            | Trivial (JSON edit) | Medium            |
| 3 | Coupled solve for Pucker↔Funnel, RollLower↔RollUpper | GAP 2, GAP 6     | Medium              | High              |
| 4 | Round-trip synthetic test animation                    | GAP 4            | Medium              | High (diagnostic) |
| 5 | Per-target clamp-boundary alerting in QA               | IMP 3            | Low                 | Low-Medium        |
| 6 | Optional temporal smoothing                            | IMP 4            | Medium              | Medium            |
| 7 | ~~Re-extract PA data with explicit negative-weight check~~ RESOLVED: negatives exist on `head_lod0_mesh__*` curves, not `ctrl_expressions_*`. Verify MHA bakes don't contain mesh curves. | UNK 1            | Low                 | Low-Medium        |
| 8 | Full 52-target simultaneous solve                      | GAP 2 (complete) | High                | High              |

---

## Part 6: Comparison — Community 1:1 vs Extracted Weights vs Pipeline Output

This table summarizes the fundamental quality difference between the three approaches to give a holistic view of the progression:


| Approach                             | Targets Covered |     Contributors Per Target     |               MouthClose               |          Normalization          |             Calibration             |
| -------------------------------------- | :---------------: | :-------------------------------: | :--------------------------------------: | :-------------------------------: | :-----------------------------------: |
| Community 1:1 (MH_Arkit_Mapping.txt) |       52       |                1                |        Wrong source (LipsPurse)        |              None              |                None                |
| AM_ArKitRemap v01 (Blueprint)        |       52       |                1                |   LipsTogether × JawOpen, clamp 0.3   |              None              |                None                |
| AM_ArKitRemap v02 (Blueprint)        |       52       |        Partial weighted        |  LipsTogether × JawOpen, calibrated  |    Global scale/offset/clamp    |        Yes (global + mouth)        |
| **Python v2 (current)**              |     **52**     | **Full weighted (168 records)** | **LipsTowards × JawOpen, calibrated** |   **sum(w²) least-squares**   | **Yes (global + mouth + perCurve)** |
| Theoretical ideal                    |       52       |     Full weighted + coupled     |         LipsTowards × JawOpen         | Simultaneous multi-target solve |       Per-character profiles       |

The Python v2 pipeline is a major leap from the community 1:1 approach and captures the vast majority of the PoseAsset's complexity. The remaining gap to the theoretical ideal is primarily the cross-contamination issue (GAP 2) and calibration refinement.
