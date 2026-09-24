"""verify_checks.axioms — extracted from verify_principles"""
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

def check_a3_global_norm(size: int = 64, device: str = "cpu") -> dict:
    from mt_ca.conservation import a3_global_norm_report

    return a3_global_norm_report(size, device=device)

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

