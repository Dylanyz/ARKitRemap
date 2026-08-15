# Changelog

## v3.1.0 — 2026-08-15

- **Live Link Face CSV export, asset-native**: new drop-in `AAU_ARKitRemap_ExportLLFCSV.uasset` adds right-click → *Scripted Asset Actions → Export Live Link Face CSV* on AnimSequences. Beats v2's CSV tooling: no Python files to install (the exporter ships inside the asset), accepts raw MHA sequences directly (auto-remaps through the definition first), writes spec-true LLF timecodes (60-base fractional frames), keeps v2's optional re-import-as-LevelSequence. Output is `<name>_LLF.csv` — suffixed so drag-drop can never be mistaken for a reimport of the source asset. Source of truth: `v3/ue-python/arkit_llf_csv.py` (also usable headless for pipelines).

## v3.0.0 — 2026-08-14

**Ground-up rebuild on UE 5.8's engine-native RigMapper system. Supersedes the v2 Python pipeline entirely.**

### The remap
- New deliverable: **`RM_MHA_to_ARKit`**, a RigMapper Definition (versioned as `v3/RM_MHA_to_ARKit.json`) — 164 MHA input curves → 52 ARKit outputs, 55 feature nodes.
- **Zero hand-tuned numbers.** The mapping is solved in deformation space: every ARKit shape evaluated through Epic's actual RigLogic rig (archetype MetaHuman head), inverse solved per-frame via bounded least squares, then fitted as a sparse weighted-sum/SDK graph (fit R² 0.92). v2's subjective calibration constants are gone.
- **Validated against ground truth**: same performance captured simultaneously as iPhone ARKit CSV and MHA-processed video. Definition output vs. iPhone: r = 0.96 (jaw), 0.94–0.96 (brows), ~0.88 (smile), ~0.87 (blink); mean 0.64 over all active curves — *better than the raw per-frame solver* (0.58).
- **MouthClose** calibrated against measured iPhone data (r = 0.81, amplitude-matched). The naive ABP-formula inversion was proven invalid on MHA-origin curves and discarded.
- L/R conventions locked by a dedicated calibration take: output is **name-consistent** (matches how real-world ARKit rigs are sculpted); Apple's observer-relative MouthLeft/Right quirk is *not* propagated.

### Workflows
- **Batch**: right-click Convert (engine's RigMapper action) or `RigMapperEditorSubsystem` scripting.
- **Live**: `abp_arkit_remap_live` template AnimBP — webcam → MHA real-time solve → Live Link → remap → character. Instance-editable `Use Live Link`, `Live Link Subject`, `Use Head Movement`.
- **Head movement** (off by default): MHA head rotation distributed across the neck chain (25/30/45).
- **`BC_ARKitRemapLive`** actor component: MetaHuman-style Details-panel toggles on any character BP.
- **Character tagging**: stamp the definition on a mesh via `RigMapperDefinitionUserData` for zero-config auto-discovery.
- **Retargeter**: Single RigMapper op in any IK Retargeter curve stack.

### Docs & repo
- New plain-language **[User Guide](docs/USER-GUIDE.md)**; README rewritten V3-first.
- Knowledge base Section L: every empirical finding (schemas, conventions, gotchas, scores).
- v2 Python pipeline moved to `legacy/v2-python/` (still functional, no longer maintained). v1 AnimModifier renamed within `legacy/`.
- Full reproducible pipeline in `v3/scripts/` + quality reports in `v3/reports/`.

### Known gaps (v3.0)
- Head movement axis signs unverified on non-Mannequin skeletons (toggle defaults off).
- MouthClose calibrated on one paired take — more paired takes will sharpen it.
- Template AnimBP asset ships on the UE5 Mannequin skeleton; other skeletons use the 5-minute recipe in the guide (Appendix A).

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
