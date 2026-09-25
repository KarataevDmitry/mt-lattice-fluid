"""Readout gates shared by scripts, verify, and the sim runner."""
from __future__ import annotations

import torch

from mt_ca.spinor import spinor_density
from mt_ca.topology import (
    gate_plane_z,
    matter_occupancy_b,
    unravel_peak_index,
    winding_channels,
    winding_nearest_int,
)


def gate_b(
    z: torch.Tensor,
    *,
    top_k: int = 4,
    contour_radius: int = 2,
) -> dict[str, float | int | bool]:
    """Matter birth gate: b≥1 at density peak (|n_∂|≥¾), dual channel."""
    rho = spinor_density(z)
    flat = rho.reshape(-1)
    k = min(top_k, flat.numel())
    _, idx = torch.topk(flat, k)
    plane_shape = rho.shape[-2:]
    ny, nx = plane_shape
    b_hits = 0
    w_abs_max = 0.0
    w_rel_max = 0.0
    w_u1_max = 0.0
    margin = contour_radius + 1
    for i in range(k):
        iz, y, x = unravel_peak_index(rho, int(idx[i].item()))
        z_plane = gate_plane_z(z, iz) if iz is not None else z
        if y < margin or x < margin or y >= ny - margin or x >= nx - margin:
            continue
        ch = winding_channels(z_plane, center=(y, x), radius=contour_radius)
        w = ch["auto"]
        if ch["rel"] == ch["rel"]:
            w_rel_max = max(w_rel_max, abs(float(ch["rel"])))
        if ch["u1"] == ch["u1"]:
            w_u1_max = max(w_u1_max, abs(float(ch["u1"])))
        if w == w:
            w_abs_max = max(w_abs_max, abs(float(w)))
            if abs(w) >= 0.75:
                b_hits += min(1, abs(winding_nearest_int(w)))
    b_argmax = matter_occupancy_b(z, contour_radius=contour_radius)
    rho_mean = float(rho.mean().item())
    rho_max = float(rho.max().item())
    return {
        "b_hits_topk": int(b_hits),
        "b_argmax": int(b_argmax),
        "passed": bool(b_hits > 0 or b_argmax > 0),
        "rho_mean": rho_mean,
        "rho_max": rho_max,
        "contrast": float(rho_max / (rho_mean + 1e-30)),
        "winding_abs_max": w_abs_max,
        "winding_rel_max": w_rel_max,
        "winding_u1_max": w_u1_max,
    }


def peak_stats(
    z: torch.Tensor,
    *,
    top_k: int = 16,
    contour_radius: int = 2,
) -> dict[str, float | int]:
    """Extended peak/birth stats for time-series sampling."""
    from mt_ca.metrics import field_amplitude
    from mt_ca.topology import winding_number

    rho = spinor_density(z)
    amp = field_amplitude(z)
    gate = gate_b(z, top_k=top_k, contour_radius=contour_radius)
    flat = rho.reshape(-1)
    k = min(top_k, flat.numel())
    _, idx = torch.topk(flat, k)
    ny, nx = rho.shape[-2:]
    windings: list[float] = []
    margin = contour_radius + 1
    for i in range(k):
        iz, y, x = unravel_peak_index(rho, int(idx[i].item()))
        z_plane = gate_plane_z(z, iz) if iz is not None else z
        if y < margin or x < margin or y >= ny - margin or x >= nx - margin:
            continue
        w = winding_number(z_plane, center=(y, x), radius=contour_radius)
        if w == w:
            windings.append(float(w))
    return {
        **gate,
        "amp_mean": float(amp.mean().item()),
        "amp_max": float(amp.max().item()),
        "top_k": k,
        "winding_topk_abs_max": max((abs(w) for w in windings), default=0.0),
        "winding_topk_mean_abs": (
            float(sum(abs(w) for w in windings) / len(windings)) if windings else 0.0
        ),
    }
