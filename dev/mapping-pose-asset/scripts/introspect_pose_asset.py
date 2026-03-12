import json
import os
import traceback

import unreal


ASSET_PATH = "/Game/MetaHumans/Common/Face/ARKit/PA_MetaHuman_ARKit_Mapping.PA_MetaHuman_ARKit_Mapping"
PROJECT_DIR = unreal.Paths.project_dir()
OUTPUT_DIR = os.path.join(
    PROJECT_DIR, ".cursor", "arkit-remap", "data", "pose-asset-mapping", "extracted"
)
OUT_PATH = os.path.join(OUTPUT_DIR, "PA_MetaHuman_ARKit_Mapping.introspection.json")


def _safe(fn, *args, **kwargs):
    try:
        return True, fn(*args, **kwargs)
    except Exception as exc:
        return False, str(exc)


def _s(value):
    try:
        return str(value)
    except Exception:
        return repr(value)


def _list_editor_properties(obj):
    if hasattr(obj, "get_editor_property_names"):
        ok, props = _safe(obj.get_editor_property_names)
        if ok:
            return [_s(x) for x in props]

    names = []
    for name in dir(obj):
        if name.startswith("_"):
            continue
        if "property" in name.lower():
            names.append(name)
    return names


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    out = {
        "assetPath": ASSET_PATH,
        "poseAssetClass": None,
        "poseAssetMethodsLikePoseOrCurve": [],
        "poseAssetEditorProperties": [],
        "sourceAnimationPath": None,
        "sourceAnimationClass": None,
        "sourceAnimationMethodsLikeCurveOrData": [],
        "sourceAnimationEditorProperties": [],
        "animationLibraryProbe": {},
    }

    pose_asset = unreal.load_asset(ASSET_PATH)
    if not pose_asset:
        raise RuntimeError("Failed to load pose asset")

    out["poseAssetClass"] = _s(pose_asset.get_class().get_name())
    out["poseAssetMethodsLikePoseOrCurve"] = sorted(
        [m for m in dir(pose_asset) if ("pose" in m.lower() or "curve" in m.lower())]
    )
    out["poseAssetEditorProperties"] = _list_editor_properties(pose_asset)

    ok, source_anim = _safe(pose_asset.get_editor_property, "source_animation")
    if not ok:
        out["sourceAnimationPath"] = "ERROR: {}".format(source_anim)
    else:
        out["sourceAnimationPath"] = source_anim.get_path_name() if source_anim else None
        if source_anim:
            out["sourceAnimationClass"] = _s(source_anim.get_class().get_name())
            out["sourceAnimationMethodsLikeCurveOrData"] = sorted(
                [
                    m
                    for m in dir(source_anim)
                    if ("curve" in m.lower() or "data" in m.lower() or "key" in m.lower())
                ]
            )
            out["sourceAnimationEditorProperties"] = _list_editor_properties(source_anim)

            probe = {}
            out["animationLibraryProbe"] = probe
            for label, fn in [
                ("get_animation_curve_names(anim)", lambda: unreal.AnimationLibrary.get_animation_curve_names(source_anim)),
                (
                    "get_animation_curve_names(anim, RCT_FLOAT)",
                    lambda: unreal.AnimationLibrary.get_animation_curve_names(
                        source_anim, unreal.RawCurveTrackTypes.RCT_FLOAT
                    ),
                ),
            ]:
                ok2, res2 = _safe(fn)
                if ok2:
                    names = [_s(x) for x in list(res2)]
                    probe[label] = {"ok": True, "count": len(names), "first10": names[:10]}
                else:
                    probe[label] = {"ok": False, "error": res2}

            for probe_key in list(probe.keys()):
                item = probe[probe_key]
                if not item.get("ok") or not item.get("first10"):
                    continue
                curve_name = item["first10"][0]
                k_ok, k_res = _safe(unreal.AnimationLibrary.get_float_keys, source_anim, curve_name)
                rec = {"curve": curve_name, "ok": k_ok}
                if k_ok:
                    if isinstance(k_res, (list, tuple)):
                        rec["returnType"] = "list_or_tuple"
                        rec["len"] = len(k_res)
                        if len(k_res) == 2 and isinstance(k_res[0], (list, tuple)) and isinstance(k_res[1], (list, tuple)):
                            rec["times_len"] = len(k_res[0])
                            rec["values_len"] = len(k_res[1])
                            rec["times_first5"] = [float(x) for x in list(k_res[0])[:5]]
                            rec["values_first5"] = [float(x) for x in list(k_res[1])[:5]]
                    else:
                        rec["returnType"] = type(k_res).__name__
                        rec["preview"] = _s(k_res)
                else:
                    rec["error"] = k_res
                probe["get_float_keys_for_first_curve_from_{}".format(probe_key)] = rec

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    unreal.log("Pose asset introspection written: {}".format(OUT_PATH))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        unreal.log_error(traceback.format_exc())
        raise
