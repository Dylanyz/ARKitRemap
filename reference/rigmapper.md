# UE 5.8 RigMapper system

Survey of Epic's RigMapper plugin — the engine framework ARKitRemap runs on. Surveyed
2026-08-12 from engine source + live asset inspection (UE 5.8.1); JSON schema and Python API
notes verified empirically 2026-08-14.

**Plugin locations (engine):**

| Plugin | Path | Contents |
|---|---|---|
| RigMapper | `Engine/Plugins/Experimental/Animation/RigMapper` | Runtime + editor modules, definition assets, utilities |
| RigMapperOp | `Engine/Plugins/Experimental/Animation/RigMapperOp` | IK Retargeter ops (Single / UserData RigMapper) |
| RigLogic | `Engine/Plugins/Animation/RigLogic` | MetaHuman runtime rig eval (open-sourced as OpenRigLogic) |
| OpenRigLogicSampleContent_5.8 | `Engine/Plugins/Marketplace/...` (from Fab) | `Sample.dna` + `faceboard.json` (2D picker-board GUI definition, MH.6, 175 controls — not a curve mapping) |

## 1. Data model: URigMapperDefinition

A `UDataAsset` (`RigMapperDefinition.h`) with:

- `Inputs: TArray<FString>` — expected input curve names
- `Features` — the node graph, 4 typed arrays:
  - **WeightedSum** (`ws:`): `Inputs: TMap<FString,double>` (name→weight, referencing input curves or other features) + clamp `Range` (`bHasLowerBound/LowerBound/bHasUpperBound/UpperBound`)
  - **SDK** (`sdk:`, set-driven-key): single `Input` + `Keys: [{In,Out}]` piecewise-linear response curve — Epic's idiom for all nonlinear shaping
  - **Multiply** (`mul:`): `Inputs: TArray<FString>` multiplied together (the corrective-combination primitive)
  - **MathOp** (new in 5.8): `Operation` in Min/Max/Abs/Negate/Floor/Ceil/Round/Divide/Multiply/Sum/Clamp/Lerp/Average, inputs are node names or constants
- `Outputs: TMap<FString,FString>` — output curve name → source node (feature name or direct input passthrough)
- `NullOutputs: TArray<FString>` — outputs explicitly emitted as null
- `bValidated` — set by editor validation only (not settable via API)

**JSON round-trip is built in and BlueprintCallable:** `LoadFromJsonFile` / `LoadFromJsonString`
/ `ExportAsJsonString` / `ExportAsJsonFile`. The definition therefore lives in this repo as
versioned JSON ([uassets/RM_MHA_to_ARKit.json](../uassets/RM_MHA_to_ARKit.json)) and can be
instantiated into any project in one call. Also useful: `LoadInputsFromSkeletalMesh` /
`LoadOutputsFromSkeletalMesh` (populate name lists from a mesh's actual curves — ground truth
instead of guessed names).

`URigMapperLinkedDefinitions` chains definitions: `SourceDefinitions` array +
`BakeDefinitions()` → flattened `BakedDefinition`. `URigMapperDefinitionUserData` is an
`UAssetUserData` holding a definitions array that can be stamped on a SkeletalMesh — both the
anim node and retarget ops auto-discover definitions from it ("tag your character once").

## 2. Evaluation semantics: FRigMapperProcessor

`RigMapperProcessor.h` — batch evaluator used by every consumer. Values are
`TArray<TOptional<float>>`: **missing input curves propagate as unset, not 0.0** (a behavioral
difference vs. pipelines that treat absent as 0 — test explicitly). Definitions are cached in a
singleton keyed by asset path; editor edits invalidate the cache (5.8 fixed live
re-evaluation). Supports multi-definition chains and frame interpolation
(`EvaluateFrames_Interp`).

## 3. Live path: FAnimNode_RigMapper

Anim graph node ("Rig Mapper" in AnimBP): `SourcePose` link → evaluates definition stack over
pose curves → sets output curves on the pose. Key properties: `Definitions` array, `Alpha`
(pin shown by default — lerps output curves against input values), `LODThreshold`. If the
target SkeletalMesh carries `URigMapperDefinitionUserData`, the node uses it to override its
definitions. Output curves drive same-named morph targets automatically (standard UE
curve→morph binding, case-insensitive), so MHA-space curves in → ARKit-named curves out →
ARKit character animates. This is the live path used by `abp_arkit_remap_universal`
(Live Link Pose node → Rig Mapper node).

The step-by-step live setup procedure lives in [playbooks/setup-live.md](../playbooks/setup-live.md);
its failure modes are explained in [gotchas.md](gotchas.md).

## 4. Retargeter path: RigMapperOp plugin (5.8 restructure)

Ops are instanced structs under the singleton **"Remap Curves"** parent op
(`FIKRetargetCurveRemapOp`); child ops stack in priority order:

- **Single RigMapper** (`FIKRetargetRigMapperOp`): one `Definition` +
  `bOverrideFromUserDataDefinitions`; multiple can be stacked
- **UserData RigMapper** (`FIKRetargetRigMapperUserDataOp`): evaluates the target mesh's
  UserData definitions array in order (the 5.7-compat path)
- Shared setting `bCopyAllSourceCurves` (false → only remapped curves on output; also applies
  to exported animations)
- Both have Python/BP controllers (`UIKRetargetRigMapperOpController` /
  `...UserDataOpController`) with Get/SetSettings
- Ops do nothing in `Run()` (bone pass); curve work happens in `ProcessAnimSequenceCurves`
  (export/bake) and `AnimGraphEvaluateAnyThread` (live retarget preview)

## 5. Batch conversion: URigMapperEditorSubsystem

BlueprintCallable static functions (Python-scriptable, `RigMapperEditorSubsystem.h`) that
convert through a definitions stack between any of: **AnimSequence, CSV
(`curve_name, frame_number, value` header), ControlRig section** — each direction with
in-place and `*New` (create asset) variants, plus `ConvertAnimSequenceToCsv`, `ConvertCsv`
(file→file), Get/SetAnimSequenceRate. Note the subsystem's CSV schema differs from the Live
Link Face format — FaceIt CSV import wants the LLF layout, which is what
`scripts/arkit_llf_csv.py` produces.

## 6. Utilities content (`/RigMapper/Utilities/`)

| Asset | What it does |
|---|---|
| `BP_AnimSequence_AssetActions_ConvertUsingRigMapper` | Right-click AnimSequence(s) → "Convert Selected Using RigMapper". Params: Definitions array, Target Mesh, Output Suffix. Loops selection, calls `ConvertAnimSequenceNew`, saves beside source with suffix. |
| `BP_RigMapperDefinition_AssetActions` | Right-click a definition → LoadFromJson / ExportToJson / ValidateAssets |
| `BP_RigMapperLinkedDefinitions_AssetActions` | Right-click linked definitions → BakeDefinitions |
| `BPI_RigMapper` | Blueprint Interface: `EnableRigMapper`, `OverrideDefinitions` — Epic's runtime toggle contract for characters using the anim node. |

## 7. Shipped definitions (`/RigMapper/Definitions/`) — and what's NOT there

Structure = Epic's authoring pattern, worth copying:

- `Raw/` — 12 hand-authored single-hop defs
- `Links/` — 4 `RML_*` chains (e.g. `RML_MHH_FNL` = MHH→FNM→FNH→FNL)
- `Baked/` — 4 flattened results of baking those chains

Rig families are **control-board namespaces**, not curve spaces:

| Family | Namespace | Example names |
|---|---|---|
| MH | MetaHuman Maya faceboard GUI controls (`.tx`/`.ty` attrs) | `CTRL_L_brow_down.ty`, `CTRL_C_jaw.tx` |
| CD | Alternate/legacy board variant | `CTRL_L_mouth_corner.tx`, `CTRL_C_tongue_move.tx` |
| FN | Faceware-style | `L_Brow.L_Brow_Up_Down`, `Mouth.phoneme_ch/fv/mbp/oo`, `L_Lipcorner.L_Smile_Frown` |

H/M/L suffixes = fidelity tiers. Authoring conventions observed in the shipped defs: outputs
map to `ws:`/`sdk:`/`mul:` features or pass an input straight through; `ws:dummy` = zeroed
sink output; `_corrected` suffix = intermediate fix-up feature.

**None of the shipped defs touch ARKit-52 or `CTRL_expressions_*` (MHA's baked space).**
Verified likewise: zero ARKit references in the OpenRigLogic repo and the RigLogic whitepaper.
Epic's only ARKit data is the `PA_MetaHuman_ARKit_Mapping` PoseAsset (see
[findings.md](findings.md)). Our `RM_MHA_to_ARKit` definition is the only asset in this
problem space.

## 8. OpenRigLogic (github.com/EpicGames/OpenRigLogic)

MIT, branch `5.8` = production. DNA read/write + RigLogic runtime evaluation as C++ libs with
SWIG Python bindings: load a DNA, `setRawControl(i, v)`, `calculate()`, read
`getJointOutputs()` / `getBlendShapeOutputs()` / `getAnimatedMapOutputs()`. Enables offline,
numerical evaluation of the actual MetaHuman rig — the basis for the V3 solve (see
[findings.md](findings.md)).

## 9. RigMapperDefinition JSON — real schema (differs from paraphrases)

Verified via `export_as_json_string()` of `/RigMapper/Definitions/Baked/RM_CDL_FNL`:

```json
{ "inputs": [...],
  "features": { "<name>": { "type": "weighted_sum|sdk|multiply",
                             "input_features": ["curveOrNode", ...],
                             "input_params": [],
                             "params": { "weights": [...] }        // ws (negatives and >1 legal)
                                      // { "in_val": [...], "out_val": [...] } sdk
                                      // {} multiply
                           } },
  "parameters": {}, "outputs": { "Out": "nodeOrInputName" }, "null_outputs": [] }
```

No clamp-range serialization observed. `load_from_json_string(text)` works from Python;
`load_from_json_file` needs an `unreal.FilePath` struct, not a str. Round-trip is byte-stable
except float formatting (`1.0`→`1`).

## 10. UE 5.8 Python API notes

- AnimSequence curve access:
  `unreal.AnimationLibrary.get_animation_curve_names(seq, unreal.RawCurveTrackTypes.RCT_FLOAT)`
  / `.get_float_keys(seq, name)` — **not** `AnimationBlueprintLibrary` (doesn't exist in 5.8
  Python), and `target_frame_rate` is not a readable editor property (`get_sequence_length` +
  `get_num_frames` instead).
- Batch remap: `unreal.RigMapperEditorSubsystem.convert_anim_sequence_new(source, target_mesh,
  [definitions], unreal.DirectoryPath (set "path"), "Name")` → new AnimSequence. Warns
  `Invalid curve type: RCT_Vector` — benign (float curves only). Output curve names are the
  definition's capitalized ARKit names (`JawOpen`, not `jawOpen`) — fine, curve→morph binding
  is case-insensitive.
- Morph targets: `SkeletalMesh.find_morph_target` is **not exposed** in 5.8 Python — use
  `mesh.get_all_morph_target_names()` and compare lowercased (field-verified 2026-08-24).
- **"Remove Redundant Curve Keys" on anim export strips within ~1e-3 tolerance — lossy**, not
  exactly-redundant-only. With Linear interpolation the loss is invisible in practice; use
  all-keys exports for numeric ground truth.
