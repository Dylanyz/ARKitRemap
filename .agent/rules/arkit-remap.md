# ARKit Remap Context

Use this rule only for the ARKit remap side project workflow.

## Trigger keywords

Match conversational terms like:
- ARKit remap
- MHA to ARKit
- AM_ArKitRemap
- FaceIt remap
- facial curve remapping
- CTRL_expressions to ARKit

## Required behavior

- Read the skill at `.agent/skills/arkit-remap/SKILL.md` for protocol and workflow context.
- For the full knowledge base, read `dev/knowledge-base.md`.
- For PoseAsset extraction data, start at `dev/mapping-pose-asset/AGENT_INDEX.md`.
- For improvement status and backlog, read `plans/arkit-remap-improvementlog.md`.

## Repository layout

- `release/` — source-of-truth for the user-facing package
- `dev/` — full development workspace (scripts, data, reports, archive)
- `dev/knowledge-base.md` — canonical technical reference
- `dev/mapping-pose-asset/` — PoseAsset extraction workspace
- `plans/` — improvement log and next-steps plans
- `legacy/` — old Blueprint AnimModifier .uasset

Consider these rules if they affect your changes.
