# Record a live performance to an AnimSequence

**Goal:** a live MHA-driven performance ([setup-live](setup-live.md)) is captured as an
AnimSequence carrying the 52 ARKit morph curves — playable afterwards with no live link.
**Prereqs:** live driving working right now (the character follows your face).

## Steps

1. Open Take Recorder (Window → Cinematics → Take Recorder) → **+ Source → From Actor** →
   pick the character.
   Check: the actor appears as a source with its components listed.

2. Untick every component **except** the target mesh.
   Check: only the ARKit mesh row is ticked.
   If it fails (recording captures the wrong component anyway — known UE 5.8 UI bug):
   [take-recorder-crosswire](../reference/gotchas.md#take-recorder-crosswire) — includes the
   workaround and the reliable offline fallback.

3. Record the performance, then stop.
   Check: the take's subsequence contains an AnimSequence for the mesh whose Curves panel
   shows the 52 ARKit curves.

4. Play it back: drop that AnimSequence on the mesh in a LevelSequence (no live link needed).
   Check: the recorded performance plays.
   If it fails (mesh ignores the sequence while its Anim Class is the live template):
   [sequencer-slot](../reference/gotchas.md#sequencer-slot).
