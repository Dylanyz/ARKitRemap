"""Environment bootstrap for the V3 P1/P2 offline harness.

The OpenRigLogic Python bindings we use are the prebuilt ones bundled with the
Poly Hammer Character DNA Blender addon (RigLogic 13.2.5, CPython 3.13 ABI).
They must be run with a Python 3.13 interpreter; Blender 5.2's bundled
standalone python.exe is the reference interpreter:

    "C:\\Program Files\\Blender Foundation\\Blender 5.2\\5.2\\python\\bin\\python.exe"

scipy is not shipped with Blender; install it repo-locally (gitignored) once:

    python.exe -m pip install --target v3/.pydeps scipy

All paths can be overridden via environment variables (ARKITREMAP_BINDINGS_DIR,
ARKITREMAP_DNA_PATH) for other machines.
"""

import os
import sys
from pathlib import Path

V3_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = V3_DIR / "data"
REPORTS_DIR = V3_DIR / "reports"

_DEFAULT_BINDINGS = (
    Path(os.environ.get("APPDATA", ""))
    / "Blender Foundation/Blender/5.2/extensions/api_portal_polyhammer_com"
    / "character_dna/bindings/windows/x64/py313"
)
BINDINGS_DIR = Path(os.environ.get("ARKITREMAP_BINDINGS_DIR", _DEFAULT_BINDINGS))

DNA_PATH = Path(
    os.environ.get(
        "ARKITREMAP_DNA_PATH",
        r"C:\Program Files\Epic Games\UE_5.8\Engine\Plugins\MetaHuman"
        r"\MetaHumanCoreTechLib\Content\ArchetypeDNA\SKM_Face.dna",
    )
)

PYDEPS_DIR = V3_DIR / ".pydeps"


def bootstrap() -> None:
    """Put the bindings and repo-local deps on sys.path. Idempotent."""
    if sys.version_info[:2] != (3, 13):
        raise RuntimeError(
            f"These bindings need CPython 3.13 (got {sys.version.split()[0]}). "
            "Run with Blender 5.2's bundled python.exe — see module docstring."
        )
    for p in (str(BINDINGS_DIR), str(PYDEPS_DIR)):
        if p not in sys.path:
            sys.path.insert(0, p)
    if not BINDINGS_DIR.is_dir():
        raise FileNotFoundError(f"RigLogic bindings not found: {BINDINGS_DIR}")
    if not DNA_PATH.is_file():
        raise FileNotFoundError(f"Archetype DNA not found: {DNA_PATH}")
