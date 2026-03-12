"""Try various approaches to register a context menu entry."""
import unreal
import json
import os
import traceback

TAG = "[MenuProbe]"
results = {}

tm = unreal.ToolMenus.get()
menu = tm.find_menu("ContentBrowser.AssetContextMenu")

entry = unreal.ToolMenuEntry(
    name="ARKitRemap_Test",
    type=unreal.MultiBlockType.MENU_ENTRY,
)
entry.set_label("ARKit Test (delete me)")

# Approach 1: add_menu_entry_object(entry)
try:
    menu.add_menu_entry_object(entry)
    results["add_menu_entry_object"] = "ok"
except Exception as e:
    results["add_menu_entry_object"] = str(e)

# Approach 2: add_menu_entry(section, entry)
try:
    menu.add_menu_entry("GetAssetActions", entry)
    results["add_menu_entry_section_entry"] = "ok"
except Exception as e:
    results["add_menu_entry_section_entry"] = str(e)

# Approach 3: add_menu_entry(entry) - one arg
try:
    menu.add_menu_entry(entry)
    results["add_menu_entry_one_arg"] = "ok"
except Exception as e:
    results["add_menu_entry_one_arg"] = str(e)

# Approach 4: Use insert_position on the entry to specify section
try:
    entry2 = unreal.ToolMenuEntry(
        name="ARKitRemap_Test2",
        type=unreal.MultiBlockType.MENU_ENTRY,
    )
    entry2.set_label("ARKit Test 2")
    ins = unreal.ToolMenuInsert()
    ins.set_editor_property("name", "GetAssetActions")
    entry2.set_editor_property("insert_position", ins)
    menu.add_menu_entry_object(entry2)
    results["insert_position_approach"] = "ok"
except Exception as e:
    results["insert_position_approach"] = str(e)

# Approach 5: add_section first, then add_menu_entry
try:
    menu.add_section("ARKitRemapSection", "ARKit Remap")
    entry3 = unreal.ToolMenuEntry(
        name="ARKitRemap_Test3",
        type=unreal.MultiBlockType.MENU_ENTRY,
    )
    entry3.set_label("ARKit Test 3")
    menu.add_menu_entry("ARKitRemapSection", entry3)
    results["own_section_approach"] = "ok"
except Exception as e:
    results["own_section_approach"] = str(e)

tm.refresh_all_widgets()

path = os.path.join(unreal.Paths.project_dir(), ".cursor/arkit-remap/reports/probe_menu_register.json")
with open(path, "w") as f:
    json.dump(results, f, indent=2)
unreal.log(f"{TAG} Done. Check report.")
