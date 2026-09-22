"""M-layer local conservation probes — §5.2.1 (bond N₄, SO(2) on canonical g)."""

from __future__ import annotations

import torch

from mt_ca.config import MConfig
from mt_ca.fixed_point import decode_spinor
from mt_ca.linear import _horizontal_bonds, linear_step_local_ca
from mt_ca.reversible import canonical_fixed, leapfrog_forward_fixed
from mt_ca.seeds import SeedClass, make_seed


def spinor_scalar(z: torch.Tensor) -> torch.Tensor:
    if z.ndim == 3 and z.shape[-1] == 2:
        return z[..., 0]
    return z


def rotate_c4(z: torch.Tensor) -> torch.Tensor:
    return torch.rot90(z, k=1, dims=(0, 1))


def bond_pair_mass_conservation(
    z: torch.Tensor,
    *,
    theta: float = 0.0625,
) -> float:
    """One horizontal bond-color sweep: |a|²+|b|² invariant on every pair."""
    u = spinor_scalar(z)
    before = u[:, 0::2].abs().square() + u[:, 1::2].abs().square()
    after_u = spinor_scalar(_horizontal_bonds(u, theta, offset=0))
    after = after_u[:, 0::2].abs().square() + after_u[:, 1::2].abs().square()
    denom = before.abs().max().clamp_min(1e-12)
    return float(((after - before).abs().max() / denom).item())


def local_ca_continuity_max(z: torch.Tensor, *, gamma: float = 0.25) -> float:
    """After one local_ca step, max |Δρ + div_disc j| / max ρ (§5.2.1 flux)."""
    u = spinor_scalar(z)
    rho = u.abs().square()
    u_next = linear_step_local_ca(u, gamma)
    rho_n = u_next.abs().square()
    jx = (u.conj() * torch.roll(u, -1, 1)).imag
    jy = (u.conj() * torch.roll(u, -1, 0)).imag
    div_j = jx - torch.roll(jx, 1, 1) + jy - torch.roll(jy, 1, 0)
    residual = (rho_n - rho + div_j).abs()
    return float((residual.max() / rho.max().clamp_min(1e-12)).item())


def so2_c4_equivariance_fixed_error(
    z: torch.Tensor,
    z_past: torch.Tensor,
    cfg: MConfig,
) -> int:
    """g(R·Ψ)=R·g(Ψ) on canonical leapfrog+projected — compare in Z_N[i], not float."""
    f_curr = canonical_fixed(z, cfg)
    f_past = canonical_fixed(z_past, cfg)
    f_rot = canonical_fixed(rotate_c4(z), cfg)
    f_past_rot = canonical_fixed(rotate_c4(z_past), cfg)

    f_next, _, _ = leapfrog_forward_fixed(f_curr, f_past, cfg)
    f_next_rot, _, _ = leapfrog_forward_fixed(f_rot, f_past_rot, cfg)
    f_next_via_rot = canonical_fixed(rotate_c4(decode_spinor(f_next)), cfg)
    return int((f_next_rot - f_next_via_rot).abs().max().item())


def local_conservation_report(
    size: int = 64,
    *,
    device: str = "cpu",
) -> dict:
    dev = torch.device(device)
    z = make_seed(SeedClass.PLANE_WAVE, size, size, device=dev, impulse_amplitude=0.12)
    pair_err = bond_pair_mass_conservation(z)
    cont_err = local_ca_continuity_max(z)
    ok = pair_err < 1e-5 and cont_err < 0.05
    return {
        "id": "LocalContinuity",
        "bond_pair_max_rel": pair_err,
        "local_ca_div_j_max_rel": cont_err,
        "ok": ok,
        "note": "§5.2.1: bond |a|²+|b|² exact; local_ca div j residual",
    }


def so2_c4_report(
    size: int = 64,
    *,
    device: str = "cpu",
) -> dict:
    dev = torch.device(device)
    cfg = MConfig()
    z = make_seed(SeedClass.PLANE_WAVE, size, size, device=dev, impulse_amplitude=0.12)
    z_past = z.clone()
    err = so2_c4_equivariance_fixed_error(z, z_past, cfg)
    ok = err == 0
    return {
        "id": "SO2_C4",
        "fixed_int_max_err": err,
        "evolution": cfg.evolution,
        "projected_collision": cfg.use_projected_collision,
        "ok": ok,
        "note": "§5.2.1 · §3.12: leapfrog+projected on Z_N[i]",
    }
