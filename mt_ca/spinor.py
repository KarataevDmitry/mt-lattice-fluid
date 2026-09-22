"""M-layer SU(2) spinor field — gate formulas; evolution is reversible.evolve_canonical (§3.12)."""

from __future__ import annotations

import torch

from mt_ca.config import MConfig
from mt_ca.holomorphy import cr_phase_drive, holomorphy_sync_step
from mt_ca.laplacian import neighbor_sum
from mt_ca.topology import pauli_phi
from mt_ca.update import apply_heisenberg_floor, macro_suppression, wrapped_phase_diff


def spinor_density(z: torch.Tensor) -> torch.Tensor:
    return z.abs().square().sum(dim=-1)


def spinor_neighbor_sum(z: torch.Tensor, cfg: MConfig) -> torch.Tensor:
    s0 = neighbor_sum(z[..., 0], cfg.stencil)
    s1 = neighbor_sum(z[..., 1], cfg.stencil)
    return torch.stack([s0, s1], dim=-1)


def holonomy_zeta(z: torch.Tensor, sum_n: torch.Tensor) -> torch.Tensor:
    return (sum_n * z.conj()).sum(dim=-1)


def arg_phase_defect(z: torch.Tensor, cfg: MConfig, *, apply_floor: bool = False) -> torch.Tensor:
    """M carrier Δφ = Arg(⟨z⟩·z*) wrapped to (−π, π] (MODEL §3.4.1, §5.0.1)."""
    sum_n = spinor_neighbor_sum(z, cfg)
    zeta = holonomy_zeta(z, sum_n)
    phase_diff = wrapped_phase_diff(zeta, torch.ones_like(zeta))
    if apply_floor:
        phase_diff = apply_heisenberg_floor(phase_diff, cfg)
    return phase_diff


def bloch_vector(z: torch.Tensor, *, eps: float = 1e-12) -> torch.Tensor:
    z1 = z[..., 0]
    z2 = z[..., 1]
    nx = 2.0 * (z1.conj() * z2).real
    ny = 2.0 * (z1.conj() * z2).imag
    nz = z1.abs().square() - z2.abs().square()
    n = torch.stack([nx, ny, nz], dim=-1)
    return n / n.norm(dim=-1, keepdim=True).clamp_min(eps)


def defect_axis(z: torch.Tensor, sum_n: torch.Tensor, *, eps: float = 1e-12, cross_eps: float = 1e-4) -> torch.Tensor:
    """SU(2) rotation axis from Bloch vectors — U(1)_vac invariant (§3.11)."""
    n_z = bloch_vector(z, eps=eps)
    n_s = bloch_vector(sum_n, eps=eps)
    cross = torch.cross(n_z, n_s, dim=-1)
    norm = cross.norm(dim=-1, keepdim=True)
    # Tiny cross → numerically unstable axis; fallback to local Bloch (U(1)-invariant).
    axis = cross / norm.clamp_min(eps)
    use_fallback = norm.squeeze(-1) < cross_eps
    return torch.where(use_fallback.unsqueeze(-1), n_z, axis)


def su2_apply(z: torch.Tensor, phi: torch.Tensor, axis: torch.Tensor) -> torch.Tensor:
    c = torch.cos(phi / 2.0).unsqueeze(-1)
    s = torch.sin(phi / 2.0).unsqueeze(-1)
    nx = axis[..., 0:1]
    ny = axis[..., 1:2]
    nz = axis[..., 2:3]
    z1 = z[..., 0:1]
    z2 = z[..., 1:2]

    u00 = c + 1j * s * nz
    u01 = 1j * s * (nx - 1j * ny)
    u10 = 1j * s * (nx + 1j * ny)
    u11 = c - 1j * s * nz

    out1 = u00 * z1 + u01 * z2
    out2 = u10 * z1 + u11 * z2
    return torch.cat([out1, out2], dim=-1)


def gate_phase(z: torch.Tensor, cfg: MConfig) -> torch.Tensor:
    rho = spinor_density(z)
    phase_diff = arg_phase_defect(z, cfg, apply_floor=True)
    phi_base = cfg.phase_scale * (cfg.alpha_factor / (rho + cfg.epsilon) * phase_diff - 1.0)
    phi = phi_base * macro_suppression(rho, cfg)
    phi = phi + cr_phase_drive(z, cfg) + pauli_phi(z, cfg)
    return phi


def apply_gate_collision(z: torch.Tensor, cfg: MConfig) -> torch.Tensor:
    """One collision map on ℂ² (gate formula probe — not a tick of g; §3.12.5 is Z_N[i])."""
    phi = gate_phase(z, cfg)
    sum_n = spinor_neighbor_sum(z, cfg)
    axis = defect_axis(z, sum_n)
    z = su2_apply(z, phi, axis)
    return holomorphy_sync_step(
        z,
        cfg,
        su2_apply=su2_apply,
        defect_axis=defect_axis,
        spinor_neighbor_sum=spinor_neighbor_sum,
    )
