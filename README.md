# ARKit Remap

**Use MetaHuman Animator with any character.** No iPhone required — just a webcam.

Converts **MetaHuman Animator (MHA)** facial performances into **Apple ARKit 52-blendshape**
curves, so studio-quality video-based capture can drive **[FaceIt](https://faceit-doc.readthedocs.io/)**
rigs, Fab characters, CC/Reallusion, or any ARKit-compatible face — baked animation or **live**.

> MHA gives you the best monocular facial solve available, but it speaks MetaHuman (~250
> proprietary `CTRL_expressions` curves). ARKit characters speak Apple's 52 blendshapes. This
> project is the translator between them.

**disclaimer** this is built with claude code. I have limited time to work on this and just
need a solution to get these features for myself, and happy to make it public to share. If you
have any difficulty, I recommend pasting this github link into an LLM and asking questions
about it, or using an agentic llm (claude code, antigravity, cursor, etc) and asking it to
download this repo, install it for you, walk you through the features and how to use it, etc.

---

## Demos

https://github.com/user-attachments/assets/630d3c59-fbbb-436d-a620-15f4942376bd
>yes, the first and third metahuman look exactly the same- but the third one is truly running arkit curves, I promise. They just look super identical. Also, pure arkit reverses the eyes for some reason.

<details><summary>Legacy demos (v2)</summary>

https://github.com/user-attachments/assets/a9ddf4c0-bda5-4709-8903-aa86677d77a9

> V2-era demo. (That "ARKit reverses the eye directions" mystery on the right? Solved during V3: selfie-style reference video is *mirrored*, while ARKit data is in true face space — the character was right all along. See [reference/conventions.md](reference/conventions.md).)

https://github.com/user-attachments/assets/ec8414bb-3ba4-49bf-8b5e-8e324259bb63

> Film use case — iOS ARKit vs. MHA remapped with this tool. Watch the film [here](https://www.youtube.com/@madricetv/).

</details>

---

## Install (2 minutes)

**You need:** UE **5.8** · the **RigMapper** plugin enabled (Edit → Plugins → search
"RigMapper" → check → restart) · an ARKit-52 character (FaceIt export, Fab, CC — anything with
the standard 52 morph target names). For capture itself you'll use the MetaHuman plugin (MHA),
same as for MetaHumans.

1. **Get the assets**: [releases page](https://github.com/Dylanyz/ARKitRemap/releases), or
   clone this repo and use [`uassets/`](uassets/) directly.
2. **Copy** them into your project at `Content/ARKitRemap/` (exact folder name — details and
   what each file is: [uassets/README.md](uassets/README.md)).
3. **Smoke test**: right-click any MHA AnimSequence → **Convert Selected Using RigMapper** →
   *Definitions* = `RM_MHA_to_ARKit`, *Target Mesh* = your character's mesh → play the result
   on your character. Face moves = you're done.

Every workflow has a step-by-step guide (each with a by-hand path and an agent path):

| Workflow | Playbook |
|---|---|
| Verify a setup / debug | [playbooks/verify.md](playbooks/verify.md) |
| Batch convert MHA → ARKit (most common) | [playbooks/convert-baked.md](playbooks/convert-baked.md) |
| **Live**: webcam → character, real time | [playbooks/setup-live.md](playbooks/setup-live.md) |
| Record a live performance to an AnimSequence | [playbooks/record-performance.md](playbooks/record-performance.md) |
| CSV for Blender/FaceIt (outside UE) | [playbooks/export-csv.md](playbooks/export-csv.md) |
| Inside an IK Retargeter | add *Remap Curves → Single RigMapper*, Definition = `RM_MHA_to_ARKit`, `bCopyAllSourceCurves` off |

**Using an AI agent?** Point it at this repo — `CLAUDE.md` routes it to everything. To trigger
it by name from *other* projects, add a one-line pointer skill on your machine (any agent
stack): a skill/rule named `arkit-remap` whose body says *"For anything about ARKit remap /
MHA-to-ARKit, read `<path-to-this-repo>/CLAUDE.md` and follow it."* The repo deliberately
ships no agent-stack config of its own.

## Concepts in 60 seconds

| Term | Plain meaning |
|---|---|
| **Curve** | A named float animating over time (`JawOpen = 0.7` at frame 12). UE facial animation is curves driving morph targets of the same name (case-insensitive). |
| **Morph target / blendshape** | A stored mesh deformation; the curve `JawOpen` at 1.0 applies the `JawOpen` shape fully. Name matching is the whole wiring. |
| **RigMapper Definition** | Epic's UE 5.8 asset type for translating one curve set into another. Ours is `RM_MHA_to_ARKit`: 164 MHA curves in → 52 ARKit curves out. |
| **Live Link** | UE's real-time data pipe. MHA streams your webcam/phone performance as a named *subject*. |
| **AnimBP** | The program deciding a mesh's pose every frame. Our universal template = "read Live Link subject → translate through the definition → output" — no skeleton binding, works on any character. |

## How the mapping was built (and why it's trustworthy)

No guessed weights, no eyeballed calibration:

1. **Extracted Epic's ground truth**: the `PA_MetaHuman_ARKit_Mapping` PoseAsset and the
   `ABP_MH_LiveLink` runtime formulas, mechanically, with reproducible scripts.
2. **Evaluated the real rig**: every ARKit shape pushed through Epic's actual RigLogic engine
   (the archetype MetaHuman head, 870 joints) to get its true facial deformation.
3. **Solved the inverse**: bounded least-squares finds the ARKit-52 combination whose
   deformation best matches what the MetaHuman face is doing; the static mapping was fitted to
   reproduce that solve (R² 0.92) as a sparse weighted-sum graph.
4. **Validated against reality**: the same performance recorded simultaneously as iPhone ARKit
   *and* MHA-processed video — correlation 0.96 (jaw), 0.94–0.96 (brows), 0.88 (smile), 0.87
   (blink). Full tables: [dev/reports/](dev/reports/).
5. **MouthClose** — the one shape ARKit has and MetaHuman doesn't — calibrated against
   measured iPhone data (r = 0.81), not invented.

**Purity rule**: the definition contains only what follows from data and math — zero
hand-tuned numbers. Any "to-taste" polish would ship as a separate optional layer, never baked
in. Full methodology: [reference/findings.md](reference/findings.md).

## Quality: what to expect

Honest numbers from paired-take validation ([reference/findings.md](reference/findings.md)):

- **Strong** (0.75–0.96 correlation): jaw, brows, smile, blink, pucker, eye look — the shapes
  that carry a performance.
- **Decent**: squints, cheeks, stretch, frown, MouthClose.
- **Weak** (inherent to the format): Dimples, MouthRollUpper, JawForward — and ~half of MHA's
  fine detail simply cannot be expressed in 52 shapes. No remap can beat the format's ceiling.
- Sometimes the result reads *more* expressive than phone ARKit (MHA's solve is better),
  occasionally less on extreme faces.

## Limitations / FAQ

- **Head movement**: optional `UseHeadMovement` toggle (off by default) — rotation only,
  distributed across the neck chain; sanity-check axis directions per skeleton.
- **Eyes as bones**: gaze-by-bone characters need their own eye-bone hookup; the EyeLook*
  curves are emitted either way. **Tongue**: MHA barely tracks tongues; `TongueOut` is weak.
- **L/R + mirroring**: the remap is name-consistent (`MouthLeft` = the character's own left);
  selfie-style source video is mirrored — details in
  [reference/conventions.md](reference/conventions.md).
- **Do I need the Python in this repo to use the remap?** No — scripts exist to produce,
  verify, and automate; using the remap needs only the uassets.
- **Live Link Face (phone ARKit) input?** Already ARKit — no remap needed. This project is for
  MHA-quality capture on ARKit characters.
- **UE 5.7 or earlier?** The JSON loads anywhere the RigMapper plugin exists (experimental
  since 5.7), but everything is built and tested on 5.8.
- **Character doesn't respond / frozen in editor?** [playbooks/verify.md](playbooks/verify.md),
  then [reference/gotchas.md](reference/gotchas.md).

## Deep dive / contributing

- **[reference/](reference/README.md)** — the technical reference: RigMapper system, measured
  conventions, how the definition was solved, field-verified gotchas, project history.
- **[dev/](dev/README.md)** — the solve workspace, evidence reports, PoseAsset extraction, and
  active plans. See [CONTRIBUTING.md](CONTRIBUTING.md).

The single most valuable contribution right now: **paired takes** (same performance captured
as iPhone ARKit CSV + mono video for MHA) — every additional pair sharpens the MouthClose
calibration and the validation suite.

## License

Mozilla Public License 2.0 (`MPL-2.0`) — see [LICENSE](LICENSE). Use it, modify it, sell with
it; if you distribute modified files from this project, make those files' source available
under MPL-2.0 and keep the notices. Please credit the repo and author — **Dylan Gitalis** — so
the project can grow.

Developed for Unreal Engine / MetaHuman workflows; users are responsible for complying with
Epic's applicable license terms.

---

You made it this far!! Check out the films made with this tool: https://YouTube.com/@madricetv
