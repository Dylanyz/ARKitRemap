"""Coupled/grouped solve verification for ARKit remap cross-contamination.

When two ARKit targets share MHA source curves, the independent per-target
least-squares solve conflates their contributions: each target absorbs the
other's signal through the shared curves, overestimating both.

This module implements joint least-squares solves for configured target pairs
and small target groups, eliminating cross-contamination while preserving
backwards compatibility for all other targets.

Integration:
    Replace _weighted_synthesis() calls with _weighted_synthesis_v2() and add
    a "coupledPairs" key to the mapping payload JSON.

Math:
    For two targets A, B with source curves s_1..s_n where each curve has
    weights w_A_i and w_B_i (0 if the curve doesn't contribute to that target):

        Forward model:  observed_i = A_true * w_A_i + B_true * w_B_i
        Normal eqns:    (W^T W) x = W^T obs

        [sum(wA^2)     sum(wA*wB)] [A]   [sum(obs*wA)]
        [sum(wA*wB)    sum(wB^2) ] [B] = [sum(obs*wB)]

    Solved per-frame via Cramer's rule (W^T W is constant across frames).
"""


# ---------------------------------------------------------------------------
# Core: grouped least-squares solve
# ---------------------------------------------------------------------------

def _invert_matrix(matrix):
    """Invert a small dense matrix with Gauss-Jordan elimination."""
    n = len(matrix)
    if n == 0 or any(len(row) != n for row in matrix):
        return None

    aug = []
    for i, row in enumerate(matrix):
        aug.append([float(v) for v in row] + [
            1.0 if i == j else 0.0 for j in range(n)
        ])

    for col in range(n):
        pivot_row = max(range(col, n), key=lambda r: abs(aug[r][col]))
        pivot = aug[pivot_row][col]
        if abs(pivot) < 1e-12:
            return None
        if pivot_row != col:
            aug[col], aug[pivot_row] = aug[pivot_row], aug[col]

        pivot = aug[col][col]
        inv_pivot = 1.0 / pivot
        for j in range(2 * n):
            aug[col][j] *= inv_pivot

        for row in range(n):
            if row == col:
                continue
            factor = aug[row][col]
            if abs(factor) < 1e-12:
                continue
            for j in range(2 * n):
                aug[row][j] -= factor * aug[col][j]

    return [row[n:] for row in aug]


def _solve_group_targets(target_names, target_index, source_cache, frame_count):
    """Solve a coupled target group jointly via NxN least-squares."""
    if len(target_names) < 2:
        return None

    weight_map = {}
    for idx, name in enumerate(target_names):
        tdata = target_index.get(name)
        if tdata is None:
            return None
        for c in tdata["contributors"]:
            key = c["source"].lower()
            if key not in weight_map:
                weight_map[key] = [0.0] * len(target_names)
            weight_map[key][idx] = c["weight"]

    active = [
        (src, weights) for src, weights in weight_map.items()
        if src in source_cache
    ]
    if not active:
        return None

    gram = []
    for i in range(len(target_names)):
        row = []
        for j in range(len(target_names)):
            row.append(sum(weights[i] * weights[j] for _, weights in active))
        gram.append(row)

    gram_inv = _invert_matrix(gram)
    if gram_inv is None:
        return None

    curve_data = [(source_cache[src][1], weights) for src, weights in active]
    outputs = [[0.0] * frame_count for _ in target_names]

    for i in range(frame_count):
        rhs = [0.0] * len(target_names)
        for vals, weights in curve_data:
            obs = vals[i]
            for j, weight in enumerate(weights):
                rhs[j] += obs * weight

        solved = []
        for row in gram_inv:
            solved.append(sum(row[j] * rhs[j] for j in range(len(target_names))))

        for j, value in enumerate(solved):
            outputs[j][i] = max(0.0, value)

    return outputs


def _coupled_solve_pair(name_a, name_b, target_index, source_cache, frame_count):
    """Solve two coupled ARKit targets jointly via 2x2 least-squares.

    Builds the union of all source curves that contribute to either target,
    forms the 2x2 Gram matrix W^T*W (constant across frames), then solves
    per frame using Cramer's rule.

    Args:
        name_a:       First ARKit target name (e.g. "MouthPucker").
        name_b:       Second ARKit target name (e.g. "MouthFunnel").
        target_index: Dict from _build_target_index() — keys are ARKit names,
                      values have "contributors" and "sumWeightSquared".
        source_cache: Dict of lowercase_curve_name -> (times, values).
        frame_count:  Number of frames in the animation.

    Returns:
        (values_a, values_b): Per-frame value lists for both targets,
                              clamped to >= 0 (pre-calibration).
        (None, None) if the solve fails (missing data or singular matrix).
    """
    outputs = _solve_group_targets(
        [name_a, name_b], target_index, source_cache, frame_count
    )
    if outputs is None:
        return None, None
    return outputs[0], outputs[1]


# ---------------------------------------------------------------------------
# V2 synthesis: coupled pairs + independent fallback
# ---------------------------------------------------------------------------

def _weighted_synthesis_v2(target_index, source_cache, calibration, frame_count,
                           coupled_pairs=None, coupled_groups=None):
    """Compute ARKit values for all 51 payload targets.

    Drop-in replacement for _weighted_synthesis(). Identical behavior when
    coupled_pairs is None or empty. When coupled pairs are configured, those
    targets are solved jointly; all others use the original independent solve.

    Args:
        target_index:  Dict from _build_target_index().
        source_cache:  Dict of lowercase_curve_name -> (times, values).
        calibration:   calibrationDefaults from payload.
        frame_count:   Number of frames.
        coupled_pairs: List of [nameA, nameB] pairs from payload's
                       "coupledPairs" key, or None for independent-only.
        coupled_groups: List of [nameA, nameB, ...] groups from payload's
                        "coupledGroups" key.

    Returns:
        (arkit_output, stats) — same shape as _weighted_synthesis().
        Stats for coupled targets include a "coupled_with" key.
    """
    global_cal = calibration.get("global", {})
    overrides = calibration.get("perCurveOverrides", {})
    arkit_output = {}
    stats = {}

    # --- Phase 1: Solve coupled pairs/groups ---------------------------
    coupled_targets = set()
    solve_groups = [list(group) for group in (coupled_groups or []) if len(group) >= 2]
    solve_groups.extend([list(pair) for pair in (coupled_pairs or []) if len(pair) == 2])

    for group_names in solve_groups:
        if len(set(group_names)) != len(group_names):
            continue
        if any(name not in target_index for name in group_names):
            try:
                import unreal
                unreal.log_warning(
                    f"[ARKit Remap] Coupled solve {group_names}: "
                    f"one or more targets not in payload, falling back to "
                    f"independent solve."
                )
            except ImportError:
                pass
            continue
        if any(name in coupled_targets for name in group_names):
            continue

        group_values = _solve_group_targets(
            group_names, target_index, source_cache, frame_count
        )

        if group_values is None:
            try:
                import unreal
                unreal.log_warning(
                    f"[ARKit Remap] Coupled solve failed for "
                    f"{group_names} (singular or no data), "
                    f"falling back to independent solve."
                )
            except ImportError:
                pass
            continue

        for idx, name in enumerate(group_names):
            vals = _apply_calibration(group_values[idx], overrides.get(name, global_cal))
            arkit_output[name] = vals
            coupled_targets.add(name)
            tdata = target_index[name]
            found = sum(
                1 for c in tdata["contributors"]
                if c["source"].lower() in source_cache
            )
            stats[name] = {
                "found": found,
                "total": len(tdata["contributors"]),
                "sw2": tdata["sumWeightSquared"],
                "skipped": False,
                "coupled_with": ", ".join(
                    target for target in group_names if target != name
                ),
                "min": min(vals),
                "max": max(vals),
                "mean": sum(vals) / len(vals) if vals else 0,
            }

        try:
            import unreal
            unreal.log(
                f"[ARKit Remap] Coupled solve [{', '.join(group_names)}]"
            )
        except ImportError:
            pass

    # --- Phase 2: Independent solve for remaining targets ---------------
    for arkit_name, tdata in target_index.items():
        if arkit_name in coupled_targets:
            continue

        contributors = tdata["contributors"]
        sw2 = tdata["sumWeightSquared"]
        if sw2 == 0:
            try:
                import unreal
                unreal.log_warning(
                    f"[ARKit Remap] sumWeightSquared==0 for {arkit_name}, "
                    f"skipping."
                )
            except ImportError:
                pass
            continue

        found = 0
        total = len(contributors)
        values = [0.0] * frame_count

        for c in contributors:
            src_lower = c["source"].lower()
            w = c["weight"]
            if src_lower not in source_cache:
                continue
            found += 1
            src_vals = source_cache[src_lower][1]
            for i in range(frame_count):
                values[i] += src_vals[i] * w

        if found == 0:
            try:
                import unreal
                unreal.log_warning(
                    f"[ARKit Remap] All {total} contributors missing for "
                    f"{arkit_name}, skipping."
                )
            except ImportError:
                pass
            stats[arkit_name] = {
                "found": 0, "total": total, "sw2": sw2, "skipped": True
            }
            continue

        values = [v / sw2 for v in values]

        cal = overrides.get(arkit_name, global_cal)
        values = _apply_calibration(values, cal)

        arkit_output[arkit_name] = values
        stats[arkit_name] = {
            "found": found,
            "total": total,
            "sw2": sw2,
            "skipped": False,
            "min": min(values),
            "max": max(values),
            "mean": sum(values) / len(values) if values else 0,
        }

    return arkit_output, stats


# ---------------------------------------------------------------------------
# Calibration helper (duplicated here for standalone testing;
# in production, import from arkit_remap.py)
# ---------------------------------------------------------------------------

def _clamp(val, lo, hi):
    return max(lo, min(hi, val))


def _apply_calibration(values, cal):
    scale = cal.get("scale", 1.0)
    offset = cal.get("offset", 0.0)
    lo = cal.get("clampMin", 0.0)
    hi = cal.get("clampMax", 1.0)
    return [_clamp(v * scale + offset, lo, hi) for v in values]


# ---------------------------------------------------------------------------
# Standalone verification (runs outside Unreal)
# ---------------------------------------------------------------------------

def _verify():
    """Verify coupled solve with known-answer test cases.

    These use the exact weights from the PA_MetaHuman_ARKit_Mapping extraction
    to confirm the math produces correct results.
    """
    print("=" * 70)
    print("COUPLED SOLVE VERIFICATION")
    print("=" * 70)

    # -- Test 1: MouthPucker=0.5, MouthFunnel=0.3 simultaneously ----------
    print("\n--- Pair 1: MouthPucker(0.5) + MouthFunnel(0.3) ---")

    # Weights from payload
    W_PUCKER_PURSE   = 1.0      # mouthlipspurse{dl,dr,ul,ur}
    W_PUCKER_FUNNEL  = 0.752    # mouthfunnel{dl,dr,ul,ur}
    W_PUCKER_TOWARDS = 0.412    # mouthlipstowards{dl,dr,ul,ur}
    W_FUNNEL_FUNNEL  = 0.999999 # mouthfunnel{dl,dr,ul,ur}

    P_TRUE, F_TRUE = 0.5, 0.3

    # Synthesize baked MHA observations (forward model)
    obs_purse   = P_TRUE * W_PUCKER_PURSE                          # 0.5
    obs_funnel  = P_TRUE * W_PUCKER_FUNNEL + F_TRUE * W_FUNNEL_FUNNEL  # 0.676
    obs_towards = P_TRUE * W_PUCKER_TOWARDS                        # 0.206

    # Build mock target_index
    target_index = {
        "MouthPucker": {
            "contributors": [
                {"source": "purse_dl",   "weight": W_PUCKER_PURSE},
                {"source": "purse_dr",   "weight": W_PUCKER_PURSE},
                {"source": "purse_ul",   "weight": W_PUCKER_PURSE},
                {"source": "purse_ur",   "weight": W_PUCKER_PURSE},
                {"source": "funnel_dl",  "weight": W_PUCKER_FUNNEL},
                {"source": "funnel_dr",  "weight": W_PUCKER_FUNNEL},
                {"source": "funnel_ul",  "weight": W_PUCKER_FUNNEL},
                {"source": "funnel_ur",  "weight": W_PUCKER_FUNNEL},
                {"source": "towards_dl", "weight": W_PUCKER_TOWARDS},
                {"source": "towards_dr", "weight": W_PUCKER_TOWARDS},
                {"source": "towards_ul", "weight": W_PUCKER_TOWARDS},
                {"source": "towards_ur", "weight": W_PUCKER_TOWARDS},
            ],
            "sumWeightSquared": 4*W_PUCKER_PURSE**2 + 4*W_PUCKER_FUNNEL**2 + 4*W_PUCKER_TOWARDS**2,
        },
        "MouthFunnel": {
            "contributors": [
                {"source": "funnel_dl", "weight": W_FUNNEL_FUNNEL},
                {"source": "funnel_dr", "weight": W_FUNNEL_FUNNEL},
                {"source": "funnel_ul", "weight": W_FUNNEL_FUNNEL},
                {"source": "funnel_ur", "weight": W_FUNNEL_FUNNEL},
            ],
            "sumWeightSquared": 4*W_FUNNEL_FUNNEL**2,
        },
    }

    # Single-frame source cache
    source_cache = {
        "purse_dl":   (None, [obs_purse]),
        "purse_dr":   (None, [obs_purse]),
        "purse_ul":   (None, [obs_purse]),
        "purse_ur":   (None, [obs_purse]),
        "funnel_dl":  (None, [obs_funnel]),
        "funnel_dr":  (None, [obs_funnel]),
        "funnel_ul":  (None, [obs_funnel]),
        "funnel_ur":  (None, [obs_funnel]),
        "towards_dl": (None, [obs_towards]),
        "towards_dr": (None, [obs_towards]),
        "towards_ul": (None, [obs_towards]),
        "towards_ur": (None, [obs_towards]),
    }

    # Independent solve (current method)
    sw2_p = target_index["MouthPucker"]["sumWeightSquared"]
    sw2_f = target_index["MouthFunnel"]["sumWeightSquared"]

    rhs_p_ind = (4 * obs_purse * W_PUCKER_PURSE
                 + 4 * obs_funnel * W_PUCKER_FUNNEL
                 + 4 * obs_towards * W_PUCKER_TOWARDS)
    rhs_f_ind = 4 * obs_funnel * W_FUNNEL_FUNNEL

    p_independent = rhs_p_ind / sw2_p
    f_independent = rhs_f_ind / sw2_f

    print(f"  Independent: Pucker={p_independent:.4f}  (true={P_TRUE}, "
          f"err={p_independent - P_TRUE:+.4f} = {(p_independent/P_TRUE - 1)*100:+.1f}%)")
    print(f"  Independent: Funnel={f_independent:.4f}  (true={F_TRUE}, "
          f"err={f_independent - F_TRUE:+.4f} = {(f_independent/F_TRUE - 1)*100:+.1f}%)")

    # Coupled solve
    vals_p, vals_f = _coupled_solve_pair(
        "MouthPucker", "MouthFunnel", target_index, source_cache, 1
    )
    p_coupled = vals_p[0]
    f_coupled = vals_f[0]

    print(f"  Coupled:     Pucker={p_coupled:.6f}  (true={P_TRUE}, "
          f"err={p_coupled - P_TRUE:+.6f})")
    print(f"  Coupled:     Funnel={f_coupled:.6f}  (true={F_TRUE}, "
          f"err={f_coupled - F_TRUE:+.6f})")

    assert abs(p_coupled - P_TRUE) < 0.001, f"Pucker error too large: {p_coupled}"
    assert abs(f_coupled - F_TRUE) < 0.001, f"Funnel error too large: {f_coupled}"
    print("  PASS")

    # -- Test 2: MouthRollLower=0.6, MouthRollUpper=0.8 -------------------
    print("\n--- Pair 2: MouthRollLower(0.6) + MouthRollUpper(0.8) ---")

    W_LOWER_LOWER = 1.0      # mouthlowerliprollin{l,r}
    W_LOWER_UPPER = 0.499    # mouthupperliprollin{l,r}
    W_UPPER_UPPER = 0.997999 # mouthupperliprollin{l,r}

    L_TRUE, U_TRUE = 0.6, 0.8

    obs_lower = L_TRUE * W_LOWER_LOWER
    obs_upper = L_TRUE * W_LOWER_UPPER + U_TRUE * W_UPPER_UPPER

    target_index_2 = {
        "MouthRollLower": {
            "contributors": [
                {"source": "lower_l", "weight": W_LOWER_LOWER},
                {"source": "lower_r", "weight": W_LOWER_LOWER},
                {"source": "upper_l", "weight": W_LOWER_UPPER},
                {"source": "upper_r", "weight": W_LOWER_UPPER},
            ],
            "sumWeightSquared": 2*W_LOWER_LOWER**2 + 2*W_LOWER_UPPER**2,
        },
        "MouthRollUpper": {
            "contributors": [
                {"source": "upper_l", "weight": W_UPPER_UPPER},
                {"source": "upper_r", "weight": W_UPPER_UPPER},
            ],
            "sumWeightSquared": 2*W_UPPER_UPPER**2,
        },
    }

    source_cache_2 = {
        "lower_l": (None, [obs_lower]),
        "lower_r": (None, [obs_lower]),
        "upper_l": (None, [obs_upper]),
        "upper_r": (None, [obs_upper]),
    }

    sw2_l = target_index_2["MouthRollLower"]["sumWeightSquared"]
    sw2_u = target_index_2["MouthRollUpper"]["sumWeightSquared"]

    rhs_l_ind = 2 * obs_lower * W_LOWER_LOWER + 2 * obs_upper * W_LOWER_UPPER
    rhs_u_ind = 2 * obs_upper * W_UPPER_UPPER

    l_independent = rhs_l_ind / sw2_l
    u_independent = rhs_u_ind / sw2_u

    print(f"  Independent: RollLower={l_independent:.4f}  (true={L_TRUE}, "
          f"err={l_independent - L_TRUE:+.4f} = {(l_independent/L_TRUE - 1)*100:+.1f}%)")
    print(f"  Independent: RollUpper={u_independent:.4f}  (true={U_TRUE}, "
          f"err={u_independent - U_TRUE:+.4f} = {(u_independent/U_TRUE - 1)*100:+.1f}%)")

    vals_l, vals_u = _coupled_solve_pair(
        "MouthRollLower", "MouthRollUpper", target_index_2, source_cache_2, 1
    )
    l_coupled = vals_l[0]
    u_coupled = vals_u[0]

    print(f"  Coupled:     RollLower={l_coupled:.6f}  (true={L_TRUE}, "
          f"err={l_coupled - L_TRUE:+.6f})")
    print(f"  Coupled:     RollUpper={u_coupled:.6f}  (true={U_TRUE}, "
          f"err={u_coupled - U_TRUE:+.6f})")

    assert abs(l_coupled - L_TRUE) < 0.001, f"RollLower error too large: {l_coupled}"
    assert abs(u_coupled - U_TRUE) < 0.001, f"RollUpper error too large: {u_coupled}"
    print("  PASS")

    # -- Test 3: Single target active (no cross-contamination) -------------
    print("\n--- Pair 1: Pucker-only (0.7), Funnel=0 ---")

    obs_purse_3   = 0.7 * W_PUCKER_PURSE
    obs_funnel_3  = 0.7 * W_PUCKER_FUNNEL
    obs_towards_3 = 0.7 * W_PUCKER_TOWARDS

    source_cache_3 = {
        "purse_dl":   (None, [obs_purse_3]),
        "purse_dr":   (None, [obs_purse_3]),
        "purse_ul":   (None, [obs_purse_3]),
        "purse_ur":   (None, [obs_purse_3]),
        "funnel_dl":  (None, [obs_funnel_3]),
        "funnel_dr":  (None, [obs_funnel_3]),
        "funnel_ul":  (None, [obs_funnel_3]),
        "funnel_ur":  (None, [obs_funnel_3]),
        "towards_dl": (None, [obs_towards_3]),
        "towards_dr": (None, [obs_towards_3]),
        "towards_ul": (None, [obs_towards_3]),
        "towards_ur": (None, [obs_towards_3]),
    }

    vals_p3, vals_f3 = _coupled_solve_pair(
        "MouthPucker", "MouthFunnel", target_index, source_cache_3, 1
    )
    print(f"  Coupled: Pucker={vals_p3[0]:.6f}  (true=0.7, "
          f"err={vals_p3[0] - 0.7:+.6f})")
    print(f"  Coupled: Funnel={vals_f3[0]:.6f}  (true=0.0, "
          f"err={vals_f3[0] - 0.0:+.6f})")
    assert abs(vals_p3[0] - 0.7) < 0.001
    assert abs(vals_f3[0] - 0.0) < 0.001
    print("  PASS")

    # -- Test 4: Backwards compatibility (no coupled pairs) ----------------
    print("\n--- Pair 3: BrowInnerUp(0.6) + BrowOuterUpLeft(0.8) + BrowOuterUpRight(0.4) ---")

    W_BI_LATERAL_L = 1.0
    W_BI_LATERAL_R = 1.0
    W_BI_RAISE_IN_L = 1.0
    W_BI_RAISE_IN_R = 1.0
    W_BOL_RAISE_IN_L = 1.0
    W_BOL_RAISE_OUT_L = 0.999998
    W_BOR_RAISE_IN_R = 0.999999
    W_BOR_RAISE_OUT_R = 0.999999

    BI_TRUE, BOL_TRUE, BOR_TRUE = 0.6, 0.8, 0.4

    target_index_3 = {
        "BrowInnerUp": {
            "contributors": [
                {"source": "laterall", "weight": W_BI_LATERAL_L},
                {"source": "lateralr", "weight": W_BI_LATERAL_R},
                {"source": "raiseinl", "weight": W_BI_RAISE_IN_L},
                {"source": "raiseinr", "weight": W_BI_RAISE_IN_R},
            ],
            "sumWeightSquared": 4.0,
        },
        "BrowOuterUpLeft": {
            "contributors": [
                {"source": "raiseinl", "weight": W_BOL_RAISE_IN_L},
                {"source": "raiseouterl", "weight": W_BOL_RAISE_OUT_L},
            ],
            "sumWeightSquared": (
                W_BOL_RAISE_IN_L ** 2 + W_BOL_RAISE_OUT_L ** 2
            ),
        },
        "BrowOuterUpRight": {
            "contributors": [
                {"source": "raiseinr", "weight": W_BOR_RAISE_IN_R},
                {"source": "raiseouterr", "weight": W_BOR_RAISE_OUT_R},
            ],
            "sumWeightSquared": (
                W_BOR_RAISE_IN_R ** 2 + W_BOR_RAISE_OUT_R ** 2
            ),
        },
    }

    source_cache_3 = {
        "laterall": (None, [BI_TRUE * W_BI_LATERAL_L]),
        "lateralr": (None, [BI_TRUE * W_BI_LATERAL_R]),
        "raiseinl": (None, [BI_TRUE * W_BI_RAISE_IN_L + BOL_TRUE * W_BOL_RAISE_IN_L]),
        "raiseinr": (None, [BI_TRUE * W_BI_RAISE_IN_R + BOR_TRUE * W_BOR_RAISE_IN_R]),
        "raiseouterl": (None, [BOL_TRUE * W_BOL_RAISE_OUT_L]),
        "raiseouterr": (None, [BOR_TRUE * W_BOR_RAISE_OUT_R]),
    }

    vals_group = _solve_group_targets(
        ["BrowInnerUp", "BrowOuterUpLeft", "BrowOuterUpRight"],
        target_index_3, source_cache_3, 1
    )
    bi_group, bol_group, bor_group = [vals[0] for vals in vals_group]

    print(f"  Grouped: BrowInnerUp={bi_group:.6f}  (true={BI_TRUE}, err={bi_group - BI_TRUE:+.6f})")
    print(f"  Grouped: BrowOuterUpLeft={bol_group:.6f}  (true={BOL_TRUE}, err={bol_group - BOL_TRUE:+.6f})")
    print(f"  Grouped: BrowOuterUpRight={bor_group:.6f}  (true={BOR_TRUE}, err={bor_group - BOR_TRUE:+.6f})")
    assert abs(bi_group - BI_TRUE) < 0.001
    assert abs(bol_group - BOL_TRUE) < 0.001
    assert abs(bor_group - BOR_TRUE) < 0.001
    print("  PASS")

    # -- Test 5: Backwards compatibility (no coupled pairs/groups) ----------
    print("\n--- Backwards compat: _weighted_synthesis_v2 with no pairs/groups ---")

    calibration = {"global": {"scale": 1.0, "offset": 0.0,
                              "clampMin": 0.0, "clampMax": 1.0},
                   "perCurveOverrides": {}}

    out_v2, _ = _weighted_synthesis_v2(
        target_index, source_cache, calibration, 1, coupled_pairs=None,
        coupled_groups=None
    )

    # Manually compute independent values for comparison
    p_v2 = out_v2.get("MouthPucker", [None])[0]
    f_v2 = out_v2.get("MouthFunnel", [None])[0]

    # These should match the independent solve values
    p_ind_check = rhs_p_ind / sw2_p
    f_ind_check = rhs_f_ind / sw2_f

    p_ind_clamped = max(0.0, min(1.0, p_ind_check))
    f_ind_clamped = max(0.0, min(1.0, f_ind_check))

    print(f"  v2(no pairs) Pucker={p_v2:.6f}  expected={p_ind_clamped:.6f}  "
          f"match={abs(p_v2 - p_ind_clamped) < 1e-6}")
    print(f"  v2(no pairs) Funnel={f_v2:.6f}  expected={f_ind_clamped:.6f}  "
          f"match={abs(f_v2 - f_ind_clamped) < 1e-6}")
    assert abs(p_v2 - p_ind_clamped) < 1e-6
    assert abs(f_v2 - f_ind_clamped) < 1e-6
    print("  PASS")

    print("\n" + "=" * 70)
    print("ALL TESTS PASSED")
    print("=" * 70)


if __name__ == "__main__":
    _verify()
