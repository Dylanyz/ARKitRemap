# PoseAsset extraction workspace

This folder is the canonical workspace for extracting and reviewing
`PA_MetaHuman_ARKit_Mapping` data. The extraction fed both the v2 payload (historical) and
V3's forward table; how V3 uses it is in [reference/findings.md](../../reference/findings.md).

Note on script outputs: the UE-side scripts (`extract_pose_asset_mapping.py`,
`introspect_pose_asset.py`, `verify_pose_asset_linearity.py`) write to
`<project>/Saved/ARKitRemap/pose-asset` (override via `ARKITREMAP_OUT`); copy results back
into `data/` and `reports/` here. The offline scripts read/write this folder directly.

## Purpose

- Extract ARKit pose to `CTRL_expressions_*` mapping data from the PoseAsset source animation.
- Keep both output variants:
  - baseline-adjusted values (recommended for remap logic work),
  - raw absolute values (for audits/debugging).
- Provide reproducible scripts and reports for future agents.

## Folder Map

- `scripts`
  - `extract_pose_asset_mapping.py`  
    Generates adjusted + raw mapping JSON and a run log.
  - `introspect_pose_asset.py`  
    Captures API/asset introspection details for UE Python troubleshooting.
  - `verify_pose_asset_linearity.py`  
    Runs the current linearly-focused verification pass: direct runtime readback attempt on `SKM_Face`, additive/interpolation property audit, and a clean 0.25/0.5/0.75/1.0 sample on the first source-animation pose segment.
  - `compare_posemaps.py`  
    Builds a raw-vs-adjusted contributor diff report.
  - `build_reverse_mapping_table.py`  
    Builds a derived reverse mapping table (ARKit target -> weighted MHA contributors).
  - `validate_reverse_mapping_table.py`  
    Validates reverse-map structure/coverage and writes a pass/fail report.
  - `build_am_v02_payload.py`  
    Builds compact AM_ArKitRemap_v02 implementation payload from reverse_map (class sections + missing-target metadata + calibration defaults).

- `data`
  - `PA_MetaHuman_ARKit_Mapping.posemap.json`  
    Baseline-adjusted dataset (`baselineAdjustment = subtract_default_pose_sample_per_curve`).
  - `PA_MetaHuman_ARKit_Mapping.posemap.raw.json`  
    Raw absolute dataset (`baselineAdjustment = none`).
  - `PA_MetaHuman_ARKit_Mapping.posemap.log.txt`  
    Run metadata (pose count, source animation path, curve count, sequence length).
  - `PA_MetaHuman_ARKit_Mapping.introspection.json`  
    Probe output for available PoseAsset/AnimSequence Python access.
  - `PA_MetaHuman_ARKit_Mapping.linearity_verification.json`  
    Machine-readable output from `verify_pose_asset_linearity.py` covering runtime probe status, source-animation fractional samples, and additive/interpolation property audit.
  - `PA_MetaHuman_ARKit_Mapping.reverse_map.json`  
    Derived reverse mapping table with per-target contributor weights and normalized metadata.
    Includes split sections under `reverseMappingTableByClass`:
    - `arkit52` (core targets),
    - `extended_pose` (`Pose_4` to `Pose_17` family),
    - `other_targets` (default/other residuals).
  - `AM_ArKitRemap_v02.mapping_payload.json`  
    Compact implementation payload for AM_ArKitRemap_v02 runtime logic. Includes:
    - `arkit52`, `extended_pose`, `other_targets`,
    - `missingArkit52Targets`,
    - calibration defaults (`global`, `mouthClose`, optional `perCurveOverrides`),
    - coupled solve config (`coupledPairs`, `coupledGroups`).

- `reports`
  - `PA_MetaHuman_ARKit_Mapping_extraction_results.md`  
    High-level extraction summary and artifact references.
  - `PA_MetaHuman_ARKit_Mapping_raw_vs_adjusted.md`  
    Per-pose contributor comparison between raw and adjusted outputs.
  - `PA_MetaHuman_ARKit_Mapping_reverse_map_summary.md`  
    Human-readable summary with separate sections for core ARKit 52 and extended poses.
  - `PA_MetaHuman_ARKit_Mapping_reverse_map_validation.md`  
    Structural validation report for reverse-map output (coverage + consistency checks).
  - `PA_MetaHuman_ARKit_Mapping_linearity_verification.md`  
    Human-readable summary of the current linearity check. Current result: first uncontaminated segment is exactly linear; transient runtime curve readback remains inconclusive from Python.
  - `AM_ArKitRemap_v02_mapping_payload_summary.md`  
    Snapshot report for payload generation (coverage counts + missing-target list + default calibration policy).

## Regeneration Order

1. Run `scripts/extract_pose_asset_mapping.py`
2. Run `scripts/introspect_pose_asset.py`
3. Run `scripts/verify_pose_asset_linearity.py`
4. Run `scripts/compare_posemaps.py`
5. Run `scripts/build_reverse_mapping_table.py`
6. Run `scripts/validate_reverse_mapping_table.py`
7. Run `scripts/build_am_v02_payload.py`

## How to use this index

1. Start with this file to locate scripts, datasets, and reports.
2. Use the `scripts` section for regeneration tasks.
3. Use the `data` section for machine-readable inputs to remap logic.
4. Use the `reports` section for fast human review before implementation changes.

## Maintenance protocol (required)

- Whenever new artifacts are added/renamed in this folder, update this file in the same change.
- Whenever this index changes materially, update the pointers in
  [reference/findings.md](../../reference/findings.md) and add a Revision Log line
  ([reference/README.md](../../reference/README.md)).
- Keep paths and regeneration steps current so future agents can reproduce outputs without searching.

## Current Snapshot (quick facts)

- Pose count: `66`
- Relevant source curves sampled: `274` (`ctrl_expressions_*`)
- Adjusted non-zero records: `168`
- Raw non-zero records: `300`
- Raw-only contributors across poses: primarily persistent offsets removed by baseline subtraction
- Linearity verification snapshot: source animation reports `AAT_NONE` + linear interpolation; first clean segment (`EyeBlinkLeft`) sampled exactly linearly at `0.25 / 0.5 / 0.75 / 1.0`; transient runtime `AnimSingleNodeInstance` readback still reports no active curves

## Downstream consumers

- **V3 (current)**: the fresh PA extraction (`dev/solve/scripts/extract_pa_mapping.py` →
  `dev/solve/data/pa_mapping.json`) supersedes this workspace's datasets as the solve input,
  but the datasets here remain the audited reference extraction (raw vs. adjusted, reverse
  map, linearity verification).
- **v2 (historical)**: `AM_ArKitRemap_v02.mapping_payload.json` fed the retired v2 Python
  pipeline — see [reference/history.md](../../reference/history.md); the pipeline itself lives
  under the git tag `pre-redesign-v2`.

## Conventions For Future Agents

- Keep all new pose-mapping artifacts inside this folder tree.
- Do not write these outputs to `Saved/Extracted`.
- Preserve both raw and adjusted exports unless explicitly told otherwise.
- Treat scripts as read-only with respect to Unreal assets (data export only).
