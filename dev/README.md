# ARKit Remap - Development Workspace

This folder is the working area for the MHA-to-ARKit remap pipeline. It contains
the research, scripts, data, and reports used to build and validate the tool.

## Canonical entry points

- `knowledge-base.md`
  Canonical long-form technical reference and revision log.
- `release/arkit_remap.py`
  Canonical release remapper.
- `mapping-pose-asset/data/AM_ArKitRemap_v02.mapping_payload.json`
  Canonical payload consumed by the remapper.
- `release/`
  Distribution-ready package mirror for release/public publishing.

## Folder guide

- `scripts/`
  Active development, calibration, validation, and comparison scripts.
- `mapping-pose-asset/`
  PoseAsset extraction workspace, datasets, and regeneration index.
- `reports/`
  Active durable findings plus generated run logs.
- `release/`
  Files intended to be copied into another project's `Content/Python/`.
- `archive/`
  Deprecated probes, one-off experiments, and superseded artifacts kept for reference.

## Key dev scripts

- `scripts/roundtrip_validation.py`
  Offline round-trip accuracy testing.
- `scripts/coupled_solve.py`
  Standalone coupled and grouped solve verification.
- `scripts/calibrate_mouth_params.py`
  Grid-search calibration against real ARKit reference data.
- `scripts/validate_mouth_pair.py`
  Per-frame mouth-pair validation on target sequences.
- `scripts/forward_remap_to_mh.py`
  ARKit-to-MetaHuman forward remap for visual comparison.
- `scripts/import_arkit_animsequence_as_livelinkface.py`
  Converts a remapped ARKit `AnimSequence` into a Live Link Face-style CSV and
  re-imports it as a `LevelSequence` so a MetaHuman can read it through
  `ABP_MH_LiveLink`.

## MetaHuman visualization workflow

Use `scripts/import_arkit_animsequence_as_livelinkface.py` when you already have
a `*_ARKit` `AnimSequence` and want to:

- visualize the remapped ARKit result on a MetaHuman using the stock Live Link
  ARKit pipeline
- generate Live Link Face-style CSV data for a setup that consumes CSV/subject
  playback instead of a raw `AnimSequence`

What the helper does:

- reads ARKit float curves from a remapped `AnimSequence`
- writes a Live Link Face-style CSV with the 52 blendshape columns plus the
  9 head and eye rotation columns
- zero-fills missing ARKit channels and currently writes zero rotations
- imports the CSV with `LiveLinkFaceImporterFactory` into a playable
  `LevelSequence`

Important naming note:

- if the imported asset basename ends with `_cal`, the resulting Live Link
  subject is the same basename without `_cal`

This is a dev workflow, not part of the packaged `release/` install path.

## Maintenance rules

- Keep `knowledge-base.md`, `release/README.md`, and `release/` contents in sync with current runtime behavior.
- Archive deprecated probes and one-off diagnostics instead of leaving them in active folders.
- Treat `knowledge-base.md` as authoritative for behavior; other docs should summarize or package that information rather than diverge from it.
