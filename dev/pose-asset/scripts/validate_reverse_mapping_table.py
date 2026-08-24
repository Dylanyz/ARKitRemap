import json
import sys
from datetime import datetime, timezone
from pathlib import Path


PROJECT_ROOT = Path(r"c:\Users\DYLPC\Documents\Unreal Projects\mdr_StrangerThings01")
WORKSPACE_DIR = PROJECT_ROOT / ".cursor" / "arkit-remap" / "mapping-pose-asset"
DATA_DIR = WORKSPACE_DIR / "data"
REPORT_DIR = WORKSPACE_DIR / "reports"

INPUT_REVERSE_MAP = DATA_DIR / "PA_MetaHuman_ARKit_Mapping.reverse_map.json"
OUTPUT_VALIDATION_MD = REPORT_DIR / "PA_MetaHuman_ARKit_Mapping_reverse_map_validation.md"

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


def check(condition, label, failures):
    if condition:
        return f"- PASS: {label}"
    failures.append(label)
    return f"- FAIL: {label}"


def main():
    payload = json.loads(INPUT_REVERSE_MAP.read_text(encoding="utf-8"))
    summary = payload.get("summary", {})
    table = payload.get("reverseMappingTable", [])
    by_class = payload.get("reverseMappingTableByClass", {})

    failures = []
    warnings = []

    lines = [
        "# PA MetaHuman ARKit Mapping: Reverse Map Validation",
        "",
        f"- Generated at (UTC): `{datetime.now(timezone.utc).isoformat()}`",
        f"- Source: `{INPUT_REVERSE_MAP}`",
        "",
        "## Structural Checks",
        "",
    ]

    lines.append(
        check(
            isinstance(table, list) and len(table) == summary.get("totalPoseTargets"),
            "summary.totalPoseTargets matches reverseMappingTable length",
            failures,
        )
    )

    arkit_rows = by_class.get("arkit52", [])
    ext_rows = by_class.get("extended_pose", [])
    other_rows = by_class.get("other_targets", [])

    lines.append(
        check(
            isinstance(arkit_rows, list)
            and isinstance(ext_rows, list)
            and isinstance(other_rows, list),
            "reverseMappingTableByClass sections exist and are lists",
            failures,
        )
    )

    lines.append(
        check(
            len(arkit_rows) == summary.get("arkit52Targets"),
            "summary.arkit52Targets matches reverseMappingTableByClass.arkit52 length",
            failures,
        )
    )
    lines.append(
        check(
            len(ext_rows) == summary.get("extendedPoseTargets"),
            "summary.extendedPoseTargets matches reverseMappingTableByClass.extended_pose length",
            failures,
        )
    )
    lines.append(
        check(
            len(other_rows) == summary.get("defaultOrOtherTargets"),
            "summary.defaultOrOtherTargets matches reverseMappingTableByClass.other_targets length",
            failures,
        )
    )

    combined_len = len(arkit_rows) + len(ext_rows) + len(other_rows)
    lines.append(
        check(
            combined_len == len(table),
            "combined by-class sections equal reverseMappingTable length",
            failures,
        )
    )

    lines.extend(["", "## ARKit Coverage Checks", ""])

    found_arkit = {row.get("arkitPoseName") for row in arkit_rows}
    expected_missing = sorted(CORE_ARKIT_52 - found_arkit)
    reported_missing = sorted(summary.get("missingArkit52Targets", []))

    lines.append(
        check(
            expected_missing == reported_missing,
            "summary.missingArkit52Targets is consistent with discovered arkit52 targets",
            failures,
        )
    )

    duplicate_targets = []
    seen = set()
    for row in arkit_rows:
        pose = row.get("arkitPoseName")
        if pose in seen:
            duplicate_targets.append(pose)
        seen.add(pose)

    lines.append(
        check(
            len(duplicate_targets) == 0,
            "no duplicate target entries inside arkit52 section",
            failures,
        )
    )

    if reported_missing:
        warnings.append(
            "Missing ARKit targets detected: " + ", ".join(f"`{x}`" for x in reported_missing)
        )

    lines.extend(["", "## Row Integrity Checks", ""])

    row_integrity_ok = True
    norm_issues = 0
    for row in table:
        contributors = row.get("contributors", [])
        if row.get("contributorCount") != len(contributors):
            row_integrity_ok = False

        abs_sum = sum(abs(float(c.get("weight", 0.0))) for c in contributors)
        norm_sum = sum(float(c.get("normalizedByAbsWeight", 0.0)) for c in contributors)
        if contributors and abs_sum > 0:
            if abs(norm_sum - 1.0) > 0.01:
                norm_issues += 1

    lines.append(check(row_integrity_ok, "contributorCount equals contributors length for all rows", failures))
    lines.append(
        check(
            norm_issues == 0,
            "normalizedByAbsWeight approximately sums to 1.0 per populated row",
            failures,
        )
    )

    lines.extend(["", "## Outcome", ""])
    if failures:
        lines.append(f"- Result: FAIL (`{len(failures)}` check(s) failed)")
    else:
        lines.append("- Result: PASS (all structural checks passed)")

    if warnings:
        lines.extend(["", "## Warnings", ""])
        lines.extend(f"- {w}" for w in warnings)

    lines.append("")

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_VALIDATION_MD.write_text("\n".join(lines), encoding="utf-8")
    print(str(OUTPUT_VALIDATION_MD))

    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
