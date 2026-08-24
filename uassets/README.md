# uassets — the product

Drop-in UE 5.8 assets. **Install: enable the RigMapper plugin (Edit → Plugins → "RigMapper" →
restart — without it these assets silently fail to load), then copy the .uasset files into
your project at `Content/ARKitRemap/` — exact folder name; the assets reference each other at
`/Game/ARKitRemap/...`.** Copy with the editor closed, or rescan afterwards. Verify with
[playbooks/verify.md](../playbooks/verify.md).

| File | What | Needed for |
|---|---|---|
| `RM_MHA_to_ARKit.uasset` | The remap itself — a RigMapper Definition, 164 MHA curves in → 52 ARKit curves out | **everything** |
| `RM_MHA_to_ARKit.json` | The same definition as versioned, human-diffable JSON — the source of truth. Create a RigMapper Definition asset → right-click → *Load From Json* to rebuild the uasset anywhere | provenance / rebuilds |
| `abp_arkit_remap_universal.uasset` | Live-driving template AnimBP (Live Link Pose → Rig Mapper → Slot), a **Template** AnimBP with no skeleton binding — works on any character. Toggles: `UseLiveLink`, `LiveLinkSubject`, `UseHeadMovement` (head rotation distributed down the neck chain; rigs without `neck_01/neck_02/head` bones skip it) | [live driving](../playbooks/setup-live.md) |
| `BC_ARKitRemapLive.uasset` | Actor component exposing the three toggles on the character's Details panel (MetaHuman-style), per placed instance | live driving (optional convenience) |
| `AAU_ARKitRemap_ExportLLFCSV.uasset` | Asset Action: right-click AnimSequence → *Export Live Link Face CSV*. Source: [scripts/arkit_llf_csv.py](../scripts/arkit_llf_csv.py) | [CSV export](../playbooks/export-csv.md) |

No other dependencies. Optional: stamp the definition onto a character's skeletal mesh
(Details → Asset User Data → add *RigMapper Definition User Data* → add `RM_MHA_to_ARKit`) and
every RigMapper tool auto-discovers it — set your team's characters up once.
