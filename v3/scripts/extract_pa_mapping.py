"""V3 P0: fresh extraction of PA_MetaHuman_ARKit_Mapping (ARKit -> MHA forward table).

Runs inside the UE editor (unreal-py / remote execution):
    py exec(open(r"<repo>/v3/scripts/extract_pa_mapping.py").read())

Reads Epic's PoseAsset + its source AnimSequence and dumps every pose sample to
v3/data/pa_mapping.json. No interpretation, no filtering beyond exact zeros.
Ground rule: this is the ONLY mapping source (see plans/arkit-remap-v3-plan.md).

Verified structure of AS_MetaHuman_ARKit_Mapping (UE 5.8.1, 2026-08-14):
- 24 fps, 65 frames, 1172 float curves.
- Pose i <-> frame i (time i/24) for the on-grid poses: index 0 = Default,
  indices 1..51 = 51 ARKit poses (MouthClose has NO pose - it is derived at
  runtime in ABP_MH_LiveLink, matching knowledge-base Section C/D).
- Indices 52..65 = Pose_4..Pose_17 (MetaHuman-internal extras) keyed at
  off-grid times with no reliable index<->time rule; their samples are dumped
  verbatim under offGridSamples instead of being force-assigned.
- Spot checks: CTRL_expressions_eyeBlinkL keys only at frame 1 (EyeBlinkLeft),
  CTRL_expressions_jawOpen only at frame 18 (JawOpen).
"""

import json
import os
from collections import OrderedDict

import unreal

PA_PATH = "/Game/MetaHumans/Common/Face/ARKit/PA_MetaHuman_ARKit_Mapping"
AS_PATH = "/Game/MetaHumans/Common/Face/ARKit/AS_MetaHuman_ARKit_Mapping"
OUT_PATH = r"C:\Users\DYLPC\Desktop\Coding\ARKitRemap\v3\data\pa_mapping.json"
FPS = 24.0
FRAME_TOLERANCE = 0.002
GRID_POSE_COUNT = 53

pose_asset = unreal.load_asset(PA_PATH)
anim = unreal.load_asset(AS_PATH)
if not pose_asset or not anim:
    raise RuntimeError("Could not load PA/AS assets: %s %s" % (pose_asset, anim))

pose_names = [str(n) for n in pose_asset.get_pose_names()]

curve_names = [
    str(n)
    for n in unreal.AnimationLibrary.get_animation_curve_names(
        anim, unreal.RawCurveTrackTypes.RCT_FLOAT
    )
]

frame_samples = {}
offgrid_samples = OrderedDict()
for cn in curve_names:
    times, values = unreal.AnimationLibrary.get_float_keys(anim, cn)
    for t, v in zip(times, values):
        t = float(t)
        v = float(v)
        f = t * FPS
        if abs(f - round(f)) < FRAME_TOLERANCE:
            if v != 0.0:
                frame_samples.setdefault(int(round(f)), OrderedDict())[cn] = v
        else:
            if v != 0.0:
                offgrid_samples.setdefault(round(t, 6), OrderedDict())[cn] = v

warnings = []
poses = OrderedDict()
for i in range(min(GRID_POSE_COUNT, len(pose_names))):
    pname = pose_names[i]
    curves = frame_samples.get(i, OrderedDict())
    if i > 0 and not curves:
        warnings.append("pose %d (%s) has no nonzero curves" % (i, pname))
    poses[pname] = OrderedDict([("frame", i), ("curves", curves)])

stray_frames = sorted(set(frame_samples) - set(range(GRID_POSE_COUNT)))
if stray_frames:
    warnings.append("nonzero on-grid samples beyond pose frames: %s" % stray_frames)

default_curves = poses.get("Default", {}).get("curves", {})

adjusted = OrderedDict()
for pname, entry in poses.items():
    if pname == "Default":
        continue
    adj = OrderedDict()
    keys = set(entry["curves"]) | set(default_curves)
    for cn in sorted(keys):
        v = entry["curves"].get(cn, 0.0) - default_curves.get(cn, 0.0)
        if abs(v) > 1e-9:
            adj[cn] = v
    adjusted[pname] = adj

nonzero_raw = sum(len(e["curves"]) for e in poses.values())
nonzero_adj = sum(len(a) for a in adjusted.values())

result = OrderedDict()
result["metadata"] = OrderedDict(
    [
        ("extractedFrom", {"poseAsset": PA_PATH, "sourceAnimation": AS_PATH}),
        ("engineVersion", unreal.SystemLibrary.get_engine_version()),
        ("extractionScript", "v3/scripts/extract_pa_mapping.py"),
        ("fps", FPS),
        ("poseToTimeRule", "pose index i <-> frame i (time i/24) for indices 0..51"),
        ("poseIndexLayout", "0=Default, 1..51=ARKit (no MouthClose pose), 52=Pose_4 (on-grid), 53..65=Pose_5..Pose_17 (unassigned, see offGridSamples)"),
        ("baselineRule", "adjusted[pose][curve] = raw[pose][curve] - raw[Default][curve]"),
        ("zeroPolicy", "exact zeros omitted in raw; |v|<=1e-9 omitted in adjusted"),
    ]
)
result["summary"] = OrderedDict(
    [
        ("poseCount", len(pose_names)),
        ("gridPoseCount", len(poses)),
        ("curveCount", len(curve_names)),
        ("nonzeroRawRecords", nonzero_raw),
        ("nonzeroAdjustedRecords", nonzero_adj),
        ("offGridSampleTimes", len(offgrid_samples)),
        ("warnings", warnings),
    ]
)
result["poseNames"] = pose_names
result["raw"] = poses
result["adjusted"] = adjusted
result["offGridSamples"] = offgrid_samples

os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
with open(OUT_PATH, "w", encoding="utf-8") as f:
    json.dump(result, f, indent=1)

print(
    "PA extraction complete: %d grid poses (of %d), %d curves, %d raw / %d adjusted nonzero, %d off-grid times -> %s"
    % (len(poses), len(pose_names), len(curve_names), nonzero_raw, nonzero_adj, len(offgrid_samples), OUT_PATH)
)
for w in warnings:
    print("WARNING:", w)