# ARKitRemap — Ground-Zero Design (Claude's cut)

*2026-08-20 — design document only; nothing executed. Supersedes `repo-redesign-ground-zero.md`
where they differ; agrees with it everywhere not mentioned.*

## The goal, restated as tests

The repo is done right when all five pass:

1. **T1 — Cold agent, any MCP**: an agent that has never seen this repo, using Epic MCP,
   runreal, raw remote-exec, or `-run=pythonscript`, can execute every workflow end-to-end
   from CLAUDE.md alone.
2. **T2 — Cold human**: an artist with no agent can follow every workflow by hand from the
   playbooks alone.
3. **T3 — No stale info**: every fact lives in exactly one file; a grep for any old path
   returns nothing.
4. **T4 — Five-minute updates**: a field-testing session folds a learning into the repo in one
   obvious place in minutes, guided by a decision table that lives where agents always look.
5. **T5 — Self-verifying**: "is my project set up right?" is answered by a script, not a
   checklist.

## Structure

```
ARKitRemap/
├── README.md            Humans + shop window. What it is, demo, install-in-60s, workflow
│                        index (links to playbooks), pointer-skill recipe, limitations.
│                        Absorbs USER-GUIDE's concepts; USER-GUIDE.md is deleted.
├── CLAUDE.md            Agent router + THE MAINTENANCE CONTRACT (see below). ~50 lines,
│                        no knowledge of its own.
├── CHANGELOG.md / LICENSE / CONTRIBUTING.md / .gitignore
│
├── uassets/             THE PRODUCT. Flat.
│   ├── RM_MHA_to_ARKit.uasset          the definition
│   ├── RM_MHA_to_ARKit.json            versioned source of truth (LoadFromJson rebuilds it)
│   ├── abp_arkit_remap_universal.uasset  live template AnimBP (any skeleton)
│   ├── BC_ARKitRemapLive.uasset          details-panel toggles component
│   ├── AAU_ARKitRemap_ExportLLFCSV.uasset  CSV right-click action
│   └── README.md        one screen: file table, install = copy → Content/ARKitRemap/
│                        (exact name), RigMapper plugin requirement first.
│
├── playbooks/           HOW. One workflow per file, one screen, human-first prose with an
│   │                    agent lane (format below).
│   ├── README.md        the playbook format spec (one paragraph) + workflow index
│   ├── setup-live.md    wire a mesh for live MHA driving
│   ├── convert-baked.md MHA AnimSequence → ARKit AnimSequence
│   ├── export-csv.md    AnimSequence → Live Link Face CSV (Blender/FaceIt)
│   ├── record-performance.md  Take Recorder capture → AnimSequence
│   └── verify.md        run verify_setup.py, read its output
│
├── scripts/             DO. Idempotent UE-editor Python.
│   ├── README.md        ★ the TRANSPORT CRIB — how to run any script here via Epic MCP /
│   │                    runreal / remote exec / -run=pythonscript. The single
│   │                    MCP-agnosticism point (T1). Plus script conventions (args, exit
│   │                    behavior, game-thread rules).
│   ├── verify_setup.py  ★ keystone: checks plugin → assets → wiring → editor-preview flag →
│   │                    live stream → output curves, prints PASS/FAIL per check WITH the fix
│   │                    (each fix line cites reference/gotchas.md#anchor)
│   ├── setup_live.py    live-wiring mechanics (actor label, component, subject) incl. the
│   │                    transient editor-preview flag
│   ├── convert_baked.py wraps RigMapperEditorSubsystem.convert_anim_sequence_new
│   └── arkit_llf_csv.py LLF CSV exporter (moves from v3/ue-python)
│
├── reference/           WHY. Facts and explanations, split by domain.
│   ├── README.md        index + Revision Log (moves from KB head)
│   ├── rigmapper.md     UE 5.8 RigMapper system survey (KB §K minus K.3.1 procedure)
│   ├── conventions.md   measured conventions: mirroring, Apple quirks, MouthClose (§L.3–L.4)
│   ├── findings.md      V3 empirical findings: RigLogic harness, basis solve, fit quality
│   │                    (§L.1–L.2, L.5+), PA mapping detail V3 still uses. Every empirical
│   │                    claim links its evidence file in dev/reports/.
│   ├── gotchas.md       failure modes with stable anchors; each entry: symptom → cause →
│   │                    fix → which playbook step / verify check covers it
│   └── history.md       v1/v2 knowledge that still informs decisions (§A–J compressed);
│                        everything else lives in git history only
│
└── dev/                 CONTRIBUTORS ONLY (CLAUDE.md routes users away).
    ├── README.md        workspace map
    ├── solve/           V3 mapping workspace (current v3/scripts + v3/data)
    ├── reports/         dated evidence cited by reference/ (current v3/reports + keepers)
    ├── pose-asset/      PA extraction workspace (current dev/mapping-pose-asset;
    │                    AGENT_INDEX.md becomes README.md; MH_Arkit_Mapping.txt moves here)
    └── plans/           active plans only
```

Deleted (git history + `pre-redesign-v2` tag keep them): `legacy/`, `dev/archive/`,
`dev/scripts/` (v2 + apples validation), `dev/reports/run-logs/` and v2-era reports not cited
by reference/, `v3/uassets/abp_arkit_remap_live.uasset` (superseded), stale plans
(`arkit-remap-next-steps_*.plan.md`, `pose_asset_extraction_methods_research.md`).

## The five deliberate changes vs. the previous plan

**C1 — The maintenance contract lives in CLAUDE.md, not in a plan.** T4 is the whole game for
the coming testing months, and agents read CLAUDE.md every session — a protocol written in a
plan file dies with the plan. CLAUDE.md carries this table verbatim:

> **When a session teaches you something, it lands in exactly ONE primary home:**
> | Learning | Home |
> |---|---|
> | A check that could have caught it | `scripts/verify_setup.py` (+ gotcha anchor) |
> | A procedure step changed | the playbook step |
> | A new fact / explanation / failure cause | `reference/` (dated) — gotchas.md if it's a failure mode |
> | Script behavior wrong | the script |
>
> Then: one Revision Log line in `reference/README.md`; CHANGELOG if user-visible. Never
> duplicate content across layers — link.

**C2 — Scripts before playbooks, and a feasibility spike before structure lock.** The previous
plan writes playbooks (phase 4) before scripts (phase 5). If `setup_live.py` can't reliably
automate K.3.1's landmines (transient editor-preview flag, per-instance wiring, game-thread
traps), the playbooks reference fiction. Order flips: prove `verify_setup.py` + `setup_live.py`
against MDR_Doomsday first; playbooks then document what demonstrably works. Any step that
proves unscriptable is marked **MANUAL** in its playbook with a gotcha link — honest beats
aspirational.

**C3 — Transport crib lives in `scripts/README.md`.** "How to run a script" is a property of
the scripts, not of the playbooks. Playbooks say `Run scripts/foo.py (see scripts/README.md)`
and stay transport-free. One file to update when a new MCP appears (T1).

**C4 — Playbooks are human-first with an agent lane.** T2 means an artist reads the playbook
as a guide, not as agent config. Format per step:

```markdown
1. <What you're doing and why, one sentence.>
   <Exact UE click path.>
   Agent: `scripts/foo.py --args`
   Check: <observable result>. Failing? → reference/gotchas.md#anchor
```

The prose line IS the step; the agent lane is one line. This is what lets USER-GUIDE.md
dissolve without losing the human path (concepts → README, workflows → playbooks,
limitations → README).

**C5 — Evidence chain.** Every empirical claim in `reference/` links the dev/reports file
that proves it; every kept report is cited by at least one claim. Anything in dev/reports
cited by nothing gets deleted in the prune. This makes "why do we believe this?" answerable
and makes future pruning mechanical.

Plus one naming call: **`uassets/`**, not `assets/` — it says exactly what's inside and can't
be confused with images/demo media. No version in the name (P2 stands: a future v4 replaces
files in place; versions live in CHANGELOG + the JSON).

## Execution phases (revised order)

0. **Spike (editor open, MDR_Doomsday):** draft `verify_setup.py` + `setup_live.py` against
   the known-good live setup. Verify must pass there and fail correctly when the
   editor-preview flag is toggled off. Outcome decides which setup-live steps are scripted
   vs MANUAL. *Nothing restructured yet; scripts drafted in scratch.*
1. **Tag + prune:** tag `pre-redesign-v2`; delete everything marked deleted, minus any
   dev/reports file reference/ will cite (final keep-list decided during phase 3's KB read).
   One commit.
2. **Move + rename:** `git mv` per the migration map (same as previous plan, with `uassets/`
   and the C3 crib location). Pure renames, one commit.
3. **Split the KB:** knowledge-base.md → the five reference files; K.3.1 procedure →
   setup-live playbook skeleton; explanations → gotchas.md; Revision Log → reference/README.
   One sitting. Build the C5 evidence links here; finalize the reports keep-list.
4. **Land the scripts** from phase 0 into `scripts/` + write `scripts/README.md` (transport
   crib) + `convert_baked.py`.
5. **Write playbooks + README + CLAUDE.md:** five playbooks against the now-real scripts;
   README absorbs USER-GUIDE concepts + pointer-skill recipe; CLAUDE.md = router +
   maintenance contract; delete docs/USER-GUIDE.md.
6. **Cross-link audit:** grep every surviving file (and Dylan's machine-level skill/memory)
   for `dev/knowledge-base`, `v3/`, `release/`, `docs/USER-GUIDE`, `legacy/`; fix. CHANGELOG
   entry. Update the arkit-remap pointer skill on Dylan's machine.

Phase 0 is one editor session. 1–2 are minutes. 3 is the one judgment-heavy sitting. 4–6 one
more session. Total ≈ 2–3 sessions, with the risk (scriptability) retired first instead of
last.

## Open decisions for Dylan

- Confirm the aggressive delete scope (same as previous plan; tag makes it one checkout away).
- Confirm `uassets/` over `assets/`.
- Green-light phase 0 spike as the starting point (needs MDR_Doomsday open in the editor).
