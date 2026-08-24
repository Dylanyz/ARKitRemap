# Set up live driving

**Goal:** a character's ARKit face is driven in real time by your face (webcam or Live Link
Face iPhone) through MHA's real-time solve.
**Prereqs:** [install](../uassets/README.md) done incl. the optional live assets · MetaHuman
plugin with the real-time solver (UE 5.6+) · an MHA Live Link subject streaming (Live Link
panel shows it green; it's a Basic-role, curves-only subject — that's normal).

## Steps

1. Wire the mesh to the universal template.
   By hand: select the character **in the level** → Details → find the target skeletal mesh
   component → *Anim Class* = `abp_arkit_remap_universal_C`.
   Agent: `scripts/setup_live.py` with `ARKITREMAP_ACTOR=<label>`
   `ARKITREMAP_SUBJECT=<subject>` ([transports](../scripts/README.md)) — does steps 1–4 in
   one run.
   Check: the component's Anim Class shows the template.
   If it fails: several characters share one BP →
   [per-instance-wiring](../reference/gotchas.md#per-instance-wiring).

2. Point it at your stream: open `abp_arkit_remap_universal` → Class Defaults → set
   *Live Link Subject* to your subject name, *Use Live Link* on. (*Use Head Movement* stays
   off when body mocap owns the head.) For per-character toggles in the Details panel, add
   the `BC_ARKitRemapLive` component to the character BP instead.
   Check: values saved (compile/save the ABP).
   If it fails (via Python): exact property names matter —
   [abp-cdo-defaults](../reference/gotchas.md#abp-cdo-defaults).

3. Enable editor preview: select the mesh component → Details → search "update animation" →
   tick **Update Animation in Editor**. This is transient — it resets every editor restart,
   and without it the mesh sits frozen while everything else works. Re-tick it each session.
   Check: the checkbox is on.
   If it fails / mesh still frozen:
   [frozen-in-editor](../reference/gotchas.md#frozen-in-editor).

4. If the character is a MetaHuman: turn OFF the actor's own *Use Live Link* (actor Details →
   Live Link section) so its face doesn't fight the custom mesh.
   Check: only the intended mesh animates.
   If it fails: [metahuman-conflict](../reference/gotchas.md#metahuman-conflict).

5. Make a face.
   Check: the character's face follows yours.
   If it fails: run [verify.md](verify.md) with `ARKITREMAP_ACTOR` set — it bisects
   stream vs. remap ([stream-bisect](../reference/gotchas.md#stream-bisect)) and names the
   broken link.
