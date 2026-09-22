from __future__ import annotations

import torch


def forward_derivatives(z: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
    """Forward differences on torus: ∂x along dim=1, ∂y along dim=0."""
    u = z.real
    v = z.imag
    du_dx = torch.roll(u, shifts=-1, dims=1) - u
    du_dy = torch.roll(u, shifts=-1, dims=0) - u
    dv_dx = torch.roll(v, shifts=-1, dims=1) - v
    dv_dy = torch.roll(v, shifts=-1, dims=0) - v
    return du_dx, du_dy, dv_dx, dv_dy


def cauchy_riemann_residual(z: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
    """Discrete CR: ∂x u = ∂y v and ∂y u = -∂x v."""
    du_dx, du_dy, dv_dx, dv_dy = forward_derivatives(z)
    r1 = du_dx - dv_dy
    r2 = du_dy + dv_dx
    return r1, r2


def cauchy_riemann_energy(z: torch.Tensor) -> float:
    r1, r2 = cauchy_riemann_residual(z)
    return float((r1.square() + r2.square()).mean().item())


def cr_stationarity_tolerance(*, energy: float) -> float:
    """Allowed |ΔE_CR| between two late windows: {B_hV}·E (§3.9.6)."""
    from mt_ca.si_constants import bekenshtein_fractional_part

    return bekenshtein_fractional_part() * energy
