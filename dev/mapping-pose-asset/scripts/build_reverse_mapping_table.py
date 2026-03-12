import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path


PROJECT_ROOT = Path(r"c:\Users\DYLPC\Documents\Unreal Projects\mdr_StrangerThings01")
WORKSPACE_DIR = PROJECT_ROOT / ".cursor" / "arkit-remap" / "mapping-pose-asset"
DATA_DIR = WORKSPACE_DIR / "data"
REPORT_DIR = WORKSPACE_DIR / "reports"

INPUT_ADJUSTED = DATA_DIR / "PA_MetaHuman_ARKit_Mapping.posemap.json"
OUTPUT_REVERSE_JSON = DATA_DIR / "PA_MetaHuman_ARKit_Mapping.reverse_map.json"
OUTPUT_SUMMARY_MD = REPORT_DIR / "PA_MetaHuman_ARKit_Mapping_reverse_map_summary.md"


CORE_ARKIT_52 = {
    "EyeBlinkLeft",
    "EyeLookDownLeft",
    "EyeLookInLeft",
    "EyeLookOutLeft",
    "EyeLookUpLeft",
    "EyeSquintLeft",
    "EyeWideLeft",
    "EyeBlinkRight",
    "EyeLookDownRight",
    "EyeLookInRight",
    "EyeLookOutRight",
    "EyeLookUpRight",
    "EyeSquintRight",
    "EyeWideRight",
    "JawForward",
    "JawLeft",
    "JawRight",
    "JawOpen",
    "MouthClose",
    "MouthFunnel",
    "MouthPucker",
    "MouthLeft",
    "MouthRight",
    "MouthSmileLeft",
    "MouthSmileRight",
    "MouthFrownLeft",
    "MouthFrownRight",
    "MouthDimpleLeft",
    "MouthDimpleRight",
    "MouthStretchLeft",
    "MouthStretchRight",
    "MouthRollLower",
    "MouthRollUpper",
    "MouthShrugLower",
    "MouthShrugUpper",
    "MouthPressLeft",
    "MouthPressRight",
    "MouthLowerDownLeft",
    "MouthLowerDownRight",
    "MouthUpperUpLeft",
    "MouthUpperUpRight",
    "BrowDownLeft",
    "BrowDownRight",
    "BrowInnerUp",
    "BrowOuterUpLeft",
    "BrowOuterUpRight",
    "CheekPuff",
    "CheekSquintLeft",
    "CheekSquintRight",
    "NoseSneerLeft",
    "NoseSneerRight",
    "TongueOut",
}


def classify_pose(pose_name):
    if pose_name == "Default":
        return "default_pose"
    if pose_name in CORE_ARKIT_52:
        return "arkit52"
    if pose_name.startswith("Pose_"):
        return "extended_pose"
    return "other"


def build_reverse_table(records):
    grouped = defaultdict(list)
    for row in records:
        grouped[row["arkitPoseName"]].append(row)

    table = []
    for pose_name in sorted(grouped.keys(), key=lambda x: x.lower()):
        contributors = []
        for row in grouped[pose_name]:
            weight = float(row["weight"])
            contributors.append(
                {
                    "sourceMhaCurveName": row["sourceMhaCurveName"],
                    "weight": round(weight, 6),
                    "absWeight": round(abs(weight), 6),
                }
            )

        contributors.sort(key=lambda x: (-x["absWeight"], x["sourceMhaCurveName"]))

        abs_sum = sum(item["absWeight"] for item in contributors)
        signed_sum = sum(item["weight"] for item in contributors)

        for rank, item in enumerate(contributors, start=1):
            item["rankByAbsWeight"] = rank
            if abs_sum > 0.0:
                item["normalizedByAbsWeight"] = round(item["absWeight"] / abs_sum, 6)
            else:
                item["normalizedByAbsWeight"] = 0.0

        dominant = contributors[0]["sourceMhaCurveName"] if contributors else None
        table.append(
            {
                "arkitPoseName": pose_name,
                "poseClass": classify_pose(pose_name),
                "contributorCount": len(contributors),
                "weightStats": {
                    "signedSum": round(signed_sum, 6),
                    "absSum": round(abs_sum, 6),
                    "maxAbsWeight": round(contributors[0]["absWeight"], 6) if contributors else 0.0,
                    "dominantSourceMhaCurveName": dominant,
                },
                "contributors": contributors,
            }
        )
    return table


def build_markdown_summary(payload):
    table = payload["reverseMappingTable"]
    by_class = payload["reverseMappingTableByClass"]

    def append_table(lines, title, rows):
        lines.extend(
            [
                f"## {title}",
                "",
                "| Target Pose | Class | Contributors | Dominant Source | Top Contributors (up to 4) |",
                "|---|---|---:|---|---|",
            ]
        )
        for row in rows:
            top = ", ".join(
                f"{c['sourceMhaCurveName']} ({c['weight']})" for c in row["contributors"][:4]
            )
            lines.append(
                "| {pose} | {pose_class} | {count} | {dominant} | {top} |".format(
                    pose=row["arkitPoseName"],
                    pose_class=row["poseClass"],
                    count=row["contributorCount"],
                    dominant=row["weightStats"]["dominantSourceMhaCurveName"] or "-",
                    top=top if top else "-",
                )
            )
        lines.append("")
    lines = [
        "# PA MetaHuman ARKit Mapping: Reverse Map Summary",
        "",
        "## Purpose",
        "",
        "Derived reverse mapping table from the baseline-adjusted posemap dataset.",
        "Use this as the canonical input for weighted MHA->ARKit remap logic.",
        "",
        "## Snapshot",
        "",
        f"- Generated at (UTC): `{payload['generatedAtUtc']}`",
        f"- Source dataset: `{payload['sourceAdjustedDataset']}`",
        f"- Total pose targets: `{payload['summary']['totalPoseTargets']}`",
        f"- ARKit 52 targets found: `{payload['summary']['arkit52Targets']}`",
        f"- ARKit 52 targets missing: `{len(payload['summary']['missingArkit52Targets'])}`",
        f"- Extended pose targets found: `{payload['summary']['extendedPoseTargets']}`",
        f"- Default/other targets found: `{payload['summary']['defaultOrOtherTargets']}`",
        "",
    ]
    if payload["summary"]["missingArkit52Targets"]:
        lines.extend(
            [
                "### Missing ARKit 52 Targets",
                "",
                "- "
                + ", ".join(
                    f"`{name}`" for name in payload["summary"]["missingArkit52Targets"]
                ),
                "",
            ]
        )
    append_table(lines, "Core ARKit 52 Targets", by_class["arkit52"])
    append_table(lines, "Extended Pose Targets", by_class["extended_pose"])
    append_table(lines, "Default / Other Targets", by_class["other_targets"])

    lines.extend(
        [
            "## Full Combined View",
            "",
            "This dataset is also available as a single ordered list in `reverseMappingTable`",
            "inside the JSON artifact.",
            "",
            f"- Combined entries: `{len(table)}`",
            "",
        ]
    )
    return "\n".join(lines)


def main():
    adjusted = json.loads(INPUT_ADJUSTED.read_text(encoding="utf-8"))
    records = adjusted.get("records", [])

    reverse_table = build_reverse_table(records)

    counts = defaultdict(int)
    for row in reverse_table:
        counts[row["poseClass"]] += 1
    found_arkit_targets = {
        row["arkitPoseName"] for row in reverse_table if row["poseClass"] == "arkit52"
    }
    missing_arkit_targets = sorted(CORE_ARKIT_52 - found_arkit_targets)

    payload = {
        "assetPath": adjusted.get("assetPath"),
        "sourceAdjustedDataset": str(INPUT_ADJUSTED),
        "generatedAtUtc": datetime.now(timezone.utc).isoformat(),
        "generationMethod": "group_adjusted_records_by_arkit_pose",
        "notes": [
            "Uses baseline-adjusted posemap as source of truth for reverse map.",
            "Preserves all contributors per target (no 1:1 collapsing).",
            "Includes both signed and abs-normalized weight metadata.",
        ],
        "summary": {
            "totalPoseTargets": len(reverse_table),
            "arkit52Targets": counts["arkit52"],
            "missingArkit52Targets": missing_arkit_targets,
            "extendedPoseTargets": counts["extended_pose"],
            "defaultOrOtherTargets": counts["default_pose"] + counts["other"],
            "sourceRecordCount": len(records),
        },
        "reverseMappingTableByClass": {
            "arkit52": [row for row in reverse_table if row["poseClass"] == "arkit52"],
            "extended_pose": [row for row in reverse_table if row["poseClass"] == "extended_pose"],
            "other_targets": [
                row
                for row in reverse_table
                if row["poseClass"] not in ("arkit52", "extended_pose")
            ],
        },
        "reverseMappingTable": reverse_table,
    }

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    OUTPUT_REVERSE_JSON.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    OUTPUT_SUMMARY_MD.write_text(build_markdown_summary(payload), encoding="utf-8")

    print(str(OUTPUT_REVERSE_JSON))
    print(str(OUTPUT_SUMMARY_MD))


if __name__ == "__main__":
    main()
