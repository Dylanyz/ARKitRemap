# Reference — the WHY layer

Facts, internals, and explanations. Procedures live in [playbooks/](../playbooks/), executable
steps in [scripts/](../scripts/). One home per fact: if it's explained here, playbooks link to
it rather than restating it.

| File | Domain |
|---|---|
| [rigmapper.md](rigmapper.md) | UE 5.8 RigMapper system: data model, evaluation semantics, anim node, retargeter ops, batch subsystem, JSON schema, Python API notes |
| [conventions.md](conventions.md) | Measured conventions: the ARKit 52, L/R naming and mirroring, MouthClose |
| [findings.md](findings.md) | How the definition was built: Epic's ground-truth assets, RigLogic harness, basis solve, fit quality, the purity rule |
| [gotchas.md](gotchas.md) | Field-verified failure modes: symptom → cause → fix, with stable anchors |
| [history.md](history.md) | v1/v2 in brief, the v2-numbers ban, lessons that still matter |

Empirical claims link their evidence in [dev/reports/](../dev/reports/). Anything not linked
from here or a playbook is a candidate for pruning.

## Revision Log

| Date | Change | Source |
|------|--------|--------|
| 2026-08-24 | Field-verified all three scripts against MDR_Doomsday via Python remote execution: verify_setup (correctly flagged the transient editor-preview flag and a dead stream), setup_live (full wiring run), convert_baked (real MHA take → 52 plausible ARKit curves). Fixes: 5.8 Python has no `SkeletalMesh.find_morph_target` (use `get_all_morph_target_names`); partial ARKit rigs (masks) must not fail the morph check; capitalized output curve names noted. | MDR_Doomsday live verification session |
| 2026-08-24 | Repo redesign: knowledge-base.md split into this reference/ set (rigmapper, conventions, findings, gotchas, history); K.3.1 procedure moved to playbooks/setup-live.md; checks moved to scripts/verify_setup.py; v2-era material pruned (tag `pre-redesign-v2`). | Repo redesign (dev/plans/repo-redesign-claude-final.md) |
| 2026-08-20 | Field-verified live setup playbook from first production deployment (MDR_Doomsday SpiderMask_BND): plugin default-off, fixed install path, per-instance wiring, ABP CDO defaults, MetaHuman UseLiveLink conflict, transient bUpdateAnimationInEditor as the #1 frozen-mesh cause, curve bisect recipe, game-thread sampling trap, Basic-role subject. Now: playbooks/setup-live.md + gotchas.md. | MDR_Doomsday live deployment |
| 2026-08-14 | V3 empirical findings: offline RigLogic harness, ARKit basis solve (cond 21.8, exact recovery), measured L/R + mirroring conventions, MouthClose calibration (r=0.81), definition fit (R² 0.92, score 0.640), real definition JSON schema, UE 5.8 Python API notes. Now: findings.md, conventions.md, rigmapper.md. | V3 P1–P3 measurement passes |
| 2026-08-12 | UE 5.8 RigMapper system survey (definition data model + JSON, anim node, retargeter ops, editor subsystem, utilities, shipped definitions, OpenRigLogic) — the V3 foundation. Now: rigmapper.md. | UE 5.8 engine investigation |
| 2026-03-11 → 2026-03-13 | v2 era (Python pipeline: PoseAsset extraction, weighted synthesis, coupled solves, mouth calibration, CSV export, apples comparison). Full log and material under tag `pre-redesign-v2`; surviving lessons in history.md. | v2 development |
