"""WNM thermal balance Γ=Λ."""

from __future__ import annotations

import copy

from mt_ca.ism_screen import load_ism_constraints
from mt_ca.wnm_thermal import wnm_equilibrium_T_K


def test_wnm_balance_near_lic_observation() -> None:
    c = load_ism_constraints()
    row = wnm_equilibrium_T_K(float(c["lic"]["n_H_cm3_nominal"]), c)
    assert row["balance_rel_err"] < 1.0e-6
    assert 5500.0 <= row["T_K"] <= 8500.0
    assert 0.005 <= row["n_e_cm3"] <= 0.05


def test_T_eq_independent_of_T_LIC_yaml() -> None:
    c = load_ism_constraints()
    base = wnm_equilibrium_T_K(0.07, c)["T_K"]
    c2 = copy.deepcopy(c)
    c2["lic"]["T_K_warm_nominal"] = 50_000.0
    assert wnm_equilibrium_T_K(0.07, c2)["T_K"] == base
