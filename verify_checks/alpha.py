"""verify_checks.alpha — extracted from verify_principles"""
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


def check_alpha_hop_ladder(device: str = "cpu") -> dict:
    """§7.4+§4.8+H probe — α = κ·N_re/N_c0 = N_★/N_c0 = N_c/N_a0; α²=N_re/N_a0; derivation OPEN."""
    from mt_ca.si_constants import SI

    del device
    row = SI.alpha_hop_ladder_row()
    ok = (
        bool(row["identity_ok"])
        and float(row["rel_kappa_form"]) < 1e-12
        and float(row["rel_star_form"]) < 1e-12
        and float(row["rel_bohr_form"]) < 1e-12
        and float(row["rel_alpha2_ladder"]) < 1e-12
        and bool(row["derivation_open"])
        and abs(float(row["N12_times_N12p1"]) - 156.0) < 1e-12
    )
    return {
        "id": "Alpha_hop_ladder",
        "alpha_from_kappa_Nre_over_Nc0": row["alpha_from_kappa_Nre_over_Nc0"],
        "alpha_from_Nstar_over_Nc0": row["alpha_from_Nstar_over_Nc0"],
        "alpha_from_Nc_over_Na0": row["alpha_from_Nc_over_Na0"],
        "alpha2_from_Nre_over_Na0": row["alpha2_from_Nre_over_Na0"],
        "v_Bohr_over_c0": row["v_Bohr_over_c0"],
        "N_a0_Bohr": row["N_a0_Bohr"],
        "alpha_codata": row["alpha_codata"],
        "N_c0_link": row["N_c0_link"],
        "N_re": row["N_re"],
        "N_star_m_c_c0": row["N_star_m_c_c0"],
        "N12_times_N12p1": row["N12_times_N12p1"],
        "derivation_open": row["derivation_open"],
        "ok": ok,
        "note": row["note"],
    }

def check_alpha_fixed_point(device: str = "cpu") -> dict:
    """First FP: analytic bare α*=[N_φ/(N_a0√(π/2))]^{1/11}; stack poly 23°; seed-invariant."""
    from mt_ca.si_constants import SI

    del device
    row = SI.alpha_fixed_point_row()
    ok = (
        bool(row["fixed_point_ok"])
        and bool(row["seed_invariant"])
        and bool(row["analytic_bare_ok"])
        and bool(row["analytic_stack_poly_ok"])
        and int(row["exponent"]) == 11
        and float(row["residual_stack"]) < 1e-12
        and float(row["residual_bare"]) < 1e-12
        and abs(float(row["alpha_fp_bare"]) - float(row["alpha_bare_analytic"])) < 1e-15
        and abs(float(row["alpha_fp_stack_inv"]) - 137.09186727) < 1e-4
        and bool(row["derivation_open"])
    )
    return {
        "id": "Alpha_fixed_point",
        "alpha_bare_analytic": row["alpha_bare_analytic"],
        "alpha_bare_analytic_inv": row["alpha_bare_analytic_inv"],
        "alpha_fp_stack": row["alpha_fp_stack"],
        "alpha_fp_stack_inv": row["alpha_fp_stack_inv"],
        "exponent": row["exponent"],
        "vs_codata_ppm_stack": row["vs_codata_ppm_stack"],
        "vs_codata_ppm_bare": row["vs_codata_ppm_bare"],
        "analytic_bare_ok": row["analytic_bare_ok"],
        "analytic_stack_poly_ok": row["analytic_stack_poly_ok"],
        "seed_invariant": row["seed_invariant"],
        "derivation_open": row["derivation_open"],
        "ok": ok,
        "note": row["note"],
    }

def check_alpha_force_lattice(device: str = "cpu") -> dict:
    """§8.2·F — α=κ/M from F₀ lattice; M from g still OPEN."""
    from mt_ca.si_constants import SI

    del device
    row = SI.alpha_force_lattice_row()
    ok = (
        bool(row["checks_ok"])
        and bool(row["M_from_g_open"])
        and not bool(row["replaces_pi_ansatz"])
        and abs(float(row["M_N12_Nhier"]) - 96.0) < 1e-12
        and abs(float(row["vs_codata_ppm_M97"]) + 1040.4) < 1.0
        and abs(float(row["vs_codata_ppm_M96"]) - 9365.5) < 1.0
    )
    return {
        "id": "Alpha_force_lattice",
        "M_target_CODATA": row["M_target_CODATA"],
        "alpha_M96_inv": row["alpha_M96_inv"],
        "alpha_M97_inv": row["alpha_M97_inv"],
        "vs_codata_ppm_M96": row["vs_codata_ppm_M96"],
        "vs_codata_ppm_M97": row["vs_codata_ppm_M97"],
        "M_from_g_open": row["M_from_g_open"],
        "ok": ok,
        "note": row["note"],
    }

def check_alpha_meaning(device: str = "cpu") -> dict:
    """§8.2·α·meaning — α is phase↔vacuum coupling; soft residual OPEN."""
    from mt_ca.si_constants import SI

    del device
    row = SI.alpha_meaning_row()
    ok = (
        bool(row["checks_ok"])
        and bool(row["residue_equals_1_over_4pi"])
        and bool(row["discrete_coupling_open"])
        and not bool(row["replaces_pi_ansatz"])
        and abs(float(row["vs_codata_ppm_pi"])) < 1.0
    )
    return {
        "id": "Alpha_meaning",
        "planck_hole_phase_residue": row["planck_hole_phase_residue"],
        "four_pi_times_alpha": row["four_pi_times_alpha"],
        "alpha_fs_inv": row["alpha_fs_inv"],
        "discrete_coupling_open": row["discrete_coupling_open"],
        "ok": ok,
        "note": row["note"],
    }

def check_alpha_descent(device: str = "cpu") -> dict:
    """§8.2·α·descent — amnesia vacuum→coupling; fraction OPEN."""
    from mt_ca.si_constants import SI

    del device
    row = SI.alpha_descent_row()
    ok = (
        bool(row["checks_ok"])
        and bool(row["residue_is_not_alpha"])
        and bool(row["coupling_fraction_open"])
        and not bool(row["used_alpha_fs_as_input"])
        and int(row["N_phi"]) == 13
        and int(row["alpha_geom_inv"]) == 137
        and abs(float(row["vs_codata_ppm_pi_AFTER"]) + 2.223) < 0.01
    )
    return {
        "id": "Alpha_descent",
        "planck_hole_phase_residue": row["planck_hole_phase_residue"],
        "N_phi": row["N_phi"],
        "alpha_geom_inv": row["alpha_geom_inv"],
        "vs_codata_ppm_pi_AFTER": row["vs_codata_ppm_pi_AFTER"],
        "vs_codata_ppm_geom": row["vs_codata_ppm_geom"],
        "coupling_fraction_open": row["coupling_fraction_open"],
        "ok": ok,
        "note": row["note"],
    }

def check_alpha_mass_defect_optics(device: str = "cpu") -> dict:
    """§8.2·α·mass-defect — QM Δm and α are one upstairs."""
    from mt_ca.si_constants import SI

    del device
    row = SI.alpha_mass_defect_optics_row()
    ok = (
        bool(row["checks_ok"])
        and abs(float(row["rel_alpha_from_dm"])) < 1e-12
        and abs(float(row["U_a0_over_BE"]) - 2.0) < 1e-12
        and abs(float(row["E_coul_NN_over_E0"]) - float(row["alpha_over_kappa"])) < 1e-12
    )
    return {
        "id": "Alpha_mass_defect_optics",
        "delta_m_over_m_e": row["delta_m_over_m_e"],
        "alpha_from_mass_defect": row["alpha_from_mass_defect"],
        "U_a0_over_BE": row["U_a0_over_BE"],
        "E_coul_NN_over_E0": row["E_coul_NN_over_E0"],
        "BE_over_E0": row["BE_over_E0"],
        "ok": ok,
        "note": row["note"],
    }

def check_alpha_arg_binding_try(device: str = "cpu") -> dict:
    """§8.2·α·Arg-try — Arg ledger identity; derivation still open."""
    from mt_ca.si_constants import SI

    del device
    row = SI.alpha_arg_binding_try_row()
    ok = (
        bool(row["checks_ok"])
        and not bool(row["derivation_closed"])
        and abs(float(row["rel_arg_identity"])) < 1e-12
    )
    return {
        "id": "Alpha_arg_binding_try",
        "M_star": row["M_star"],
        "delta_m_over_m_arg": row["delta_m_over_m_arg"],
        "try_M97_ppm": row["try_M97_ppm"],
        "derivation_closed": row["derivation_closed"],
        "ok": ok,
        "note": row["note"],
    }

def check_alpha_schwinger(device: str = "cpu") -> dict:
    """§8.2·α·Schwinger — lab door ae; phase residue explains 1/(2π)."""
    from mt_ca.si_constants import SI

    del device
    row = SI.alpha_schwinger_row()
    ok = (
        bool(row["checks_ok"])
        and not bool(row["derivation_closed"])
        and abs(float(row["rel_2ar_vs_schwinger"])) < 1e-15
    )
    return {
        "id": "Alpha_schwinger",
        "ae_Schwinger_1loop": row["ae_Schwinger_1loop"],
        "vacuum_phase_residue_r": row["vacuum_phase_residue_r"],
        "one_loop_vs_ae_ppm": row["one_loop_vs_ae_ppm"],
        "derivation_closed": row["derivation_closed"],
        "ok": ok,
        "note": row["note"],
    }

def check_alpha_dirac_g2(device: str = "cpu") -> dict:
    """§8.2·α·g2 — bare g=2 closed; A5→ae still open."""
    from mt_ca.si_constants import SI

    del device
    row = SI.alpha_dirac_g2_row()
    ok = (
        bool(row["checks_ok"])
        and bool(row["bare_g2_closed"])
        and not bool(row["derivation_ae_closed"])
        and abs(float(row["g_bare"]) - 2.0) < 1e-15
    )
    return {
        "id": "Alpha_dirac_g2",
        "g_bare": row["g_bare"],
        "ae_bare": row["ae_bare"],
        "bare_g2_closed": row["bare_g2_closed"],
        "derivation_ae_closed": row["derivation_ae_closed"],
        "ok": ok,
        "note": row["note"],
    }

def check_alpha_ae_cloud(device: str = "cpu") -> dict:
    """§8.2·α·ae — ae=α·2r factors; does not bypass coupling OPEN."""
    from mt_ca.si_constants import SI

    del device
    row = SI.alpha_ae_cloud_row()
    ok = (
        bool(row["checks_ok"])
        and bool(row["factorization_closed"])
        and not bool(row["derivation_ae_closed"])
        and not bool(row["bypasses_coupling_open"])
        and abs(float(row["best_geo_ppm"])) > 1e3
    )
    return {
        "id": "Alpha_ae_cloud",
        "two_r": row["two_r"],
        "best_geo_try": row["best_geo_try"],
        "best_geo_ppm": row["best_geo_ppm"],
        "factorization_closed": row["factorization_closed"],
        "derivation_ae_closed": row["derivation_ae_closed"],
        "bypasses_coupling_open": row["bypasses_coupling_open"],
        "ok": ok,
        "note": row["note"],
    }

def check_alpha_rydberg_hall(device: str = "cpu") -> dict:
    """§8.2·α·Rydberg·Hall — lab doors; R_∞ phase-residue identity; same coupling OPEN."""
    from mt_ca.si_constants import SI

    del device
    row = SI.alpha_rydberg_hall_row()
    ok = (
        bool(row["checks_ok"])
        and bool(row["factorization_rydberg_closed"])
        and not bool(row["hall_is_alpha_source_post2019"])
        and not bool(row["derivation_closed"])
        and not bool(row["bypasses_coupling_open"])
        and abs(float(row["rel_Rinf_phase_residue_vs_classic"])) < 1e-15
    )
    return {
        "id": "Alpha_rydberg_hall",
        "Rinf_vs_codata_ppm": row["Rinf_vs_codata_ppm"],
        "Hall_legacy_vs_codata_ppm": row["Hall_legacy_vs_codata_ppm"],
        "hall_is_alpha_source_post2019": row["hall_is_alpha_source_post2019"],
        "derivation_closed": row["derivation_closed"],
        "ok": ok,
        "note": row["note"],
    }

def check_alpha_em_face_weight(device: str = "cpu") -> dict:
    """§8.2·α·EM·faces — area/dihedral ≠ α; Φ_□ still open."""
    from mt_ca.si_constants import SI

    del device
    row = SI.alpha_em_face_weight_row()
    ok = (
        bool(row["checks_ok"])
        and not bool(row["face_weight_is_alpha"])
        and not bool(row["derivation_closed"])
        and not bool(row["bypasses_coupling_open"])
        and abs(float(row["best_ppm"])) > 1e3
    )
    return {
        "id": "Alpha_em_face_weight",
        "w_square": row["w_square"],
        "best_try": row["best_try"],
        "best_ppm": row["best_ppm"],
        "face_weight_is_alpha": row["face_weight_is_alpha"],
        "derivation_closed": row["derivation_closed"],
        "ok": ok,
        "note": row["note"],
    }

def check_alpha_dual_fraction(device: str = "cpu") -> dict:
    """§8.2·α·dual — α=m/n via two independent paths; inventory pairs."""
    from mt_ca.si_constants import SI

    del device
    row = SI.alpha_dual_fraction_row()
    strongest = str(row["strongest_alive_pair"])
    ok = (
        bool(row["checks_ok"])
        and not bool(row["derivation_closed"])
        and bool(row.get("M_combinatorial_closed", False))
        and ("soft face" in strongest or strongest.startswith("force"))
    )
    return {
        "id": "Alpha_dual_fraction",
        "strongest_alive_pair": row["strongest_alive_pair"],
        "M_combinatorial_closed": row.get("M_combinatorial_closed"),
        "M_target": row["M_target"],
        "kappa": row["kappa"],
        "derivation_closed": row["derivation_closed"],
        "ok": ok,
        "note": row["note"],
    }

def check_alpha_sqrt2_descent(device: str = "cpu") -> dict:
    """§8.2·α·√2·descent — force dual ⇒ α∉ℚ; reject exact p/q."""
    from mt_ca.si_constants import SI

    del device
    row = SI.alpha_sqrt2_descent_row()
    ok = (
        bool(row["checks_ok"])
        and bool(row["lemma_force_alpha_not_rational"])
        and bool(row["reject_exact_rational_alpha_under_force"])
        and bool(row["derivation_M_closed"])
        and abs(float(row["kappa"]) ** 2 - 0.5) < 1e-15
    )
    return {
        "id": "Alpha_sqrt2_descent",
        "kappa": row["kappa"],
        "M_target": row["M_target"],
        "lemma_force_alpha_not_rational": row["lemma_force_alpha_not_rational"],
        "derivation_M_closed": row["derivation_M_closed"],
        "ok": ok,
        "note": row["note"],
    }

def check_alpha_M_from_g_try(device: str = "cpu") -> dict:
    """§8.2·α·M·g·try — M=1+N12·N_hier theorem (proof via nF Thm)."""
    from mt_ca.si_constants import SI

    del device
    row = SI.alpha_M_from_g_try_row()
    ok = (
        bool(row["checks_ok"])
        and bool(row["story_ok"])
        and bool(row["derivation_closed"])
        and int(row["M_try"]) == 97
    )
    return {
        "id": "Alpha_M_from_g_try",
        "M_try": row["M_try"],
        "alpha_try": row["alpha_try"],
        "vs_codata_ppm": row["vs_codata_ppm"],
        "derivation_closed": row["derivation_closed"],
        "ok": ok,
        "note": row["note"],
    }

def check_alpha_nF_momentum_registry(device: str = "cpu") -> dict:
    """§8.2·α·nF·Thm — lemmas force unique M=97 (momentum registry seats)."""
    from mt_ca.si_constants import SI

    del device
    row = SI.alpha_nF_momentum_registry_row()
    ok = (
        bool(row["checks_ok"])
        and bool(row["census_ok"])
        and bool(row["derivation_closed"])
        and not bool(row["runtime_sim_closed"])
        and int(row["n_F_seats"]) == 97
        and int(row["n_core"]) == 1
        and int(row["n_link_hier"]) == 96
    )
    return {
        "id": "Alpha_nF_momentum_registry",
        "n_F_seats": row["n_F_seats"],
        "M": row["M"],
        "alpha": row["alpha"],
        "vs_codata_ppm": row["vs_codata_ppm"],
        "derivation_closed": row["derivation_closed"],
        "ok": ok,
        "note": row["note"],
    }

def check_alpha_full_quantization_bridge(device: str = "cpu") -> dict:
    """§8.2·α·full-quant — α=κ/M from full quantization; pi-tower removed; alpha=fundamentals."""
    from mt_ca.si_constants import SI

    del device
    row = SI.alpha_full_quantization_bridge_row()
    ok = (
        bool(row["checks_ok"])
        and bool(row["discrete_path_derived"])
        and bool(row["M_combinatorial_closed"])
        and bool(row["pi_tower_absent"])
        and bool(row["soft_residual_open"])
        and not bool(row["derivation_closed"])
        and int(row["M"]) == 97
    )
    return {
        "id": "Alpha_full_quantization_bridge",
        "M": row["M"],
        "alpha": row["alpha"],
        "vs_codata_ppm_discrete": row["vs_codata_ppm_discrete"],
        "vs_codata_ppm_pi_tower": row["vs_codata_ppm_pi_tower"],
        "discrete_path_derived": row["discrete_path_derived"],
        "soft_residual_open": row["soft_residual_open"],
        "ok": ok,
        "note": row["note"],
    }

def check_alpha_upstairs_mass_probe(device=None):
    from mt_ca.si_constants import SI

    del device
    r = SI.alpha_upstairs_mass_probe_row()
    ok = (
        bool(r["checks_ok"])
        and bool(r["derivation_closed"])
        and bool(r["cascade_law_closed"])
        and bool(r["pi_tower_not_input"])
        and bool(r["soft_floors_open"])
    )
    return {
        "id": "Alpha_upstairs_mass_probe",
        "ok": ok,
        "derivation_closed": r["derivation_closed"],
        "cascade_law_closed": r["cascade_law_closed"],
        "v_GeV": r["v_GeV"],
        "m_H_GeV": r["m_H_GeV"],
        "m_H_rel_err": r["m_H_rel_err"],
        "m_p_rel_err": r["m_p_rel_err"],
        "m_e_rel_err": r["m_e_rel_err"],
        "m_n_rel_err": r["m_n_rel_err"],
        "note": r["note"],
    }

def check_alpha_si_bridge(device: str = "cpu") -> dict:
    """§8.2·α·SI-bridge — carrier α exact (no u(α)); U0 packet; T-door optional."""
    from mt_ca.si_constants import SI

    del device
    row = SI.alpha_si_bridge_row()
    ok = (
        bool(row["checks_ok"])
        and bool(row["derivation_closed"])
        and bool(row["macros_not_inputs"])
        and bool(row["alpha_exact"])
        and bool(row["no_u_alpha"])
        and bool(row["identity_hbar_c_eq_2kappa_U0"])
        and bool(row["identity_pref_eq_dU"])
        and bool(row["identity_pref_eq_cleared"])
        and int(row["M"]) == 97
        and int(row["d"]) == 7
        and int(row["codata_year"]) == 2022
    )
    return {
        "id": "Alpha_si_bridge",
        "M": row["M"],
        "d": row["d"],
        "U": row["U"],
        "alpha_preferred": row["alpha_preferred"],
        "alpha_exact": row["alpha_exact"],
        "no_u_alpha": row["no_u_alpha"],
        "T_lab_contrast_ppm": row["T_lab_contrast_ppm"],
        "hbar_c_over_U0": row["hbar_c_over_U0"],
        "ok": ok,
        "note": row["note"],
    }

def check_alpha_meter_na0_bridge(device: str = "cpu") -> dict:
    """§8.2·α·meter — N_a0/a0 from sealed α; meter not input to α."""
    from mt_ca.si_constants import SI

    del device
    row = SI.alpha_meter_na0_bridge_row()
    ok = (
        bool(row["checks_ok"])
        and bool(row["derivation_closed"])
        and bool(row["meter_not_input_to_alpha"])
        and bool(row["meter_not_on_M"])
        and bool(row["SI_metre_is_T_export_only"])
        and bool(row["M_lengths_are_hops"])
        and bool(row["optical_a0_is_T_door_only"])
        and bool(row["alpha_path_closed"])
        and bool(row["identity_alpha_eq_Nc_over_Na0"])
        and bool(row["identity_a0_bohr_eq_Na0_lP"])
        and (not bool(row["independent_Na0_blocks_alpha"]))
        and float(row["T_lab_rel_vs_optical_a0"]) < 1e-2
    )
    return {
        "id": "Alpha_meter_na0_bridge",
        "alpha_preferred": row["alpha_preferred"],
        "N_c": row["N_c"],
        "N_a0_predicted": row["N_a0_predicted"],
        "T_lab_rel_vs_optical_a0": row["T_lab_rel_vs_optical_a0"],
        "meter_not_input_to_alpha": row["meter_not_input_to_alpha"],
        "alpha_path_closed": row["alpha_path_closed"],
        "ok": ok,
        "note": row["note"],
    }

def check_coulomb_M_native(device: str = "cpu") -> dict:
    """§8.2·Coulomb·M-native — F=n1 n2 F₀/(M N²); α is T-readout only."""
    from mt_ca.si_constants import SI

    del device
    row = SI.coulomb_M_native_row()
    ok = (
        bool(row["checks_ok"])
        and bool(row["identity_alpha_equals_F_NN_over_FP"])
        and bool(row["derivation_closed"])
        and bool(row["soft_residual_open"])
        and int(row["M"]) == 97
        and abs(float(row["F_NN_over_F0"]) - 1.0 / 97.0) < 1e-15
    )
    return {
        "id": "Coulomb_M_native",
        "M": row["M"],
        "alpha_T": row["alpha_T"],
        "F_NN_over_F0": row["F_NN_over_F0"],
        "derivation_closed": row["derivation_closed"],
        "ok": ok,
        "note": row["note"],
    }

def check_alpha_U0_soft_face(device: str = "cpu") -> dict:
    """§8.2 soft face — prefer seat+face unit; inside CODATA 2022 band."""
    from mt_ca.si_constants import SI

    del device
    row = SI.alpha_U0_soft_face_row()
    ok = (
        bool(row["checks_ok"])
        and bool(row["soft_candidate_derived"])
        and bool(row["mechanism_descent_derived"])
        and bool(row["plus_1ppm_explained"])
        and bool(row["axiom_inv_cut_derived"])
        and bool(row["axiom_seat_unit_derived"])
        and bool(row["axiom_seat_plus_face_derived"])
        and bool(row["identity_dress_frac"])
        and bool(row["identity_invcut_frac"])
        and bool(row["identity_pref_face_seat"])
        and bool(row["within_codata_band"])
        and bool(row["identity_seven_N4_plus_SU2"])
        and bool(row["seven_meaning_fundamental_candidate"])
        and not bool(row["carrier_soft_unit_answer_candidate"])
        and bool(row["false_trail_global_M_book"])
        and not bool(row["local_cubocta_residue_candidate"])
        and bool(row["symmetry_soft_singlet_candidate"])
        and bool(row["identity_soft_symmetry_triple"])
        and bool(row["axiom_G_grade_completeness_soft"])
        and bool(row["derivation_closed"])
        and int(row["M"]) == 97
        and int(row["codata_year"]) == 2022
        and abs(float(row["vs_codata_ppm_pref"])) < 0.00016
        and abs(float(row["vs_codata_ppm_seat"])) < 0.001
    )
    return {
        "id": "Alpha_U0_soft_face",
        "M": row["M"],
        "alpha_pref": row["alpha_pref"],
        "vs_codata_ppm_pref": row["vs_codata_ppm_pref"],
        "vs_codata_ppm_seat": row["vs_codata_ppm_seat"],
        "codata_year": row["codata_year"],
        "within_codata_band": row["within_codata_band"],
        "ok": ok,
        "note": row["note"],
    }

def check_alpha_bridges(device: str = "cpu") -> dict:
    """§8.2 audit — α*↔α_fs partial links (missed-readings probe)."""
    from mt_ca.si_constants import N12_FCC_CAUSAL_LINKS, SI

    del device
    pi = math.pi
    a = SI.alpha_preferred
    a_struct = a
    phase_sat = SI.phase_saturation
    residue = SI.planck_hole_phase_residue

    higgs = SI.higgs_mass_row()
    runner = SI.alpha_runner_row()
    wein = SI.weinberg_row()
    coul = SI.coulomb_row()
    ew = SI.electroweak_mass_row()

    delta_lam = higgs["delta_lambda_quantum"]
    gate_residue_ok = (
        abs(residue - 1.0 / (4.0 * pi)) < 1e-15
        and abs(residue - SI.delta_phi_min / (2.0 * pi)) < 1e-15
    )
    delta_lambda_link_ok = (
        abs(delta_lam - a_struct / (4.0 * pi)) < 1e-15
        and abs(delta_lam - a_struct * residue) < 1e-15
    )
    pi_tower_absent = abs(SI.alpha_fs - SI.alpha_preferred) < 1e-18
    alpha_mz_runner_ok = runner["alpha_MZ_inv_rel_err"] < 2e-4
    fcc_cluster_n_phi_ok = (
        wein["N_cluster"] == 13.0
        and wein["N_phi"] == 13.0
        and wein["N12"] == float(N12_FCC_CAUSAL_LINKS)
        and wein["N_cluster"] == wein["N_phi"]
        and wein["sin2_theta_W_bare"] == 3.0 / 13.0
    )
    phase_ratio_over_pi = (4.0 * pi**2 + pi + 1.0) / pi
    cascade_guess = residue**3 * 4.0 * pi * (4.0 * pi**2 + pi + 1.0) / (4.0 * pi**2)
    cascade_rel_err = abs(cascade_guess - a) / a
    residue_cascade_to_alpha_fs_open = cascade_rel_err > 0.03
    coulomb_carrier_ok = coul["rel_F_over_FP_is_alpha"] < 1e-12
    electroweak_tree_ok = (
        abs(ew["mass_ratio_sin2"] - ew["sin2_theta_W"]) < 1e-12
        and ew["m_W_rel_err"] < 0.005
        and ew["m_Z_rel_err"] < 0.005
    )

    ok = (
        gate_residue_ok
        and delta_lambda_link_ok
        and pi_tower_absent
        and alpha_mz_runner_ok
        and fcc_cluster_n_phi_ok
        and residue_cascade_to_alpha_fs_open
        and coulomb_carrier_ok
        and electroweak_tree_ok
    )
    return {
        "id": "Alpha_bridges",
        "ok": ok,
        "gate_residue_ok": gate_residue_ok,
        "delta_lambda_phase_residue_ok": delta_lambda_link_ok,
        "pi_tower_absent": pi_tower_absent,
        "alpha_MZ_runner_ok": alpha_mz_runner_ok,
        "alpha_MZ_inv_rel_err": runner["alpha_MZ_inv_rel_err"],
        "fcc_cluster_N_phi_ok": fcc_cluster_n_phi_ok,
        "phase_ratio_over_pi": phase_ratio_over_pi,
        "phase_ratio_minus_N_phi": phase_ratio_over_pi - 13.0,
        "residue_cascade_to_alpha_fs_open": residue_cascade_to_alpha_fs_open,
        "cascade_rel_err": cascade_rel_err,
        "coulomb_carrier_ok": coulomb_carrier_ok,
        "electroweak_tree_ok": electroweak_tree_ok,
        "alpha_fs_inv_ppm_vs_CODATA": abs(SI.alpha_fs_inv - 137.035999177) / 137.035999177 * 1e6,
        "note": (
            "§8.2 audit: δλ=α_fs/(4π)=α_fs(α*−1), B_hV runner, N_φ=|N12|+1 PASS; "
            "α*→α_fs cascade + e₀ derivation + lattice Coulomb sim OPEN"
        ),
    }

