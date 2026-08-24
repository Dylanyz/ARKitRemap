# Gotchas — field-verified failure modes

Every entry below cost real debugging time (first production deployment: MDR_Doomsday
SpiderMask_BND, 2026-08-20; Sequencer/Take Recorder entries added in v3.1.x). Format:
symptom → cause → fix. Anchors are stable — playbooks and `scripts/verify_setup.py` link to
them; don't rename without a cross-link audit.

## plugin-off {#plugin-off}

**Symptom:** `unreal.load_asset("/Game/ARKitRemap/RM_MHA_to_ARKit")` returns None;
`hasattr(unreal, "RigMapperDefinition")` is False; assets appear to import but silently fail.
**Cause:** the RigMapper plugin is OFF by default in every project.
**Fix:** add `{"Name": "RigMapper", "Enabled": true}` to the .uproject Plugins array (add
`RigMapperOp` too if retargeter ops are wanted) and **restart the editor**. The Epic-MCP
`PluginToolset.SetPluginEnabled` may silently no-op — verify the .uproject JSON directly.

## install-path {#install-path}

**Symptom:** the template ABP compiles but produces no ARKit output.
**Cause:** the uassets reference each other at `/Game/ARKitRemap/...` — the install folder
name is not a suggestion.
**Fix:** install to exactly `Content/ARKitRemap/` (confirm via asset-registry dependencies of
the ABP).

## frozen-in-editor {#frozen-in-editor}

**Symptom:** everything is wired, the anim instance evaluates, `get_curve_value` returns live
values — but the mesh doesn't move in the editor viewport (works in PIE). The #1 "wired but
frozen" cause.
**Cause:** editor-world (non-PIE) skeletal components do not visibly animate without
`bUpdateAnimationInEditor`. **Transient — resets on editor restart.** MetaHuman BPs set it
themselves when their live link toggle is on, which is why MetaHumans "just work" and custom
meshes don't. PIE and Take Recorder are unaffected.
**Fix:** enable *Update Animation in Editor* on the skeletal mesh component (Details → search
"update animation"). From Python on a BP-instanced component,
`set_editor_property("update_animation_in_editor", True)` fails ("cannot be edited on
templates") — call `comp.set_update_animation_in_editor(True)` instead.

## per-instance-wiring {#per-instance-wiring}

**Symptom:** setting the anim class on the Blueprint asset wires one character but not the
others (or none of the placed ones).
**Cause:** multiple level actors share one BP class (e.g. spider1/2/3 all `BP_MC_spider1_C`).
**Fix:** set `animation_mode` + `anim_class` on the **level actor instance's** component, not
in the Blueprint.

## abp-cdo-defaults {#abp-cdo-defaults}

**Symptom:** Python attempts to set the ABP's variables fail with property-name errors.
**Cause:** snake-case name guesses; `LiveLinkSubject` is a struct, not a string.
**Fix:** `unreal.get_default_object(abp.generated_class())`, then `set_editor_property` with
exact names `UseLiveLink` (bool), `LiveLinkSubject` (`unreal.LiveLinkSubjectName()` struct —
set its `name`), `UseHeadMovement` (False when body mocap owns the head). Save the ABP asset
afterwards.

## metahuman-conflict {#metahuman-conflict}

**Symptom:** the MetaHuman's own face animates alongside (or instead of) the custom mesh.
**Cause:** the character actor's own `UseLiveLink` property (actor Details → Live Link
section) drives the MetaHuman face via ABP_Face.
**Fix:** set it False per-instance when only the custom mesh should move.

## python-binding-hijack {#python-binding-hijack}

**Symptom:** probes return results from the wrong project; nothing you set seems to land.
**Cause:** a second open UE instance (e.g. a template project) captured the Python remote-exec
binding.
**Fix:** always verify `unreal.Paths.get_project_file_path()` before trusting any probe
result.

## game-thread-sampling {#game-thread-sampling}

**Symptom:** sampling a live curve repeatedly in one script returns identical values every
time.
**Cause:** a `time.sleep` loop inside one editor-Python call blocks the game thread, so
animation never ticks.
**Fix:** take instant snapshots across separate calls.

## stream-bisect {#stream-bisect}

Not a failure — the diagnostic recipe for "live chain dead somewhere". On the component's anim
instance: `inst.get_curve_value("CTRL_expressions_jawOpen")` ≠ 0 → MHA stream arriving;
`inst.get_curve_value("jawOpen")` ≠ 0 → definition producing output; `MHFDSVersion == 1.0`
confirms the MHFDS stream. The MHA real-time subject (MetaHuman Local Live Link source, e.g. a
webcam device) is **Basic role**, curves-only — Live Link Pose consumes it fine. Curve→morph
binding is case-insensitive, so lowercase ARKit morph names match fine.

## no-morph-response {#no-morph-response}

**Symptom:** conversion/live output exists but the character's face doesn't move at all.
**Cause (in order of likelihood):** mesh lacks the 52 ARKit morph targets; Live Link subject
not streaming; AnimBP not assigned; `UseLiveLink` off.
**Fix:** check in that order — open the mesh (Morph Target Preview), Live Link panel green,
Anim Class set, toggle on. Then [frozen-in-editor](#frozen-in-editor).

## sequencer-slot {#sequencer-slot}

**Symptom:** a Sequencer animation track "plays" but the mesh keeps its live/rest pose.
**Cause:** a mesh whose Anim Class is set plays Sequencer tracks through the AnimBP's
`DefaultSlot`; a graph without a Slot node silently discards the sequence.
**Fix:** fixed in `abp_arkit_remap_universal` v3.1.2 (`ComponentToLocalSpace → Slot
'DefaultSlot' → Output Pose`). Sequencer overrides live during playback; live link resumes
when it stops. Custom ABP variants must include the Slot node.

## take-recorder-crosswire {#take-recorder-crosswire}

**Symptom:** Take Recorder records the wrong component no matter which checkboxes you tick.
**Cause:** observed in UE 5.8 — the take's LevelSequence held TWO `TakeRecorderSources`
subobjects; the details panel edited one while recording read the other, with the last two
skeletal-component rows swapped. Programmatic writes to the live source get stomped every UI
tick.
**Fix:** invert the two checkboxes deliberately, or close the Take Recorder panel, fix the
stored `ActorRecorderPropertyMap` values via Python
(`unreal.ObjectIterator(unreal.ActorRecorderPropertyMap)`), and reopen. Reliable fallback:
the offline path — export the MHA performance to an AnimSequence, convert through the
definition ([playbooks/convert-baked.md](../playbooks/convert-baked.md)), and place the result
on the mesh in a LevelSequence.

## csv-name-collision {#csv-name-collision}

**Symptom:** dragging an exported CSV into UE triggers a *reimport* of an existing asset with
a confusing "not a valid Alembic" error.
**Cause:** the CSV had the exact same name as an asset in that folder.
**Fix:** the exporter writes `<name>_LLF.csv` for this reason; keep the suffix.

## mirrored-source {#mirrored-source}

**Symptom:** the character's left/right appears swapped vs. the performer.
**Cause:** selfie-style captures are mirrored; the remap faithfully reproduces whatever MHA
saw. See [conventions.md](conventions.md).
**Fix:** unmirror the video before MHA processing, or accept mirror-space (matches how people
see themselves). If one specific character was *sculpted* with swapped sides, flip the two
names in a duplicate of the definition.
