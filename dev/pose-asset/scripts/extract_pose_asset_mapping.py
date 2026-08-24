import json
import os
import traceback

import unreal


ASSET_PATH = "/Game/MetaHumans/Common/Face/ARKit/PA_MetaHuman_ARKit_Mapping.PA_MetaHuman_ARKit_Mapping"
PROJECT_DIR = unreal.Paths.project_dir()
OUTPUT_DIR = os.path.join(
    PROJECT_DIR, ".cursor", "arkit-remap", "data", "pose-asset-mapping", "extracted"
)
OUTPUT_JSON = os.path.join(OUTPUT_DIR, "PA_MetaHuman_ARKit_Mapping.posemap.json")
OUTPUT_JSON_RAW = os.path.join(OUTPUT_DIR, "PA_MetaHuman_ARKit_Mapping.posemap.raw.json")
OUTPUT_LOG = os.path.join(OUTPUT_DIR, "PA_MetaHuman_ARKit_Mapping.posemap.log.txt")


def _name_to_str(value):
    try:
        return str(value)
    except Exception:
        return repr(value)


def _safe_call(fn, *args, **kwargs):
    try:
        return True, fn(*args, **kwargs)
    except Exception as exc:
        return False, str(exc)


def _get_pose_names(pose_asset):
    if hasattr(pose_asset, "get_pose_names"):
        ok, result = _safe_call(pose_asset.get_pose_names)
        if ok and result is not None:
            return [_name_to_str(x) for x in list(result)]

    for prop in ("pose_names", "PoseNames"):
        ok, result = _safe_call(pose_asset.get_editor_property, prop)
        if ok and result:
            return [_name_to_str(x) for x in list(result)]

    return []


def _get_source_animation(pose_asset):
    for prop in ("source_animation", "SourceAnimation"):
        ok, result = _safe_call(pose_asset.get_editor_property, prop)
        if ok and result:
            return result
    return None


def _get_animation_curve_names(anim_seq):
    ok, result = _safe_call(
        unreal.AnimationLibrary.get_animation_curve_names,
        anim_seq,
        unreal.RawCurveTrackTypes.RCT_FLOAT,
    )
    if ok and result is not None:
        return [_name_to_str(x) for x in list(result)]
    return []


def _get_curve_keys(anim_seq, curve_name):
    candidates = [
        lambda: unreal.AnimationLibrary.get_float_keys(anim_seq, curve_name),
        lambda: unreal.AnimationLibrary.get_float_keys(anim_seq, unreal.Name(curve_name)),
    ]
    for fn in candidates:
        ok, result = _safe_call(fn)
        if ok and result is not None:
            return result
    return None


def _normalize_curve_keys(raw):
    if raw is None:
        return []

    if isinstance(raw, (tuple, list)) and len(raw) == 2:
        times, values = raw
        try:
            times_seq = list(times)
            values_seq = list(values)
        except Exception:
            times_seq = []
            values_seq = []
        keys = []
        for t, v in zip(times_seq, values_seq):
            try:
                keys.append((float(t), float(v)))
            except Exception:
                continue
        keys.sort(key=lambda x: x[0])
        return keys

    if isinstance(raw, (list, tuple)) and raw:
        first = raw[0]
        if hasattr(first, "time") and hasattr(first, "value"):
            keys = []
            for item in raw:
                try:
                    keys.append((float(item.time), float(item.value)))
                except Exception:
                    continue
            keys.sort(key=lambda x: x[0])
            return keys

    return []


def _sample_curve_linear(keys, sample_time):
    if not keys:
        return 0.0
    if sample_time <= keys[0][0]:
        return float(keys[0][1])
    if sample_time >= keys[-1][0]:
        return float(keys[-1][1])

    lo = 0
    hi = len(keys) - 1
    while lo + 1 < hi:
        mid = (lo + hi) // 2
        if keys[mid][0] <= sample_time:
            lo = mid
        else:
            hi = mid

    t0, v0 = keys[lo]
    t1, v1 = keys[hi]
    if t1 == t0:
        return float(v0)
    alpha = (sample_time - t0) / (t1 - t0)
    return float(v0 + (v1 - v0) * alpha)


def _get_play_length(anim_seq):
    if hasattr(anim_seq, "get_play_length"):
        ok, result = _safe_call(anim_seq.get_play_length)
        if ok:
            try:
                return float(result)
            except Exception:
                pass
    for prop in ("sequence_length", "SequenceLength"):
        ok, result = _safe_call(anim_seq.get_editor_property, prop)
        if ok:
            try:
                return float(result)
            except Exception:
                pass
    return 0.0


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    log_lines = []

    result = {
        "assetPath": ASSET_PATH,
        "extractionMethod": "editor_python",
        "records": [],
        "mappingAssumptions": {
            "poseIndexToTimeRule": "i/(N-1)",
            "samplingRule": "linear_interpolation_from_float_keys",
            "baselineAdjustment": "subtract_default_pose_sample_per_curve",
            "filteredZeroWeights": True,
            "epsilon": 0.0001,
        },
        "validationSummary": {"poseCount": 0, "curveCount": 0, "sanityChecks": [], "warnings": []},
        "debug": {},
    }
    result_raw = {
        "assetPath": ASSET_PATH,
        "extractionMethod": "editor_python",
        "records": [],
        "mappingAssumptions": {
            "poseIndexToTimeRule": "i/(N-1)",
            "samplingRule": "linear_interpolation_from_float_keys",
            "baselineAdjustment": "none",
            "filteredZeroWeights": True,
            "epsilon": 0.0001,
        },
        "validationSummary": {"poseCount": 0, "curveCount": 0, "sanityChecks": [], "warnings": []},
        "debug": {},
    }

    pose_asset = unreal.load_asset(ASSET_PATH)
    if not pose_asset:
        raise RuntimeError("Failed to load PoseAsset: {}".format(ASSET_PATH))

    pose_names = _get_pose_names(pose_asset)
    result["validationSummary"]["poseCount"] = len(pose_names)
    result["debug"]["poseNames"] = pose_names
    result_raw["validationSummary"]["poseCount"] = len(pose_names)
    result_raw["debug"]["poseNames"] = pose_names
    log_lines.append("Loaded pose asset. Pose count: {}".format(len(pose_names)))

    source_anim = _get_source_animation(pose_asset)
    if not source_anim:
        raise RuntimeError("PoseAsset source_animation is missing or inaccessible.")

    source_anim_path = source_anim.get_path_name()
    result["debug"]["sourceAnimationPath"] = source_anim_path
    result_raw["debug"]["sourceAnimationPath"] = source_anim_path
    log_lines.append("Source animation: {}".format(source_anim_path))

    curve_names = _get_animation_curve_names(source_anim)
    curve_names = [c for c in curve_names if c.lower().startswith("ctrl_expressions_")]
    result["validationSummary"]["curveCount"] = len(curve_names)
    result["debug"]["curveNames"] = curve_names
    result_raw["validationSummary"]["curveCount"] = len(curve_names)
    result_raw["debug"]["curveNames"] = curve_names
    log_lines.append("Curve count from source animation: {}".format(len(curve_names)))

    play_length = _get_play_length(source_anim)
    result["debug"]["sourceAnimationLengthSeconds"] = play_length
    result_raw["debug"]["sourceAnimationLengthSeconds"] = play_length
    log_lines.append("Source animation length (s): {:.6f}".format(play_length))

    if len(pose_names) == 0:
        result["validationSummary"]["warnings"].append("No pose names found.")
        result_raw["validationSummary"]["warnings"].append("No pose names found.")
    if len(curve_names) == 0:
        result["validationSummary"]["warnings"].append("No source animation curves found.")
        result_raw["validationSummary"]["warnings"].append("No source animation curves found.")

    epsilon = float(result["mappingAssumptions"]["epsilon"])
    pose_count = len(pose_names)

    curve_keys_cache = {}
    non_empty_curve_key_count = 0
    for curve_name in curve_names:
        raw_keys = _get_curve_keys(source_anim, curve_name)
        normalized = _normalize_curve_keys(raw_keys)
        curve_keys_cache[curve_name] = normalized
        if normalized:
            non_empty_curve_key_count += 1
    result["debug"]["nonEmptyCurveKeyCount"] = non_empty_curve_key_count
    result_raw["debug"]["nonEmptyCurveKeyCount"] = non_empty_curve_key_count

    baseline_by_curve = {}
    for curve_name in curve_names:
        baseline_by_curve[curve_name] = _sample_curve_linear(curve_keys_cache[curve_name], 0.0)
    result["debug"]["baselineCurveCount"] = len(baseline_by_curve)

    non_zero_total = 0
    non_zero_total_raw = 0
    for i, pose_name in enumerate(pose_names):
        sample_time = 0.0 if pose_count <= 1 else (float(i) / float(pose_count - 1)) * play_length

        for curve_name in curve_names:
            sampled = _sample_curve_linear(curve_keys_cache[curve_name], sample_time)
            if abs(sampled) > epsilon:
                non_zero_total_raw += 1
                result_raw["records"].append(
                    {
                        "arkitPoseName": pose_name,
                        "sourceMhaCurveName": curve_name,
                        "weight": round(float(sampled), 6),
                        "sampleTimeOrFrame": "time={:.6f}s".format(sample_time),
                        "confidenceNotes": "sampled from source_animation float curve keys",
                    }
                )
            adjusted = sampled - baseline_by_curve.get(curve_name, 0.0)
            if abs(adjusted) > epsilon:
                non_zero_total += 1
                result["records"].append(
                    {
                        "arkitPoseName": pose_name,
                        "sourceMhaCurveName": curve_name,
                        "weight": round(float(adjusted), 6),
                        "sampleTimeOrFrame": "time={:.6f}s".format(sample_time),
                        "confidenceNotes": "sampled then baseline-subtracted using Default pose sample",
                    }
                )

    result["validationSummary"]["sanityChecks"].extend(
        [
            "pose asset loaded",
            "source animation loaded",
            "curve key sampling completed",
            "non-zero record count: {}".format(non_zero_total),
        ]
    )
    result_raw["validationSummary"]["sanityChecks"].extend(
        [
            "pose asset loaded",
            "source animation loaded",
            "curve key sampling completed",
            "non-zero record count: {}".format(non_zero_total_raw),
        ]
    )

    if non_zero_total == 0:
        result["validationSummary"]["warnings"].append(
            "No non-zero records found with current sampling assumptions."
        )
    if non_zero_total_raw == 0:
        result_raw["validationSummary"]["warnings"].append(
            "No non-zero records found with current sampling assumptions."
        )

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    with open(OUTPUT_JSON_RAW, "w", encoding="utf-8") as f:
        json.dump(result_raw, f, indent=2)
    with open(OUTPUT_LOG, "w", encoding="utf-8") as f:
        f.write("\n".join(log_lines) + "\n")

    unreal.log("Pose mapping extraction complete: {}".format(OUTPUT_JSON))
    unreal.log("Pose mapping extraction (raw) complete: {}".format(OUTPUT_JSON_RAW))
    unreal.log("Pose mapping extraction log: {}".format(OUTPUT_LOG))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        tb = traceback.format_exc()
        unreal.log_error(tb)
        try:
            os.makedirs(OUTPUT_DIR, exist_ok=True)
            with open(OUTPUT_LOG, "w", encoding="utf-8") as f:
                f.write(tb + "\n")
        except Exception:
            pass
        raise
