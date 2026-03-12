# ARKit Remap — Development Workspace

This folder is the working area for the MHA-to-ARKit remap pipeline. It contains all research, scripts, data, and reports used to develop and validate the tool.

## Canonical entry points

- [`knowledge-base.md`](knowledge-base.md)
  Canonical long-form technical reference and revision log (800+ lines).
- [`../release/arkit_remap.py`](../release/arkit_remap.py)
  Canonical remap script (the release copy is source-of-truth).
- [`mapping-pose-asset/data/AM_ArKitRemap_v02.mapping_payload.json`](mapping-pose-asset/data/AM_ArKitRemap_v02.mapping_payload.json)
  Canonical payload consumed by the remapper.
- [`../release/`](../release/)
  Distribution-ready package.

## Folder guide

| Folder | Contents |
|--------|----------|
| `scripts/` | Active development, calibration, validation, and comparison scripts |
| `mapping-pose-asset/` | PoseAsset extraction workspace, datasets, and regeneration index |
| `reports/` | Active durable findings plus generated run logs |
| `archive/` | Deprecated probes, one-off experiments, and superseded artifacts |

## Key dev scripts

| Script | Purpose |
|--------|---------|
| `scripts/roundtrip_validation.py` | Offline round-trip accuracy testing (no UE required) |
| `scripts/coupled_solve.py` | Standalone coupled/grouped solve verification |
| `scripts/calibrate_mouth_params.py` | Grid-search calibration against real ARKit ground truth |
| `scripts/validate_mouth_pair.py` | Per-frame mouth-pair validation on a target sequence |
| `scripts/forward_remap_to_mh.py` | ARKit→MHA forward remap for round-trip comparison |
| `scripts/compare_apples.py` | Apples-to-apples A vs B comparison |

## PoseAsset extraction

Start at [`mapping-pose-asset/AGENT_INDEX.md`](mapping-pose-asset/AGENT_INDEX.md) for the full extraction workspace.

## Maintenance rules

- Keep `knowledge-base.md`, `../release/README.md`, and `../release/` contents in sync with current runtime behavior.
- Archive deprecated probes and one-off diagnostics instead of leaving them in active folders.
- Treat `knowledge-base.md` as authoritative for behavior; other docs should summarize or package that information rather than diverge from it.
