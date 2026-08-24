# ARKit Remap — agent router

MHA-to-ARKit facial curve remapping for UE **5.8**: MetaHuman Animator `CTRL_expressions`
curves → the 52 ARKit blendshapes, baked / live / CSV. This file routes; it holds no
knowledge of its own. One home per fact — never restate, link.

## Route by task

| You're here to… | Go to |
|---|---|
| Install / any workflow (convert, live, record, CSV) | [playbooks/](playbooks/) — install prereqs in [uassets/README.md](uassets/README.md) |
| Debug "it doesn't work" | run [scripts/verify_setup.py](playbooks/verify.md) first; then [reference/gotchas.md](reference/gotchas.md) |
| Run a script over your MCP/bridge | [scripts/README.md](scripts/README.md) (the transport crib) |
| Understand internals (RigMapper, conventions, how the mapping was solved) | [reference/](reference/README.md) |
| Improve the mapping / contribute | [dev/](dev/README.md) + active plans in [dev/plans/](dev/plans/) |

Users never need `dev/`. Hard rule: **v2's mapping numbers were AI-guessed and must NOT feed
the definition** — see [reference/history.md](reference/history.md).

## Maintenance contract (every session that learns something)

A learning lands in **exactly one** primary home:

| Learning | Home |
|---|---|
| A check could have caught it | `scripts/verify_setup.py` (+ a gotcha entry it cites) |
| A procedure step changed | the playbook step |
| A new failure mode | `reference/gotchas.md` (symptom → cause → fix, stable anchor) |
| A new fact / explanation / measurement | the matching `reference/` file, dated, evidence linked in `dev/reports/` |
| Script behavior wrong | the script itself |

Then always: one Revision Log line in [reference/README.md](reference/README.md);
`CHANGELOG.md` if user-visible. Never duplicate content across layers — link. Playbooks stay
one screen, no explanations, "By hand" + "Agent" lanes both present.

This repo is public-facing: write for strangers, no machine-specific paths or MCP-stack
assumptions in user-facing files.
