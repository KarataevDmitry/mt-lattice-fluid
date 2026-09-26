"""Readout gates shared by scripts, verify, and the sim runner."""
from __future__ import annotations

from typing import Any

import torch

from mt_ca.matter_readout import MatterSite, default_anchor, planckon_instrument, survey_density_sites
from mt_ca.spinor import spinor_density
from mt_ca.topology import gate_plane_z, winding_channels, winding_nearest_int


def gate_b(
    z: torch.Tensor,
    *,
    anchor: MatterSite | tuple[int | None, int, int] | None = None,
    top_k: int = 4,
    contour_radius: int = 2,
    use_survey_pass: bool = True,
) -> dict[str, float | int | bool]:
    """Matter birth gate: b≥1 with |n_∂|≥¾ (dual channel).

    **Legacy survey** (default): local-ρ maxima inside torus margin — not raw global argmax.
    **Anchor mode** (planted core): pass ``anchor=(iz,y,x)`` or use ``anchor="center"`` via kwargs
    in :func:`peak_stats`.

    ``passed`` = survey OR anchor when both are provided (either sees matter).
    """
    anchor_site: MatterSite | None = None
    if anchor is not None:
        if isinstance(anchor, MatterSite):
            anchor_site = anchor
        else:
            iz, y, x = anchor
            anchor_site = MatterSite(iz, y, x)

    inst = planckon_instrument(
        z,
        anchor=anchor_site,
        top_k=top_k,
        contour_radius=contour_radius,
        require_local_max=True,
    )

    # Top-k hit count (winding on ranked peaks, margin-safe) — diagnostics for scripts.
    rho = spinor_density(z)
    ny, nx = rho.shape[-2:]
    margin = contour_radius + 1
    b_hits = 0
    w_rel_max = 0.0
    w_u1_max = 0.0
    w_abs_max = float(inst["winding_survey_max"])
    for site in survey_density_sites(
        rho, top_k=top_k, margin=margin, require_local_max=False
    ):
        z_plane = gate_plane_z(z, site.iz) if site.iz is not None else z
        if not (
            site.y >= margin
            and site.x >= margin
            and site.y < ny - margin
            and site.x < nx - margin
        ):
            continue
        ch = winding_channels(z_plane, center=(site.y, site.x), radius=contour_radius)
        w = ch["auto"]
        if ch["rel"] == ch["rel"]:
            w_rel_max = max(w_rel_max, abs(float(ch["rel"])))
        if ch["u1"] == ch["u1"]:
            w_u1_max = max(w_u1_max, abs(float(ch["u1"])))
        if w == w and abs(w) >= 0.75:
            b_hits += min(1, abs(winding_nearest_int(w)))

    b_argmax = int(inst["b_survey_max"])
    passed = bool(inst["passed_survey"] if use_survey_pass else False)
    if anchor_site is not None and inst["passed_anchor"]:
        passed = True

    return {
        "b_hits_topk": int(b_hits),
        "b_argmax": b_argmax,
        "b_anchor": int(inst["b_anchor"]),
        "passed": passed,
        "passed_survey": bool(inst["passed_survey"]),
        "passed_anchor": bool(inst["passed_anchor"]),
        "rho_mean": float(inst["rho_mean"]),
        "rho_max": float(inst["rho_max"]),
        "contrast": float(inst["contrast"]),
        "winding_abs_max": w_abs_max,
        "winding_rel_max": w_rel_max,
        "winding_u1_max": w_u1_max,
    }


def peak_stats(
    z: torch.Tensor,
    *,
    anchor: MatterSite | tuple[int | None, int, int] | str | None = None,
    top_k: int = 16,
    contour_radius: int = 2,
) -> dict[str, float | int]:
    """Extended peak/birth stats for time-series sampling."""
    from mt_ca.metrics import field_amplitude
    from mt_ca.topology import winding_number

    anchor_site: MatterSite | None = None
    if anchor == "center":
        anchor_site = default_anchor(z)
    elif isinstance(anchor, MatterSite):
        anchor_site = anchor
    elif isinstance(anchor, tuple):
        iz, y, x = anchor
        anchor_site = MatterSite(iz, y, x)

    gate = gate_b(
        z,
        anchor=anchor_site,
        top_k=top_k,
        contour_radius=contour_radius,
    )
    inst: dict[str, Any] = planckon_instrument(
        z,
        anchor=anchor_site,
        top_k=top_k,
        contour_radius=contour_radius,
    )

    rho = spinor_density(z)
    amp = field_amplitude(z)
    ny, nx = rho.shape[-2:]
    windings: list[float] = []
    margin = contour_radius + 1
    for site in survey_density_sites(
        rho, top_k=top_k, margin=margin, require_local_max=False
    ):
        z_plane = gate_plane_z(z, site.iz) if site.iz is not None else z
        if site.y < margin or site.x < margin or site.y >= ny - margin or site.x >= nx - margin:
            continue
        w = winding_number(z_plane, center=(site.y, site.x), radius=contour_radius)
        if w == w:
            windings.append(float(w))

    return {
        **gate,
        "amp_mean": float(amp.mean().item()),
        "amp_max": float(amp.max().item()),
        "top_k": min(top_k, rho.numel()),
        "winding_topk_abs_max": max((abs(w) for w in windings), default=0.0),
        "winding_topk_mean_abs": (
            float(sum(abs(w) for w in windings) / len(windings)) if windings else 0.0
        ),
        "instrument": inst,
    }
