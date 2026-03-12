# ARKit Remap — Agent Instructions

MHA-to-ARKit facial curve remapping pipeline for Unreal Engine. Converts MetaHuman Animator `CTRL_expressions` curves into 52 ARKit blendshapes for FaceIt-rigged characters.

## Project structure

- `release/` — user-facing package (copy to `Content/Python/` to install)
- `dev/` — full development workspace (scripts, data, reports, archive)
- `dev/knowledge-base.md` — canonical 800+ line technical reference
- `dev/mapping-pose-asset/` — PoseAsset extraction workspace (start at `AGENT_INDEX.md`)
- `plans/` — improvement log and backlog
- `legacy/` — old Blueprint AnimModifier (.uasset)

## Key files

| Purpose | Path |
|---------|------|
| Main remap script | `release/arkit_remap.py` |
| Mapping payload + calibration | `release/arkit_remap_payload.json` |
| Smoothing filters | `release/temporal_smoothing.py` |
| Context menu launcher | `release/arkit_remap_menu.py` |
| Menu registration (UE startup) | `release/init_unreal.py` |
| Technical reference | `dev/knowledge-base.md` |
| Improvement log + backlog | `plans/arkit-remap-improvementlog.md` |
| PoseAsset extraction index | `dev/mapping-pose-asset/AGENT_INDEX.md` |

## How to run

1. Copy `release/` contents into a UE project's `Content/Python/`.
2. Enable Python Editor Script Plugin.
3. Select AnimSequence(s) in Content Browser.
4. Output Log: `py import arkit_remap`

## Testing and validation

- `dev/scripts/roundtrip_validation.py` — offline round-trip accuracy (no UE needed)
- `dev/scripts/coupled_solve.py` — standalone coupled/grouped solve verification
- Both are pure Python, runnable outside Unreal.

## Code style

- Python scripts that run inside UE use `unreal.AnimationLibrary` (not `AnimationBlueprintLibrary`).
- Payload JSON is the single source of calibration truth — don't hardcode magic numbers.
- Use controller bracket batching for all curve writes.

## When changing code

Keep these in sync after any pipeline changes:

1. `dev/knowledge-base.md` Section E.6 — update behavior/coverage description
2. `dev/knowledge-base.md` Revision Log — add a dated entry
3. Skill files (`.cursor/skills/arkit-remap/SKILL.md` and `.agent/skills/arkit-remap/SKILL.md`)
4. `dev/mapping-pose-asset/AGENT_INDEX.md` — if payload or script paths changed
5. `CHANGELOG.md` — for user-visible changes

## Build and release

```
python build_release.py
```

Produces `dist/ARKitRemap-v<version>.zip` from `release/` contents.

## Key technical context

- Uses `sum(weight²)` normalization (least-squares inverse projection)
- Coupled solve for MouthPucker↔MouthFunnel, MouthRollLower↔MouthRollUpper
- Grouped 3-target solve for BrowInnerUp + BrowOuterUpLeft/Right
- Unified mouth-pair model: MouthClose derived from LipsTowards + LipsPurse, JawOpen purse-compensated
- minWeight filter (0.05) removes trace contributor artifacts
- EMA smoothing recommended over One-Euro
- Tested on UE 5.7

## Deep dive

For full pipeline math, calibration methodology, forward/reverse pipeline analysis, and gap analysis, read `dev/knowledge-base.md`.
