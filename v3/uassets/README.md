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

`abp_arkit_remap_universal.uasset` — the live-driving template AnimBP
(Live Link Pose → Rig Mapper → output, with Use Live Link / Subject /
Use Head Movement toggles). It is a **Template Animation Blueprint — no
skeleton binding**, so it works on ANY character: set the mesh's Anim Class
to `abp_arkit_remap_universal_C` and you're live. (Head-movement bone names
resolve at runtime; rigs without `neck_01`/`neck_02`/`head` bones simply
skip those.)

`BC_ARKitRemapLive.uasset` — actor component exposing the three toggles on
the character's Details panel (MetaHuman-style). Add it to any character BP
whose mesh runs the universal template.

(`abp_arkit_remap_live.uasset` is the older skeleton-bound variant, kept for
reference only — superseded by the universal template.)

**Install:** copy to `YourProject/Content/ARKitRemap/` (create the folder if
needed), then restart or rescan. The definition and CSV-action assets have no
external dependencies; any UE 5.8 project with the RigMapper plugin enabled.

Prefer building the definition from source? Create a RigMapper Definition
asset and right-click → Load From Json →
[`../RM_MHA_to_ARKit.json`](../RM_MHA_to_ARKit.json) — identical result.
