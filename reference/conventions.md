# Measured conventions

Naming, mirroring, and channel conventions — every claim below was measured, not assumed.
Sources: paired iPhone-ARKit / MHA takes (`20260814_DefaultSlate_3`), two Fab rigs, Epic's
`ABP_MH_LiveLink`. Evidence: [dev/reports/p2_convention_verdicts.md](../dev/reports/p2_convention_verdicts.md).

## The 52 ARKit blendshapes

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

MetaHuman Animator's baked space is ~250 `CTRL_expressions_*` curves (251 raw controls on the
archetype rig). Curve→morph binding in UE is name-based and **case-insensitive** —
`eyeBlinkLeft` and `EyeBlinkLeft` both bind (field-verified).

## Left/right conventions (measured on-device)

- **Apple ARKit naming is performer-relative for eyes/brows/smile but OBSERVER-relative for
  MouthLeft/MouthRight.** JawLeft/Right unverdictable — Apple's lateral-jaw signal p95 ≈ 0.03.
- **Wild ARKit rigs are name-consistent** (mouthLeft = character's own left), verified with
  two Fab rigs + Epic's ABP_MH_LiveLink in a five-way lineup. Apple's mouth quirk therefore
  must NOT be baked into remap output — corrections apply only reference-side when scoring
  against Apple CSVs. `RM_MHA_to_ARKit` is name-consistent.
- **Blip's saved mono video is mirrored** (selfie convention) → MHA output from it is a
  mirror-space performance. Proven 3 ways: gaze matches swapped partners (+0.98),
  smile-asymmetry anti-correlates (−0.80), calibration-take event order. If side-correctness
  matters, unmirror the video before MHA processing.

## MouthClose

The obvious inversion of Epic's forward rule (`MouthClose = mean(lipsTogether) × jawOpen`,
from `ABP_MH_LiveLink`'s post-PoseAsset graph) **fails on MHA-origin curves** (r ≈ −0.07):
MHA solves appearance, so its `jawOpen ≈ 0` exactly when lips are pressed; the relation only
holds for control sets produced BY the forward ABP. MHA encodes closed-lips-while-jaw-open as
`mouthLipsThickU/D*`, `mouthLipsPushU/D*`, `mouthLipsPurse*` (raw r up to +0.76). V3 fits
MouthClose against the measured iPhone MouthClose of a paired take over L/R-symmetrized
lip-pair sums → r = 0.81, amplitude matched. MouthClose is the only calibrated (vs. solved)
output in the definition.
