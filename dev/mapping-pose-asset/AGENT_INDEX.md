# Pose Asset Mapping Agent Index

This folder is the canonical workspace for extracting and reviewing
`PA_MetaHuman_ARKit_Mapping` data.

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

- Whenever new artifacts are added/renamed in `mapping-pose-asset`, update this file in the same change.
- Whenever this index changes materially, update:
  - `.cursor/arkit-remap/knowledge-base.md` (navigation and usage guidance), and
  - `.cursor/skills/arkit-remap/SKILL.md` (future-agent workflow reminders).
- Keep paths and regeneration steps current so future agents can reproduce outputs without searching.

## Current Snapshot (quick facts)

- Pose count: `66`
- Relevant source curves sampled: `274` (`ctrl_expressions_*`)
- Adjusted non-zero records: `168`
- Raw non-zero records: `300`
- Raw-only contributors across poses: primarily persistent offsets removed by baseline subtraction
- Linearity verification snapshot: source animation reports `AAT_NONE` + linear interpolation; first clean segment (`EyeBlinkLeft`) sampled exactly linearly at `0.25 / 0.5 / 0.75 / 1.0`; transient runtime `AnimSingleNodeInstance` readback still reports no active curves

## Python ARKit Remap Pipeline (primary remap method)

The primary remap implementation is now a standalone Python script that runs
inside UE5's editor Python environment. It consumes the payload generated by
this workspace and writes ARKit curves directly into AnimSequence assets.

Behavior details live in `..\\knowledge-base.md` and the release package docs.
This section is only a navigation summary for the assets that connect back to
the pose-extraction workspace.

| Artifact | Path |
|----------|------|
| Remap script | `.cursor/arkit-remap/scripts/arkit_remap.py` |
| Temporal smoothing module | `.cursor/arkit-remap/scripts/temporal_smoothing.py` |
| Coupled solve verification | `.cursor/arkit-remap/scripts/coupled_solve.py` |
| Round-trip validation | `.cursor/arkit-remap/scripts/roundtrip_validation.py` |
| Mapping payload (input) | `data/AM_ArKitRemap_v02.mapping_payload.json` |
| Context-menu launcher | `.cursor/arkit-remap/scripts/arkit_remap_menu.py` |
| Context-menu registration | `.cursor/arkit-remap/scripts/init_unreal.py` |
| QA run logs (output) | `.cursor/arkit-remap/reports/run-logs/` |
| Improvement log | `.cursor/plans/arkit-remap-improvementlog.md` |
| Release package | `.cursor/arkit-remap/release/` |

How to run:
1. Select one or more AnimSequence assets in the Content Browser.
2. Either run `py import arkit_remap` in the UE Output Log, or right-click the
   selected assets → **Run ARKit Remap**.
   The menu entry currently appears in the main Content Browser context menu,
   not under `Asset Actions`.
   The context-menu path opens a smoothing prompt for the current run and
   passes a one-shot override (`None`, `One-Euro`, `EMA`) into the remap script.

Key technical details:
- Uses `sum(weight²)` normalization (least-squares inverse projection).
- Coupled 2-target solve for MouthPucker↔MouthFunnel, MouthRollLower↔MouthRollUpper.
- Grouped 3-target solve for BrowInnerUp + BrowOuterUpLeft/Right.
- minWeight filter (0.05) removes sub-threshold contributor artifacts.
- Controller bracket batching for fast curve writes (~0.5 s per sequence).
- 51 ARKit curves from payload + unified mouth-pair logic for `MouthClose`
  and `JawOpen`.
- `MouthClose` derives lip closure from `LipsTowards + lipsPurseWeight * LipsPurse`,
  then caps against the adjusted `JawOpen` path used for FaceIt compatibility.
- Optional temporal smoothing (1-euro filter, disabled by default).
- QA clamp-boundary alerting in run reports.
- Calibration via payload JSON (`global`, `mouthClose`, `perCurveOverrides`,
  `coupledPairs`, `coupledGroups`, `smoothing`).
- Tested on UE 5.7; uses `unreal.AnimationLibrary` (not `AnimationBlueprintLibrary`).

The Blueprint AnimModifier assets (`AM_ArKitRemap`, `AM_ArKitRemap_v02`) are now
legacy/fallback. Prefer the Python script for all new remap work.

## Conventions For Future Agents

- Keep all new pose-mapping artifacts inside this folder tree.
- Do not write these outputs to `Saved/Extracted`.
- Preserve both raw and adjusted exports unless explicitly told otherwise.
- Treat scripts as read-only with respect to Unreal assets (data export only).
