# ARKit Remap v2

Converts **MetaHuman Animator (MHA)** facial performances (`CTRL_expressions`
curves) into **Apple ARKit 52-blendshape** curves so they can drive
**FaceIt** or other ARKit-compatible facial rigs.

## Package contents

- `arkit_remap.py`
  Main remap script.
- `arkit_remap_payload.json`
  Mapping payload and calibration config.
- `init_unreal.py`
  Optional startup script that registers the right-click menu entry.
- `arkit_remap_menu.py`
  Optional context-menu launcher with smoothing prompt.
- `temporal_smoothing.py`
  Optional runtime helper used when smoothing is enabled.

## Installation

1. Copy `arkit_remap.py` and `arkit_remap_payload.json` into your project's
   `Content/Python/` folder.
2. If you want the right-click menu, also copy `init_unreal.py`,
   `arkit_remap_menu.py`, and `temporal_smoothing.py` into `Content/Python/`.
3. Enable Unreal's **Python Editor Script Plugin**.
4. Restart the editor only if you added `init_unreal.py` for menu support.

No project config edits are required for the console workflow.

## Usage

### Option A: Output Log command

1. Select one or more `AnimSequence` assets in the Content Browser.
2. In the Output Log, run: `py import arkit_remap`

### Option B: Right-click context menu

1. Copy the optional menu files listed above.
2. Select one or more `AnimSequence` assets.
3. Right-click and choose **Run ARKit Remap**.

The menu path opens a one-shot smoothing prompt:

- `Yes` = One-Euro
- `No` = EMA
- `Cancel` = None

This override affects only the current run and does not modify the payload.

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
