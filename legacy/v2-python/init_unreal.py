"""ARKit Remap - Editor Startup / Context Menu Registration

Registers two entries in the Content Browser right-click menu:
  1. "Run ARKit Remap" — remap with smoothing prompt
  2. "ARKitRemap - Convert to CSV" — export ARKit curves to CSV

In current UE behavior they appear in the main context menu rather
than under the "Asset Actions" subsection.

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

    csv_entry = unreal.ToolMenuEntry(
        name="ARKitRemap_CSV",
        type=unreal.MultiBlockType.MENU_ENTRY,
    )
    csv_entry.set_label("ARKitRemap - Convert to CSV")
    csv_entry.set_tool_tip(
        "Export ARKit blendshape curves from selected AnimSequence(s) "
        "to Live Link Face-style CSV"
    )

    csv_cmd = (
        "import unreal, os; "
        "_p = os.path.join(unreal.Paths.project_dir(), "
        "'Content', 'Python', 'arkit_csv_export.py'); "
        "exec(open(_p).read()) if os.path.isfile(_p) else "
        "unreal.log_error('[ARKit CSV Export] Script not found: ' + _p)"
    )
    csv_entry.set_string_command(
        type=unreal.ToolMenuStringCommandType.PYTHON,
        custom_type="",
        string=csv_cmd,
    )

    menu.add_menu_entry("GetAssetActions", csv_entry)

    tool_menus.refresh_all_widgets()
    unreal.log(f"{TAG} Registered context menu entries (Remap, CSV Export).")
    return True


try:
    success = register_context_menu()
    if success:
        unreal.log(f"{TAG} Startup complete.")
    else:
        unreal.log_warning(f"{TAG} Startup completed with warnings.")
except Exception as e:
    unreal.log_warning(f"{TAG} Registration failed: {e}")
