"""Barrier / slit helpers for §4.9 GPU leaves (T readout probes)."""

from __future__ import annotations

import math

import torch

from mt_ca.config import MConfig
from mt_ca.reversible import evolve_canonical


def make_directed_wave_packet(
    ny: int,
    nx: int,
    *,
    device: torch.device,
    dtype: torch.dtype = torch.complex64,
    amplitude: float = 0.5,
    sigma: float = 5.0,
    kx: float = 0.18,
    cy_frac: float = 0.5,
    cx_frac: float = 0.22,
) -> torch.Tensor:
    """Gaussian packet with plane-wave momentum (propagates +x)."""
    real_dtype = torch.float32 if dtype == torch.complex64 else torch.float64
    ys = torch.arange(ny, device=device, dtype=real_dtype)
    xs = torch.arange(nx, device=device, dtype=real_dtype)
    yy, xx = torch.meshgrid(ys, xs, indexing="ij")
    cy, cx = ny * cy_frac, nx * cx_frac
    env = amplitude * torch.exp(-((yy - cy) ** 2 + (xx - cx) ** 2) / (2.0 * sigma**2))
    wave = torch.exp(1j * kx * xx.to(dtype))
    env = (env.to(dtype) * wave)
    c, s = math.cos(0.12), math.sin(0.12)
    return torch.stack([c * env, s * env], dim=-1)


def barrier_mask(
    ny: int,
    nx: int,
    device: torch.device,
    *,
    x_frac: float = 0.58,
    width: int = 3,
    slit_half_height: int = 14,
) -> torch.Tensor:
    """Vertical hard wall with centered slit (Young-lite geometry)."""
    x0 = int(nx * x_frac)
    xs = torch.arange(nx, device=device)
    col = (xs >= x0) & (xs < x0 + width)
    mask = col.unsqueeze(0).expand(ny, nx).clone()
    cy = ny // 2
    y0 = max(cy - slit_half_height, 0)
    y1 = min(cy + slit_half_height, ny)
    mask[y0:y1, x0 : x0 + width] = False
    return mask


def wall_field(mask: torch.Tensor, cfg: MConfig) -> torch.Tensor:
    """High-density opaque wall state (A7-saturated)."""
    z = torch.zeros(*mask.shape, 2, device=mask.device, dtype=torch.complex64)
    z[..., 0] = cfg.rho_max**0.5
    return z


def micro_steps_with_barrier(
    z: torch.Tensor,
    cfg: MConfig,
    barrier: torch.Tensor,
    steps: int,
) -> torch.Tensor:
    """Evolve with post-step hard wall reset in barrier cells."""
    wall = wall_field(barrier, cfg)
    b = barrier.unsqueeze(-1)
    for _ in range(steps):
        z = evolve_canonical(z, cfg)
        z = torch.where(b, wall, z)
    return z


def screen_slice(
    rho: torch.Tensor,
    *,
    x_frac: float = 0.82,
) -> torch.Tensor:
    """Detector strip on the far side of the lattice."""
    x0 = int(rho.shape[1] * x_frac)
    return rho[:, x0:]
