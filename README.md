# ARKit Remap

**Use MetaHuman Animator with any character.** No iPhone required — just a webcam.

Converts **MetaHuman Animator (MHA)** facial performances into **Apple ARKit 52-blendshape** curves, so studio-quality video-based capture can drive **[FaceIt](https://faceit-doc.readthedocs.io/)** rigs, Fab characters, or any ARKit-compatible face — baked animation or **live**.

> MHA gives you the best monocular facial solve available, but it speaks MetaHuman (~250 proprietary `CTRL_expressions` curves). ARKit characters speak Apple's 52 blendshapes. This project is the translator between them.

**V3 is a ground-up rebuild** on UE 5.8's engine-native RigMapper system: the mapping is *solved mathematically in deformation space* against Epic's own MetaHuman rig — zero hand-tuned numbers — and validated against real iPhone ARKit recordings of the same performances.

📖 **[User Guide](docs/USER-GUIDE.md)** — plain-language setup, concepts, and all three workflows.

---

## Demos

https://github.com/user-attachments/assets/a9ddf4c0-bda5-4709-8903-aa86677d77a9

> V2-era demo. (That "ARKit reverses the eye directions" mystery on the right? Solved during V3: selfie-style reference video is *mirrored*, while ARKit data is in true face space — the character was right all along. See the [user guide](docs/USER-GUIDE.md#9-current-limitations--roadmap).)

## Demo 2

https://github.com/user-attachments/assets/ec8414bb-3ba4-49bf-8b5e-8e324259bb63

> Film use case — iOS ARKit vs. MHA remapped with this tool. Watch the film [here](https://www.youtube.com/@madricetv/).

---

## What V3 is

One small asset does everything: **`RM_MHA_to_ARKit`**, a UE 5.8 **RigMapper Definition** (versioned in this repo as [`v3/RM_MHA_to_ARKit.json`](v3/RM_MHA_to_ARKit.json)). 164 MHA curves in → 52 ARKit curves out. No custom runtime code — it runs on Epic's own RigMapper plugin, which means:

| Workflow | How |
|---|---|
| **Batch convert** | Right-click any MHA AnimSequence → *Convert Selected Using RigMapper* → ARKit AnimSequence out |
| **Live** | Template AnimBP: your webcam → MHA real-time solve → Live Link → character. Toggle `Use Live Link`, pick a subject, done |
| **Retargeting** | *Single RigMapper* op inside any IK Retargeter's curve stack |
| **Set-and-forget** | Stamp the definition onto a character's mesh (Asset User Data) and every RigMapper tool auto-discovers it |

Optional **head movement** pass-through (off by default): MHA's head rotation distributed naturally across the neck chain.

## How the mapping was built (and why it's trustworthy)

No guessed weights, no eyeballed calibration. The V3 pipeline:

1. **Extracted Epic's ground truth**: the `PA_MetaHuman_ARKit_Mapping` PoseAsset (Epic's own ARKit→MetaHuman table) and the `ABP_MH_LiveLink` runtime formulas, mechanically, with reproducible scripts.
2. **Evaluated the real rig**: every ARKit shape was pushed through Epic's actual RigLogic engine (the archetype MetaHuman head, 870 joints) to get its true facial deformation.
3. **Solved the inverse**: for any MHA frame, bounded least-squares finds the ARKit-52 combination whose deformation best matches what the MetaHuman face is actually doing. The static mapping was then fitted to reproduce that solve (R² 0.92) as a sparse weighted-sum graph.
4. **Validated against reality**: the same performance recorded simultaneously as iPhone ARKit *and* MHA-processed video. The remap's output correlates with the iPhone's own data at 0.96 (jaw), 0.94–0.96 (brows), 0.88 (smile), 0.87 (blink)… full per-curve tables in [`v3/reports/`](v3/reports/).
5. **MouthClose** — the one shape ARKit has and MetaHuman doesn't — is calibrated against measured iPhone data (r = 0.81), not invented.

**Purity rule**: the core definition contains only what follows from data and math. Any future "to-taste" polish ships as a separate, documented, optional layer — never baked in. Full methodology: [build plan](plans/arkit-remap-v3-plan.md) · [knowledge base](dev/knowledge-base.md) (Section L = everything V3 measured).

## Quality expectations

Honest numbers from the paired-take validation: the performance-carrying shapes (jaw, brows, smile, blink, pucker, gaze) track excellently; subtle mouth detail (dimples, lip rolls) is weaker; and ~half of MHA's fine detail simply exceeds what 52 blendshapes can express — no remap can beat the format's ceiling. Sometimes the result reads *more* expressive than phone ARKit (MHA's solve is better), occasionally less on extreme faces. See [User Guide §8](docs/USER-GUIDE.md#8-quality-what-to-expect).

## Requirements

- **Unreal Engine 5.8** (RigMapper plugin enabled; experimental since 5.7 — built and tested on 5.8)
- **MetaHuman plugin** for MHA capture (real-time webcam solve needs 5.6+)
- An ARKit-52 character (FaceIt export, Fab, CC, custom — anything with the standard 52 morph names)

## Getting started

1. Get `RM_MHA_to_ARKit` into your project — either way works:
   - **Drop-in**: copy [`v3/uassets/RM_MHA_to_ARKit.uasset`](v3/uassets/) to `YourProject/Content/ARKitRemap/` (no dependencies), or
   - **From source**: create a RigMapper Definition asset → right-click → *Load From Json* → [`v3/RM_MHA_to_ARKit.json`](v3/RM_MHA_to_ARKit.json).
2. Follow the **[User Guide](docs/USER-GUIDE.md)** for your workflow (batch / live / retargeter). The live template AnimBP and Details-panel component are a five-minute build from the guide's Appendix A (they're skeleton-specific, so they can't ship as universal assets).

---

<details>
<summary><b>V2 (legacy Python pipeline)</b> — superseded by V3</summary>

V2 was a Python-based reverse mapping (`arkit_remap.py` + weight payload) with right-click menus and CSV export for Blender/FaceIt. It worked, but its weights were reverse-engineered with subjective calibration — exactly what V3 eliminates. The V2 files remain in [`legacy/v2-python/`](legacy/v2-python/) and its history in the [improvement log](plans/arkit-remap-improvementlog.md). The CSV export use case is covered engine-natively in 5.8 by `RigMapperEditorSubsystem.ConvertAnimSequenceToCsv`.

</details>

## Deep dive

- **[Knowledge Base](dev/knowledge-base.md)** — the canonical technical reference: Epic's forward pipeline, the RigMapper system survey (Section K), and every V3 empirical finding (Section L: conventions, schemas, gotchas, scores)
- **[V3 Build Plan](plans/arkit-remap-v3-plan.md)** — the living plan with every decision recorded
- **[v3/reports/](v3/reports/)** — conditioning, solver validation, ground-truth comparisons, fit quality
- **[v3/scripts/](v3/scripts/)** — the reproducible pipeline that produced the definition (offline Python on prebuilt RigLogic bindings; not needed to *use* the remap)

## Contributing

Using **Claude Code**? Just point it at this repo — it ships a `CLAUDE.md` and an `arkit-remap` skill, so it picks up full project context automatically. Otherwise see **[CONTRIBUTING.md](CONTRIBUTING.md)**.

The single most valuable contribution right now: **paired takes** (same performance captured as iPhone ARKit CSV + mono video for MHA) — every additional pair sharpens the MouthClose calibration and the validation suite.

## License

Mozilla Public License 2.0 (`MPL-2.0`) — see [LICENSE](LICENSE). Use it, modify it, sell with it; if you distribute modified files from this project, make those files' source available under MPL-2.0 and keep the notices. Please credit the repo and author — **Dylan Gitalis** — so the project can grow.

Developed for Unreal Engine / MetaHuman workflows; users are responsible for complying with Epic's applicable license terms.

---

You made it this far!! Check out the films made with this tool: https://YouTube.com/@madricetv
