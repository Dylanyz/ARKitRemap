"""ARKitRemap live wiring — run inside the UE editor (see scripts/README.md for how).

Wires a level actor's skeletal mesh for live MHA driving through the universal template:
sets the anim class per-instance, sets the ABP defaults (subject, UseLiveLink), enables the
transient editor-preview flag, and warns about a conflicting MetaHuman live-link drive.
Idempotent - safe to re-run. Verify afterwards with verify_setup.py.

Config via env vars:
  ARKITREMAP_ACTOR      label of the level actor to wire (REQUIRED)
  ARKITREMAP_SUBJECT    Live Link subject name (default: "webcam")
  ARKITREMAP_COMPONENT  skeletal mesh component name (optional; default: auto-pick the one
                        with ARKit morphs)
  ARKITREMAP_HEAD       "1" to enable UseHeadMovement (default off - body mocap usually owns
                        the head)
"""

import os
import unreal

CONFIG = {
    "actor_label": os.environ.get("ARKITREMAP_ACTOR", ""),
    "subject": os.environ.get("ARKITREMAP_SUBJECT", "webcam"),
    "component_name": os.environ.get("ARKITREMAP_COMPONENT", ""),
    "use_head": os.environ.get("ARKITREMAP_HEAD", "0") == "1",
}

GOTCHAS = "reference/gotchas.md"
ABP_PATH = "/Game/ARKitRemap/abp_arkit_remap_universal"
ARKIT_PROBE_MORPH = "jawOpen"


def fail(msg):
    print("FAIL: %s" % msg)
    raise SystemExit


print("INFO: project = %s" % unreal.Paths.get_project_file_path())
if not CONFIG["actor_label"]:
    fail("set ARKITREMAP_ACTOR to the level actor's label (World Outliner name)")
if not hasattr(unreal, "RigMapperDefinition"):
    fail("RigMapper plugin not loaded - see %s#plugin-off" % GOTCHAS)

abp = unreal.load_asset(ABP_PATH)
if abp is None:
    fail("%s missing - install uassets/ to Content/ARKitRemap/ (see %s#install-path)" % (ABP_PATH, GOTCHAS))

# --- ABP class defaults (CDO): subject + toggles. Exact property names matter. ---
cdo = unreal.get_default_object(abp.generated_class())
subj = unreal.LiveLinkSubjectName()
subj.set_editor_property("name", CONFIG["subject"])
cdo.set_editor_property("LiveLinkSubject", subj)
cdo.set_editor_property("UseLiveLink", True)
cdo.set_editor_property("UseHeadMovement", CONFIG["use_head"])
unreal.EditorAssetLibrary.save_asset(ABP_PATH)
print("PASS: ABP defaults - subject=%r UseLiveLink=True UseHeadMovement=%s (saved)"
      % (CONFIG["subject"], CONFIG["use_head"]))

# --- Find the actor + component (per-instance: shared BP classes must be wired on the instance) ---
actor = None
for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
    if a.get_actor_label() == CONFIG["actor_label"]:
        actor = a
        break
if actor is None:
    fail("actor '%s' not found in the level" % CONFIG["actor_label"])

comps = list(actor.get_components_by_class(unreal.SkeletalMeshComponent))
if not comps:
    fail("actor has no SkeletalMeshComponent")
comp = None
if CONFIG["component_name"]:
    comp = next((c for c in comps if c.get_name() == CONFIG["component_name"]), None)
    if comp is None:
        fail("component %r not found; candidates: %s"
             % (CONFIG["component_name"], [c.get_name() for c in comps]))
else:
    for c in comps:
        mesh = c.get_skeletal_mesh_asset() if hasattr(c, "get_skeletal_mesh_asset") else c.skeletal_mesh
        if mesh and mesh.find_morph_target(ARKIT_PROBE_MORPH) is not None:
            comp = c
            break
    if comp is None:
        comp = comps[0]
        print("INFO: no component with ARKit morphs found - using '%s'; pass ARKITREMAP_COMPONENT "
              "to override" % comp.get_name())
print("INFO: wiring component '%s'" % comp.get_name())

# --- Per-instance anim class + the transient editor-preview flag ---
comp.set_editor_property("animation_mode", unreal.AnimationMode.ANIMATION_BLUEPRINT)
comp.set_editor_property("anim_class", abp.generated_class())
print("PASS: anim class set per-instance (%s#per-instance-wiring)" % GOTCHAS)

comp.set_update_animation_in_editor(True)
print("PASS: Update Animation in Editor enabled - TRANSIENT, resets on editor restart; re-run "
      "this script or re-enable after relaunch (%s#frozen-in-editor)" % GOTCHAS)

# --- Kill a conflicting MetaHuman drive if present ---
try:
    if actor.get_editor_property("UseLiveLink"):
        actor.set_editor_property("UseLiveLink", False)
        print("PASS: actor's own MetaHuman UseLiveLink disabled (%s#metahuman-conflict)" % GOTCHAS)
except Exception:
    pass  # not a MetaHuman-style actor - nothing to disable

print("DONE. Now stream your MHA subject (%r) and run verify_setup.py with "
      "ARKITREMAP_ACTOR=%r to confirm end-to-end." % (CONFIG["subject"], CONFIG["actor_label"]))
