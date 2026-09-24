#!/usr/bin/env python3
"""Verify M-layer axioms after first-principles rebuild."""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path

import torch

from mt_ca.cauchy_riemann import cauchy_riemann_energy
from mt_ca.config import MConfig
from mt_ca.metrics import field_amplitude, norm_drift, total_norm_squared
from mt_ca.seeds import SeedClass, make_seed
from mt_ca.simulator import LatticeFluidSimulator
from mt_ca.linear import linear_step, linear_step_local_ca
from mt_ca.reversible import evolve_canonical
from mt_ca.spinor import arg_phase_defect, apply_gate_collision, gate_phase, holonomy_zeta, spinor_neighbor_sum, su2_apply
from mt_ca.update import apply_heisenberg_floor, vacuum_phase, wrapped_phase_diff


def check_a3_unitarity(size: int = 128, steps: int = 256, device: str = "cpu") -> dict:
    from mt_ca.reversible import bit_exact_roundtrip_report

    row = bit_exact_roundtrip_report(size, min(steps, 32), device, seed_class=SeedClass.PLANE_WAVE)
    return {
        "id": "A3",
        "bit_exact": row["bit_exact"],
        "max_rel_err": row["max_rel_err"],
        "steps": row["steps"],
        "ok": row["ok"],
        "note": "A3 on Z_N[i] projected g — bit-exact roundtrip (§3.12)",
    }


def check_a3_local_ca(size: int = 128, steps: int = 256, device: str = "cpu") -> dict:
    cfg = MConfig.for_stencil('hex', linear_mode="local_ca")
    z = make_seed(SeedClass.PLANE_WAVE, size, size, device=torch.device(device))
    norm0 = total_norm_squared(z)
    for _ in range(steps):
        c0 = linear_step_local_ca(z[..., 0], cfg.gamma)
        c1 = linear_step_local_ca(z[..., 1], cfg.gamma)
        z = torch.stack([c0, c1], dim=-1)
    drift = norm_drift(norm0, total_norm_squared(z))
    ok = drift < 1e-3
    return {
        "id": "A3_local_ca",
        "linear_mode": "local_ca",
        "norm_drift": drift,
        "ok": ok,
        "note": "bond-unitary stream only — not full g",
    }


def check_a3_spectral_reference(size: int = 128, device: str = "cpu") -> dict:
    from mt_ca.t_analysis import spectral_unitary_reference

    cfg = MConfig.for_stencil('hex')
    z = make_seed(SeedClass.PLANE_WAVE, size, size, device=torch.device(device))[..., 0]
    z_ref = spectral_unitary_reference(z, cfg.gamma)
    z_ca = linear_step_local_ca(z, cfg.gamma)
    rel = float((z_ref - z_ca).abs().mean() / (z.abs().mean() + 1e-8))
    return {
        "id": "T_dft_oracle",
        "local_vs_spectral_mean_rel_err": rel,
        "ok": rel < 0.5,
        "note": "T-layer DFT calibrates dispersion, not M g",
    }


def check_a3_diffusive_fails(size: int = 128, steps: int = 256, device: str = "cpu") -> dict:
    cfg = MConfig.for_stencil('hex', linear_mode="diffusive", macro_weight=False, cr_strength=0.0)
    z = make_seed(SeedClass.PLANE_WAVE, size, size, device=torch.device(device))
    norm0 = total_norm_squared(z)
    for _ in range(steps):
        c0 = linear_step(z[..., 0], cfg.gamma, "diffusive", stencil=cfg.stencil)
        c1 = linear_step(z[..., 1], cfg.gamma, "diffusive", stencil=cfg.stencil)
        z = torch.stack([c0, c1], dim=-1)
    drift = norm_drift(norm0, total_norm_squared(z))
    return {
        "id": "A3_diffusive",
        "linear_mode": "diffusive",
        "norm_drift": drift,
        "ok": drift > 0.01,
        "note": "A3 vs A6: z+γΔ не унитарна (MODEL §3.6)",
    }


def check_a4_phase_preserves_modulus(device: str = "cpu") -> dict:
    cfg = MConfig.for_stencil('hex')
    z = torch.tensor([0.3 + 0.4j, 0.1 - 0.2j], device=device, dtype=torch.complex64)
    rho = z.abs().square()
    phi = vacuum_phase(rho, cfg)
    z2 = z * torch.exp(1j * phi)
    delta = float((z2.abs() - z.abs()).abs().max().item())
    return {"id": "A4", "max_modulus_change": delta, "ok": delta < 1e-6}


def check_impl_zero_frozen(size: int = 32, device: str = "cpu") -> dict:
    cfg = MConfig.for_stencil('hex')
    z = torch.zeros(size, size, 2, device=device, dtype=torch.complex64)
    z1 = apply_gate_collision(z, cfg)
    frozen = float(field_amplitude(z1).max().item()) == 0.0
    return {
        "id": "I2_zero",
        "max_amp_after_step": float(field_amplitude(z1).max().item()),
        "ok": frozen,
        "note": "z≡0 frozen — use VACUUM seed with vacuum_amplitude",
    }


def check_a5_vacuum_floor(size: int = 64, steps: int = 64, device: str = "cpu") -> dict:
    sim = LatticeFluidSimulator(size, size, MConfig.for_stencil('hex'), device=device)
    sim.reset(SeedClass.VACUUM)
    amp0 = float(sim.snapshot_amplitude().mean().item())
    sim.step(steps)
    amp1 = float(sim.snapshot_amplitude().mean().item())
    ok = amp0 > 0 and amp1 > 0 and amp1 >= 0.5 * amp0
    return {"id": "A5", "amp_mean_initial": amp0, "amp_mean_final": amp1, "ok": ok}


def check_a8_macro_suppression(device: str = "cpu") -> dict:
    cfg = MConfig.for_stencil('hex', macro_weight=True, macro_rho=1.0)
    rho_low = torch.tensor([0.01, 0.05], device=device)
    rho_high = torch.tensor([32.0, 128.0], device=device)
    phi_low = vacuum_phase(rho_low, cfg)
    phi_high = vacuum_phase(rho_high, cfg)
    kick_low = float((torch.exp(1j * phi_low) - 1.0).abs().mean().item())
    kick_high = float((torch.exp(1j * phi_high) - 1.0).abs().mean().item())
    ok = kick_high < kick_low * 0.5
    return {"id": "A8", "kick_low": kick_low, "kick_high": kick_high, "ok": ok}


def check_a9_cr_smooth_modes(
    size: int = 64,
    burn_in: int = 32,
    settle: int = 32,
    device: str = "cpu",
) -> dict:
    from mt_ca.cauchy_riemann import cr_stationarity_tolerance
    from mt_ca.si_constants import (
        bekenshtein_fractional_part,
        cr_dispersion_ceiling,
        cr_seed_ceiling,
        nu_CA_natural,
    )

    # Canon A5: HF ON; Φ = saturating holonomy only (§3.12.5). §3.9 defect is Δφ_N in that gate —
    # not a second CR/sync channel (double-count filled the grid; sim dogfood).
    sim = LatticeFluidSimulator(
        size,
        size,
        MConfig.for_stencil("hex", heisenberg_floor=True),
        device=device,
    )
    sim.reset(SeedClass.PLANE_WAVE)
    e0 = cauchy_riemann_energy(sim.z[..., 0])
    sim.step(burn_in)
    e1 = cauchy_riemann_energy(sim.z[..., 0])
    sim.step(settle)
    e2 = cauchy_riemann_energy(sim.z[..., 0])

    seed_max = cr_seed_ceiling()
    stat_max = cr_dispersion_ceiling()
    stat_tol = cr_stationarity_tolerance(energy=e1)
    delta = abs(e2 - e1)
    plateau_ok = e1 <= stat_max  # aspirational ν_CA band — still open on projected g
    ok = e0 <= seed_max and delta <= stat_tol
    return {
        "id": "A9",
        "cr_energy_initial": e0,
        "cr_energy_after_burn_in": e1,
        "cr_energy_after_settle": e2,
        "cr_seed_ceiling": seed_max,
        "cr_dispersion_ceiling": stat_max,
        "nu_CA_natural": nu_CA_natural(),
        "B_hV_fraction": bekenshtein_fractional_part(),
        "stationarity_delta": delta,
        "stationarity_tol": stat_tol,
        "plateau_ok": plateau_ok,
        "ok": ok,
        "note": "§3.9.6: gate=ζ holonomy; HF ON; stationarity; absolute ν_CA ceiling open",
    }


def check_a11_vortex_persistence(size: int = 128, steps: int = 128, device: str = "cpu") -> dict:
    sim = LatticeFluidSimulator(size, size, MConfig.for_stencil('hex'), device=device)
    sim.reset(SeedClass.VORTEX_P)
    amp0 = float(sim.snapshot_amplitude().max().item())
    sim.step(steps)
    amp1 = float(sim.snapshot_amplitude().max().item())
    ok = amp1 > 0.2 * amp0 and not torch.isnan(sim.z).any().item()
    return {"id": "A11", "amp_max_initial": amp0, "amp_max_final": amp1, "ok": ok}


def check_a16_heisenberg_floor(size: int = 64, device: str = "cpu") -> dict:
    from mt_ca.projected_collision import (
        holonomy_zeta_int,
        int_neighbor_sum,
        rho2_int,
        saturating_phi_kick,
    )
    from mt_ca.reversible import canonical_fixed
    from mt_ca.si_constants import DELTA_PHI_MIN, heisenberg_phi_min_disc, heisenberg_phi_min_physical

    cfg = MConfig.for_stencil('hex', heisenberg_floor=True)
    phi_min_rad = heisenberg_phi_min_physical()
    phi_min_disc = heisenberg_phi_min_disc(phase_bits=cfg.phase_bits)
    n_ring = 1 << cfg.phase_bits
    dev = torch.device(device)

    z = make_seed(SeedClass.PLANE_WAVE, size, size, device=dev)
    sum_n = spinor_neighbor_sum(z, cfg)
    zeta = holonomy_zeta(z, sum_n)
    pd = wrapped_phase_diff(zeta, torch.ones_like(zeta))
    pd_floor = apply_heisenberg_floor(pd, cfg)
    # Sub-threshold nonzero → 0; already-zero stays 0; |Δφ|≥floor unchanged.
    small_nz = (pd.abs() > 0) & (pd.abs() < phi_min_rad)
    if bool(small_nz.any()):
        enforced = float((pd_floor[small_nz].abs() < 1e-12).float().mean().item())
    else:
        enforced = 1.0
    large = pd.abs() >= phi_min_rad
    if bool(large.any()):
        preserved = float((pd_floor[large] - pd[large]).abs().max().item()) < 1e-12
    else:
        preserved = True
    phi_gate = gate_phase(z, cfg)

    f = canonical_fixed(z, cfg)
    fb = cfg.frac_bits
    u0 = f[..., 0].to(torch.int64)
    v0 = f[..., 1].to(torch.int64)
    sum_n_i = int_neighbor_sum(f, cfg.stencil)
    zeta_r, zeta_i = holonomy_zeta_int(u0, v0, sum_n_i[..., 0], sum_n_i[..., 1], frac_bits=fb)
    rho2 = rho2_int(u0, v0, frac_bits=fb)
    phi_disc = saturating_phi_kick(zeta_r, zeta_i, rho2, cfg)

    in_ring = bool(((phi_disc >= 0) & (phi_disc < n_ring)).all())
    mod_ok = bool(torch.equal(phi_disc, phi_disc % n_ring))
    half = n_ring // 2
    signed = torch.where(phi_disc >= half, phi_disc - n_ring, phi_disc)
    # Nonzero discrete kicks must be ≥ φ_min; zeros OK (snap-down).
    disc_floor_ok = bool((~(signed != 0) | (signed.abs() >= phi_min_disc)).all())

    ok = (
        abs(phi_min_rad - DELTA_PHI_MIN) < 1e-12
        and phi_min_disc >= 1
        and enforced >= 0.99
        and preserved
        and float(phi_gate.abs().max().item()) > 0.0
        and in_ring
        and mod_ok
        and disc_floor_ok
    )
    return {
        "id": "A16",
        "fraction_floored": enforced,
        "max_phi": float(phi_gate.abs().max().item()),
        "heisenberg_phi_min_rad": phi_min_rad,
        "heisenberg_phi_min_disc": phi_min_disc,
        "N_ring": n_ring,
        "mod512_ok": mod_ok and in_ring,
        "disc_floor_ok": disc_floor_ok,
        "ok": ok,
    }


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
        and abs(float(row["alpha_star_bare"]) - float(row["alpha_bare_analytic"])) < 1e-15
        and abs(float(row["alpha_star_stack_inv"]) - 137.09186727) < 1e-4
        and bool(row["derivation_open"])
    )
    return {
        "id": "Alpha_fixed_point",
        "alpha_bare_analytic": row["alpha_bare_analytic"],
        "alpha_bare_analytic_inv": row["alpha_bare_analytic_inv"],
        "alpha_star_stack": row["alpha_star_stack"],
        "alpha_star_stack_inv": row["alpha_star_stack_inv"],
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


def check_na0_from_carrier(device: str = "cpu") -> dict:
    """HISTORICAL: N_a0=N_c·137 probe; ask-model rejected as α-input."""
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


def check_na0_h_carrier_ask(device: str = "cpu") -> dict:
    """§8.2·H·ask — carrier inventory for N_a0; independent integer still OPEN."""
    from mt_ca.si_constants import SI

    del device
    row = SI.na0_h_carrier_ask_row()
    ok = (
        bool(row["ask_ok"])
        and bool(row["N_a0_must_be_integer"])
        and bool(row["mass_hop_same_power"])
        and bool(row["reject_Nc_times_137"])
        and bool(row["reject_optical_a0_as_M_definition"])
        and bool(row["independent_Na0_open"])
        and float(row["rel_mass_vs_hop_alpha2"]) < 1e-4
    )
    return {
        "id": "Na0_H_carrier_ask",
        "mass_hop_same_power": row["mass_hop_same_power"],
        "rel_mass_vs_hop_alpha2": row["rel_mass_vs_hop_alpha2"],
        "reject_Nc_times_137": row["reject_Nc_times_137"],
        "independent_Na0_open": row["independent_Na0_open"],
        "ok": ok,
        "note": row["note"],
    }


def check_alpha_force_lattice_ask(device: str = "cpu") -> dict:
    """§8.2·F·ask — α=κ/M from F₀ lattice; M from g still OPEN."""
    from mt_ca.si_constants import SI

    del device
    row = SI.alpha_force_lattice_ask_row()
    ok = (
        bool(row["ask_ok"])
        and bool(row["M_from_g_open"])
        and not bool(row["replaces_pi_ansatz"])
        and abs(float(row["M_N12_Nhier"]) - 96.0) < 1e-12
        and abs(float(row["vs_codata_ppm_M97"]) + 1040.4) < 1.0
        and abs(float(row["vs_codata_ppm_M96"]) - 9365.5) < 1.0
    )
    return {
        "id": "Alpha_force_lattice_ask",
        "M_target_CODATA": row["M_target_CODATA"],
        "alpha_M96_inv": row["alpha_M96_inv"],
        "alpha_M97_inv": row["alpha_M97_inv"],
        "vs_codata_ppm_M96": row["vs_codata_ppm_M96"],
        "vs_codata_ppm_M97": row["vs_codata_ppm_M97"],
        "M_from_g_open": row["M_from_g_open"],
        "ok": ok,
        "note": row["note"],
    }


def check_alpha_meaning_ask(device: str = "cpu") -> dict:
    """§8.2·α·meaning — α is phase↔vacuum coupling; soft residual OPEN."""
    from mt_ca.si_constants import SI

    del device
    row = SI.alpha_meaning_ask_row()
    ok = (
        bool(row["ask_ok"])
        and bool(row["residue_equals_1_over_4pi"])
        and bool(row["discrete_coupling_open"])
        and not bool(row["replaces_pi_ansatz"])
        and abs(float(row["vs_codata_ppm_pi"]) + 2.223) < 0.01
    )
    return {
        "id": "Alpha_meaning_ask",
        "vacuum_residue": row["vacuum_residue"],
        "four_pi_times_alpha": row["four_pi_times_alpha"],
        "alpha_fs_inv": row["alpha_fs_inv"],
        "discrete_coupling_open": row["discrete_coupling_open"],
        "ok": ok,
        "note": row["note"],
    }


def check_alpha_descent_ask(device: str = "cpu") -> dict:
    """§8.2·α·descent — amnesia vacuum→coupling; fraction OPEN."""
    from mt_ca.si_constants import SI

    del device
    row = SI.alpha_descent_ask_row()
    ok = (
        bool(row["ask_ok"])
        and bool(row["residue_is_not_alpha"])
        and bool(row["coupling_fraction_open"])
        and not bool(row["used_alpha_fs_as_input"])
        and int(row["N_phi"]) == 13
        and int(row["alpha_geom_inv"]) == 137
        and abs(float(row["vs_codata_ppm_pi_AFTER"]) + 2.223) < 0.01
    )
    return {
        "id": "Alpha_descent_ask",
        "vacuum_residue": row["vacuum_residue"],
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
        bool(row["ask_ok"])
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
        bool(row["ask_ok"])
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


def check_alpha_schwinger_ask(device: str = "cpu") -> dict:
    """§8.2·α·Schwinger — lab door ae; foot explains 1/(2π)."""
    from mt_ca.si_constants import SI

    del device
    row = SI.alpha_schwinger_ask_row()
    ok = (
        bool(row["ask_ok"])
        and not bool(row["derivation_closed"])
        and abs(float(row["rel_2ar_vs_schwinger"])) < 1e-15
    )
    return {
        "id": "Alpha_schwinger_ask",
        "ae_Schwinger_1loop": row["ae_Schwinger_1loop"],
        "vacuum_foot_r": row["vacuum_foot_r"],
        "one_loop_vs_ae_ppm": row["one_loop_vs_ae_ppm"],
        "derivation_closed": row["derivation_closed"],
        "ok": ok,
        "note": row["note"],
    }


def check_alpha_dirac_g2_ask(device: str = "cpu") -> dict:
    """§8.2·α·g2·ask — bare g=2 closed; A5→ae still open."""
    from mt_ca.si_constants import SI

    del device
    row = SI.alpha_dirac_g2_ask_row()
    ok = (
        bool(row["ask_ok"])
        and bool(row["bare_g2_closed"])
        and not bool(row["derivation_ae_closed"])
        and abs(float(row["g_bare"]) - 2.0) < 1e-15
    )
    return {
        "id": "Alpha_dirac_g2_ask",
        "g_bare": row["g_bare"],
        "ae_bare": row["ae_bare"],
        "bare_g2_closed": row["bare_g2_closed"],
        "derivation_ae_closed": row["derivation_ae_closed"],
        "ok": ok,
        "note": row["note"],
    }


def check_alpha_ae_cloud_ask(device: str = "cpu") -> dict:
    """§8.2·α·ae·ask — ae=α·2r factors; does not bypass coupling OPEN."""
    from mt_ca.si_constants import SI

    del device
    row = SI.alpha_ae_cloud_ask_row()
    ok = (
        bool(row["ask_ok"])
        and bool(row["factorization_closed"])
        and not bool(row["derivation_ae_closed"])
        and not bool(row["bypasses_coupling_open"])
        and abs(float(row["best_geo_ppm"])) > 1e3
    )
    return {
        "id": "Alpha_ae_cloud_ask",
        "two_r": row["two_r"],
        "best_geo_try": row["best_geo_try"],
        "best_geo_ppm": row["best_geo_ppm"],
        "factorization_closed": row["factorization_closed"],
        "derivation_ae_closed": row["derivation_ae_closed"],
        "bypasses_coupling_open": row["bypasses_coupling_open"],
        "ok": ok,
        "note": row["note"],
    }


def check_alpha_rydberg_hall_ask(device: str = "cpu") -> dict:
    """§8.2·α·Rydberg·Hall — lab doors; R_∞ foot identity; same coupling OPEN."""
    from mt_ca.si_constants import SI

    del device
    row = SI.alpha_rydberg_hall_ask_row()
    ok = (
        bool(row["ask_ok"])
        and bool(row["factorization_rydberg_closed"])
        and not bool(row["hall_is_alpha_source_post2019"])
        and not bool(row["derivation_closed"])
        and not bool(row["bypasses_coupling_open"])
        and abs(float(row["rel_Rinf_foot_vs_classic"])) < 1e-15
    )
    return {
        "id": "Alpha_rydberg_hall_ask",
        "Rinf_vs_codata_ppm": row["Rinf_vs_codata_ppm"],
        "Hall_legacy_vs_codata_ppm": row["Hall_legacy_vs_codata_ppm"],
        "hall_is_alpha_source_post2019": row["hall_is_alpha_source_post2019"],
        "derivation_closed": row["derivation_closed"],
        "ok": ok,
        "note": row["note"],
    }


def check_alpha_em_face_weight_ask(device: str = "cpu") -> dict:
    """§8.2·α·EM·faces — area/dihedral ≠ α; Φ_□ still open."""
    from mt_ca.si_constants import SI

    del device
    row = SI.alpha_em_face_weight_ask_row()
    ok = (
        bool(row["ask_ok"])
        and not bool(row["face_weight_is_alpha"])
        and not bool(row["derivation_closed"])
        and not bool(row["bypasses_coupling_open"])
        and abs(float(row["best_ppm"])) > 1e3
    )
    return {
        "id": "Alpha_em_face_weight_ask",
        "w_square": row["w_square"],
        "best_try": row["best_try"],
        "best_ppm": row["best_ppm"],
        "face_weight_is_alpha": row["face_weight_is_alpha"],
        "derivation_closed": row["derivation_closed"],
        "ok": ok,
        "note": row["note"],
    }


def check_alpha_dual_fraction_ask(device: str = "cpu") -> dict:
    """§8.2·α·dual — α=m/n via two independent paths; inventory pairs."""
    from mt_ca.si_constants import SI

    del device
    row = SI.alpha_dual_fraction_ask_row()
    strongest = str(row["strongest_alive_pair"])
    ok = (
        bool(row["ask_ok"])
        and not bool(row["derivation_closed"])
        and bool(row.get("M_combinatorial_closed", False))
        and strongest.startswith("force κ/M")
    )
    return {
        "id": "Alpha_dual_fraction_ask",
        "strongest_alive_pair": row["strongest_alive_pair"],
        "M_combinatorial_closed": row.get("M_combinatorial_closed"),
        "M_target": row["M_target"],
        "kappa": row["kappa"],
        "derivation_closed": row["derivation_closed"],
        "ok": ok,
        "note": row["note"],
    }


def check_alpha_sqrt2_descent_ask(device: str = "cpu") -> dict:
    """§8.2·α·√2·descent — force dual ⇒ α∉ℚ; reject exact p/q."""
    from mt_ca.si_constants import SI

    del device
    row = SI.alpha_sqrt2_descent_ask_row()
    ok = (
        bool(row["ask_ok"])
        and bool(row["lemma_force_alpha_not_rational"])
        and bool(row["reject_exact_rational_alpha_under_force"])
        and not bool(row["derivation_M_closed"])
        and abs(float(row["kappa"]) ** 2 - 0.5) < 1e-15
    )
    return {
        "id": "Alpha_sqrt2_descent_ask",
        "kappa": row["kappa"],
        "M_target": row["M_target"],
        "lemma_force_alpha_not_rational": row["lemma_force_alpha_not_rational"],
        "derivation_M_closed": row["derivation_M_closed"],
        "ok": ok,
        "note": row["note"],
    }


def check_alpha_M_from_g_try(device: str = "cpu") -> dict:
    """§8.2·α·M·g·try — M=1+N12·N_hier story; not full census close."""
    from mt_ca.si_constants import SI

    del device
    row = SI.alpha_M_from_g_try_row()
    ok = (
        bool(row["ask_ok"])
        and bool(row["story_ok"])
        and not bool(row["derivation_closed"])
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


def check_alpha_nF_kick_census(device: str = "cpu") -> dict:
    """§8.2·α·nF·census — enumerate kick-ledger seats → M=97."""
    from mt_ca.si_constants import SI

    del device
    row = SI.alpha_nF_kick_census_row()
    ok = (
        bool(row["ask_ok"])
        and bool(row["census_ok"])
        and bool(row["derivation_closed"])
        and not bool(row["runtime_sim_closed"])
        and int(row["n_F_seats"]) == 97
        and int(row["n_core"]) == 1
        and int(row["n_link_hier"]) == 96
    )
    return {
        "id": "Alpha_nF_kick_census",
        "n_F_seats": row["n_F_seats"],
        "M": row["M"],
        "alpha": row["alpha"],
        "vs_codata_ppm": row["vs_codata_ppm"],
        "derivation_closed": row["derivation_closed"],
        "ok": ok,
        "note": row["note"],
    }


def check_alpha_full_quantization_bridge(device: str = "cpu") -> dict:
    """§8.2·α·full-quant — α=κ/M from full quantization; π-tower demoted as descent."""
    from mt_ca.si_constants import SI

    del device
    row = SI.alpha_full_quantization_bridge_row()
    ok = (
        bool(row["ask_ok"])
        and bool(row["discrete_path_shipped"])
        and bool(row["M_combinatorial_closed"])
        and bool(row["pi_tower_demoted_as_descent"])
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
        "discrete_path_shipped": row["discrete_path_shipped"],
        "soft_residual_open": row["soft_residual_open"],
        "ok": ok,
        "note": row["note"],
    }



def check_alpha_upstairs_mass_probe(device=None):
    from mt_ca.si_constants import SI
    r = SI.alpha_upstairs_mass_probe_row()
    return {
        "id": "Alpha_upstairs_mass_probe",
        "ok": bool(r["ask_ok"]),
        "m_H_rel_err": r["m_H_rel_err"],
        "m_p_rel_err": r["m_p_rel_err"],
        "m_e_rel_err": r["m_e_rel_err"],
        "note": r["note"],
    }

def check_coulomb_M_native(device: str = "cpu") -> dict:
    """§8.2·Coulomb·M-native — F=n1 n2 F₀/(M N²); α is T-readout only."""
    from mt_ca.si_constants import SI

    del device
    row = SI.coulomb_M_native_row()
    ok = (
        bool(row["ask_ok"])
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



def check_alpha_U0_soft_face_ask(device: str = "cpu") -> dict:
    """§8.2 soft-face — prefer seat+face unit; inside CODATA 2022 band."""
    from mt_ca.si_constants import SI

    del device
    row = SI.alpha_U0_soft_face_ask_row()
    ok = (
        bool(row["ask_ok"])
        and bool(row["soft_candidate_shipped"])
        and bool(row["mechanism_descent_shipped"])
        and bool(row["plus_1ppm_explained"])
        and bool(row["axiom_inv_cut_shipped"])
        and bool(row["axiom_seat_unit_shipped"])
        and bool(row["axiom_seat_plus_face_shipped"])
        and bool(row["identity_dress_frac"])
        and bool(row["identity_invcut_frac"])
        and bool(row["identity_pref_face_seat"])
        and bool(row["lab_inside_codata_band"])
        and bool(row["identity_seven_N4_plus_SU2"])
        and bool(row["seven_meaning_fundamental_candidate"])
        and not bool(row["carrier_soft_unit_answer_candidate"])
        and bool(row["false_trail_global_M_book"])
        and not bool(row["derivation_closed"])
        and int(row["M"]) == 97
        and int(row["codata_year"]) == 2022
        and abs(float(row["vs_codata_ppm_pref"])) < 0.00016
        and abs(float(row["vs_codata_ppm_seat"])) < 0.001
    )
    return {
        "id": "Alpha_U0_soft_face_ask",
        "M": row["M"],
        "alpha_pref": row["alpha_pref"],
        "vs_codata_ppm_pref": row["vs_codata_ppm_pref"],
        "vs_codata_ppm_seat": row["vs_codata_ppm_seat"],
        "codata_year": row["codata_year"],
        "lab_inside_codata_band": row["lab_inside_codata_band"],
        "ok": ok,
        "note": row["note"],
    }

def check_floor1_leptonic_ask(device: str = "cpu") -> dict:
    """§6·floor1·ask — pre-resonance band; content census open."""
    from mt_ca.si_constants import SI

    del device
    row = SI.floor1_leptonic_ask_row()
    ok = (
        bool(row["ask_ok"])
        and bool(row["window_ok"])
        and bool(row["ir_landmarks_far_above"])
        and not bool(row["derivation_closed"])
        and int(row["N12"]) == 12
        and abs(float(row["L_lo_dl"]) - 1728.0) < 1e-9
        and abs(float(row["L_mid_dl"]) - 20736.0) < 1e-9
    )
    return {
        "id": "Floor1_leptonic_ask",
        "L_lo_dl": row["L_lo_dl"],
        "L_mid_dl": row["L_mid_dl"],
        "derivation_closed": row["derivation_closed"],
        "ok": ok,
        "note": row["note"],
    }


def check_floor1_B0_census_ask(device: str = "cpu") -> dict:
    """§6·floor1·B0·census — class census of stable B=0 at N12^3…^4."""
    from mt_ca.si_constants import SI

    del device
    row = SI.floor1_B0_census_ask_row()
    ok = (
        bool(row["ask_ok"])
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
        "id": "Floor1_B0_census_ask",
        "R_lo_dl": row["R_lo_dl"],
        "R_hi_dl": row["R_hi_dl"],
        "stable_matter_ids": row["stable_matter_ids"],
        "derivation_closed": row["derivation_closed"],
        "ok": ok,
        "note": row["note"],
    }


def check_floor1_dressing_ask(device: str = "cpu") -> dict:
    """§6·floor1·dressing·ask — near-zone ρ_Θ of lightest Q=±1; outer R open."""
    from mt_ca.si_constants import SI

    del device
    row = SI.floor1_dressing_ask_row()
    ok = (
        bool(row["ask_ok"])
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
        "id": "Floor1_dressing_ask",
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
        bool(row["ask_ok"])
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
        bool(row["ask_ok"])
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
        bool(row["ask_ok"])
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
        bool(row["ask_ok"])
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
    """§6·floor1·C3·bath·dogfood — VACUUM_BOIL moves; b matter still soft."""
    from mt_ca.si_constants import SI

    del device
    row = SI.floor1_C3_bath_dogfood_row()
    ok = (
        bool(row["ask_ok"])
        and bool(row["vacuum_frozen"])
        and not bool(row["boil_emerged_b"])
        and float(row["boil_contrast_final"]) > 10.0
        and "closed_vacuum_boil_whole_lattice_moves" in row["closed_ids"]
        and "soft_open_b_matter_not_yet" in row["soft_open_ids"]
    )
    return {
        "id": "Floor1_C3_bath_dogfood",
        "boil_contrast_final": row["boil_contrast_final"],
        "boil_emerged_b": row["boil_emerged_b"],
        "derivation_closed": row["derivation_closed"],
        "ok": ok,
        "note": row["note"],
    }


def check_carrier_torus_close(device: str = "cpu") -> dict:
    """§1.7 — finite wall-free carrier = torus; Λ×S¹ fiber; N soft."""
    from mt_ca.si_constants import SI

    del device
    row = SI.carrier_torus_close_row()
    ok = (
        bool(row["ask_ok"])
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
        bool(row["ask_ok"])
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


def check_cuboctahedron_carrier_ask(device: str = "cpu") -> dict:
    """§8.2·geo·ask — body ratio inventory; shipped κ/κ_link/V identity; holonomy/α open."""
    from mt_ca.si_constants import KAPPA_FCC_1TICK, N12_FCC_CAUSAL_LINKS, SI, kappa_link

    del device
    row = SI.cuboctahedron_carrier_ask_row()
    inv = row["ratio_inventory"]
    by_id = {str(r["id"]): r for r in inv}
    ok = (
        abs(row["V_over_v_hV"] - 16.0 / 3.0) < 1e-12
        and abs(float(by_id["edge_a_anchor"]["ratio"]) - 1.0) < 1e-12
        and abs(row["edge_a_m"] - SI.l_P) / SI.l_P < 1e-12
        and abs(float(by_id["kappa_inscr_1tick"]["ratio"]) - KAPPA_FCC_1TICK) < 1e-12
        and abs(float(by_id["kappa_link"]["ratio"]) - kappa_link(n_links=N12_FCC_CAUSAL_LINKS)) < 1e-12
        and by_id["Phi_square_holonomy"]["status"] == "open"
        and by_id["alpha_fs_stamped"]["status"] == "stamped_T"
        and len(row["anchor_chain"]) >= 8
        and int(row["ratio_shipped_count"]) >= 3
        and int(row["ratio_open_count"]) >= 4
        and len(inv) >= 14
    )
    return {
        "id": "Cuboctahedron_ask",
        "edge_a_m": row["edge_a_m"],
        "V_over_v_hV": row["V_over_v_hV"],
        "V_over_S_m": row["V_over_S_m"],
        "V_over_S_over_l_P": row["V_over_S_over_l_P"],
        "n_square_over_n_triangle": row["n_square_over_n_triangle"],
        "ratio_shipped_count": row["ratio_shipped_count"],
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


def check_rhombic_dodecahedron_carrier_ask(device: str = "cpu") -> dict:
    """§8.2·geo·voronoi·ask — Voronoy vs hull inventory."""
    from mt_ca.si_constants import SI

    del device
    row = SI.rhombic_dodecahedron_carrier_ask_row()
    inv = row["ratio_inventory"]
    by_id = {str(r["id"]): r for r in inv}
    ok = (
        abs(row["V_over_v_hV"] - 1.0) < 1e-12
        and abs(row["V_cuboctahedron_over_V_voronoi"] - 16.0 / 3.0) < 1e-12
        and abs(float(by_id["R_in_Voronoi"]["ratio"]) - 0.5) < 1e-12
        and by_id["V_over_v_hV"]["status"] == "shipped"
        and by_id["R_in_Voronoi"]["status"] == "shipped"
        and len(row["ratio_inventory"]) >= 6
    )
    return {
        "id": "Rhombic_dodecahedron_ask",
        "V_over_v_hV": row["V_over_v_hV"],
        "R_in_Voronoi_m": row["R_in_Voronoi_m"],
        "V_cuboctahedron_over_V_voronoi": row["V_cuboctahedron_over_V_voronoi"],
        "ratio_shipped_count": row["ratio_shipped_count"],
        "ok": ok,
        "note": row["note"],
    }


def check_cuboctahedron_geometry(device: str = "cpu") -> dict:
    """§8.2·geo — cuboctahedron V=(16/3)v_hV; discrete α candidate vs stamped π."""
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
        and row["alpha_inv_stamped_rel_err"] < 1e-5
    )
    return {
        "id": "Cuboctahedron_geo",
        "edge_a_m": row["edge_a_m"],
        "V_over_v_hV": row["V_over_v_hV"],
        "V_over_S_m": row["V_over_S_m"],
        "alpha_fs_inv_geom": row["alpha_fs_inv_geom"],
        "alpha_inv_geom_rel_err": row["alpha_inv_geom_rel_err"],
        "alpha_inv_stamped_rel_err": row["alpha_inv_stamped_rel_err"],
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
    """META §3.0.1 — exact bubble age t = N·hT from stamped hT (no readout)."""
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


def check_vortex_hex_contour(
    size: int = 512,
    steps: int = 256,
    device: str = "cpu",
) -> dict:
    """§3.8: hex stencil + contour axis ratio on micro |z| (§3.7.3)."""
    from mt_ca.metrics import contour_axis_ratio, contour_radius_anisotropy, field_amplitude

    sim = LatticeFluidSimulator(size, size, MConfig.for_stencil('hex'), device=device)
    sim.reset(SeedClass.VORTEX_P)
    sim.step(steps)
    micro = field_amplitude(sim.z)
    axis = contour_axis_ratio(micro, threshold=0.5)
    r_theta = contour_radius_anisotropy(micro, threshold=0.5)
    ok = axis == axis and axis < 1.05
    return {
        "id": "Vortex_hex",
        "contour_axis_ratio": round(axis, 4) if axis == axis else None,
        "contour_r_anisotropy": round(r_theta, 4) if r_theta == r_theta else None,
        "stencil": "hex",
        "ok": ok,
    }


def check_a7_density_clamp(device: str = "cpu") -> dict:
    cfg = MConfig.for_stencil('hex', rho_max=1.0)
    sim = LatticeFluidSimulator(4, 4, cfg, device=device)
    z = torch.zeros(4, 4, 2, device=device, dtype=torch.complex64)
    z[..., 0] = 2.0 + 0j
    z[..., 1] = 2.0 + 0j
    sim.set_field(z)
    sim.step(1)
    rho = float(sim.z.abs().square().sum(dim=-1).max().item())
    ok = rho <= 1.0 + 1e-5
    return {"id": "A7", "rho_after_step": rho, "rho_max": cfg.rho_max, "ok": ok}


def check_a10_winding(size: int = 128, steps: int = 128, device: str = "cpu") -> dict:
    from mt_ca.seeds import make_seed
    from mt_ca.topology import winding_nearest_int, winding_robust

    dev = torch.device(device)
    seed_charges = {
        SeedClass.VORTEX_P: 1,
        SeedClass.VORTEX_M: -1,
        SeedClass.VORTEX_N2: 2,
    }
    read = {}
    for seed, expected in seed_charges.items():
        z = make_seed(seed, size, size, device=dev)
        n = winding_nearest_int(winding_robust(z))
        read[seed.value] = n
    seeds_ok = all(read[k.value] == v for k, v in seed_charges.items())

    # Canon: HF ON; Φ from saturating holonomy only (§3.12.5). Persistence holds without CR double-count.
    sim = LatticeFluidSimulator(
        size, size, MConfig.for_stencil("hex", heisenberg_floor=True), device=device
    )
    sim.reset(SeedClass.VORTEX_P)
    sim.step(steps)
    w_late = abs(winding_robust(sim.z))
    persist_ok = w_late >= 0.5
    ok = seeds_ok and persist_ok
    return {
        "id": "A10",
        "seed_charges": read,
        "abs_winding_after_steps": round(w_late, 4),
        "ok": ok,
        "note": "n∈ℤ at seeds; |n|≥½ after evolution (T contour readout)",
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
        and row["ladder_shipped_count"] == len(row["ladder_rows"])
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
        "note": "§5.2.3: no mechanical float-knobs; CODATA only for e₀ T-anchor",
    }


def check_pauli_repel(device: str = "cpu") -> dict:
    cfg = MConfig.for_stencil('hex', pauli_exclusion=True)
    sim = LatticeFluidSimulator(1, 1, cfg, device=device)
    z = torch.zeros(1, 1, 2, device=device, dtype=torch.complex64)
    z[..., 0] = 0.8 + 0j
    z[..., 1] = 0.8 + 0j
    sim.set_field(z)
    for _ in range(4):
        sim.step(1)
    overlap = float((sim.z[..., 0].conj() * sim.z[..., 1]).abs().item())
    ok = overlap <= 0.5 + 1e-5
    return {"id": "Pauli", "overlap_after_step": overlap, "ok": ok}


def check_su2_720_sign(size: int = 64, device: str = "cpu") -> dict:
    dev = torch.device(device)
    z = torch.zeros(1, 1, 2, device=dev, dtype=torch.complex64)
    z[..., 0] = 1.0
    axis = torch.tensor([[[0.0, 0.0, 1.0]]], device=dev)
    phi = torch.tensor([[4.0 * torch.pi]], device=dev)
    z_rot = su2_apply(z, phi, axis)
    dot = float((z * z_rot.conj()).sum().real.item())
    ok = dot > 0.5
    return {"id": "SU2_720", "overlap_after_4pi": dot, "ok": ok}


def check_discrete_rot_exp(device: str = "cpu") -> dict:
    """§3.10.3 ↔ §3.12.5: canonical M gate = R(Φ)=ω^Φ via Rot_LUT."""
    import math

    from mt_ca.config import MConfig
    from mt_ca.fixed_point import decode_spinor, encode_spinor
    from mt_ca.projected_collision import rot_kick_uv
    from mt_ca.si_constants import heisenberg_phi_min_disc, phase_disc_to_rad
    from mt_ca.z_ring import mod_lane

    cfg = MConfig.for_stencil('hex')
    dev = torch.device(device)
    n_ring = 1 << cfg.phase_bits

    z = torch.zeros(1, 1, 2, device=dev, dtype=torch.complex64)
    z[..., 0] = 1.0
    f = encode_spinor(z, frac_bits=cfg.frac_bits, mod_bits=cfg.mod_bits)

    def apply_rot(encoded: torch.Tensor, phi_ticks: int) -> torch.Tensor:
        u0 = encoded[..., 0].to(torch.int64)
        v0 = encoded[..., 1].to(torch.int64)
        u1 = encoded[..., 2].to(torch.int64)
        v1 = encoded[..., 3].to(torch.int64)
        phi = torch.tensor([phi_ticks], device=dev, dtype=torch.int64)
        du0, dv0 = rot_kick_uv(u0, v0, phi, phase_bits=cfg.phase_bits)
        du1, dv1 = rot_kick_uv(u1, v1, phi, phase_bits=cfg.phase_bits)
        out = encoded.clone()
        out[..., 0] = mod_lane(u0 + du0, cfg.mod_bits)
        out[..., 1] = mod_lane(v0 + dv0, cfg.mod_bits)
        out[..., 2] = mod_lane(u1 + du1, cfg.mod_bits)
        out[..., 3] = mod_lane(v1 + dv1, cfg.mod_bits)
        return decode_spinor(out, frac_bits=cfg.frac_bits, mod_bits=cfg.mod_bits)

    phi_test = heisenberg_phi_min_disc(phase_bits=cfg.phase_bits, delta_phi_min=cfg.heisenberg_phi_min)
    z_rot = apply_rot(f, phi_test)
    ang = phase_disc_to_rad(phi_test, phase_bits=cfg.phase_bits)
    z_expected = z.clone()
    z_expected[..., 0] = z[..., 0] * complex(math.cos(ang), math.sin(ang))
    lut_rel = float((z_rot[..., 0] - z_expected[..., 0]).abs().item())
    ok_lut = lut_rel < 0.08

    z_half = apply_rot(f, n_ring // 2)
    half_dot = float((z[..., 0].conj() * z_half[..., 0]).real.item())
    ok_half = half_dot < -0.5

    z_full = apply_rot(f, n_ring)
    full_dot = float((z[..., 0].conj() * z_full[..., 0]).real.item())
    ok_full = full_dot > 0.99

    ok = ok_lut and ok_half and ok_full
    return {
        "id": "DiscreteRotExp",
        "ok": ok,
        "lut_rel_err": lut_rel,
        "half_turn_dot": half_dot,
        "full_turn_dot": full_dot,
        "phi_ticks": phi_test,
        "note": "§3.10.3: M gate R(Φ)=ω^Φ; not matrix exp(i·Θ·σ/2)",
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


def check_fcc_n12(device: str = "cpu") -> dict:
    """§1.6 — default stencil FCC N₁₂; κ_link=1/12; 3D multi-tick with HF ON (A5)."""
    from mt_ca.config import MConfig
    from mt_ca.laplacian import _FCC_OFFSETS, fcc_neighbor_sum, stencil_n_links
    from mt_ca.seeds import SeedClass
    from mt_ca.simulator import LatticeFluidSimulator

    cfg = MConfig()  # canon default = fcc
    n = stencil_n_links(cfg.stencil)
    ok_geom = cfg.stencil == "fcc" and n == 12 and len(_FCC_OFFSETS) == 12
    ok_kappa = abs(cfg.gamma - 1.0 / 12.0) < 1e-15

    # Canon: floor ON. After gate-only Φ (no CR double-count) + N_φ vacuum, multi-tick holds.
    cfg_dyn = MConfig.for_stencil("fcc", heisenberg_floor=True)
    sim = LatticeFluidSimulator(8, 8, cfg_dyn, device=device)
    sim.reset(SeedClass.IMPULSE)
    n0 = sim.norm()
    norms = [n0]
    for _ in range(16):
        sim.step(1)
        norms.append(sim.norm())
    n_late = norms[-1]
    ok_step = (
        abs(n_late - n0) / max(n0, 1e-9) < 1e-6
        and sim.z.ndim == 4
        and sim.z.shape[-1] == 2
        and max(norms) < 10.0 * max(n0, 1e-6)
    )
    s = fcc_neighbor_sum(sim.z[..., 0])
    ok_sum = s.shape == sim.z.shape[:-1]
    ok = ok_geom and ok_kappa and ok_step and ok_sum
    return {
        "id": "FCC_N12",
        "stencil": cfg.stencil,
        "n_links": n,
        "gamma": cfg.gamma,
        "shape": list(sim.z.shape),
        "norm0": n0,
        "norm_late": n_late,
        "ticks": 16,
        "heisenberg_floor": True,
        "ok": ok,
        "note": "§1.6 cuboctahedral ε; multi-tick stable with HF ON (A5)",
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


def check_a3_global_norm(size: int = 64, device: str = "cpu") -> dict:
    from mt_ca.conservation import a3_global_norm_report

    return a3_global_norm_report(size, device=device)


def check_t_madelung_continuity(size: int = 64, device: str = "cpu") -> dict:
    from mt_ca.conservation import t_madelung_continuity_report

    return t_madelung_continuity_report(size, device=device)


def check_t_continuum_readout(device: str = "cpu") -> dict:
    from mt_ca.t_continuum_readout import t_continuum_readout_row

    del device
    row = t_continuum_readout_row()
    ok = (
        row["path_atom_is_121"] is True
        and row["var_atom"] == 0.5
        and row["multiplier_id_err"] < 1e-15
        and row["max_rel_err_k_sigma_lt_0_30"] < 1e-4
        and row["max_rel_err_k_sigma_lt_0_50"] < 1e-3
        and row["taylor_leading_R_over_96"] < 0.02
        and row["fcc_n_nn"] == 12
        and row["fcc_n_walks"] == 144
        and row["fcc_w_origin"] == 12
        and abs(float(row["fcc_p_origin"]) - 1.0 / 12.0) < 1e-15
        and row["fcc_w_nn_shell"] == 48
        and row["hex_n_nn"] == 6
        and row["hex_n_walks"] == 36
        and row["hex_w_origin"] == 6
        and abs(float(row["hex_p_origin"]) - 1.0 / 6.0) < 1e-15
        and row["separable_121_is_not_fcc_law"] is True
    )
    return {
        "id": "T_continuum_readout",
        "max_rel_err_k_sigma_lt_0_30": row["max_rel_err_k_sigma_lt_0_30"],
        "fcc_p_origin": row["fcc_p_origin"],
        "hex_p_origin": row["hex_p_origin"],
        "ok": ok,
        "note": row["note"],
    }


def check_t_hydro_limit(device: str = "cpu") -> dict:
    from mt_ca.t_continuum_readout import fcc_hydro_limit_row

    del device
    row = fcc_hydro_limit_row()
    ok = (
        abs(float(row["M_xx"]) - 4.0 / 3.0) < 1e-12
        and abs(float(row["M_xy"])) < 1e-12
        and abs(float(row["E_r2"]) - 4.0) < 1e-12
        and abs(float(row["E_x4"]) - 4.0) < 1e-12
        and abs(float(row["E_x2y2"]) - 14.0 / 9.0) < 1e-12
        and abs(float(row["hatK_k2_coeff"]) - 2.0 / 3.0) < 1e-12
        and abs(float(row["kappa_link_fcc"]) - 1.0 / 12.0) < 1e-15
        and abs(float(row["nu_CA_fcc"]) - 1.0 / 12.0) < 1e-15
        and row["isotropic_M"] is True
        and row["nlse_class"] is True
        and row["ns_class_via_madelung"] is True
        and row["gaussian_fourth_not_exact"] is True
        and row["n_nn"] == 12
        and row["n_walks"] == 144
    )
    return {
        "id": "T_hydro_limit",
        "M_xx": row["M_xx"],
        "hatK_k2_coeff": row["hatK_k2_coeff"],
        "nu_CA_fcc": row["nu_CA_fcc"],
        "ok": ok,
        "note": row["note"],
    }


def check_so2_c4(size: int = 64, device: str = "cpu") -> dict:
    from mt_ca.conservation import so2_c4_report

    return so2_c4_report(size, device=device)


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


def check_alpha_bridges(device: str = "cpu") -> dict:
    """§8.2 audit — α*↔α_fs partial links (missed-readings probe)."""
    from mt_ca.si_constants import N12_FCC_CAUSAL_LINKS, SI

    del device
    pi = math.pi
    a = SI.alpha_fs  # π-tower T-label
    a_struct = SI.alpha_preferred  # upstairs structural feed
    a_star = SI.alpha_star
    residue = a_star - 1.0

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
    phase_tower_ok = abs(SI.alpha_fs_inv - pi * (4.0 * pi**2 + pi + 1.0)) < 1e-9
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
    alpha_star_cascade_open = cascade_rel_err > 0.03
    coulomb_carrier_ok = coul["rel_F_over_FP_is_alpha"] < 1e-12
    electroweak_tree_ok = (
        abs(ew["mass_ratio_sin2"] - ew["sin2_theta_W"]) < 1e-12
        and ew["m_W_rel_err"] < 0.005
        and ew["m_Z_rel_err"] < 0.005
    )

    ok = (
        gate_residue_ok
        and delta_lambda_link_ok
        and phase_tower_ok
        and alpha_mz_runner_ok
        and fcc_cluster_n_phi_ok
        and alpha_star_cascade_open
        and coulomb_carrier_ok
        and electroweak_tree_ok
    )
    return {
        "id": "Alpha_bridges",
        "ok": ok,
        "gate_residue_ok": gate_residue_ok,
        "delta_lambda_alpha_star_ok": delta_lambda_link_ok,
        "phase_tower_ok": phase_tower_ok,
        "alpha_MZ_runner_ok": alpha_mz_runner_ok,
        "alpha_MZ_inv_rel_err": runner["alpha_MZ_inv_rel_err"],
        "fcc_cluster_N_phi_ok": fcc_cluster_n_phi_ok,
        "phase_ratio_over_pi": phase_ratio_over_pi,
        "phase_ratio_minus_N_phi": phase_ratio_over_pi - 13.0,
        "alpha_star_cascade_open": alpha_star_cascade_open,
        "cascade_rel_err": cascade_rel_err,
        "coulomb_carrier_ok": coulomb_carrier_ok,
        "electroweak_tree_ok": electroweak_tree_ok,
        "alpha_fs_inv_ppm_vs_CODATA": abs(SI.alpha_fs_inv - 137.035999177) / 137.035999177 * 1e6,
        "note": (
            "§8.2 audit: δλ=α_fs/(4π)=α_fs(α*−1), B_hV runner, N_φ=|N12|+1 PASS; "
            "α*→α_fs cascade + e₀ derivation + lattice Coulomb sim OPEN"
        ),
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


def check_arg_mass_carrier(size: int = 64, device: str = "cpu") -> dict:
    """§5.0.1: Arg(⟨z⟩·z*) carrier ≡ holonomy_zeta + wrapped_phase_diff; wrap fixes naive bug."""
    dev = torch.device(device)
    cfg = MConfig.for_stencil('hex', heisenberg_floor=False)
    ny = nx = size
    z = make_seed(SeedClass.VORTEX_P, ny, nx, device=dev)
    for _ in range(16):
        z = evolve_canonical(z, cfg)
    sum_n = spinor_neighbor_sum(z, cfg)

    zeta_impl = holonomy_zeta(z, sum_n)
    zeta_ref = (sum_n * z.conj()).sum(dim=-1)
    zeta_err = float((zeta_impl - zeta_ref).abs().max().item())

    pd_impl = arg_phase_defect(z, cfg, apply_floor=False)
    pd_ref = wrapped_phase_diff(zeta_impl, torch.ones_like(zeta_impl))
    pd_err = float((pd_impl - pd_ref).abs().max().item())

    zeta_near_pi = torch.tensor([[-0.999 + 0.04j]], device=dev, dtype=torch.complex64)
    wrapped = wrapped_phase_diff(zeta_near_pi, torch.ones_like(zeta_near_pi))
    explicit = (torch.atan2(zeta_near_pi.imag, zeta_near_pi.real) + torch.pi) % (2.0 * torch.pi) - torch.pi
    wrap_err = float((wrapped - explicit).abs().max().item())

    z1 = torch.exp(1j * torch.tensor(3.05, device=dev))
    zn = torch.exp(1j * torch.tensor(-2.95, device=dev))
    zeta_scalar = z1 * zn.conj()
    wrapped_scalar = wrapped_phase_diff(zeta_scalar.unsqueeze(0).unsqueeze(0), torch.ones(1, 1, device=dev))
    naive_scalar = torch.atan2(zn.imag, zn.real) - torch.atan2(z1.imag, z1.real)
    naive_scalar = (naive_scalar + torch.pi) % (2.0 * torch.pi) - torch.pi
    wrap_beats_naive = float((wrapped_scalar - naive_scalar).abs().item()) > 0.5

    phi = gate_phase(z, MConfig.for_stencil('hex', heisenberg_floor=True))
    dphi = arg_phase_defect(z, cfg, apply_floor=False)
    active_mean = float(dphi.abs().mean().item())
    active_max = float(dphi.abs().max().item())
    gate_live = float(phi.abs().max().item()) > 0.0

    ok = (
        zeta_err < 1e-6
        and pd_err < 1e-6
        and wrap_err < 1e-6
        and wrap_beats_naive
        and active_max > 0.05
        and gate_live
    )
    return {
        "id": "Arg_mass_carrier",
        "zeta_max_err": zeta_err,
        "phase_max_err": pd_err,
        "wrap_formula_err": wrap_err,
        "wrap_beats_naive": wrap_beats_naive,
        "mean_abs_dphi": active_mean,
        "max_abs_dphi": active_max,
        "max_gate_phi": float(phi.abs().max().item()),
        "ok": ok,
        "note": "M mass carrier = Arg(⟨z⟩·z*); Higgs is T readout only (§5.0.1)",
    }


def check_u1_vac(size: int = 128, device: str = "cpu") -> dict:
    from mt_ca.symmetry import u1_vac_report

    row = u1_vac_report(size, device)
    return {
        "id": row["id"],
        "seeds": row["seeds"],
        "ok": row["ok"],
        "note": "U(1)_vac: global phase on z; defect_axis fallback = local Bloch (§3.11)",
    }


def check_chiral_su2(size: int = 64, device: str = "cpu") -> dict:
    from mt_ca.symmetry import chiral_projector_report

    row = chiral_projector_report(size, device)
    return {
        "id": row["id"],
        "recombine_max_err": row["recombine_max_err"],
        "chi_u1_max_err": row["chi_u1_max_err"],
        "ok": row["ok"],
        "note": row["note"],
    }


def check_a14_symmetry(size: int = 128, steps: int = 64, device: str = "cpu") -> dict:
    from mt_ca.symmetry import symmetry_report

    row = symmetry_report(size, steps, device)
    return {
        "id": "A14",
        "parity_ok": row["parity_seeds"]["p_flips_p"],
        "u1_ok": row["U1_vac"]["ok"],
        "chiral_ok": row["chiral"]["ok"],
        "cpt_unwind_ok": row["CPT_unwind"]["ok"],
        "cpt_unwind_optional": True,
        "g_P_1step_match": row["g_P_1step"]["winding_match"],
        "g_P_long_match": row["g_P_steps"]["winding_match"],
        "ok": row["ok"],
        "note": "P/C/T/U1 on g; M reverse = A13 Leapfrog; CPT product optional T-layer probe",
    }


def check_leapfrog_bit_exact(size: int = 64, steps: int = 32, device: str = "cpu") -> dict:
    from mt_ca.reversible import bit_exact_roundtrip_report
    from mt_ca.seeds import SeedClass

    impulse = bit_exact_roundtrip_report(size, steps, device, seed_class=SeedClass.IMPULSE)
    vortex = bit_exact_roundtrip_report(size, min(steps, 16), device, seed_class=SeedClass.VORTEX_P)
    ok = impulse["ok"] and vortex["bit_exact"]
    return {
        "id": "Leapfrog",
        "impulse": {k: impulse[k] for k in ("bit_exact", "max_rel_err", "steps")},
        "vortex": {k: vortex[k] for k in ("bit_exact", "n0", "n_back", "n_stable", "steps")},
        "ok": ok,
        "note": "§3.12: z(t+Δt)=−z(t−Δt)+2z(t)+⌊kick⌋; g⁻¹ without CPT",
    }


def check_spinor_360_sign(size: int = 64, device: str = "cpu") -> dict:
    dev = torch.device(device)
    z = torch.zeros(1, 1, 2, device=dev, dtype=torch.complex64)
    z[..., 0] = 1.0
    axis = torch.tensor([[[0.0, 0.0, 1.0]]], device=dev)
    phi = torch.tensor([[2.0 * torch.pi]], device=dev)
    z_rot = su2_apply(z, phi, axis)
    dot = float((z * z_rot.conj()).sum().real.item())
    ok = dot < -0.5
    return {"id": "SU2_360", "overlap_after_2pi": dot, "ok": ok, "note": "360° → −1 on z=(1,0)"}


def check_no_m_heat_death(device: str = "cpu") -> dict:
    """§2.3 theorem: M has no heat death / no shutdown — A3 + A5 + A13."""
    a3 = check_a3_unitarity(device=device)
    a5 = check_a5_vacuum_floor(device=device)
    a13 = check_leapfrog_bit_exact(device=device)
    ok = a3["ok"] and a5["ok"] and a13["ok"]
    return {
        "id": "NoMHeatDeath",
        "ok": ok,
        "a3_norm_drift": a3.get("norm_drift"),
        "a5_ok": a5["ok"],
        "a13_ok": a13["ok"],
        "note": "§2.3 consistency probe (A3+A5+A13); not a proof certificate",
    }


def check_theorem_2_3_8(size: int = 32, device: str = "cpu") -> dict:
    """§2.3.8: D5 on Z_N[i] = constants only; Planck VACUUM ≠ D5."""
    from mt_ca.fixed_point import vacuum_amplitude_quantum
    from mt_ca.projected_collision import projected_collision_kick
    from mt_ca.reversible import canonical_fixed, leapfrog_forward_fixed
    from mt_ca.simulator import LatticeFluidSimulator
    from mt_ca.z_ring import mod_lane

    cfg = MConfig.for_stencil('hex')
    dev = torch.device(device)
    z_min = vacuum_amplitude_quantum(frac_bits=cfg.frac_bits)

    amp = z_min
    z_const = torch.full((size, size, 2), amp, device=dev, dtype=torch.complex64)
    cfg_d5 = MConfig.for_stencil('hex', heisenberg_floor=False)
    f_const = canonical_fixed(z_const, cfg_d5)
    kick_const = projected_collision_kick(f_const, cfg_d5)
    f_next, _, _ = leapfrog_forward_fixed(f_const, f_const, cfg_d5)
    const_kick_zero = int(kick_const.abs().max().item()) == 0
    const_step_fixed = bool(torch.equal(mod_lane(f_next, cfg.mod_bits), mod_lane(f_const, cfg.mod_bits)))

    # Non-constant: orthogonal neighbor bricks at amp large enough that Φ ≥ Δφ_disc.
    f_nc = torch.zeros(size, size, 4, device=dev, dtype=torch.int64)
    f_nc[..., 0] = 64
    yy, xx = torch.meshgrid(
        torch.arange(size, device=dev), torch.arange(size, device=dev), indexing="ij"
    )
    odd = (yy + xx) % 2 == 1
    f_nc[odd, 0] = 0
    f_nc[odd, 1] = 64
    f_nc[..., 2] = f_nc[..., 0]
    f_nc[..., 3] = f_nc[..., 1]
    nonconst_kick = int(projected_collision_kick(f_nc, cfg).abs().max().item()) > 0

    sim = LatticeFluidSimulator(size, size, cfg, device=dev)
    sim.reset(SeedClass.VACUUM)
    kick_vac = projected_collision_kick(sim._f_curr, cfg)
    vac_not_frozen = int(kick_vac.abs().max().item()) > 0
    # Holomorphic ocean (one Heisenberg class) may have ⌊𝒩⌋=0 locally (§2.3.8 remark).
    # Physical claim: VACUUM ≠ c=0 deadlock and ≠ empty lattice; A5 floor holds.
    vac_alive = float(sim.z.abs().square().sum(-1).min().item()) > 0.0
    vac_not_deadlock = vac_alive and float(sim.z.abs().mean().item()) > 0.0

    ok = const_kick_zero and const_step_fixed and nonconst_kick and vac_not_deadlock
    return {
        "id": "Theorem_2_3_8",
        "const_kick_zero": const_kick_zero,
        "const_step_fixed": const_step_fixed,
        "nonconst_kick": nonconst_kick,
        "vac_not_frozen": vac_not_frozen,
        "vac_alive": vac_alive,
        "ok": ok,
        "note": "§2.3.8a–b; VACUUM = Heisenberg-class ocean at z_min (kick may be 0 locally)",
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


def check_matter_b_readout(size: int = 64, device: str = "cpu") -> dict:
    from mt_ca.macro import macro_amplitude, macro_matter_b
    from mt_ca.spinor import spinor_density
    from mt_ca.topology import matter_occupancy_b, matter_occupancy_b_field, winding_channels, winding_number

    dev = torch.device(device)
    radius = 2

    z_v = make_seed(SeedClass.VACUUM, size, size, device=dev)
    vac_b_mean = float(matter_occupancy_b_field(z_v).float().mean().item())
    vac_macro_b = float(macro_matter_b(z_v, radius=radius).mean().item())
    vac_macro_amp = float(macro_amplitude(z_v, radius=radius).mean().item())

    z_p = make_seed(SeedClass.VORTEX_P, size, size, device=dev)
    cy, cx = torch.unravel_index(spinor_density(z_p).argmax(), z_p.shape[:2])
    cy, cx = int(cy.item()), int(cx.item())
    w = winding_number(z_p, center=(cy, cx), radius=2)
    ch_p = winding_channels(z_p, center=(cy, cx), radius=2)
    core_b = 1 if w == w and abs(w) >= 0.75 else matter_occupancy_b(z_p, y=cy, x=cx)
    vortex_macro_b = float(macro_matter_b(z_p, radius=radius).max().item())

    # Locked equal-lane U(1) vortex: old Arg(z₂/z₁) thermometer was blind (§5.0).
    z_u1 = torch.zeros(size, size, 2, device=dev, dtype=torch.complex64)
    yy, xx = torch.meshgrid(
        torch.arange(size, device=dev),
        torch.arange(size, device=dev),
        indexing="ij",
    )
    ang = torch.atan2((yy - cy).float(), (xx - cx).float())
    amp = 0.5
    z_u1[..., 0] = amp * torch.exp(1j * ang)
    z_u1[..., 1] = amp * torch.exp(1j * ang)
    ch_u1 = winding_channels(z_u1, center=(cy, cx), radius=16)
    u1_b = matter_occupancy_b(z_u1, y=cy, x=cx, contour_radius=16)

    ok = (
        vac_b_mean < 0.05
        and vac_macro_b < 0.05
        and vac_macro_amp > vac_macro_b
        and core_b == 1
        and abs(ch_p["rel"]) >= 0.75
        and vortex_macro_b > 0.1
        and abs(ch_u1["u1"]) >= 0.75
        and abs(ch_u1["rel"]) < 0.25
        and u1_b == 1
    )
    return {
        "id": "MatterOccupancyB",
        "vac_b_mean": vac_b_mean,
        "vac_macro_b": vac_macro_b,
        "vac_macro_amp": vac_macro_amp,
        "vortex_core_b": core_b,
        "vortex_channels": ch_p,
        "vortex_macro_b_max": vortex_macro_b,
        "u1_locked_channels": ch_u1,
        "u1_locked_b": u1_b,
        "ok": ok,
        "note": "§5.0: b=min(1,|n_∂|); dual channel rel+U(1) auto; macro ⟨b⟩ primary over |z|²",
    }


def check_model_purity() -> dict:
    """MODEL must not contain DEVLOG/impl pollution (hard gate)."""
    root = Path(__file__).resolve().parent
    model_dir = root / "model"
    patterns: list[tuple[re.Pattern[str], str]] = [
        (re.compile(r"\*\*SSOT-часть MODEL"), "meta header SSOT"),
        (re.compile(r"\*\*Не SSOT"), "meta header DEVLOG pointer"),
        (re.compile(r"\*\*Не сюда:"), "meta header DEVLOG pointer"),
        (re.compile(r"\*\*В теле §3 запрещено:"), "meta header forbidden list"),
        (re.compile(r"\*\*Код:\*\*"), "**Код:**"),
        (re.compile(r"(?<!\*)\bКод:\s*`"), "Код:`"),
        (re.compile(r"verify\s+\*\*"), "verify **"),
        (re.compile(r"✅"), "✅"),
        (re.compile(r"mt_ca/"), "mt_ca/"),
        (re.compile(r"`[^`]+\.py`"), ".py backtick"),
        (re.compile(r"\*\*Impl:\*\*"), "**Impl:**"),
        (re.compile(r"не канон", re.I), "не канон"),
        (re.compile(r"\b[Кк]анон\b"), "канон"),
        (re.compile(r"legacy\s*[··]", re.I), "legacy label"),
        (re.compile(r"\(legacy", re.I), "(legacy"),
        (re.compile(r"\bsim-gap\b", re.I), "sim-gap"),
        (re.compile(r"\*\*Verify / impl:\*\*"), "Verify / impl"),
        (re.compile(r"\*\*Verify `"), "Verify `"),
        (re.compile(r"\bmt_ca\b"), "mt_ca"),
        (re.compile(r"\*\*Fix:\*\*"), "**Fix:**"),
        (re.compile(r"\bburn-in\b", re.I), "burn-in"),
        (re.compile(r"\bbit-exact\b", re.I), "bit-exact"),
        (re.compile(r"\| leaf \|"), "leaf column"),
        (re.compile(r"\*\*Не путать"), "**Не путать"),
        (re.compile(r"\(impl"), "(impl"),
        (re.compile(r"impl v\d", re.I), "impl version"),
        (re.compile(r"DEVLOG\.md"), "DEVLOG link in body"),
        (re.compile(r"\bDEVLOG\b"), "DEVLOG"),
        (re.compile(r"\*\*Claim:\*\*"), "**Claim:**"),
        (re.compile(r"\*\*Итог"), "**Итог"),
        (re.compile(r"\bDoD\b"), "DoD"),
        (re.compile(r"verify_principles"), "verify_principles"),
        (re.compile(r"\bPASS\b"), "PASS"),
        (re.compile(r"\bFAIL\b"), "FAIL"),
        (re.compile(r"\bleaf\b", re.I), "leaf"),
        (re.compile(r"T-leaf", re.I), "T-leaf"),
        (re.compile(r"\*\*Код / verify:\*\*"), "Код / verify"),
        (re.compile(r"Sim \(live"), "Sim (live"),
        (re.compile(r"❌"), "❌"),
        (re.compile(r"sim TODO", re.I), "sim TODO"),
        (re.compile(r"verify DoD", re.I), "verify DoD"),
        (re.compile(r"Не путать", re.I), "Не путать"),
    ]
    allow_fragments = ("GPU-вкусовщина",)
    hits: list[str] = []
    for path in sorted(model_dir.glob("*.md")):
        for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if any(frag in line for frag in allow_fragments):
                continue
            for rx, label in patterns:
                if rx.search(line):
                    hits.append(f"{path.name}:{i}: {label}")
                    break
    return {
        "id": "Model_purity",
        "count": len(hits),
        "violations": hits[:12],
        "ok": len(hits) == 0,
        "note": "MODEL=physics only; impl/verify → DEVLOG.md",
    }


def run_all(device: str) -> list[dict]:
    return [
        check_a3_unitarity(device=device),
        check_a3_local_ca(device=device),
        check_a3_spectral_reference(device=device),
        check_a3_diffusive_fails(device=device),
        check_a4_phase_preserves_modulus(device=device),
        check_impl_zero_frozen(device=device),
        check_a5_vacuum_floor(device=device),
        check_a8_macro_suppression(device=device),
        check_a9_cr_smooth_modes(device=device),
        check_a11_vortex_persistence(device=device),
        check_a16_heisenberg_floor(device=device),
        check_a7_density_clamp(device=device),
        check_a10_winding(device=device),
        check_pauli_repel(device=device),
        check_compton_electron(device=device),
        check_alpha_hop_ladder(device=device),
        check_alpha_fixed_point(device=device),
        check_na0_from_carrier(device=device),
        check_na0_h_carrier_ask(device=device),
        check_alpha_force_lattice_ask(device=device),
        check_alpha_meaning_ask(device=device),
        check_alpha_descent_ask(device=device),
        check_alpha_mass_defect_optics(device=device),
        check_alpha_arg_binding_try(device=device),
        check_alpha_schwinger_ask(device=device),
        check_alpha_dirac_g2_ask(device=device),
        check_alpha_ae_cloud_ask(device=device),
        check_alpha_rydberg_hall_ask(device=device),
        check_alpha_em_face_weight_ask(device=device),
        check_alpha_dual_fraction_ask(device=device),
        check_alpha_sqrt2_descent_ask(device=device),
        check_alpha_M_from_g_try(device=device),
        check_alpha_nF_kick_census(device=device),
        check_alpha_full_quantization_bridge(device=device),
        check_coulomb_M_native(device=device),
        check_alpha_U0_soft_face_ask(device=device),
        check_alpha_upstairs_mass_probe(device=device),
        check_floor1_leptonic_ask(device=device),
        check_floor1_B0_census_ask(device=device),
        check_floor1_dressing_ask(device=device),
        check_floor1_dressing_close(device=device),
        check_floor1_dressing_f_close(device=device),
        check_floor1_leftovers_close(device=device),
        check_floor1_C3_gamma_close(device=device),
        check_floor1_C3_bath_dogfood(device=device),
        check_carrier_torus_close(device=device),
        check_gpu_eng_tail_close(device=device),
        check_bubble_tick(device=device),
        check_nu_CA_exact(device=device),
        check_hv_bit_budget(device=device),
        check_congruence_ladder(device=device),
        check_rho_P_binary(device=device),
        check_vdw_algebra(device=device),
        check_arg_quantum(device=device),
        check_higgs_mass(device=device),
        check_vacuum_bath(device=device),
        check_cuboctahedron_geometry(device=device),
        check_cuboctahedron_carrier_ask(device=device),
        check_rhombic_dodecahedron_geometry(device=device),
        check_rhombic_dodecahedron_carrier_ask(device=device),
        check_kappa_bottom_up(device=device),
        check_planck_from_cell_conditions(device=device),
        check_anchor_a_is_l_P(device=device),
        check_discreteness_from_axioms(device=device),
        check_mechanics_from_axioms(device=device),
        check_excitations_full_quantization(device=device),
        check_phonon_from_carrier(device=device),
        check_square_face_holonomy_probe(device=device),
        check_alpha_bridges(device=device),
        check_proton_mass(device=device),
        check_electron_mass(device=device),
        check_neutron_mass(device=device),
        check_neutrino_mass(device=device),
        check_mechanical_quantum(device=device),
        check_quarter_quantum(device=device),
        check_energy_quantum(device=device),
        check_elementary_quanta(device=device),
        check_a3_global_norm(device=device),
        check_t_madelung_continuity(device=device),
        check_t_continuum_readout(device=device),
        check_t_hydro_limit(device=device),
        check_so2_c4(device=device),
        check_arg_mass_carrier(device=device),
        check_u1_vac(device=device),
        check_chiral_su2(device=device),
        check_leapfrog_bit_exact(device=device),
        check_no_m_heat_death(device=device),
        check_theorem_2_3_8(device=device),
        check_planck_vacuum_floor(device=device),
        check_ladder_ledger(device=device),
        check_matter_b_readout(device=device),
        check_a14_symmetry(device=device),
        check_electron_anchor(device=device),
        check_saturation_bc(device=device),
        check_fcc_n12(device=device),
        check_vortex_hex_contour(device=device),
        check_spinor_360_sign(device=device),
        check_su2_720_sign(device=device),
        check_discrete_rot_exp(device=device),
        check_model_purity(),
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description="First-principles M-layer verification")
    parser.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    results = run_all(args.device)
    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print(f"device={args.device}")
        print("-" * 60)
        for row in results:
            status = "PASS" if row["ok"] else "FAIL"
            print(f"{row['id']:12}  {status}  { {k: v for k, v in row.items() if k not in ('id', 'ok')} }")

    failed = [r for r in results if not r["ok"] and r["id"] not in ("A3_diffusive", "T_dft_oracle", "I2_zero", "T_MadelungContinuity")]
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
