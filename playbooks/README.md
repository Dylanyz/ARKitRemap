# Playbooks — the HOW layer

One workflow per file, one screen each, written for a human artist first — every step gives
the exact UE click path, then a one-line `Agent:` lane naming the script that does the same
thing (how to run scripts over any bridge: [scripts/README.md](../scripts/README.md)). Steps
end with an observable **Check**; failures link a [gotcha](../reference/gotchas.md) anchor.
No explanations here — that's [reference/](../reference/)'s job.

| Playbook | Workflow |
|---|---|
| [verify.md](verify.md) | "Is this project set up right?" — run first when anything misbehaves |
| [convert-baked.md](convert-baked.md) | MHA AnimSequence → ARKit AnimSequence (most common) |
| [setup-live.md](setup-live.md) | Drive a character's face live from webcam/phone via MHA |
| [record-performance.md](record-performance.md) | Capture a live performance to an AnimSequence |
| [export-csv.md](export-csv.md) | AnimSequence → Live Link Face CSV (Blender/FaceIt, outside UE) |

All of them assume the install in [uassets/README.md](../uassets/README.md) is done
(RigMapper plugin enabled + uassets copied to `Content/ARKitRemap/`).
