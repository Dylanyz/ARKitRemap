import unreal, json, os

r = {}
for c in ["ToolMenuEntryScript", "ToolMenuSectionDynamic", "ToolMenuInsert", "ToolMenuEntryInitData"]:
    r[c] = hasattr(unreal, c)

if hasattr(unreal, "ToolMenuEntryScript"):
    r["ToolMenuEntryScript_attrs"] = [
        a for a in dir(unreal.ToolMenuEntryScript) if not a.startswith("__")
    ]

if hasattr(unreal, "ToolMenuInsert"):
    r["ToolMenuInsert_attrs"] = [
        a for a in dir(unreal.ToolMenuInsert) if not a.startswith("__")
    ]

# Try to construct entry with keyword args
try:
    entry = unreal.ToolMenuEntry(
        name="test",
        type=unreal.MultiBlockType.MENU_ENTRY,
    )
    r["construct_kw"] = "ok"
    r["entry_type"] = type(entry).__name__
except Exception as e:
    r["construct_kw_err"] = str(e)

# Try ToolMenuEntryScript approach
if hasattr(unreal, "ToolMenuEntryScript"):
    try:
        script_entry = unreal.ToolMenuEntryScript()
        r["script_entry_type"] = type(script_entry).__name__
        script_attrs = [a for a in dir(script_entry) if not a.startswith("__")]
        r["script_entry_attrs"] = [a for a in script_attrs if "init" in a.lower() or "data" in a.lower() or "register" in a.lower() or "entry" in a.lower()]
    except Exception as e:
        r["script_entry_err"] = str(e)

path = os.path.join(unreal.Paths.project_dir(), ".cursor/arkit-remap/reports/probe_tme3.json")
with open(path, "w") as f:
    json.dump(r, f, indent=2)
unreal.log("[probe] menu entry done")
