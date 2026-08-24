"""Verify PoseAsset linearity with the strongest editor-side evidence available.

This script tackles improvement-log item #12 by combining:
1. A direct runtime probe against the PoseAsset on `SKM_Face`.
2. A property audit for additive/blend-risk signals on the PoseAsset and source animation.
3. A clean fractional sample on the first non-default source-animation segment
   (0.25 / 0.5 / 0.75 / 1.0), where no earlier pose contamination exists.

Run inside Unreal Editor via:
  python .cursor/scripts/run_python_in_unreal.py --file .cursor/arkit-remap/mapping-pose-asset/scripts/verify_pose_asset_linearity.py
"""

import json
import os
import traceback

import unreal


TAG = "[PoseAssetLinearity]"
POSE_ASSET_PATH = "/Game/MetaHumans/Common/Face/ARKit/PA_MetaHuman_ARKit_Mapping"
MESH_PATH = "/Game/MetaHumans/Common/Face/SKM_Face"
FRACTIONS = [0.25, 0.5, 0.75, 1.0]
EPSILON = 1e-4

PROJECT_DIR = unreal.Paths.project_dir()
OUTPUT_JSON = os.path.join(
    PROJECT_DIR,
    ".cursor",
    "arkit-remap",
    "mapping-pose-asset",
    "data",
    "PA_MetaHuman_ARKit_Mapping.linearity_verification.json",
)
OUTPUT_MD = os.path.join(
    PROJECT_DIR,
    ".cursor",
    "arkit-remap",
    "mapping-pose-asset",
    "reports",
    "PA_MetaHuman_ARKit_Mapping_linearity_verification.md",
)

RCT_FLOAT = unreal.RawCurveTrackTypes.RCT_FLOAT
LIB = unreal.AnimationLibrary


def _safe_call(fn, *args, **kwargs):
    try:
        return True, fn(*args, **kwargs)
    except Exception as exc:
        return False, str(exc)


def _name_to_str(value):
    try:
        return str(value)
    except Exception:
        return repr(value)


def _get_pose_names(pose_asset):
    if hasattr(pose_asset, "get_pose_names"):
        ok, result = _safe_call(pose_asset.get_pose_names)
        if ok and result is not None:
            return [_name_to_str(x) for x in list(result)]
    return []


def _get_source_animation(pose_asset):
    for prop in ("source_animation", "SourceAnimation"):
        ok, result = _safe_call(pose_asset.get_editor_property, prop)
        if ok and result:
            return result
    return None


def _get_animation_curve_names(anim_seq):
    ok, result = _safe_call(LIB.get_animation_curve_names, anim_seq, RCT_FLOAT)
    if ok and result is not None:
        return [_name_to_str(x) for x in list(result)]
    return []


def _normalize_curve_keys(raw):
    if raw is None:
        return []
    if isinstance(raw, (tuple, list)) and len(raw) == 2:
        try:
            times = list(raw[0])
            values = list(raw[1])
        except Exception:
            return []
        out = []
        for time_val, curve_val in zip(times, values):
            try:
                out.append((float(time_val), float(curve_val)))
            except Exception:
                continue
        out.sort(key=lambda item: item[0])
        return out
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
    if abs(t1 - t0) < 1e-12:
        return float(v0)
    alpha = (sample_time - t0) / (t1 - t0)
    return float(v0 + ((v1 - v0) * alpha))


def _get_play_length(anim_seq):
    ok, value = _safe_call(anim_seq.get_play_length)
    if ok:
        return float(value)
    return 0.0


def _coerce_json(value):
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, list):
        return [_coerce_json(item) for item in value]
    if isinstance(value, dict):
        return {str(k): _coerce_json(v) for k, v in value.items()}
    return str(value)


def _property_audit(obj, property_names):
    result = {}
    for prop_name in property_names:
        ok, value = _safe_call(obj.get_editor_property, prop_name)
        result[prop_name] = value if ok else f"UNAVAILABLE: {value}"
    return _coerce_json(result)


def _runtime_probe(pose_asset):
    result = {
        "meshPath": MESH_PATH,
        "animInstanceType": None,
        "activeCurveNames": [],
        "samples": [],
        "status": "not_run",
    }

    mesh = unreal.load_asset(MESH_PATH)
    if mesh is None:
        result["status"] = "mesh_missing"
        return result

    actor = None
    try:
        actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
            unreal.SkeletalMeshActor, unreal.Vector(0.0, 0.0, 0.0)
        )
        comp = actor.skeletal_mesh_component
        comp.set_update_animation_in_editor(True)
        comp.set_enable_animation(True)
        comp.set_allow_anim_curve_evaluation(True)
        comp.set_skeletal_mesh_asset(mesh)
        comp.set_animation_mode(unreal.AnimationMode.ANIMATION_SINGLE_NODE)
        comp.set_animation(pose_asset)

        inst = comp.get_anim_instance()
        result["animInstanceType"] = type(inst).__name__ if inst else None
        if inst is None:
            result["status"] = "no_anim_instance"
            return result

        ok, curve_names = _safe_call(inst.get_all_curve_names)
        if ok and curve_names is not None:
            result["activeCurveNames"] = [_name_to_str(x) for x in list(curve_names)[:40]]

        for weight in FRACTIONS:
            sample = {"inputPose": "JawOpen", "weight": weight}
            ok, value = _safe_call(inst.set_preview_curve_override, "JawOpen", weight, False)
            sample["setPreviewCurveOverride"] = "ok" if ok else value
            _safe_call(inst.kismet_update_animation, 0.033)
            _safe_call(inst.blueprint_post_evaluate_animation)
            for curve_name in (
                "JawOpen",
                "ctrl_expressions_jaw_open",
                "CTRL_Expressions_Jaw_Open",
            ):
                ok, value = _safe_call(inst.get_curve_value, curve_name)
                sample[curve_name] = value if ok else f"ERROR: {value}"
            result["samples"].append(sample)

        any_non_zero = False
        for sample in result["samples"]:
            for key in ("ctrl_expressions_jaw_open", "CTRL_Expressions_Jaw_Open"):
                value = sample.get(key, 0.0)
                if isinstance(value, (int, float)) and abs(value) > 1e-6:
                    any_non_zero = True
                    break
            if any_non_zero:
                break

        result["status"] = "runtime_readback_ok" if any_non_zero else "runtime_readback_inconclusive"
        return result
    finally:
        if actor is not None:
            _safe_call(unreal.EditorLevelLibrary.destroy_actor, actor)


def _first_segment_fractional_probe(pose_asset):
    result = {
        "status": "not_run",
        "firstNonDefaultPose": None,
        "sampleTime": 0.0,
        "fractions": [],
        "curveCount": 0,
        "maxAbsError": 0.0,
        "meanAbsError": 0.0,
        "topCurvesAtFullPose": [],
    }

    source_anim = _get_source_animation(pose_asset)
    if source_anim is None:
        result["status"] = "missing_source_animation"
        return result

    pose_names = _get_pose_names(pose_asset)
    if len(pose_names) < 2:
        result["status"] = "not_enough_poses"
        return result

    play_length = _get_play_length(source_anim)
    first_pose_name = pose_names[1]
    first_pose_time = play_length / float(len(pose_names) - 1) if len(pose_names) > 1 else 0.0
    result["firstNonDefaultPose"] = first_pose_name
    result["sampleTime"] = first_pose_time

    curve_names = [
        curve_name
        for curve_name in _get_animation_curve_names(source_anim)
        if curve_name.lower().startswith("ctrl_expressions_")
    ]

    curve_cache = {}
    baseline_by_curve = {}
    full_adjusted = {}
    for curve_name in curve_names:
        keys = _normalize_curve_keys(LIB.get_float_keys(source_anim, curve_name))
        curve_cache[curve_name] = keys
        baseline = _sample_curve_linear(keys, 0.0)
        baseline_by_curve[curve_name] = baseline
        full_value = _sample_curve_linear(keys, first_pose_time) - baseline
        if abs(full_value) > EPSILON:
            full_adjusted[curve_name] = full_value

    result["curveCount"] = len(full_adjusted)
    result["topCurvesAtFullPose"] = [
        {"curve": name, "fullAdjusted": full_adjusted[name]}
        for name in sorted(full_adjusted, key=lambda key: abs(full_adjusted[key]), reverse=True)[:10]
    ]

    all_errors = []
    for fraction in FRACTIONS:
        sample_time = first_pose_time * fraction
        sample_errors = []
        for curve_name, full_value in full_adjusted.items():
            actual_adjusted = _sample_curve_linear(curve_cache[curve_name], sample_time) - baseline_by_curve[curve_name]
            expected_adjusted = full_value * fraction
            error = actual_adjusted - expected_adjusted
            sample_errors.append(abs(error))

        max_abs_error = max(sample_errors) if sample_errors else 0.0
        mean_abs_error = sum(sample_errors) / len(sample_errors) if sample_errors else 0.0
        all_errors.extend(sample_errors)
        result["fractions"].append(
            {
                "fraction": fraction,
                "sampleTime": sample_time,
                "maxAbsError": max_abs_error,
                "meanAbsError": mean_abs_error,
            }
        )

    result["maxAbsError"] = max(all_errors) if all_errors else 0.0
    result["meanAbsError"] = sum(all_errors) / len(all_errors) if all_errors else 0.0
    result["status"] = "ok"
    return result


def _write_markdown(report):
    lines = [
        "# PoseAsset Linearity Verification",
        "",
        f"- PoseAsset: `{report['poseAssetPath']}`",
        f"- Source animation: `{report['sourceAnimationPath']}`",
        "",
        "## Result",
        "",
        f"- Status: **{report['status']}**",
        f"- Conclusion: {report['conclusion']}",
        "",
        "## Runtime Probe",
        "",
        f"- Status: `{report['runtimeProbe']['status']}`",
        f"- AnimInstance: `{report['runtimeProbe'].get('animInstanceType')}`",
        f"- Reported curve-name count: `{len(report['runtimeProbe'].get('activeCurveNames', []))}`",
        "",
        "| Weight | JawOpen | ctrl_expressions_jaw_open | CTRL_Expressions_Jaw_Open |",
        "|--------|---------|---------------------------|---------------------------|",
    ]

    for sample in report["runtimeProbe"]["samples"]:
        lines.append(
            "| {} | {} | {} | {} |".format(
                sample.get("weight"),
                sample.get("JawOpen"),
                sample.get("ctrl_expressions_jaw_open"),
                sample.get("CTRL_Expressions_Jaw_Open"),
            )
        )

    seg = report["firstSegmentProbe"]
    lines.extend(
        [
            "",
            "## First-Segment Fractional Probe",
            "",
            f"- First non-default pose: `{seg.get('firstNonDefaultPose')}`",
            f"- Contributor curve count: `{seg.get('curveCount')}`",
            f"- Global max abs error: `{seg.get('maxAbsError')}`",
            f"- Global mean abs error: `{seg.get('meanAbsError')}`",
            "",
            "| Fraction | Sample time (s) | Max abs error | Mean abs error |",
            "|----------|------------------|---------------|----------------|",
        ]
    )

    for fraction_row in seg.get("fractions", []):
        lines.append(
            "| {} | {:.6f} | {:.8f} | {:.8f} |".format(
                fraction_row["fraction"],
                fraction_row["sampleTime"],
                fraction_row["maxAbsError"],
                fraction_row["meanAbsError"],
            )
        )

    lines.extend(
        [
            "",
            "## Property Audit",
            "",
            "### PoseAsset",
        ]
    )
    for key, value in report["poseAssetProperties"].items():
        lines.append(f"- `{key}` = `{value}`")

    lines.append("")
    lines.append("### Source Animation")
    for key, value in report["sourceAnimationProperties"].items():
        lines.append(f"- `{key}` = `{value}`")

    with open(OUTPUT_MD, "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")


def main():
    os.makedirs(os.path.dirname(OUTPUT_JSON), exist_ok=True)
    os.makedirs(os.path.dirname(OUTPUT_MD), exist_ok=True)

    pose_asset = unreal.load_asset(POSE_ASSET_PATH)
    if pose_asset is None:
        raise RuntimeError(f"Could not load PoseAsset: {POSE_ASSET_PATH}")

    source_anim = _get_source_animation(pose_asset)
    if source_anim is None:
        raise RuntimeError("PoseAsset source_animation is missing or inaccessible.")

    report = {
        "poseAssetPath": POSE_ASSET_PATH,
        "sourceAnimationPath": source_anim.get_path_name(),
        "poseAssetProperties": _property_audit(
            pose_asset,
            [
                "parent_asset",
                "preview_pose_asset",
                "retarget_source",
                "retarget_source_asset",
                "source_animation",
                "skeleton",
            ],
        ),
        "sourceAnimationProperties": _property_audit(
            source_anim,
            [
                "additive_anim_type",
                "additive_base_pose_type",
                "ref_pose_type",
                "ref_frame_index",
                "interpolation",
                "enable_root_motion",
            ],
        ),
        "runtimeProbe": _runtime_probe(pose_asset),
        "firstSegmentProbe": _first_segment_fractional_probe(pose_asset),
        "status": "needs_followup",
        "conclusion": "",
    }

    segment_ok = (
        report["firstSegmentProbe"]["status"] == "ok"
        and report["firstSegmentProbe"]["maxAbsError"] < 1e-3
    )
    runtime_ok = report["runtimeProbe"]["status"] == "runtime_readback_ok"

    if runtime_ok and segment_ok:
        report["status"] = "verified"
        report["conclusion"] = (
            "The direct runtime probe produced non-zero readback and the clean first "
            "source-animation segment scales linearly across 0.25/0.5/0.75/1.0."
        )
    elif segment_ok:
        report["status"] = "likely_linear_runtime_probe_inconclusive"
        report["conclusion"] = (
            "The direct PoseAsset runtime probe did not expose readable output curves from "
            "Python on a transient `AnimSingleNodeInstance`, but the first uncontaminated "
            "source-animation segment sampled cleanly at 0.25/0.5/0.75/1.0 with negligible "
            "error. This materially reduces the linearity risk, but it does not fully prove "
            "live-node behavior for every pose."
        )
    else:
        report["conclusion"] = (
            "Neither the runtime probe nor the first-segment fractional sample was strong "
            "enough to clear the linearity concern. Review the generated data before relying "
            "on the weight-only assumption."
        )

    with open(OUTPUT_JSON, "w", encoding="utf-8") as handle:
        json.dump(_coerce_json(report), handle, indent=2)
    _write_markdown(report)

    unreal.log(f"{TAG} JSON report: {OUTPUT_JSON}")
    unreal.log(f"{TAG} Markdown report: {OUTPUT_MD}")
    unreal.log(f"{TAG} Status: {report['status']}")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        tb = traceback.format_exc()
        unreal.log_error(tb)
        os.makedirs(os.path.dirname(OUTPUT_JSON), exist_ok=True)
        with open(OUTPUT_JSON, "w", encoding="utf-8") as handle:
            json.dump({"status": "error", "traceback": tb}, handle, indent=2)
        raise
