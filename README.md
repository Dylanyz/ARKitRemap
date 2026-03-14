# ARKit Remap

**Use MetaHuman Animator with any character.** No iPhone required — just a webcam.

Converts **MetaHuman Animator (MHA)** facial performances into **Apple ARKit 52-blendshape** curves so they can drive
**[FaceIt](https://faceit-doc.readthedocs.io/)** or other ARKit-compatible facial rigs.

*Also includes* easy .CSV convert, to export for Blender/FaceIt/wherever!

> MHA(MetaHuman Animator) gives you studio-quality facial capture from monocular video, but outputs its own proprietary curve format (~130+ `CTRL_expressions` curves). FaceIt characters expect the 52 standard ARKit blendshapes. This tool bridges the gap using weighted reverse mapping extracted from Epic's own PoseAsset data.

# Demo

https://github.com/user-attachments/assets/a9ddf4c0-bda5-4709-8903-aa86677d77a9

> This video shows two examples. *Not sure why ARKit on the right is reversing the eye directions...*

<details>
<summary>demo video details/examples</summary>

### Example 1. Character rigged with FaceIt.

*No manual corrections, just the basic workflow.*

**Left:** The footage you see ran through metahuman animator(mono video input) and remmapped with ArKit Remap, to create ArKit curves the character can use

**Right:** The straight ArKit curves from Live Link Face iOS

### Example 2. Metahuman

**Left:** The same footage, ran through metahuman animator(mono video input), applied to the Metahuman

**Middle:** The metahuman animator sequence remapped with ArKit Remap to create ArKit curves, then applied to the metahuman. *Note, in doing this, the pipeline needs to convert the arkit curves BACK into metahuman animator curves. Essentially going from MHA -> ArKit -> MHA haha. You would never do this- for visualization purposes.*

Right: Straight ArKit curves from Live Link Face iOS. *These are also converted to MHA curves through Epic's pipeline*

</details>
---

<details>
<summary> ## Package contents </summary>

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

</details>

## Installation

1. Copy all the package files into your project's
   `Content/Python/` folder.
2. Enable Unreal's **Python Editor Script Plugin**.
- If you want to re-import your CSVs back into the engine, also enable the
   **Live Link Face Importer** plugin.
3. Restart the editor
> If you don't want context menus, only copy `arkit_remap.py` and `arkit_remap_payload.json`. Then run with `py import arkit_remap`

## Usage

1. Select one or more `AnimSequence` assets.
2. Right-click and choose **Run ARKit Remap** to remap, or **ARKitRemap - Convert to CSV** to export.

The **Run ARKit Remap** prompt:

- `Yes` = EMA smoothing (recommended)
- `No` = One-Euro smoothing
- `Cancel` = No smoothing
- `X` = Close window and cancel

This override affects only the current run.

### Convert to CSV (export for Blender / other DCCs)

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

---

## ELI5 What the tool does

Theres 2 facial systems.

1. Unreal Engine metahumans
2. ArKit (made by apple)
   Metahumans have the best facial animations and work with any camera, but it has to be a normal human character.

ArKit is really easy to apply to any character or creature([FaceIt](https://faceit-doc.readthedocs.io/)), but you need an iPhone to record it, and its alot less good quality.

Unreal Engine has a converter to apply ArKit animations onto Metahumans. But doesn't provide the reverse. That's what this tool does.

I mapped out the pipeline of how Unreal converts ArKit onto Metahumans and reversed it so it can go the other way around.
So now I am not limited to an iPhone, and I get the higher quality animations.

---

## What the Tool Does

```
Your webcam video
    ↓
MetaHuman Animator (MHA)
    ↓
Baked AnimSequence with ~130 CTRL_expressions curves
    ↓
ARKit Remap  ← this tool
    ↓
52 ARKit blendshape curves
    ↓
Your FaceIt character comes alive
```

The tool:

- **Duplicates** each selected AnimSequence as `*_ARKit`
- **Synthesizes** 51 ARKit curves using weighted least-squares from Epic's own PoseAsset mapping data
- **Derives** MouthClose via a unified mouth-pair model (lip closure + jaw compensation)
- **Optionally smooths** the output with EMA or One-Euro temporal filters
- Runs in **under 1 second** per sequence (vs. minutes with the old Blueprint approach)
- Re-running on the same source clears and rewrites — safe to iterate

### Using with Body Animations

Use a **slot system** to combine face + body:

1. Create an AnimBlueprint for your character
2. Add a slot in Anim Slot Manager (e.g. "FaceSlot")
3. Add a **Layered Blend Per Bone** node:
   - Body slot → Base Pose
   - Face slot → Blend Poses 0
   - Set **Bone Name** to `head`, **Blend Depth** to `1`
4. In Sequencer, right-click the animation section → Animation → Slot → type your slot name

This makes the face animation only affect the head bone and its children.

---

## How It Works

### The Problem

MetaHuman Animator outputs ~130+ proprietary `CTRL_expressions` curves. FaceIt and other ARKit rigs expect the standard 52 ARKit blendshapes (eyeBlinkLeft, jawOpen, mouthSmileLeft, etc.). These are completely different naming conventions with different value semantics — it's not a simple rename.

### The Solution

Epic ships a PoseAsset (`PA_MetaHuman_ARKit_Mapping`) that maps between ARKit and MHA curves using weighted combinations. We extracted those weights and built a reverse pipeline:

1. **Weighted least-squares synthesis** — each ARKit curve is reconstructed from multiple MHA source curves using the formula:

   ```
   arkitValue = Σ(weight × sourceValue) / Σ(weight²)
   ```

   This `sum(weight²)` normalization produces physically plausible blendshape values.
2. **Coupled and grouped solves** — targets that share source curves (like MouthPucker/MouthFunnel, or the brow trio) are solved jointly via small linear systems instead of independently, eliminating cross-contamination artifacts.
3. **Unified mouth-pair model** — MouthClose and JawOpen are computed together because MetaHuman represents "closed mouth" differently than ARKit. MHA uses high JawOpen + LipsPurse; ARKit uses low JawOpen + high MouthClose. The model translates between these representations with calibrated parameters fitted against real iPhone ARKit ground truth.
4. **minWeight filtering** — removes trace contributors (like `browlaterall` at 0.031) that would pollute unrelated targets.

### Calibration

All parameters are tunable in `arkit_remap_payload.json`:


| Parameter                           | Default | What it controls                                        |
| ------------------------------------- | --------- | --------------------------------------------------------- |
| `mouthClose.lipsPurseWeight`        | 0.735   | How much LipsPurse contributes to MouthClose derivation |
| `mouthClose.forwardConstraintRatio` | 1.5     | Max ratio of MouthClose to JawOpen                      |
| `mouthClose.clampMax`               | 0.5     | Upper clamp for MouthClose output                       |
| `jawPurseCompensation.factor`       | 0.75    | How much JawOpen is reduced when lips are pursed        |
| `calibrationDefaults.minWeight`     | 0.05    | Threshold for filtering trace contributors              |
| `smoothing.enabled`                 | false   | Enable/disable temporal smoothing                       |

#### Remap tuning process

I basically tried to use the **pose_mapping asset** as the main basis for the remap. Cause that is Epic's mapping for arkit->MHA. So I extracted all that information and it's [in the repo](https://github.com/Dylanyz/ARKitRemap/tree/main/dev/mapping-pose-asset).

Then the parameters were tweaked and improved by having AI compare the data of the same facial take between:

1)**MHA solve** | 2)**arkit remap**(MHA converted to arkit) | 3)**raw arkit** from live link face |

> All from the same take and phone (i used the reference video from live link face as mono video input for MHA).

I also took screenshots at various points that the mouth open or close didn't line up to get it to correct it. Through doing that, I think subjectivity came into play(which I don't want- I want an exact reversing of Epic's arkit->MHA pipeline).

Also, this was just one small take, and there may have been errors with lining up the timing. So I think with more data for the AI agent to cross reference between those three assets of the same take, and rebuilding from that and the pose mapping asset, we can get the remap payload json even more accurate.

## Compatibility

- **Unreal Engine:** Tested on UE 5.7
- **Python:** Uses `unreal.AnimationLibrary` (built into UE's Python environment)
- **Input:** Any baked MHA AnimSequence with `CTRL_expressions` curves
- **Output:** 52 ARKit blendshape curves on a duplicated AnimSequence
- **Target rigs:** FaceIt, or any ARKit-compatible morph target rig

### Known Limitations

- **Eye-look curves** are bone-driven in MetaHuman and don't have clean curve-only inverses. The pipeline writes weighted approximations.
- **TongueOut** relies on `ctrl_expressions_tonguerolldown`, which is typically absent from MHA captures (produces zero output when missing).
- The legacy Blueprint AnimModifier (v1) is included in [`legacy/`](legacy/) for reference but is no longer recommended.

---

## Videos

- [ARKit vs MHA-to-ARKit comparison](https://youtu.be/oiIFQVm8Pug) (before mouth fix)
- [How the original AnimModifier worked](https://youtu.be/EF0tNFFY00Y?si=K5xUtGHVuF-Ryord)

---

## Deep Dive: Research and Knowledge Base

This tool was built through extensive reverse engineering of Epic's MetaHuman animation pipeline. The full research is available in this repo:

- **[Knowledge Base](dev/knowledge-base.md)** — 800+ line canonical technical reference covering the forward pipeline (ABP_MH_LiveLink), PoseAsset weight extraction, the reverse pipeline math, MouthClose derivation, calibration methodology, and known gaps
- **[Improvement Log](plans/arkit-remap-improvementlog.md)** — detailed history of every pipeline improvement with before/after metrics
- **[PoseAsset Extraction Workspace](dev/mapping-pose-asset/)** — scripts and data from extracting Epic's `PA_MetaHuman_ARKit_Mapping` weights
- **[Archive](dev/archive/)** — deprecated probes, calibration experiments, and superseded approaches kept for reference

---

## Contributing

Using agents like Cursor or Antigravity? No setup needed. Just paste (https://github.com/Dylanyz/ARKitRemap) into it and ask it to clone(download) the development files to your computer. The whole project is already setup for the agents to work with.

Want to improve the remap quality, add new features, or help with research? See **[CONTRIBUTING.md](CONTRIBUTING.md)** for:

- Repository structure guide
- How to set up the dev environment
- How to use AI agents (Cursor) with the included skills and rules
- Where to find everything

---

You made it this far!! Check out my YouTube videos using this tool in Unreal Engine :) https://YouTube.com/@madricetv

## License

[MIT](LICENSE) — Dylan G, 2026
