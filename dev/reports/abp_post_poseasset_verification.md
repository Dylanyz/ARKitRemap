# ABP_MH_LiveLink Post-PoseAsset Verification

- Blueprint: `/Game/MetaHumans/Common/Animation/ABP_MH_LiveLink`
- Test sequence: `/Game/3_FaceAnims/VEC_MHA/AgenticPy/AS_MP_VecDemo1-allkeys`

## Result

- Status: **verified_post_poseasset_overrides_not_baked**
- Conclusion: The representative baked MHA sequence contains none of the jaw/teeth curves written by the post-PoseAsset nodes, and the blueprint class defaults for `JawOpenAlpha` / `TeethShowAlpha` are both 0.0. This indicates those nodes behave as runtime/manual override paths rather than baked signals that the reverse remapper must reconstruct.

## Baked Sequence Evidence

- Missing alpha-like curves on bake: `jawopenalpha, teethshowalpha, jaw_open_alpha, teeth_show_alpha, JawOpenAlpha, TeethShowAlpha`

| Curve | Exists | Min | Max | Mean | Non-zero keys |
|------|--------|-----|-----|------|---------------|
| ctrl_expressions_jaw_open | no | 0.000000 | 0.000000 | 0.000000 | 0 |
| ctrl_expressions_mouth_lower_lip_depress_l | no | 0.000000 | 0.000000 | 0.000000 | 0 |
| ctrl_expressions_mouth_lower_lip_depress_r | no | 0.000000 | 0.000000 | 0.000000 | 0 |
| ctrl_expressions_mouth_upper_lip_raise_l | no | 0.000000 | 0.000000 | 0.000000 | 0 |
| ctrl_expressions_mouth_upper_lip_raise_r | no | 0.000000 | 0.000000 | 0.000000 | 0 |
| ctrl_expressions_mouth_corner_pull_l | no | 0.000000 | 0.000000 | 0.000000 | 0 |
| ctrl_expressions_mouth_corner_pull_r | no | 0.000000 | 0.000000 | 0.000000 | 0 |
| ctrl_expressions_mouth_stretch_l | no | 0.000000 | 0.000000 | 0.000000 | 0 |
| ctrl_expressions_mouth_stretch_r | no | 0.000000 | 0.000000 | 0.000000 | 0 |

## Blueprint Defaults Probe

- Loaded class path: `/Game/MetaHumans/Common/Animation/ABP_MH_LiveLink.ABP_MH_LiveLink_C`
- Default object class: `AnimInstance`
- `JawOpenAlpha` = `0.0`
- `jaw_open_alpha` = `ERROR: AnimInstance: Failed to find property 'jaw_open_alpha' for attribute 'jaw_open_alpha' on 'ABP_MH_LiveLink_C'`
- `TeethShowAlpha` = `0.0`
- `teeth_show_alpha` = `ERROR: AnimInstance: Failed to find property 'teeth_show_alpha' for attribute 'teeth_show_alpha' on 'ABP_MH_LiveLink_C'`
