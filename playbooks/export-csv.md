# Export a Live Link Face CSV

**Goal:** an AnimSequence becomes a `<name>_LLF.csv` in the exact format the Live Link Face
app records (Timecode + 61 columns in Apple's order) — for FaceIt's CSV import in Blender, or
any tool that reads LLF recordings.
**Prereqs:** [install](../uassets/README.md) incl. `AAU_ARKitRemap_ExportLLFCSV.uasset` ·
Python Editor Script Plugin enabled (UE default).

## Steps

1. Select the AnimSequence(s) in the Content Browser — remapped ARKit sequences **or raw MHA
   sequences** (raw ones are auto-remapped through `RM_MHA_to_ARKit` first; the intermediate
   `_ARKit` sequence is kept).
   Check: selection includes only AnimSequences.

2. Right-click → **Scripted Asset Actions → Export Live Link Face CSV**. Answer the prompt
   (re-import into UE as a LevelSequence too? — needs the *Live Link Face Importer* plugin;
   without it the export is CSV-only).
   Agent: the action's logic lives in `scripts/arkit_llf_csv.py`; the asset action is the
   supported entry point.
   Check: `<name>_LLF.csv` appears beside each asset on disk.
   If it fails: menu entry missing → the AAU asset isn't installed
   ([install-path](../reference/gotchas.md#install-path)); auto-remap fails →
   [plugin-off](../reference/gotchas.md#plugin-off).

3. Import in the target tool (Blender/FaceIt: FaceIt's Live Link import).
   Check: the animation plays on the rig.
   Note: never rename the CSV to exactly match a UE asset's name —
   [csv-name-collision](../reference/gotchas.md#csv-name-collision).
