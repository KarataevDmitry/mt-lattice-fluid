from __future__ import annotations

import torch

from mt_ca.cauchy_riemann import cauchy_riemann_residual
from mt_ca.config import MConfig
from mt_ca.laplacian import neighbor_sum
from mt_ca.update import wrapped_phase_diff


def cr_phase_drive(z: torch.Tensor, cfg: MConfig) -> torch.Tensor:
    """§3.9: CR defect magnitude → extra gate phase (restores holomorphy)."""
    if cfg.cr_strength <= 0:
        return torch.zeros(z.shape[:-1], device=z.device, dtype=z.real.dtype)

    drive = torch.zeros(z.shape[0], z.shape[1], device=z.device, dtype=z.real.dtype)
    for comp in (0, 1):
        r1, r2 = cauchy_riemann_residual(z[..., comp])
        drive = drive + torch.sqrt(r1.square() + r2.square())

    return cfg.cr_strength * 0.25 * drive


def holomorphy_sync_step(
    z: torch.Tensor,
    cfg: MConfig,
    *,
    su2_apply,
    defect_axis,
    spinor_neighbor_sum,
) -> torch.Tensor:
    """§3.9: soft pull toward Δ_disc z=0 (neighbor holomorphy) on same Δt."""
    if not cfg.holomorphy_sync or cfg.sync_strength <= 0:
        return z

    sum_n = spinor_neighbor_sum(z, cfg)
    zeta = (sum_n * z.conj()).sum(dim=-1)
    phase_pull = wrapped_phase_diff(zeta, torch.ones_like(zeta))
    phi = cfg.sync_strength * phase_pull
    axis = defect_axis(z, sum_n)
    return su2_apply(z, phi, axis)


def clamp_density(z: torch.Tensor, cfg: MConfig) -> torch.Tensor:
    """A7: hard ceiling |z|² ≤ rho_max (natural units)."""
    rho = z.abs().square().sum(dim=-1)
    scale = torch.where(
        rho > cfg.rho_max,
        torch.sqrt(cfg.rho_max / rho.clamp_min(1e-20)),
        torch.ones_like(rho),
    )
    return z * scale.unsqueeze(-1)
