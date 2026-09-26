"""ISM screen forward — ν-damp + column τ; VLISM magnetothermal; CMB chain.

Column τ SSOT: ``mt_ca.blanket.column``. Blanket geometry: ``mt_ca.blanket`` · BLANKET.md.
"""

from __future__ import annotations

import math
from typing import Any

from mt_ca.blanket.column import column_tau_at_r, r_au_to_pc
from mt_ca.blanket.constraints import load_ism_constraints
from mt_ca.blanket.wnm import equilibrium_T_wnm_K


def apply_tau_on_contrast(rms_rel: float, tau: float) -> float:
    if rms_rel <= 0.0:
        return 0.0
    return rms_rel * math.exp(-tau)


def nu_damp_contrast(rms_rel: float, nu_passes: float, *, alpha: float) -> float:
    if rms_rel <= 0.0 or nu_passes <= 0.0:
        return 0.0
    return rms_rel * (float(nu_passes) ** (-alpha))


def required_tau_for_target(rms_after_nu: float, target: float) -> float:
    if rms_after_nu <= 0.0 or target <= 0.0:
        return float("inf")
    if rms_after_nu <= target:
        return 0.0
    return math.log(rms_after_nu / target)


def loglog_extrapolate_rms(
    nu_passes: list[int],
    rms_rel: list[float],
    nu_query: float,
) -> float:
    pts = sorted(
        [(float(p), r) for p, r in zip(nu_passes, rms_rel, strict=True) if p > 0 and r > 0.0],
        key=lambda t: t[0],
    )
    if not pts:
        return 0.0
    if nu_query <= pts[0][0]:
        return pts[0][1]
    for (p0, r0), (p1, r1) in zip(pts, pts[1:], strict=False):
        if p0 <= nu_query <= p1:
            t = (math.log(nu_query) - math.log(p0)) / (math.log(p1) - math.log(p0))
            return math.exp(math.log(r0) + t * (math.log(r1) - math.log(r0)))
    p0, r0 = pts[-2]
    p1, r1 = pts[-1]
    t = (math.log(nu_query) - math.log(p0)) / (math.log(p1) - math.log(p0))
    return math.exp(math.log(r0) + t * (math.log(r1) - math.log(r0)))


_K_BOLTZ = 1.380649e-23
_MU0 = 4.0e-7 * math.pi


def saha_h_ionization_fraction(T_K: float, n_H_cm3: float) -> float:
    if T_K <= 0.0 or n_H_cm3 <= 0.0:
        return 0.0
    n_m3 = n_H_cm3 * 1.0e6
    h = 6.62607015e-34
    m_e = 9.1093837015e-31
    k = _K_BOLTZ
    chi_ev = 13.5984
    ev_j = 1.602176634e-19
    pref = (2.0 * math.pi * m_e * k * T_K / (h * h)) ** 1.5
    k_saha = (2.0 / n_m3) * pref * math.exp(-chi_ev * ev_j / (k * T_K))
    if k_saha <= 0.0:
        return 0.0
    disc = k_saha * k_saha + 4.0 * k_saha
    x = (-k_saha + math.sqrt(disc)) / 2.0
    return max(0.0, min(1.0, x))


def ne_magnetothermal_cm3(B_nT: float, T_eff_K: float) -> float:
    if T_eff_K <= 0.0:
        return 0.0
    b_t = B_nT * 1.0e-9
    n_m3 = (b_t * b_t) / (2.0 * _MU0 * _K_BOLTZ * T_eff_K)
    return n_m3 * 1.0e-6


def vlism_T_ref_K(vlism: dict[str, Any]) -> float:
    if "T_eff_K_range" in vlism:
        lo, hi = vlism["T_eff_K_range"]
        return 0.5 * (float(lo) + float(hi))
    return float(vlism["T_eff_K_reference"])


def effective_T_from_wall_rms(
    T_ref_K: float,
    rms_rel: float,
    *,
    rms_reference_boil: float,
    thermal_coupling: float,
) -> float:
    if rms_reference_boil <= 0.0:
        return T_ref_K
    delta = rms_rel / rms_reference_boil - 1.0
    return T_ref_K * (1.0 + thermal_coupling * delta)


def predict_ne_lic_cm3(constraints: dict[str, Any], *, rms_rel: float) -> float:
    lic = constraints["lic"]
    m = constraints["model_v1"]
    n_h = float(lic["n_H_cm3_nominal"])
    t_k = equilibrium_T_wnm_K(n_h, constraints)
    x_cap = float(m["warm_neutral_ionization_max"])
    x_saha = min(x_cap, saha_h_ionization_fraction(t_k, n_h))
    x_photo = float(m["photoionization_fraction_floor"])
    rms_ref = float(m["rms_reference_boil"])
    gain = float(m["rms_ionization_gain"])
    boost = 1.0 + gain * (rms_rel / rms_ref - 1.0) if rms_ref > 0.0 else 1.0
    x = min(x_cap, max(x_saha, x_photo) * max(0.0, boost))
    y_he = float(m["Y_He_mass_fraction"])
    return n_h * (1.0 + y_he) * x


def predict_ne_vlism_cm3(constraints: dict[str, Any], *, rms_rel: float) -> dict[str, float]:
    v_obs = constraints["vlism_voyager_v1"]
    m = constraints["model_v1"]
    b = float(v_obs["B_nT_nominal"])
    t_ref = vlism_T_ref_K(v_obs)
    t_eff = effective_T_from_wall_rms(
        t_ref,
        rms_rel,
        rms_reference_boil=float(m["rms_reference_boil"]),
        thermal_coupling=float(m["thermal_coupling"]),
    )
    return {
        "T_eff_K": t_eff,
        "T_ref_K": t_ref,
        "B_nT": b,
        "n_e_cm3": ne_magnetothermal_cm3(b, t_eff),
    }


def evaluate_ism_screen_v2(
    *,
    log10_T_M_over_CMB: float,
    rms_rel_wall: float | None = None,
    constraints: dict[str, Any] | None = None,
    nu_passes: float | None = None,
    power_alpha: float | None = None,
    smooth_decay: list[dict[str, Any]] | None = None,
    nu_at_N_CMB: float | None = None,
    block: int = 4,
) -> dict[str, Any]:
    c = constraints or load_ism_constraints()
    scr = c["screen_v0"]
    pas = c["pass"]
    cmb = c["cmb_forward"]
    v_obs = c["vlism_voyager_v1"]
    geom = c.get("geometry", {})

    rms0 = float(
        rms_rel_wall if rms_rel_wall is not None else scr["rms_rel_after_wall_typical"]
    )
    nu = float(nu_passes if nu_passes is not None else scr["nu_passes_typical"])
    alpha = float(
        power_alpha if power_alpha is not None else scr["power_law_alpha_typical"]
    )
    target = float(cmb["delta_T_over_T"])

    if smooth_decay:
        decay_nu = [int(r["nu_passes"]) for r in smooth_decay]
        decay_rms = [float(r["rms_rel"]) for r in smooth_decay]
        rms_nu = loglog_extrapolate_rms(decay_nu, decay_rms, nu)
    else:
        rms_nu = nu_damp_contrast(rms0, nu, alpha=alpha)

    tau_req = required_tau_for_target(rms_nu, target)
    tau_scalar_cap = float(scr["tau_column_max"])
    tau_use = min(tau_req, tau_scalar_cap)
    rms_final = apply_tau_on_contrast(rms_nu, tau_use)

    r_voy_pc = r_au_to_pc(float(v_obs["r_au_nominal"]), geom) if geom else 0.0
    lic_edge = float(c["column_screen"].get("lic_outer_pc", 15.0))
    tau_v = column_tau_at_r(c, r_voy_pc)
    tau_lic = column_tau_at_r(c, lic_edge)

    ncmb_block: dict[str, Any] = {}
    if smooth_decay and nu_at_N_CMB and nu_at_N_CMB > 0:
        rms_ncmb = loglog_extrapolate_rms(decay_nu, decay_rms, float(nu_at_N_CMB))
        tau_req_ncmb = required_tau_for_target(rms_ncmb, target)
        ncmb_block = {
            "nu_at_N_CMB": float(nu_at_N_CMB),
            "rms_blind_at_N_CMB": rms_ncmb,
            "tau_required_at_N_CMB": tau_req_ncmb,
            "needs_acoustic_growth": rms_ncmb < target * 0.5,
        }

    lic_pred = predict_ne_lic_cm3(c, rms_rel=rms0)
    vl = predict_ne_vlism_cm3(c, rms_rel=rms0)
    n_e_pred = float(vl["n_e_cm3"])
    n_e_obs = float(v_obs["n_e_cm3_nominal"])
    ne_lo, ne_hi = v_obs["n_e_cm3_range"]
    tol = float(pas["vlism_ne_tolerance_frac"])
    rel_err = abs(n_e_pred - n_e_obs) / n_e_obs if n_e_obs > 0.0 else float("inf")

    lic = c["lic"]
    lic_lo, lic_hi = lic.get("n_e_cm3_range", [0.0, 1.0e9])

    ok_log = log10_T_M_over_CMB >= float(pas["log10_T_M_over_CMB_min"])
    ok_tau = tau_req <= float(pas["required_tau_max"])
    ok_rms = rms_final <= target * 1.05
    ok_vlism = ne_lo <= n_e_pred <= ne_hi and rel_err <= tol
    ok_lic = lic_lo <= lic_pred <= lic_hi
    ok_column = tau_v["tau"] <= tau_lic["tau"] + 1.0e-9
    expect_gap = bool(c.get("pass_v2", {}).get("expect_acoustic_gap_at_N_CMB", True))
    ok_ncmb = True
    if ncmb_block:
        ok_ncmb = ncmb_block["needs_acoustic_growth"] if expect_gap else True

    row: dict[str, Any] = {
        "id": "ISM_screen_v2",
        "log10_T_M_over_CMB": log10_T_M_over_CMB,
        "rms_rel_wall": rms0,
        "rms_after_nu": rms_nu,
        "nu_passes": nu,
        "alpha": alpha,
        "tau_required": tau_req,
        "tau_applied_scalar": tau_use,
        "rms_after_screen": rms_final,
        "delta_T_over_T_target": target,
        "tau_ism_voyager": tau_v,
        "tau_ism_lic_full": tau_lic,
        "r_voyager_pc": r_voy_pc,
        "n_e_lic_pred_cm3": lic_pred,
        "lic_ne_range": lic.get("n_e_cm3_range"),
        "n_e_vlism_pred_cm3": n_e_pred,
        "n_e_vlism_obs_cm3": n_e_obs,
        "vlism_ne_rel_err": rel_err,
        "vlism_ne_range": v_obs["n_e_cm3_range"],
        "vlism_T_eff_K": vl["T_eff_K"],
        "vlism_T_ref_K": vl["T_ref_K"],
        "vlism_B_nT": vl["B_nT"],
        "ok_log10_gap": ok_log,
        "ok_tau_feasible": ok_tau,
        "ok_rms_target": ok_rms,
        "ok_lic_ne": ok_lic,
        "ok_vlism_ne": ok_vlism,
        "ok_column_profile": ok_column,
        "ok_ncmb_acoustic_gap": ok_ncmb,
        "ok": ok_log and ok_tau and ok_rms and ok_lic and ok_vlism and ok_column and ok_ncmb,
        "note": (
            "v2: column τ(N_H,r); T_ref from VLISM literature range; "
            "N_CMB blind ν extrapolation flags acoustic growth (not wall-only)."
        ),
    }
    row.update(ncmb_block)
    return row


def evaluate_ism_screen_v1(**kwargs: Any) -> dict[str, Any]:
    row = dict(evaluate_ism_screen_v2(**kwargs))
    row["id"] = "ISM_screen_v1"
    row["tau_applied"] = row.pop("tau_applied_scalar")
    row["ok"] = (
        row["ok_log10_gap"]
        and row["ok_tau_feasible"]
        and row["ok_rms_target"]
        and row["ok_lic_ne"]
        and row["ok_vlism_ne"]
    )
    return row


def evaluate_ism_screen_v0(**kwargs: Any) -> dict[str, Any]:
    row = evaluate_ism_screen_v1(**kwargs)
    row["id"] = "ISM_screen_v0"
    return row
