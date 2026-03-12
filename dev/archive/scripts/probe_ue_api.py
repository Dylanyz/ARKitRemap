"""ARKit Remap - UE Python API Probe
Run once in UE Output Log to verify API availability and signatures.
Results saved to .cursor/arkit-remap/reports/probe_ue_api_results.json

Usage (exec one-liner in UE Output Log):
  exec(open(unreal.Paths.project_dir() + ".cursor/arkit-remap/scripts/probe_ue_api.py").read())

Or if bootstrapper is set up:
  py probe_ue_api
"""

import unreal
import json
import os
import traceback

SANDBOX_ASSET = "/Game/3_FaceAnims/VEC_MHA/AgenticPy/AS_VecDemo1RAW_Cursor"
TEMP_DUP_PATH = "/Game/3_FaceAnims/VEC_MHA/AgenticPy/__probe_temp_dup__"

_project_dir = unreal.Paths.project_dir()
REPORT_PATH = os.path.join(
    _project_dir, ".cursor", "arkit-remap", "reports", "probe_ue_api_results.json"
)

results = {}


def probe(name, fn):
    try:
        val = fn()
        results[name] = {"ok": True, "value": val}
        unreal.log(f"[Probe] {name}: OK")
    except Exception as e:
        results[name] = {
            "ok": False,
            "error": str(e),
            "traceback": traceback.format_exc(),
        }
        unreal.log_warning(f"[Probe] {name}: FAILED - {e}")


# ---------------------------------------------------------------------------
# 1. Which animation library class exists?
# ---------------------------------------------------------------------------
def test_animation_library():
    found = {}
    for name in ("AnimationLibrary", "AnimationBlueprintLibrary"):
        found[name] = hasattr(unreal, name)
    return found


probe("animation_library_class", test_animation_library)


def _get_anim_lib():
    for name in ("AnimationLibrary", "AnimationBlueprintLibrary"):
        if hasattr(unreal, name):
            return getattr(unreal, name), name
    return None, None


# ---------------------------------------------------------------------------
# 2. RawCurveTrackTypes enum
# ---------------------------------------------------------------------------
def test_raw_curve_track_types():
    info = {}
    if not hasattr(unreal, "RawCurveTrackTypes"):
        return {"exists": False}
    info["exists"] = True
    for attr in ("RCT_FLOAT", "FLOAT", "RCT_VECTOR", "RCT_TRANSFORM"):
        try:
            info[attr] = str(getattr(unreal.RawCurveTrackTypes, attr))
        except AttributeError:
            info[attr] = None
    return info


probe("raw_curve_track_types", test_raw_curve_track_types)


# ---------------------------------------------------------------------------
# 3. Load sandbox asset
# ---------------------------------------------------------------------------
def test_load_asset():
    asset = unreal.load_asset(SANDBOX_ASSET)
    if asset is None:
        return {"error": "load_asset returned None - asset may not exist at path"}
    return {
        "type": type(asset).__name__,
        "is_anim_sequence": isinstance(asset, unreal.AnimSequence),
    }


probe("load_sandbox_asset", test_load_asset)


# ---------------------------------------------------------------------------
# 4. does_curve_exist
# ---------------------------------------------------------------------------
def test_does_curve_exist():
    seq = unreal.load_asset(SANDBOX_ASSET)
    lib, lib_name = _get_anim_lib()
    if lib is None:
        return {"error": "No animation library found"}
    out = {"lib": lib_name}
    test_curve = "ctrl_expressions_browdownl"

    for label, args in [
        ("with_RCT_FLOAT", (seq, test_curve, unreal.RawCurveTrackTypes.RCT_FLOAT)),
        ("name_only", (seq, test_curve)),
    ]:
        try:
            r = lib.does_curve_exist(*args)
            out[label] = r
        except Exception as e:
            out[label + "_err"] = str(e)

    try:
        r = lib.does_curve_exist(
            seq, "NONEXISTENT_XYZ", unreal.RawCurveTrackTypes.RCT_FLOAT
        )
        out["nonexistent"] = r
    except Exception as e:
        out["nonexistent_err"] = str(e)

    return out


probe("does_curve_exist", test_does_curve_exist)


# ---------------------------------------------------------------------------
# 5. get_float_keys return format
# ---------------------------------------------------------------------------
def test_get_float_keys():
    seq = unreal.load_asset(SANDBOX_ASSET)
    lib, _ = _get_anim_lib()
    if lib is None:
        return {"error": "No animation library found"}
    out = {}

    try:
        ret = lib.get_float_keys(seq, "ctrl_expressions_browdownl")
        out["return_type"] = type(ret).__name__

        if isinstance(ret, (list, tuple)):
            out["length"] = len(ret)
            if len(ret) > 0:
                first = ret[0]
                out["first_type"] = type(first).__name__
                if isinstance(first, (list, tuple)):
                    out["first_length"] = len(first)
                    if len(first) > 0:
                        out["first_sub_type"] = type(first[0]).__name__
                else:
                    attrs = [a for a in dir(first) if not a.startswith("_")]
                    out["first_attrs"] = attrs[:25]
                    for a in ("time", "value", "interp_mode", "arrive_tangent",
                              "leave_tangent", "tangent_mode"):
                        if hasattr(first, a):
                            out[f"first.{a}"] = str(getattr(first, a))
                if len(ret) >= 3:
                    out["sample_3"] = [str(k) for k in ret[:3]]
            out["total_keys"] = len(ret)
        else:
            out["raw_repr"] = repr(ret)[:500]
    except Exception as e:
        out["error"] = str(e)
        out["tb"] = traceback.format_exc()

    return out


probe("get_float_keys", test_get_float_keys)


# ---------------------------------------------------------------------------
# 6. add_curve / add_float_curve_keys / remove_curve
#    Uses a temporary duplicate to avoid touching the sandbox asset.
# ---------------------------------------------------------------------------
def test_add_and_remove_curve():
    out = {}

    if unreal.EditorAssetLibrary.does_asset_exist(TEMP_DUP_PATH):
        unreal.EditorAssetLibrary.delete_asset(TEMP_DUP_PATH)

    dup = unreal.EditorAssetLibrary.duplicate_asset(SANDBOX_ASSET, TEMP_DUP_PATH)
    if dup is None:
        return {"error": "Could not create temp duplicate for write tests"}

    seq = unreal.load_asset(TEMP_DUP_PATH)
    lib, _ = _get_anim_lib()
    test_name = "__probe_test__"

    # add_curve
    for label, args in [
        (
            "add_with_enum_and_meta",
            (seq, test_name, unreal.RawCurveTrackTypes.RCT_FLOAT, False),
        ),
        ("add_with_enum_only", (seq, test_name, unreal.RawCurveTrackTypes.RCT_FLOAT)),
        ("add_name_only", (seq, test_name)),
    ]:
        try:
            lib.add_curve(seq, "__already__", unreal.RawCurveTrackTypes.RCT_FLOAT, False)
        except:
            pass
        try:
            lib.remove_curve(seq, test_name, False)
        except:
            pass
        try:
            lib.remove_curve(seq, test_name, unreal.RawCurveTrackTypes.RCT_FLOAT, False)
        except:
            pass

        try:
            lib.add_curve(*args)
            out[label] = "ok"
        except Exception as e:
            out[label + "_err"] = str(e)

    # add_float_curve_keys
    try:
        lib.add_curve(seq, test_name, unreal.RawCurveTrackTypes.RCT_FLOAT, False)
    except:
        pass
    try:
        lib.add_float_curve_keys(seq, test_name, [0.0, 0.033], [0.0, 0.5])
        out["add_float_curve_keys"] = "ok"
    except Exception as e:
        out["add_float_curve_keys_err"] = str(e)

    # remove_curve
    for label, args in [
        ("remove_with_enum_and_meta", (seq, test_name, unreal.RawCurveTrackTypes.RCT_FLOAT, False)),
        ("remove_with_enum_only", (seq, test_name, unreal.RawCurveTrackTypes.RCT_FLOAT)),
        ("remove_name_only", (seq, test_name)),
        ("remove_bool_only", (seq, test_name, False)),
    ]:
        try:
            lib.add_curve(seq, test_name, unreal.RawCurveTrackTypes.RCT_FLOAT, False)
        except:
            pass
        try:
            lib.remove_curve(*args)
            out[label] = "ok"
        except Exception as e:
            out[label + "_err"] = str(e)

    # Cleanup temp duplicate
    try:
        unreal.EditorAssetLibrary.delete_asset(TEMP_DUP_PATH)
        out["cleanup"] = "ok"
    except Exception as e:
        out["cleanup_err"] = str(e)

    return out


probe("add_and_remove_curve", test_add_and_remove_curve)


# ---------------------------------------------------------------------------
# 7. EditorAssetLibrary.duplicate_asset behavior
# ---------------------------------------------------------------------------
def test_duplicate_asset():
    out = {}
    dup_path = SANDBOX_ASSET + "__probe_dup"

    if unreal.EditorAssetLibrary.does_asset_exist(dup_path):
        unreal.EditorAssetLibrary.delete_asset(dup_path)

    try:
        ret = unreal.EditorAssetLibrary.duplicate_asset(SANDBOX_ASSET, dup_path)
        out["return_type"] = type(ret).__name__ if ret is not None else "None"
        out["returned_non_null"] = ret is not None
        out["dest_exists"] = unreal.EditorAssetLibrary.does_asset_exist(dup_path)
    except Exception as e:
        out["error"] = str(e)

    # duplicate when dest already exists
    try:
        ret2 = unreal.EditorAssetLibrary.duplicate_asset(SANDBOX_ASSET, dup_path)
        out["dup_when_exists_return"] = type(ret2).__name__ if ret2 is not None else "None"
        out["dup_when_exists_non_null"] = ret2 is not None
    except Exception as e:
        out["dup_when_exists_err"] = str(e)

    # cleanup
    try:
        unreal.EditorAssetLibrary.delete_asset(dup_path)
    except:
        pass

    return out


probe("duplicate_asset", test_duplicate_asset)


# ---------------------------------------------------------------------------
# 8. EditorAssetLibrary.save_asset
# ---------------------------------------------------------------------------
def test_save_asset():
    out = {}
    out["has_save_asset"] = hasattr(unreal.EditorAssetLibrary, "save_asset")
    out["has_save_loaded_asset"] = hasattr(unreal.EditorAssetLibrary, "save_loaded_asset")
    return out


probe("save_asset", test_save_asset)


# ---------------------------------------------------------------------------
# 9. EditorUtilityLibrary.get_selected_assets
# ---------------------------------------------------------------------------
def test_get_selected_assets():
    out = {}
    out["has_EditorUtilityLibrary"] = hasattr(unreal, "EditorUtilityLibrary")
    if not out["has_EditorUtilityLibrary"]:
        return out

    try:
        sel = unreal.EditorUtilityLibrary.get_selected_assets()
        out["return_type"] = type(sel).__name__
        out["count"] = len(sel) if hasattr(sel, "__len__") else "no_len"
        if sel and len(sel) > 0:
            f = sel[0]
            out["first_type"] = type(f).__name__
            if hasattr(f, "get_path_name"):
                out["first_path"] = f.get_path_name()
    except Exception as e:
        out["error"] = str(e)

    return out


probe("get_selected_assets", test_get_selected_assets)


# ---------------------------------------------------------------------------
# 10. Re-execution counter
# ---------------------------------------------------------------------------
def test_reexecution():
    counter_path = os.path.join(
        _project_dir, ".cursor", "arkit-remap", "reports", "probe_run_counter.txt"
    )
    count = 0
    if os.path.isfile(counter_path):
        try:
            count = int(open(counter_path).read().strip())
        except ValueError:
            pass
    count += 1
    os.makedirs(os.path.dirname(counter_path), exist_ok=True)
    with open(counter_path, "w") as f:
        f.write(str(count))
    return {
        "run_count": count,
        "note": "Run py probe_ue_api again; if count increments, re-execution works.",
    }


probe("reexecution", test_reexecution)


# ---------------------------------------------------------------------------
# BONUS: List all curve names on the sandbox asset
# ---------------------------------------------------------------------------
def test_list_curves():
    seq = unreal.load_asset(SANDBOX_ASSET)
    lib, _ = _get_anim_lib()
    if lib is None:
        return {"error": "No animation library found"}
    out = {}

    for method in ("get_animation_curve_names", "get_float_curve_names"):
        if not hasattr(lib, method):
            out[method] = "not_found"
            continue
        try:
            names = getattr(lib, method)(seq)
            name_list = [str(n) for n in names]
            out[method + "_count"] = len(name_list)
            out[method + "_sample"] = name_list[:10]
            out[method + "_has_browdownl"] = any(
                "browdownl" in n.lower() for n in name_list
            )
        except Exception as e:
            out[method + "_err"] = str(e)

    return out


probe("list_curves", test_list_curves)


# ---------------------------------------------------------------------------
# Write results
# ---------------------------------------------------------------------------
def _serialize(obj):
    if isinstance(obj, (bool, int, float, str, type(None))):
        return obj
    if isinstance(obj, dict):
        return {str(k): _serialize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_serialize(v) for v in obj]
    return str(obj)


os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)
with open(REPORT_PATH, "w") as f:
    json.dump(_serialize(results), f, indent=2)

unreal.log(f"[Probe] ============================")
unreal.log(f"[Probe] All tests complete.")
unreal.log(f"[Probe] Results written to: {REPORT_PATH}")
unreal.log(f"[Probe] ============================")
