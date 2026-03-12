"""Forward Remap to MetaHuman

Converts ARKit-named AnimSequences back to ctrl_expressions curves using the
PoseAsset weight matrix (transposed), producing MetaHuman-playable sequences
for side-by-side visual comparison.

Forward direction:
    ctrl_expr_X = sum(arkit_value_i * weight_X_in_target_i)

MouthClose special handling (replicates ABP_MH_LiveLink logic):
    LipsTogether = SafeDivide(MouthClose, JawOpen), clamped [0, 1]
    Written to ctrl_expressions_mouthlipstogether{dl,dr,ul,ur}

Usage (called from another script or runner):
    import forward_remap_to_mh
    forward_remap_to_mh.main(
        asset_paths=["/Game/.../MyARKitAnim"],
        output_suffix="_OnMH",
        time_offset=0.0,
        duration=None,
        template_path=None,
    )
"""

import unreal
import json
import os
from datetime import datetime, timezone

RCT_FLOAT = unreal.RawCurveTrackTypes.RCT_FLOAT
LIB = unreal.AnimationLibrary
EAL = unreal.EditorAssetLibrary
TAG = "[Forward Remap]"


# ---------------------------------------------------------------------------
# Payload loading (shared path logic with arkit_remap.py)
# ---------------------------------------------------------------------------

def _find_payload():
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
    except NameError:
        script_dir = None
    if script_dir:
        local = os.path.join(script_dir, "arkit_remap_payload.json")
        if os.path.isfile(local):
            return local

    project_dir = unreal.Paths.project_dir()
    dev = os.path.join(
        project_dir, ".cursor", "arkit-remap",
        "mapping-pose-asset", "data",
        "AM_ArKitRemap_v02.mapping_payload.json",
    )
    if os.path.isfile(dev):
        return dev
    return None


def _load_payload():
    path = _find_payload()
    if path is None:
        unreal.log_error(f"{TAG} Payload not found.")
        return None, None
    unreal.log(f"{TAG} Payload: {path}")
    with open(path, "r") as f:
        return json.load(f), path


# ---------------------------------------------------------------------------
# Build forward (transposed) index
# ---------------------------------------------------------------------------

def _build_forward_index(payload):
    """Transpose the weight matrix for the forward direction.

    Input (reverse/payload):  {arkitTarget -> [ctrl_expr contributors]}
    Output (forward):         {ctrl_expr_lower -> [(arkitTarget, weight)]}

    Uses ALL weights (no minWeight filtering) because we are replicating the
    PoseAsset forward behavior exactly.
    """
    forward = {}
    arkit_sources = set()

    for entry in payload["arkit52"]:
        target = entry["target"]
        arkit_sources.add(target)
        for contrib in entry["contributors"]:
            ctrl_lower = contrib["source"].lower()
            weight = contrib["weight"]
            if ctrl_lower not in forward:
                forward[ctrl_lower] = []
            forward[ctrl_lower].append((target, weight))

    return forward, arkit_sources


# ---------------------------------------------------------------------------
# Asset path helpers
# ---------------------------------------------------------------------------

def _asset_path(asset):
    return asset.get_path_name().rsplit(".", 1)[0]


def _asset_name(asset_path):
    return asset_path.rsplit("/", 1)[-1]


# ---------------------------------------------------------------------------
# Read ARKit curves (with optional time windowing)
# ---------------------------------------------------------------------------

def _read_arkit_curves(seq, arkit_names, time_offset=0.0, duration=None):
    """Read ARKit-named curves from source, optionally windowing by time.

    Returns dict: curve_name -> (times_list, values_list)
    Output times are zero-based (offset subtracted).
    """
    cache = {}
    missing = []

    for name in sorted(arkit_names):
        if not LIB.does_curve_exist(seq, name, RCT_FLOAT):
            missing.append(name)
            continue
        raw_times, raw_values = LIB.get_float_keys(seq, name)
        times = list(raw_times)
        values = list(raw_values)

        if time_offset > 0 or duration is not None:
            end_time = (time_offset + duration) if duration else float('inf')
            windowed_t, windowed_v = [], []
            for t, v in zip(times, values):
                if t >= time_offset - 1e-6 and t < end_time + 1e-6:
                    windowed_t.append(t - time_offset)
                    windowed_v.append(v)
            times, values = windowed_t, windowed_v

        if times:
            cache[name] = (times, values)
        else:
            missing.append(name)

    if missing:
        unreal.log_warning(
            f"{TAG} {len(missing)} ARKit curves not found or empty after "
            f"windowing (first 10): {missing[:10]}"
        )

    return cache, missing


# ---------------------------------------------------------------------------
# Forward synthesis
# ---------------------------------------------------------------------------

def _forward_synthesis(forward_index, arkit_cache, frame_count):
    """Compute ctrl_expressions values from ARKit curves using transposed weights.

    For each ctrl_expressions curve:
        ctrl_expr_X = sum(arkit_value_i * weight_X_in_target_i)
    """
    ctrl_output = {}
    stats = {}

    for ctrl_name, contributions in forward_index.items():
        values = [0.0] * frame_count
        found = 0

        for arkit_target, weight in contributions:
            if arkit_target not in arkit_cache:
                continue
            found += 1
            arkit_vals = arkit_cache[arkit_target][1]
            n = min(frame_count, len(arkit_vals))
            for i in range(n):
                values[i] += arkit_vals[i] * weight

        if found == 0:
            continue

        ctrl_output[ctrl_name] = values
        stats[ctrl_name] = {
            "contributors": found,
            "total": len(contributions),
            "min": min(values),
            "max": max(values),
            "mean": sum(values) / len(values) if values else 0,
        }

    return ctrl_output, stats


# ---------------------------------------------------------------------------
# MouthClose -> LipsTogether (ABP_MH_LiveLink forward logic)
# ---------------------------------------------------------------------------

def _compute_lips_together(arkit_cache, frame_count):
    """Replicate ABP_MH_LiveLink MouthClose block:
        LipsTogether = SafeDivide(MouthClose, JawOpen), clamped [0, 1]
        Written to all four mouthlipstogether variants.
    """
    mc_key = "MouthClose"
    jo_key = "JawOpen"

    if mc_key not in arkit_cache:
        unreal.log_warning(f"{TAG} {mc_key} not found, skipping LipsTogether.")
        return {}
    if jo_key not in arkit_cache:
        unreal.log_warning(f"{TAG} {jo_key} not found, skipping LipsTogether.")
        return {}

    mc_vals = arkit_cache[mc_key][1]
    jo_vals = arkit_cache[jo_key][1]

    lt_vals = []
    for i in range(frame_count):
        mc = mc_vals[i] if i < len(mc_vals) else 0.0
        jo = jo_vals[i] if i < len(jo_vals) else 0.0
        if abs(jo) < 0.001:
            lt = 0.0
        else:
            lt = mc / jo
        lt_vals.append(max(0.0, min(1.0, lt)))

    curves = {}
    for suffix in ["dl", "dr", "ul", "ur"]:
        curves[f"ctrl_expressions_mouthlipstogether{suffix}"] = list(lt_vals)

    lt_min, lt_max = min(lt_vals), max(lt_vals)
    lt_mean = sum(lt_vals) / len(lt_vals) if lt_vals else 0
    unreal.log(
        f"{TAG} LipsTogether: min={lt_min:.4f}, max={lt_max:.4f}, "
        f"mean={lt_mean:.4f} ({frame_count} frames)"
    )

    return curves


# ---------------------------------------------------------------------------
# Output preparation
# ---------------------------------------------------------------------------

def _prepare_output(source_path, suffix, template_path=None):
    """Create the output sequence.

    If template_path is provided, duplicate the template instead of the source.
    This is used when the source skeleton differs from the target MetaHuman
    skeleton (e.g. for real iPhone ARKit bakes).
    """
    src_name = _asset_name(source_path)
    folder = source_path.rsplit("/", 1)[0]
    out_name = f"{src_name}{suffix}"
    out_path = f"{folder}/{out_name}"

    base_for_dup = template_path if template_path else source_path

    if EAL.does_asset_exist(out_path):
        unreal.log(f"{TAG} Output already exists, clearing ctrl_expressions: {out_path}")
        out_seq = unreal.load_asset(out_path)
        if out_seq is None:
            unreal.log_error(f"{TAG} Could not load existing output: {out_path}")
            return None, None
        return out_seq, out_path

    dup_asset = EAL.duplicate_asset(base_for_dup, out_path)
    if dup_asset is None:
        unreal.log_error(
            f"{TAG} Failed to duplicate {base_for_dup} -> {out_path}"
        )
        return None, None
    unreal.log(f"{TAG} Created output: {out_path} (from {_asset_name(base_for_dup)})")
    return dup_asset, out_path


# ---------------------------------------------------------------------------
# Write ctrl_expressions curves
# ---------------------------------------------------------------------------

def _write_ctrl_curves(seq, ctrl_output, times):
    """Write computed ctrl_expressions curves, batched inside a controller bracket."""
    controller = None
    try:
        controller = seq.controller
        controller.open_bracket(unreal.Text("Forward Remap Batch Write"))
    except Exception:
        controller = None

    written = 0
    for name, values in ctrl_output.items():
        if LIB.does_curve_exist(seq, name, RCT_FLOAT):
            LIB.remove_curve(seq, name, False)
        LIB.add_curve(seq, name, RCT_FLOAT, False)
        LIB.add_float_curve_keys(seq, name, times, values)
        written += 1

    if controller is not None:
        try:
            controller.close_bracket()
        except Exception:
            pass

    return written


# ---------------------------------------------------------------------------
# QA report
# ---------------------------------------------------------------------------

def _write_qa_report(run_data, payload_path):
    project_dir = unreal.Paths.project_dir()
    reports_dir = os.path.join(
        project_dir, ".cursor", "arkit-remap", "reports", "run-logs"
    )
    os.makedirs(reports_dir, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%S")
    md_path = os.path.join(reports_dir, f"forward_remap_run_{ts}.md")

    lines = [
        "# Forward Remap Run Report",
        "",
        f"**Timestamp:** {ts}  ",
        f"**Payload:** `{payload_path}`  ",
        f"**Sequences processed:** {len(run_data)}  ",
        "",
    ]

    for entry in run_data:
        lines.append(f"## {entry['source_path']}")
        lines.append("")
        lines.append(f"- Output: `{entry['out_path']}`")
        if entry.get("template_path"):
            lines.append(f"- Template: `{entry['template_path']}`")
        lines.append(f"- Time offset: {entry.get('time_offset', 0)}s")
        lines.append(f"- Duration: {entry.get('duration', 'full')}")
        lines.append(f"- Frames: {entry['frame_count']}")
        lines.append(f"- Curves written: {entry['curves_written']}")
        lines.append(f"- Missing ARKit sources: {len(entry.get('missing', []))}")
        if entry.get("missing"):
            for m in entry["missing"][:10]:
                lines.append(f"  - `{m}`")
        lines.append("")

        if entry.get("stats"):
            lines.append("### Curve Ranges")
            lines.append("")
            lines.append("| ctrl_expressions curve | min | max | mean | # contributors |")
            lines.append("|------------------------|-----|-----|------|----------------|")
            for cname, s in sorted(entry["stats"].items()):
                lines.append(
                    f"| {cname} | {s['min']:.4f} | {s['max']:.4f} | "
                    f"{s['mean']:.4f} | {s['contributors']}/{s['total']} |"
                )
            lines.append("")

    with open(md_path, "w") as f:
        f.write("\n".join(lines))
    unreal.log(f"{TAG} QA report: {md_path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(asset_paths=None, output_suffix="_OnMH", time_offset=0.0,
         duration=None, template_path=None):
    """Run the forward remap pipeline.

    Args:
        asset_paths: List of UE asset paths (e.g. ["/Game/.../MyAnim"]).
        output_suffix: Suffix for output sequence names.
        time_offset: Start time in seconds (for windowing long sequences).
        duration: Duration in seconds (None = full sequence).
        template_path: UE path to a template sequence to duplicate for output.
            Use when the source is on a non-MH skeleton (e.g. ARKit bake).
            The template should be on the MetaHuman face_archetype_skeleton.
    """
    unreal.log(f"{TAG} === Forward Remap to MetaHuman starting ===")
    unreal.log(
        f"{TAG} Params: suffix={output_suffix}, offset={time_offset}s, "
        f"duration={duration}, template={template_path}"
    )

    payload, payload_path = _load_payload()
    if payload is None:
        return

    forward_index, arkit_needed = _build_forward_index(payload)
    arkit_needed.add("MouthClose")
    arkit_needed.add("JawOpen")

    unreal.log(
        f"{TAG} Forward index: {len(forward_index)} ctrl_expressions targets "
        f"from {len(arkit_needed)} ARKit source curves."
    )

    if not asset_paths:
        selected = unreal.EditorUtilityLibrary.get_selected_assets()
        sequences = [a for a in selected if isinstance(a, unreal.AnimSequence)]
        if not sequences:
            unreal.log_error(f"{TAG} No AnimSequence selected.")
            return
    else:
        sequences = []
        for p in asset_paths:
            a = unreal.load_asset(p)
            if a is None:
                unreal.log_error(f"{TAG} Asset not found: {p}")
            elif not isinstance(a, unreal.AnimSequence):
                unreal.log_error(f"{TAG} Not an AnimSequence: {p}")
            else:
                sequences.append(a)
        if not sequences:
            return

    run_data = []

    for seq_asset in sequences:
        source_path = _asset_path(seq_asset)
        source_name = _asset_name(source_path)
        unreal.log(f"{TAG} ── Processing: {source_name} ──")

        arkit_cache, missing = _read_arkit_curves(
            seq_asset, arkit_needed, time_offset, duration
        )
        if not arkit_cache:
            unreal.log_error(
                f"{TAG} No ARKit curves found on {source_name}. Skipping."
            )
            continue

        ref_curve = next(iter(arkit_cache.values()))
        times = ref_curve[0]
        frame_count = len(times)
        unreal.log(
            f"{TAG} Read {len(arkit_cache)} ARKit curves, {frame_count} frames, "
            f"time range [{times[0]:.4f}, {times[-1]:.4f}]s"
        )

        ctrl_output, stats = _forward_synthesis(
            forward_index, arkit_cache, frame_count
        )
        unreal.log(f"{TAG} Synthesized {len(ctrl_output)} ctrl_expressions curves.")

        lt_curves = _compute_lips_together(arkit_cache, frame_count)
        ctrl_output.update(lt_curves)
        for lt_name in lt_curves:
            vals = lt_curves[lt_name]
            stats[lt_name] = {
                "contributors": 2, "total": 2,
                "min": min(vals), "max": max(vals),
                "mean": sum(vals) / len(vals) if vals else 0,
            }

        out_seq, out_path = _prepare_output(
            source_path, output_suffix, template_path
        )
        if out_seq is None:
            continue

        written = _write_ctrl_curves(out_seq, ctrl_output, times)
        unreal.log(
            f"{TAG} Wrote {written} ctrl_expressions curves to "
            f"{_asset_name(out_path)}."
        )

        EAL.save_asset(out_path)
        unreal.log(f"{TAG} Saved: {out_path}")

        run_data.append({
            "source_path": source_path,
            "out_path": out_path,
            "template_path": template_path,
            "time_offset": time_offset,
            "duration": duration,
            "frame_count": frame_count,
            "curves_written": written,
            "missing": missing,
            "stats": stats,
        })

    if run_data:
        _write_qa_report(run_data, payload_path)

    unreal.log(
        f"{TAG} === Forward Remap complete: "
        f"{len(run_data)}/{len(sequences)} sequences processed ==="
    )


if not globals().get("_FORWARD_REMAP_NO_AUTO_RUN"):
    main()
