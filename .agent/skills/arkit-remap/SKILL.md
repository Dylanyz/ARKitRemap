---
name: arkit-remap
description: >-
  MHA-to-ARKit facial curve remapping pipeline for FaceIt-rigged characters.
  Covers the Python remap script, ABP_MH_LiveLink reverse engineering,
  PA_MetaHuman_ARKit_Mapping pose asset, and CTRL_expressions to ARKit blendshape
  conversion. Use when discussing ARKit remap, MHA to ARKit, AM_ArKitRemap,
  FaceIt remap, facial curve remapping, or CTRL_expressions to ARKit.
---

# ARKit Remap Pipeline

This skill provides context for the MHA-to-ARKit facial animation remapping pipeline.

## What this is

A pipeline to convert **MetaHuman Animator (MHA)** facial performances (which use ~130+ proprietary `CTRL_expressions` curves) into **Apple ARKit 52-blendshape** format, so they can drive custom characters rigged with **FaceIt** (which expects ARKit morph targets).

**Why:** MHA produces high-quality facial capture from monocular video (no iPhone needed), but outputs MHA-format curves. FaceIt-rigged characters need ARKit curves. This pipeline bridges the gap.

## Key concepts

| Term | Meaning |
|------|---------|
| ARKit 52 | Apple's 52 named facial blendshapes (eyeBlinkLeft, jawOpen, mouthSmileLeft, etc.) |
| MHA / CTRL_expressions | MetaHuman's ~130+ internal facial control curves |
| PA_MetaHuman_ARKit_Mapping | Epic's PoseAsset that maps ARKit curves to MHA curves with weights |
| ABP_MH_LiveLink | Epic's AnimBlueprint that converts ARKit (via LiveLink) into MHA curves at runtime |
| FaceIt | Blender addon that rigs characters with ARKit-compatible morph targets |

## Pipeline overview

```
Forward (Epic's pipeline):
  ARKit 52 blendshapes --> PA_MetaHuman_ARKit_Mapping --> CTRL_expressions --> MetaHuman face

Reverse (primary — Python pipeline):
  MHA CTRL_expressions (baked) --> arkit_remap.py (weighted synthesis) --> ARKit 52 curves --> FaceIt character
```

**Head rotation** is out of scope; body mocap handles head.

## Primary remap method: Python ARKit Remap v2

| Artifact | Path |
|----------|------|
| Remap script | `release/arkit_remap.py` |
| Mapping payload | `release/arkit_remap_payload.json` |
| Temporal smoothing module | `release/temporal_smoothing.py` |
| Context-menu launcher | `release/arkit_remap_menu.py` |
| CSV export (context menu) | `release/arkit_csv_export.py` |
| Context-menu registration | `release/init_unreal.py` |
| Dev scripts (calibration etc.) | `dev/scripts/` |
| Coupled solve verification | `dev/scripts/coupled_solve.py` |
| Round-trip validation | `dev/scripts/roundtrip_validation.py` |
| Mouth calibration | `dev/scripts/calibrate_mouth_params.py` |
| Mouth pair validation | `dev/scripts/validate_mouth_pair.py` |
| PoseAsset extraction workspace | `dev/mapping-pose-asset/` |
| QA run logs | `dev/reports/run-logs/` |
| Improvement log | `plans/arkit-remap-improvementlog.md` |

**How to run:**
1. Copy `release/` contents into an Unreal project's `Content/Python/`.
2. Select AnimSequence(s) in the Content Browser.
3. Run via **either**:
   - UE Output Log: `py import arkit_remap`
   - Right-click → **Run ARKit Remap** (opens smoothing prompt: EMA recommended, One-Euro, or None)
   - Right-click → **ARKitRemap - Convert to CSV** — exports ARKit blendshape curves to Live Link Face-style CSV. Primary use case: bring the animation into Blender via FaceIt's CSV import, or any other DCC/tool that consumes ARKit CSV data. Prompts: Yes = CSV only (saved beside source asset); No = CSV + import as `<name>_CSV` LevelSequence via `LiveLinkFaceImporterFactory` (requires Live Link Face Importer plugin).

**Key technical points:**
- Uses `sum(weight²)` normalization (least-squares inverse projection).
- Controller bracket batching for fast writes (~0.5 s vs ~40 min unbatched).
- 51 ARKit curves from payload + unified `_compute_mouth_pair` that jointly
  determines JawOpen (purse-compensated) and MouthClose (derived from raw
  JawOpen, capped against adjusted JawOpen, optional pucker-aware cap).
- **Coupled/grouped solve** for shared-curve targets:
  - MouthPucker↔MouthFunnel
  - MouthRollLower↔MouthRollUpper
  - BrowInnerUp + BrowOuterUpLeft/Right (3-target grouped solve)
- **minWeight filter** (default 0.05): removes sub-threshold contributor artifacts.
- MouthClose uses `ctrl_expressions_mouthlipstowards{ul,ur,dl,dr}` plus
  `ctrl_expressions_mouthlipspurse{ul,ur,dl,dr}` (with configurable
  `lipsPurseWeight`, default 0.735).
- **Optional temporal smoothing** — EMA recommended, One-Euro available.
- Calibration via payload JSON (`global`, `mouthClose`, `perCurveOverrides`,
  `coupledPairs`, `coupledGroups`, `smoothing`).
- **QA clamp-boundary alerting** in run reports.
- Tested on UE 5.7; uses `unreal.AnimationLibrary`.

**For full technical details:** see `dev/knowledge-base.md` **Section E.6**.

## Agent output organization (required)

When creating new docs, reports, scripts, or extracted data, place them under `dev/` and keep the structure tidy.

- `dev/knowledge-base.md` for long-form canonical project knowledge
- `dev/reports/` for generated findings and run summaries
- `dev/scripts/` for utility scripts
- `dev/mapping-pose-asset/` for PoseAsset-specific investigation artifacts
- `release/` for packaged release artifacts ready for distribution
- `dev/archive/` for deprecated probes and experiments

Rules for new files:
1. Use descriptive filenames with dates when relevant.
2. Prefer updating an existing file when it is the canonical location.
3. Keep one concern per file (data vs report vs script).
4. Cross-link new artifacts from `dev/knowledge-base.md`.

Required sync when `release/arkit_remap.py` changes:
1. Update `dev/knowledge-base.md` **Section E.6** with behavior/API/coverage changes.
2. Add a Revision Log entry in the KB.
3. Update this `SKILL.md` if the run workflow or release packaging changes.
4. Update `dev/mapping-pose-asset/AGENT_INDEX.md` if payload or script paths change.

Required sync when artifacts change in `dev/mapping-pose-asset/`:
1. Update `dev/mapping-pose-asset/AGENT_INDEX.md`.
2. Update `dev/knowledge-base.md` (Section D/J navigation + usage).
3. If workflow expectations changed, update this `SKILL.md`.

## Knowledge base

For detailed asset analysis, node-by-node pipeline walkthroughs, scrutiny findings, and the improvement roadmap, read:

**[knowledge-base.md](../../dev/knowledge-base.md)**

Key sections:
- **Section C** for ABP_MH_LiveLink forward pipeline detail
- **Section D** for PA_MetaHuman_ARKit_Mapping
- **Section E.6** for the Python ARKit Remap v2 (primary method)
- **Section I** for quality issues and improvement roadmap

## Updating the knowledge base

When you discover new information:
1. Read `dev/knowledge-base.md`
2. Add or update the relevant section
3. Add an entry to the **Revision Log** at the top
4. Keep all three in sync: knowledge-base, AGENT_INDEX, SKILL.md
