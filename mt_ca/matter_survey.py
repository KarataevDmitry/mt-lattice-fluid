"""Planckon matter survey instrument (§5.0 · A10).

Separates:
  - **site** — where we point the contour loop (iz?, y, x)
  - **survey** — find candidate sites from ρ (local maxima, torus-safe)
  - **anchor** — fixed site (planted core, tracker COM) independent of global ρ max

Winding is always measured on a 2D plane: xy slice at iz (3+1) or the field itself (2+1).
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any

import torch

from mt_ca.config import MConfig
from mt_ca.spinor import spinor_density
from mt_ca.topology import (
    gate_plane_z,
    unravel_peak_index,
    winding_channels,
    winding_nearest_int,
)


def plane_mconfig(z_plane: torch.Tensor, cfg: MConfig) -> MConfig:
    """Gate-plane contour uses 2D hex neighbors even in 3+1 FCC (A10)."""
    if z_plane.ndim == 3 and cfg.stencil != "hex":
        return replace(cfg, stencil="hex")
    return cfg


@dataclass(frozen=True, slots=True)
class MatterSite:
    """Survey target on the torus."""

    iz: int | None
    y: int
    x: int


@dataclass(frozen=True, slots=True)
class SiteSurvey:
    site: MatterSite
    rho: float
    b: int
    winding_rel: float
    winding_u1: float
    winding_auto: float
    contour_radius: int
    rho_floor_ok: bool
    torus_safe: bool
    local_max: bool


def spatial_shape(z: torch.Tensor) -> tuple[int | None, int, int]:
    if z.ndim == 3:
        ny, nx = z.shape[0], z.shape[1]
        return None, ny, nx
    if z.ndim == 4:
        nz, ny, nx = z.shape[0], z.shape[1], z.shape[2]
        return nz, ny, nx
    raise ValueError(f"spinor field must be (ny,nx,2) or (nz,ny,nx,2), got {tuple(z.shape)}")


def density_shape(rho: torch.Tensor) -> tuple[int | None, int, int]:
    if rho.ndim == 2:
        ny, nx = rho.shape
        return None, ny, nx
    if rho.ndim == 3:
        return rho.shape[0], rho.shape[1], rho.shape[2]
    raise ValueError(f"density must be (ny,nx) or (nz,ny,nx), got {tuple(rho.shape)}")


def rho_at(rho: torch.Tensor, site: MatterSite) -> float:
    if site.iz is None:
        return float(rho[site.y, site.x].item())
    return float(rho[site.iz, site.y, site.x].item())


def snap_column_peak(rho: torch.Tensor, y: int, x: int, *, iz_hint: int | None = None) -> MatterSite:
    """For a line defect along z: pick iz with maximal ρ at fixed (y, x)."""
    if rho.ndim == 2:
        return MatterSite(None, y, x)
    col = rho[:, y, x]
    iz = int(col.argmax().item())
    if iz_hint is not None and float(col[iz_hint].item()) >= 0.85 * float(col[iz].item()):
        iz = iz_hint
    return MatterSite(iz, y, x)


def torus_site_safe(site: MatterSite, nz: int | None, ny: int, nx: int, margin: int) -> bool:
    if site.y < margin or site.x < margin or site.y >= ny - margin or site.x >= nx - margin:
        return False
    if nz is not None and site.iz is not None:
        if site.iz < margin or site.iz >= nz - margin:
            return False
    return True


def is_local_density_max(rho: torch.Tensor, site: MatterSite, *, shell: int = 1) -> bool:
    """Strict ρ maximum in a (2·shell+1)³ (or ² in 2D) torus neighborhood."""
    nz, ny, nx = density_shape(rho)
    center = rho_at(rho, site)
    for dz in range(-shell, shell + 1):
        for dy in range(-shell, shell + 1):
            for dx in range(-shell, shell + 1):
                if dz == 0 and dy == 0 and dx == 0:
                    continue
                if nz is None:
                    yy = (site.y + dy) % ny
                    xx = (site.x + dx) % nx
                    if float(rho[yy, xx].item()) > center:
                        return False
                else:
                    assert site.iz is not None
                    zz = (site.iz + dz) % nz
                    yy = (site.y + dy) % ny
                    xx = (site.x + dx) % nx
                    if float(rho[zz, yy, xx].item()) > center:
                        return False
    return True


def spinor_plane(z: torch.Tensor, site: MatterSite) -> torch.Tensor:
    if site.iz is None:
        return z
    return gate_plane_z(z, site.iz)


def b_from_winding(w: float) -> int:
    if w != w or abs(w) < 0.75:
        return 0
    return min(1, abs(winding_nearest_int(w)))


def survey_at_site(
    z: torch.Tensor,
    site: MatterSite,
    *,
    contour_radius: int = 2,
    rho_frac: float = 0.25,
    cfg: MConfig | None = None,
) -> SiteSurvey:
    """Single-site densitometer: ρ gate + dual-channel contour winding → b."""
    cfg = cfg or MConfig.for_stencil("fcc" if z.ndim == 4 else "hex")
    rho = spinor_density(z)
    nz, ny, nx = spatial_shape(z)
    margin = contour_radius + 1
    safe = torus_site_safe(site, nz, ny, nx, margin)
    local = is_local_density_max(rho, site, shell=1)
    rho_val = rho_at(rho, site)
    rho_ok = rho_val >= rho_frac * cfg.rho_max
    z_plane = spinor_plane(z, site)
    ch = winding_channels(z_plane, center=(site.y, site.x), radius=contour_radius)
    w_auto = float(ch["auto"])
    b = b_from_winding(w_auto) if rho_ok else 0
    return SiteSurvey(
        site=site,
        rho=rho_val,
        b=b,
        winding_rel=float(ch["rel"]),
        winding_u1=float(ch["u1"]),
        winding_auto=w_auto,
        contour_radius=contour_radius,
        rho_floor_ok=rho_ok,
        torus_safe=safe,
        local_max=local,
    )


def survey_density_sites(
    rho: torch.Tensor,
    *,
    top_k: int = 8,
    margin: int = 3,
    require_local_max: bool = True,
) -> list[MatterSite]:
    """Candidate sites from global ρ ranking, with column snap and torus margin."""
    nz, ny, nx = density_shape(rho)
    flat = rho.reshape(-1)
    k = min(top_k, flat.numel())
    _, idx = torch.topk(flat, k)
    sites: list[MatterSite] = []
    seen: set[tuple[int | None, int, int]] = set()
    for i in range(k):
        iz, y, x = unravel_peak_index(rho, int(idx[i].item()))
        site = snap_column_peak(rho, y, x, iz_hint=iz)
        if not torus_site_safe(site, nz, ny, nx, margin):
            continue
        if require_local_max and not is_local_density_max(rho, site, shell=1):
            continue
        key = (site.iz, site.y, site.x)
        if key in seen:
            continue
        seen.add(key)
        sites.append(site)
    return sites


def planckon_instrument(
    z: torch.Tensor,
    *,
    anchor: MatterSite | None = None,
    top_k: int = 8,
    contour_radius: int = 2,
    rho_frac: float = 0.25,
    survey_margin: int | None = None,
    require_local_max: bool = True,
    cfg: MConfig | None = None,
) -> dict[str, Any]:
    """Full instrument: anchor readout + ρ survey (denisitometer modes)."""
    cfg = cfg or MConfig.for_stencil("fcc" if z.ndim == 4 else "hex")
    rho = spinor_density(z)
    margin = survey_margin if survey_margin is not None else contour_radius + 1

    anchor_row: SiteSurvey | None = None
    if anchor is not None:
        anchor_row = survey_at_site(
            z, anchor, contour_radius=contour_radius, rho_frac=rho_frac, cfg=cfg
        )

    survey_rows: list[SiteSurvey] = []
    for site in survey_density_sites(
        rho, top_k=top_k, margin=margin, require_local_max=require_local_max
    ):
        survey_rows.append(
            survey_at_site(z, site, contour_radius=contour_radius, rho_frac=rho_frac, cfg=cfg)
        )

    b_survey_max = max((r.b for r in survey_rows), default=0)
    w_survey_max = max((abs(r.winding_auto) for r in survey_rows), default=0.0)
    passed_survey = b_survey_max > 0
    passed_anchor = anchor_row is not None and anchor_row.b > 0
    passed = passed_anchor if anchor is not None else passed_survey

    rho_mean = float(rho.mean().item())
    rho_max = float(rho.max().item())

    return {
        "mode": "anchor" if anchor is not None else "survey",
        "anchor": _row_dict(anchor_row),
        "b_anchor": anchor_row.b if anchor_row else 0,
        "passed_anchor": passed_anchor,
        "survey": [_row_dict(r) for r in survey_rows],
        "b_survey_max": int(b_survey_max),
        "winding_survey_max": float(w_survey_max),
        "passed_survey": passed_survey,
        "passed": passed,
        "rho_mean": rho_mean,
        "rho_max": rho_max,
        "contrast": float(rho_max / (rho_mean + 1e-30)),
        "contour_radius": contour_radius,
        "survey_margin": margin,
    }


def _row_dict(row: SiteSurvey | None) -> dict[str, Any] | None:
    if row is None:
        return None
    return {
        "iz": row.site.iz,
        "y": row.site.y,
        "x": row.site.x,
        "rho": row.rho,
        "b": row.b,
        "w_rel": row.winding_rel,
        "w_u1": row.winding_u1,
        "w_auto": row.winding_auto,
        "rho_floor_ok": row.rho_floor_ok,
        "torus_safe": row.torus_safe,
        "local_max": row.local_max,
    }


def default_anchor(z: torch.Tensor) -> MatterSite:
    """Lattice center (planted VORTEX_* default)."""
    nz, ny, nx = spatial_shape(z)
    if nz is None:
        return MatterSite(None, ny // 2, nx // 2)
    cy, cx = ny // 2, nx // 2
    rho = spinor_density(z)
    iz = int(rho[:, cy, cx].argmax().item())
    return MatterSite(iz, cy, cx)


def defect_candidates(
    z: torch.Tensor,
    *,
    top_k: int = 24,
    contour_radius: int = 2,
    margin: int | None = None,
    require_local_max: bool = False,
) -> list[SiteSurvey]:
    """Survey instrument: sites with b≥1 (|n|≥¾) after column-snap and plane readout."""
    margin = margin if margin is not None else contour_radius + 1
    rho = spinor_density(z)
    sites = survey_density_sites(
        rho,
        top_k=top_k,
        margin=margin,
        require_local_max=require_local_max,
    )
    rows: list[SiteSurvey] = []
    for site in sites:
        row = survey_at_site(z, site, contour_radius=contour_radius)
        if row.b >= 1:
            rows.append(row)
    rows.sort(key=lambda r: r.rho, reverse=True)
    return rows
