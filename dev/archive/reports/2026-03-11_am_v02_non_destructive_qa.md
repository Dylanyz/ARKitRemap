# AM_ArKitRemap_v02 Non-Destructive QA

Date: 2026-03-11  
Scope: Validation without editing any Unreal assets other than `AM_ArKitRemap_v02`.

## Inputs Reviewed

- `.cursor/arkit-remap/mapping-pose-asset/data/PA_MetaHuman_ARKit_Mapping.reverse_map.json`
- `.cursor/arkit-remap/mapping-pose-asset/data/AM_ArKitRemap_v02.mapping_payload.json`
- `.cursor/arkit-remap/mapping-pose-asset/reports/PA_MetaHuman_ARKit_Mapping_reverse_map_validation.md`
- Unreal MCP summaries for `/Game/3_FaceAnims/AM_ArKitRemap_v02`

## Checklist

- [x] Scope lock artifact created.
- [x] Compact AM_v02 payload generated with explicit class sections and missing-target metadata.
- [x] `AM_ArKitRemap_v02` includes explicit MouthClose branch (`CTRL_Expressions_Mouth_Lips_Together_UL * JawOpen`, scaled/clamped).
- [x] Calibration controls added (`GlobalScale`, `GlobalOffset`, `GlobalClampMin`, `GlobalClampMax`, `MouthCloseClampMax`, `MouthCloseScale`).
- [x] Weighted synthesis branch added and guarded by `bUseWeightedCoreRemap`.
- [x] No changes made to `ABP_MH_LiveLink`, `PA_MetaHuman_ARKit_Mapping`, or animation sequences.

## Behavior Gates (Pass/Fail)

- Mouth behavior:
  - **PASS**: explicit `MouthClose` path exists and no longer depends on implicit fallback.
  - **PASS**: configurable max clamp for MouthClose (`MouthCloseClampMax`, default `0.3`).
- Jaw behavior:
  - **PASS**: MouthClose computation multiplies by `JawOpen` each frame (lips-together semantics).
  - **RISK**: `JawOpen` itself still uses existing transfer path and is not multi-contributor synthesized in current graph.
- Brow behavior:
  - **PARTIAL**: weighted branch is present (`bUseWeightedCoreRemap`) but currently confirmed for at least one core weighted target path; full arkit52 weighted coverage is not yet confirmed by MCP summary output.
- Asymmetry behavior:
  - **PARTIAL**: weighted approach supports contributor blending where authored, but right/left asymmetry coverage still depends on which targets are explicitly synthesized.

## Known Caveats

- MCP graph summaries still show the legacy `EventGraph` transfer path in the asset alongside generated `OnApply` logic; manual editor inspection is recommended to confirm final execution order in runtime application.
- Payload indicates missing extracted core target: `MouthClose`. This is expected and handled through explicit branch logic.
- Full data-driven weighted synthesis for all 51 extracted arkit52 targets is not yet verifiably present from current summary output.

## Out-of-Scope Escalation Note

Editing `ABP_MH_LiveLink` or `PA_MetaHuman_ARKit_Mapping` is still out of scope for this revision, but enabling read-only comparison utilities there would help verify parity and accelerate full weighted coverage validation in a future pass.
