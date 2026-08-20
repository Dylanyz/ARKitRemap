# ARKitRemap Repo Redesign — Ground Zero

*2026-08-20 — design document only; nothing here is executed yet.*

## What this repo must be (the criteria)

1. **A repository of knowledge + tools** — the single home for everything ARKitRemap.
2. **Agent-executable** — any agent, driving UE through *any* MCP (Epic's, runreal, raw remote
   exec, headless), can perform every workflow end-to-end.
3. **Human-teachable** — every workflow has a guide a person can follow by hand.
4. **Zero stale info, zero bloat** — no duplicated knowledge, no dead files in daily view.
5. **Cheap to update** — during the coming weeks/months of field testing, an agent folds a
   learning into the repo in minutes, and it's obvious where it goes.

## Design principles

**P1 — One home per fact.** Every piece of information lives in exactly one file; everything
else links to it. Duplication is the root of staleness.

**P2 — Organize by audience, not by history.** "v2/v3/dev-era" folders force every visitor to
know the project's past. Instead: what a *user* needs at top level, what a *contributor* needs
in one clearly-marked room, history in git only.

**P3 — Scripts over prose.** Docs rot silently; code fails loudly. Any step that *can* be a
script *is* a script, and scripts verify their own results. Prose is reserved for what scripts
can't do (UI-only steps) and for explanations.

**P4 — Three layers, one job each:**

| Layer | Job | Rots when… | Defense |
|---|---|---|---|
| `playbooks/` | HOW — steps | procedures change | steps are mostly script calls (P3) |
| `scripts/` | DO — executable steps | UE API changes | fails loudly at run time, gets fixed |
| `reference/` | WHY — facts, internals | rarely (facts don't expire fast) | revision log, dated claims |

**P5 — The repo carries content; triggering is the user's own layer.** No `.claude/` in the
repo. Agents entering the repo read `CLAUDE.md` (the router). Users who want name-triggering
from other projects add a personal pointer skill on their machine (README shows how). Learned
the hard way: a skill inside the repo never fires where the work happens.

**P6 — MCP-agnostic by construction.** Scripts are plain `unreal`-API Python with no
MCP-specific imports. Playbooks name the *goal* of each step plus the script; the agent uses
whatever bridge it has. A per-transport crib (how to run a script via Epic MCP / runreal /
remote exec / `-run=pythonscript`) lives in ONE place: `playbooks/README.md`.

## Target structure

```
ARKitRemap/
├── README.md                  Humans + shop window: what it is, demos, install-in-60s,
│                              "point your agent at this repo", optional pointer-skill recipe.
├── CLAUDE.md                  Agents: pure router (~40 lines). Task → playbook. Question →
│                              reference. Contributing → dev/. NO knowledge of its own.
├── CHANGELOG.md               User-visible changes only.
├── LICENSE / CONTRIBUTING.md / .gitignore
│
├── assets/                    THE PRODUCT. Flat, minimal:
│   ├── RM_MHA_to_ARKit.uasset         the definition
│   ├── RM_MHA_to_ARKit.json           same definition, versioned/human-diffable (source of truth
│   │                                  for the asset — LoadFromJson rebuilds it anywhere)
│   ├── abp_arkit_remap_universal.uasset   live template AnimBP (any skeleton)
│   ├── BC_ARKitRemapLive.uasset           details-panel toggles component
│   ├── AAU_ARKitRemap_ExportLLFCSV.uasset CSV right-click action
│   └── README.md                          one screen: what each file is, install = copy to
│                                          Content/ARKitRemap/ (exact name), plugin requirement
│
├── playbooks/                 HOW. One file per workflow, one screen each:
│   ├── README.md              format spec + the per-transport "how to run a script" crib
│   ├── setup-live.md          wire a mesh for live MHA driving
│   ├── convert-baked.md       MHA AnimSequence → ARKit AnimSequence
│   ├── export-csv.md          ARKit/MHA AnimSequence → Live Link Face CSV (Blender/FaceIt)
│   ├── record-performance.md  capture a live performance to an AnimSequence
│   └── verify.md              "is this project set up right?" → run verify_setup.py, read output
│
├── scripts/                   DO. Idempotent UE-editor Python (+ the CSV lib):
│   ├── verify_setup.py        ★ keystone: checks plugin/assets/wiring/stream/curves end-to-end,
│   │                          prints pass-fail per check with the fix for each failure
│   ├── setup_live.py          performs setup-live mechanics (params: actor label, component,
│   │                          subject) incl. the transient editor-preview flag
│   ├── convert_baked.py       wraps RigMapperEditorSubsystem.convert_anim_sequence_new
│   └── arkit_llf_csv.py       LLF CSV exporter (already exists; moves here)
│
├── reference/                 WHY. The knowledge base, split by domain (grep-able, no 1000-line
│   │                          monolith):
│   ├── README.md              index of the files below + Revision Log (moves from KB head)
│   ├── rigmapper.md           UE 5.8 RigMapper system survey (KB §K minus K.3.1 procedure)
│   ├── conventions.md         measured conventions: mirroring, Apple naming quirks, MouthClose
│   │                          (KB §L.3–L.4)
│   ├── findings.md            V3 empirical findings: RigLogic harness, basis solve, fit quality
│   │                          (KB §L.1–L.2, L.5+)
│   ├── gotchas.md             field-verified failure modes with explanations (the WHY half of
│   │                          K.3.1; each entry linked from the playbook step that avoids it)
│   └── history.md             v1/v2 pipeline knowledge worth keeping (KB §A–J compressed to
│                              what still informs decisions; the rest → git history)
│
└── dev/                       CONTRIBUTORS ONLY. Users never enter; CLAUDE.md says so.
    ├── README.md              map of the workspace
    ├── solve/                 V3 mapping workspace (current v3/scripts + v3/data): RigLogic
    │                          harness, basis build, inverse solver, fit/score. .pydeps stays
    │                          gitignored here.
    ├── reports/               dated evidence for claims in reference/ (current v3/reports +
    │                          the few dev/reports worth keeping)
    ├── pose-asset/            PA extraction workspace (current dev/mapping-pose-asset)
    └── plans/                 active plans only (this file, v3 plan while alive)
```

Gone entirely (git history keeps them; nothing in daily view):

- `legacy/` — v2 Python package + v1 AnimModifier. Tag the current commit `pre-redesign-v2`
  first so it's one checkout away.
- `dev/archive/` — 43 probe scripts/JSONs from v2 calibration, all superseded by V3's solved
  mapping.
- `dev/reports/run-logs/` + v2-era one-off reports — evidence for a pipeline that no longer
  ships.
- `v3/uassets/abp_arkit_remap_live.uasset` — superseded by the universal template (its README
  already says "kept for reference only").
- Stale plans (`arkit-remap-next-steps_*.plan.md`, `pose_asset_extraction_methods_research.md`
  if absorbed into reference/).

## The playbook format (the anti-drift contract)

Every playbook is one screen, fixed shape:

```markdown
# <Workflow name>
Goal: <one sentence>   Prereqs: <links, e.g. assets/README install>

## Steps
1. <Action>
   - By agent: `scripts/foo.py --args` (transport crib: playbooks/README.md)
   - By hand: <exact UE click path>
   - Verify: <observable result>
   - If it fails: <link to reference/gotchas.md#anchor>
```

Rules: **no explanations in playbooks** (link them), **no code blocks longer than one call**
(that's a script), **"By hand" and "By agent" always both present** — this is how the repo
teaches Dylan (and any artist) while remaining automatable, and it's what replaces the
USER-GUIDE/playbook split: `docs/USER-GUIDE.md` dissolves into README (concepts, §1–6) +
playbooks (workflows, §7+) + reference (limitations/roadmap).

## The maintenance protocol (testing weeks)

Standing rule for every session that touches ARKitRemap — a learning lands in **exactly one**
of:

1. a **script fix** (preferred — self-verifying),
2. a **playbook step** (procedure changed),
3. a **reference entry** (new fact/explanation; dated),

plus a Revision Log line in `reference/README.md`, plus CHANGELOG if user-visible. If unsure
where it goes: gotcha *explanations* → reference/gotchas.md; the *avoidance step* → the
playbook; the *check* → verify_setup.py. Ideally all three, each holding its own piece.

**Consolidation pass** at the end of the testing period (or monthly): one agent session that
re-sorts anything that landed in the wrong layer and prunes anything superseded. Cheap when the
structure exists; this document is the spec for "correct."

## Migration map (current → target)

| Current | Target |
|---|---|
| `v3/uassets/{RM,abp_universal,BC,AAU}.uasset` + `v3/RM_MHA_to_ARKit.json` | `assets/` |
| `v3/uassets/README.md` | `assets/README.md` (rewritten to spec) |
| `v3/uassets/abp_arkit_remap_live.uasset` | **delete** (superseded) |
| `v3/ue-python/arkit_llf_csv.py` | `scripts/arkit_llf_csv.py` |
| *(new)* | `scripts/verify_setup.py`, `scripts/setup_live.py`, `scripts/convert_baked.py` |
| `docs/USER-GUIDE.md` | dissolved → README (concepts) + playbooks + reference; file deleted |
| `dev/knowledge-base.md` §K (minus K.3.1 procedure) | `reference/rigmapper.md` |
| §K.3.1 | split: procedure → `playbooks/setup-live.md` + `verify.md`; explanations → `reference/gotchas.md`; checks → `verify_setup.py` |
| §L.3–L.4 | `reference/conventions.md` |
| §L.1–L.2, L.5+ | `reference/findings.md` |
| §A–J (v2/PA/forward-pipeline analysis) | compressed → `reference/history.md`; PA mapping detail that V3 still uses → `reference/findings.md` |
| KB Revision Log | `reference/README.md` |
| `v3/scripts/`, `v3/data/` | `dev/solve/` |
| `v3/reports/` | `dev/reports/` |
| `dev/mapping-pose-asset/` | `dev/pose-asset/` (AGENT_INDEX.md becomes its README) |
| `dev/MH_Arkit_Mapping.txt` | `dev/pose-asset/` (data it belongs to) |
| `dev/reports/` (v2-era) + `run-logs/` | **delete**, except any file cited by reference/ |
| `dev/archive/` | **delete** |
| `dev/scripts/` (v2 + apples-comparison) | **delete** (roundtrip/coupled-solve validation is v2-only); `forward_remap_to_mh.py`/apples scripts → delete, methodology already captured in findings |
| `legacy/` | **delete** (after tagging `pre-redesign-v2`) |
| `plans/arkit-remap-v3-plan.md`, this file, `arkit-remap-improvementlog.md` | `dev/plans/` |
| `plans/arkit-remap-next-steps_*.plan.md`, `pose_asset_extraction_methods_research.md` | **delete** (stale / absorbed) |
| `CLAUDE.md` | rewritten as pure router (current one still references the moved `release/` dir — already stale, proving the point) |
| `README.md` | keep structure; update paths, add pointer-skill recipe, absorb USER-GUIDE concepts |

## Execution phases

1. **Tag + prune** — tag `pre-redesign-v2`; delete everything marked delete. *(One commit,
   biggest single de-bloat.)*
2. **Move + rename** — create the new tree, `git mv` everything per the map. No content edits
   yet, so the diff is pure renames. *(One commit.)*
3. **Split the KB** — carve knowledge-base.md into the four reference files + extract playbook
   procedure. The only phase requiring judgment; do it in one sitting so nothing dangles.
4. **Write the router + assets README + playbooks** — CLAUDE.md, README updates,
   five playbooks (setup-live and verify first — they're the tested ones).
5. **Write the scripts** — `verify_setup.py` (keystone), `setup_live.py`, `convert_baked.py`.
   Test against MDR_Doomsday's working setup: verify must pass there, and fail correctly when
   e.g. the editor-preview flag is off.
6. **Cross-link audit** — grep for old paths (`dev/knowledge-base`, `v3/uassets`, `release/`,
   `docs/USER-GUIDE`) in every surviving file + Dylan's machine skill; fix. CHANGELOG entry.

Phases 1–2 are mechanical (minutes). 3–4 are the real work (one focused session). 5 is a
session with the editor open. Total: ~2 sessions.

## Open decisions (Dylan)

- **Delete scope**: the map above deletes aggressively (legacy/, archive/, v2 reports,
  run-logs). Confirm, or name keepers.
- **KB split vs monolith**: this plan splits reference/ into 5 domain files for grep-ability
  and smaller diffs. If you prefer the single knowledge-base.md feel, the same plan works with
  one `reference/knowledge-base.md` — everything else unchanged.
- **`assets/` vs keeping `v3/` name**: "v3" is history-speak (P2); `assets/` assumes v4 would
  replace files in place rather than get a sibling folder. Confirm.
- **Timing**: recommend executing before serious testing begins, so learnings land in the new
  structure from day one.
