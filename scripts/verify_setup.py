"""ARKitRemap setup verifier — run inside the UE editor (see scripts/README.md for how).

Checks the project end-to-end and prints PASS/FAIL per check with the fix for each failure.
Two tiers:
  1. Project tier (always): plugin enabled, assets installed.
  2. Live tier (only if ARKITREMAP_ACTOR is set): the actor's mesh wiring, editor-preview
     flag, Live Link stream, and definition output.

Config via env vars (set before editor launch, or in-process via os.environ):
  ARKITREMAP_ACTOR      label of the level actor to check live wiring on (optional)
  ARKITREMAP_COMPONENT  name of the skeletal mesh component (optional; default: first
                        component whose mesh has ARKit morphs, else first skeletal component)
"""

import os
import unreal

CONFIG = {
    "actor_label": os.environ.get("ARKITREMAP_ACTOR", ""),
    "component_name": os.environ.get("ARKITREMAP_COMPONENT", ""),
}

GOTCHAS = "reference/gotchas.md"
ASSET_ROOT = "/Game/ARKitRemap"
REQUIRED_ASSETS = ["RM_MHA_to_ARKit"]
OPTIONAL_ASSETS = ["abp_arkit_remap_universal", "BC_ARKitRemapLive", "AAU_ARKitRemap_ExportLLFCSV"]
ARKIT_PROBE_MORPHS = ["jawOpen", "eyeBlinkLeft", "mouthSmileLeft"]

_results = {"pass": 0, "fail": 0}


def report(ok, name, fix=""):
    if ok:
        _results["pass"] += 1
        print("PASS: %s" % name)
    else:
        _results["fail"] += 1
        print("FAIL: %s" % name)
        if fix:
            print("      FIX: %s" % fix)
    return ok


def check_project_tier():
    # Which editor answered? (multi-instance hijack guard)
    print("INFO: project = %s  (verify this is the project you meant; see %s#python-binding-hijack)"
          % (unreal.Paths.get_project_file_path(), GOTCHAS))

    plugin_ok = report(
        hasattr(unreal, "RigMapperDefinition"),
        "RigMapper plugin loaded",
        'add {"Name": "RigMapper", "Enabled": true} to the .uproject Plugins array and RESTART '
        "the editor. Verify the .uproject JSON directly - MCP plugin toggles can silently no-op. "
        "See %s#plugin-off" % GOTCHAS,
    )

    assets_ok = True
    for name, required in [(a, True) for a in REQUIRED_ASSETS] + [(a, False) for a in OPTIONAL_ASSETS]:
        path = "%s/%s" % (ASSET_ROOT, name)
        loaded = unreal.EditorAssetLibrary.does_asset_exist(path) and unreal.load_asset(path) is not None
        if required:
            assets_ok &= report(
                loaded, "asset %s" % path,
                "copy uassets/ into Content/ARKitRemap/ (EXACT folder name - assets reference "
                "each other at /Game/ARKitRemap/...). If files are there but won't load, it's "
                "the plugin (see above). See %s#install-path" % GOTCHAS,
            )
        elif loaded:
            print("PASS: optional asset %s" % path)
        else:
            print("INFO: optional asset %s not installed (fine unless you need it)" % path)
    return plugin_ok and assets_ok


def morph_names(comp):
    """Lowercased morph target names of the component's mesh (5.8: no find_morph_target
    in Python; use get_all_morph_target_names). Curve->morph binding is case-insensitive."""
    mesh = comp.get_skeletal_mesh_asset()
    if mesh is None:
        return None
    return {str(n).lower() for n in mesh.get_all_morph_target_names()}


def find_component(actor):
    comps = list(actor.get_components_by_class(unreal.SkeletalMeshComponent))
    if not comps:
        return None
    if CONFIG["component_name"]:
        for c in comps:
            if c.get_name() == CONFIG["component_name"]:
                return c
        print("INFO: component %r not found; candidates: %s"
              % (CONFIG["component_name"], [c.get_name() for c in comps]))
        return None
    for c in comps:  # prefer a mesh that actually has ARKit morphs
        names = morph_names(c)
        if names and any(m.lower() in names for m in ARKIT_PROBE_MORPHS):
            return c
    return comps[0]


def check_live_tier():
    label = CONFIG["actor_label"]
    actor = None
    subsys = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for a in subsys.get_all_level_actors():
        if a.get_actor_label() == label:
            actor = a
            break
    if not report(actor is not None, "actor '%s' found in level" % label,
                  "check the actor label in the World Outliner; ARKITREMAP_ACTOR must match it exactly"):
        return

    comp = find_component(actor)
    if not report(comp is not None, "skeletal mesh component found",
                  "the actor has no SkeletalMeshComponent, or ARKITREMAP_COMPONENT names a missing one"):
        return
    print("INFO: checking component '%s'" % comp.get_name())

    # Mesh has ARKit morphs (partial sets are legitimate - e.g. a mask; fail only on zero)
    names = morph_names(comp)
    if names is not None:
        hits = [m for m in ARKIT_PROBE_MORPHS if m.lower() in names]
        missing = [m for m in ARKIT_PROBE_MORPHS if m.lower() not in names]
        report(bool(hits), "mesh has ARKit morph targets (%d total; probed %s)"
               % (len(names), ", ".join(ARKIT_PROBE_MORPHS)),
               "none of the probed ARKit names exist - this mesh is not ARKit-rigged (matching "
               "is case-insensitive, so casing is not the problem). See %s#no-morph-response" % GOTCHAS)
        if hits and missing:
            print("INFO: partial ARKit set - missing %s (fine for partial rigs like masks)" % missing)

    # Anim class wired per-instance
    anim_class = comp.get_editor_property("anim_class")
    is_ours = anim_class is not None and "arkit_remap" in str(anim_class.get_name()).lower()
    report(is_ours, "anim class is an ARKitRemap template (got: %s)"
           % (anim_class.get_name() if anim_class else "None"),
           "set anim class on the LEVEL ACTOR INSTANCE's component (not the Blueprint) to "
           "abp_arkit_remap_universal_C - run setup_live.py. See %s#per-instance-wiring" % GOTCHAS)

    # The #1 frozen-mesh cause
    upd = bool(comp.get_editor_property("update_animation_in_editor"))
    report(upd, "Update Animation in Editor enabled (transient - resets each editor session)",
           "comp.set_update_animation_in_editor(True)  (the set_editor_property spelling fails on "
           "BP-instanced components). Without it the mesh is frozen outside PIE even though the "
           "anim instance evaluates. See %s#frozen-in-editor" % GOTCHAS)

    # Anim instance vars + stream bisect
    inst = comp.get_anim_instance()
    if not report(inst is not None, "anim instance exists",
                  "component not initialized - toggle Update Animation in Editor (above) or re-set the anim class"):
        return
    try:
        use_ll = inst.get_editor_property("UseLiveLink")
        subj = inst.get_editor_property("LiveLinkSubject")
        print("INFO: UseLiveLink=%s  LiveLinkSubject=%s" % (use_ll, subj))
        report(bool(use_ll), "UseLiveLink is on",
               "set it on the instance or CDO (see %s#abp-cdo-defaults), or via the BC_ARKitRemapLive component" % GOTCHAS)
    except Exception as e:
        print("INFO: could not read ABP vars (%s) - custom ABP variant?" % e)

    mha_in = inst.get_curve_value("CTRL_expressions_jawOpen")
    arkit_out = inst.get_curve_value("jawOpen")
    print("INFO: bisect - CTRL_expressions_jawOpen=%.4f  jawOpen=%.4f "
          "(single snapshot; if both are 0 with a neutral face, move the jaw and re-run - do NOT "
          "sleep-loop, see %s#game-thread-sampling)" % (mha_in, arkit_out, GOTCHAS))
    report(mha_in != 0.0, "MHA stream reaching the anim instance (jaw ~neutral can read 0 - re-run mid-expression)",
           "no input curves: check the Live Link subject is green in the Live Link panel and the "
           "subject name matches. Bisect recipe: %s#stream-bisect" % GOTCHAS)
    report(arkit_out != 0.0 or mha_in == 0.0, "definition producing ARKit output",
           "input arrives but no output: definition not in the ABP's Rig Mapper node, or wrong "
           "asset path. See %s#install-path" % GOTCHAS)


print("=" * 60)
print("ARKitRemap verify_setup")
print("=" * 60)
ok = check_project_tier()
if CONFIG["actor_label"]:
    if ok:
        try:
            check_live_tier()
        except Exception:
            import traceback
            _results["fail"] += 1
            print("FAIL: live tier crashed - traceback follows (report this; the check itself is buggy)")
            traceback.print_exc()
    else:
        print("INFO: skipping live tier until project tier passes")
else:
    print("INFO: live tier skipped (set ARKITREMAP_ACTOR to check a character's wiring)")
print("-" * 60)
print("RESULT: %d passed, %d failed%s"
      % (_results["pass"], _results["fail"],
         " - see FIX lines above" if _results["fail"] else " - setup looks good"))
