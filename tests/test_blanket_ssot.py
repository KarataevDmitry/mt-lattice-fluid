"""Tests that blanket SSOT package loads and re-exports."""

from __future__ import annotations

from mt_ca import blanket
from mt_ca.blanket import BlanketPreset, load_ism_constraints


def test_blanket_preset_ocean_scenario() -> None:
    from mt_ca.app.scenario import get_scenario

    s = get_scenario("ocean_ism_blanket")
    assert s.blanket is BlanketPreset.HOMOGENEOUS_MZW
    assert s.habitat.is_live


def test_load_constraints_via_package() -> None:
    c = load_ism_constraints()
    assert "wnm_thermal" in c
    assert blanket.equilibrium_T_wnm_K(float(c["lic"]["n_H_cm3_nominal"]), c) > 1000.0
