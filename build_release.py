"""Build the ARKit Remap release zip from the release/ folder.

Run from the repo root:
    python build_release.py

Produces: dist/ARKitRemap-v2.0.0.zip
"""

import os
import zipfile
from pathlib import Path

VERSION = "2.0.0"

RELEASE_DIR = Path("release")
DIST_DIR = Path("dist")
ZIP_NAME = f"ARKitRemap-v{VERSION}.zip"

RELEASE_FILES = [
    "arkit_remap.py",
    "arkit_remap_payload.json",
    "init_unreal.py",
    "arkit_remap_menu.py",
    "temporal_smoothing.py",
    "README.md",
]


def main():
    DIST_DIR.mkdir(exist_ok=True)
    zip_path = DIST_DIR / ZIP_NAME

    missing = [f for f in RELEASE_FILES if not (RELEASE_DIR / f).exists()]
    if missing:
        print(f"ERROR: Missing release files: {missing}")
        return 1

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for fname in RELEASE_FILES:
            src = RELEASE_DIR / fname
            zf.write(src, fname)
            print(f"  added {fname} ({src.stat().st_size:,} bytes)")

    print(f"\nBuilt: {zip_path} ({zip_path.stat().st_size:,} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
