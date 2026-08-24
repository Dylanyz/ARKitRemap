# PA MetaHuman ARKit Mapping: Reverse Map Validation

- Generated at (UTC): `2026-03-11T19:04:59.812750+00:00`
- Source: `c:\Users\DYLPC\Documents\Unreal Projects\mdr_StrangerThings01\.cursor\arkit-remap\mapping-pose-asset\data\PA_MetaHuman_ARKit_Mapping.reverse_map.json`

## Structural Checks

- PASS: summary.totalPoseTargets matches reverseMappingTable length
- PASS: reverseMappingTableByClass sections exist and are lists
- PASS: summary.arkit52Targets matches reverseMappingTableByClass.arkit52 length
- PASS: summary.extendedPoseTargets matches reverseMappingTableByClass.extended_pose length
- PASS: summary.defaultOrOtherTargets matches reverseMappingTableByClass.other_targets length
- PASS: combined by-class sections equal reverseMappingTable length

## ARKit Coverage Checks

- PASS: summary.missingArkit52Targets is consistent with discovered arkit52 targets
- PASS: no duplicate target entries inside arkit52 section

## Row Integrity Checks

- PASS: contributorCount equals contributors length for all rows
- PASS: normalizedByAbsWeight approximately sums to 1.0 per populated row

## Outcome

- Result: PASS (all structural checks passed)

## Warnings

- Missing ARKit targets detected: `MouthClose`
