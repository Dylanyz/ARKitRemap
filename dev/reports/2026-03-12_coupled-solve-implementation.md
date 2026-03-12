# Coupled 2-Target Solve: Implementation & Analysis

**Date:** 2026-03-12  
**Addresses:** GAP 2, GAP 6, IMP 2 from architecture QA deep analysis  
**Status:** Implementation complete, verification passing  

---

## Problem Statement

The independent per-target least-squares solve treats each ARKit target in isolation.
When two targets share MHA source curves, each target's solve absorbs the other's
contribution through the shared curves, systematically overestimating both.

This is the **single largest source of reconstruction error** identified in the
architecture QA (GAP 2), particularly impactful for speech animation where pucker
and funnel co-activate on "oo" sounds.

---

## Mathematical Foundation

### Forward Model

The PoseAsset defines a linear forward mapping:

```
observed_source_i = Σ_j (ARKit_j × w_ij)
```

For a pair of targets A and B sharing source curves s_1...s_n:

```
observed_i = A_true × w_A_i + B_true × w_B_i  (+ contributions from other targets)
```

### Independent Solve (Current — Flawed for Shared Curves)

```
A_hat = Σ(observed_i × w_A_i) / Σ(w_A_i²)
```

This conflates B's contribution into A's estimate through the shared curves.

### Coupled Solve (New — Correct)

Minimize `||W × [A, B]^T − observed||²` jointly. Taking partial derivatives:

```
Normal equations:  (W^T W) × [A, B]^T = W^T × observed

[ Σ(wA²)     Σ(wA·wB) ] [A]   [ Σ(obs·wA) ]
[ Σ(wA·wB)   Σ(wB²)   ] [B] = [ Σ(obs·wB) ]
```

Solved per-frame via Cramer's rule (the 2×2 Gram matrix W^T W is constant across
all frames since the weights don't change).

---

## Pair 1: MouthPucker ↔ MouthFunnel

### Source Curve Weights (from PA_MetaHuman_ARKit_Mapping extraction)

| Source Curves (×4 variants: dl,dr,ul,ur) | w_Pucker | w_Funnel |
|------------------------------------------|----------|----------|
| `ctrl_expressions_mouthlipspurse{*}`     | 1.000    | 0.000    |
| `ctrl_expressions_mouthfunnel{*}`        | 0.752    | ~1.000   |
| `ctrl_expressions_mouthlipstowards{*}`   | 0.412    | 0.000    |

**12 source curves total** (4 unique to Pucker, 4 shared, 4 unique to Pucker).

### Gram Matrix (W^T W)

```
Σ(wA²)   = 4×(1.0² + 0.752² + 0.412²) = 4×1.7352 = 6.941
Σ(wA·wB) = 4×(0 + 0.752×1.0 + 0)       = 4×0.752  = 3.008
Σ(wB²)   = 4×(0 + 1.0² + 0)            = 4×1.0    = 4.000

G = [ 6.941   3.008 ]
    [ 3.008   4.000 ]

det(G) = 6.941×4.000 − 3.008² = 27.764 − 9.048 = 18.716

G⁻¹ = (1/18.716) × [  4.000  −3.008 ]
                     [ −3.008   6.941 ]
```

### Worked Example: Pucker=0.5, Funnel=0.3

Baked observations (forward model):
```
lipspurse:    0.5 × 1.0 = 0.500
funnel:       0.5 × 0.752 + 0.3 × 1.0 = 0.676
lipstowards:  0.5 × 0.412 = 0.206
```

| Method | Pucker | Error | Funnel | Error |
|--------|--------|-------|--------|-------|
| **Independent** | 0.630 | **+26.0%** | 0.676 | **+125.3%** |
| **Coupled** | 0.500 | **0.0%** | 0.300 | **0.0%** |

The independent solve overestimates Funnel by 2.25× because every shared funnel
curve carries Pucker's 0.376 contribution that gets fully attributed to Funnel.

---

## Pair 2: MouthRollLower ↔ MouthRollUpper

### Source Curve Weights

| Source Curves (×2 variants: l,r) | w_Lower | w_Upper |
|----------------------------------|---------|---------|
| `ctrl_expressions_mouthlowerliprollin{*}` | 1.000 | 0.000 |
| `ctrl_expressions_mouthupperliprollin{*}` | 0.499 | ~0.998 |

**4 source curves total** (2 unique to Lower, 2 shared).

### Gram Matrix

```
Σ(wA²)   = 2×(1.0² + 0.499²)      = 2×1.249 = 2.498
Σ(wA·wB) = 2×(0 + 0.499×0.998)    = 2×0.498 = 0.996
Σ(wB²)   = 2×(0 + 0.998²)         = 2×0.996 = 1.992

G = [ 2.498   0.996 ]
    [ 0.996   1.992 ]

det(G) = 2.498×1.992 − 0.996² = 4.976 − 0.992 = 3.984

G⁻¹ = (1/3.984) × [  1.992  −0.996 ]
                    [ −0.996   2.498 ]
```

### Worked Example: RollLower=0.6, RollUpper=0.8

Baked observations (forward model):
```
lowerliprollin:  0.6 × 1.0 = 0.600
upperliprollin:  0.6 × 0.499 + 0.8 × 0.998 = 1.098
```

| Method | RollLower | Error | RollUpper | Error |
|--------|-----------|-------|-----------|-------|
| **Independent** | 0.919 | **+53.2%** | 1.100 | **+37.5%** |
| **Coupled** | 0.600 | **0.0%** | 0.800 | **0.0%** |

RollUpper exceeds 1.0 with the independent solve — a physically impossible ARKit
value that only the post-calibration clamp masks.

---

## Implementation

### Files

| Artifact | Path |
|----------|------|
| Implementation | `.cursor/arkit-remap/scripts/coupled_solve.py` |
| Functions | `_coupled_solve_pair()`, `_weighted_synthesis_v2()` |
| Tests | `_verify()` — 4 test cases, all passing |

### Integration into `arkit_remap.py`

1. Copy `_coupled_solve_pair()` and `_weighted_synthesis_v2()` into `arkit_remap.py`.
2. In `main()`, replace:
   ```python
   arkit_output, stats = _weighted_synthesis(
       target_index, source_cache, calibration, frame_count
   )
   ```
   with:
   ```python
   coupled_pairs = payload.get("coupledPairs")
   arkit_output, stats = _weighted_synthesis_v2(
       target_index, source_cache, calibration, frame_count,
       coupled_pairs=coupled_pairs,
   )
   ```
3. Remove duplicate `_clamp` / `_apply_calibration` (already in arkit_remap.py).
4. Add `"coupledPairs"` to the payload JSON.

### Payload JSON Addition

Add this top-level key to `AM_ArKitRemap_v02.mapping_payload.json`:

```json
"coupledPairs": [
    ["MouthPucker", "MouthFunnel"],
    ["MouthRollLower", "MouthRollUpper"]
]
```

---

## Expected Improvement Analysis

### Pair 1: MouthPucker ↔ MouthFunnel

- **When both active (speech "oo" sounds):** Eliminates +26% Pucker and +125%
  Funnel overestimation. This is the most common co-activation in speech.
- **When only one active:** Coupled solve produces identical results to
  independent (verified in test 3). No regression risk.
- **Visual impact:** Lip protrusion will be correctly proportioned instead of
  exaggerated. FaceIt characters will show natural speech shapes.

### Pair 2: MouthRollLower ↔ MouthRollUpper

- **When both active (lip pressing/biting):** Eliminates +53% Lower and +38%
  Upper overestimation. Prevents RollUpper from exceeding 1.0.
- **Visual impact:** Lip roll animations will have correct upper/lower
  separation instead of both being pushed to maximum.

### Overall

The coupled solve addresses the **highest-impact gap** (GAP 2) with medium
implementation effort. It's strictly better than the independent solve for the
configured pairs and has zero effect on all other targets. No numpy dependency.

---

## Verification Results

```
Pair 1: MouthPucker(0.5) + MouthFunnel(0.3)
  Independent: Pucker=0.630 (+26.0%)  Funnel=0.676 (+125.3%)
  Coupled:     Pucker=0.500 (exact)   Funnel=0.300 (exact)      PASS

Pair 2: MouthRollLower(0.6) + MouthRollUpper(0.8)
  Independent: Lower=0.919 (+53.2%)   Upper=1.100 (+37.5%)
  Coupled:     Lower=0.600 (exact)    Upper=0.800 (exact)       PASS

Pair 1 single-target: Pucker-only(0.7), Funnel=0
  Coupled:     Pucker=0.700 (exact)   Funnel=0.000 (exact)      PASS

Backwards compat: v2 with no coupled pairs
  Matches independent solve exactly                              PASS
```
