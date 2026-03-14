"""ARKitRemap - Export ARKit curves to Live Link Face-style CSV.

Reads ARKit float curves from selected AnimSequence(s) and writes a
Live Link Face-style CSV per sequence with the 52 blendshape columns
plus 9 head/eye rotation columns (zero-filled).

Invoked from the Content Browser context menu via init_unreal.py.
"""

import csv
import math
import os

import unreal

TAG = "[ARKit CSV Export]"
LIB = unreal.AnimationLibrary
RCT_FLOAT = unreal.RawCurveTrackTypes.RCT_FLOAT



ARKIT_HEADERS = [
    "EyeBlinkLeft",
    "EyeLookDownLeft",
    "EyeLookInLeft",
    "EyeLookOutLeft",
    "EyeLookUpLeft",
    "EyeSquintLeft",
    "EyeWideLeft",
    "EyeBlinkRight",
    "EyeLookDownRight",
    "EyeLookInRight",
    "EyeLookOutRight",
    "EyeLookUpRight",
    "EyeSquintRight",
    "EyeWideRight",
    "JawForward",
    "JawRight",
    "JawLeft",
    "JawOpen",
    "MouthClose",
    "MouthFunnel",
    "MouthPucker",
    "MouthRight",
    "MouthLeft",
    "MouthSmileLeft",
    "MouthSmileRight",
    "MouthFrownLeft",
    "MouthFrownRight",
    "MouthDimpleLeft",
    "MouthDimpleRight",
    "MouthStretchLeft",
    "MouthStretchRight",
    "MouthRollLower",
    "MouthRollUpper",
    "MouthShrugLower",
    "MouthShrugUpper",
    "MouthPressLeft",
    "MouthPressRight",
    "MouthLowerDownLeft",
    "MouthLowerDownRight",
    "MouthUpperUpLeft",
    "MouthUpperUpRight",
    "BrowDownLeft",
    "BrowDownRight",
    "BrowInnerUp",
    "BrowOuterUpLeft",
    "BrowOuterUpRight",
    "CheekPuff",
    "CheekSquintLeft",
    "CheekSquintRight",
    "NoseSneerLeft",
    "NoseSneerRight",
    "TongueOut",
]

ROTATION_HEADERS = [
    "HeadYaw",
    "HeadPitch",
    "HeadRoll",
    "LeftEyeYaw",
    "LeftEyePitch",
    "LeftEyeRoll",
    "RightEyeYaw",
    "RightEyePitch",
    "RightEyeRoll",
]


def _get_selected_sequences():
    selected = unreal.EditorUtilityLibrary.get_selected_assets()
    seqs = [a for a in selected if isinstance(a, unreal.AnimSequence)]
    if not seqs:
        unreal.log_error(
            f"{TAG} No AnimSequence(s) selected in the Content Browser."
        )
    return seqs


def _read_curve_cache(seq):
    cache = {}
    missing = []
    for curve_name in ARKIT_HEADERS:
        if not LIB.does_curve_exist(seq, curve_name, RCT_FLOAT):
            missing.append(curve_name)
            continue
        times, values = LIB.get_float_keys(seq, curve_name)
        cache[curve_name] = (list(times), list(values))
    if missing:
        unreal.log_warning(
            f"{TAG} Missing ARKit curves (zero-filled): {missing}"
        )
    return cache


def _pick_canonical_times(curve_cache, play_length):
    if not curve_cache:
        raise RuntimeError("No ARKit curves were found on the source AnimSequence.")

    uniform_lengths = {len(values) for _, values in curve_cache.values()}
    if len(uniform_lengths) == 1:
        any_name = next(iter(curve_cache))
        times = list(curve_cache[any_name][0])
        if times:
            return times

    deltas = []
    longest_times = []
    for times, values in curve_cache.values():
        if len(times) > len(longest_times):
            longest_times = list(times)
        for i in range(1, len(times)):
            delta = float(times[i] - times[i - 1])
            if delta > 1e-6:
                deltas.append(delta)

    if not deltas:
        return [0.0, play_length] if play_length > 1e-6 else [0.0]

    min_delta = min(deltas)
    estimated_frames = max(1, int(round(play_length / min_delta)) + 1)
    if longest_times and len(longest_times) >= estimated_frames:
        return longest_times[:estimated_frames]

    return [i * min_delta for i in range(estimated_frames)]


def _sample_curve(times, values, sample_time):
    if not times or not values:
        return 0.0
    if sample_time <= times[0]:
        return float(values[0])
    last_index = len(times) - 1
    if sample_time >= times[last_index]:
        return float(values[last_index])

    lo = 0
    hi = last_index
    while lo <= hi:
        mid = (lo + hi) // 2
        mid_time = times[mid]
        if math.isclose(mid_time, sample_time, rel_tol=0.0, abs_tol=1e-7):
            return float(values[mid])
        if mid_time < sample_time:
            lo = mid + 1
        else:
            hi = mid - 1

    right_index = max(1, lo)
    left_index = right_index - 1
    left_time = times[left_index]
    right_time = times[right_index]
    left_value = float(values[left_index])
    right_value = float(values[right_index])

    span = right_time - left_time
    if span <= 1e-8:
        return right_value

    alpha = (sample_time - left_time) / span
    return left_value + (right_value - left_value) * alpha


def _timecode_string(sample_time, fps):
    fps = max(1.0, float(fps))
    total_frames_float = sample_time * fps
    total_frames = int(round(total_frames_float))
    hours = total_frames // int(round(fps * 3600.0))
    frames_after_hours = total_frames - (hours * int(round(fps * 3600.0)))
    minutes = frames_after_hours // int(round(fps * 60.0))
    frames_after_minutes = frames_after_hours - (minutes * int(round(fps * 60.0)))
    seconds = frames_after_minutes // int(round(fps))
    frames = frames_after_minutes - (seconds * int(round(fps)))
    milliseconds = int(round((sample_time - (total_frames / fps)) * 1000.0))
    if milliseconds < 0:
        milliseconds = 0
    if milliseconds > 999:
        milliseconds = 999
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}:{frames:02d}.{milliseconds:03d}"


def _write_csv(seq, curve_cache, canonical_times, output_path):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    fps = 30.0
    if len(canonical_times) >= 2:
        delta = canonical_times[1] - canonical_times[0]
        if delta > 1e-6:
            fps = round(1.0 / delta, 3)

    headers = ["Timecode", "BlendshapeCount"] + ARKIT_HEADERS + ROTATION_HEADERS
    with open(output_path, "w", encoding="utf-8", newline="") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(headers)
        for sample_time in canonical_times:
            row = [_timecode_string(sample_time, fps), "61"]
            for curve_name in ARKIT_HEADERS:
                if curve_name in curve_cache:
                    times, values = curve_cache[curve_name]
                    sampled_value = _sample_curve(times, values, sample_time)
                else:
                    sampled_value = 0.0
                row.append(f"{sampled_value:.10f}")
            for _ in ROTATION_HEADERS:
                row.append("0.0000000000")
            writer.writerow(row)

    unreal.log(
        f"{TAG} Wrote {output_path} from {seq.get_path_name()} "
        f"({len(canonical_times)} samples @ ~{fps} fps)"
    )


def _asset_to_filesystem_dir(seq):
    """Convert a /Game/Foo/Bar asset path to the on-disk Content/Foo/Bar/ directory."""
    package_path = seq.get_path_name().rsplit(".", 1)[0]  # /Game/Foo/Bar/Name
    package_dir = package_path.rsplit("/", 1)[0]           # /Game/Foo/Bar
    relative = package_dir.replace("/Game/", "", 1)        # Foo/Bar
    return os.path.join(unreal.Paths.project_content_dir(), relative)


def _import_csv(csv_path, destination_path, destination_name):
    """Import a Live Link Face CSV into UE as a LevelSequence via LiveLinkFaceImporterFactory."""
    factory = unreal.LiveLinkFaceImporterFactory()
    task = unreal.AssetImportTask()
    task.filename = csv_path
    task.destination_path = destination_path
    task.destination_name = destination_name
    task.automated = True
    task.save = True
    task.replace_existing = True
    task.replace_existing_settings = True
    task.factory = factory

    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    imported_paths = list(task.imported_object_paths)
    if not imported_paths:
        unreal.log_warning(
            f"{TAG} LiveLinkFace import did not report any created assets for {csv_path}"
        )
        return None
    imported_path = imported_paths[0]
    unreal.EditorAssetLibrary.save_asset(imported_path, only_if_is_dirty=False)
    unreal.log(f"{TAG} Imported LevelSequence: {imported_path}")
    return imported_path


def _check_llf_importer_available():
    try:
        unreal.LiveLinkFaceImporterFactory()
        return True
    except AttributeError:
        return False


def _export_sequence_csv_only(seq):
    asset_name = seq.get_name()
    play_length = float(seq.get_play_length())
    curve_cache = _read_curve_cache(seq)
    if not curve_cache:
        unreal.log_warning(
            f"{TAG} Skipping {asset_name}: no ARKit curves found."
        )
        return None, None
    canonical_times = _pick_canonical_times(curve_cache, play_length)
    output_dir = _asset_to_filesystem_dir(seq)
    output_path = os.path.join(output_dir, f"{asset_name}.csv")
    _write_csv(seq, curve_cache, canonical_times, output_path)
    package_path = seq.get_path_name().rsplit(".", 1)[0]
    destination_path = package_path.rsplit("/", 1)[0]
    import_name = f"{asset_name}_CSV"
    return output_path, (destination_path, import_name)


def _notify(message, success=True):
    unreal.EditorDialog.show_message(
        "ARKit CSV Export",
        message,
        unreal.AppMsgType.OK,
    )


def _choose_mode():
    llf_available = _check_llf_importer_available()

    msg = (
        "Choose export mode:\n\n"
        "Yes  =  CSV only\n"
        "Save .csv beside the source asset. No engine import.\n\n"
        "No  =  CSV + Import to Content Browser\n"
        "Also imports via LiveLinkFaceImporterFactory as a LevelSequence.\n"
        "Result appears in Content Browser beside the source asset as <name>_CSV."
    )
    if not llf_available:
        msg += (
            "\n\n\u26a0 LiveLinkFaceImporterFactory not found.\n"
            "Enable the Live Link Face Importer plugin and restart the editor\n"
            "to use the import option. CSV-only will still work."
        )

    result = unreal.EditorDialog.show_message(
        "ARKit CSV Export",
        msg,
        unreal.AppMsgType.YES_NO,
    )
    if result == unreal.AppReturnType.YES:
        return "csv_only"
    return "import" if llf_available else "csv_only"


def run():
    seqs = _get_selected_sequences()
    if not seqs:
        _notify(
            "No AnimSequence(s) selected in the Content Browser.\n\n"
            "Select one or more remapped *_ARKit AnimSequences first.",
        )
        return

    mode = _choose_mode()

    csv_paths = []
    imported_paths = []
    skipped = []

    for seq in seqs:
        csv_path, import_args = _export_sequence_csv_only(seq)
        if csv_path is None:
            skipped.append(seq.get_name())
            continue
        csv_paths.append(csv_path)
        if mode == "import" and import_args:
            destination_path, import_name = import_args
            result = _import_csv(csv_path, destination_path, import_name)
            if result:
                imported_paths.append(result)

    if not csv_paths:
        unreal.log_warning(f"{TAG} No CSV files were exported.")
        _notify(
            "No CSV files were exported.\n\n"
            "The selected sequence(s) had no ARKit curves.\n"
            "Make sure you select remapped *_ARKit AnimSequences.",
        )
        return

    unreal.log(f"{TAG} Exported {len(csv_paths)} CSV file(s).")
    for p in csv_paths:
        unreal.log(f"{TAG}   {p}")

    if mode == "csv_only":
        msg = f"Saved {len(csv_paths)} CSV file(s):\n\n" + "\n".join(csv_paths)
    else:
        msg = (
            f"Exported {len(csv_paths)} CSV file(s) and "
            f"imported {len(imported_paths)} LevelSequence(s)."
        )
        if imported_paths:
            msg += "\n\n" + "\n".join(imported_paths)

    if skipped:
        msg += f"\n\nSkipped (no ARKit curves): {', '.join(skipped)}"
    _notify(msg)


run()
