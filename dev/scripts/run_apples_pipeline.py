"""Apples-to-Apples Comparison Pipeline Runner

Orchestrates Steps 2-4 of the comparison plan:
  Step 2: Run arkit_remap.py on apples/AS_MP_VecDemo1-allkeys -> _ARKit
  Step 3: Forward-pass allkeys_ARKit -> allkeys_ARKit_OnMH (ctrl_expressions)
  Step 4: Forward-pass Vec-ARKITBAKED-T34_60fps-02 (offset 345.4s, 24.15s)
          -> Vec-ARKITBAKED-excerpt_OnMH (ctrl_expressions)

Run inside Unreal via:
    py exec(open(unreal.Paths.project_dir() + ".cursor/arkit-remap/scripts/run_apples_pipeline.py").read())
"""

import unreal
import os
import sys

TAG = "[Apples Pipeline]"
APPLES = "/Game/3_FaceAnims/VEC_MHA/AgenticPy/apples"

ALLKEYS_SRC = f"{APPLES}/AS_MP_VecDemo1-allkeys"
ALLKEYS_ARKIT = f"{APPLES}/AS_MP_VecDemo1-allkeys_ARKit"
ONMH_TEMPLATE = f"{APPLES}/AS_MP_VecDemo1-OnMH"
ARKITBAKED_SRC = f"{APPLES}/Vec-ARKITBAKED-T34_60fps-02"

ARKIT_OFFSET = 345.4
ARKIT_DURATION = 24.15

script_dir = os.path.dirname(os.path.abspath(__file__)) if '__file__' in dir() else os.path.join(
    unreal.Paths.project_dir(), ".cursor", "arkit-remap", "scripts"
)
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)


def step2_remap_allkeys():
    """Run the ARKit remap on the allkeys copy in apples/."""
    unreal.log(f"{TAG} ═══ Step 2: Remap allkeys -> ARKit ═══")

    globals()["_ARKIT_REMAP_NO_AUTO_RUN"] = True
    import importlib
    import arkit_remap
    importlib.reload(arkit_remap)

    arkit_remap.main(asset_paths=[ALLKEYS_SRC])
    unreal.log(f"{TAG} Step 2 complete.")


def step3_forward_B():
    """Forward-pass our remap output to produce OnMH ctrl_expressions."""
    unreal.log(f"{TAG} ═══ Step 3: Forward-pass allkeys_ARKit -> OnMH ═══")

    globals()["_FORWARD_REMAP_NO_AUTO_RUN"] = True
    import importlib
    import forward_remap_to_mh
    importlib.reload(forward_remap_to_mh)

    forward_remap_to_mh.main(
        asset_paths=[ALLKEYS_ARKIT],
        output_suffix="_OnMH",
        time_offset=0.0,
        duration=None,
        template_path=ONMH_TEMPLATE,  # must be on face_archetype_skeleton
    )
    unreal.log(f"{TAG} Step 3 complete.")


def step4_forward_C():
    """Forward-pass real iPhone ARKit bake (windowed) to produce OnMH."""
    unreal.log(f"{TAG} ═══ Step 4: Forward-pass ARKit bake -> OnMH ═══")

    globals()["_FORWARD_REMAP_NO_AUTO_RUN"] = True
    import importlib
    import forward_remap_to_mh
    importlib.reload(forward_remap_to_mh)

    forward_remap_to_mh.main(
        asset_paths=[ARKITBAKED_SRC],
        output_suffix="_OnMH",
        time_offset=ARKIT_OFFSET,
        duration=ARKIT_DURATION,
        template_path=ONMH_TEMPLATE,
    )
    unreal.log(f"{TAG} Step 4 complete.")


def run_all():
    unreal.log(f"{TAG} ═══════════════════════════════════════")
    unreal.log(f"{TAG} Starting Apples-to-Apples Pipeline")
    unreal.log(f"{TAG} ═══════════════════════════════════════")

    step2_remap_allkeys()
    step3_forward_B()
    step4_forward_C()

    unreal.log(f"{TAG} ═══════════════════════════════════════")
    unreal.log(f"{TAG} Pipeline complete. Output sequences:")
    unreal.log(f"{TAG}   A: {ONMH_TEMPLATE} (ground truth, no conversion)")
    unreal.log(f"{TAG}   B: {ALLKEYS_ARKIT}_OnMH (remap round-trip)")
    unreal.log(f"{TAG}   C: {ARKITBAKED_SRC}_OnMH (real iPhone ARKit)")
    unreal.log(f"{TAG} ═══════════════════════════════════════")


run_all()
