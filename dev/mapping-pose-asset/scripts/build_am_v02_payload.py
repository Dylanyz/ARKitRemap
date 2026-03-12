import json
from datetime import datetime, timezone
from pathlib import Path


PROJECT_ROOT = Path(r"c:\Users\DYLPC\Documents\Unreal Projects\mdr_StrangerThings01")
WORKSPACE_DIR = PROJECT_ROOT / ".cursor" / "arkit-remap" / "mapping-pose-asset"
DATA_DIR = WORKSPACE_DIR / "data"
REPORT_DIR = WORKSPACE_DIR / "reports"

INPUT_REVERSE_MAP = DATA_DIR / "PA_MetaHuman_ARKit_Mapping.reverse_map.json"
OUTPUT_PAYLOAD = DATA_DIR / "AM_ArKitRemap_v02.mapping_payload.json"
OUTPUT_SUMMARY = REPORT_DIR / "AM_ArKitRemap_v02_mapping_payload_summary.md"

DEFAULT_CALIBRATION = {
    "global": {
        "scale": 1.0,
        "offset": 0.0,
        "clampMin": 0.0,
        "clampMax": 1.0,
    },
    "mouthClose": {
        "enabled": True,
        "lipsTogetherSourceCurve": "CTRL_Expressions_Mouth_Lips_Together_UL",
        "jawOpenSourceCurve": "JawOpen",
        "scale": 1.0,
        "offset": 0.0,
        "clampMin": 0.0,
        "clampMax": 0.3,
    },
    "perCurveOverrides": {},
}


def _pack_section(rows):
    compact = []
    for row in rows:
        compact.append(
            {
                "target": row["arkitPoseName"],
                "contributors": [
                    {
                        "source": c["sourceMhaCurveName"],
                        "weight": c["weight"],
                    }
                    for c in row.get("contributors", [])
                ],
                "contributorCount": row.get("contributorCount", 0),
                "dominantSource": row.get("weightStats", {}).get("dominantSourceMhaCurveName"),
                "absWeightSum": row.get("weightStats", {}).get("absSum", 0.0),
            }
        )
    return compact


def _build_summary(payload):
    missing = payload["missingArkit52Targets"]
    lines = [
        "# AM_ArKitRemap_v02 Mapping Payload Summary",
        "",
        "## Snapshot",
        "",
        f"- Generated at (UTC): `{payload['generatedAtUtc']}`",
        f"- Source reverse map: `{payload['sourceReverseMap']}`",
        f"- ARKit52 targets in payload: `{len(payload['arkit52'])}`",
        f"- Extended targets in payload: `{len(payload['extended_pose'])}`",
        f"- Other targets in payload: `{len(payload['other_targets'])}`",
        f"- Missing ARKit52 targets: `{len(missing)}`",
        "",
    ]
    if missing:
        lines.extend(
            [
                "## Missing ARKit52 Targets",
                "",
                "- " + ", ".join(f"`{name}`" for name in missing),
                "",
            ]
        )
    lines.extend(
        [
            "## Calibration Defaults",
            "",
            "- Global clamp: `0.0..1.0`",
            "- MouthClose explicit clamp: `0.0..0.3`",
            "- Per-curve overrides: empty by default (opt-in)",
            "",
        ]
    )
    return "\n".join(lines)


def main():
    reverse_map = json.loads(INPUT_REVERSE_MAP.read_text(encoding="utf-8"))
    by_class = reverse_map["reverseMappingTableByClass"]
    summary = reverse_map["summary"]

    payload = {
        "payloadVersion": "am_v02_compact_1",
        "generatedAtUtc": datetime.now(timezone.utc).isoformat(),
        "sourceReverseMap": str(INPUT_REVERSE_MAP),
        "sourceReverseMapGeneratedAtUtc": reverse_map.get("generatedAtUtc"),
        "missingArkit52Targets": summary.get("missingArkit52Targets", []),
        "arkit52": _pack_section(by_class.get("arkit52", [])),
        "extended_pose": _pack_section(by_class.get("extended_pose", [])),
        "other_targets": _pack_section(by_class.get("other_targets", [])),
        "calibrationDefaults": DEFAULT_CALIBRATION,
        "notes": [
            "Compact payload for AM_ArKitRemap_v02 weighted synthesis.",
            "Contributors preserve reverse-map weights (no top-1 collapse).",
            "MouthClose is expected to use explicit branch logic because it is missing from arkit52 extraction.",
        ],
    }

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    OUTPUT_PAYLOAD.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    OUTPUT_SUMMARY.write_text(_build_summary(payload), encoding="utf-8")

    print(str(OUTPUT_PAYLOAD))
    print(str(OUTPUT_SUMMARY))


if __name__ == "__main__":
    main()
