# Changelog

## v2.1.0 — 2026-03-13

### What's New

- **"ARKitRemap - Convert to CSV" context menu entry** — right-click any remapped `*_ARKit` AnimSequence in the Content Browser and choose **ARKitRemap - Convert to CSV**. Primary use case is exporting the remapped ARKit blendshape data out of UE for use in Blender (FaceIt shape key import), other DCCs, or any tool that consumes Live Link Face-style CSV.
- On click, a prompt asks whether you want CSV-only (save beside source asset) or CSV + import back into UE as a LevelSequence (`<name>_CSV`) via `LiveLinkFaceImporterFactory`.
- Batch export: works on multiple selected AnimSequences at once.
- If `LiveLinkFaceImporterFactory` is unavailable (plugin not enabled), the prompt warns and falls back to CSV-only automatically.

### CSV format

Live Link Face-style: `Timecode`, `BlendshapeCount`, 52 ARKit blendshape columns, 9 head/eye rotation columns (zero-filled). Compatible with FaceIt's CSV import and standard Live Link Face tooling.

### Files Added

- `arkit_csv_export.py` — CSV export + optional LevelSequence import, registered as second context-menu entry in `init_unreal.py`.

### Files Changed

- `init_unreal.py` — registers both context menu entries (Remap + CSV Export).

---

## v2.0.0 — 2026-03-12

Complete rewrite from Blueprint AnimModifier to Python pipeline. This is a major upgrade in quality, speed, and configurability.

### What's New

- **Python-based remap pipeline** replacing the Blueprint AnimModifier approach
- **Weighted least-squares synthesis** using extracted PoseAsset weights (`sum(weight²)` normalization)
- **Coupled 2-target solve** for MouthPucker↔MouthFunnel and MouthRollLower↔MouthRollUpper — eliminates cross-contamination (Funnel error: 125%→0%)
- **Grouped 3-target brow solve** for BrowInnerUp + BrowOuterUpLeft/Right
- **Unified mouth-pair model** — JawOpen and MouthClose computed jointly with:
  - LipsPurse contribution to lip closure (calibrated weight: 0.735)
  - JawOpen purse compensation for FaceIt compatibility
  - Relaxed forward constraint (1.5×) matching real ARKit behavior
- **minWeight filtering** (default 0.05) — removes trace contributor artifacts
- **Optional temporal smoothing** — EMA (recommended) or One-Euro filter, per-curve overrides supported
- **Context-menu integration** — right-click AnimSequences → Run ARKit Remap with smoothing prompt
- **Controller bracket batching** — sub-second execution per sequence (vs. minutes with Blueprint)
- **QA clamp-boundary alerting** in run reports
- **Full calibration via JSON** — global, per-curve, mouth, jaw, smoothing parameters
- **Round-trip validation framework** — offline verification of all 51 payload targets

### Breaking Changes

- Replaces the Blueprint AnimModifier workflow. The legacy `AM_ArKitRemap.uasset` is still available in `legacy/` but is no longer the recommended approach.
- New file structure: Python scripts go in `Content/Python/` instead of applying a .uasset modifier.

### Calibration Improvements

- MouthClose at closed-mouth frame 956: **0.006 → 0.202** (reference: 0.203)
- JawOpen at closed-mouth frame 956: **0.53 → 0.155** (reference: ~0.11)
- MouthPucker/Funnel cross-contamination: **eliminated**
- BrowLateralL artifact across 10+ targets: **eliminated**

---

## v1.0.0 — 2026-02-08

Initial release — Blueprint AnimModifier approach.

- `AM_ArKitRemap.uasset` — right-click modifier for AnimSequences
- 1:1 curve rename from MHA to ARKit names using a CurveMap
- MouthClose fix: `MouthClose = LipsTogether × JawOpen`, clamped to [0, 0.3]
- Works but limited: no weighted mapping, no calibration, slow execution
