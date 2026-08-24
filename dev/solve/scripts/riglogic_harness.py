"""RigLogic evaluation harness over the archetype face DNA (V3 P1).

Wraps the prebuilt OpenRigLogic bindings so the rest of the pipeline can talk
in MHA curve names (`CTRL_expressions_jawOpen`, the Live Link / PoseAsset
spelling) and get back joint-output deformation vectors.

Joint-output layout (verified against Poly Hammer's rig_instance.py and the
RigLogic docs): flat float array, 9 attributes per joint —
[tx ty tz (cm), rx ry rz (degrees, euler), sx sy sz (delta scale)] — deltas
from the rest pose. Archetype: 870 joints -> 7830 dims. The rig is joints-only
(no blendshapes); 82 animated maps are exposed separately.

Name matching is case-insensitive: PoseAsset extraction lowercased curve names
(FNames are case-insensitive), so `ctrl_expressions_eyeblinkl` and
`CTRL_expressions_eyeBlinkL` both resolve to DNA raw control
`CTRL_expressions.eyeBlinkL`.
"""

from __future__ import annotations

import numpy as np

import p1_env

p1_env.bootstrap()

import dna  # noqa: E402
import riglogic  # noqa: E402

ATTRS_PER_JOINT = 9


def _mha_key(raw_control_name: str) -> str:
    """DNA raw control name -> case-folded MHA curve key ('.' -> '_')."""
    return raw_control_name.replace(".", "_").lower()


class RigHarness:
    def __init__(self, dna_path=None):
        path = str(dna_path or p1_env.DNA_PATH)
        stream = dna.FileStream(
            path, dna.FileStream.AccessMode_Read, dna.FileStream.OpenMode_Binary
        )
        self.reader = dna.BinaryStreamReader(stream, dna.DataLayer_All)
        self.reader.read()
        self.rig = riglogic.RigLogic(self.reader, riglogic.Configuration(), None)
        self.instance = riglogic.RigInstance(rigLogic=self.rig, memRes=None)

        r = self.reader
        self.raw_names = [r.getRawControlName(i) for i in range(r.getRawControlCount())]
        self.joint_names = [r.getJointName(i) for i in range(r.getJointCount())]
        self.map_names = [r.getAnimatedMapName(i) for i in range(r.getAnimatedMapCount())]
        self.n_raw = len(self.raw_names)
        self.n_joint_attrs = len(self.joint_names) * ATTRS_PER_JOINT

        # expression controls only (the 12 neck/head .q* quat channels are
        # bone-driven, never part of the MHA curve stream)
        self.expr_indices = [
            i for i, n in enumerate(self.raw_names) if n.startswith("CTRL_expressions.")
        ]
        self.key_to_raw_index = {_mha_key(self.raw_names[i]): i for i in self.expr_indices}

        self._neutral = None

    # ---- name mapping ----

    def resolve(self, curve_names) -> tuple[dict, list]:
        """Map MHA curve names -> raw control indices.

        Returns (mapping, unmatched): mapping is {curve_name: raw_index};
        unmatched keeps original spellings of names with no DNA counterpart.
        """
        mapping, unmatched = {}, []
        for name in curve_names:
            idx = self.key_to_raw_index.get(name.lower())
            if idx is None:
                unmatched.append(name)
            else:
                mapping[name] = idx
        return mapping, unmatched

    def control_vector(self, curve_values: dict, clamp=True) -> tuple[np.ndarray, list]:
        """MHA {curve_name: value} dict -> full raw-control vector.

        Unmatched names are returned, not raised: the PoseAsset carries curves
        (wrinkle maps, mesh shapes, ctrl_riglogic_offon) that are outputs, not
        rig inputs, and callers are expected to have filtered or to log them.
        """
        vec = np.zeros(self.n_raw, dtype=np.float64)
        unmatched = []
        for name, value in curve_values.items():
            idx = self.key_to_raw_index.get(name.lower())
            if idx is None:
                unmatched.append(name)
                continue
            vec[idx] = min(max(float(value), 0.0), 1.0) if clamp else float(value)
        return vec, unmatched

    # ---- evaluation ----

    def evaluate(self, control_vec: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """Evaluate a full raw-control vector -> (joint_outputs, animated_maps).

        Joint outputs are RigLogic's deltas from rest pose (not relative to any
        pose); use `delta_from_neutral` when a neutral-relative vector is wanted.
        """
        inst = self.instance
        for i in range(self.n_raw):
            inst.setRawControl(i, float(control_vec[i]))
        self.rig.calculate(inst)
        joints = np.asarray(inst.getJointOutputs(), dtype=np.float64).copy()
        maps = np.asarray(inst.getAnimatedMapOutputs(), dtype=np.float64).copy()
        return joints, maps

    @property
    def neutral(self) -> tuple[np.ndarray, np.ndarray]:
        """Outputs for the all-zero control vector (cached)."""
        if self._neutral is None:
            self._neutral = self.evaluate(np.zeros(self.n_raw))
        return self._neutral

    def evaluate_curves(self, curve_values: dict) -> tuple[np.ndarray, np.ndarray, list]:
        vec, unmatched = self.control_vector(curve_values)
        joints, maps = self.evaluate(vec)
        return joints, maps, unmatched

    def per_joint_norms(self, joint_delta: np.ndarray) -> np.ndarray:
        return np.linalg.norm(joint_delta.reshape(-1, ATTRS_PER_JOINT), axis=1)
