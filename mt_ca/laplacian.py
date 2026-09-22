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


# FCC / cuboctahedron 1-tick shell (§1.6.2): 12 face-diagonal offsets on ℤ³.
_FCC_OFFSETS: tuple[tuple[int, int, int], ...] = (
    (1, 1, 0),
    (1, -1, 0),
    (-1, 1, 0),
    (-1, -1, 0),
    (1, 0, 1),
    (1, 0, -1),
    (-1, 0, 1),
    (-1, 0, -1),
    (0, 1, 1),
    (0, 1, -1),
    (0, -1, 1),
    (0, -1, -1),
)


def fcc_neighbor_sum(z: torch.Tensor) -> torch.Tensor:
    """Σ_{N₁₂} on 3D torus — cuboctahedral ε, |N|=12 (§1.6)."""
    if z.ndim < 3:
        raise ValueError("fcc stencil needs spatial rank ≥3 (nz, ny, nx)")
    # spatial dims = last three before optional batch; we treat (-3,-2,-1) as z,y,x
    acc = torch.zeros_like(z)
    for dz, dy, dx in _FCC_OFFSETS:
        acc = acc + torch.roll(torch.roll(torch.roll(z, shifts=dz, dims=-3), shifts=dy, dims=-2), shifts=dx, dims=-1)
    return acc


def fcc_neighbor_mean(z: torch.Tensor) -> torch.Tensor:
    return fcc_neighbor_sum(z) / 12.0


def fcc_laplacian(z: torch.Tensor) -> torch.Tensor:
    return fcc_neighbor_sum(z) - 12.0 * z


def neighbor_sum(z: torch.Tensor, stencil: str) -> torch.Tensor:
    if stencil == "n4":
        return von_neumann_neighbor_sum(z)
    if stencil == "hex":
        return hex_neighbor_sum(z)
    if stencil == "fcc":
        return fcc_neighbor_sum(z)
    raise ValueError(f"Unknown stencil: {stencil!r}. Use 'n4', 'hex', or 'fcc'.")


def neighbor_laplacian(z: torch.Tensor, stencil: str) -> torch.Tensor:
    if stencil == "n4":
        return von_neumann_laplacian(z)
    if stencil == "hex":
        return hex_laplacian(z)
    if stencil == "fcc":
        return fcc_laplacian(z)
    raise ValueError(f"Unknown stencil: {stencil!r}. Use 'n4', 'hex', or 'fcc'.")


def stencil_n_links(stencil: str) -> int:
    if stencil == "n4":
        return 4
    if stencil == "hex":
        return 6
    if stencil == "fcc":
        return 12
    raise ValueError(f"Unknown stencil: {stencil!r}")
