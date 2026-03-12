"""ARKit Remap context-menu launcher with smoothing prompt."""

import os
import unreal

TAG = "[ARKit Remap Menu]"

_TITLE = "ARKit Remap Smoothing"

_MESSAGE = (
    "Choose smoothing mode for this run.\n\n"
    "Yes = EMA (recommended)\n"
    "Simple, predictable fixed smoothing.\n"
    "Best default for most MetaHuman Animator to ARKit remaps.\n\n"
    "No = One-Euro\n"
    "Adaptive smoothing. Heavier filtering, harder to predict.\n"
    "Use if EMA leaves too much high-frequency noise.\n\n"
    "Cancel = None\n"
    "No smoothing. Rawest output.\n"
    "Use for QA, validation, or when animation already looks stable.\n\n"
    "Epic / MetaHuman note:\n"
    "These smoothing filters are custom post-processing for this "
    "remapper, not built-in MetaHuman options."
)


def _choose_smoothing_mode():
    result = unreal.EditorDialog.show_message(
        _TITLE,
        _MESSAGE,
        unreal.AppMsgType.YES_NO_CANCEL,
    )
    if result == unreal.AppReturnType.YES:
        return "ema"
    if result == unreal.AppReturnType.NO:
        return "one_euro"
    return "none"


def run():
    mode = _choose_smoothing_mode()

    script_path = os.path.join(
        unreal.Paths.project_dir(),
        "Content",
        "Python",
        "arkit_remap.py",
    )

    if not os.path.isfile(script_path):
        unreal.log_error(f"{TAG} Script not found: {script_path}")
        return

    exec_globals = {
        "__name__": "__main__",
        "__file__": script_path,
        "_ARKIT_REMAP_RUNTIME_OPTIONS": {
            "smoothingMode": mode,
            "invokedFromContextMenu": True,
        },
    }

    unreal.log(f"{TAG} Launching remap with smoothing mode: {mode}")
    with open(script_path, "r") as f:
        exec(compile(f.read(), script_path, "exec"), exec_globals)


if __name__ == "__main__":
    run()
