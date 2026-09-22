"""T-layer self-validation: M→T invariants without external benchmarks."""

from __future__ import annotations

import torch

from mt_ca.macro import macro_amplitude
from mt_ca.metrics import coarse_amplitude, ring_anisotropy


def coarse_grain(
    z: torch.Tensor,
    block: int,
    *,
    radius: int | None = None,
    nu_viscosity_passes: int = 0,
) -> torch.Tensor:
    """Binomial (1-2-1) macro readout |Φ| — MODEL §4.1.1 (stride = block, R ≈ block)."""
    if block <= 1:
        return coarse_amplitude(z, max(block, 1))
    r = radius if radius is not None else block
    return macro_amplitude(
        z,
        radius=r,
        stride=block,
        nu_viscosity_passes=nu_viscosity_passes,
    )


def nu_readout_passes(steps: int, block: int) -> int:
    """Extra binomial passes on T readout — ν_CA coarse-graining loss (§4.1.2)."""
    from mt_ca.si_constants import nu_CA_natural

    return max(0, int(round(2.0 * steps * nu_CA_natural() / max(block, 1))))
def macro_mass(
    z: torch.Tensor,
    block: int,
    *,
    foam_quantile: float = 0.5,
    nu_viscosity_passes: int = 0,
) -> float:
    """Integrated macro amplitude Σ|Φ−Φ_foam|² — ν_CA coherent mass (§4.1.2, §5.0.1)."""
    coarse = coarse_grain(z, block, nu_viscosity_passes=nu_viscosity_passes)
    floor = float(torch.quantile(coarse.reshape(-1), foam_quantile).item())
    signal = (coarse - floor).clamp_min(0.0)
    return float(signal.square().sum().item())


def covariance_isotropy(rho: torch.Tensor, *, threshold: float = 0.08) -> float:
    """λ_max/λ_min of amplitude-weighted covariance (1.0 = perfect circle)."""
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


def isotropy_ratio(rho: torch.Tensor, center: tuple[float, float] | None = None) -> float:
    """Primary T isotropy score — blend ring + covariance (→1 isotropic)."""
    ring = ring_anisotropy(rho, center=center)
    cov = covariance_isotropy(rho)
    scores = [x for x in (ring, cov) if x == x and x < float("inf")]
    if not scores:
        return float("inf")
    return float(min(scores))


def radial_front_radii(
    rho: torch.Tensor,
    *,
    center: tuple[float, float] | None = None,
    threshold: float = 0.15,
    n_angles: int = 72,
) -> torch.Tensor:
    """For each angle, radius where rho drops below threshold * peak (T front probe)."""
    ny, nx = rho.shape
    if center is None:
        cy, cx = ny / 2.0, nx / 2.0
    else:
        cy, cx = center

    peak = float(rho.max().item())
    if peak <= 1e-12:
        return torch.full((n_angles,), float("nan"), device=rho.device, dtype=rho.dtype)

    level = threshold * peak
    ys = torch.arange(ny, device=rho.device, dtype=rho.dtype)
    xs = torch.arange(nx, device=rho.device, dtype=rho.dtype)
    yy, xx = torch.meshgrid(ys, xs, indexing="ij")
    dy = yy - cy
    dx = xx - cx

    angles = torch.linspace(0, 2 * torch.pi, n_angles + 1, device=rho.device)[:-1]
    radii: list[float] = []
    max_r = int(min(cy, cx, ny - cy, nx - cx) - 1)

    for theta in angles:
        cos_t = torch.cos(theta)
        sin_t = torch.sin(theta)
        proj = dy * sin_t + dx * cos_t
        along = proj >= 0
        r_found = float("nan")
        for r in range(1, max_r):
            mask = along & (proj >= r - 0.5) & (proj < r + 0.5)
            if mask.any() and float(rho[mask].mean().item()) < level:
                r_found = float(r)
                break
        radii.append(r_found)

    return torch.tensor(radii, device=rho.device, dtype=rho.dtype)


def radial_speed_uniformity(rho_t0: torch.Tensor, rho_t1: torch.Tensor, *, dt_steps: int = 1) -> float:
    """Coefficient of variation of radial front speeds over angles (lower = more isotropic c)."""
    r0 = radial_front_radii(rho_t0)
    r1 = radial_front_radii(rho_t1)
    valid = torch.isfinite(r0) & torch.isfinite(r1) & (r1 > r0)
    if not valid.any():
        return float("inf")
    speeds = (r1[valid] - r0[valid]) / dt_steps
    mean = float(speeds.mean().item())
    if mean <= 1e-12:
        return float("inf")
    std = float(speeds.std(unbiased=False).item())
    return std / mean


def profile_correlation(a: torch.Tensor, b: torch.Tensor) -> float:
    """Pearson correlation between flattened real profiles (soliton shape stability)."""
    ar = a.reshape(-1).float()
    br = b.reshape(-1).float()
    ar = ar - ar.mean()
    br = br - br.mean()
    denom = ar.norm() * br.norm()
    if float(denom) <= 1e-12:
        return 0.0
    return float((ar * br).sum().item() / denom)


def soliton_peak_track(rho: torch.Tensor) -> tuple[float, float]:
    """Peak location on coarse map."""
    flat_idx = int(rho.argmax().item())
    ny, nx = rho.shape
    py, px = divmod(flat_idx, nx)
    return float(py), float(px)


def collision_peak_count(rho: torch.Tensor, *, min_frac: float = 0.35) -> int:
    """Count distinct peaks above min_frac * global max (post-collision structure)."""
    peak = float(rho.max().item())
    if peak <= 1e-12:
        return 0
    level = min_frac * peak
    mask = rho >= level
    if not mask.any():
        return 0

    visited = torch.zeros_like(rho, dtype=torch.bool)
    ny, nx = rho.shape
    count = 0
    for i in range(ny):
        for j in range(nx):
            if not mask[i, j] or visited[i, j]:
                continue
            count += 1
            stack = [(i, j)]
            while stack:
                y, x = stack.pop()
                if y < 0 or y >= ny or x < 0 or x >= nx:
                    continue
                if visited[y, x] or not mask[y, x]:
                    continue
                visited[y, x] = True
                stack.extend([(y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)])
    return count


def wave_particle_readout(
    size: int = 512,
    steps: int = 256,
    block: int = 8,
    device: str | torch.device = "cpu",
) -> dict[str, float | int | bool | str]:
    """§4.9: dual-Gaussian interference (wave) vs vortex localization (particle) on same g."""
    from mt_ca.config import MConfig
    from mt_ca.seeds import SeedClass, make_wave_packet
    from mt_ca.simulator import LatticeFluidSimulator

    dev = torch.device(device)
    cfg = MConfig.for_stencil("hex")
    sep = size // 6

    left = make_wave_packet(size, size, device=dev, amplitude=0.45, sigma=6.0)
    right = make_wave_packet(size, size, device=dev, amplitude=0.45, sigma=6.0)
    left = torch.roll(left, shifts=-sep, dims=1)
    right = torch.roll(right, shifts=sep, dims=1)
    z_wave = left + right

    sim_w = LatticeFluidSimulator(size, size, cfg, device=dev)
    sim_w.set_field(z_wave, momentum_k=(0.06, 0.0))
    sim_w.step(steps)
    coarse_w = coarse_grain(sim_w.z, block).detach().cpu()
    wave_peaks = collision_peak_count(coarse_w)
    wave_mass = macro_mass(sim_w.z, block)
    wave_peak = float(coarse_w.max().item())

    sim_v = LatticeFluidSimulator(size, size, cfg, device=dev)
    sim_v.reset(SeedClass.VORTEX_P)
    sim_v.step(steps)
    coarse_v = coarse_grain(sim_v.z, block).detach().cpu()
    vortex_peaks = collision_peak_count(coarse_v)
    vortex_mass = macro_mass(sim_v.z, block)
    vortex_peak = float(coarse_v.max().item())

    ok = (
        wave_peaks >= 2
        and vortex_peaks >= 1
        and vortex_mass > max(wave_mass * 5.0, 0.05)
        and vortex_peak > max(wave_peak * 1.5, 0.08)
    )
    return {
        "wave_peaks": wave_peaks,
        "wave_macro_mass": wave_mass,
        "wave_peak": wave_peak,
        "vortex_peaks": vortex_peaks,
        "vortex_macro_mass": vortex_mass,
        "vortex_peak": vortex_peak,
        "mass_ratio_v_over_w": vortex_mass / (wave_mass + 1e-12),
        "steps": steps,
        "ok": ok,
    }
