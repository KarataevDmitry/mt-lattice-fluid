"""Chiral spinor projectors — SU(2)_L × SU(2)_R packaging on ℂ² (MODEL §3.11)."""

from __future__ import annotations

import math

import torch


def project_left(z: torch.Tensor) -> torch.Tensor:
    """P_L: left component carrier (z₁)."""
    out = torch.zeros_like(z)
    out[..., 0] = z[..., 0]
    return out


def project_right(z: torch.Tensor) -> torch.Tensor:
    """P_R: right component carrier (z₂)."""
    out = torch.zeros_like(z)
    out[..., 1] = z[..., 1]
    return out


def recombine(z_left: torch.Tensor, z_right: torch.Tensor) -> torch.Tensor:
    """z = P_L z + P_R z on disjoint components."""
    return z_left + z_right


def chirality_imbalance(z: torch.Tensor) -> torch.Tensor:
    """|z_L|² − |z_R|² per cell — U(1)_vac invariant."""
    return z[..., 0].abs().square() - z[..., 1].abs().square()


def chirality_norms(z: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
    """Per-cell |z_L|² and |z_R|²."""
    rho_l = z[..., 0].abs().square()
    rho_r = z[..., 1].abs().square()
    return rho_l, rho_r


def chirality_flip_boost(z: torch.Tensor) -> torch.Tensor:
    """T: flip spinor chirality — SU(2) boost U = exp(i·π·σ_x/2) = i·σ_x (§3.11.3)."""
    from mt_ca.spinor import su2_apply

    axis = torch.zeros(*z.shape[:-1], 3, device=z.device, dtype=z.real.dtype)
    axis[..., 0] = 1.0
    phi = torch.full(z.shape[:-1], math.pi, device=z.device, dtype=z.real.dtype)
    return su2_apply(z, phi, axis)


def chirality_flip_sign(z: torch.Tensor) -> torch.Tensor:
    """Check helper: T negates |z_L|²−|z_R|² where defined."""
    return chirality_flip_boost(z)
