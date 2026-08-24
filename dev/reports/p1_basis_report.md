# P1 basis report — ARKit-51 in joint-output space

Basis: 51 poses x 7830 joint attrs (870 joints x 9), archetype DNA `SKM_Face.dna`.

## Live curve audit
- 251/251 live MHA expression curves resolve to DNA raw controls
- live-only (no DNA control): none
- DNA-only (never streamed): none

## Conditioning
- singular value range: 122.646 .. 5.636 (condition number 21.8)
- rank at 1e-3 rel tolerance: 51/51
- pose norms: min 8.183 (BrowDownRight), max 94.512 (MouthRight)

## Overlapping pairs (cosine > 0.5)
- MouthSmileLeft / MouthDimpleLeft: 0.8459
- MouthSmileRight / MouthDimpleRight: 0.8417
- MouthFunnel / MouthPucker: 0.8396
- MouthRollLower / MouthPressRight: 0.7653
- MouthRollLower / MouthPressLeft: 0.7603
- EyeSquintLeft / CheekSquintLeft: 0.6705
- EyeSquintRight / CheekSquintRight: 0.665
- MouthUpperUpRight / NoseSneerRight: 0.6278
- MouthUpperUpLeft / NoseSneerLeft: 0.6122
- EyeBlinkRight / EyeLookDownRight: 0.5712
- EyeBlinkLeft / EyeLookDownLeft: 0.566
- EyeLookUpRight / EyeWideRight: 0.5473
- EyeLookUpLeft / EyeWideLeft: 0.5466
- MouthSmileRight / MouthUpperUpRight: 0.5191
- MouthSmileLeft / MouthUpperUpLeft: 0.5138
