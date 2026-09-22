#!/usr/bin/env python3
"""M→T self-validation: symmetry invariants, no external benchmarks."""

from __future__ import annotations

import argparse
import json
import sys

import torch

from mt_ca.config import MConfig
from mt_ca.metrics import field_amplitude
from mt_ca.seeds import SeedClass, make_seed, make_wave_packet
from mt_ca.simulator import LatticeFluidSimulator
from mt_ca.t_validation import (
    coarse_grain,
    collision_peak_count,
    isotropy_ratio,
    macro_mass,
    profile_correlation,
    radial_speed_uniformity,
    soliton_peak_track,
    wave_particle_readout,
)


def test_isotropy(
    size: int = 512,
    steps: int = 256,
    block: int = 8,
    device: str = "cpu",
) -> dict:
    """T1: localized packet → coarse front should approach a circle (Lorentz on macro)."""
    sim = LatticeFluidSimulator(size, size, MConfig(), device=device)
    z0 = make_wave_packet(size, size, device=torch.device(device), amplitude=0.55, sigma=5.0)
    sim.set_field(z0)
    coarse_0 = coarse_grain(sim.z, block)

    sim.step(steps)
    rho_micro = field_amplitude(sim.z)
    coarse = coarse_grain(sim.z, block)

    micro_ani = isotropy_ratio(rho_micro)
    macro_ani = isotropy_ratio(coarse)
    speed_cv = radial_speed_uniformity(coarse_0, coarse, dt_steps=steps)

    ok = (
        micro_ani <= 1.05
        and float(coarse.max()) > 0.02
        and (
            micro_ani <= 1.01
            or (
                macro_ani == macro_ani
                and macro_ani < 1.2
                and macro_ani <= micro_ani
            )
        )
        and (speed_cv == speed_cv and speed_cv < 0.4 or speed_cv == float("inf"))
    )
    return {
        "id": "T1_isotropy",
        "micro_anisotropy": round(micro_ani, 4),
        "macro_anisotropy": round(macro_ani, 4),
        "radial_speed_cv": speed_cv if speed_cv == speed_cv else None,
        "block": block,
        "steps": steps,
        "ok": ok,
        "criterion": "macro front circle: anisotropy→1, c uniform in θ",
    }


def test_soliton(
    size: int = 512,
    steps: int = 128,
    block: int = 8,
    device: str = "cpu",
) -> dict:
    """T2: localized packet keeps coarse profile on boiling vacuum."""
    sim = LatticeFluidSimulator(size, size, MConfig(), device=device)
    sim.reset(SeedClass.PLANE_WAVE)
    profile_0 = coarse_grain(sim.z, block).detach().cpu()
    mass_0 = macro_mass(sim.z, block)

    sim.step(steps // 2)
    mid = coarse_grain(sim.z, block).detach().cpu()
    sim.step(steps // 2)
    profile_1 = coarse_grain(sim.z, block).detach().cpu()

    corr_mid = profile_correlation(profile_0, mid)
    corr_late = profile_correlation(profile_0, profile_1)
    amp_max_0 = float(profile_0.max())
    amp_max_1 = float(profile_1.max())
    amp_ratio = amp_max_1 / (amp_max_0 + 1e-12)
    mass_late = macro_mass(sim.z, block)
    mass_ratio = mass_late / (mass_0 + 1e-12)

    # ν_CA: peak drops; integrated macro mass bleeds into vacuum foam (§4.1.2).
    ok = corr_late > 0.3 and amp_ratio > 0.08 and mass_ratio < 0.99
    return {
        "id": "T2_soliton",
        "profile_corr_mid": round(corr_mid, 4),
        "profile_corr_late": round(corr_late, 4),
        "amp_ratio": round(amp_ratio, 4),
        "macro_mass_ratio": round(mass_ratio, 4),
        "ok": ok,
        "criterion": "profile survives ν_CA damping (§4.1.2); not dead noise",
    }


def test_collision(
    size: int = 512,
    steps: int = 192,
    block: int = 8,
    device: str = "cpu",
) -> dict:
    """T2b: two wave packets interfere, not pixel mush."""
    dev = torch.device(device)
    z = torch.zeros(size, size, 2, device=dev, dtype=torch.complex64)
    cy, cx = size // 2, size // 2
    sep = size // 6
    z[cy, cx - sep, 0] = 0.45 + 0j
    z[cy, cx + sep, 0] = 0.45 + 0j

    sim = LatticeFluidSimulator(size, size, MConfig(), device=device)
    sim.set_field(z)
    coarse_0 = coarse_grain(sim.z, block).cpu()
    peaks_0 = collision_peak_count(coarse_0)
    micro_amp_0 = float(field_amplitude(sim.z).max())

    sim.step(steps)
    coarse = coarse_grain(sim.z, block).cpu()
    peaks_late = collision_peak_count(coarse)
    micro_amp_late = float(field_amplitude(sim.z).max())
    coarse_amp_ratio = float(coarse.max()) / (float(coarse_0.max()) + 1e-12)

    structured = 1 <= peaks_late <= 4
    ok = structured and peaks_0 >= 2
    return {
        "id": "T2_collision",
        "peaks_initial": peaks_0,
        "peaks_late": peaks_late,
        "micro_amp_ratio": round(micro_amp_late / (micro_amp_0 + 1e-12), 4),
        "coarse_amp_ratio": round(coarse_amp_ratio, 4),
        "ok": ok,
        "criterion": "interference structure on coarse; corpuscular identity: §3.7.1 MODEL",
    }


def test_gaussian_collision(
    size: int = 512,
    steps: int = 256,
    block: int = 8,
    device: str = "cpu",
) -> dict:
    """§3.7.3: two Gaussian packets head-on — coarse amp ratio DoD."""
    dev = torch.device(device)
    cy, cx = size // 2, size // 2
    sep = size // 6
    left = make_wave_packet(size, size, device=dev, amplitude=0.45, sigma=6.0)
    right = make_wave_packet(size, size, device=dev, amplitude=0.45, sigma=6.0)
    right = torch.roll(right, shifts=sep, dims=2)
    left = torch.roll(left, shifts=-sep, dims=2)
    z = left + right

    sim = LatticeFluidSimulator(size, size, MConfig(), device=device)
    sim.set_field(z)
    coarse_0 = coarse_grain(sim.z, block).cpu()
    amp0 = float(coarse_0.max())
    mass0 = macro_mass(sim.z, block)

    sim.step(steps)
    coarse = coarse_grain(sim.z, block).cpu()
    ratio = float(coarse.max()) / (amp0 + 1e-12)
    mass_ratio = macro_mass(sim.z, block) / (mass0 + 1e-12)
    peaks = collision_peak_count(coarse)

    ok = ratio >= 0.08 and mass_ratio < 0.99 and 1 <= peaks <= 4
    return {
        "id": "T2_gaussian",
        "coarse_amp_ratio": round(ratio, 4),
        "macro_mass_ratio": round(mass_ratio, 4),
        "peaks_late": peaks,
        "ok": ok,
        "criterion": "Gaussian head-on: structure + ν_CA-tolerant amp (§4.1.2)",
    }


def test_macro_viscosity(
    size: int = 512,
    steps: int = 384,
    block: int = 8,
    device: str = "cpu",
) -> dict:
    """§4.1.2: macro Φ decays (ν_CA) while micro norm stays unitary."""
    from mt_ca.metrics import norm_drift, total_norm_squared
    from mt_ca.si_constants import SI

    dev = torch.device(device)
    z0 = make_wave_packet(size, size, device=dev, amplitude=0.55, sigma=5.0)
    sim = LatticeFluidSimulator(size, size, MConfig(), device=device)
    sim.set_field(z0)
    norm0 = total_norm_squared(sim.z)
    peak0 = float(coarse_grain(sim.z, block).max().item())
    mass0 = macro_mass(sim.z, block)

    sim.step(steps)
    norm_d = norm_drift(norm0, total_norm_squared(sim.z))
    peak1 = float(coarse_grain(sim.z, block).max().item())
    mass1 = macro_mass(sim.z, block)
    peak_ratio = peak1 / (peak0 + 1e-12)
    mass_ratio = mass1 / (mass0 + 1e-12)

    ok = (
        norm_d < 1e-3
        and 0.03 < peak_ratio < 0.95
        and mass_ratio < 0.99
    )
    return {
        "id": "T3_macro_viscosity",
        "micro_norm_drift": norm_d,
        "macro_peak_ratio": round(peak_ratio, 4),
        "macro_mass_ratio": round(mass_ratio, 4),
        "nu_CA_SI_m2_s": SI.nu_CA,
        "ok": ok,
        "criterion": "A3 micro stable; macro Φ damps into vacuum foam (§4.1.2)",
    }


def test_zigzag_mass(
    size: int = 256,
    steps: int = 64,
    block: int = 8,
    device: str = "cpu",
) -> dict:
    """§5.0.1: vortex Arg-activity + macro m_rest exceed dilute vacuum (mass from zigzag)."""
    from mt_ca.m_to_t import arg_mass_load, m_rest_readout

    cfg = MConfig()

    sim_v = LatticeFluidSimulator(size, size, cfg, device=device)
    sim_v.reset(SeedClass.VORTEX_P)
    sim_v.step(steps)
    load_v = arg_mass_load(sim_v.z, cfg)
    m_v = m_rest_readout(sim_v.z, block)

    sim_vac = LatticeFluidSimulator(size, size, cfg, device=device)
    sim_vac.reset(SeedClass.VACUUM)
    sim_vac.step(steps)
    load_vac = arg_mass_load(sim_vac.z, cfg)
    m_vac = m_rest_readout(sim_vac.z, block)

    ratio_load = load_v / (load_vac + 1e-12)
    ratio_m = m_v / (m_vac + 1e-12)
    ok = ratio_load > 50.0 and ratio_m > 5.0 and load_v > 1.0 and m_v > m_vac
    return {
        "id": "T_zigzag_mass",
        "vortex_arg_load": round(load_v, 4),
        "vacuum_arg_load": round(load_vac, 4),
        "arg_load_ratio": round(ratio_load, 4),
        "vortex_m_rest": round(m_v, 4),
        "vacuum_m_rest": round(m_vac, 4),
        "m_rest_ratio": round(ratio_m, 4),
        "steps": steps,
        "ok": ok,
        "criterion": "vortex: Σ|Δφ|·ρ and m_rest ≫ vacuum foam (§5.0.1)",
    }


def test_wave_particle(
    size: int = 512,
    steps: int = 256,
    block: int = 8,
    device: str = "cpu",
) -> dict:
    """§4.9: wave interference vs vortex localization on same CA (no duality paradox)."""
    row = wave_particle_readout(size, steps, block, device)
    ok = bool(row["ok"])
    return {
        "id": "T_wave_particle",
        "wave_peaks": row["wave_peaks"],
        "wave_macro_mass": round(float(row["wave_macro_mass"]), 6),
        "wave_peak": round(float(row["wave_peak"]), 4),
        "vortex_peaks": row["vortex_peaks"],
        "vortex_macro_mass": round(float(row["vortex_macro_mass"]), 4),
        "vortex_peak": round(float(row["vortex_peak"]), 4),
        "mass_ratio_v_over_w": round(float(row["mass_ratio_v_over_w"]), 2),
        "steps": steps,
        "ok": ok,
        "criterion": "§4.9: interference (wave) vs K_P-localized soliton (particle) — same g",
    }


def test_dispersion(size: int = 128, steps: int = 64, device: str = "cpu") -> dict:
    """§4.6: plane-wave phase advance vs γ (T readout)."""
    from mt_ca.t_analysis import estimate_phase_velocity_plane_wave

    sim = LatticeFluidSimulator(size, size, MConfig(), device=device)
    sim.reset(SeedClass.PLANE_WAVE)
    z0 = sim.z[..., 0].clone()
    sim.step(steps)
    z1 = sim.z[..., 0]
    omega = estimate_phase_velocity_plane_wave(z0, z1, kx=0.12, ky=0.08)
    ok = omega == omega and abs(omega) > 1e-6
    return {
        "id": "T_dispersion",
        "phase_advance": omega if omega == omega else None,
        "steps": steps,
        "ok": ok,
        "criterion": "non-zero phase advance on plane-wave seed (T diagnostic)",
    }


def run_all(device: str, size: int, steps: int, block: int) -> list[dict]:
    return [
        test_isotropy(size, steps, block, device),
        test_soliton(size, steps, block, device),
        test_collision(size, steps, block, device),
        test_gaussian_collision(size, steps, block, device),
        test_macro_viscosity(size, steps, block, device),
        test_zigzag_mass(size, steps // 2, block, device),
        test_wave_particle(size, steps, block, device),
        test_dispersion(min(size, 128), steps // 4, device),
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description="M→T symmetry self-validation")
    parser.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    parser.add_argument("--size", type=int, default=512)
    parser.add_argument("--steps", type=int, default=256)
    parser.add_argument("--block", type=int, default=8)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    results = run_all(args.device, args.size, args.steps, args.block)
    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print(f"device={args.device} size={args.size} steps={args.steps} block={args.block}")
        print("Self-validation: no external benchmarks — symmetry invariants only.")
        print("-" * 68)
        for row in results:
            status = "PASS" if row["ok"] else "FAIL"
            extra = {k: v for k, v in row.items() if k not in ("id", "ok", "criterion")}
            print(f"{row['id']:18}  {status}  {extra}")
            print(f"                     {row['criterion']}")

    failed = [r for r in results if not r["ok"]]
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
