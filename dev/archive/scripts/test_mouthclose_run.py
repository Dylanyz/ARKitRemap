"""Test runner: execute arkit_remap pipeline on AS_MP_VecDemo1-allkeys
by asset path, then log MouthClose stats for validation."""

import sys
import os

_ARKIT_REMAP_NO_AUTO_RUN = True
globals()["_ARKIT_REMAP_NO_AUTO_RUN"] = True

project_dir = __import__("unreal").Paths.project_dir()
scripts_dir = os.path.join(project_dir, ".cursor", "arkit-remap", "scripts")
if scripts_dir not in sys.path:
    sys.path.insert(0, scripts_dir)

import importlib
import arkit_remap
importlib.reload(arkit_remap)

arkit_remap.main(asset_paths=[
    "/Game/3_FaceAnims/VEC_MHA/AgenticPy/AS_MP_VecDemo1-allkeys"
])
