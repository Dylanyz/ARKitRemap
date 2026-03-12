# ARKit Remap

**Use MetaHuman Animator with any character.** No iPhone required — just a webcam.

ARKit Remap converts MetaHuman Animator (MHA) facial performances into Apple ARKit 52-blendshape curves, so they can drive characters rigged with [FaceIt](https://faceit-doc.readthedocs.io/) or any other ARKit-compatible facial rig.

> MHA gives you studio-quality facial capture from monocular video, but outputs its own proprietary curve format (~130+ `CTRL_expressions` curves). FaceIt characters expect the 52 standard ARKit blendshapes. This tool bridges the gap using weighted reverse mapping extracted from Epic's own PoseAsset data.

---

## Quick Start

### 1. Download

Grab the latest release zip from [**Releases**](https://github.com/Dylanyz/ARKitRemap/releases).

### 2. Install

Copy the contents of the zip into your Unreal project's `Content/Python/` folder:

```
YourProject/
  Content/
    Python/
      arkit_remap.py              ← required
      arkit_remap_payload.json    ← required
      init_unreal.py              ← optional (right-click menu)
      arkit_remap_menu.py         ← optional (right-click menu)
      temporal_smoothing.py       ← optional (smoothing filters)
```

Make sure the **Python Editor Script Plugin** is enabled in your project (Edit → Plugins → search "Python").

### 3. Run

1. Select one or more **AnimSequence** assets in the Content Browser (these should be your MHA-baked performances).
2. In the **Output Log**, type:

```
py import arkit_remap
```

That's it. Each selected sequence gets a `*_ARKit` duplicate with all 52 ARKit curves written.

### Optional: Right-Click Menu

If you copied the optional files (`init_unreal.py`, `arkit_remap_menu.py`, `temporal_smoothing.py`), restart the editor. You'll get a **Run ARKit Remap** entry when you right-click AnimSequence assets. It opens a smoothing prompt before running:

| Choice | Mode | When to use |
|--------|------|-------------|
| **Yes** | EMA (recommended) | Simple, predictable smoothing. Best default. |
| **No** | One-Euro | Adaptive smoothing. Use if EMA leaves too much noise. |
| **Cancel** | None | Raw output. Best for QA or already-clean animations. |

---

## What It Does

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

| Parameter | Default | What it controls |
|-----------|---------|-----------------|
| `mouthClose.lipsPurseWeight` | 0.735 | How much LipsPurse contributes to MouthClose derivation |
| `mouthClose.forwardConstraintRatio` | 1.5 | Max ratio of MouthClose to JawOpen |
| `mouthClose.clampMax` | 0.5 | Upper clamp for MouthClose output |
| `jawPurseCompensation.factor` | 0.75 | How much JawOpen is reduced when lips are pursed |
| `calibrationDefaults.minWeight` | 0.05 | Threshold for filtering trace contributors |
| `smoothing.enabled` | false | Enable/disable temporal smoothing |

---

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

## License

[MIT](LICENSE) — Dylan G, 2026
