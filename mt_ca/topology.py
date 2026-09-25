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


def _wrap_pi(d: torch.Tensor) -> torch.Tensor:
    return (d + math.pi) % (2.0 * math.pi) - math.pi


def _square_contour_winding(phase: torch.Tensor, *, cy: int, cx: int, radius: int) -> float:
    """∮ dφ / 2π on a square contour in a precomputed phase field."""
    ny, nx = phase.shape
    r = min(radius, cy - 1, cx - 1, ny - cy - 1, nx - cx - 1)
    if r < 2:
        return float("nan")
    total = 0.0
    y0, y1 = cy - r, cy + r
    x0, x1 = cx - r, cx + r
    for x in range(x0, x1):
        total += float(_wrap_pi(phase[y0, x + 1] - phase[y0, x]).item())
    for y in range(y0, y1):
        total += float(_wrap_pi(phase[y + 1, x1] - phase[y, x1]).item())
    for x in range(x1, x0, -1):
        total += float(_wrap_pi(phase[y1, x - 1] - phase[y1, x]).item())
    for y in range(y1, y0, -1):
        total += float(_wrap_pi(phase[y - 1, x0] - phase[y, x0]).item())
    return total / (2.0 * math.pi)


def phase_field_rel(z: torch.Tensor) -> torch.Tensor:
    """Relative spinor phase Arg(z₂/z₁) — SU(2) / fermionic channel (§5.0)."""
    return torch.angle(z[..., 1] / (z[..., 0] + 1e-12))


def gate_plane_z(z: torch.Tensor, iz: int) -> torch.Tensor:
    """2D (ny,nx,2) slice for A10 contour readout in 3+1 (winding in a plane)."""
    if z.ndim == 3:
        return z
    return z[iz]


def unravel_peak_index(rho: torch.Tensor, flat_idx: int) -> tuple[int | None, int, int]:
    """Map flat density index → (iz?, iy, ix). iz is None in 2+1."""
    if rho.ndim == 2:
        _, nx = rho.shape
        iy = flat_idx // nx
        ix = flat_idx % nx
        return None, iy, ix
    _, ny, nx = rho.shape
    iz = flat_idx // (ny * nx)
    rem = flat_idx % (ny * nx)
    iy = rem // nx
    ix = rem % nx
    return iz, iy, ix


def phase_field_u1(z: torch.Tensor) -> torch.Tensor:
    """U(1) ocean phase Arg(z₁+z₂) — sees locked equal-lane boil (§5.0 · A10).

    When z₁≡z₂ (VACUUM_BOIL), Arg(z₂/z₁)≡0 and the old thermometer was blind.
    Coherent sum keeps the common ocean Arg; when lanes differ it tracks bulk U(1).
    """
    return torch.angle(z[..., 0] + z[..., 1])


def winding_number(
    z: torch.Tensor,
    *,
    center: tuple[int, int] | None = None,
    radius: int = 24,
    channel: str = "auto",
) -> float:
    """Discrete ∮ d arg / 2π around square contour → winding n (A10 · §5.0).

    Channels:
      rel  — Arg(z₂/z₁) (planted VORTEX_* / relative topo)
      u1   — Arg(z₁+z₂) (ocean / locked equal lanes)
      auto — pick channel with larger |n| (thermometer not blind to boil)
    """
    ny, nx = z.shape[0], z.shape[1]
    cy, cx = center if center is not None else (ny // 2, nx // 2)

    def _one(ch: str) -> float:
        if ch == "rel":
            phase = phase_field_rel(z)
        elif ch == "u1":
            phase = phase_field_u1(z)
        else:
            raise ValueError(f"channel must be rel|u1|auto, got {ch!r}")
        return _square_contour_winding(phase, cy=cy, cx=cx, radius=radius)

    if channel == "auto":
        w_rel = _one("rel")
        w_u1 = _one("u1")
        if w_rel != w_rel and w_u1 != w_u1:
            return float("nan")
        if w_rel != w_rel:
            return w_u1
        if w_u1 != w_u1:
            return w_rel
        return w_rel if abs(w_rel) >= abs(w_u1) else w_u1
    return _one(channel)


def winding_channels(
    z: torch.Tensor,
    *,
    center: tuple[int, int] | None = None,
    radius: int = 24,
) -> dict[str, float]:
    """Both A10 readouts + auto pick — for probes / seed seeker diagnostics."""
    w_rel = winding_number(z, center=center, radius=radius, channel="rel")
    w_u1 = winding_number(z, center=center, radius=radius, channel="u1")
    w_auto = winding_number(z, center=center, radius=radius, channel="auto")
    return {"rel": w_rel, "u1": w_u1, "auto": w_auto}


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
    *,
    channel: str = "auto",
) -> float:
    """Discrete ∮ d arg on ∂(hV) — local n_∂ for cell (y,x) (A10, §5.0)."""
    ny, nx = z.shape[0], z.shape[1]
    if y < 0 or x < 0 or y + 1 >= ny or x + 1 >= nx:
        return float("nan")

    def _one(ch: str) -> float:
        if ch == "rel":
            phase = phase_field_rel(z)
        elif ch == "u1":
            phase = phase_field_u1(z)
        else:
            raise ValueError(f"channel must be rel|u1|auto, got {ch!r}")
        total = 0.0
        total += float(_wrap_pi(phase[y, x + 1] - phase[y, x]).item())
        total += float(_wrap_pi(phase[y + 1, x + 1] - phase[y, x + 1]).item())
        total += float(_wrap_pi(phase[y + 1, x] - phase[y + 1, x + 1]).item())
        total += float(_wrap_pi(phase[y, x] - phase[y + 1, x]).item())
        return total / (2.0 * math.pi)

    if channel == "auto":
        w_rel = _one("rel")
        w_u1 = _one("u1")
        return w_rel if abs(w_rel) >= abs(w_u1) else w_u1
    return _one(channel)


def matter_occupancy_b(
    z: torch.Tensor,
    *,
    y: int | None = None,
    x: int | None = None,
    rho_frac: float = 0.25,
    contour_radius: int = 2,
) -> int:
    """b(x) = min(1, |n_∂|) at cell — §5.0: ρ_matter = ρ_P·b, m_cell = m_P·b."""
    from mt_ca.config import MConfig
    from mt_ca.spinor import spinor_density

    rho = spinor_density(z)
    if y is None or x is None:
        flat_idx = int(rho.reshape(-1).argmax().item())
        iz, y, x = unravel_peak_index(rho, flat_idx)
        if iz is not None:
            z = gate_plane_z(z, iz)
            rho_peak = float(rho[iz, y, x].item())
        else:
            rho_peak = float(rho[y, x].item())
    else:
        rho_peak = float(rho[y, x].item()) if rho.ndim == 2 else float(rho[:, y, x].max().item())

    if rho_peak < rho_frac * MConfig.for_stencil("hex").rho_max:
        return 0

    w = winding_number(z, center=(y, x), radius=contour_radius)
    if w != w or abs(w) < 0.75:
        return 0
    return min(1, abs(winding_nearest_int(w)))


def matter_occupancy_b_field(
    z: torch.Tensor,
    *,
    rho_min: float | None = None,
    rho_frac: float = 0.25,
    contour_radius: int = 2,
) -> torch.Tensor:
    """b(x) ∈ {0,1} — primary matter readout; needs ρ ≥ ρ_frac·ρ_P and |n_∂|≥¾ (§5.2.3)."""
    from mt_ca.spinor import spinor_density

    cfg = MConfig.for_stencil("hex")
    q = rho_frac * cfg.rho_max if rho_min is None else rho_min
    rho = spinor_density(z)
    ny, nx = rho.shape
    b = torch.zeros(ny, nx, dtype=torch.int64, device=z.device)
    candidates = (rho >= q).nonzero(as_tuple=False)
    margin = contour_radius + 1
    for idx in candidates:
        y, x = int(idx[0].item()), int(idx[1].item())
        if y < margin or x < margin or y >= ny - margin or x >= nx - margin:
            continue
        w = winding_number(z, center=(y, x), radius=contour_radius)
        if w == w and abs(w) >= 0.75:
            b[y, x] = min(1, abs(winding_nearest_int(w)))
    return b
