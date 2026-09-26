"""ISM blanket (ММС/МЗВ) over settled boil ocean — spatial τ screen on top layers."""

from __future__ import annotations

from typing import Any

import torch

from mt_ca.ism_screen import column_tau_at_r, load_ism_constraints, r_au_to_pc
from mt_ca.t_validation import coarse_grain


def tau_map_ism_blanket(
    ny: int,
    nx: int,
    constraints: dict[str, Any],
    *,
    device: torch.device,
    dtype: torch.dtype,
    wind_axis: str = "x",
) -> torch.Tensor:
    """2D optical-depth map on the blanket: local column at Sun → full LIC downwind."""
    geom = constraints["geometry"]
    v1 = constraints["vlism_voyager_v1"]
    lic_pc = float(constraints["column_screen"].get("lic_outer_pc", 15.0))
    r_voy = r_au_to_pc(float(v1["r_au_nominal"]), geom)
    tau_local = column_tau_at_r(constraints, r_voy)["tau"]
    tau_lic = column_tau_at_r(constraints, lic_pc)["tau"]

    ys = torch.arange(ny, device=device, dtype=torch.float32)
    xs = torch.arange(nx, device=device, dtype=torch.float32)
    yy, xx = torch.meshgrid(ys, xs, indexing="ij")
    cy, cx = (ny - 1) * 0.5, (nx - 1) * 0.5
    if wind_axis == "x":
        path = ((xx - cx) / max(cx, 1.0) + 1.0) * 0.5
    elif wind_axis == "y":
        path = ((yy - cy) / max(cy, 1.0) + 1.0) * 0.5
    else:
        raise ValueError(wind_axis)
    path = path.clamp(0.0, 1.0)
    return tau_local + (tau_lic - tau_local) * path


def apply_ism_blanket(
    z: torch.Tensor,
    tau_2d: torch.Tensor,
    *,
    thickness: int,
    frac_bits: int,
    mod_bits: int,
) -> torch.Tensor:
    """Install top ``thickness`` layers: copy ocean interface, attenuate by exp(-τ) per cell."""
    if thickness <= 0:
        return z
    nz = z.shape[0]
    if thickness >= nz:
        raise ValueError("blanket thicker than grid")
    z2 = z.clone()
    iface = nz - thickness - 1
    base_layer = z2[iface]
    per_layer = tau_2d / float(thickness)
    att = torch.exp(-per_layer).to(z.dtype).unsqueeze(-1)
    for k in range(thickness):
        z2[iface + 1 + k] = base_layer * att
    return z2


def readout_slice_stats(z: torch.Tensor, iz: int, block: int) -> dict[str, float]:
    macro = coarse_grain(z[iz], block)
    m = float(macro.mean().item())
    s = float(macro.std().item())
    flat = macro.detach().flatten()
    q = torch.quantile(flat, torch.tensor([0.05, 0.5, 0.95], device=flat.device))
    return {
        "mean": m,
        "std": s,
        "rms_rel": s / m if m > 0 else 0.0,
        "p05": float(q[0].item()),
        "p50": float(q[1].item()),
        "p95": float(q[2].item()),
    }


def blanket_distribution_report(
    z_before: torch.Tensor,
    z_after: torch.Tensor,
    *,
    thickness: int,
    block: int,
    tau_2d: torch.Tensor,
) -> dict[str, Any]:
    iface = z_after.shape[0] - thickness - 1
    iz_top = z_after.shape[0] - 1
    ocean = readout_slice_stats(z_before, iface, block)
    under = readout_slice_stats(z_after, iface, block)
    top = readout_slice_stats(z_after, iz_top, block)
    tau_flat = tau_2d.detach().flatten()
    return {
        "iz_interface": iface,
        "iz_blanket_top": iz_top,
        "ocean_before_blanket": ocean,
        "interface_after_blanket": under,
        "blanket_top": top,
        "contrast_ratio_mean": top["mean"] / under["mean"] if under["mean"] > 0 else 0.0,
        "blanket_smooths": top["rms_rel"] < under["rms_rel"],
        "tau_min": float(tau_flat.min().item()),
        "tau_max": float(tau_flat.max().item()),
        "tau_mean": float(tau_flat.mean().item()),
    }
