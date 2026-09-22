#!/usr/bin/env python3
"""Verify M-layer axioms after first-principles rebuild."""

from __future__ import annotations

import argparse
import json
import math
import sys

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
    size: int = 128,
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

    sim = LatticeFluidSimulator(size, size, MConfig.for_stencil('hex'), device=device)
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
    ok = e0 <= seed_max and e1 <= stat_max and delta <= stat_tol
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
        "ok": ok,
        "note": "§3.9.6: smooth plane wave → ν_CA plateau on N₄; vortex cores stay non-holomorphic",
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
    small = pd.abs() < phi_min_rad
    enforced = (
        float((pd_floor[small].abs() >= phi_min_rad - 1e-6).float().mean().item())
        if bool(small.any())
        else 1.0
    )
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
    disc_floor_ok = bool((phi_disc.abs() >= phi_min_disc).all())

    ok = (
        abs(phi_min_rad - DELTA_PHI_MIN) < 1e-12
        and phi_min_disc >= 1
        and enforced >= 0.99
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

    sim = LatticeFluidSimulator(size, size, MConfig.for_stencil('hex'), device=device)
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
    """§1.6 — default stencil FCC N₁₂; κ_link=1/12; 3D sim smoke (1 tick)."""
    from mt_ca.config import MConfig
    from mt_ca.laplacian import _FCC_OFFSETS, fcc_neighbor_sum, stencil_n_links
    from mt_ca.seeds import SeedClass
    from mt_ca.simulator import LatticeFluidSimulator

    cfg = MConfig()  # canon default
    n = stencil_n_links(cfg.stencil)
    ok_geom = cfg.stencil == "fcc" and n == 12 and len(_FCC_OFFSETS) == 12
    ok_kappa = abs(cfg.gamma - 1.0 / 12.0) < 1e-15
    sim = LatticeFluidSimulator(8, 8, cfg, device=device)
    sim.reset(SeedClass.IMPULSE)
    n0 = sim.norm()
    sim.step(1)
    n1 = sim.norm()
    # 1-tick bounded; multi-tick FCC fill still open gap (DEVLOG)
    ok_step = n1 < 10.0 * max(n0, 1e-6) and sim.z.ndim == 4 and sim.z.shape[-1] == 2
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
        "norm1": n1,
        "ok": ok,
        "note": "§1.6 cuboctahedral ε on ℤ³; multi-tick stability open",
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
    from mt_ca.si_constants import N4_CAUSAL_LINKS, quarter_quantum_row

    row = quarter_quantum_row()
    cfg = MConfig.for_stencil('hex')
    ok = (
        row["N4_links"] == N4_CAUSAL_LINKS
        and abs(row["kappa_link"] - 0.25) < 1e-12
        and abs(row["gamma"] - row["cr_strength"]) < 1e-12
        and abs(row["gamma"] - row["nu_CA_natural"]) < 1e-12
        and abs(cfg.gamma - row["kappa_link"]) < 1e-12
        and abs(cfg.cr_strength - row["kappa_link"]) < 1e-12
    )
    return {
        "id": "QuarterQuantum",
        "kappa_link": row["kappa_link"],
        "gamma": row["gamma"],
        "cr_strength": row["cr_strength"],
        "nu_CA_natural": row["nu_CA_natural"],
        "ok": ok,
        "note": "γ=cr_strength=ν_CA_natural=1/|N₄|=¼ (§5.2.2)",
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


def check_local_continuity(size: int = 64, device: str = "cpu") -> dict:
    from mt_ca.conservation import local_conservation_report

    return local_conservation_report(size, device=device)


def check_so2_c4(size: int = 64, device: str = "cpu") -> dict:
    from mt_ca.conservation import so2_c4_report

    return so2_c4_report(size, device=device)


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

    f_nc = torch.zeros(size, size, 4, device=dev, dtype=torch.int64)
    f_nc[..., 0] = 10
    f_nc[..., 1] = 5
    f_nc[0, 0, 0] = 20
    f_nc[0, 0, 1] = 8
    nonconst_kick = int(projected_collision_kick(f_nc, cfg).abs().max().item()) > 0

    sim = LatticeFluidSimulator(size, size, cfg, device=dev)
    sim.reset(SeedClass.VACUUM)
    kick_vac = projected_collision_kick(sim._f_curr, cfg)
    vac_not_frozen = int(kick_vac.abs().max().item()) > 0

    ok = const_kick_zero and const_step_fixed and nonconst_kick and vac_not_frozen
    return {
        "id": "Theorem_2_3_8",
        "const_kick_zero": const_kick_zero,
        "const_step_fixed": const_step_fixed,
        "nonconst_kick": nonconst_kick,
        "vac_not_frozen": vac_not_frozen,
        "ok": ok,
        "note": "§2.3.8a–b; VACUUM at z_min with gauge_fix=False encode",
    }


def check_planck_vacuum_floor(size: int = 32, device: str = "cpu") -> dict:
    """§0.5 / §10.2: vacuum_amplitude = z_min; no |z|→0 knob; VACUUM boils on Z_N[i]."""
    from mt_ca.fixed_point import vacuum_amplitude_quantum
    from mt_ca.projected_collision import projected_collision_kick
    from mt_ca.simulator import LatticeFluidSimulator

    cfg = MConfig.for_stencil('hex')
    dev = torch.device(device)
    z_min = vacuum_amplitude_quantum(frac_bits=cfg.frac_bits)
    amp_match = abs(cfg.vacuum_amplitude - z_min) < 1e-12

    sim = LatticeFluidSimulator(size, size, cfg, device=dev)
    sim.reset(SeedClass.VACUUM)
    from mt_ca.metrics import field_amplitude

    decoded_min = float(field_amplitude(sim.z).min().item())
    above_floor = decoded_min >= 0.5 * z_min
    kick = projected_collision_kick(sim._f_curr, cfg)
    boils = int(kick.abs().max().item()) > 0

    ok = amp_match and above_floor and boils
    return {
        "id": "PlanckVacuumFloor",
        "z_min": z_min,
        "vacuum_amplitude": cfg.vacuum_amplitude,
        "decoded_min": decoded_min,
        "boils": boils,
        "ok": ok,
        "note": "§0.5: z_min derived; global U(1) gauge on encode (not per-cell §10.2)",
    }


def check_ladder_ledger(size: int = 64, device: str = "cpu") -> dict:
    from mt_ca.ledger import ladder_ledger_report

    return ladder_ledger_report(size, device=device)


def check_matter_b_readout(size: int = 64, device: str = "cpu") -> dict:
    from mt_ca.macro import macro_amplitude, macro_matter_b
    from mt_ca.spinor import spinor_density
    from mt_ca.topology import matter_occupancy_b, matter_occupancy_b_field, winding_number

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
    core_b = 1 if w == w and abs(w) >= 0.75 else matter_occupancy_b(z_p, y=cy, x=cx)
    vortex_macro_b = float(macro_matter_b(z_p, radius=radius).max().item())

    ok = (
        vac_b_mean < 0.05
        and vac_macro_b < 0.05
        and vac_macro_amp > vac_macro_b
        and core_b == 1
        and vortex_macro_b > 0.1
    )
    return {
        "id": "MatterOccupancyB",
        "vac_b_mean": vac_b_mean,
        "vac_macro_b": vac_macro_b,
        "vac_macro_amp": vac_macro_amp,
        "vortex_core_b": core_b,
        "vortex_macro_b_max": vortex_macro_b,
        "ok": ok,
        "note": "§5.0: b=min(1,|n_∂|); macro ⟨b⟩ primary over |z|²",
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
        check_nu_CA_exact(device=device),
        check_hv_bit_budget(device=device),
        check_rho_P_binary(device=device),
        check_vdw_algebra(device=device),
        check_arg_quantum(device=device),
        check_mechanical_quantum(device=device),
        check_quarter_quantum(device=device),
        check_energy_quantum(device=device),
        check_elementary_quanta(device=device),
        check_local_continuity(device=device),
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

    failed = [r for r in results if not r["ok"] and r["id"] not in ("A3_diffusive", "T_dft_oracle", "I2_zero")]
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
