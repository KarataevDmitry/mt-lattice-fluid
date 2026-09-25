"""verify_checks.sm — extracted from verify_principles"""
from __future__ import annotations

import math
import re
from pathlib import Path

import torch

from mt_ca.cauchy_riemann import cauchy_riemann_energy
from mt_ca.config import MConfig
from mt_ca.metrics import field_amplitude, norm_drift, total_norm_squared
from mt_ca.seeds import SeedClass, make_seed
from mt_ca.simulator import LatticeFluidSimulator
from mt_ca.linear import linear_step, linear_step_local_ca
from mt_ca.reversible import evolve_canonical
from mt_ca.spinor import (
    arg_phase_defect,
    apply_gate_collision,
    gate_phase,
    holonomy_zeta,
    spinor_neighbor_sum,
    su2_apply,
)
from mt_ca.update import apply_heisenberg_floor, vacuum_phase, wrapped_phase_diff


def check_compton_electron(device: str = "cpu") -> dict:
    from mt_ca.si_constants import SI, compton_wavelength, reduced_compton_wavelength

    m_e = SI.m_e_CODATA
    lambda_bar = reduced_compton_wavelength(m_e)
    lambda_c = compton_wavelength(m_e)
    codata_lambda_c = 2.426310238e-12
    rel = abs(lambda_c - codata_lambda_c) / codata_lambda_c
    ok = rel < 1e-6
    return {
        "id": "Compton_e",
        "lambda_bar_m": lambda_bar,
        "lambda_C_m": lambda_c,
        "codata_rel_err": rel,
        "ok": ok,
    }

def check_electron_anchor(device: str = "cpu") -> dict:
    from mt_ca.m_to_t import electron_v_p_anchor

    row = electron_v_p_anchor()
    ok = row["rel_err"] < 1e-9
    return {"id": "M2T_e", "f_geometry": row["f_geometry"], "rel_err": row["rel_err"], "ok": ok}

def check_saturation_bc(device: str = "cpu") -> dict:
    """§8.4.2-C′′′ — live D_★ strain vs Newton; hinge = mismatch, not stitch."""
    from mt_ca.si_constants import SI
    from mt_ca.strain_metric import saturation_core_probe

    alg = SI.saturation_bc_row()
    live = saturation_core_probe(size=64, device=device)
    # Pass = hinge confirmed (near ≫ Newton), algebra↔field agree on order
    hinge = live["near_over_newton"] > 100.0 and alg["near_over_newton"] > 100.0
    agree = abs(math.log10(live["near_over_newton"] + 1e-30) - math.log10(alg["near_over_newton"] + 1e-30)) < 0.5
    ok = hinge and agree
    return {
        "id": "SatBC_Cppp",
        "h_star_near": live["h_star_near"],
        "h_star_newton": live["h_star_newton"],
        "near_over_newton": live["near_over_newton"],
        "alg_near_over_newton": alg["near_over_newton"],
        "far_R2_ratio": live["far_R2_ratio"],
        "far_R8_ratio": live["far_R8_ratio"],
        "ok": ok,
        "note": "C′′′: |h_near/h_Newton|≫1 on A5-floor; far 1/R not claimed",
    }

def check_higgs_mass(device: str = "cpu") -> dict:
    from mt_ca.si_constants import SI

    del device
    row = SI.higgs_mass_row()
    ok = (
        abs(row["m_H_bare_GeV"] - row["m_H_direct_GeV"]) / row["m_H_bare_GeV"] < 1e-12
        and abs(row["m_H_over_v_bare"] - 0.5) < 1e-12
        and row["N_hier"] == 8.0
        and abs(row["delta_lambda_stack"] - 8.0 * row["delta_lambda_quantum"]) < 1e-15
        and row["m_H_rel_err"] < 0.001
        and row["m_H_bare_rel_err"] < 0.03
    )
    return {
        "id": "Higgs_mass",
        "m_H_bare_GeV": row["m_H_bare_GeV"],
        "m_H_GeV": row["m_H_GeV"],
        "v_GeV": row["v_GeV"],
        "lambda_bare": row["lambda_bare"],
        "lambda_quartic": row["lambda_quartic"],
        "delta_lambda_stack": row["delta_lambda_stack"],
        "m_H_rel_err": row["m_H_rel_err"],
        "ok": ok,
        "note": row["note"],
    }

def check_proton_mass(device: str = "cpu") -> dict:
    from mt_ca.si_constants import KAPPA_FCC_1TICK, N12_FCC_CAUSAL_LINKS, SI

    del device
    row = SI.proton_mass_row()
    delta_pack = (KAPPA_FCC_1TICK ** 2) / float(N12_FCC_CAUSAL_LINKS)
    ok = (
        abs(row["m_p_over_m_H_bare"] - row["alpha_preferred"]) < 1e-12
        and abs(row["m_p_bare_GeV"] - row["alpha_preferred"] * row["m_H_bare_GeV"]) < 1e-12
        and abs(row["kappa_FCC"] - KAPPA_FCC_1TICK) < 1e-15
        and row["N12"] == float(N12_FCC_CAUSAL_LINKS)
        and abs(row["delta_pack"] - delta_pack) < 1e-15
        and abs(row["pack_stack_factor"] - (1.0 + delta_pack)) < 1e-15
        and abs(row["m_p_GeV"] - row["m_p_bare_GeV"] * row["pack_stack_factor"]) < 1e-12
        and row["m_p_bare_rel_err"] < 0.05
        and row["m_p_rel_err"] < 0.005
    )
    return {
        "id": "Proton_mass",
        "m_p_bare_GeV": row["m_p_bare_GeV"],
        "m_p_GeV": row["m_p_GeV"],
        "m_H_bare_GeV": row["m_H_bare_GeV"],
        "v_GeV": row["v_GeV"],
        "delta_pack": row["delta_pack"],
        "m_p_bare_rel_err": row["m_p_bare_rel_err"],
        "m_p_rel_err": row["m_p_rel_err"],
        "ok": ok,
        "note": row["note"],
    }

def check_electron_mass(device: str = "cpu") -> dict:
    from mt_ca.si_constants import HV, SI

    del device
    row = SI.electron_mass_row()
    n_phi = float(HV.N_phi)
    a2 = row["alpha_preferred"] ** 2
    ok = (
        row["N_phi"] == n_phi
        and n_phi == 13.0
        and abs(row["m_e_bare_GeV"] - a2 * row["m_H_bare_GeV"] / n_phi) < 1e-18
        and abs(row["m_e_GeV"] - a2 * row["m_H_GeV"] / n_phi) < 1e-18
        and row["m_e_bare_rel_err"] < 0.02
        and row["m_e_rel_err"] < 0.005
    )
    return {
        "id": "Electron_mass",
        "m_e_bare_GeV": row["m_e_bare_GeV"],
        "m_e_GeV": row["m_e_GeV"],
        "m_H_GeV": row["m_H_GeV"],
        "N_phi": row["N_phi"],
        "f_geom": row["f_geom"],
        "m_e_bare_rel_err": row["m_e_bare_rel_err"],
        "m_e_rel_err": row["m_e_rel_err"],
        "ok": ok,
        "note": row["note"],
    }

def check_neutrino_mass(device: str = "cpu") -> dict:
    from mt_ca.si_constants import HV, SI

    del device
    row = SI.neutrino_mass_row()
    n_phi = float(HV.N_phi)
    n_hier = float(row["N_hier"])
    a = row["alpha_preferred"]
    expected = (a**5) * (2.0 * row["m_H_GeV"]) / (n_hier * n_phi) * 1e9
    bare = (a**5) * row["v_GeV"] / (n_hier * n_phi) * 1e9
    bridge = (a**3) * row["m_e_GeV"] / (n_hier / 2.0) * 1e9
    ok = (
        row["N_phi"] == n_phi
        and n_phi == 13.0
        and n_hier == 8.0
        and abs(row["m_nu_atm_eV"] - expected) / expected < 1e-12
        and abs(row["m_nu_atm_bare_eV"] - bare) / bare < 1e-12
        and abs(row["m_nu_atm_eV"] - bridge) / bridge < 1e-12
        and row["bridge_equals_stack"] < 1e-12
        and row["m_nu_atm_bare_rel_err"] < 0.03
        and row["m_nu_atm_rel_err"] < 0.005
    )
    return {
        "id": "Neutrino_mass",
        "m_nu_atm_bare_eV": row["m_nu_atm_bare_eV"],
        "m_nu_atm_eV": row["m_nu_atm_eV"],
        "m_nu_sol_lemma_eV": row["m_nu_sol_lemma_eV"],
        "m_nu_lightest_lemma_eV": row["m_nu_lightest_lemma_eV"],
        "N_hier": row["N_hier"],
        "N_phi": row["N_phi"],
        "m_nu_atm_bare_rel_err": row["m_nu_atm_bare_rel_err"],
        "m_nu_atm_rel_err": row["m_nu_atm_rel_err"],
        "ok": ok,
        "note": row["note"],
    }

def check_neutron_mass(device: str = "cpu") -> dict:
    from mt_ca.si_constants import SI

    del device
    row = SI.neutron_mass_row()
    ok = (
        row["k"] == 2
        and abs(row["delta_GeV"] - 2.0 * row["m_e_GeV"]) < 1e-18
        and abs(row["m_n_GeV"] - (row["m_p_GeV"] + row["delta_GeV"])) < 1e-18
        and row["beta_downhill"] is True
        and row["m_n_GeV"] > row["threshold_m_p_plus_m_e_GeV"]
        and abs(row["m_n_GeV"] - (row["m_p_GeV"] + 2.0 * row["m_e_GeV"])) < 1e-18
        and row["m_n_rel_err"] < 0.01
    )
    return {
        "id": "Neutron_mass",
        "m_n_GeV": row["m_n_GeV"],
        "m_p_GeV": row["m_p_GeV"],
        "m_e_GeV": row["m_e_GeV"],
        "k": row["k"],
        "delta_GeV": row["delta_GeV"],
        "beta_downhill": row["beta_downhill"],
        "m_n_rel_err": row["m_n_rel_err"],
        "delta_rel_err": row["delta_rel_err"],
        "ok": ok,
        "note": row["note"],
    }


def check_annihilation_t_stats(device: str = "cpu") -> dict:
    """§5.0.3 T-readout: lattice τ_M, dipole 2γ proxy, ensemble ⟨dσ/dΩ⟩ isotropy."""
    from mt_ca.annihilation_t_stats import annihilation_t_stats_probe

    row = annihilation_t_stats_probe(size=160, steps=64, block=8, ensemble=12, device=device)
    # Partial DoD: dipole back-to-back on ΔΦ; full ensemble axis + PDG τ bridge open.
    ok = bool(row["back_to_back_proxy"])
    return {
        "id": "Annihilation_T_stats",
        "probe_path": row["probe_path"],
        "tick_focus": row["tick_focus"],
        "tau_M_s": row["tau_M_s"],
        "tau_M_over_tau_PDG": row["tau_M_over_tau_PDG"],
        "peaks_on_delta": row["peaks_on_delta"],
        "elongation_delta": row["elongation_delta"],
        "ensemble_axis_hist_cv": row["ensemble_axis_hist_cv"],
        "mean_axis_tracking_err_rad": row["mean_axis_tracking_err_rad"],
        "back_to_back_proxy": row["back_to_back_proxy"],
        "ensemble_isotropic": row["ensemble_isotropic"],
        "axis_tracks_injection": row["axis_tracks_injection"],
        "axis_tracks_pi": row["axis_tracks_pi"],
        "ok": ok,
        "note": row["note"],
    }
