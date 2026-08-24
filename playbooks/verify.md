# Verify a project's setup

**Goal:** confirm the ARKitRemap install (and optionally one character's live wiring) is
correct, with a named fix for anything that isn't.
**Prereqs:** none — this is the thing you run first.

## Steps

1. Run the verifier and read its output.
   By hand: there is no by-hand equivalent worth doing — open the UE **Output Log** and run:
   `py "<repo>/scripts/verify_setup.py"`
   Agent: `scripts/verify_setup.py` (set `ARKITREMAP_ACTOR=<actor label>` first to also check
   a character's live wiring; [transports](../scripts/README.md))
   Check: ends with `RESULT: N passed, 0 failed`.
   If it fails: every `FAIL:` line prints its own fix and a
   [gotchas](../reference/gotchas.md) anchor — apply them top to bottom and re-run; earlier
   failures cause later ones.

2. (Manual fallback, if Python is unavailable) Check the two things that break most installs:
   the **RigMapper** plugin is enabled (Edit → Plugins → "RigMapper" → checked → editor was
   restarted), and `RM_MHA_to_ARKit` appears in the Content Browser under
   `Content/ARKitRemap/` and opens when double-clicked.
   Check: both true.
   If it fails: [plugin-off](../reference/gotchas.md#plugin-off) ·
   [install-path](../reference/gotchas.md#install-path).
