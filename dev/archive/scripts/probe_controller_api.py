"""Probe: find the correct AnimSequence controller/bracket API for batch writes."""
import unreal
import json
import os

ASSET = "/Game/3_FaceAnims/VEC_MHA/AgenticPy/AS_MP_VecDemo1-allkeys"
TAG = "[CtrlProbe]"
results = {}

seq = unreal.load_asset(ASSET)
unreal.log(f"{TAG} Loaded: {type(seq).__name__}")

# 1. Search AnimSequence for controller/bracket/model methods
seq_attrs = [a for a in dir(seq) if not a.startswith("__")]
results["seq_controller_attrs"] = [a for a in seq_attrs if "control" in a.lower()]
results["seq_bracket_attrs"] = [a for a in seq_attrs if "bracket" in a.lower()]
results["seq_model_attrs"] = [a for a in seq_attrs if "model" in a.lower() or "data_model" in a.lower()]
results["seq_modify_attrs"] = [a for a in seq_attrs if "modif" in a.lower() or "batch" in a.lower()]
results["seq_compress_attrs"] = [a for a in seq_attrs if "compress" in a.lower() or "recompress" in a.lower()]

# 2. Check for AnimationDataController class
for cls_name in [
    "AnimationDataController",
    "AnimationDataControllerBracket",
    "AnimDataController",
    "IAnimationDataController",
    "AnimationDataModel",
    "AnimDataModel",
]:
    results[f"has_{cls_name}"] = hasattr(unreal, cls_name)

# 3. Check AnimationLibrary for bracket/batch methods
lib_attrs = [a for a in dir(unreal.AnimationLibrary) if not a.startswith("__")]
results["lib_bracket_attrs"] = [a for a in lib_attrs if "bracket" in a.lower()]
results["lib_batch_attrs"] = [a for a in lib_attrs if "batch" in a.lower() or "bulk" in a.lower()]
results["lib_controller_attrs"] = [a for a in lib_attrs if "control" in a.lower()]

# 4. Check for ScopedTransaction or other transaction wrappers
for cls_name in [
    "ScopedEditorTransaction",
    "ScopedTransaction",
    "ScopedSlowTask",
    "TransactionContext",
]:
    results[f"has_{cls_name}"] = hasattr(unreal, cls_name)

# 5. Try accessing data model through various paths
for method in ["get_data_model", "data_model", "get_controller", "controller"]:
    try:
        val = getattr(seq, method)
        if callable(val):
            val = val()
        results[f"seq.{method}"] = {"type": type(val).__name__, "ok": True}
    except Exception as e:
        results[f"seq.{method}"] = {"error": str(e), "ok": False}

# 6. Check if AnimSequence has open_bracket directly
for method in ["open_bracket", "close_bracket", "begin_modification", "end_modification"]:
    results[f"seq_has_{method}"] = hasattr(seq, method)

# 7. Check skeleton compression properties
for prop in [
    "bone_compression_settings",
    "curve_compression_settings",
    "compressed_data",
    "do_not_override_compression",
]:
    try:
        val = seq.get_editor_property(prop)
        results[f"prop_{prop}"] = {"value": str(val)[:200], "ok": True}
    except Exception as e:
        results[f"prop_{prop}"] = {"error": str(e), "ok": False}

# 8. Full list of seq methods containing potentially relevant keywords
relevant_kw = ["curve", "key", "raw", "compress", "control", "bracket", "model", "modif", "data", "notify"]
for kw in relevant_kw:
    matches = [a for a in seq_attrs if kw in a.lower()]
    if matches:
        results[f"seq_kw_{kw}"] = matches

# Write results
project_dir = unreal.Paths.project_dir()
report = os.path.join(project_dir, ".cursor", "arkit-remap", "reports", "probe_controller_results.json")
os.makedirs(os.path.dirname(report), exist_ok=True)

def _ser(obj):
    if isinstance(obj, (bool, int, float, str, type(None))):
        return obj
    if isinstance(obj, dict):
        return {str(k): _ser(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_ser(v) for v in obj]
    return str(obj)

with open(report, "w") as f:
    json.dump(_ser(results), f, indent=2)

unreal.log(f"{TAG} Results written to: {report}")
unreal.log(f"{TAG} Done.")
