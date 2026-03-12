# Contributing to ARKit Remap

Welcome! This project benefits from both human contributors and AI agent workflows. This guide covers the repo layout, how to get started, and how to work effectively — whether you're coding by hand or using an AI assistant.

---

## Repository Structure

```
ARKitRemap/
├── README.md                 Main user-facing documentation
├── CONTRIBUTING.md           This file
├── CHANGELOG.md              Version history
├── LICENSE                   MIT license
│
├── release/                  Source-of-truth for the user-facing package
│   ├── arkit_remap.py          Main remap script
│   ├── arkit_remap_payload.json Mapping data + calibration config
│   ├── init_unreal.py          Context menu registration
│   ├── arkit_remap_menu.py     Menu launcher with smoothing prompt
│   ├── temporal_smoothing.py   Smoothing filters
│   └── README.md               Install docs (included in release zip)
│
├── dev/                      Full development workspace
│   ├── README.md               Dev entry point and folder guide
│   ├── knowledge-base.md       Canonical technical reference (800+ lines)
│   ├── MH_Arkit_Mapping.txt    Community-sourced 1:1 mapping (reference)
│   ├── scripts/                Active development and calibration scripts
│   ├── mapping-pose-asset/     PoseAsset extraction workspace
│   │   ├── AGENT_INDEX.md        Navigation index for this workspace
│   │   ├── data/                 Extracted mapping data (JSON)
│   │   ├── reports/              Extraction and validation reports
│   │   └── scripts/              Extraction and verification scripts
│   ├── reports/                QA reports and run logs
│   │   └── run-logs/             Per-run output logs
│   └── archive/                Deprecated probes and experiments
│
├── plans/                    Development plans and tracking
│   ├── arkit-remap-improvementlog.md
│   ├── arkit-remap-next-steps_f8a2c301.plan.md
│   └── pose_asset_extraction_methods_research.md
│
├── AGENTS.md                 Universal agent instructions (works with all AI tools)
├── GEMINI.md                 Antigravity-native entry point
├── .cursor/                  Cursor IDE agent integration
│   ├── rules/
│   │   └── arkit-remap.mdc      Trigger rules for ARKit remap context
│   └── skills/
│       └── arkit-remap/
│           └── SKILL.md          Agent skill with full pipeline context
├── .agent/                   Antigravity IDE agent integration
│   ├── rules/
│   │   └── arkit-remap.md       Same rules, Antigravity format
│   └── skills/
│       └── arkit-remap/
│           └── SKILL.md          Same skill, Antigravity discovery path
│
├── legacy/                   Legacy Blueprint AnimModifier (.uasset)
│   └── AM_ArKitRemap.uasset
│
└── build_release.py          Script to build the release zip
```

### Key Files to Know

| If you want to... | Start here |
|---|---|
| Understand the math and pipeline | [`dev/knowledge-base.md`](dev/knowledge-base.md) |
| See what's been done and what's next | [`plans/arkit-remap-improvementlog.md`](plans/arkit-remap-improvementlog.md) |
| Read the main remap code | [`release/arkit_remap.py`](release/arkit_remap.py) |
| Understand the payload format | [`release/arkit_remap_payload.json`](release/arkit_remap_payload.json) |
| Explore PoseAsset extraction data | [`dev/mapping-pose-asset/AGENT_INDEX.md`](dev/mapping-pose-asset/AGENT_INDEX.md) |
| See calibration and validation scripts | [`dev/scripts/`](dev/scripts/) |
| Read deprecated experiments | [`dev/archive/`](dev/archive/) |

---

## Getting Started

### Prerequisites

- **Unreal Engine 5.7+** with the Python Editor Script Plugin enabled
- A MetaHuman project with baked MHA AnimSequences
- Git

### Clone and Explore

```bash
git clone https://github.com/Dylanyz/ARKitRemap.git
cd ARKitRemap
```

The `release/` folder contains the user-facing package. The `dev/` folder contains the full development workspace with all research, scripts, and data.

### Running the Tool in Your UE Project

Copy the `release/` contents into your project's `Content/Python/` folder. See the [main README](README.md) for usage instructions.

### Running Dev Scripts

Most scripts in `dev/scripts/` are designed to run inside UE's Python environment. To run them:

1. Open your UE project
2. In the Output Log: `py exec(open(r"path\to\script.py").read())`

Some scripts (like `roundtrip_validation.py` and `coupled_solve.py`) are pure Python and can run outside UE for offline testing.

---

## Working with AI Agents

This repo is set up for productive AI-assisted development with multiple tools. Agent instructions and skills are provided for both **Cursor** and **Google Antigravity**, plus a universal `AGENTS.md` that works with any tool supporting the standard (Codex, Copilot, Windsurf, Jules, Aider, etc.).

### Quick setup by tool

| Tool | What happens when you open the repo |
|------|------|
| **Cursor** | `.cursor/rules/` and `.cursor/skills/` are auto-detected. Mentioning "ARKit remap" triggers the skill. |
| **Antigravity** | `AGENTS.md` is loaded automatically. `.agent/skills/` and `.agent/rules/` are discovered. `GEMINI.md` also available. |
| **Codex / Copilot / Windsurf / others** | `AGENTS.md` at the root is auto-detected. Full project context in one file. |

No manual configuration needed for any of these — just open the repo.

### What the agent gets

All agent configurations provide:

- Complete pipeline overview (forward and reverse)
- Artifact locations for every script, data file, and report
- How to run the remap tool
- Key technical points (normalization, coupled solve, mouth-pair model)
- Required sync protocols (what to update when code changes)
- Output organization rules

### Agent workflow tips

- **Start a new task** by mentioning "ARKit remap" — triggers automatic context loading
- **For research tasks**, point the agent to `dev/knowledge-base.md` for full technical context
- **For code changes**, the skill requires agents to update the knowledge base, SKILL.md, and AGENT_INDEX when relevant
- **For calibration work**, the `dev/scripts/` folder has specialized calibration and validation tools
- **For PoseAsset work**, start at `dev/mapping-pose-asset/AGENT_INDEX.md`

### Adding new rules or skills

For Cursor:
```
.cursor/rules/your-rule.mdc
.cursor/skills/your-skill/SKILL.md
```

For Antigravity:
```
.agent/rules/your-rule.md
.agent/skills/your-skill/SKILL.md
```

For universal compatibility, add instructions to `AGENTS.md`.

---

## Development Workflow

### Making Changes to the Remap Script

1. Edit `release/arkit_remap.py` (this is the source of truth)
2. Test in UE by copying to `Content/Python/` and running
3. Update `dev/knowledge-base.md` Section E.6 with behavior changes
4. Add a Revision Log entry in the knowledge base
5. Update `CHANGELOG.md`

### Release Process

1. Make sure `release/` contains the current versions of all package files
2. Run `python build_release.py` to generate a zip
3. Commit and push
4. Create a GitHub Release and attach the zip

### Documentation Sync Protocol

When making changes, keep these in sync:

| What changed | Update these |
|---|---|
| `arkit_remap.py` behavior | `dev/knowledge-base.md` (Section E.6), SKILL.md, CHANGELOG.md |
| Payload format | `dev/knowledge-base.md`, `dev/mapping-pose-asset/AGENT_INDEX.md` |
| New scripts or data | `dev/README.md`, `dev/mapping-pose-asset/AGENT_INDEX.md` if relevant |
| Mapping extraction | `dev/mapping-pose-asset/AGENT_INDEX.md`, `dev/knowledge-base.md` (Section D/J) |

### Archiving

If a script or report is no longer part of the active workflow, move it to `dev/archive/` rather than deleting it. This preserves the research trail.

---

## Areas Where Help Is Wanted

Check the [improvement log](plans/arkit-remap-improvementlog.md) for the current backlog. Key open items:

- **Eye-look quality** — are monocular-captured eye curves meaningful?
- **Mesh-level curves** — do MHA bakes contain `head_lod0_mesh__*` curves?
- **Curve-family classification** — annotating contributors as direct/signed/phased for better QA
- **Full 52-target simultaneous solve** — only needed if current grouped solves prove insufficient
- **Visual QA on more performances** — the math looks good but more eyeball testing is always valuable

---

## Code of Conduct

Be kind, be constructive, share what you learn. This project started as a side project to solve a real problem — contributions that improve quality for everyone are welcome.
