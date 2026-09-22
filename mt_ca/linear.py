from __future__ import annotations

import math

import torch

from mt_ca.laplacian import neighbor_laplacian


def _bond_unitary(
    a: torch.Tensor, b: torch.Tensor, theta: float
) -> tuple[torch.Tensor, torch.Tensor]:
    """2×2 unitary mixing on one N₄ link: preserves |a|²+|b|²."""
    c = math.cos(theta)
    s = math.sin(theta)
    a_new = c * a + 1j * s * b
    b_new = 1j * s * a + c * b
    return a_new, b_new


def _horizontal_bonds(z: torch.Tensor, theta: float, offset: int) -> torch.Tensor:
    if offset == 0:
        a = z[:, 0::2]
        b = z[:, 1::2]
        a_new, b_new = _bond_unitary(a, b, theta)
        out = z.clone()
        out[:, 0::2] = a_new
        out[:, 1::2] = b_new
        return out

    a = z[:, 1::2]
    b = torch.cat([z[:, 2::2], z[:, :1]], dim=1)
    a_new, b_new = _bond_unitary(a, b, theta)
    out = z.clone()
    out[:, 1::2] = a_new
    out[:, 2::2] = b_new[:, :-1]
    out[:, :1] = b_new[:, -1:]
    return out


def _vertical_bonds(z: torch.Tensor, theta: float, offset: int) -> torch.Tensor:
    if offset == 0:
        a = z[0::2, :]
        b = z[1::2, :]
        a_new, b_new = _bond_unitary(a, b, theta)
        out = z.clone()
        out[0::2, :] = a_new
        out[1::2, :] = b_new
        return out

    a = z[1::2, :]
    b = torch.cat([z[2::2, :], z[:1, :]], dim=0)
    a_new, b_new = _bond_unitary(a, b, theta)
    out = z.clone()
    out[1::2, :] = a_new
    out[2::2, :] = b_new[:-1, :]
    out[:1, :] = b_new[-1:, :]
    return out


def linear_step_local_ca(z: torch.Tensor, gamma: float) -> torch.Tensor:
    """Local unitary CA step on N₄: four bond-color sweeps (A2 + A3).

    Product of 2×2 unitaries on disjoint links; one macro-tick = one hT.
    θ = γ/4 per sub-sweep → O(γ) mixing akin to exp(i·γ·Δ₄) at small γ.
    """
    theta = gamma / 4.0
    z = _horizontal_bonds(z, theta, offset=0)
    z = _horizontal_bonds(z, theta, offset=1)
    z = _vertical_bonds(z, theta, offset=0)
    z = _vertical_bonds(z, theta, offset=1)
    return z


def linear_step_diffusive(z: torch.Tensor, gamma: float, *, stencil: str = "n4") -> torch.Tensor:
    """z+γ·Δ z — не унитарна; конфликт A3 vs A6 (MODEL §3.6)."""
    return z + gamma * neighbor_laplacian(z, stencil)


def linear_step(z: torch.Tensor, gamma: float, mode: str, *, stencil: str = "n4") -> torch.Tensor:
    if mode == "isotropic":
        return z
    if mode == "local_ca":
        return linear_step_local_ca(z, gamma)
    if mode == "diffusive":
        return linear_step_diffusive(z, gamma, stencil=stencil)
    raise ValueError(f"Unknown linear_mode: {mode!r}. Use 'isotropic', 'local_ca', or 'diffusive'.")
