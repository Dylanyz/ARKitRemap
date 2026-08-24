# Scripts — the DO layer

Idempotent UE-editor Python. Each script prints `PASS`/`FAIL`/`ACTION` lines with the fix for
every failure, so its output is the verification. Playbooks call these by name; this file is
the **single place** that explains how to run them over any bridge.

| Script | Does |
|---|---|
| `verify_setup.py` | ★ Checks a project end-to-end: plugin → assets → (optionally) a character's live wiring → stream → output curves. Run it first whenever anything misbehaves. |
| `setup_live.py` | Wires a level actor's mesh for live MHA driving (anim class, subject, per-instance flags, the transient editor-preview flag). |
| `convert_baked.py` | Batch-converts MHA AnimSequence(s) → ARKit AnimSequence(s) through the definition. |
| `arkit_llf_csv.py` | Live Link Face CSV exporter — the source of the `AAU_ARKitRemap_ExportLLFCSV` asset action. Normally you use the right-click action, not this file. |

## Running a script (transport crib)

The scripts are plain `unreal`-API Python with **no MCP-specific imports** — use whatever
bridge you have:

| Bridge | How |
|---|---|
| **UE Output Log / Cmd** | `py "D:/path/to/ARKitRemap/scripts/verify_setup.py"` |
| **Editor Python console** | `exec(open(r"D:/path/to/script.py").read())` |
| **Epic's UE MCP** (or any MCP with an execute-Python tool) | pass the file's contents, or `exec(open(...).read())`, to the execute-Python tool |
| **Python remote execution** (`remote_execution.py`) | enable *Python Remote Execution* in Project Settings; the client ships with the engine at `Engine/Plugins/Experimental/PythonScriptPlugin/Content/Python/remote_execution.py` — import it, `RemoteExecution().start()`, open a command connection, send `exec(open(...).read())` (field-verified transport) |
| **Headless / CI** | `UnrealEditor-Cmd.exe Project.uproject -run=pythonscript -script="D:/path/to/script.py"` |

**Parameters** are module-level `CONFIG` values at the top of each script, overridable via
environment variables (documented per script) — argv is unreliable across bridges. Either
edit the `CONFIG` block, set the env vars before launching the editor, or set them in-process
first: `import os; os.environ["ARKITREMAP_ACTOR"] = "spider1"`.

## Conventions (for anyone adding a script)

- Idempotent: safe to re-run; check state before changing it.
- Loud: every check prints `PASS:`/`FAIL:` with the fix inline; failures cite a
  [reference/gotchas.md](../reference/gotchas.md) anchor.
- **Never** `time.sleep`-loop inside one editor call — it blocks the game thread and live
  values freeze ([gotcha](../reference/gotchas.md#game-thread-sampling)). Sample across
  separate calls.
- With multiple editors open, print/verify `unreal.Paths.get_project_file_path()` before
  trusting results ([gotcha](../reference/gotchas.md#python-binding-hijack)).
- AnimSequence curves: `unreal.AnimationLibrary` (not `AnimationBlueprintLibrary`); batch
  curve writes inside `controller.open_bracket()`/`close_bracket()`. Morph checks:
  `get_all_morph_target_names()`, not `find_morph_target` (absent in 5.8 Python).
- Git Bash callers: `/Game/...` arguments get mangled into Windows paths by MSYS — prefix the
  command with `MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL="*"`.
