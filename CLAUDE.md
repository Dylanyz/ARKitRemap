# ARKit Remap

MHA-to-ARKit facial curve remapping for Unreal Engine **5.8**. Converts MetaHuman Animator
`CTRL_expressions` curves into the 52 ARKit blendshapes for any ARKit-52-rigged character —
baked (AnimSequence → AnimSequence), live (Live Link → morph targets in real time), or CSV
(for Blender/FaceIt and other DCCs).

This repo is agent-first: **CLAUDE.md + `dev/knowledge-base.md` are the single source of
truth.** Keep all knowledge in the repo docs — don't fork it into external skills, rules, or
notes that can drift.

## Are you USING the tool or DEVELOPING it?

**Using it in a UE project → this section is your path. Do not start from `plans/` or v2.**

The deliverable is **V3**: a `RigMapperDefinition` asset (`RM_MHA_to_ARKit`) plus drop-in
helpers, all in `v3/uassets/`. Complete instructions: **`docs/USER-GUIDE.md`**. Summary:

1. **Enable the `RigMapper` plugin** in the project (.uproject Plugins array) + restart the
   editor. Without it the assets silently fail to load. (This is gotcha #1 — check it first.)
2. Copy `v3/uassets/*.uasset` into the project's `Content/ARKitRemap/` — **exact folder name;
   the assets reference each other at `/Game/ARKitRemap/...`**.
3. Pick a workflow:
   - **Baked**: right-click MHA AnimSequence(s) → *Convert Selected Using RigMapper* →
     Definitions = `RM_MHA_to_ARKit`, Target Mesh = the ARKit character's mesh.
   - **Live** (drive a mesh's ARKit morphs from MetaHuman Animator real-time / Live Link):
     set the mesh's Anim Class to `abp_arkit_remap_universal_C`, set its `LiveLinkSubject` /
     `UseLiveLink` vars. **Follow `dev/knowledge-base.md` Section K.3.1** — the field-verified
     playbook (10 gotchas: plugin default-off, transient *Update Animation in Editor* flag as
     the #1 "wired but frozen" cause, per-instance wiring on shared BPs, MetaHuman `UseLiveLink`
     conflict, input/output curve bisect recipe, Python game-thread sampling trap…).
   - **CSV export**: right-click AnimSequence → *Export Live Link Face CSV* (needs
     `AAU_ARKitRemap_ExportLLFCSV.uasset`).
4. Recording live performances: Take Recorder → From Actor → untick every component except the
   target mesh → AnimSequence with ARKit morph curves, no live link needed for playback.
5. Troubleshooting: `docs/USER-GUIDE.md` (user-level) and KB K.3.1 (agent-level, with Python
   snippets).

## Developing / improving the pipeline

- **Read `plans/arkit-remap-v3-plan.md`** for the V3 workstream. Hard rule from Dylan: **v2's
  mapping numbers (payload weights, calibration constants) were AI-guessed and must NOT feed
  V3.** V2 material is process/reference knowledge only.
- `dev/knowledge-base.md` — canonical 900+ line technical reference. Key sections: **K**
  (RigMapper system survey), **K.3.1** (live setup playbook), **L** (V3 empirical findings —
  RigLogic harness, ARKit basis solve, conventions), **E.6** (v2 pipeline, legacy), **D**
  (PA_MetaHuman_ARKit_Mapping).
- This repo is **public-facing**: other artists use it with their own agents. Write docs for
  strangers — no machine-specific absolute paths or assumptions about a particular MCP stack in
  user-facing material; label agent-stack-specific tips as such.

## Project structure

| Path | What |
|---|---|
| `v3/uassets/` | **The deliverable** — drop-in definition + live template ABP + helpers (see its README) |
| `v3/RM_MHA_to_ARKit.json` | The definition as versioned JSON (LoadFromJson rebuilds it anywhere) |
| `v3/scripts/`, `v3/reports/`, `v3/data/` | V3 solve/fit/score workspace and evidence |
| `docs/USER-GUIDE.md` | User-facing install + workflows + troubleshooting |
| `dev/knowledge-base.md` | Canonical technical reference (+ Revision Log) |
| `dev/mapping-pose-asset/` | PoseAsset extraction workspace (start at `AGENT_INDEX.md`) |
| `plans/` | V3 plan, improvement log, backlog |
| `release/`, `legacy/` | v2 Python package + old Blueprint AnimModifier — **legacy, don't ship** |

## When changing things

Keep in sync after any change:

1. `dev/knowledge-base.md` — relevant section + a dated **Revision Log** entry
2. `docs/USER-GUIDE.md` — if user-visible workflow changed
3. `CHANGELOG.md` — for user-visible changes
4. `dev/mapping-pose-asset/AGENT_INDEX.md` — if payload or script paths changed

v2-only (legacy) conventions, kept for reference: UE-side scripts use
`unreal.AnimationLibrary` (not `AnimationBlueprintLibrary`); payload JSON is the calibration
truth; controller bracket batching for curve writes. `python build_release.py` builds the v2
zip from `release/`.
