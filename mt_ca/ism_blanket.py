"""ISM blanket — homogeneous МЗВ fill over ocean; T_ISM readout (not CMB / not T_M_bath)."""

from __future__ import annotations

import math
from typing import Any

import torch

from mt_ca.ism_screen import column_tau_at_r, equilibrium_T_wnm_K, load_ism_constraints, r_au_to_pc
from mt_ca.t_validation import coarse_grain


def tau_uniform_ism_blanket(
    ny: int,
    nx: int,
    constraints: dict[str, Any],
    *,
    device: torch.device,
) -> torch.Tensor:
    """One τ everywhere: macro МЗВ заполнена однородно (как океан), без «полос» по ветру."""
    geom = constraints["geometry"]
    v1 = constraints["vlism_voyager_v1"]
    r_voy = r_au_to_pc(float(v1["r_au_nominal"]), geom)
    tau0 = float(column_tau_at_r(constraints, r_voy)["tau"])
    return torch.full((ny, nx), tau0, device=device, dtype=torch.float32)


def tau_map_ism_blanket(
    ny: int,
    nx: int,
    constraints: dict[str, Any],
    *,
    device: torch.device,
    dtype: torch.dtype,
    wind_axis: str = "x",
) -> torch.Tensor:
    """Backward-compatible name — always uniform fill (``wind_axis`` ignored)."""
    del dtype, wind_axis
    return tau_uniform_ism_blanket(ny, nx, constraints, device=device)


def apply_ism_blanket(
    z: torch.Tensor,
    tau_2d: torch.Tensor,
    *,
    thickness: int,
    frac_bits: int,
    mod_bits: int,
) -> torch.Tensor:
    del frac_bits, mod_bits
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
    constraints: dict[str, Any],
) -> torch.Tensor:
    """T_МЗВ: T_eq(n_H, Saha↔UV) × ℬ ripple; T_LIC_obs only for external pass compare."""
    lic = constraints["lic"]
    m = constraints["model_v1"]
    n_h = float(lic["n_H_cm3_nominal"])
    t_eq = equilibrium_T_wnm_K(n_h, constraints)
    ref = float(phi_ocean_ref.mean().item())
    if ref <= 0.0:
        ref = float(phi_blanket.mean().item()) or 1.0
    ripple = (phi_blanket / ref).clamp(0.05, 4.0)
    coupling = float(m["thermal_coupling"])
    return t_eq * (1.0 + coupling * (ripple - 1.0))


def _quantiles(t: torch.Tensor, qs: list[float]) -> list[float]:
    flat = t.detach().flatten()
    q = torch.quantile(flat, torch.tensor(qs, device=flat.device))
    return [float(x.item()) for x in q]


def ism_temperature_report(
    z_ocean: torch.Tensor,
    z_blanket: torch.Tensor,
    constraints: dict[str, Any],
    *,
    thickness: int,
    block: int,
) -> dict[str, Any]:
    iface = z_blanket.shape[0] - thickness - 1
    iz_top = z_blanket.shape[0] - 1
    phi_o = coarse_grain(z_ocean[iface], block)
    phi_b = coarse_grain(z_blanket[iz_top], block)
    t_map = ism_T_map_K(phi_b, phi_o, constraints)
    t_eq = equilibrium_T_wnm_K(float(constraints["lic"]["n_H_cm3_nominal"]), constraints)
    pas = constraints.get("pass_blanket", {})
    lic_lo, lic_hi = pas.get("T_lic_K_range", [4000.0, 12000.0])
    t_obs = float(constraints["lic"]["T_K_warm_nominal"])
    med = float(t_map.median().item())
    mean = float(t_map.mean().item())
    rel = abs(med - t_obs) / t_obs
    tol = float(pas.get("T_lic_median_tolerance_frac", 0.55))
    ok_scale = lic_lo <= med <= lic_hi
    ok_match_obs = rel <= tol

    return {
        "T_ism_map_K": {
            "quantiles": dict(
                zip(
                    ["min", "p05", "p50", "p95", "max"],
                    _quantiles(t_map, [0.0, 0.05, 0.5, 0.95, 1.0]),
                    strict=True,
                )
            ),
            "mean_K": mean,
            "log10_mean": math.log10(mean),
            "median_rel_err_vs_LIC_obs": rel,
        },
        "derived_K": {"T_eq_from_nH_Saha_UV": t_eq},
        "observation_K": {"T_LIC_literature": t_obs},
        "ok_T_ISM_scale": ok_scale,
        "ok_match_LIC_observation": ok_match_obs,
        "ok_T_ISM_hypothesis": ok_scale,
        "note": "T_eq from n_H + Saha↔UV floor; ℬ ripple from sim; LIC 7000K is pass compare only.",
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
        "tau_ism_uniform": float(tau_flat[0].item()),
        "ocean_phi_rms_rel": ocean["rms_rel"],
        "blanket_phi_rms_rel": top["rms_rel"],
    }
    if constraints is not None:
        out["T_ism"] = ism_temperature_report(
            z_before,
            z_after,
            constraints,
            thickness=thickness,
            block=block,
        )
    return out
