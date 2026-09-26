"""Finite-difference linearization of leapfrog g on a boil background (Fourier modes)."""
from __future__ import annotations

import math
from typing import Iterable

import torch

from mt_ca.fixed_point import decode_spinor
from mt_ca.reversible import canonical_fixed, leapfrog_forward_fixed


def torus_mode(
    spatial_shape: tuple[int, ...],
    k: tuple[int, ...],
    *,
    device: torch.device,
    dtype: torch.dtype = torch.complex64,
) -> torch.Tensor:
    """Unit-amplitude mode exp(i 2π k·x / L) on spatial grid (no spinor dim)."""
    if len(spatial_shape) != len(k):
        raise ValueError("k must match spatial_shape rank")
    grids = [
        torch.arange(n, device=device, dtype=torch.float64) for n in spatial_shape
    ]
    mesh = torch.meshgrid(*grids, indexing="ij")
    phase = sum(
        (float(ki) * m / float(n) for ki, m, n in zip(k, mesh, spatial_shape, strict=True))
    )
    return torch.exp((2.0j * math.pi * phase).to(dtype))


def leapfrog_pair_decode(
    z_curr: torch.Tensor,
    z_past: torch.Tensor,
    cfg,
) -> tuple[torch.Tensor, torch.Tensor]:
    """One g tick: (z_curr, z_past) → (z_next, z_past_new) through Z_N[i] CA."""
    f_curr = canonical_fixed(z_curr, cfg)
    f_past = canonical_fixed(z_past, cfg)
    f_next, f_prev, _ = leapfrog_forward_fixed(f_curr, f_past, cfg)
    z_next = decode_spinor(f_next, frac_bits=cfg.frac_bits, mod_bits=cfg.mod_bits)
    z_past_new = decode_spinor(f_prev, frac_bits=cfg.frac_bits, mod_bits=cfg.mod_bits)
    return z_next, z_past_new


def project_mode(z: torch.Tensor, mode: torch.Tensor, *, component: int = 0) -> torch.Tensor:
    """Discrete Fourier coefficient of one spinor component against mode."""
    comp = z[..., component]
    num = (comp * mode.conj()).sum()
    den = mode.abs().square().sum().clamp_min(1e-20)
    return num / den


def mode_eigenvalue(
    z_curr: torch.Tensor,
    z_past: torch.Tensor,
    cfg,
    k: tuple[int, ...],
    *,
    eps_quanta: float = 2.0,
    component: int = 0,
) -> dict:
    """One-sided FD estimate of λ for mode k (perturb z_curr, read z_next)."""
    device = z_curr.device
    mode = torus_mode(z_curr.shape[:-1], k, device=device)
    quanta = float(eps_quanta) / float(1 << cfg.frac_bits)
    delta = quanta * mode.to(z_curr.dtype)
    z_pert = z_curr.clone()
    z_pert[..., component] = z_pert[..., component] + delta

    z_next0, _ = leapfrog_pair_decode(z_curr, z_past, cfg)
    z_next1, _ = leapfrog_pair_decode(z_pert, z_past, cfg)

    coeff0 = project_mode(z_next0, mode, component=component)
    coeff1 = project_mode(z_next1, mode, component=component)
    lam = (coeff1 - coeff0) / quanta
    mag = float(lam.abs().item())
    phase = float(torch.angle(lam).item())
    inferred_T: float | None = None
    stable = mag <= 1.05
    if stable and mag > 1e-6 and abs(phase) > 1e-6:
        inferred_T = abs(2.0 * math.pi / phase)
    return {
        "k": k,
        "lambda_re": round(float(lam.real.item()), 6),
        "lambda_im": round(float(lam.imag.item()), 6),
        "abs_lambda": round(mag, 6),
        "log_abs_lambda": round(math.log(mag + 1e-30), 6),
        "phase_rad": round(phase, 6),
        "stable_mode": stable,
        "inferred_T_ticks": round(inferred_T, 3) if inferred_T else None,
        "eps_quanta": eps_quanta,
    }


def scan_low_k_modes(
    z_curr: torch.Tensor,
    z_past: torch.Tensor,
    cfg,
    *,
    max_k: int = 2,
    eps_quanta: float = 2.0,
) -> list[dict]:
    """Scan |k|∞ ≤ max_k on torus (skip k=0)."""
    rank = len(z_curr.shape) - 1
    ks: list[tuple[int, ...]] = []
    ranges = [range(-max_k, max_k + 1)] * rank
    for k_tuple in _product_ranges(ranges):
        if all(ki == 0 for ki in k_tuple):
            continue
        ks.append(k_tuple)
    rows = [mode_eigenvalue(z_curr, z_past, cfg, k, eps_quanta=eps_quanta) for k in ks]
    rows.sort(key=lambda r: r["abs_lambda"], reverse=True)
    return rows


def _product_ranges(ranges: Iterable[Iterable[int]]) -> list[tuple[int, ...]]:
    out: list[tuple[int, ...]] = [()]
    for r in ranges:
        out = [prev + (x,) for prev in out for x in r]
    return out


def ring_period_candidates(cfg) -> list[int]:
    from mt_ca.si_constants import heisenberg_phi_min_disc

    phi_min = heisenberg_phi_min_disc(
        phase_bits=cfg.phase_bits, delta_phi_min=cfg.heisenberg_phi_min
    )
    n_ring = 1 << cfg.phase_bits
    seam = 21
    return [seam, phi_min, 2 * phi_min, n_ring // 2, n_ring]
