"""ISM screen v1 — prediction independent of Voyager n_e nominal."""

from __future__ import annotations

import copy

from mt_ca.ism_screen import (
    evaluate_ism_screen_v1,
    load_ism_constraints,
    predict_ne_vlism_cm3,
)


def test_vlism_pred_ignores_observed_ne_in_formula() -> None:
    c = load_ism_constraints()
    rms = 0.026
    base = predict_ne_vlism_cm3(c, rms_rel=rms)["n_e_cm3"]
    c2 = copy.deepcopy(c)
    c2["vlism_voyager_v1"]["n_e_cm3_nominal"] = 999.0
    alt = predict_ne_vlism_cm3(c2, rms_rel=rms)["n_e_cm3"]
    assert base == alt


def test_evaluate_no_toy_fill_keys() -> None:
    row = evaluate_ism_screen_v1(log10_T_M_over_CMB=30.9, rms_rel_wall=0.026)
    assert "toy_n_e_cm3" not in row
    assert "macro_fill" not in str(row)
    assert row["n_e_vlism_pred_cm3"] > 0.0
