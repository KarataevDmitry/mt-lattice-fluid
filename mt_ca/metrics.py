from __future__ import annotations

import torch


def total_norm_squared(z: torch.Tensor) -> float:
    return float(z.abs().square().sum().item())


def norm_drift(initial: float, current: float) -> float:
    if initial == 0.0:
        return float("inf") if current != 0.0 else 0.0
    return abs(current - initial) / initial


def field_amplitude(z: torch.Tensor) -> torch.Tensor:
    """√(|z₁|² + |z₂|²) per cell."""
    return z.abs().square().sum(dim=-1).sqrt()


def coarse_amplitude(z: torch.Tensor, block: int) -> torch.Tensor:
    amp = field_amplitude(z)
    ny, nx = amp.shape
    by, bx = ny // block, nx // block
    trimmed = amp[: by * block, : bx * block]
    blocks = trimmed.reshape(by, block, bx, block)
    return blocks.mean(dim=(1, 3))


def ring_anisotropy(rho: torch.Tensor, center: tuple[float, float] | None = None) -> float:
    """Radial shell falloff ratio (max/min mean over radii) — not angular contour."""
    ny, nx = rho.shape
    if center is None:
        cy, cx = ny / 2.0, nx / 2.0
    else:
        cy, cx = center

    ys = torch.arange(ny, device=rho.device, dtype=rho.dtype)
    xs = torch.arange(nx, device=rho.device, dtype=rho.dtype)
    yy, xx = torch.meshgrid(ys, xs, indexing="ij")
    rr = torch.sqrt((yy - cy) ** 2 + (xx - cx) ** 2)

    peak = float(rho.max().item())
    if peak <= 1e-12:
        return float("inf")

    max_r = int(min(cy, cx, ny - cy, nx - cx) - 1)
    if max_r < 2:
        return 1.0

    means: list[float] = []
    for r in range(2, max_r):
        mask = (rr >= r - 0.5) & (rr < r + 0.5)
        if not mask.any():
            continue
        m = float(rho[mask].mean().item())
        if m >= peak * 0.02:
            means.append(m)

    if len(means) < 2:
        return float("inf")

    lo = min(means)
    hi = max(means)
    if lo <= 1e-12:
        return float("inf")
    return hi / lo


def contour_axis_ratio(rho: torch.Tensor, *, threshold: float = 0.5) -> float:
    """Vortex contour λ_max/λ_min at ρ ≥ threshold·peak (§3.7.3). 1.0 = circle."""
    peak = float(rho.max().item())
    if peak <= 1e-12:
        return float("inf")

    mask = rho >= threshold * peak
    if int(mask.sum()) < 16:
        return float("inf")

    ys = torch.arange(rho.shape[0], device=rho.device, dtype=rho.dtype)
    xs = torch.arange(rho.shape[1], device=rho.device, dtype=rho.dtype)
    yy, xx = torch.meshgrid(ys, xs, indexing="ij")
    w = rho * mask
    mass = float(w.sum().item())
    cy = float((yy * w).sum().item()) / mass
    cx = float((xx * w).sum().item()) / mass
    dy = yy - cy
    dx = xx - cx
    m20 = float((dy * dy * w).sum().item()) / mass
    m02 = float((dx * dx * w).sum().item()) / mass
    m11 = float((dy * dx * w).sum().item()) / mass
    trace = m20 + m02
    det = m20 * m02 - m11 * m11
    disc = max(trace * trace / 4.0 - det, 0.0)
    root = disc**0.5
    lam_max = trace / 2.0 + root
    lam_min = trace / 2.0 - root
    if lam_min <= 1e-12:
        return float("inf")
    return lam_max / lam_min


def contour_radius_anisotropy(
    rho: torch.Tensor,
    *,
    threshold: float = 0.5,
    n_bins: int = 64,
) -> float:
    """max r(θ)/min r(θ) on isodensity contour (§3.8 Fourier r(θ) readout)."""
    peak = float(rho.max().item())
    if peak <= 1e-12:
        return float("inf")

    mask = rho >= threshold * peak
    if int(mask.sum()) < 16:
        return float("inf")

    ys = torch.arange(rho.shape[0], device=rho.device, dtype=rho.dtype)
    xs = torch.arange(rho.shape[1], device=rho.device, dtype=rho.dtype)
    yy, xx = torch.meshgrid(ys, xs, indexing="ij")
    w = rho * mask
    mass = float(w.sum().item())
    cy = float((yy * w).sum().item()) / mass
    cx = float((xx * w).sum().item()) / mass
    dy = yy[mask] - cy
    dx = xx[mask] - cx
    theta = torch.atan2(dy, dx)
    rr = torch.sqrt(dy * dy + dx * dx)

    bins = torch.linspace(-torch.pi, torch.pi, n_bins + 1, device=rho.device, dtype=rho.dtype)
    means: list[float] = []
    for i in range(n_bins):
        lo, hi = bins[i], bins[i + 1]
        if i < n_bins - 1:
            m = (theta >= lo) & (theta < hi)
        else:
            m = (theta >= lo) | (theta < bins[0])
        if not m.any():
            continue
        means.append(float(rr[m].mean().item()))

    if len(means) < 4:
        return float("inf")
    lo = min(means)
    hi = max(means)
    if lo <= 1e-12:
        return float("inf")
    return hi / lo


def has_nan(z: torch.Tensor) -> bool:
    return bool(torch.isnan(z.real).any().item() or torch.isnan(z.imag).any().item())
