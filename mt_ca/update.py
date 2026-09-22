from __future__ import annotations

import torch

from mt_ca.config import MConfig


def macro_suppression(rho: torch.Tensor, cfg: MConfig) -> torch.Tensor:
    """A8: w→1 at vacuum scale, w→0 at macro |z|² ≫ ρ_macro."""
    if not cfg.macro_weight:
        return torch.ones_like(rho)
    ratio = rho / cfg.macro_rho
    return 1.0 / (1.0 + ratio * ratio)


def vacuum_phase(rho: torch.Tensor, cfg: MConfig) -> torch.Tensor:
    """A5 + A7 vacuum gate; A8 via macro_suppression."""
    phi_base = cfg.phase_scale * (cfg.alpha_factor / (rho + cfg.epsilon) - 1.0)
    return phi_base * macro_suppression(rho, cfg)


def apply_heisenberg_floor(phase_diff: torch.Tensor, cfg: MConfig) -> torch.Tensor:
    """§3.7.2: |Δφ| < heisenberg_phi_min → ±floor (zeros → +floor)."""
    if not cfg.heisenberg_floor:
        return phase_diff
    m = cfg.heisenberg_phi_min
    ad = phase_diff.abs()
    sign = torch.sign(phase_diff)
    sign = torch.where(sign == 0, torch.ones_like(sign), sign)
    return torch.where(ad < m, sign * m, phase_diff)


def wrapped_phase_diff(a: torch.Tensor, b: torch.Tensor, *, eps: float = 1e-20) -> torch.Tensor:
    """arg(a)−arg(b) in (−π, π] via ζ = a·b*."""
    out = torch.zeros_like(a.real if a.is_complex() else a)
    mask = b.abs() > eps
    zeta = a[mask] * b[mask].conj()
    phase = torch.atan2(zeta.imag, zeta.real)
    out[mask] = (phase + torch.pi) % (2.0 * torch.pi) - torch.pi
    return out
