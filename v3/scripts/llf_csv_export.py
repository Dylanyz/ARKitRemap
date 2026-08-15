"""Export an ARKit AnimSequence as a Live Link Face-style CSV (V3).

Runs INSIDE the UE editor's Python (unlike the offline P1/P2 scripts).
The engine's own `RigMapperEditorSubsystem.ConvertAnimSequenceToCsv` writes a
different schema (`curve_name, frame_number, value`); FaceIt's CSV import and
other Live Link Face tooling want Apple's layout — Timecode, BlendshapeCount,
52 blendshape columns, 9 head/eye rotation columns. Column order below matches
a real Live Link Face recording exactly.

Curves the sequence doesn't have are zero-filled (typically the head/eye
rotations). Sparse keys are resampled with linear interpolation, matching the
Linear export interpolation of MHA sequences.

Usage (UE Python console or remote exec):
    import llf_csv_export
    llf_csv_export.export("/Game/ARKitRemap/arkittest/mh_AS_arkittest_V3remap")
    # optional: export(path, csv_path="D:/out.csv", fps=60.0)
"""

import os

import unreal

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


def _timecode(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int(seconds % 3600 // 60)
    s = int(seconds % 60)
    frames = (seconds % 1.0) * TIMECODE_FPS
    return "%02d:%02d:%02d:%06.3f" % (h, m, s, frames)


def export(asset_path: str, csv_path: str = None, fps: float = None) -> str:
    """Write <asset>.csv beside the asset's package (in Content/) by default.

    Returns the CSV file path.
    """
    seq = unreal.load_asset(asset_path)
    if seq is None:
        raise ValueError("asset not found: " + asset_path)
    lib = unreal.AnimationLibrary

    length = lib.get_sequence_length(seq)
    n_frames = lib.get_num_frames(seq)
    if fps is None:
        fps = (n_frames - 1) / length if length > 0 and n_frames > 1 else 30.0

    names = {str(n) for n in
             lib.get_animation_curve_names(seq, unreal.RawCurveTrackTypes.RCT_FLOAT)}

    # per-column sampled values (zero-filled when the curve is absent)
    grid = [f / fps for f in range(n_frames)]
    columns = {}
    for col in LLF_COLUMNS:
        if col not in names:
            columns[col] = [0.0] * n_frames
            continue
        times, values = lib.get_float_keys(seq, col)
        times = [float(t) for t in times]
        values = [float(v) for v in values]
        # linear resample onto the frame grid
        out, k = [], 0
        for t in grid:
            while k + 1 < len(times) and times[k + 1] <= t:
                k += 1
            if k + 1 >= len(times) or t <= times[0]:
                out.append(values[min(k, len(values) - 1)] if t > times[0] else values[0])
            else:
                t0, t1 = times[k], times[k + 1]
                a = (t - t0) / (t1 - t0) if t1 > t0 else 0.0
                out.append(values[k] * (1 - a) + values[k + 1] * a)
        columns[col] = out

    if csv_path is None:
        package_path = unreal.Paths.convert_relative_path_to_full(
            unreal.PackageTools.package_name_to_filename(
                str(seq.get_outermost().get_name())))
        csv_path = os.path.splitext(package_path)[0] + ".csv"

    with open(csv_path, "w", newline="") as f:
        f.write("Timecode,BlendshapeCount," + ",".join(LLF_COLUMNS) + "\n")
        for i in range(n_frames):
            row = [_timecode(grid[i]), str(len(LLF_COLUMNS))]
            row += ["%.10f" % columns[c][i] for c in LLF_COLUMNS]
            f.write(",".join(row) + "\n")

    unreal.log("LLF CSV written: %s (%d frames @ %.2f fps)" % (csv_path, n_frames, fps))
    return csv_path
