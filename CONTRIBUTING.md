# Contributing to ARKit Remap

Using an AI agent (Claude Code, Cursor, etc.)? No setup needed — point it at this repo;
[CLAUDE.md](CLAUDE.md) routes it to everything, including the maintenance contract for where
changes land.

## Layout

| Path | What |
|---|---|
| `uassets/` | The product: drop-in UE assets + the definition's versioned JSON |
| `playbooks/` | One guide per workflow — by-hand and agent lanes |
| `scripts/` | UE-editor Python (verify / setup / convert) + the transport crib |
| `reference/` | The technical reference: RigMapper, conventions, findings, gotchas, history |
| `dev/` | Contributors' workspace: solver, evidence reports, PoseAsset extraction, plans |

## Ground rules

- **One home per fact.** Add knowledge to the right `reference/` file (dated, with evidence in
  `dev/reports/`), procedures to playbooks, checks to `scripts/verify_setup.py` — and link
  between them instead of restating. Log every change in `reference/README.md`'s Revision Log;
  user-visible changes also go in `CHANGELOG.md`.
- **The purity rule**: the definition contains only what follows from Epic's assets, measured
  data, and math. No hand-tuned numbers — see
  [reference/findings.md](reference/findings.md).
- Write for strangers: no machine-specific paths or agent-stack assumptions in user-facing
  files.

## The most valuable contribution

**Paired takes**: the same performance captured simultaneously as iPhone ARKit CSV (Live Link
Face recording) and mono video processed through MHA. Every pair sharpens the MouthClose
calibration and the validation suite. Open an issue to share one.

## License

MPL-2.0 — by contributing you agree your changes are licensed the same way. See
[LICENSE](LICENSE).
