"""ISM screen v2 — column τ, T_eff range, N_CMB chain."""

from __future__ import annotations

import copy

from mt_ca.ism_screen import (
    column_tau_at_r,
    evaluate_ism_screen_v1,
    evaluate_ism_screen_v2,
    load_ism_constraints,
    predict_ne_vlism_cm3,
    vlism_T_ref_K,
)


def test_vlism_pred_ignores_observed_ne_in_formula() -> None:
    c = load_ism_constraints()
    rms = 0.026
    base = predict_ne_vlism_cm3(c, rms_rel=rms)["n_e_cm3"]
    c2 = copy.deepcopy(c)
    c2["vlism_voyager_v1"]["n_e_cm3_nominal"] = 999.0
    alt = predict_ne_vlism_cm3(c2, rms_rel=rms)["n_e_cm3"]
    assert base == alt


def test_T_ref_from_literature_range_not_obs_ne() -> None:
    c = load_ism_constraints()
    v = c["vlism_voyager_v1"]
    assert "T_eff_K_range" in v
    ref = vlism_T_ref_K(v)
    lo, hi = v["T_eff_K_range"]
    assert lo < ref < hi


def test_column_tau_grows_with_radius() -> None:
    c = load_ism_constraints()
    t_in = column_tau_at_r(c, 0.0001)["tau"]
    t_out = column_tau_at_r(c, 15.0)["tau"]
    assert t_out > t_in


def test_evaluate_no_toy_fill_keys() -> None:
    row = evaluate_ism_screen_v1(log10_T_M_over_CMB=30.9, rms_rel_wall=0.026)
    assert "toy_n_e_cm3" not in row
    assert row["n_e_vlism_pred_cm3"] > 0.0


def test_v2_ncmb_flags_acoustic_gap() -> None:
    decay = [
        {"nu_passes": 1, "rms_rel": 0.03},
        {"nu_passes": 64, "rms_rel": 0.003},
        {"nu_passes": 256, "rms_rel": 0.001},
    ]
    row = evaluate_ism_screen_v2(
        log10_T_M_over_CMB=30.9,
        rms_rel_wall=0.03,
        smooth_decay=decay,
        nu_at_N_CMB=1.0e6,
    )
    assert row["needs_acoustic_growth"] is True
    assert row["ok_ncmb_acoustic_gap"] is True
