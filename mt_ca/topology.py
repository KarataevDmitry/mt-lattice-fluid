from __future__ import annotations

import math

import torch

from mt_ca.config import MConfig


def pauli_phi(z: torch.Tensor, cfg: MConfig) -> torch.Tensor:
    """§3.10.4: parallel spinors in one v_p → K_P repulsion via extra gate phase."""
    if not cfg.pauli_exclusion:
        return torch.zeros(z.shape[:-1], device=z.device, dtype=z.real.dtype)

    z1 = z[..., 0]
    z2 = z[..., 1]
    rho1 = z1.abs().square()
    rho2 = z2.abs().square()
    dot = z1.conj() * z2
    cos2 = dot.real.square() + dot.imag.square()
    denom = rho1 * rho2 + 1e-12
    parallel = (cos2 / denom) > cfg.pauli_overlap_cos**2
    dense = (rho1 > cfg.pauli_rho_min) & (rho2 > cfg.pauli_rho_min)
    bad = parallel & dense
    return torch.where(bad, torch.full_like(rho1, cfg.pauli_kick), torch.zeros_like(rho1))


def _contour_min_rho(
    rho: torch.Tensor,
    *,
    cy: int,
    cx: int,
    radius: int,
) -> float:
    y0, y1 = cy - radius, cy + radius
    x0, x1 = cx - radius, cx + radius
    edges = torch.cat(
        [
            rho[y0, x0:x1],
            rho[y0:y1, x1],
            rho[y1, x0 : x1 + 1],
            rho[y0:y1, x0],
        ]
    )
    return float(edges.min().item())


def winding_number(
    z: torch.Tensor,
    *,
    center: tuple[int, int] | None = None,
    radius: int = 24,
) -> float:
    """Discrete ∮ d arg(z₂/z₁) around square contour → integer winding n (A10)."""
    ny, nx = z.shape[0], z.shape[1]
    cy, cx = center if center is not None else (ny // 2, nx // 2)
    r = min(radius, cy - 1, cx - 1, ny - cy - 1, nx - cx - 1)
    if r < 2:
        return float("nan")

    ratio = z[..., 1] / (z[..., 0] + 1e-12)
    phase = torch.angle(ratio)

    def _wrap(d: torch.Tensor) -> torch.Tensor:
        return (d + math.pi) % (2.0 * math.pi) - math.pi

    total = 0.0
    y0, y1 = cy - r, cy + r
    x0, x1 = cx - r, cx + r

    for x in range(x0, x1):
        total += float(_wrap(phase[y0, x + 1] - phase[y0, x]).item())
    for y in range(y0, y1):
        total += float(_wrap(phase[y + 1, x1] - phase[y, x1]).item())
    for x in range(x1, x0, -1):
        total += float(_wrap(phase[y1, x - 1] - phase[y1, x]).item())
    for y in range(y1, y0, -1):
        total += float(_wrap(phase[y - 1, x0] - phase[y, x0]).item())

    return total / (2.0 * math.pi)


def winding_robust(
    z: torch.Tensor,
    *,
    center: tuple[int, int] | None = None,
    min_radius: int = 8,
) -> float:
    """Pick square contour with strong |z|² on loop and nearest-integer winding."""
    from mt_ca.spinor import spinor_density

    rho = spinor_density(z)
    ny, nx = z.shape[0], z.shape[1]
    if center is None:
        cy, cx = torch.unravel_index(rho.argmax(), rho.shape)
        cy, cx = int(cy.item()), int(cx.item())
    else:
        cy, cx = center

    max_r = min(cy - 2, cx - 2, ny - cy - 2, nx - cx - 2)
    if max_r < min_radius:
        return float("nan")

    peak = float(rho.max().item())
    best_w = float("nan")
    best_score = -1.0
    for r in range(min_radius, max_r + 1):
        w = winding_number(z, center=(cy, cx), radius=r)
        if w != w:
            continue
        contour_rho = _contour_min_rho(rho, cy=cy, cx=cx, radius=r)
        if contour_rho < 0.08 * peak:
            continue
        int_dist = abs(w - round(w))
        score = contour_rho / peak - 0.35 * int_dist
        if score > best_score:
            best_score = score
            best_w = w
    return best_w


def winding_nearest_int(n: float) -> int:
    return int(round(n))


def plaquette_winding(
    z: torch.Tensor,
    y: int,
    x: int,
) -> float:
    """Discrete ∮ d arg(z₂/z₁) on ∂(hV) — local n_∂ for cell (y,x) (A10, §5.0)."""
    ny, nx = z.shape[0], z.shape[1]
    if y < 0 or x < 0 or y + 1 >= ny or x + 1 >= nx:
        return float("nan")
    ratio = z[..., 1] / (z[..., 0] + 1e-12)
    phase = torch.angle(ratio)

    def _wrap(d: torch.Tensor) -> torch.Tensor:
        return (d + math.pi) % (2.0 * math.pi) - math.pi

    total = 0.0
    total += float(_wrap(phase[y, x + 1] - phase[y, x]).item())
    total += float(_wrap(phase[y + 1, x + 1] - phase[y, x + 1]).item())
    total += float(_wrap(phase[y + 1, x] - phase[y + 1, x + 1]).item())
    total += float(_wrap(phase[y, x] - phase[y + 1, x]).item())
    return total / (2.0 * math.pi)


def matter_occupancy_b(
    z: torch.Tensor,
    *,
    y: int | None = None,
    x: int | None = None,
) -> int:
    """b(x) = min(1, |n_∂|) at cell — §5.0: ρ_matter = ρ_P·b, m_cell = m_P·b."""
    if y is None or x is None:
        from mt_ca.spinor import spinor_density

        cy, cx = torch.unravel_index(spinor_density(z).argmax(), z.shape[:2])
        y, x = int(cy.item()), int(cx.item())
    n = plaquette_winding(z, y, x)
    if n != n:
        return 0
    return min(1, abs(winding_nearest_int(n)))
