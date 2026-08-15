# Drop-in assets

`RM_MHA_to_ARKit.uasset` — the fitted RigMapper Definition, ready to use.

`AAU_ARKitRemap_ExportLLFCSV.uasset` — Asset Action Utility that adds
**right-click AnimSequence → Scripted Asset Actions → Export Live Link Face
CSV**. Accepts remapped ARKit sequences *or* raw MHA sequences (those are
auto-remapped through the definition first). Writes `<name>_LLF.csv` beside
the asset; optionally re-imports it into UE as a LevelSequence. Requires the
Python Editor Script Plugin (enabled by default) — the exporter ships inside
the asset, nothing else to install. Source of truth:
[`../ue-python/arkit_llf_csv.py`](../ue-python/arkit_llf_csv.py).

`abp_arkit_remap_live.uasset` + `BC_ARKitRemapLive.uasset` — the live-driving
template AnimBP (Live Link Pose → Rig Mapper → output, with Use Live Link /
Subject / Use Head Movement toggles) and the actor component that exposes
those toggles on the character's Details panel. ⚠️ **Skeleton-bound example
assets**: an AnimBP is hard-bound to a specific skeleton asset path — these
were built on a UE5-Mannequin skeleton as shipped in a Fab character pack
(`/Game/MonsterPack/DemoContent/Mannequins/Meshes/SK_Mannequin_UE5`). If your
character uses a different skeleton (likely), they will not load — rebuild
them for your skeleton in ~5 minutes with the user guide's Appendix A, or
open these in a matching project as a reference.

**Install:** copy to `YourProject/Content/ARKitRemap/` (create the folder if
needed), then restart or rescan. The definition and CSV-action assets have no
external dependencies; any UE 5.8 project with the RigMapper plugin enabled.

Prefer building the definition from source? Create a RigMapper Definition
asset and right-click → Load From Json →
[`../RM_MHA_to_ARKit.json`](../RM_MHA_to_ARKit.json) — identical result.
