# AM_ArKitRemap_v02 Full Revision Run Brief

Date: 2026-03-11

## Scope Contract

- Allowed Unreal asset edit target (only):
  - `C:\Users\DYLPC\Documents\Unreal Projects\mdr_StrangerThings01\Content\3_FaceAnims\AM_ArKitRemap_v02.uasset`
- No edits allowed to any other Unreal assets:
  - no `ABP_MH_LiveLink` edits,
  - no `PA_MetaHuman_ARKit_Mapping` edits,
  - no animation sequence writes.
- Supporting artifacts may be created or updated only under:
  - `.cursor/arkit-remap/**`

## Inputs

- `.cursor/arkit-remap/mapping-pose-asset/data/PA_MetaHuman_ARKit_Mapping.reverse_map.json`
- `.cursor/arkit-remap/mapping-pose-asset/reports/PA_MetaHuman_ARKit_Mapping_reverse_map_validation.md`
- `.cursor/arkit-remap/mapping-pose-asset/AGENT_INDEX.md`
- `.cursor/arkit-remap/knowledge-base.md`
- `.cursor/plans/arkit_v02_full_revision_5c2582b0.plan.md`

## Planned Outputs

- Compact AM_v02 payload and summary under:
  - `.cursor/arkit-remap/mapping-pose-asset/data/`
  - `.cursor/arkit-remap/mapping-pose-asset/reports/`
- Updated `AM_ArKitRemap_v02` graph logic for:
  - weighted core ARKit synthesis,
  - explicit `MouthClose` branch,
  - calibration controls (global + per-curve override path).
- Non-destructive QA checklist/report in `.cursor/arkit-remap/reports/`.
- Documentation sync updates:
  - `.cursor/arkit-remap/mapping-pose-asset/AGENT_INDEX.md`
  - `.cursor/arkit-remap/knowledge-base.md`
  - `.cursor/skills/arkit-remap/SKILL.md`

## Traceability Notes

- This run brief is the scope lock artifact for `scope-lock`.
- If Unreal-side edits cannot be fully applied via MCP tooling, all blockers and partial progress must be documented in the QA report.
