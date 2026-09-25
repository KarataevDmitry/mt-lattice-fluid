"""verify_checks.carrier — extracted from verify_principles"""
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
    apply_saturating_phase_collision,
    saturating_phase,
    holonomy_zeta,
    spinor_neighbor_sum,
    su2_apply,
)
from mt_ca.update import apply_heisenberg_floor, vacuum_phase, wrapped_phase_diff


def check_carrier_torus_close(device: str = "cpu") -> dict:
    """§1.7 — finite wall-free carrier = torus; Λ×S¹ fiber; N soft."""
    from mt_ca.si_constants import SI

    del device
    row = SI.carrier_torus_close_row()
    ok = (
        bool(row["checks_ok"])
        and bool(row["derivation_closed"])
        and bool(row["topology_closed"])
        and bool(row["Lambda_times_S1_closed"])
        and bool(row["period_N_soft_open"])
        and "closed_finite_wallfree_is_torus" in row["closed_ids"]
        and "closed_Lambda_times_S1_fiber" in row["closed_ids"]
        and "reject_absorbing_wall" in row["reject_ids"]
        and "soft_open_period_N_and_covers" in row["soft_open_ids"]
    )
    return {
        "id": "Carrier_torus_close",
        "topology_closed": row["topology_closed"],
        "Lambda_times_S1_closed": row["Lambda_times_S1_closed"],
        "period_N_soft_open": row["period_N_soft_open"],
        "derivation_closed": row["derivation_closed"],
        "ok": ok,
        "note": row["note"],
    }

def check_gpu_eng_tail_close(device: str = "cpu") -> dict:
    """§0.10 — GPU eng-tail floor/step/literals closed as MODEL readout."""
    from mt_ca.si_constants import SI

    del device
    row = SI.gpu_eng_tail_close_row()
    ok = (
        bool(row["checks_ok"])
        and bool(row["derivation_closed"])
        and bool(row["floor_closed"])
        and bool(row["unitary_step_closed"])
        and bool(row["literals_closed"])
        and abs(float(row["z_min"]) - 1.0 / 64.0) < 1e-15
        and "closed_planck_floor_and_seed" in row["closed_ids"]
        and "closed_R_Phi_not_Euler" in row["closed_ids"]
        and "reject_Euler_add_step" in row["reject_ids"]
        and "soft_open_norm_drift_verify_threshold" in row["soft_open_ids"]
    )
    return {
        "id": "Gpu_eng_tail_close",
        "z_min": row["z_min"],
        "floor_closed": row["floor_closed"],
        "unitary_step_closed": row["unitary_step_closed"],
        "literals_closed": row["literals_closed"],
        "derivation_closed": row["derivation_closed"],
        "ok": ok,
        "note": row["note"],
    }

def check_square_face_holonomy_probe(device: str = "cpu") -> dict:
    """§8.2·geo — Phi_□ hull holonomy probe; alpha from lattice E open (not pi ansatz)."""
    from mt_ca.si_constants import SI

    row = SI.square_face_holonomy_probe_row(grid=16, device=device)
    ok = (
        abs(row["edge_a_over_l_P"] - 1.0) < 1e-12
        and abs(row["phi_square_vac_rad"]) < 0.2
        and abs(row["delta_phi_nn_vortex"]) > 0.5
        and row["readout_ok"]
        and row["alpha_match_open"]
        and row["V_over_v_hV"] == 16.0 / 3.0
    )
    return {
        "id": "Phi_square_probe",
        "phi_square_vortex_rad": row["phi_square_vortex_rad"],
        "delta_phi_nn_vortex": row["delta_phi_nn_vortex"],
        "delta_phi_nn_alpha_link": row["delta_phi_nn_alpha_link"],
        "alpha_link_readout_rel_err": row["alpha_link_readout_rel_err"],
        "B_square_vortex_T": row["B_square_vortex_T"],
        "alpha_fs": row["alpha_fs"],
        "alpha_from_E_rel_err": row["alpha_from_E_rel_err"],
        "alpha_match_open": row["alpha_match_open"],
        "readout_ok": row["readout_ok"],
        "ok": ok,
        "note": row["note"],
    }

def check_cuboctahedron_carrier(device: str = "cpu") -> dict:
    """§8.2·geo — body ratio inventory; derived κ/κ_link/V identity; holonomy/α open."""
    from mt_ca.si_constants import KAPPA_FCC_1TICK, N12_FCC_CAUSAL_LINKS, SI, kappa_link

    del device
    row = SI.cuboctahedron_carrier_inventory_row()
    inv = row["ratio_inventory"]
    by_id = {str(r["id"]): r for r in inv}
    ok = (
        abs(row["V_over_v_hV"] - 16.0 / 3.0) < 1e-12
        and abs(float(by_id["edge_a_anchor"]["ratio"]) - 1.0) < 1e-12
        and abs(row["edge_a_m"] - SI.l_P) / SI.l_P < 1e-12
        and abs(float(by_id["kappa_inscr_1tick"]["ratio"]) - KAPPA_FCC_1TICK) < 1e-12
        and abs(float(by_id["kappa_link"]["ratio"]) - kappa_link(n_links=N12_FCC_CAUSAL_LINKS)) < 1e-12
        and by_id["Phi_square_holonomy"]["status"] == "open"
        and by_id["alpha_fs_derived"]["status"] == "derived_T"
        and len(row["anchor_chain"]) >= 8
        and int(row["ratio_derived_count"]) >= 3
        and int(row["ratio_open_count"]) >= 4
        and len(inv) >= 14
    )
    return {
        "id": "Cuboctahedron",
        "edge_a_m": row["edge_a_m"],
        "V_over_v_hV": row["V_over_v_hV"],
        "V_over_S_m": row["V_over_S_m"],
        "V_over_S_over_l_P": row["V_over_S_over_l_P"],
        "n_square_over_n_triangle": row["n_square_over_n_triangle"],
        "ratio_derived_count": row["ratio_derived_count"],
        "ratio_open_count": row["ratio_open_count"],
        "ok": ok,
        "note": row["note"],
    }

def check_discreteness_from_axioms(device: str = "cpu") -> dict:
    """§0 Thm 0.1 — discreteness from axioms + bit budget; replaces Postulate 0.1."""
    from mt_ca.si_constants import DELTA_PHI_MIN, SI

    del device
    row = SI.discreteness_from_axioms_row()
    ok = (
        row["replaces_postulate_0_1"] is True
        and row["lemma_a1_fcc_n12"] == 12
        and row["z_min_positive"] is True
        and row["s0_equals_hbar_half"] is True
        and row["p0_equals_hbar_over_2hL"] is True
        and row["p0_equals_m_arg_c0_half"] is True
        and abs(float(row["B_hV_pure"]) - 2.0 * math.pi / math.log(2.0)) < 1e-12
        and int(row["N_phi"]) == 13
        and int(row["N_ring"]) == 512
        and int(row["frac_bits"]) == 6
        and float(row["delta_phi_min_rad"]) == DELTA_PHI_MIN
        and row["c_not_in_discreteness_chain"] is True
    )
    return {
        "id": "Discreteness_from_axioms",
        "B_hV_pure": row["B_hV_pure"],
        "N_ring": row["N_ring"],
        "N_phi": row["N_phi"],
        "z_min_natural": row["z_min_natural"],
        "ok": ok,
        "note": row["note"],
    }

def check_excitations_full_quantization(device: str = "cpu") -> dict:
    """§0.9 / Thm 5.2 — full quantization: no wave on M; sound/light = excitation quanta."""
    from mt_ca.si_constants import SI

    del device
    row = SI.excitations_full_quantization_row()
    ok = (
        row["no_fundamental_wave_on_M"] is True
        and row["energy_transfer_n_E_integer"] is True
        and row["E_equals_n_E_times_E0"] is True
        and row["hbar_nu0_equals_2E0"] is True
        and row["photon_sector_n0"] is True
        and row["E0_ladder_closed"] is True
        and row["continuum_wave_is_T_only"] is True
        and row["madelung_j_is_T_readout"] is True
    )
    return {
        "id": "Excitations_full_quantization",
        "nu0_Hz": row["nu0_Hz"],
        "hbar_nu0_equals_2E0": row["hbar_nu0_equals_2E0"],
        "n_E_example": row["n_E_from_phi_example"],
        "ok": ok,
        "note": row["note"],
    }

def check_phonon_from_carrier(device: str = "cpu") -> dict:
    """§5.2.6 — phonon parameters forced by FCC carrier geometry + hT/hL."""
    from mt_ca.si_constants import SI

    del device
    row = SI.phonon_from_carrier_row()
    ok = (
        int(row["g_acoustic_branches"]) == 3
        and row["n_density_over_sqrt2_lP3"] is True
        and row["v_acoustic_equals_2c0"] is True
        and row["omega_D_equals_v_a_k_max"] is True
        and abs(float(row["omega_D_over_nu0"]) - 1.0) < 1e-12
        and row["hbar_nu0_equals_2E0"] is True
        and row["p0_equals_hbar_k_max_over_2pi"] is True
        and row["phonon_not_sin_wave"] is True
        and row["pressure_wave_not_same_as_phonon_v_a"] is True
    )
    return {
        "id": "Phonon_from_carrier",
        "v_acoustic_m_s": row["v_acoustic_m_s"],
        "v_acoustic_over_c0": row["v_acoustic_over_c0"],
        "omega_D_rad_s": row["omega_D_rad_s"],
        "k_BZ_max_m": row["k_BZ_max_m"],
        "g_acoustic_branches": row["g_acoustic_branches"],
        "ok": ok,
        "note": row["note"],
    }

def check_mechanics_from_axioms(device: str = "cpu") -> dict:
    """§0.8 / Thm 5.1 — Landau mechanics from axioms + Thm 0.1; not separate p/F postulates."""
    from mt_ca.si_constants import DELTA_PHI_MIN, SI

    del device
    row = SI.mechanics_from_axioms_row()
    ok = (
        row["replaces_mechanical_postulates"] is True
        and row["lemma_a5_s0"] is True
        and row["lemma_thm01_p0"] is True
        and row["lemma_L0_equals_s0"] is True
        and row["lemma_F0_equals_m_arg_g_M"] is True
        and row["lemma_p0_equals_m_arg_c0_half"] is True
        and row["lemma_E0_ladder_p0_c0"] is True
        and row["lemma_E0_ladder_F0_hL"] is True
        and row["lemma_E0_ladder_L0_hT"] is True
        and float(row["delta_phi_min_rad"]) == DELTA_PHI_MIN
        and row["continuum_p_L_F_is_T_readout"] is True
        and row["p0_from_hbar_over_2hL_not_macro_c"] is True
    )
    return {
        "id": "Mechanics_from_axioms",
        "s0_J_s": row["s0_J_s"],
        "p0_kg_m_s": row["p0_kg_m_s"],
        "F0_N": row["F0_N"],
        "F0_equals_m_arg_g_M": row["lemma_F0_equals_m_arg_g_M"],
        "ok": ok,
        "note": row["note"],
    }

def check_anchor_a_is_l_P(device: str = "cpu") -> dict:
    """§7.4 — hull edge a ≡ hL ≡ l_P; textbook √(ℏG/c³) is consistency check."""
    from mt_ca.si_constants import SI

    del device
    row = SI.anchor_a_is_l_P_row()
    ok = (
        row["a_equals_l_P"] is True
        and row["a_equals_hL"] is True
        and row["l_P_not_defined_by_c"] is True
        and row["scale_decoupled_from_c_definition"] is True
        and row["v_hV_equals_lP3_over_sqrt2"] is True
        and row["m_arg_mech_equals_em"] is True
        and row["p0_equals_hbar_over_2lP"] is True
        and float(row["l_P_textbook_rel_err"]) < 1e-12
        and row["no_second_ruler"] is True
    )
    return {
        "id": "Anchor_a_lP",
        "a_equals_l_P": row["a_equals_l_P"],
        "l_P_textbook_rel_err": row["l_P_textbook_rel_err"],
        "m_arg_mech_equals_em": row["m_arg_mech_equals_em"],
        "ok": ok,
        "note": row["note"],
    }

def check_planck_from_cell_conditions(device: str = "cpu") -> dict:
    """§7.3 — cell physics + geometry closes μ_P; conventional Planck derived via κ."""
    from mt_ca.si_constants import SI

    del device
    row = SI.planck_from_cell_conditions_row()
    ok = (
        row["closure_rho_cell_equals_mu_P"] is True
        and row["closure_mP_over_lP3_equals_mu_P"] is True
        and row["fluid_u_P_equals_mu_P_c2"] is True
        and row["fluid_c2_equals_K_P_over_mu_P"] is True
        and row["cell_m_arg_equals_mP_over_sqrt2"] is True
        and row["cell_E0_equals_s0_over_hT"] is True
        and row["bekenstein_algebraic"] is True
        and abs(float(row["geometry_v_hV_over_lP3"]) - 1.0 / math.sqrt(2.0)) < 1e-12
        and float(row["conventional_t_P_rel_err"]) < 1e-12
        and float(row["conventional_E_P_rel_err"]) < 1e-12
        and int(row["register_N_phi"]) == 13
        and int(row["register_N_hier"]) == 8
    )
    return {
        "id": "Planck_from_cell",
        "closure_rho_cell_equals_mu_P": row["closure_rho_cell_equals_mu_P"],
        "geometry_v_hV_over_lP3": row["geometry_v_hV_over_lP3"],
        "conventional_t_P_rel_err": row["conventional_t_P_rel_err"],
        "bekenstein_B_hV": row["bekenstein_B_hV"],
        "ok": ok,
        "note": row["note"],
    }

def check_kappa_bottom_up(device: str = "cpu") -> dict:
    """§7.2 — Planck units embed c; κ_geom from hull; c=κc₀ is identity check."""
    from mt_ca.si_constants import KAPPA_FCC_1TICK, SI

    del device
    row = SI.kappa_bottom_up_row()
    kappa = KAPPA_FCC_1TICK
    ok = (
        row["kappa_not_defined_as_c_over_c0"] is True
        and row["kappa_geom_equals_R_in_over_R_out"] is True
        and abs(float(row["kappa_geom_FCC"]) - kappa) < 1e-12
        and row["hT_equals_kappa_geom_times_t_P"] is True
        and row["c0_equals_l_P_over_hT"] is True
        and row["c_equals_kappa_c0_check"] is True
        and row["c_over_c0_equals_kappa_check"] is True
        and row["c0_over_c_equals_inv_kappa"] is True
        and row["E_0_over_E_P_equals_kappa"] is True
        and abs(float(row["hT_over_t_P"]) - kappa) < 1e-12
        and float(row["l_P_rel_err"]) < 1e-12
        and row["t_P_equals_l_P_over_c"] is True
    )
    return {
        "id": "Kappa_bottom_up",
        "kappa_geom_FCC": row["kappa_geom_FCC"],
        "hT_over_t_P": row["hT_over_t_P"],
        "c0_over_c": row["c0_over_c"],
        "E_0_over_E_P": row["E_0_over_E_P"],
        "ok": ok,
        "note": row["note"],
    }

def check_rhombic_dodecahedron_geometry(device: str = "cpu") -> dict:
    """§8.2·geo·voronoi — FCC Voronoy cell; dual to cuboctahedron; V=v_hV."""
    from mt_ca.si_constants import KAPPA_FCC_1TICK, SI

    del device
    row = SI.rhombic_dodecahedron_geometry_row()
    ok = (
        abs(row["V_over_v_hV"] - 1.0) < 1e-12
        and abs(row["edge_a_over_l_P"] - 1.0) < 1e-12
        and abs(row["R_in_over_a"] - 0.5) < 1e-12
        and abs(row["V_cuboctahedron_over_V_voronoi"] - 16.0 / 3.0) < 1e-12
        and abs(row["R_in_Voronoi_over_R_in_cuboctahedron_1tick"] - KAPPA_FCC_1TICK) < 1e-12
        and row["R_in_Voronoi_eq_kappa_times_R_in_cuboctahedron"] is True
        and abs(row["V_over_S_over_a"] - 1.0 / 16.0) < 1e-12
        and abs(row["R_vertex_axis_over_a"] - KAPPA_FCC_1TICK) < 1e-12
        and row["n_faces_rhomb"] == 12
        and row["n_vertices"] == 14
        and row["n_edges"] == 24
        and abs(row["rhombus_acute_cos"] - 1.0 / 3.0) < 1e-12
    )
    return {
        "id": "Rhombic_dodecahedron_geo",
        "edge_a_m": row["edge_a_m"],
        "V_over_v_hV": row["V_over_v_hV"],
        "R_in_Voronoi_m": row["R_in_Voronoi_m"],
        "V_cuboctahedron_over_V_voronoi": row["V_cuboctahedron_over_V_voronoi"],
        "V_over_S_over_a": row["V_over_S_over_a"],
        "ok": ok,
        "note": row["note"],
    }

def check_rhombic_dodecahedron_carrier(device: str = "cpu") -> dict:
    """§8.2·geo·voronoi — Voronoy vs hull inventory."""
    from mt_ca.si_constants import SI

    del device
    row = SI.rhombic_dodecahedron_carrier_inventory_row()
    inv = row["ratio_inventory"]
    by_id = {str(r["id"]): r for r in inv}
    ok = (
        abs(row["V_over_v_hV"] - 1.0) < 1e-12
        and abs(row["V_cuboctahedron_over_V_voronoi"] - 16.0 / 3.0) < 1e-12
        and abs(float(by_id["R_in_Voronoi"]["ratio"]) - 0.5) < 1e-12
        and by_id["V_over_v_hV"]["status"] == "derived"
        and by_id["R_in_Voronoi"]["status"] == "derived"
        and len(row["ratio_inventory"]) >= 6
    )
    return {
        "id": "Rhombic_dodecahedron",
        "V_over_v_hV": row["V_over_v_hV"],
        "R_in_Voronoi_m": row["R_in_Voronoi_m"],
        "V_cuboctahedron_over_V_voronoi": row["V_cuboctahedron_over_V_voronoi"],
        "ratio_derived_count": row["ratio_derived_count"],
        "ok": ok,
        "note": row["note"],
    }

def check_cuboctahedron_geometry(device: str = "cpu") -> dict:
    """§8.2·geo — cuboctahedron V=(16/3)v_hV; discrete α candidate vs derived π."""
    from mt_ca.si_constants import SI

    del device
    row = SI.cuboctahedron_geometry_row()
    ok = (
        abs(row["V_over_v_hV"] - 16.0 / 3.0) < 1e-12
        and abs(row["edge_a_over_l_P"] - 1.0) < 1e-12
        and abs(row["R_in_over_R_out_1tick"] - 1.0 / math.sqrt(2.0)) < 1e-12
        and abs(row["A_square_one_m2"] - row["edge_a_m"] ** 2) < 1e-24 * row["edge_a_m"] ** 2
        and row["n_faces_square"] == 6
        and row["n_faces_triangle"] == 8
        and row["alpha_fs_inv_geom"] == 137.0
        and row["alpha_inv_geom_rel_err"] < 0.001
        and row["alpha_inv_derived_rel_err"] < 1e-5
    )
    return {
        "id": "Cuboctahedron_geo",
        "edge_a_m": row["edge_a_m"],
        "V_over_v_hV": row["V_over_v_hV"],
        "V_over_S_m": row["V_over_S_m"],
        "alpha_fs_inv_geom": row["alpha_fs_inv_geom"],
        "alpha_inv_geom_rel_err": row["alpha_inv_geom_rel_err"],
        "alpha_inv_derived_rel_err": row["alpha_inv_derived_rel_err"],
        "ok": ok,
        "note": row["note"],
    }

def check_vacuum_bath(device: str = "cpu") -> dict:
    """§8.2·vac — A5 boiling bath algebra vs CMB reference (not same object)."""
    from mt_ca.si_constants import SI

    del device
    row = SI.vacuum_bath_row()
    four_pi = 4.0 * math.pi
    ok = (
        abs(row["h_nu0_over_E0"] - four_pi) / four_pi < 1e-12
        and row["rho_E_vac_J_m3"] > 0.0
        and row["z_min"] == 2.0 ** (-row["frac_bits"])
        and row["T_M_bath_K"] < row["T_uP_ceiling_K"]
        and row["log10_T_M_bath"] > 30.0
        and row["log10_T_M_bath_over_CMB"] > 28.0
        and row["is_CMB"] is False
        and abs(row["lambda_0_over_l_P"] - (1.0 / math.sqrt(2.0))) / (1.0 / math.sqrt(2.0)) < 1e-12
    )
    return {
        "id": "Vacuum_bath",
        "T_M_bath_K": row["T_M_bath_K"],
        "log10_T_M_bath": row["log10_T_M_bath"],
        "T_CMB_K_ref": row["T_CMB_K_ref"],
        "z_min": row["z_min"],
        "rho_over_uP": row["rho_over_uP"],
        "lambda_0_over_l_P": row["lambda_0_over_l_P"],
        "ok": ok,
        "note": row["note"],
    }

def check_bubble_tick(device: str = "cpu") -> dict:
    """META §3.0.1 — exact bubble age t = N·hT from derived hT (no readout)."""
    from mt_ca.si_constants import SI

    del device
    row = SI.bubble_tick_row()
    ok = (
        row["t_start_s"] == 0.0
        and row["roundtrip_age_rel_err"] == 0.0
        and row["roundtrip_recomb_rel_err"] == 0.0
        and row["N_CMB"] < row["N_today"]
        and 60.9 < row["log10_N_today"] < 61.2
        and 55.5 < row["log10_N_CMB"] < 56.5
        and abs(row["t_age_exact_Gyr"] - row["cosmo_age_Gyr"]) < 1e-12
        and abs(row["t_recomb_exact_kyr"] - row["cosmo_recomb_kyr"]) < 1e-12
    )
    return {
        "id": "Bubble_tick",
        "N_today_sci": row["N_today_sci"],
        "N_CMB_sci": row["N_CMB_sci"],
        "log10_N_today": row["log10_N_today"],
        "t_age_exact_Gyr": row["t_age_exact_Gyr"],
        "t_recomb_exact_kyr": row["t_recomb_exact_kyr"],
        "hT_s": row["hT_s"],
        "ok": ok,
        "note": row["note"],
    }

def check_internal_phase_coords(device: str = "cpu") -> dict:
    """§3.12.6c — CL-O4 probe: canonical (kappa, rho) coords on Z_N_ring."""
    from mt_ca.si_constants import internal_phase_coords_row

    row = internal_phase_coords_row()
    ok = (
        row["N_ring"] == 512
        and row["N_phi"] == 13
        and row["delta_phi_disc"] == 41
        and row["frac_bits"] == 6
        and row["seam_ticks"] == 21
        and row["seam_eq_N_phi_plus_N_hier"]
        and row["naive_kappa_rho_collisions"] == 21
        and row["canonical_bijection_ok"]
        and row["heisenberg_section_rho_zero_ok"]
        and row["delta_inv_mod_N_phi"] == 7
    )
    return {
        "id": "Internal_phase_coords",
        "ok": ok,
        **{k: v for k, v in row.items() if k != "theorem"},
        "note": row["note"],
    }


def check_congruence_ladder(device: str = "cpu") -> dict:
    """§3.12.7 — Z_512 congruence ladder: gcd, half-ring Pauli, n_E ledger."""
    from mt_ca.si_constants import congruence_ladder_row, n_E_from_phi_ticks

    row = congruence_ladder_row()
    ok = (
        row["N_ring"] == 512
        and row["N_phi"] == 13
        and row["N_cluster_eq_N_phi"]
        and row["delta_phi_disc"] == 41
        and row["gcd_delta_phi_N_ring"] == 1
        and row["delta_phi_generates_Z_N"]
        and row["additive_order_delta_phi"] == 512
        and row["gcd_N_phi_N_ring"] == 1
        and row["pauli_equals_half_ring"]
        and row["pauli_kick_disc"] == 256
        and row["energy_ticks_eq_delta_phi_disc"]
        and row["n_E_sample"] == row["n_E_sample_expected"]
        and row["n_E_sample"] == n_E_from_phi_ticks(int(row["n_E_sample_phi_ticks"]))
        and row["ladder_derived_count"] == len(row["ladder_rows"])
        and row["frac_bits"] == 6
        and abs(row["kappa_link_fcc"] - 1.0 / 12.0) < 1e-15
        and row["sync_strength_disc_fcc"] == 3
    )
    return {
        "id": "Congruence_ladder",
        "ok": ok,
        **{k: v for k, v in row.items() if k not in ("ladder_rows", "open_leaves")},
        "ladder_ids": [r["id"] for r in row["ladder_rows"]],
        "open_ids": [r["id"] for r in row["open_leaves"]],
        "note": "§3.12.7: physics->Z_512->congruence; x N_12 in holonomy",
    }

def check_elementary_quanta(device: str = "cpu") -> dict:
    from mt_ca.config import MConfig
    from mt_ca.si_constants import elementary_quanta_row

    row = elementary_quanta_row()
    cfg = MConfig.for_stencil('hex')
    ok = (
        abs(cfg.sync_strength - row["sync_strength_rad"]) < 1e-12
        and abs(cfg.pauli_kick - row["pauli_kick_rad"]) < 1e-12
        and abs(cfg.pauli_rho_min - row["pauli_rho_min_natural"]) < 1e-12
        and abs(cfg.pauli_overlap_cos - row["pauli_overlap_cos"]) < 1e-12
        and row["sync_equals_kappa_times_delta_phi"] == 1.0
        and row["pauli_kick_disc_equals_half_ring"]
        and row["pauli_kick_disc"] == row["N_ring"] // 2
        and row["energy_ticks_per_E0"] == row["delta_phi_min_disc"]
    )
    return {
        "id": "ElementaryQuanta",
        "config_matches_row": ok,
        "row": row,
        "ok": ok,
        "note": "§5.2.3: no mechanical continuous parameters; CODATA only for e₀ T-anchor",
    }

def check_nu_CA_exact(device: str = "cpu") -> dict:
    from mt_ca.si_constants import SI

    nu = SI.nu_CA
    expected = 0.25 * SI.c0 * SI.l_P
    codata = 1.713111e-27
    rel_formula = abs(nu - expected) / expected
    rel_codata = abs(nu - codata) / codata
    ok = rel_formula < 1e-12 and rel_codata < 1e-6
    return {
        "id": "Nu_CA",
        "nu_CA_m2_s": nu,
        "formula_rel_err": rel_formula,
        "codata_rel_err": rel_codata,
        "ok": ok,
        "note": "ν_CA = ¼·c₀·l_P (N₄ lattice gas, §4.1.2)",
    }

def check_hv_bit_budget(device: str = "cpu") -> dict:
    from mt_ca.config import MConfig
    from mt_ca.si_constants import HV, hv_bit_budget_row

    row = hv_bit_budget_row()
    cfg = MConfig.for_stencil('hex')
    ok = (
        row["rel_err"] < 1e-12
        and row["N_phi"] == 13
        and row["mod_bits"] == 9
        and row["N_ring"] == 512
        and row["phase_bits"] == 9
        and row["frac_bits"] == 6
        and abs(row["heisenberg_phi_min_rad"] - 0.5) < 1e-12
        and row["heisenberg_phi_min_disc"] == 41
        and cfg.mod_bits == HV.mod_bits
        and cfg.frac_bits == HV.frac_bits
        and cfg.phase_bits == HV.phase_bits
        and abs(cfg.heisenberg_phi_min - 0.5) < 1e-12
    )
    return {
        "id": "HvBitBudget",
        "ok": ok,
        **{k: v for k, v in row.items()},
        "note": "§3.12.6: B_hV=2π/ln2, N_ring=512, defaults from Planck brick",
    }

def check_rho_P_binary(device: str = "cpu") -> dict:
    from mt_ca.si_constants import SI, macro_density_illusion, planck_density_from_cell

    rho_cell = planck_density_from_cell()
    rel = abs(rho_cell - SI.rho_P) / SI.rho_P
    water_illusion = macro_density_illusion(occupied_fraction=1000.0 / SI.rho_P)
    ok = rel < 1e-12 and abs(water_illusion - 1000.0) / 1000.0 < 1e-6
    return {
        "id": "Rho_P_binary",
        "rho_P_kg_m3": SI.rho_P,
        "m_P_over_lP3": rho_cell,
        "rel_err": rel,
        "water_macro_if_f_occ": water_illusion,
        "ok": ok,
        "note": "M: ρ∈{0,ρ_P}; macro kg/m³ = f_occ·ρ_P (§5.0)",
    }

def check_vdw_algebra(device: str = "cpu") -> dict:
    from mt_ca.si_constants import N_AVOGADRO, SI, vdw_a, vdw_b, vdw_core_volume, vdw_pressure

    nv = 1.0
    n_moles = 1.0
    b = vdw_b(n_moles, n_vortices_per_molecule=nv)
    a = vdw_a(n_vortices_per_molecule=nv)
    b_expected = n_moles * N_AVOGADRO * nv * 4.0 * SI.l_P**3
    a_expected = N_AVOGADRO**2 * nv**2 * SI.K_P * SI.l_P**6 * SI.alpha_fs
    ok = (
        abs(b - b_expected) / b_expected < 1e-12
        and abs(a - a_expected) / a_expected < 1e-12
        and vdw_core_volume() == 4.0 * SI.l_P**3
    )
    p = vdw_pressure(n_moles, 1e-3, 300.0, n_vortices_per_molecule=nv)
    ok = ok and p == p and p > 0.0
    return {
        "id": "VdW_algebra",
        "b_m3": b,
        "a_Pa_m6_mol2": a,
        "sample_P_Pa": p,
        "ok": ok,
        "note": "b=4nN_A N_v l_P³; a=N_A² N_v² K_P l_P⁶ α_fs (§5.3.3)",
    }

def check_mechanical_quantum(device: str = "cpu") -> dict:
    from mt_ca.si_constants import SI, mechanical_quantum_row

    row = mechanical_quantum_row()
    ok = (
        abs(row["L_0_J_s"] - SI.s_0) / SI.s_0 < 1e-12
        and abs(row["p_0_kg_m_s"] - SI.p_0) / SI.p_0 < 1e-12
        and abs(row["F_0_N"] - SI.F_0) / SI.F_0 < 1e-12
        and abs(row["L_0_over_hbar"] - 0.5) < 1e-12
        and abs(row["p_0_equals_m_arg_c0_over_2"] - 1.0) < 1e-6
        and abs(row["F_0_equals_m_arg_g_M"] - 1.0) < 1e-6
        and abs(row["F_0_equals_p_0_over_hT"] - 1.0) < 1e-12
    )
    return {
        "id": "MechanicalQuantum",
        "p_0_kg_m_s": row["p_0_kg_m_s"],
        "L_0_J_s": row["L_0_J_s"],
        "F_0_N": row["F_0_N"],
        "g_M_m_s2": row["g_M_m_s2"],
        "p_0_over_half_mP_c": row["p_0_over_half_mP_c"],
        "F_0_equals_m_arg_g_M": row["F_0_equals_m_arg_g_M"],
        "ok": ok,
        "note": "p₀=m_arg·c₀/2; F₀=m_arg·g_M; dF=dm·g (§5.2.1)",
    }

def check_quarter_quantum(device: str = "cpu") -> dict:
    from mt_ca.config import MConfig
    from mt_ca.laplacian import stencil_n_links
    from mt_ca.si_constants import (
        N4_CAUSAL_LINKS,
        N6_CAUSAL_LINKS,
        N12_FCC_CAUSAL_LINKS,
        kappa_link,
        quarter_quantum_row,
    )

    row = quarter_quantum_row()  # N₄ archive MVP
    cfg_n4 = MConfig.for_stencil("n4")
    cfg_hex = MConfig.for_stencil("hex")
    cfg_fcc = MConfig.for_stencil("fcc")
    ok_n4 = (
        row["N4_links"] == N4_CAUSAL_LINKS
        and abs(row["kappa_link"] - 0.25) < 1e-12
        and abs(row["gamma"] - row["cr_strength"]) < 1e-12
        and abs(row["gamma"] - row["nu_CA_natural"]) < 1e-12
        and abs(cfg_n4.gamma - kappa_link(n_links=N4_CAUSAL_LINKS)) < 1e-12
    )
    ok_hex = abs(cfg_hex.gamma - kappa_link(n_links=N6_CAUSAL_LINKS)) < 1e-12
    ok_fcc = (
        abs(cfg_fcc.gamma - kappa_link(n_links=N12_FCC_CAUSAL_LINKS)) < 1e-12
        and stencil_n_links("fcc") == 12
    )
    ok = ok_n4 and ok_hex and ok_fcc
    return {
        "id": "QuarterQuantum",
        "kappa_n4": cfg_n4.gamma,
        "kappa_hex": cfg_hex.gamma,
        "kappa_fcc": cfg_fcc.gamma,
        "nu_CA_natural": row["nu_CA_natural"],
        "ok": ok,
        "note": "κ_link=1/|N|: n4=¼ · hex=⅙ · fcc=1/12 (§5.2.2 · §1.6)",
    }

def check_energy_quantum(device: str = "cpu") -> dict:
    from mt_ca.si_constants import SI, energy_quantum_row

    row = energy_quantum_row()
    ok = (
        row["rel_p0_c0"] < 1e-12
        and row["rel_F0_lP"] < 1e-12
        and row["rel_L0_hT"] < 1e-12
        and abs(row["E_0_J"] - SI.E_0) / SI.E_0 < 1e-12
    )
    return {
        "id": "EnergyQuantum",
        "E_0_J": row["E_0_J"],
        "rel_p0_c0": row["rel_p0_c0"],
        "rel_F0_lP": row["rel_F0_lP"],
        "rel_L0_hT": row["rel_L0_hT"],
        "ok": ok,
        "note": "E₀=p₀·c₀=F₀·l_P=L₀/hT=s₀/hT (§5.2.2)",
    }

def check_arg_quantum(device: str = "cpu") -> dict:
    from mt_ca.si_constants import M_HIGGS_GEV, SI, arg_quantum_row

    row = arg_quantum_row()
    s0_expected = SI.hbar / 2.0
    e0_expected = SI.E_P / math.sqrt(2.0)
    m_expected = SI.m_P / math.sqrt(2.0)
    ok = (
        abs(row["s_0_J_s"] - s0_expected) / s0_expected < 1e-12
        and abs(row["E_0_J"] - e0_expected) / e0_expected < 1e-12
        and abs(row["m_arg_kg"] - m_expected) / m_expected < 1e-12
        and row["v_arg_m_s"] == SI.c0
        and row["E_0_over_E_Higgs"] > 1e16
    )
    return {
        "id": "Arg_quantum",
        "s_0_J_s": row["s_0_J_s"],
        "E_0_J": row["E_0_J"],
        "E_0_eV": row["E_0_eV"],
        "m_arg_kg": row["m_arg_kg"],
        "v_arg_m_s": row["v_arg_m_s"],
        "E_0_over_E_Higgs": row["E_0_over_E_Higgs"],
        "Higgs_GeV": M_HIGGS_GEV,
        "ok": ok,
        "note": "s₀=ℏ/2, E₀=E_P/√2, m_arg=m_P/√2, v_arg=c₀ (§5.0.2)",
    }

def check_planck_vacuum_floor(size: int = 32, device: str = "cpu") -> dict:
    """§0.5 / §10.2: vacuum_amplitude = z_min; full Z_N ocean; HF ON does not fill."""
    from mt_ca.fixed_point import vacuum_amplitude_quantum
    from mt_ca.projected_collision import projected_collision_kick
    from mt_ca.simulator import LatticeFluidSimulator

    cfg = MConfig.for_stencil('hex', heisenberg_floor=True)
    dev = torch.device(device)
    z_min = vacuum_amplitude_quantum(frac_bits=cfg.frac_bits)
    amp_match = abs(cfg.vacuum_amplitude - z_min) < 1e-12

    sim = LatticeFluidSimulator(size, size, cfg, device=dev)
    sim.reset(SeedClass.VACUUM)
    from mt_ca.metrics import field_amplitude

    decoded_min = float(field_amplitude(sim.z).min().item())
    above_floor = decoded_min >= 0.5 * z_min
    n0 = float(sim.norm())
    for _ in range(64):
        sim.step(1)
    n1 = float(sim.norm())
    rho = sim.z.abs().square().sum(-1)
    frac_sat = float((rho > 0.9).float().mean().item())
    # Holomorphic vacuum may have ⌊𝒩⌋=0 locally (§2.3.8); must not fill under HF.
    stable = frac_sat < 0.05 and abs(n1 - n0) / max(n0, 1e-12) < 0.5

    ok = amp_match and above_floor and stable
    return {
        "id": "PlanckVacuumFloor",
        "z_min": z_min,
        "vacuum_amplitude": cfg.vacuum_amplitude,
        "decoded_min": decoded_min,
        "norm0": n0,
        "norm64": n1,
        "frac_sat": frac_sat,
        "ok": ok,
        "note": "§0.5: full brick ocean; HF snap-down; long-run no fill",
    }

def check_ladder_ledger(size: int = 64, device: str = "cpu") -> dict:
    from mt_ca.ledger import ladder_ledger_report

    return ladder_ledger_report(size, device=device)

