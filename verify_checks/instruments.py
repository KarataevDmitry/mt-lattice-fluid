"""Instrument panel — catalog wired to sim via app lab SSOT."""
from __future__ import annotations


def check_instrument_panel_vortex(size: int = 48, device: str = "cpu") -> dict:
    """§5 panel on **3+1 FCC** planckon (``floor0_planckon`` + ``LabSession``)."""
    from mt_ca.app.lab import open_lab
    from mt_ca.instruments import REGISTRY

    lab = open_lab("floor0_planckon", size, device=device)
    lab.step(128)
    panel = lab.panel()
    site = panel["site"]
    t = panel["t"]["readings"]
    rho_si = site["scaled"]["rho_field"]["value_si"]
    ok = (
        len(REGISTRY) >= 30
        and site["b_matter"] == 1
        and site["rho_field"] > 0
        and site["n_E"] >= 0
        and "phi_kick_tick" in site
        and "t_m_rest" in t
        and rho_si > 0
        and lab.dimension.value == "3+1"
    )
    return {
        "id": "Instrument_panel_vortex",
        "ok": ok,
        "dimension": lab.meta["dimension"],
        "scenario_id": lab.meta["scenario_id"],
        "grid": lab.meta["grid"],
        "catalog_count": len(REGISTRY),
        "b_matter": site["b_matter"],
        "n_topo": site["n_topo"],
        "n_E": site["n_E"],
        "rho_field_si_J_m3": rho_si,
        "t_m_rest_si": t["t_m_rest"]["value_si"],
        "rho_contrast": panel["field"]["rho_contrast"],
        "note": "§5 panel via lab; floor0_planckon @ embedding 3+1",
    }


def check_instrument_panel_hex_slice(size: int = 64, device: str = "cpu") -> dict:
    """§5 panel on **2+1** embedding — same ``floor0_planckon`` conditions."""
    from mt_ca.app.dimension import LatticeDimension
    from mt_ca.app.lab import open_lab
    from mt_ca.instruments import REGISTRY

    lab = open_lab(
        "floor0_planckon",
        size,
        device=device,
        embedding=LatticeDimension.SLICE_2P1,
    )
    lab.settle(32)
    lab.step(32)
    panel = lab.panel()
    site = panel["site"]
    ok = (
        len(REGISTRY) >= 30
        and site["b_matter"] == 1
        and lab.dimension.value == "2+1"
        and lab.meta["stencil"] == "hex"
    )
    return {
        "id": "Instrument_panel_hex_slice",
        "ok": ok,
        "dimension": lab.meta["dimension"],
        "scenario_id": lab.meta["scenario_id"],
        "grid": lab.meta["grid"],
        "b_matter": site["b_matter"],
        "note": "Same planckon scenario; embedding=2+1 (hex slice)",
    }


def check_instrument_scales_ladder(device: str = "cpu") -> dict:
    """E₀/p₀/F₀ ladder scales close under SI bridge (§5.2.1)."""
    from mt_ca.instruments.scales import QuantityKind, reading
    from mt_ca.si_constants import SI, energy_quantum_row

    row = energy_quantum_row()
    e0 = reading("E_0", QuantityKind.ENERGY_E0, 1.0)
    rel = abs(e0.value_si - SI.E_0) / SI.E_0
    ok = rel < 1e-12 and row["rel_p0_c0"] < 1e-12
    return {
        "id": "Instrument_scales_ladder",
        "ok": ok,
        "E_0_si": e0.value_si,
        "si_per_nat": e0.si_per_nat,
        "rel_p0_c0": row["rel_p0_c0"],
        "note": "Instrument SI scale for 1 E₀ matches SI.E_0",
    }


def check_instrument_scales_time_first(device: str = "cpu") -> dict:
    """§8.2 time-first cascade is SSOT for all instrument si_per_nat."""
    from mt_ca.instruments.scales import QuantityKind, reading
    from mt_ca.instruments.time_first_ladder import instrument_ladder
    from mt_ca.si_constants import SI

    L = instrument_ladder()
    e0 = reading("E_0", QuantityKind.ENERGY_E0, 1.0)
    ht = reading("hT", QuantityKind.TIME_HT, 1.0)
    rho = reading("rho", QuantityKind.RHO_FIELD, 1.0)
    mp = reading("m_P", QuantityKind.MASS_MP, 1.0)
    rel_e0 = abs(e0.value_si - L.E_0_J) / L.E_0_J
    rel_ht = abs(ht.value_si - L.hT_s) / L.hT_s
    rel_rho = abs(rho.value_si - L.u_P_J_m3) / L.u_P_J_m3
    rel_mp = abs(mp.value_si - L.m_P_kg) / L.m_P_kg
    id_lp_ct = abs(L.l_P_m / (L.c_m_s * L.t_P_s) - 1.0)
    ok = (
        L.cascade_checks_ok
        and L.energy_ladder_rel_max < 1e-12
        and rel_e0 < 1e-12
        and rel_ht < 1e-12
        and rel_rho < 1e-12
        and rel_mp < 1e-12
        and id_lp_ct < 1e-14
        and e0.si_derivation.startswith("s₀/hT")
        and e0.scale_ssot.startswith("§8.2")
    )
    return {
        "id": "Instrument_scales_time_first",
        "ok": ok,
        "cascade_checks_ok": L.cascade_checks_ok,
        "ontology_order": list(L.ontology_order),
        "rel_E_0": rel_e0,
        "rel_hT": rel_ht,
        "rel_u_P": rel_rho,
        "rel_m_P": rel_mp,
        "identity_lP_eq_c_tP": id_lp_ct,
        "note": "Instruments export SI from time-first ladder, not scattered SI.*",
    }
