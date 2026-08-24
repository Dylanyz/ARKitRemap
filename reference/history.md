# History — v1/v2, and what still informs decisions

The full v1/v2 material (scripts, payloads, probes, run logs, the uncompressed knowledge-base
sections A–J) lives in git history under the tag **`pre-redesign-v2`**. This file keeps only
what still informs current decisions.

## The three generations

| Gen | Mechanism | Status |
|---|---|---|
| v1 | Blueprint AnimationModifier (`AM_ArKitRemap`): 1:1 curve rename via a CurveMap + a MouthClose post-pass | superseded |
| v2 | Python pipeline (`arkit_remap.py` + JSON weight payload): weighted synthesis from a PoseAsset extraction, least-squares normalization, coupled solves, hand calibration | superseded |
| V3 | `RM_MHA_to_ARKit` RigMapper definition: mapping solved in deformation space through real RigLogic, validated against paired iPhone data | **current** |

## The hard rule that shaped V3

**v2's mapping numbers (payload weights, calibration constants like
`lipsPurseWeight=0.735`, `jawFactor=0.75`) were AI-guessed/hand-calibrated and must NOT feed
V3.** v2 material is process/reference knowledge only. V3's purity rule
([findings.md](findings.md)) is the direct response.

## v2 → V3 component migration

| v2 component | V3 replacement |
|---|---|
| `arkit_remap.py` (curve write pipeline) | `URigMapperEditorSubsystem.ConvertAnimSequence*` + engine right-click action |
| `arkit_remap_payload.json` (weights) | `RM_MHA_to_ARKit` definition JSON (ws/sdk/mul/MathOp features) |
| Mouth-pair model (Python) | calibrated MouthClose feature fitted against measured iPhone data |
| Temporal smoothing | dropped (RigMapper is a static per-frame graph; live path relies on MHA solve smoothness) |
| CSV export (`arkit_csv_export.py`) | `AAU_ARKitRemap_ExportLLFCSV` asset action → `scripts/arkit_llf_csv.py` |
| Live preview | new in V3: universal template ABP (Live Link Pose → Rig Mapper) |

## v2 lessons that still matter

- **Curve-space inversion of the forward ABP rule fails on MHA data** — v2's whole
  MouthClose calibration saga (LipsPurse contribution, jaw compensation, forward-constraint
  ratios) was symptom-chasing a model mismatch that V3 resolved by fitting against measured
  iPhone MouthClose. See [conventions.md](conventions.md).
- **Shared source curves cross-contaminate independent per-target solves** (v2's
  Pucker↔Funnel, RollLower↔RollUpper, brow-trio coupled solves). V3 avoids the whole class by
  solving all 51 weights jointly in deformation space.
- **Eye-look curves are bone/derived-driven in MetaHuman** — no clean curve-only inverse
  exists; any curve-space mapping approximates. (V3's deformation-space solve handles this
  correctly by construction.)
- **`unreal.AnimationLibrary` + controller bracket batching**
  (`seq.controller.open_bracket()`/`close_bracket()`) collapsed ~40 min of per-key writes to
  ~0.5 s/sequence — still the right pattern for any script that writes curves.
- **The community 1:1 mapping table** (`dev/pose-asset/MH_Arkit_Mapping.txt`, Csaba Kiss /
  Tomhalpin8) is subjective and disagrees with Epic's data in places (maps MouthClose to
  LipsPurse) — reference only, never a mapping source.

## PoseAsset extraction methods (if it ever needs redoing)

The established workflow lives in [dev/pose-asset/](../dev/pose-asset/) (start at its README;
regeneration order is scripts 1–6 listed there). Fallback strategies, in order: editor UI
inspection → editor Python (`get_pose_names`, `asset_mapping_table`) → C++
(`LoadObject<UPoseAsset>`) → on-disk parse (UAssetAPI) → runtime observation. Known facts:
PoseAssets are opaque to MCP asset-summary tools, and the PA has negative weights on its
`head_lod0_mesh__*` layer that pure `ctrl_expressions_*` extraction misses.
