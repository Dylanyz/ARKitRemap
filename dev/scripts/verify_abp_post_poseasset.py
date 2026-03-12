"""Verify ABP_MH_LiveLink post-PoseAsset behavior against baked data.

This script focuses on improvement-log item #10:
- confirm the JawOpenAlpha / TeethShowAlpha logic exists post-PoseAsset,
- check whether baked MHA AnimSequences already contain the final jaw/teeth curves,
- and record whether separate alpha curves are absent from the bake.

Run inside Unreal Editor via:
  python .cursor/scripts/run_python_in_unreal.py --file .cursor/arkit-remap/scripts/verify_abp_post_poseasset.py
"""

import json
import os
import traceback

import unreal


TAG = "[ABPPostPoseVerify]"
ABP_PATH = "/Game/MetaHumans/Common/Animation/ABP_MH_LiveLink"
TEST_SEQUENCE_PATH = "/Game/3_FaceAnims/VEC_MHA/AgenticPy/AS_MP_VecDemo1-allkeys"
OUTPUT_DIR = os.path.join(
    unreal.Paths.project_dir(), ".cursor", "arkit-remap", "reports"
)
OUTPUT_JSON = os.path.join(OUTPUT_DIR, "abp_post_poseasset_verification.json")
OUTPUT_MD = os.path.join(OUTPUT_DIR, "abp_post_poseasset_verification.md")

RCT_FLOAT = unreal.RawCurveTrackTypes.RCT_FLOAT
LIB = unreal.AnimationLibrary

JAW_CURVE = "ctrl_expressions_jaw_open"
TEETH_CURVES = [
    "ctrl_expressions_mouth_lower_lip_depress_l",
    "ctrl_expressions_mouth_lower_lip_depress_r",
    "ctrl_expressions_mouth_upper_lip_raise_l",
    "ctrl_expressions_mouth_upper_lip_raise_r",
    "ctrl_expressions_mouth_corner_pull_l",
    "ctrl_expressions_mouth_corner_pull_r",
    "ctrl_expressions_mouth_stretch_l",
    "ctrl_expressions_mouth_stretch_r",
]
ALPHA_CURVE_CANDIDATES = [
    "jawopenalpha",
    "teethshowalpha",
    "jaw_open_alpha",
    "teeth_show_alpha",
    "JawOpenAlpha",
    "TeethShowAlpha",
]


def _safe_call(fn, *args, **kwargs):
    try:
        return True, fn(*args, **kwargs)
    except Exception as exc:
        return False, str(exc)


def _normalize_keys(raw):
    if raw is None:
        return [], []
    if isinstance(raw, (tuple, list)) and len(raw) == 2:
        try:
            return list(raw[0]), list(raw[1])
        except Exception:
            return [], []
    return [], []


def _curve_stats(seq, curve_name):
    exists = LIB.does_curve_exist(seq, curve_name, RCT_FLOAT)
    result = {"exists": exists}
    if not exists:
        return result

    times, values = _normalize_keys(LIB.get_float_keys(seq, curve_name))
    values = [float(v) for v in values]
    result.update(
        {
            "keyCount": len(values),
            "min": min(values) if values else 0.0,
            "max": max(values) if values else 0.0,
            "mean": (sum(values) / len(values)) if values else 0.0,
            "nonZeroKeys": sum(1 for v in values if abs(v) > 1e-6),
            "first3": values[:3],
            "last3": values[-3:] if len(values) >= 3 else values[:],
            "timeRange": [
                float(times[0]) if times else 0.0,
                float(times[-1]) if times else 0.0,
            ],
        }
    )
    return result


def _try_load_blueprint_defaults(asset_path):
    results = {"classPath": None, "defaultObjectClass": None, "properties": {}}

    cls = None
    for class_path in (asset_path + "_C", asset_path + "." + asset_path.rsplit("/", 1)[-1] + "_C"):
        ok, loaded = _safe_call(unreal.load_object, None, class_path)
        if ok and loaded is not None:
            cls = loaded
            results["classPath"] = class_path
            break

    if cls is None and hasattr(unreal, "EditorAssetLibrary"):
        ok, loaded = _safe_call(unreal.EditorAssetLibrary.load_blueprint_class, asset_path)
        if ok and loaded is not None:
            cls = loaded
            results["classPath"] = asset_path

    if cls is None:
        results["error"] = "Could not load generated blueprint class."
        return results

    default_obj = None
    if hasattr(unreal, "get_default_object"):
        ok, loaded = _safe_call(unreal.get_default_object, cls)
        if ok:
            default_obj = loaded

    if default_obj is None and hasattr(cls, "get_default_object"):
        ok, loaded = _safe_call(cls.get_default_object)
        if ok:
            default_obj = loaded

    if default_obj is None:
        results["error"] = "Could not access class default object."
        return results

    results["defaultObjectClass"] = type(default_obj).__name__
    for prop_name in (
        "JawOpenAlpha",
        "jaw_open_alpha",
        "TeethShowAlpha",
        "teeth_show_alpha",
    ):
        ok, value = _safe_call(default_obj.get_editor_property, prop_name)
        results["properties"][prop_name] = value if ok else f"ERROR: {value}"
    return results


def _write_markdown(report):
    lines = [
        "# ABP_MH_LiveLink Post-PoseAsset Verification",
        "",
        f"- Blueprint: `{report['blueprintPath']}`",
        f"- Test sequence: `{report['testSequencePath']}`",
        "",
        "## Result",
        "",
        f"- Status: **{report['status']}**",
        f"- Conclusion: {report['conclusion']}",
        "",
        "## Baked Sequence Evidence",
        "",
        f"- Missing alpha-like curves on bake: `{', '.join(report['missingAlphaCurves']) or 'none'}`",
        "",
        "| Curve | Exists | Min | Max | Mean | Non-zero keys |",
        "|------|--------|-----|-----|------|---------------|",
    ]

    for curve_name in [JAW_CURVE] + TEETH_CURVES:
        stats = report["curveStats"].get(curve_name, {})
        lines.append(
            "| {} | {} | {:.6f} | {:.6f} | {:.6f} | {} |".format(
                curve_name,
                "yes" if stats.get("exists") else "no",
                float(stats.get("min", 0.0)),
                float(stats.get("max", 0.0)),
                float(stats.get("mean", 0.0)),
                int(stats.get("nonZeroKeys", 0)),
            )
        )

    defaults = report.get("blueprintDefaults", {})
    if defaults:
        lines.extend(
            [
                "",
                "## Blueprint Defaults Probe",
                "",
                f"- Loaded class path: `{defaults.get('classPath')}`",
                f"- Default object class: `{defaults.get('defaultObjectClass')}`",
            ]
        )
        for key, value in defaults.get("properties", {}).items():
            lines.append(f"- `{key}` = `{value}`")

    with open(OUTPUT_MD, "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    report = {
        "blueprintPath": ABP_PATH,
        "testSequencePath": TEST_SEQUENCE_PATH,
        "curveStats": {},
        "missingAlphaCurves": [],
        "blueprintDefaults": {},
        "status": "needs_followup",
        "conclusion": "",
    }

    seq = unreal.load_asset(TEST_SEQUENCE_PATH)
    if seq is None or not isinstance(seq, unreal.AnimSequence):
        raise RuntimeError(f"Could not load AnimSequence: {TEST_SEQUENCE_PATH}")

    for curve_name in [JAW_CURVE] + TEETH_CURVES:
        report["curveStats"][curve_name] = _curve_stats(seq, curve_name)

    for curve_name in ALPHA_CURVE_CANDIDATES:
        if not LIB.does_curve_exist(seq, curve_name, RCT_FLOAT):
            report["missingAlphaCurves"].append(curve_name)

    report["blueprintDefaults"] = _try_load_blueprint_defaults(ABP_PATH)

    jaw_ok = report["curveStats"][JAW_CURVE].get("nonZeroKeys", 0) > 0
    teeth_present = [
        name
        for name in TEETH_CURVES
        if report["curveStats"][name].get("nonZeroKeys", 0) > 0
    ]
    alpha_curves_present = [
        name for name in ALPHA_CURVE_CANDIDATES if name not in report["missingAlphaCurves"]
    ]

    default_props = report["blueprintDefaults"].get("properties", {})
    jaw_default = default_props.get("JawOpenAlpha")
    teeth_default = default_props.get("TeethShowAlpha")

    if jaw_ok and teeth_present and not alpha_curves_present:
        report["status"] = "verified_runtime_only_assumption"
        report["conclusion"] = (
            "The baked MHA sequence already contains varying jaw/teeth control curves, "
            "while separate alpha driver curves are absent from the bake. This supports "
            "the working assumption that JawOpenAlpha and TeethShowAlpha are runtime "
            "modulators in ABP_MH_LiveLink rather than extra signals that the reverse "
            "pipeline must invert."
        )
    elif (
        not jaw_ok
        and not teeth_present
        and not alpha_curves_present
        and jaw_default == 0.0
        and teeth_default == 0.0
    ):
        report["status"] = "verified_post_poseasset_overrides_not_baked"
        report["conclusion"] = (
            "The representative baked MHA sequence contains none of the jaw/teeth curves "
            "written by the post-PoseAsset nodes, and the blueprint class defaults for "
            "`JawOpenAlpha` / `TeethShowAlpha` are both 0.0. This indicates those nodes "
            "behave as runtime/manual override paths rather than baked signals that the "
            "reverse remapper must reconstruct."
        )
    else:
        report["conclusion"] = (
            "The baked-curve check did not fully support the runtime-only assumption. "
            "Review the JSON details for missing jaw/teeth activity or unexpected alpha-like "
            "curves."
        )

    with open(OUTPUT_JSON, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)
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
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        with open(OUTPUT_JSON, "w", encoding="utf-8") as handle:
            json.dump({"status": "error", "traceback": tb}, handle, indent=2)
        raise
