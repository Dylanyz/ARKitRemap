# ARKit Remap V3 — User Guide

Drive any ARKit-52 character (FaceIt rigs, Fab characters, CC/Reallusion, custom sculpts) with **MetaHuman Animator** facial capture — baked or live — inside Unreal Engine 5.8. No plugins to build, no custom runtime code: everything runs on UE's own RigMapper system.

This guide assumes you know your way around the UE editor but explains every concept the tool touches. You do not need to understand the math to use it.

---

## 1. What this actually does

**MetaHuman Animator (MHA)** turns video of a face (iPhone, webcam, head-mounted cam) into facial animation — but it speaks *MetaHuman*: its output is ~250 animation curves with names like `CTRL_expressions_jawOpen`. Only MetaHuman faces understand those.

**ARKit characters** understand a different, much smaller language: the 52 blendshape names Apple defined (`JawOpen`, `EyeBlinkLeft`, `MouthSmileRight`, …). Thousands of characters in the wild are rigged to exactly these 52 names.

**This project is the translator.** It converts MetaHuman-space animation into the best possible ARKit-52 approximation. The translation table wasn't tuned by eye — it was solved mathematically: every one of the 52 ARKit shapes was evaluated through Epic's actual MetaHuman rig (the same RigLogic engine the editor uses), and the mapping is the least-squares answer to "which combination of ARKit shapes deforms the face most similarly to what MHA said the face was doing." See [the plan](../plans/arkit-remap-v3-plan.md) and `v3/reports/` if you want the receipts.

The deliverable is one small asset:

> **`RM_MHA_to_ARKit`** — a *RigMapper Definition*. Think of it as a spreadsheet: 164 MetaHuman curve names in, 52 ARKit curve names out, with the solved weights connecting them. It's also versioned as human-readable JSON in this repo (`v3/RM_MHA_to_ARKit.json`).

Everything below is just different ways of feeding animation through that one asset.

---

## 2. Concepts in 60 seconds

| Term | Plain meaning |
|---|---|
| **Curve** | A named float value that animates over time (`JawOpen = 0.7` at frame 12). Facial animation in UE is mostly curves driving morph targets of the same name. |
| **Morph target / blendshape** | A stored mesh deformation. When the curve `JawOpen` hits 1.0, the mesh's `JawOpen` shape is fully applied. Curve names must match shape names — that's the whole wiring. |
| **RigMapper Definition** | Epic's asset type (UE 5.8) for translating one set of curve names/values into another. Ours is `RM_MHA_to_ARKit`. |
| **Rig Mapper node** | An AnimBP node that applies a definition to whatever pose flows through it. Curves in MHA-space enter, ARKit-52 curves exit, morphs move. |
| **Live Link** | UE's real-time data pipe. MHA streams your webcam/phone performance as a Live Link *subject* (a named source you pick from a dropdown). |
| **AnimBP (Animation Blueprint)** | The little program that decides a skeletal mesh's pose every frame. Our template AnimBP = "read Live Link subject → translate through the definition → output." |

---

## 3. What's in the package

| Asset / file | What it is |
|---|---|
| `RM_MHA_to_ARKit` (`/Game/ARKitRemap/`) | The translator. The one asset everything else uses. |
| `v3/RM_MHA_to_ARKit.json` (repo) | The same translator as versioned JSON. Right-click the asset → LoadFromJson to (re)build it in any project. |
| `abp_arkit_remap_live` (`/Game/ARKitRemap/`) | Template AnimBP for **live** driving: Live Link Pose → Rig Mapper → output, with `Use Live Link` (on/off) and `Live Link Subject` exposed as editable variables. |
| `v3/scripts/` (repo) | The offline solver/fitting pipeline that produced the definition. You never need to run it to *use* the remap. |
| `v3/reports/` (repo) | Quality reports: how the remap scores against real iPhone ARKit ground truth, per curve. |

---

## 4. Path A — Batch convert an animation (most common)

You have an MHA-exported AnimSequence (from MetaHuman Performance) and want an ARKit version for your character.

1. In the Content Browser, **right-click your MHA AnimSequence**.
2. Choose **Convert Selected Using RigMapper** (comes with the engine's RigMapper plugin — enable *RigMapper* in Edit → Plugins if you don't see it).
3. In the dialog: **Definitions** = `RM_MHA_to_ARKit`, **Target Mesh** = your ARKit character's skeletal mesh, pick an output suffix.
4. A new AnimSequence appears with 52 ARKit curves. Play it on your character — done.

(Scripted/pipeline version: `RigMapperEditorSubsystem.ConvertAnimSequenceNew` in Python — one call, same result.)

## 5. Path B — Live: drive your character with your face

Requires the MetaHuman plugin's real-time solver (UE 5.6+): connect a webcam or a Live Link Face iPhone as a **MetaHuman Animator Live Link subject** (the video-based one, not raw ARKit — the point is that MHA's solve drives everything).

1. Get your MHA subject streaming (Live Link panel should show it green).
2. Select your character in the level → Details → **Anim Class** → pick `abp_arkit_remap_live_C`.
3. That's it. Your face is on the character.

Two settings live on the AnimBP (open `abp_arkit_remap_live` → Class Defaults, or set them per-instance from your character Blueprint):

- **Live Link Subject** — which stream to listen to (default: `webcam`).
- **Use Live Link** — master on/off. Off = character returns to rest pose.

> **Skeleton note:** an AnimBP only offers itself to meshes using the same skeleton. The shipped template is on the UE5 Mannequin skeleton; for a character on a different skeleton, recreate the template there — it's four nodes: Live Link Pose → Rig Mapper (Definition = `RM_MHA_to_ARKit`) → Blend Poses by Bool → Output Pose. Two minutes of work; the definition asset is skeleton-agnostic and does all the real lifting.

## 6. Path C — Inside an IK Retargeter

When you're already retargeting a MetaHuman performance onto another character, the curves can be remapped in the same step: in the retargeter's op stack add **Remap Curves → Single RigMapper**, set Definition = `RM_MHA_to_ARKit`, and (recommended) set `bCopyAllSourceCurves = false` so only the 52 ARKit curves come out.

---

## 7. "Tagging" a character (optional convenience)

You can stamp the definition **onto the skeletal mesh asset itself** so tools find it automatically — Epic calls this *Asset User Data*:

- Think of it as a sticky note on the mesh that says "when remapping curves for me, use `RM_MHA_to_ARKit`."
- Any Rig Mapper anim node and the retargeter's *UserData RigMapper* op will read the sticky note and use that definition **without you assigning it anywhere** — set your team's characters up once, and artists never have to know the definition exists.
- To tag: open the Skeletal Mesh asset → Details → **Asset User Data** → add `RigMapper Definition User Data` → add `RM_MHA_to_ARKit` to its Definitions array.

That's all "tagging your character" means: a default stored on the mesh so every other tool auto-discovers it.

---

## 8. Quality: what to expect

Measured against real iPhone ARKit ground truth of the same performance (see `v3/reports/p2_definition_score.md`):

- **Strong** (correlation 0.75–0.96): jaw, brows, smile, blink, pucker, eye look — the shapes that carry a performance.
- **Decent**: squints, cheeks, stretch, frown, MouthClose (calibrated against measured iPhone data).
- **Weak** (inherent to the format): Dimples, MouthRollUpper, JawForward — and roughly half of MHA's fine detail simply *cannot* be expressed in 52 shapes. The remap finds the best 52-shape approximation; it cannot exceed the format's ceiling.
- Intense/extreme expressions may read slightly differently than pure ARKit capture — sometimes better (MHA's solve is often more expressive than the phone's), occasionally worse.

Philosophy: the mapping contains **zero hand-tuned numbers**. It is entirely derived from Epic's own assets, real device data, and math. Any future "to-taste" adjustments will ship as a separate, documented add-on layer — never baked into the core.

## 9. Current limitations / roadmap

- **Head movement**: MHA streams head yaw/pitch/roll + translation; pass-through to the character's neck/head bones is planned as a toggle. For now heads stay still (or come from your body animation).
- **Eyes as bones**: characters whose gaze is bone-driven rather than blendshape-driven need their own eye-bone hookup; the remap emits the EyeLook* curves either way.
- **Tongue**: MHA's video solve barely tracks tongues; `TongueOut` output exists but is weak. Phone-ARKit tongue is better if you need it.
- **L/R conventions**: the remap is *name-consistent* — `MouthLeft` means the character's own left, matching how community ARKit rigs are actually sculpted. (Fun fact discovered during development: Apple's own `MouthLeft`/`MouthRight` data is inverted relative to its eye/brow naming. The remap does not propagate that quirk.) If a specific character was sculpted with swapped sides, flip the two names in a duplicate of the definition.
- **Mirrored video sources**: selfie-style captures are mirrored; the remap faithfully reproduces whatever MHA saw. If side-correctness matters, unmirror the video before processing (or accept mirror-space, which matches how people see themselves).

## 10. FAQ

**Do I need this repo's Python scripts to use the remap?**
No. They exist to *produce and verify* the definition. Using it needs only the two assets.

**Does it work with Live Link Face (phone ARKit) input?**
That input is already ARKit — you don't need a remap at all, just point the phone subject at your character. This project is specifically for MHA-quality capture (video solve) on ARKit characters.

**Will it work in UE 5.7 or earlier?**
The definition JSON loads anywhere the RigMapper plugin exists (experimental since 5.7), but everything here is built and tested on 5.8.

**My character doesn't respond.**
Check, in order: mesh actually has the 52 ARKit morph targets (open the mesh, Morph Target Preview); curve names match exactly (`EyeBlinkLeft`, not `eyeBlinkLeft`); the Live Link subject is streaming (green in the Live Link panel); the AnimBP is on the mesh's skeleton and assigned; `Use Live Link` is on.
