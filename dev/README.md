# dev — contributors' workspace

Users never need this folder; the product and its docs live at the repo root
([CLAUDE.md](../CLAUDE.md) routes). This is where the mapping is built, measured, and proven.

| Folder | What |
|---|---|
| [solve/](solve/) | The V3 mapping workspace: RigLogic harness, ARKit basis build, inverse solver, definition fit/score (`solve/scripts/`), plus captured/derived datasets (`solve/data/`). Local pip deps go in gitignored `solve/.pydeps` (`pip install --target dev/solve/.pydeps scipy`). |
| [reports/](reports/) | Dated evidence for every empirical claim in [reference/](../reference/README.md) — basis conditioning, solver validation, convention verdicts, fit and score reports. If a claim cites a report, the report lives here. |
| [pose-asset/](pose-asset/) | PoseAsset extraction workspace (`PA_MetaHuman_ARKit_Mapping` → JSON datasets). Start at its [README](pose-asset/README.md); regeneration order is documented there. |
| [plans/](plans/) | Active plans only ([V3 plan](plans/arkit-remap-v3-plan.md), redesign specs, improvement log). Dead plans get deleted — git history keeps them. |

Ground rules: the hard v2-numbers ban and surviving v2 lessons are in
[reference/history.md](../reference/history.md); the maintenance contract for folding new
learnings into the repo is in [CLAUDE.md](../CLAUDE.md). Pre-redesign material (v2 pipeline,
probes, run logs): `git checkout pre-redesign-v2`.
