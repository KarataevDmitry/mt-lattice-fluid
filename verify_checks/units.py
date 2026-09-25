"""verify_checks.units — extracted from verify_principles"""
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


def check_na0_from_carrier(device: str = "cpu") -> dict:
    """HISTORICAL: N_a0=N_c·137 probe; model rejected as α-input."""
    from mt_ca.si_constants import SI

    del device
    row = SI.na0_from_carrier_row()
    ok = (
        bool(row["carrier_na0_ok"])
        and abs(float(row["N_a0_carrier_over_optical"]) - 1.0) < 5e-4
        and abs(float(row["alpha_star_stack_inv"]) - 137.088598) < 1e-3
        and bool(row["monomial_stack_open"])
        and bool(row.get("ask_rejected_as_alpha_input", False))
    )
    return {
        "id": "Na0_from_carrier",
        "N_a0_carrier": row["N_a0_carrier"],
        "N_a0_carrier_over_optical": row["N_a0_carrier_over_optical"],
        "alpha_star_stack_inv": row["alpha_star_stack_inv"],
        "vs_codata_ppm_stack": row["vs_codata_ppm_stack"],
        "monomial_stack_open": row["monomial_stack_open"],
        "ask_rejected_as_alpha_input": row.get("ask_rejected_as_alpha_input", False),
        "ok": ok,
        "note": row["note"],
    }

def check_na0_h_carrier(device: str = "cpu") -> dict:
    """§8.2·H — carrier inventory for N_a0; independent integer still OPEN."""
    from mt_ca.si_constants import SI

    del device
    row = SI.na0_h_carrier_inventory_row()
    ok = (
        bool(row["checks_ok"])
        and bool(row["N_a0_must_be_integer"])
        and bool(row["mass_hop_same_power"])
        and bool(row["reject_Nc_times_137"])
        and bool(row["reject_optical_a0_as_M_definition"])
        and bool(row["independent_Na0_open"])
        and float(row["rel_mass_vs_hop_alpha2"]) < 1e-4
    )
    return {
        "id": "Na0_H_carrier",
        "mass_hop_same_power": row["mass_hop_same_power"],
        "rel_mass_vs_hop_alpha2": row["rel_mass_vs_hop_alpha2"],
        "reject_Nc_times_137": row["reject_Nc_times_137"],
        "independent_Na0_open": row["independent_Na0_open"],
        "ok": ok,
        "note": row["note"],
    }

def check_meter_decouple_from_M(device: str = "cpu") -> dict:
    """§8.2·meter·decouple — SI metre ∉ M; lengths are hops."""
    from mt_ca.si_constants import SI

    del device
    row = SI.meter_decouple_from_M_row()
    ok = (
        bool(row["checks_ok"])
        and bool(row["derivation_closed"])
        and bool(row["meter_not_on_M"])
        and bool(row["SI_metre_is_T_export_only"])
        and bool(row["M_lengths_are_hops"])
        and bool(row["meter_not_input_to_alpha"])
        and bool(row["meter_not_input_to_masses"])
        and bool(row["meter_not_input_to_Na0"])
        and bool(row["l_P_not_defined_by_c"])
        and bool(row["hL_equals_l_P"])
    )
    return {
        "id": "Meter_decouple_from_M",
        "N_a0_predicted": row["N_a0_predicted"],
        "meter_not_on_M": row["meter_not_on_M"],
        "SI_metre_is_T_export_only": row["SI_metre_is_T_export_only"],
        "M_lengths_are_hops": row["M_lengths_are_hops"],
        "ok": ok,
        "note": row["note"],
    }

def check_length_dim_from_lP_alpha(device: str = "cpu") -> dict:
    """§8.2·[L]·l_P — length dimension = l_P; hierarchy from exact α."""
    from mt_ca.si_constants import SI

    del device
    row = SI.length_dim_from_lP_alpha_row()
    ok = (
        bool(row["checks_ok"])
        and bool(row["derivation_closed"])
        and bool(row["length_dim_is_l_P"])
        and bool(row["identity_L_eq_V_T"])
        and bool(row["identity_lP_eq_sqrt_hbarGc"])
        and bool(row["alpha_sets_length_hierarchy"])
        and bool(row["not_historical_SI_metre"])
        and bool(row["identity_a0_eq_Nc_over_alpha"])
        and bool(row["identity_re_eq_alpha_Nc"])
        and bool(row["identity_alpha_eq_Nc_over_Na0"])
    )
    return {
        "id": "Length_dim_from_lP_alpha",
        "alpha_preferred": row["alpha_preferred"],
        "N_c": row["N_c"],
        "N_a0": row["N_a0"],
        "N_re": row["N_re"],
        "length_dim_is_l_P": row["length_dim_is_l_P"],
        "ok": ok,
        "note": row["note"],
    }

def check_time_dim_from_tP(device: str = "cpu") -> dict:
    """§8.2·[T]·t_P — time dimension = t_P; M tick hT=κ·t_P."""
    from mt_ca.si_constants import SI

    del device
    row = SI.time_dim_from_tP_row()
    ok = (
        bool(row["checks_ok"])
        and bool(row["derivation_closed"])
        and bool(row["time_dim_is_t_P"])
        and bool(row["M_tick_is_hT"])
        and bool(row["identity_T_eq_L_over_V"])
        and bool(row["identity_tP_eq_sqrt_hbarGc5"])
        and bool(row["identity_hT_eq_kappa_tP"])
        and bool(row["not_historical_SI_second"])
        and bool(row["SI_second_is_T_export_only"])
    )
    return {
        "id": "Time_dim_from_tP",
        "t_P": row["t_P"],
        "hT": row["hT"],
        "kappa": row["kappa"],
        "time_dim_is_t_P": row["time_dim_is_t_P"],
        "M_tick_is_hT": row["M_tick_is_hT"],
        "ok": ok,
        "note": row["note"],
    }

def check_units_time_first_cascade(device: str = "cpu") -> dict:
    """§8.2·units·time-first — t_P → l_P → m_P ([M])."""
    from mt_ca.si_constants import SI

    del device
    row = SI.units_time_first_cascade_row()
    ok = (
        bool(row["checks_ok"])
        and bool(row["derivation_closed"])
        and bool(row["time_first"])
        and bool(row["si_base_triad_LMT"])
        and bool(row["mass_unit_exact"])
        and bool(row["derived_units_as_in_SI"])
        and bool(row["G_not_ontology_step"])
        and bool(row["identity_lP_eq_c_tP"])
        and bool(row["identity_mP_eq_hbar_over_c2_tP"])
        and bool(row["identity_mP_eq_hbar_over_c_lP"])
        and bool(row["identity_mP_time_eq_length_form"])
    )
    return {
        "id": "Units_time_first_cascade",
        "ontology_order": row["ontology_order"],
        "m_P": row["m_P"],
        "m_P_from_t_P": row["m_P_from_t_P"],
        "time_first": row["time_first"],
        "mass_unit_exact": row["mass_unit_exact"],
        "ok": ok,
        "note": row["note"],
    }

def check_planck_temperature_independent(device: str = "cpu") -> dict:
    """§8.2·units·T_P — T_P:=E_P without k_B."""
    from mt_ca.si_constants import SI

    del device
    row = SI.planck_temperature_independent_row()
    ok = (
        bool(row["checks_ok"])
        and bool(row["derivation_closed"])
        and bool(row["k_B_not_in_definition"])
        and bool(row["no_separate_Theta_on_M"])
        and bool(row["identity_TP_eq_EP"])
        and bool(row["identity_TPM_eq_E0"])
        and bool(row["identity_TPM_eq_kappa_EP"])
        and bool(row["identity_EP_eq_sqrt2_E0"])
    )
    return {
        "id": "Planck_temperature_independent",
        "T_P": row["T_P"],
        "T_P_M": row["T_P_M"],
        "k_B_not_in_definition": row["k_B_not_in_definition"],
        "ok": ok,
        "note": row["note"],
    }

