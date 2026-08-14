# ARKit Remap V3 — Build Plan

**Status:** active (started 2026-08-14). Supersedes the v2 pipeline entirely.

## Ground rules (Dylan's direction, 2026-08-14)

1. **V2's mapping numbers are dead.** The v2 payload (`release/arkit_remap_payload.json`) was AI-guessed reverse engineering with subjective hand calibration. It is NOT a source for V3. Do not port its weights, constants, or calibrations (`lipsPurseWeight=0.735`, `jawFactor=0.75`, etc.).
2. **Only authoritative engine sources feed the mapping:**
   - `PA_MetaHuman_ARKit_Mapping` / `AS_MetaHuman_ARKit_Mapping` — Epic's actual ARKit→MHA table (re-extract fresh from the 5.8 asset with reproducible scripts; do not reuse v2's extraction files without re-verification)
   - `ABP_MH_LiveLink` runtime formulas (MouthClose = clamp(MouthClose/JawOpen) → LipsTogether controls; head rotation scaling) — mechanical facts read from the Blueprint
   - **OpenRigLogic** (github.com/EpicGames/OpenRigLogic, branch `5.8`) + a real MetaHuman head DNA — numerical evaluation of the actual rig for solving the inverse
3. **V2 research is still valid as *process* knowledge** (what the pipeline layers are, where MouthClose lives, curve name spaces, pitfalls) — that's `dev/knowledge-base.md`. Its mapping *conclusions* are not.
4. **The deliverable is a `RigMapperDefinition`** (`RM_MHA_to_ARKit`), authored/versioned as JSON in this repo, consumed via UE 5.8's RigMapper stack (see knowledge base Section K). No custom runtime code.

## Why the inverse must be solved, not transposed

Epic's PA mapping is **forward** (ARKit→MHA): each ARKit curve turns on a pose of MHA control values. Going MHA→ARKit is an inverse problem: many MHA control combinations map to the same visual result, and naive weight transposition (v2's approach) ignores how controls actually combine on the mesh. The correct inversion happens in **deformation space**:

```
Basis:  for each ARKit shape j:
          c_j = MHA control vector of PA pose j          (from fresh PA extraction)
          B_j = RigLogic(c_j)                            (blendshape + joint outputs via OpenRigLogic)

Solve:  for any MHA frame with controls c:
          d = RigLogic(c)
          w* = argmin over w in [0,1]^52 of || Σ_j w_j·B_j − d ||²   (bounded least squares / NNLS)
```

`w*` is the best ARKit-52 approximation of what the MetaHuman face is actually doing. The static definition is then **fitted** to reproduce `c → w*` over a large sample set.

## Phases

### P0 — Ground truth extraction
- [ ] Fresh, scripted extraction of `PA_MetaHuman_ARKit_Mapping` from the 5.8 asset (pose names, per-pose curve weights, baseline handling). Output: `v3/data/pa_mapping.json` + extraction script committed.
- [ ] Record `ABP_MH_LiveLink` runtime formulas from the 5.8 asset (MouthClose block, alphas, MHFDS switch). Output: `v3/data/abp_runtime_rules.json`.
- [ ] Export a MetaHuman head DNA (e.g. MH_EL04 from MDR_58_tester, or a MetaHuman Creator DCC export). Output: local `.dna` (not committed if large/licensed — document the export steps instead).
- [ ] Verify MHA real-time Live Link subject curve names (expected: `CTRL_expressions_*` / MHFDS). 30-second live check.

### P1 — OpenRigLogic harness (offline Python, no UE needed)
- [ ] Build OpenRigLogic `5.8` branch Python bindings (dna + riglogic modules; needs CMake, SWIG, MSVC, Python dev headers).
- [ ] Load head DNA; enumerate raw/GUI control names, blendshape channels, joints; map MHA curve names ↔ DNA raw control indices.
- [ ] Evaluate the 52 ARKit basis deformations `B_j`; assess conditioning/overlap (which shapes share deformation mass — brows, mouth region).
- [ ] Sanity probes: PSD/corrective activation behavior, linearity ranges.

### P2 — Inverse solve + definition fitting
- [ ] Bounded least-squares per-frame solver (`c → w*`), validated on synthetic poses (feed pure ARKit basis poses through — should recover identity).
- [ ] Sample set: real MHA takes (MDR_58_tester has several) + synthetic control sweeps.
- [ ] Fit a sparse WS/SDK/MathOp feature graph per ARKit output from the samples; MouthClose/JawOpen handled by inverting the ABP formula exactly, not by tuned constants.
- [ ] Export `v3/RM_MHA_to_ARKit.json` (RigMapperDefinition JSON schema).

### P3 — In-engine assembly + validation
- [ ] Load JSON → `/Game/ARKitRemap/RM_MHA_to_ARKit` (replace the 2026-06 draft asset, which was built with v2-derived thinking), validate in the 5.8 definition editor, re-import inputs from the face SKM.
- [ ] Wire the three consumption paths: right-click Convert action, IK Retargeter Single RigMapper op, and confirm UserData discovery.
- [ ] Comparison harness: same take as (a) V3 definition output vs (b) raw iPhone ARKit reference (Live Link Face recording). Metrics per curve + visual passes. **No v2 output in the comparison baseline** — v2 is not a reference.

### P4 — Live preview + packaging
- [ ] Template AnimBP: Live Link Pose (MHA subject) → Rig Mapper node → output; Alpha as blend; implement `BPI_RigMapper` (EnableRigMapper / OverrideDefinitions) for the toggle.
- [ ] UserData stamping helper (one-click "tag this character").
- [ ] Guides: how the MetaHuman LiveLink/AnimBP system works; setting up an ARKit-52 character (generic — FaceIt as documented example) for baked + live use.
- [ ] Repo restructure: v2 `release/` + payload → `legacy/`; V3 package = definition JSON + ABP template + guides.

## Key technical references

- `dev/knowledge-base.md` Section K — full UE 5.8 RigMapper system survey (data model, JSON, anim node, retarget ops, editor subsystem, utilities, shipped defs)
- `dev/knowledge-base.md` Sections C/D — forward pipeline + PA asset (process knowledge; re-verify data before use)
- OpenRigLogic docs: https://EpicGames.github.io/OpenRigLogic + `docs/design/design.md` in the repo (RigLogic 4 design: PSD → linear → conditional stages)
- RigLogic whitepaper PDF (DNA format, runtime strategy)

## Open questions

- DNA per-character vs archetype: does the remap definition need per-character fitting, or is the archetype rig close enough? (Expectation: archetype is fine — RigLogic behavior is shared; DNA differences are mostly geometry/joint placement.)
- Eye-look curves: bone-driven in MetaHuman; decide whether V3 ships weighted approximations (as v2 did) or leaves eyes to a documented Live Link passthrough.
- TongueOut and other shapes with no reliable MHA source signal: emit as NullOutputs or approximate?
