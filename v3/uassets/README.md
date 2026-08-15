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

**Install:** copy to `YourProject/Content/ARKitRemap/` (create the folder if
needed), then restart or rescan. No external dependencies; any UE 5.8 project
with the RigMapper plugin enabled.

Prefer building the definition from source? Create a RigMapper Definition
asset and right-click → Load From Json →
[`../RM_MHA_to_ARKit.json`](../RM_MHA_to_ARKit.json) — identical result.
