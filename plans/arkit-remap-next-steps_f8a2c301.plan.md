---
name: ARKit Remap Next Steps
overview: Continuation plan after apples-to-apples comparison. Covers remaining quality improvements, visual testing on FaceIt character, and optional real-ARKit comparison fix.
todos:
  - id: visual-test-faceit
    content: Apply remap output to FaceIt character in Sequencer and visually evaluate mouth/jaw/brow quality at key frames
    status: pending
  - id: funnel-roundtrip
    content: "Investigate mouthFunnel round-trip error (0.07 MSE, max diff 0.62): coupled Pucker/Funnel solve may over-distribute to Funnel"
    status: pending
  - id: lipstogether-roundtrip
    content: "Investigate LipsTogether round-trip error (0.45 MSE): MouthClose derivation is lossy through jawOpen purse compensation"
    status: pending
  - id: jawopen-roundtrip
    content: "Evaluate jawOpen round-trip (0.10 MSE): purse compensation intentionally changes the value. Is the FaceIt visual result correct?"
    status: pending
  - id: tongue-artifacts
    content: Tongue curves have 0.105 MSE round-trip from shared PoseAsset contributors. Verify these are zero/negligible in real performances.
    status: pending
  - id: fix-real-arkit-forward
    content: "Optional: fix C (real iPhone ARKit forward-pass) by clearing all ctrl_expressions from template before writing. Low priority."
    status: pending
isProject: false
---

# ARKit Remap Next Steps

## Where we are

The apples-to-apples comparison is complete. We have validated the reverse remap pipeline by:

1. Taking MHA ctrl_expressions (A)
2. Remapping to ARKit curves via `arkit_remap.py`
3. Forward-passing back to ctrl_expressions via `forward_remap_to_mh.py` (B)
4. Comparing A vs B numerically and visually on the MetaHuman

Alignment note: the MHA excerpt and the baked iPhone ARKit reference come from the same take. The `345.4s` offset is an intra-take trim alignment (`ARKit` frame `20724` at 60 fps = `MHA` frame `0`), not a cross-session approximation.

### Key results (A vs B round-trip MSE by family)


| Family | MSE   | Notes                                            |
| ------ | ----- | ------------------------------------------------ |
| eye    | 0.000 | Perfect — 1:1 PoseAsset mapping                  |
| nose   | 0.000 | Perfect — 1:1 mapping                            |
| jaw    | 0.013 | Purse compensation intentionally reduces JawOpen |
| brow   | 0.019 | Slight error from grouped brow solve             |
| mouth  | 0.043 | Dominated by LipsTogether/MouthClose path        |
| tongue | 0.105 | Shared contributors in PoseAsset                 |


### Visual confirmation

Frames 0, 276, 956, 1087 compared on MetaHuman. B tracks A well overall. Screenshots saved in agent transcript.

### What didn't work

Real iPhone ARKit forward-pass (C) is broken — template duplication leaves ~220 of A's residual ctrl_expressions curves that contaminate C. Would need to clear ALL curves or use the PoseAsset node at runtime. Low priority.

## What to do next

### Priority 1: Test on FaceIt character

The whole point of the remap is to play on FaceIt characters, not MetaHumans. The next step is to apply the _ARKit remap output to the actual FaceIt character in Sequencer and evaluate:

- Does the mouth close properly? (the calibrated MouthClose/JawOpen)
- Do brows look right?
- Are there any over-driven or dead curves?

**Asset to test:** `/Game/3_FaceAnims/VEC_MHA/AgenticPy/apples/AS_MP_VecDemo1-allkeys_ARKit` (or the one in the parent AgenticPy folder)

### Priority 2: Investigate top round-trip errors

The comparison identified specific error sources. For each, decide if it's a real visual problem on FaceIt or just a numerical artifact:

1. **MouthFunnel** (0.07 MSE): The coupled Pucker/Funnel solve produces accurate ARKit values, but the forward pass re-distributes them differently than the original MHA. May look fine on FaceIt since the ARKit values are correct.
2. **LipsTogether** (0.45 MSE): The MouthClose → LipsTogether round-trip is inherently lossy because `MouthClose = lipClosure * jawOpen` then `LipsTogether = MouthClose / adjustedJawOpen` — and adjustedJawOpen differs from raw jawOpen. This is by design for FaceIt compatibility. Visual check needed.
3. **JawOpen** (0.10 MSE): Intentionally reduced by purse compensation. The adjusted value (B) matches real ARKit better than the raw MHA value (A).

### Priority 3 (optional): Fix real ARKit comparison

If desired, fix C by modifying `forward_remap_to_mh.py` to clear ALL ctrl_expressions curves from the template before writing new ones. This requires enumerating the full set of ~300 curve names. Could read them from A's original sequence at runtime.

## Key files for continuation


| Purpose           | Path                                                                                 |
| ----------------- | ------------------------------------------------------------------------------------ |
| Start here        | `.cursor/plans/arkit-remap-next-steps_f8a2c301.plan.md` (this file)                  |
| Knowledge base    | `.cursor/arkit-remap/knowledge-base.md`                                              |
| Remap script      | `.cursor/arkit-remap/scripts/arkit_remap.py`                                         |
| Forward remap     | `.cursor/arkit-remap/scripts/forward_remap_to_mh.py`                                 |
| Comparison data   | `.cursor/arkit-remap/reports/apples_comparison_2026-03-12T152950.json`               |
| Comparison report | `.cursor/arkit-remap/reports/apples_comparison_2026-03-12T152950.md`                 |
| Mapping payload   | `.cursor/arkit-remap/mapping-pose-asset/data/AM_ArKitRemap_v02.mapping_payload.json` |
| Apples assets     | `/Game/3_FaceAnims/VEC_MHA/AgenticPy/apples/`                                        |


## To start a new chat

Say: "Continue from `@.cursor/plans/arkit-remap-next-steps_f8a2c301.plan.md` — test the remap on the FaceIt character" (or whichever priority you want to tackle).