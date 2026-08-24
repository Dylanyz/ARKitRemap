"""ARKitRemap batch convert — run inside the UE editor (see scripts/README.md for how).

Converts MHA AnimSequence(s) into ARKit AnimSequence(s) through RM_MHA_to_ARKit, same as the
right-click "Convert Selected Using RigMapper" action but scriptable. Operates on the
Content Browser selection by default, or on explicit paths.

Config via env vars:
  ARKITREMAP_SOURCES  semicolon-separated asset paths (e.g. "/Game/Anims/AS_Take1;...").
                      Empty = use the current Content Browser selection.
  ARKITREMAP_MESH     asset path of the target ARKit skeletal mesh (REQUIRED)
  ARKITREMAP_SUFFIX   output name suffix (default "_ARKit")
"""

import os
import unreal

CONFIG = {
    "sources": [p for p in os.environ.get("ARKITREMAP_SOURCES", "").split(";") if p],
    "mesh": os.environ.get("ARKITREMAP_MESH", ""),
    "suffix": os.environ.get("ARKITREMAP_SUFFIX", "_ARKit"),
}

GOTCHAS = "reference/gotchas.md"
DEF_PATH = "/Game/ARKitRemap/RM_MHA_to_ARKit"


def fail(msg):
    print("FAIL: %s" % msg)
    raise SystemExit


print("INFO: project = %s" % unreal.Paths.get_project_file_path())
if not hasattr(unreal, "RigMapperDefinition"):
    fail("RigMapper plugin not loaded - see %s#plugin-off" % GOTCHAS)

definition = unreal.load_asset(DEF_PATH)
if definition is None:
    fail("%s missing - install uassets/ to Content/ARKitRemap/ (%s#install-path)" % (DEF_PATH, GOTCHAS))

if not CONFIG["mesh"]:
    fail("set ARKITREMAP_MESH to the target ARKit character's SkeletalMesh asset path")
mesh = unreal.load_asset(CONFIG["mesh"])
if mesh is None:
    fail("target mesh not found: %s" % CONFIG["mesh"])

if CONFIG["sources"]:
    sources = [unreal.load_asset(p) for p in CONFIG["sources"]]
    missing = [p for p, a in zip(CONFIG["sources"], sources) if a is None]
    if missing:
        fail("source asset(s) not found: %s" % missing)
else:
    sources = [a for a in unreal.EditorUtilityLibrary.get_selected_assets()
               if isinstance(a, unreal.AnimSequence)]
    if not sources:
        fail("no AnimSequences selected in the Content Browser (or set ARKITREMAP_SOURCES)")

converted = 0
for seq in sources:
    pkg = seq.get_path_name().rsplit("/", 1)[0]
    name = seq.get_name() + CONFIG["suffix"]
    out_dir = unreal.DirectoryPath()
    out_dir.set_editor_property("path", pkg)
    # "Invalid curve type: RCT_Vector" warnings are benign (float curves only).
    result = unreal.RigMapperEditorSubsystem.convert_anim_sequence_new(
        seq, mesh, [definition], out_dir, name)
    if result:
        unreal.EditorAssetLibrary.save_loaded_asset(result)
        converted += 1
        print("PASS: %s -> %s/%s" % (seq.get_name(), pkg, name))
    else:
        print("FAIL: %s - conversion returned None. Check the source is an MHA sequence with "
              "CTRL_expressions_* curves and the mesh has ARKit morphs (%s#no-morph-response)"
              % (seq.get_name(), GOTCHAS))

print("RESULT: %d/%d converted" % (converted, len(sources)))
