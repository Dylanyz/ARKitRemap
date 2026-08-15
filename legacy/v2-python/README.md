# ARKit Remap v2

Converts **MetaHuman Animator (MHA)** facial performances (`CTRL_expressions`
curves) into **Apple ARKit 52-blendshape** curves so they can drive
**FaceIt** or other ARKit-compatible facial rigs.

*Also includes* easy .CSV convert, to export for Blender/FaceIt/wherever!

## Package contents

- `arkit_remap.py`
  Main remap script.
- `arkit_remap_payload.json`
  Mapping payload and calibration config.
- `init_unreal.py`
  Optional startup script that registers both right-click menu entries.
- `arkit_remap_menu.py`
  Context-menu launcher for Run ARKit Remap (smoothing prompt).
- `arkit_csv_export.py`
  Context-menu launcher for Convert to CSV (export + optional UE import).
- `temporal_smoothing.py`
  Optional runtime helper used when smoothing is enabled.

## Installation

1. Copy `arkit_remap.py` and `arkit_remap_payload.json` into your project's
   `Content/Python/` folder.
2. If you want the right-click menus, also copy `init_unreal.py`,
   `arkit_remap_menu.py`, `arkit_csv_export.py`, and `temporal_smoothing.py`
   into `Content/Python/`.
3. Enable Unreal's **Python Editor Script Plugin**.
4. To use **Convert to CSV → import to Content Browser**, also enable the
   **Live Link Face Importer** plugin.
5. Restart the editor only if you added `init_unreal.py` for menu support.

No project config edits are required for the console workflow.

## Usage

### Option A: Output Log command

1. Select one or more `AnimSequence` assets in the Content Browser.
2. In the Output Log, run: `py import arkit_remap`

### Option B: Right-click context menu

1. Copy the optional menu files listed above.
2. Select one or more `AnimSequence` assets.
3. Right-click and choose **Run ARKit Remap** to remap, or **ARKitRemap - Convert to CSV** to export.

The **Run ARKit Remap** prompt:

- `Yes` = EMA smoothing (recommended)
- `No` = One-Euro smoothing
- `Cancel` = No smoothing
- `X` = Close window and cancel

This override affects only the current run and does not modify the payload.

### Option C: Convert to CSV (export for Blender / other DCCs)

The **ARKitRemap - Convert to CSV** context menu entry exports the remapped ARKit
blendshape curves to a Live Link Face-style CSV. Primary use case is bringing
the animation data into Blender via FaceIt's CSV import, or any other tool that
consumes ARKit CSV data.

On click a prompt appears:

- `Yes` = CSV only — saves `<name>.csv` beside the source asset in `Content/`.
- `No` = CSV + import to Content Browser — also runs `LiveLinkFaceImporterFactory`
  and creates a `<name>_CSV` LevelSequence in the same folder.
  Requires the **Live Link Face Importer** plugin to be enabled in UE.
- `X` = Close window and cancel

CSV format: `Timecode`, `BlendshapeCount`, 52 ARKit blendshape columns, 9 head/eye
rotation columns (zero-filled). Compatible with FaceIt's CSV import.

## What the script does

- Duplicates each selected sequence as `*_ARKit`
- Preserves the original MHA curves on the duplicate
- Synthesizes 51 ARKit curves from the payload using least-squares
  normalization (`sum(weight^2)`)
- Derives `MouthClose` via the unified mouth-pair logic:
  - lip closure from `LipsTowards + lipsPurseWeight * LipsPurse`
  - `JawOpen` purse compensation for FaceIt compatibility
  - forward-constraint cap against adjusted `JawOpen`
- Optionally applies temporal smoothing
- Saves the duplicate automatically

Re-running on the same source clears and rewrites the ARKit output curves.

## Calibration

Edit `arkit_remap_payload.json` to tune:

- `calibrationDefaults.global`
- `calibrationDefaults.mouthClose`
- `calibrationDefaults.jawPurseCompensation`
- `calibrationDefaults.perCurveOverrides`
- `calibrationDefaults.minWeight`
- `smoothing`

Current calibrated defaults include:

- `mouthClose.lipsPurseWeight = 0.735`
- `mouthClose.forwardConstraintRatio = 1.5`
- `mouthClose.clampMax = 0.5`
- `jawPurseCompensation.factor = 0.75`

## Notes

- If `temporal_smoothing.py` is missing, the remapper still runs; smoothing is
  simply skipped.
- The menu entry currently appears in the main Content Browser context menu
  rather than under `Asset Actions`.
- Tested on Unreal Engine 5.7.
