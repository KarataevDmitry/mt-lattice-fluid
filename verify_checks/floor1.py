"""verify_checks.floor1 — extracted from verify_principles"""
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


def check_floor1_leptonic(device: str = "cpu") -> dict:
    """§6·floor1 — pre-resonance band; content census open."""
    from mt_ca.si_constants import SI

    del device
    row = SI.floor1_leptonic_row()
    ok = (
        bool(row["checks_ok"])
        and bool(row["window_ok"])
        and bool(row["ir_landmarks_far_above"])
        and not bool(row["derivation_closed"])
        and int(row["N12"]) == 12
        and abs(float(row["L_lo_dl"]) - 1728.0) < 1e-9
        and abs(float(row["L_mid_dl"]) - 20736.0) < 1e-9
    )
    return {
        "id": "Floor1_leptonic",
        "L_lo_dl": row["L_lo_dl"],
        "L_mid_dl": row["L_mid_dl"],
        "derivation_closed": row["derivation_closed"],
        "ok": ok,
        "note": row["note"],
    }

def check_floor1_B0_census(device: str = "cpu") -> dict:
    """§6·floor1·B0·census — class census of stable B=0 at N12^3…^4."""
    from mt_ca.si_constants import SI

    del device
    row = SI.floor1_B0_census_row()
    ok = (
        bool(row["checks_ok"])
        and bool(row["census_ok"])
        and bool(row["derivation_closed"])
        and not bool(row["sim_metastable_maps_open"])
        and bool(row["soft_Gamma_open"])
        and row["stable_matter_ids"] == ["C2_lightest_Q_pm1_dressed"]
        and row["pre_resonance_ids"] == ["C4_Q0_multicell_blob"]
        and row["classes"][3]["status"] == "unstable_channel_closed"
        and row["classes"][6]["status"] == "stable_off_band"
    )
    return {
        "id": "Floor1_B0_census",
        "R_lo_dl": row["R_lo_dl"],
        "R_hi_dl": row["R_hi_dl"],
        "stable_matter_ids": row["stable_matter_ids"],
        "derivation_closed": row["derivation_closed"],
        "ok": ok,
        "note": row["note"],
    }

def check_floor1_dressing(device: str = "cpu") -> dict:
    """§6·floor1·dressing — near-zone ρ_Θ of lightest Q=±1; outer R open."""
    from mt_ca.si_constants import SI

    del device
    row = SI.floor1_dressing_row()
    ok = (
        bool(row["checks_ok"])
        and bool(row["min_support_closed"])
        and not bool(row["derivation_closed"])
        and int(row["N12"]) == 12
        and abs(float(row["R_min_dl"]) - 1.0) < 1e-12
        and abs(float(row["Delta_phi_min"]) - 0.5) < 1e-12
        and "closed_rho_Theta_is_dressing" in row["closed_ids"]
        and "open_R_dress_outer" in row["open_ids"]
        and "reject_R_equals_floor1_band" in row["reject_ids"]
    )
    return {
        "id": "Floor1_dressing",
        "R_min_dl": row["R_min_dl"],
        "R_floor1_lo_dl": row["R_floor1_lo_dl"],
        "derivation_closed": row["derivation_closed"],
        "min_support_closed": row["min_support_closed"],
        "ok": ok,
        "note": row["note"],
    }

def check_floor1_dressing_close(device: str = "cpu") -> dict:
    """§6·floor1·dressing·close — R_dress=1·dl via N12<N_phi + local star."""
    from mt_ca.si_constants import SI

    del device
    row = SI.floor1_dressing_close_row()
    ok = (
        bool(row["checks_ok"])
        and bool(row["derivation_closed"])
        and bool(row["star_above_floor"])
        and bool(row["N12_lt_Nphi"])
        and int(row["N12"]) == 12
        and int(row["N_phi"]) == 13
        and abs(float(row["R_dress_dl"]) - 1.0) < 1e-12
        and float(row["Delta_phi_ring"]) > float(row["Delta_phi_min"])
    )
    return {
        "id": "Floor1_dressing_close",
        "R_dress_dl": row["R_dress_dl"],
        "Delta_phi_ring": row["Delta_phi_ring"],
        "derivation_closed": row["derivation_closed"],
        "ok": ok,
        "note": row["note"],
    }

def check_floor1_dressing_f_close(device: str = "cpu") -> dict:
    """§6·floor1·dressing·f·close — ρ_Θ = 𝟙[|Δφ|≥Δφ_min]."""
    from mt_ca.si_constants import SI

    del device
    row = SI.floor1_dressing_f_close_row()
    ok = (
        bool(row["checks_ok"])
        and bool(row["derivation_closed"])
        and row["f_form"] == "Heaviside(|Δφ_N|-Δφ_min)"
        and abs(float(row["Delta_phi_min"]) - 0.5) < 1e-12
        and "closed_f_heaviside_dphi" in row["closed_ids"]
        and "reject_smooth_continuum_f" in row["reject_ids"]
    )
    return {
        "id": "Floor1_dressing_f_close",
        "f_form": row["f_form"],
        "derivation_closed": row["derivation_closed"],
        "ok": ok,
        "note": row["note"],
    }

def check_floor1_leftovers_close(device: str = "cpu") -> dict:
    """§6·floor1·leftovers·close — C3 channel existence + ν off-band."""
    from mt_ca.si_constants import SI

    del device
    row = SI.floor1_leftovers_close_row()
    ok = (
        bool(row["checks_ok"])
        and bool(row["derivation_closed"])
        and bool(row["C3_channel_existence_closed"])
        and bool(row["C3_Gamma_soft_open"])
        and bool(row["nu_floor1_size_rejected"])
        and "closed_C3_channel_existence" in row["closed_ids"]
        and "closed_by_C3_gamma_continuum" in row["closed_ids"]
        and "soft_open_C3_n_ticks_filled_bath" in row["soft_open_ids"]
    )
    return {
        "id": "Floor1_leftovers_close",
        "C3_channel_existence_closed": row["C3_channel_existence_closed"],
        "nu_floor1_size_rejected": row["nu_floor1_size_rejected"],
        "derivation_closed": row["derivation_closed"],
        "ok": ok,
        "note": row["note"],
    }

def check_floor1_C3_gamma_close(device: str = "cpu") -> dict:
    """§6·floor1·C3·gamma·close — continuum Γ≠M; n_ticks in bath soft."""
    from mt_ca.si_constants import SI

    del device
    row = SI.floor1_C3_gamma_close_row()
    ok = (
        bool(row["checks_ok"])
        and not bool(row["derivation_closed"])
        and bool(row["continuum_rejected"])
        and "closed_M_clock_form_n_ticks" in row["closed_ids"]
        and "soft_open_C3_n_ticks_filled_bath" in row["soft_open_ids"]
        and "reject_continuum_Gamma_as_M_law" in row["reject_ids"]
    )
    return {
        "id": "Floor1_C3_gamma_close",
        "n_ticks_alone_hyp": row["n_ticks_alone_hyp"],
        "continuum_rejected": row["continuum_rejected"],
        "derivation_closed": row["derivation_closed"],
        "ok": ok,
        "note": row["note"],
    }

def check_floor1_C3_bath_dogfood(device: str = "cpu") -> dict:
    """§6·floor1·C3·bath·dogfood — VACUUM_BOIL moves; densitometer sees b=1."""
    from mt_ca.si_constants import SI

    del device
    row = SI.floor1_C3_bath_dogfood_row()
    ok = (
        bool(row["checks_ok"])
        and bool(row["vacuum_frozen"])
        and bool(row["boil_emerged_b"])
        and float(row["boil_contrast_final"]) > 10.0
        and "closed_vacuum_boil_whole_lattice_moves" in row["closed_ids"]
        and "closed_thermometer_dual_channel_b1" in row["closed_ids"]
        and "soft_open_b_matter_not_yet" not in row["soft_open_ids"]
    )
    return {
        "id": "Floor1_C3_bath_dogfood",
        "boil_contrast_final": row["boil_contrast_final"],
        "boil_emerged_b": row["boil_emerged_b"],
        "derivation_closed": row["derivation_closed"],
        "ok": ok,
        "note": row["note"],
    }

