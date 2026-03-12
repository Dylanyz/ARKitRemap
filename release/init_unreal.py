"""ARKit Remap - Editor Startup / Context Menu Registration

Registers a "Run ARKit Remap" entry in the Content Browser right-click
menu. In current UE behavior it appears in the main context menu rather
than under the "Asset Actions" subsection. The launcher prompts for
smoothing mode before executing the remap.

Run once per editor session (e.g. via startup scripts or remote execution).
"""

import unreal
import os

TAG = "[ARKit Remap Init]"


def register_context_menu():
    tool_menus = unreal.ToolMenus.get()
    if tool_menus is None:
        unreal.log_warning(f"{TAG} ToolMenus.get() returned None.")
        return False

    menu = tool_menus.find_menu("ContentBrowser.AssetContextMenu")
    if menu is None:
        unreal.log_warning(f"{TAG} ContentBrowser.AssetContextMenu not found.")
        return False

    entry = unreal.ToolMenuEntry(
        name="ARKitRemap_Run",
        type=unreal.MultiBlockType.MENU_ENTRY,
    )
    entry.set_label("Run ARKit Remap")
    entry.set_tool_tip(
        "Run weighted ARKit remap on selected AnimSequence(s) "
        "with a smoothing mode prompt"
    )

    remap_cmd = (
        "import unreal, os; "
        "_p = os.path.join(unreal.Paths.project_dir(), "
        "'Content', 'Python', 'arkit_remap_menu.py'); "
        "exec(open(_p).read()) if os.path.isfile(_p) else "
        "unreal.log_error('[ARKit Remap] Script not found: ' + _p)"
    )
    entry.set_string_command(
        type=unreal.ToolMenuStringCommandType.PYTHON,
        custom_type="",
        string=remap_cmd,
    )

    menu.add_menu_entry("GetAssetActions", entry)
    tool_menus.refresh_all_widgets()
    unreal.log(f"{TAG} Registered 'Run ARKit Remap' in the Content Browser context menu.")
    return True


try:
    success = register_context_menu()
    if success:
        unreal.log(f"{TAG} Startup complete.")
    else:
        unreal.log_warning(f"{TAG} Startup completed with warnings.")
except Exception as e:
    unreal.log_warning(f"{TAG} Registration failed: {e}")
