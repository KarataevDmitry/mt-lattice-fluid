"""ISM blanket (ММС/МЗВ) over settled boil ocean — spatial τ + T_ISM readout (not CMB / not T_M_bath)."""

from __future__ import annotations

import math
from typing import Any

import torch

from mt_ca.ism_screen import column_tau_at_r, load_ism_constraints, r_au_to_pc, vlism_T_ref_K
from mt_ca.t_validation import coarse_grain


def tau_map_ism_blanket(
    ny: int,
    nx: int,
    constraints: dict[str, Any],
    *,
    device: torch.device,
    dtype: torch.dtype,
    wind_axis: str = "x",
) -> tuple[torch.Tensor, torch.Tensor]:
    """τ(x,y) and wind path in [0,1] (0 = upwind / local column, 1 = LIC downwind)."""
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
    tau = tau_local + (tau_lic - tau_local) * path
    return tau, path


def apply_ism_blanket(
    z: torch.Tensor,
    tau_2d: torch.Tensor,
    *,
    thickness: int,
    frac_bits: int,
    mod_bits: int,
) -> torch.Tensor:
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


def ism_T_map_K(
    phi_blanket: torch.Tensor,
    phi_ocean_ref: torch.Tensor,
    tau_2d: torch.Tensor,
    path_2d: torch.Tensor,
    constraints: dict[str, Any],
) -> torch.Tensor:
    """Macro T readout of ISM on the blanket — anchored to LIC / VLISM literature, modulated by sim ℬ."""
    lic = constraints["lic"]
    m = constraints["model_v1"]
    t_lic = float(lic["T_K_warm_nominal"])
    t_vl = vlism_T_ref_K(constraints["vlism_voyager_v1"])
    tau_min = float(tau_2d.min().item())
    tau_max = float(tau_2d.max().item())
    span = max(tau_max - tau_min, 1.0e-12)
    tau_norm = (tau_2d - tau_min) / span

    # Column / wind: warm LIC → hotter plasma scale downwind (longer column).
    t_column = t_lic + (t_vl - t_lic) * tau_norm

    ref = float(phi_ocean_ref.mean().item())
    if ref <= 0.0:
        ref = float(phi_blanket.mean().item()) or 1.0
    ripple = (phi_blanket / ref).clamp(0.05, 4.0)
    coupling = float(m["thermal_coupling"])
    return t_column * (1.0 + coupling * (ripple - 1.0))


def _quantiles(t: torch.Tensor, qs: list[float]) -> list[float]:
    flat = t.detach().flatten()
    q = torch.quantile(flat, torch.tensor(qs, device=flat.device))
    return [float(x.item()) for x in q]


def ism_temperature_report(
    z_ocean: torch.Tensor,
    z_blanket: torch.Tensor,
    tau_2d: torch.Tensor,
    path_2d: torch.Tensor,
    constraints: dict[str, Any],
    *,
    thickness: int,
    block: int,
) -> dict[str, Any]:
    iface = z_blanket.shape[0] - thickness - 1
    iz_top = z_blanket.shape[0] - 1
    phi_o = coarse_grain(z_ocean[iface], block)
    phi_b = coarse_grain(z_blanket[iz_top], block)
    tau_c = tau_2d
    path_c = path_2d
    if tau_c.shape != phi_b.shape:
        import torch.nn.functional as F

        tau_c = F.interpolate(
            tau_2d.unsqueeze(0).unsqueeze(0),
            size=phi_b.shape,
            mode="bilinear",
            align_corners=True,
        ).squeeze()
        path_c = F.interpolate(
            path_2d.unsqueeze(0).unsqueeze(0),
            size=phi_b.shape,
            mode="bilinear",
            align_corners=True,
        ).squeeze()

    t_map = ism_T_map_K(phi_b, phi_o, tau_c, path_c, constraints)
    pas = constraints.get("pass_blanket", {})
    lic_lo, lic_hi = pas.get("T_lic_K_range", [4000.0, 12000.0])
    vl_lo, vl_hi = pas.get("T_vlism_K_range", [15000.0, 65000.0])
    lic_path = float(pas.get("lic_sky_path_max", 0.35))
    vl_path = float(pas.get("vlism_sky_path_min", 0.65))

    lic_mask = path_c <= lic_path
    vl_mask = path_c >= vl_path
    t_lic_side = t_map[lic_mask] if bool(lic_mask.any()) else t_map
    t_vl_side = t_map[vl_mask] if bool(vl_mask.any()) else t_map

    t_nom_lic = float(constraints["lic"]["T_K_warm_nominal"])
    t_nom_vl = vlism_T_ref_K(constraints["vlism_voyager_v1"])

    med_lic = float(t_lic_side.median().item())
    med_vl = float(t_vl_side.median().item())
    ok_lic = lic_lo <= med_lic <= lic_hi
    ok_vl = vl_lo <= med_vl <= vl_hi

    return {
        "T_ism_map_K": {
            "quantiles": dict(
                zip(
                    ["min", "p05", "p50", "p95", "max"],
                    _quantiles(t_map, [0.0, 0.05, 0.5, 0.95, 1.0]),
                    strict=True,
                )
            ),
            "mean_K": float(t_map.mean().item()),
            "log10_mean": math.log10(float(t_map.mean().item())),
        },
        "anchors_K": {
            "T_LIC_nominal": t_nom_lic,
            "T_VLISM_ref": t_nom_vl,
        },
        "regimes": {
            "lic_sky_median_K": med_lic,
            "vlism_sky_median_K": med_vl,
            "lic_sky_rel_err": abs(med_lic - t_nom_lic) / t_nom_lic,
            "vlism_sky_rel_err": abs(med_vl - t_nom_vl) / t_nom_vl,
        },
        "ok_T_LIC_sky": ok_lic,
        "ok_T_VLISM_sky": ok_vl,
        "ok_T_ISM_hypothesis": ok_lic and ok_vl,
        "note": "T_ISM from LIC/VLISM anchors × column(path) × ℬ ripple; not T_M_bath, not T_CMB.",
    }


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
    path_2d: torch.Tensor | None = None,
    constraints: dict[str, Any] | None = None,
) -> dict[str, Any]:
    iface = z_after.shape[0] - thickness - 1
    iz_top = z_after.shape[0] - 1
    ocean = readout_slice_stats(z_before, iface, block)
    under = readout_slice_stats(z_after, iface, block)
    top = readout_slice_stats(z_after, iz_top, block)
    tau_flat = tau_2d.detach().flatten()
    out: dict[str, Any] = {
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
    if path_2d is not None and constraints is not None:
        out["T_ism"] = ism_temperature_report(
            z_before,
            z_after,
            tau_2d,
            path_2d,
            constraints,
            thickness=thickness,
            block=block,
        )
    return out
