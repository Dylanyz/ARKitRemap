"""Runner: exec arkit_remap.py with an explicit asset path (for remote execution)."""
import unreal, os

_ARKIT_REMAP_NO_AUTO_RUN = True

_script = os.path.join(
    unreal.Paths.project_dir(),
    ".cursor", "arkit-remap", "scripts", "arkit_remap.py",
)
exec(open(_script).read())

main(asset_paths=["/Game/3_FaceAnims/VEC_MHA/AgenticPy/AS_MP_VecDemo1-allkeys"])
