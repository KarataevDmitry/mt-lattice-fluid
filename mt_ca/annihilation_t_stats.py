"""§5.0.3 · T-statistics readout for 2γ-like dual-front channel.

M: deterministic g; T: binomial coarse readout + rotated ensemble (§2.1).

**Probe path:** head-on Gaussian packets (macro pressure-wave analog, §4.2 T2) —
full vortex-pair annihilation on torus with global winding is **sim-open** (winding NaN on superposition).

**Not PDG Γ/τ:** para-Ps τ≈125 ps needs bound-state scale; lattice clock τ_M=n_ticks·hT is separate.
"""

from __future__ import annotations

import math

import torch

from mt_ca.config import MConfig
from mt_ca.seeds import make_wave_packet
from mt_ca.simulator import LatticeFluidSimulator
from mt_ca.t_validation import coarse_grain, collision_peak_count, covariance_isotropy, isotropy_ratio


def _head_on_packets(
    size: int,
    *,
    angle: float,
    sep: int,
    device: torch.device,
    amplitude: float = 0.42,
    sigma: float = 6.0,
) -> torch.Tensor:
    """Two Gaussians on a line through grid centre (collision axis = angle)."""
    base = make_wave_packet(size, size, device=device, amplitude=amplitude, sigma=sigma)
    ca, sa = math.cos(angle), math.sin(angle)
    oy1 = int(round(sep * sa / 2.0))
    ox1 = int(round(sep * ca / 2.0))
    left = torch.roll(torch.roll(base, shifts=-oy1, dims=0), shifts=-ox1, dims=1)
    right = torch.roll(torch.roll(base, shifts=oy1, dims=0), shifts=ox1, dims=1)
    return left + right


def _dipole_axis_angle(coarse: torch.Tensor) -> float | None:
    """Major axis of amplitude-weighted covariance (T dipole readout)."""
    rho = coarse.detach().float()
    peak = float(rho.max().item())
    if peak <= 1e-9:
        return None
    ny, nx = rho.shape
    ys = torch.arange(ny, device=rho.device, dtype=rho.dtype)
    xs = torch.arange(nx, device=rho.device, dtype=rho.dtype)
    yy, xx = torch.meshgrid(ys, xs, indexing="ij")
    w = rho / peak
    mass = float(w.sum().item())
    if mass <= 1e-9:
        return None
    cy = float((yy * w).sum().item()) / mass
    cx = float((xx * w).sum().item()) / mass
    dy = yy - cy
    dx = xx - cx
    m20 = float((dy * dy * w).sum().item()) / mass
    m02 = float((dx * dx * w).sum().item()) / mass
    m11 = float((dy * dx * w).sum().item()) / mass
    return float(0.5 * math.atan2(2.0 * m11, m20 - m02))


def _angular_flux_cv(coarse: torch.Tensor, *, n_bins: int = 36) -> float:
    rho = coarse.detach().float()
    ny, nx = rho.shape
    cy, cx = ny / 2.0, nx / 2.0
    ys = torch.arange(ny, device=rho.device, dtype=rho.dtype)
    xs = torch.arange(nx, device=rho.device, dtype=rho.dtype)
    yy, xx = torch.meshgrid(ys, xs, indexing="ij")
    theta = torch.atan2(yy - cy, xx - cx)
    bins = torch.floor((theta + math.pi) / (2.0 * math.pi) * n_bins).long().clamp(0, n_bins - 1)
    w = rho.square().reshape(-1)
    flux = torch.bincount(bins.reshape(-1), weights=w, minlength=n_bins).to(rho.dtype)
    mean = float(flux.mean().item())
    if mean <= 1e-18:
        return float("inf")
    return float(flux.std(unbiased=False).item()) / mean


def _run_collision(
    size: int,
    steps: int,
    block: int,
    angle: float,
    sep: int,
    device: torch.device,
) -> dict[str, float | int | None]:
    cfg = MConfig.for_stencil("hex")
    z = _head_on_packets(size, angle=angle, sep=sep, device=device)
    sim = LatticeFluidSimulator(size, size, cfg, device=device)
    k_push = 0.07
    sim.set_field(z, momentum_k=(k_push * math.cos(angle), k_push * math.sin(angle)))
    coarse_before = coarse_grain(sim.z, block).detach().cpu()
    peak_before = collision_peak_count(coarse_before, min_frac=0.3)

    for t in range(1, steps + 1):
        sim.step(1)
        coarse = coarse_grain(sim.z, block).detach().cpu()
        peaks = collision_peak_count(coarse, min_frac=0.28)
        if peaks >= 2 and t >= steps // 4:
            tick_focus = t
            coarse_focus = coarse
            break
    else:
        tick_focus = steps
        coarse_focus = coarse_grain(sim.z, block).detach().cpu()

    delta = (coarse_focus - coarse_before).clamp_min(0.0)
    return {
        "tick_focus": tick_focus,
        "peak_before": peak_before,
        "peaks_late": collision_peak_count(coarse_focus, min_frac=0.28),
        "peaks_on_delta": collision_peak_count(delta, min_frac=0.22),
        "coarse_late": coarse_focus,
        "delta": delta,
        "axis_angle": _dipole_axis_angle(delta),
        "elongation": covariance_isotropy(delta) if float(delta.max()) > 1e-9 else float("inf"),
        "angular_cv": _angular_flux_cv(delta),
        "isotropy_late": isotropy_ratio(coarse_focus),
    }


def annihilation_t_stats_probe(
    *,
    size: int = 192,
    steps: int = 96,
    block: int = 8,
    sep: int | None = None,
    ensemble: int = 12,
    device: str = "cpu",
) -> dict[str, float | int | bool | str | None]:
    """Head-on dual-front T-readout + rotated ensemble (⟨dσ/dΩ⟩ proxy)."""
    dev = torch.device(device)
    sep = sep if sep is not None else max(16, size // 6)

    single = _run_collision(size, steps, block, 0.0, sep, dev)
    axis_angles: list[float] = []
    axis_err: list[float] = []
    for k in range(ensemble):
        ang = 2.0 * math.pi * k / ensemble
        row = _run_collision(size, steps, block, ang, sep, dev)
        a_meas = row["axis_angle"]
        if a_meas is not None:
            axis_angles.append(a_meas)
            # periodic error vs injected axis
            d = (a_meas - ang + math.pi) % (2.0 * math.pi) - math.pi
            axis_err.append(abs(d))

    hist = [0] * 12
    for a in axis_angles:
        hist[int((a + math.pi) / (2.0 * math.pi) * 12) % 12] += 1
    hist_mean = sum(hist) / len(hist) if hist else 0.0
    hist_cv = (
        (sum((h - hist_mean) ** 2 for h in hist) / len(hist)) ** 0.5 / (hist_mean + 1e-12)
        if hist
        else float("inf")
    )
    mean_axis_err = sum(axis_err) / len(axis_err) if axis_err else float("inf")

    from mt_ca.si_constants import SI

    tau_m_s = float(single["tick_focus"]) * SI.hT
    tau_para_ps_PDG = 125.0e-12
    gamma_pdg_hz = SI.hbar / tau_para_ps_PDG

    back_to_back = (
        single["peaks_on_delta"] is not None
        and single["peaks_on_delta"] >= 2
        and single["elongation"] is not None
        and single["elongation"] > 1.25
        and single["elongation"] < float("inf")
    )
    # Injected ensemble is uniform; readout should track axis modulo π (dipole symmetry).
    axis_tracks = mean_axis_err < 0.35 if axis_err else False
    pi_amb = [min(e, abs(e - math.pi)) for e in axis_err]
    mean_pi_err = sum(pi_amb) / len(pi_amb) if pi_amb else float("inf")
    axis_tracks_pi = mean_pi_err < 0.35
    # Flat histogram of measured axes ⇒ ⟨dσ/dΩ⟩ isotropic under random orientation.
    iso_ensemble = hist_cv < 0.75 and len(axis_angles) >= max(4, ensemble // 2)

    ok = back_to_back and axis_tracks_pi and iso_ensemble

    return {
        "probe_path": "head_on_gaussian_T2",
        "tick_focus": single["tick_focus"],
        "tau_M_s": tau_m_s,
        "hT_s": SI.hT,
        "tau_para_Ps_PDG_s": tau_para_ps_PDG,
        "Gamma_para_PDG_Hz": gamma_pdg_hz,
        "tau_M_over_tau_PDG": tau_m_s / tau_para_ps_PDG,
        "peaks_before": single["peak_before"],
        "peaks_late": single["peaks_late"],
        "peaks_on_delta": single["peaks_on_delta"],
        "elongation_delta": single["elongation"] if single["elongation"] == single["elongation"] else None,
        "angular_flux_cv_single": single["angular_cv"] if single["angular_cv"] == single["angular_cv"] else None,
        "isotropy_late": single["isotropy_late"],
        "ensemble_axes": len(axis_angles),
        "ensemble_axis_hist_cv": hist_cv if hist_cv == hist_cv else None,
        "mean_axis_tracking_err_rad": mean_axis_err if mean_axis_err == mean_axis_err else None,
        "mean_axis_pi_err_rad": mean_pi_err if mean_pi_err == mean_pi_err else None,
        "back_to_back_proxy": back_to_back,
        "ensemble_isotropic": iso_ensemble,
        "axis_tracks_injection": axis_tracks,
        "axis_tracks_pi": axis_tracks_pi,
        "ok": ok,
        "note": (
            "T-stats via dual-front sim (T2 analog); vortex e+e- winding on torus sim-open. "
            "τ_M=n_ticks·hT ≠ PDG para-Ps without binding bridge; "
            "⟨dσ/dΩ⟩=σ₀/(4π) via rotated ensemble axis histogram."
        ),
    }
