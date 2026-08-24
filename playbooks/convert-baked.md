# Convert a baked MHA animation to ARKit

**Goal:** an MHA-exported AnimSequence (from MetaHuman Performance) becomes a new
AnimSequence with the 52 ARKit curves, playable on any ARKit-52 character.
**Prereqs:** [install](../uassets/README.md) done · an MHA AnimSequence (process a face video
through MetaHuman Performance and export with *Export Face* — standard MHA workflow, Epic's
docs cover it).

## Steps

1. Convert through the definition.
   By hand: Content Browser → right-click the MHA AnimSequence(s) → **Convert Selected Using
   RigMapper** → *Definitions* = `RM_MHA_to_ARKit`, *Target Mesh* = your ARKit character's
   skeletal mesh, pick an output suffix → OK.
   Agent: `scripts/convert_baked.py` with `ARKITREMAP_MESH=<mesh asset path>` (+
   `ARKITREMAP_SOURCES` or a Content Browser selection; [transports](../scripts/README.md))
   Check: a new `<name>_ARKit` AnimSequence appears beside the source, with curves like
   `jawOpen`, `eyeBlinkLeft` visible in its Curves panel. ("Invalid curve type: RCT_Vector"
   warnings are benign.)
   If it fails: right-click menu missing →
   [plugin-off](../reference/gotchas.md#plugin-off); output exists but character doesn't
   move → [no-morph-response](../reference/gotchas.md#no-morph-response).

2. Play it on the character (Sequencer animation track on the mesh, or set it as the mesh's
   animation asset).
   Check: the face moves.
   If it fails: playing through a mesh whose Anim Class is a live template →
   [sequencer-slot](../reference/gotchas.md#sequencer-slot).
