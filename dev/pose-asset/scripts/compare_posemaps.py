import json
from collections import defaultdict
from pathlib import Path


PROJECT_ROOT = Path(r"c:\Users\DYLPC\Documents\Unreal Projects\mdr_StrangerThings01")
DATA_DIR = PROJECT_ROOT / ".cursor" / "arkit-remap" / "data" / "pose-asset-mapping" / "extracted"
REPORT_DIR = PROJECT_ROOT / ".cursor" / "arkit-remap" / "reports" / "pose-asset-mapping"
RAW_PATH = DATA_DIR / "PA_MetaHuman_ARKit_Mapping.posemap.raw.json"
ADJ_PATH = DATA_DIR / "PA_MetaHuman_ARKit_Mapping.posemap.json"
OUT_PATH = REPORT_DIR / "PA_MetaHuman_ARKit_Mapping_raw_vs_adjusted.md"


def build_pose_curve_map(records):
    mapping = defaultdict(set)
    for row in records:
        mapping[row["arkitPoseName"]].add(row["sourceMhaCurveName"])
    return mapping


def main():
    raw = json.loads(RAW_PATH.read_text(encoding="utf-8"))
    adj = json.loads(ADJ_PATH.read_text(encoding="utf-8"))
    raw_map = build_pose_curve_map(raw["records"])
    adj_map = build_pose_curve_map(adj["records"])
    poses = sorted(set(raw_map.keys()) | set(adj_map.keys()))
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    lines = ["# PA MetaHuman ARKit Mapping: Raw vs Adjusted", "", "## Summary", ""]
    changed = 0
    unchanged = 0
    total_gained = 0
    total_lost = 0
    rows = []

    for pose in poses:
        raw_set = raw_map.get(pose, set())
        adj_set = adj_map.get(pose, set())
        gained = sorted(raw_set - adj_set)
        lost = sorted(adj_set - raw_set)
        total_gained += len(gained)
        total_lost += len(lost)
        if gained or lost:
            changed += 1
        else:
            unchanged += 1
        rows.append(
            {
                "pose": pose,
                "raw_count": len(raw_set),
                "adj_count": len(adj_set),
                "gained_count": len(gained),
                "lost_count": len(lost),
                "gained": gained,
                "lost": lost,
            }
        )

    lines.extend(
        [
            f"- Total poses compared: `{len(poses)}`",
            f"- Poses with changed contributor set: `{changed}`",
            f"- Poses unchanged: `{unchanged}`",
            f"- Total contributors present only in raw: `{total_gained}`",
            f"- Total contributors present only in adjusted: `{total_lost}`",
            "",
            "## Per-pose contributor counts",
            "",
            "| Pose | Raw | Adjusted | Raw-only | Adjusted-only |",
            "|---|---:|---:|---:|---:|",
        ]
    )

    for row in sorted(rows, key=lambda x: x["pose"].lower()):
        lines.append(
            f"| {row['pose']} | {row['raw_count']} | {row['adj_count']} | {row['gained_count']} | {row['lost_count']} |"
        )

    lines.extend(["", "## Changed poses (details)", ""])
    for row in sorted(rows, key=lambda x: (x["gained_count"] + x["lost_count"]), reverse=True):
        if row["gained_count"] == 0 and row["lost_count"] == 0:
            continue
        lines.append(f"### {row['pose']}")
        lines.append(
            f"- Counts: raw `{row['raw_count']}`, adjusted `{row['adj_count']}`, raw-only `{row['gained_count']}`, adjusted-only `{row['lost_count']}`"
        )
        lines.append(
            f"- Raw-only contributors: `{', '.join(row['gained'])}`" if row["gained"] else "- Raw-only contributors: none"
        )
        lines.append(
            f"- Adjusted-only contributors: `{', '.join(row['lost'])}`" if row["lost"] else "- Adjusted-only contributors: none"
        )
        lines.append("")

    OUT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(str(OUT_PATH))


if __name__ == "__main__":
    main()
