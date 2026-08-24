"""ARKit Remap V3 — Live Link Face CSV export.

This file is the SOURCE OF TRUTH for the exporter embedded inside the
`AAU_ARKitRemap_ExportLLFCSV` Asset Action Utility (a single .uasset — users
never install this file; the uasset carries the script and adds the
right-click menu entry natively). It also works standalone for pipeline
scripting:

    import arkit_llf_csv
    arkit_llf_csv.export("/Game/Path/AS_MySequence")   # headless, no dialogs
    arkit_llf_csv.run()                                 # interactive, uses
                                                        # Content Browser selection

What it does, per selected AnimSequence:
  1. Already has ARKit curves -> exports directly.
  2. Has MHA curves (CTRL_expressions_*) -> auto-remaps through the
     RM_MHA_to_ARKit definition first (engine-native RigMapperEditorSubsystem;
     the intermediate <name>_ARKit sequence is kept beside the source), then
     exports.
  3. Neither -> skipped with a warning.

Output: <asset>_LLF.csv beside the asset's package on disk. The _LLF suffix
is load-bearing: a CSV named exactly like an existing asset makes UE treat a
drag-drop as a REIMPORT of that asset ("not a valid Alembic" errors).

CSV format: real Live Link Face layout — Timecode (60-base fractional
frames, matching actual LLF recordings), BlendshapeCount, 52 blendshapes +
9 head/eye rotation columns in Apple's column order. Curves the sequence
doesn't carry are zero-filled. Optionally re-imports the CSV into UE as a
LevelSequence via LiveLinkFaceImporterFactory (v2-parity feature).

If you edit this file, re-embed it into the Asset Action Utility
(v3/scripts/build_csv_action.py does the embedding).
"""

import os

import unreal

TAG = "[ARKit Remap CSV]"
LIB = unreal.AnimationLibrary
RCT_FLOAT = unreal.RawCurveTrackTypes.RCT_FLOAT
DEFINITION_PATH = "/Game/ARKitRemap/RM_MHA_to_ARKit"

LLF_COLUMNS = [
    "EyeBlinkLeft", "EyeLookDownLeft", "EyeLookInLeft", "EyeLookOutLeft",
    "EyeLookUpLeft", "EyeSquintLeft", "EyeWideLeft", "EyeBlinkRight",
    "EyeLookDownRight", "EyeLookInRight", "EyeLookOutRight", "EyeLookUpRight",
    "EyeSquintRight", "EyeWideRight", "JawForward", "JawRight", "JawLeft",
    "JawOpen", "MouthClose", "MouthFunnel", "MouthPucker", "MouthRight",
    "MouthLeft", "MouthSmileLeft", "MouthSmileRight", "MouthFrownLeft",
    "MouthFrownRight", "MouthDimpleLeft", "MouthDimpleRight",
    "MouthStretchLeft", "MouthStretchRight", "MouthRollLower",
    "MouthRollUpper", "MouthShrugLower", "MouthShrugUpper", "MouthPressLeft",
    "MouthPressRight", "MouthLowerDownLeft", "MouthLowerDownRight",
    "MouthUpperUpLeft", "MouthUpperUpRight", "BrowDownLeft", "BrowDownRight",
    "BrowInnerUp", "BrowOuterUpLeft", "BrowOuterUpRight", "CheekPuff",
    "CheekSquintLeft", "CheekSquintRight", "NoseSneerLeft", "NoseSneerRight",
    "TongueOut", "HeadYaw", "HeadPitch", "HeadRoll", "LeftEyeYaw",
    "LeftEyePitch", "LeftEyeRoll", "RightEyeYaw", "RightEyePitch",
    "RightEyeRoll",
]
TIMECODE_FPS = 60  # Live Link Face timecodes tick at 60 frames/second


# ---------------------------------------------------------------- helpers

def _timecode(seconds):
    h = int(seconds // 3600)
    m = int(seconds % 3600 // 60)
    s = int(seconds % 60)
    frames = (seconds % 1.0) * TIMECODE_FPS
    return "%02d:%02d:%02d:%06.3f" % (h, m, s, frames)


def _curve_names(seq):
    return {str(n) for n in LIB.get_animation_curve_names(seq, RCT_FLOAT)}


def _classify(seq):
    """'arkit' | 'mha' | None."""
    names = _curve_names(seq)
    arkit_hits = sum(1 for c in LLF_COLUMNS[:52] if c in names)
    if arkit_hits >= 10:
        return "arkit"
    if any(n.startswith("CTRL_expressions_") for n in names):
        return "mha"
    return None


def _find_definition():
    d = unreal.load_asset(DEFINITION_PATH)
    if d:
        return d
    ar = unreal.AssetRegistryHelpers.get_asset_registry()
    hits = ar.get_assets_by_class(
        unreal.TopLevelAssetPath("/Script/RigMapper", "RigMapperDefinition"), True)
    for a in hits:
        if str(a.asset_name) == "RM_MHA_to_ARKit":
            return unreal.load_asset(str(a.package_name))
    return None


def _preview_mesh_for(seq):
    skeleton = seq.get_editor_property("skeleton")
    if skeleton is None:
        return None
    try:
        mesh = skeleton.get_editor_property("preview_skeletal_mesh")
        if mesh:
            return mesh
    except Exception:
        pass
    ar = unreal.AssetRegistryHelpers.get_asset_registry()
    skel_path = skeleton.get_path_name()
    for a in ar.get_assets_by_class(
            unreal.TopLevelAssetPath("/Script/Engine", "SkeletalMesh"), True):
        m = unreal.load_asset(str(a.package_name))
        if m and m.get_editor_property("skeleton") and \
                m.get_editor_property("skeleton").get_path_name() == skel_path:
            return m
    return None


def _auto_remap(seq):
    """MHA sequence -> new <name>_ARKit sequence beside it (or None)."""
    definition = _find_definition()
    if definition is None:
        unreal.log_error(
            "%s RM_MHA_to_ARKit definition not found. Install it (see the "
            "ARKit Remap user guide) or remap manually first." % TAG)
        return None
    mesh = _preview_mesh_for(seq)
    if mesh is None:
        unreal.log_error(
            "%s No skeletal mesh found for %s's skeleton (needed by the "
            "RigMapper converter)." % (TAG, seq.get_name()))
        return None
    pkg_dir = seq.get_path_name().rsplit(".", 1)[0].rsplit("/", 1)[0]
    out_name = seq.get_name() + "_ARKit"
    dir_path = unreal.DirectoryPath()
    dir_path.set_editor_property("path", pkg_dir)
    converted = unreal.RigMapperEditorSubsystem.convert_anim_sequence_new(
        seq, mesh, [definition], dir_path, out_name)
    if converted:
        unreal.EditorAssetLibrary.save_asset(pkg_dir + "/" + out_name)
        unreal.log("%s Auto-remapped %s -> %s" % (TAG, seq.get_name(), out_name))
    return converted


def _sample(times, values, t):
    if not times:
        return 0.0
    if t <= times[0]:
        return values[0]
    if t >= times[-1]:
        return values[-1]
    lo, hi = 0, len(times) - 1
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if times[mid] <= t:
            lo = mid
        else:
            hi = mid
    span = times[hi] - times[lo]
    if span <= 1e-9:
        return values[hi]
    a = (t - times[lo]) / span
    return values[lo] * (1.0 - a) + values[hi] * a


# ---------------------------------------------------------------- core API

def export(asset, csv_path=None, fps=None):
    """Export one AnimSequence (path or object) to an LLF CSV. Returns path."""
    seq = unreal.load_asset(asset) if isinstance(asset, str) else asset
    if seq is None:
        raise ValueError("asset not found: %s" % asset)

    length = LIB.get_sequence_length(seq)
    n_frames = LIB.get_num_frames(seq)
    if fps is None:
        fps = (n_frames - 1) / length if length > 0 and n_frames > 1 else 30.0

    names = _curve_names(seq)
    grid = [f / fps for f in range(n_frames)]
    columns, missing = {}, []
    for col in LLF_COLUMNS:
        if col not in names:
            columns[col] = None
            missing.append(col)
            continue
        times, values = LIB.get_float_keys(seq, col)
        times = [float(t) for t in times]
        values = [float(v) for v in values]
        columns[col] = [_sample(times, values, t) for t in grid]
    if missing:
        unreal.log("%s zero-filled columns for %s: %s"
                   % (TAG, seq.get_name(), ", ".join(missing)))

    if csv_path is None:
        package_path = unreal.Paths.convert_relative_path_to_full(
            unreal.PackageTools.package_name_to_filename(
                str(seq.get_outermost().get_name())))
        # _LLF suffix avoids colliding with the source asset's name: a CSV
        # named like an existing asset turns drag-drop into a failed REIMPORT
        csv_path = os.path.splitext(package_path)[0] + "_LLF.csv"
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)

    zero_cell = "0.0000000000"
    with open(csv_path, "w", newline="") as f:
        f.write("Timecode,BlendshapeCount," + ",".join(LLF_COLUMNS) + "\n")
        for i in range(n_frames):
            row = [_timecode(grid[i]), str(len(LLF_COLUMNS))]
            for c in LLF_COLUMNS:
                v = columns[c]
                row.append(zero_cell if v is None else "%.10f" % v[i])
            f.write(",".join(row) + "\n")

    unreal.log("%s Wrote %s (%d frames @ %.2f fps)" % (TAG, csv_path, n_frames, fps))
    return csv_path


def _llf_importer_available():
    return hasattr(unreal, "LiveLinkFaceImporterFactory")


def _import_csv(csv_path, destination_path, destination_name):
    task = unreal.AssetImportTask()
    task.filename = csv_path
    task.destination_path = destination_path
    task.destination_name = destination_name
    task.automated = True
    task.save = True
    task.replace_existing = True
    task.factory = unreal.LiveLinkFaceImporterFactory()
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    paths = list(task.imported_object_paths)
    if paths:
        unreal.log("%s Imported LevelSequence: %s" % (TAG, paths[0]))
        return paths[0]
    unreal.log_warning("%s LLF import created no assets for %s" % (TAG, csv_path))
    return None


# ------------------------------------------------------------ interactive

def run():
    """Interactive entry point (used by the Asset Action Utility)."""
    selected = unreal.EditorUtilityLibrary.get_selected_assets()
    seqs = [a for a in selected if isinstance(a, unreal.AnimSequence)]
    if not seqs:
        unreal.EditorDialog.show_message(
            "ARKit Remap CSV", "Select one or more AnimSequences first.",
            unreal.AppMsgType.OK)
        return

    do_import = False
    if _llf_importer_available():
        answer = unreal.EditorDialog.show_message(
            "ARKit Remap CSV",
            "Also import each CSV back into UE as a LevelSequence?\n\n"
            "Yes = CSV + LevelSequence (via Live Link Face Importer)\n"
            "No  = CSV file only (saved beside the asset as <name>_LLF.csv)",
            unreal.AppMsgType.YES_NO)
        do_import = answer == unreal.AppReturnType.YES

    done, remapped, imported, skipped = [], [], [], []
    for seq in seqs:
        kind = _classify(seq)
        if kind == "mha":
            converted = _auto_remap(seq)
            if converted is None:
                skipped.append(seq.get_name() + " (auto-remap failed)")
                continue
            remapped.append(converted.get_name())
            seq = converted
        elif kind is None:
            skipped.append(seq.get_name() + " (no ARKit or MHA curves)")
            continue
        csv_path = export(seq)
        done.append(csv_path)
        if do_import:
            pkg_dir = seq.get_path_name().rsplit(".", 1)[0].rsplit("/", 1)[0]
            result = _import_csv(csv_path, pkg_dir, seq.get_name() + "_CSV")
            if result:
                imported.append(result)

    msg = "Exported %d CSV file(s)." % len(done)
    if done:
        msg += "\n\n" + "\n".join(done)
    if remapped:
        msg += "\n\nAuto-remapped from MHA first: " + ", ".join(remapped)
    if imported:
        msg += "\n\nImported LevelSequences: %d" % len(imported)
    if skipped:
        msg += "\n\nSkipped: " + ", ".join(skipped)
    unreal.EditorDialog.show_message("ARKit Remap CSV", msg, unreal.AppMsgType.OK)
