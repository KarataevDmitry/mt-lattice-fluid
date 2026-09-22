"""§8.4.2-C′/C′′′ — strain readout h_00 from ρ-edges; saturation-core probe."""

from __future__ import annotations

import math

import torch

from mt_ca.fixed_point import vacuum_amplitude_quantum
from mt_ca.spinor import spinor_density


def edge_rho_n4(rho: torch.Tensor) -> dict[str, torch.Tensor]:
    """ρ_e = ½(ρ(x)+ρ(y)) on N₄ bonds (MVP stencil)."""
    rho_r = 0.5 * (rho + torch.roll(rho, shifts=-1, dims=1))
    rho_l = 0.5 * (rho + torch.roll(rho, shifts=1, dims=1))
    rho_d = 0.5 * (rho + torch.roll(rho, shifts=-1, dims=0))
    rho_u = 0.5 * (rho + torch.roll(rho, shifts=1, dims=0))
    return {"e": rho_r, "w": rho_l, "s": rho_d, "n": rho_u}


def epsilon_from_rho_e(rho_e: torch.Tensor, rho_vac: float) -> torch.Tensor:
    return (rho_e - rho_vac) / max(rho_vac, 1e-30)


def h00_from_eps_n4(eps_edges: dict[str, torch.Tensor]) -> torch.Tensor:
    """h_00 = −(2/|N|) Σ ε_e, |N|=4 on MVP."""
    n = 4.0
    s = eps_edges["e"] + eps_edges["w"] + eps_edges["s"] + eps_edges["n"]
    return -(2.0 / n) * s


def strain_h00(z: torch.Tensor, *, rho_vac: float | None = None) -> torch.Tensor:
    if rho_vac is None:
        a = vacuum_amplitude_quantum()
        rho_vac = float(a * a)
    rho = spinor_density(z)
    edges = edge_rho_n4(rho)
    eps = {k: epsilon_from_rho_e(v, rho_vac) for k, v in edges.items()}
    return h00_from_eps_n4(eps)


def shell_mean(field: torch.Tensor, *, cy: float, cx: float, r: float, half: float = 0.5) -> float:
    ny, nx = field.shape
    ys = torch.arange(ny, device=field.device, dtype=field.dtype)
    xs = torch.arange(nx, device=field.device, dtype=field.dtype)
    yy, xx = torch.meshgrid(ys, xs, indexing="ij")
    rr = torch.sqrt((yy - cy) ** 2 + (xx - cx) ** 2)
    mask = (rr >= r - half) & (rr < r + half)
    if not bool(mask.any().item()):
        return float("nan")
    return float(field[mask].mean().item())


def make_saturation_core(
    ny: int,
    nx: int,
    *,
    device: torch.device,
    rho_star: float = 1.0,
    dtype: torch.dtype = torch.complex64,
) -> torch.Tensor:
    """D_★ = one cell at ρ=ρ_★; elsewhere A5 vacuum amplitude (§8.4.2-C′′′)."""
    amp = vacuum_amplitude_quantum()
    real_dtype = torch.float32 if dtype == torch.complex64 else torch.float64
    re = amp * torch.ones(ny, nx, device=device, dtype=real_dtype)
    im = torch.zeros(ny, nx, device=device, dtype=real_dtype)
    z1 = torch.complex(re, im).to(dtype)
    z2 = torch.zeros(ny, nx, device=device, dtype=dtype)
    z = torch.stack([z1, z2], dim=-1)
    cy, cx = ny // 2, nx // 2
    # |z1|² = ρ_★, z2=0 → density ρ_★
    core = math.sqrt(rho_star)
    z[cy, cx, 0] = core + 0j
    z[cy, cx, 1] = 0j
    return z


def saturation_core_probe(
    size: int = 64,
    *,
    device: str = "cpu",
    rho_star: float = 1.0,
    m_over_m_P: float = 1.0,
) -> dict[str, float]:
    """Live C′′′ hinge: h_near from D_★ vs Newton −2m/(m_P R_★)."""
    dev = torch.device(device)
    z = make_saturation_core(size, size, device=dev, rho_star=rho_star)
    a = vacuum_amplitude_quantum()
    rho_vac = float(a * a)
    h = strain_h00(z, rho_vac=rho_vac)
    cy = cx = size / 2.0
    iy, ix = size // 2, size // 2
    h_near = float(h[iy, ix].item())
    r_star = 1.0
    h_newton = -2.0 * m_over_m_P / r_star
    mismatch = abs(h_near / h_newton) if h_newton != 0.0 else float("inf")

    # far shells: compare strain h_00(R) to Newton −2/R
    far_rows: list[dict[str, float]] = []
    for r in (2, 4, 8, 12):
        if r >= size // 2 - 1:
            continue
        hs = shell_mean(h, cy=cy, cx=cx, r=float(r))
        hn = -2.0 * m_over_m_P / float(r)
        far_rows.append(
            {
                "R": float(r),
                "h_strain": hs,
                "h_newton": hn,
                "ratio": abs(hs / hn) if hn != 0.0 and not math.isnan(hs) else float("nan"),
            }
        )

    return {
        "rho_star": rho_star,
        "rho_vac": rho_vac,
        "h_star_near": h_near,
        "h_star_newton": h_newton,
        "near_over_newton": mismatch,
        "far_R2_ratio": far_rows[0]["ratio"] if far_rows else float("nan"),
        "far_R8_ratio": next((r["ratio"] for r in far_rows if r["R"] == 8.0), float("nan")),
        "n_far_shells": float(len(far_rows)),
    }
