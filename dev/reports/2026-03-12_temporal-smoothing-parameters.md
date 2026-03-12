# Temporal Smoothing: Parameter Recommendations for Facial Mocap

**Date:** 2026-03-12
**Context:** ARKit Remap v2 pipeline — optional post-synthesis smoothing pass

---

## Background

MHA captures from monocular video are inherently noisier than traditional marker-based or depth-sensor mocap. The noise manifests as frame-to-frame jitter that is most visible on:

1. **MouthClose** — community reports specifically call this out ("it works way better without the mouth close curve... you have to at least smooth it out")
2. **MouthPucker / MouthFunnel** — these are computed from 4–12 contributors with shared sources, amplifying small per-frame estimation errors
3. **Cheek and nose targets** — subtle movements where noise amplitude is comparable to signal amplitude

The 1-euro filter is well-suited for this because it adapts in real time: slow movements (where noise is most visible) get heavy smoothing, while fast movements (speech, blinks) pass through with minimal lag.

---

## 1-Euro Filter Parameters

The filter has three parameters:

| Parameter | Symbol | Effect |
|-----------|--------|--------|
| `minCutoff` | f_c,min | Minimum cutoff frequency in Hz. Lower = more smoothing on slow/stationary signals. This is the primary smoothing knob. |
| `beta` | β | Speed coefficient. Higher = cutoff rises faster with signal speed, reducing lag on fast movements. |
| `dCutoff` | f_c,d | Cutoff for the internal derivative filter. Usually left at 1.0 unless the derivative itself is very noisy. |

### How they interact

The effective cutoff at each frame is:

```
f_c = minCutoff + beta * |dx/dt|
```

- When the face is mostly still: `|dx/dt| ≈ 0`, so `f_c ≈ minCutoff` → heavy smoothing
- During speech or fast expression change: `|dx/dt|` is large → `f_c` rises → less smoothing, less lag

---

## Recommended Defaults

### At 30 fps (typical MHA bake rate)

```json
{
  "minCutoff": 1.5,
  "beta": 0.5,
  "dCutoff": 1.0
}
```

**Rationale:**
- `minCutoff = 1.5 Hz` — at 30 fps the Nyquist limit is 15 Hz; facial expression changes rarely exceed 4–5 Hz even during rapid speech. A 1.5 Hz cutoff preserves all intentional movement while smoothing high-frequency jitter. This gives a time constant τ ≈ 106 ms, meaning ~3 frames of smoothing context.
- `beta = 0.5` — moderate speed sensitivity. During fast phoneme transitions (which can produce dx/dt ≈ 3–5 units/sec on mouth curves), the effective cutoff rises to ~3–4 Hz, maintaining responsiveness.
- `dCutoff = 1.0` — the derivative filter smooths the speed estimate. At 1.0 Hz it removes frame-rate-level derivative noise without over-damping.

### At 60 fps

```json
{
  "minCutoff": 1.5,
  "beta": 0.7,
  "dCutoff": 1.0
}
```

**Rationale:**
- `minCutoff` stays the same — it's in Hz, not frames, so it's frame-rate-independent by design.
- `beta` increased to 0.7 — at 60 fps, per-frame deltas are half as large (same velocity, twice the sampling), so the derivative magnitude `|dx/dt|` is the same in theory. However in practice the higher-frequency noise at 60 fps makes the derivative slightly noisier, so a higher beta compensates by reacting more aggressively to genuine speed changes.

---

## Per-Curve Override Recommendations

Not all 52 ARKit curves need the same smoothing. The table below groups curves by noise sensitivity and recommended parameter adjustments:

### High smoothing (noisy signals, slow-changing targets)

| Curve(s) | Why | Recommended Override |
|-----------|-----|---------------------|
| `MouthClose` | Product of two noisy signals (LipsTowards × JawOpen); community reports jitter | `minCutoff: 0.8, beta: 0.3` |
| `MouthPucker` | 12 contributors across 3 weight tiers; accumulates noise | `minCutoff: 1.0, beta: 0.4` |
| `MouthFunnel` | 4 contributors sharing sources with MouthPucker; cross-contamination noise | `minCutoff: 1.0, beta: 0.4` |
| `CheekPuff` | 5 contributors; subtle signal easily masked by noise | `minCutoff: 1.0, beta: 0.4` |
| `MouthRollLower` / `MouthRollUpper` | Shared upper-lip sources cause cross-contamination | `minCutoff: 1.0, beta: 0.4` |

### Default smoothing (standard targets)

| Curve(s) | Why |
|-----------|-----|
| `JawOpen`, `MouthSmile*`, `MouthFrown*`, `BrowDown*` | Single dominant contributor; moderate noise |
| `MouthStretch*`, `MouthPress*`, `MouthDimple*` | 1–2 contributors; normal noise profile |
| `NoseSneer*`, `CheekSquint*` | Subtle but not excessively noisy |

Use defaults: `minCutoff: 1.5, beta: 0.5`

### Light or no smoothing (fast-changing or binary-ish signals)

| Curve(s) | Why | Recommended Override |
|-----------|-----|---------------------|
| `EyeBlink*` | Near-binary; aggressive smoothing would slow blink onset | `minCutoff: 3.0, beta: 1.0` |
| `EyeWide*` | Fast startle responses need to pass through | `minCutoff: 2.5, beta: 0.8` |
| `EyeLook*` | Saccades are fast and intentional; smoothing causes visible lag | `minCutoff: 3.0, beta: 1.0` |
| `EyeSquint*` | Usually intentional; MHA estimates are reasonably stable | `minCutoff: 2.0, beta: 0.6` |
| `TongueOut` | Rare, intentional; mostly zero | skip or use defaults |

---

## EMA Alternative

For simpler workflows or when the 1-euro filter's adaptive behavior isn't needed:

| Scenario | Alpha | Equivalent behavior |
|----------|-------|-------------------|
| Light smoothing | 0.7–0.8 | Removes single-frame spikes |
| Moderate smoothing | 0.4–0.6 | Visible smoothing, some lag |
| Heavy smoothing | 0.2–0.3 | Significant smoothing, noticeable lag on fast movements |

**Downside of EMA vs 1-euro:** EMA applies the same weight regardless of signal speed, so it either under-smooths stationary noise or over-smooths (lags) fast movements. The 1-euro filter avoids this trade-off. EMA is provided as a fallback for simplicity or when variable-rate behavior isn't desired.

---

## Validation Strategy

After enabling smoothing, check the QA report's Temporal Smoothing section. Healthy signs:

- **MouthClose** `meanDelta` > 0.01, `alteredPct` > 30% — confirms noise reduction is active
- **EyeBlink** `meanDelta` < 0.005 — confirms blinks are passing through
- **JawOpen** `maxDelta` < 0.05 — confirms jaw isn't being over-smoothed
- No curve should have `maxDelta` > 0.15 unless it was very noisy — that would indicate over-smoothing

If a curve's `maxDelta` is unexpectedly high, reduce `minCutoff` toward defaults or increase `beta`.

---

## Implementation Notes

- The smoothing pass runs **after** synthesis and calibration, **before** writing curves. It does not change the synthesis math.
- The `times` array from the animation keyframes is used directly, so variable frame rate is handled correctly.
- The filter processes each curve independently and in forward-time order (causal filtering). There is no look-ahead or bidirectional pass, which means zero additional latency.
- Disabled by default (`"enabled": false` in payload). Opt-in only.
