# Pose Asset Extraction Methods Research

## Purpose

Document possible methods to extract per-ARKit-curve mapping weights from `PA_MetaHuman_ARKit_Mapping` into a portable dataset for later KB import.

This document is intentionally research-only. It does **not** update `.cursor/arkit-remap/knowledge-base.md`.

## Scope Boundaries

- Target asset: `/Game/MetaHumans/Common/Face/ARKit/PA_MetaHuman_ARKit_Mapping`
- Target output concept: `ARKit Pose Name -> [{MHA Curve Name, Weight, Sample Time/Frame}]`
- No Blueprint, asset, or KB mutations in this phase
- Goal is to choose extraction approach(es), not run extraction yet

## Constraints and Known Limits

- Current MCP toolset does not expose a dedicated PoseAsset-internals reader.
- `get_asset_summary` can be useful for supported assets, but PoseAsset weight internals are not guaranteed to be surfaced.
- Editor UI may show pose names/source animation but often not full weight matrices.
- Runtime-observed values can validate behavior but are inferential, not guaranteed exact source data.
- Community mappings are helpful references but non-authoritative for this specific project asset.

## Method Catalog

### 1) Editor UI Inspection (Fast Triage)

**What it does**
- Open PoseAsset in Content Browser and inspect Details/related panels for:
  - pose names
  - source animation reference
  - visible mapping or curve metadata (if exposed)

**Access/requirements**
- Unreal Editor open with project loaded
- No scripting required

**Strengths**
- Fastest sanity check
- Confirms asset identity and top-level metadata

**Limitations / failure modes**
- Usually does not provide complete per-pose curve-weight values
- Cannot reliably produce final extraction dataset alone

**Confidence for full dataset**
- Low

### 2) Editor Python Extraction (Primary Path)

**What it does**
- Uses Unreal Python APIs against PoseAsset + source animation curve data to build pose-to-weight mapping.

**Access/requirements**
- Unreal Editor open
- Editor scripting enabled
- Ability to run Python in-editor

**Core API surface (expected)**
- `unreal.load_asset(...)`
- `pose_asset.get_pose_names()`
- `pose_asset.get_editor_property("source_animation")`
- `unreal.AnimationLibrary.get_animation_curve_names(...)`
- `unreal.AnimationLibrary.get_float_keys(...)`
- `unreal.AnimationLibrary.get_frame_at_time(...)`

**Strengths**
- Best speed-to-fidelity ratio
- Repeatable and scriptable
- Easy to standardize output schema for later KB import

**Limitations / failure modes**
- Pose-to-time mapping may need validation (`i/(N-1)` vs `i/N` style)
- Parent/child asset patterns can obscure where source data truly lives
- Additive or transformed curves may require interpretation notes

**Confidence for full dataset**
- High (with validation checks)

### 3) C++/Plugin Native Extraction (High-Control Fallback)

**What it does**
- Implement extractor using engine-native `UPoseAsset` + anim data APIs and export JSON/CSV/TXT.

**Access/requirements**
- C++ plugin/project source access
- Build/compile capability
- Unreal Editor/project build environment

**Strengths**
- Max control over internals
- Strong for difficult edge cases and exact frame sampling logic
- Good long-term reusable tooling path

**Limitations / failure modes**
- Higher implementation effort
- Slower iteration than Python
- Engine API/version differences can increase complexity

**Confidence for full dataset**
- High

### 4) Runtime Inference via AnimGraph Observation (Validation Path)

**What it does**
- Observe post-PA outputs in a controlled test graph/session to infer contribution patterns.

**Access/requirements**
- Test setup in AnimBlueprint/animation runtime
- Logging/inspection workflow

**Strengths**
- Useful for behavioral validation
- Helps verify assumptions from direct extraction

**Limitations / failure modes**
- Inference, not guaranteed canonical stored weights
- Hard to recover full static mapping matrix reliably

**Confidence for full dataset**
- Medium-low

### 5) Raw `.uasset` Parsing (Last Resort)

**What it does**
- Parse binary asset exports (`.uasset/.uexp`) with third-party tooling and reconstruct data tables.

**Access/requirements**
- External parser tooling (engine-version compatible)
- Asset-format reverse-engineering tolerance

**Strengths**
- Can work when editor APIs are blocked/unavailable
- Potentially direct file-level extraction

**Limitations / failure modes**
- Engine-version brittle
- High effort, high fragility
- Struct interpretation ambiguity

**Confidence for full dataset**
- Medium (variable by tooling/version match)

### 6) Documentation/Community Triangulation (Reference Only)

**What it does**
- Leverage docs/community mappings as context and plausibility checks.

**Access/requirements**
- External references

**Strengths**
- Fast background context
- Useful for naming sanity checks

**Limitations / failure modes**
- Non-authoritative for local asset
- Can conflict with true project-specific mapping

**Confidence for full dataset**
- Low

## Recommended Execution Sequence

1. **Editor UI check** for asset identity, pose count, source animation references.
2. **Editor Python extraction** as the primary dataset generation path.
3. **Python validation pass**:
   - verify pose index to sample time/frame mapping
   - verify non-zero distribution sanity
   - spot-check known curves (e.g., `MouthClose`, `JawOpen`)
4. If blocked or ambiguous, switch to **C++ native extraction** for deterministic control.
5. Use **runtime inference** only to validate behavior, not as authoritative source.
6. Use **raw uasset parsing** only if editor-side approaches fail.
7. Use **docs/community** only as confidence annotations.

## Practical Ranking (Method -> Practicality / Confidence)

1. Editor Python -> Very High / High  
2. Editor UI -> High for triage / Low for full extraction  
3. C++ Native -> Medium practicality / High confidence  
4. Runtime Inference -> Medium practicality / Medium-low confidence  
5. Raw `.uasset` parsing -> Low practicality / Medium confidence  
6. Docs/Community -> High practicality / Low confidence

## Downstream Agent Handoff Contract

Subsequent extraction agents should return structured records using this schema:

```json
{
  "assetPath": "/Game/MetaHumans/Common/Face/ARKit/PA_MetaHuman_ARKit_Mapping",
  "extractionMethod": "editor_python | cpp_native | runtime_inference | uasset_parse",
  "records": [
    {
      "arkitPoseName": "mouthClose",
      "sourceMhaCurveName": "CTRL_expressions_mouth_...",
      "weight": 0.42,
      "sampleTimeOrFrame": "time=0.4333s|frame=13",
      "confidenceNotes": "direct sampled value; nearest-key"
    }
  ],
  "mappingAssumptions": {
    "poseIndexToTimeRule": "i/(N-1)",
    "samplingRule": "nearest_key|linear_interpolation",
    "filteredZeroWeights": true,
    "epsilon": 0.0001
  },
  "validationSummary": {
    "poseCount": 52,
    "curveCount": 130,
    "sanityChecks": [
      "all poses resolved",
      "non-empty weight sets",
      "spot-check mouthClose/jawOpen completed"
    ]
  }
}
```

## Handoff Checklist For Next Agents

- Confirm exact PoseAsset path loaded successfully
- Report pose count and source animation path
- Explicitly state pose-index-to-time/frame mapping rule used
- Provide one output record per non-zero contribution (or clearly state if dense/full matrix)
- Include confidence notes for any interpolated/inferred values
- Include validation summary and known caveats
- Keep output in a standalone artifact; do not write into KB during extraction run

## Final Notes

- This document is the method decision baseline for upcoming extraction runs.
- KB integration is intentionally deferred until extraction data is produced and reviewed.
