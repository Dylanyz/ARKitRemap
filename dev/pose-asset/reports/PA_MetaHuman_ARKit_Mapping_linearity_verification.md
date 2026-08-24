# PoseAsset Linearity Verification

- PoseAsset: `/Game/MetaHumans/Common/Face/ARKit/PA_MetaHuman_ARKit_Mapping`
- Source animation: `/Game/MetaHumans/Common/Face/ARKit/AS_MetaHuman_ARKit_Mapping.AS_MetaHuman_ARKit_Mapping`

## Result

- Status: **likely_linear_runtime_probe_inconclusive**
- Conclusion: The direct PoseAsset runtime probe did not expose readable output curves from Python on a transient `AnimSingleNodeInstance`, but the first uncontaminated source-animation segment sampled cleanly at 0.25/0.5/0.75/1.0 with negligible error. This materially reduces the linearity risk, but it does not fully prove live-node behavior for every pose.

## Runtime Probe

- Status: `runtime_readback_inconclusive`
- AnimInstance: `AnimSingleNodeInstance`
- Reported curve-name count: `0`

| Weight | JawOpen | ctrl_expressions_jaw_open | CTRL_Expressions_Jaw_Open |
|--------|---------|---------------------------|---------------------------|
| 0.25 | 0.0 | 0.0 | 0.0 |
| 0.5 | 0.0 | 0.0 | 0.0 |
| 0.75 | 0.0 | 0.0 | 0.0 |
| 1.0 | 0.0 | 0.0 | 0.0 |

## First-Segment Fractional Probe

- First non-default pose: `EyeBlinkLeft`
- Contributor curve count: `1`
- Global max abs error: `0.0`
- Global mean abs error: `0.0`

| Fraction | Sample time (s) | Max abs error | Mean abs error |
|----------|------------------|---------------|----------------|
| 0.25 | 0.010417 | 0.00000000 | 0.00000000 |
| 0.5 | 0.020833 | 0.00000000 | 0.00000000 |
| 0.75 | 0.031250 | 0.00000000 | 0.00000000 |
| 1.0 | 0.041667 | 0.00000000 | 0.00000000 |

## Property Audit

### PoseAsset
- `parent_asset` = `None`
- `preview_pose_asset` = `None`
- `retarget_source` = `None`
- `retarget_source_asset` = `None`
- `source_animation` = `<Object '/Game/MetaHumans/Common/Face/ARKit/AS_MetaHuman_ARKit_Mapping.AS_MetaHuman_ARKit_Mapping' (0x000001FB3F23CB00) Class 'AnimSequence'>`
- `skeleton` = `<Object '/Game/MetaHumans/Common/Face/Face_Archetype_Skeleton.Face_Archetype_Skeleton' (0x000001FB3F0F0500) Class 'Skeleton'>`

### Source Animation
- `additive_anim_type` = `<AdditiveAnimationType.AAT_NONE: 0>`
- `additive_base_pose_type` = `UNAVAILABLE: AnimSequence: Failed to find property 'additive_base_pose_type' for attribute 'additive_base_pose_type' on 'AnimSequence'`
- `ref_pose_type` = `<AdditiveBasePoseType.ABPT_NONE: 0>`
- `ref_frame_index` = `0`
- `interpolation` = `<AnimInterpolationType.LINEAR: 0>`
- `enable_root_motion` = `False`
