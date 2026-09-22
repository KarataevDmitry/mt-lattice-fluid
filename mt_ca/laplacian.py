from __future__ import annotations

import torch


def von_neumann_laplacian(z: torch.Tensor) -> torch.Tensor:
    """Δ₄ on torus: Σ_{N₄}(z(y)−z(x))."""
    return von_neumann_neighbor_sum(z) - 4.0 * z


def von_neumann_neighbor_mean(z: torch.Tensor) -> torch.Tensor:
    return von_neumann_neighbor_sum(z) * 0.25


def von_neumann_neighbor_sum(z: torch.Tensor) -> torch.Tensor:
    up = torch.roll(z, shifts=-1, dims=0)
    down = torch.roll(z, shifts=1, dims=0)
    left = torch.roll(z, shifts=1, dims=1)
    right = torch.roll(z, shifts=-1, dims=1)
    return up + down + left + right


def _parity_mask(ny: int, nx: int, device: torch.device) -> torch.Tensor:
    ys = torch.arange(ny, device=device)
    xs = torch.arange(nx, device=device)
    yy, xx = torch.meshgrid(ys, xs, indexing="ij")
    return ((yy + xx) % 2) == 0


def hex_neighbor_sum(z: torch.Tensor) -> torch.Tensor:
    """6-neighbor honeycomb stencil on ℤ² torus (§3.8 ladder step 1)."""
    up = torch.roll(z, shifts=-1, dims=0)
    down = torch.roll(z, shifts=1, dims=0)
    left = torch.roll(z, shifts=1, dims=1)
    right = torch.roll(z, shifts=-1, dims=1)
    diag_pp = torch.roll(torch.roll(z, shifts=-1, dims=0), shifts=-1, dims=1)
    diag_mm = torch.roll(torch.roll(z, shifts=1, dims=0), shifts=1, dims=1)
    diag_pm = torch.roll(torch.roll(z, shifts=-1, dims=0), shifts=1, dims=1)
    diag_mp = torch.roll(torch.roll(z, shifts=1, dims=0), shifts=-1, dims=1)

    card = up + down + left + right
    sum_even = card + diag_pp + diag_mm
    sum_odd = card + diag_pm + diag_mp

    ny, nx = z.shape[-2], z.shape[-1]
    even = _parity_mask(ny, nx, z.device)
    return torch.where(even, sum_even, sum_odd)


def hex_neighbor_mean(z: torch.Tensor) -> torch.Tensor:
    return hex_neighbor_sum(z) / 6.0


def hex_laplacian(z: torch.Tensor) -> torch.Tensor:
    return hex_neighbor_sum(z) - 6.0 * z


def neighbor_sum(z: torch.Tensor, stencil: str) -> torch.Tensor:
    if stencil == "n4":
        return von_neumann_neighbor_sum(z)
    if stencil == "hex":
        return hex_neighbor_sum(z)
    raise ValueError(f"Unknown stencil: {stencil!r}. Use 'n4' or 'hex'.")


def neighbor_laplacian(z: torch.Tensor, stencil: str) -> torch.Tensor:
    if stencil == "n4":
        return von_neumann_laplacian(z)
    if stencil == "hex":
        return hex_laplacian(z)
    raise ValueError(f"Unknown stencil: {stencil!r}. Use 'n4' or 'hex'.")
