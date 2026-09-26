"""ISM screen v1 — ν-damp + exp(-τ) on ℬ contrast; VLISM n_e from magnetothermal + sim T_eff."""



from __future__ import annotations



import json

import math

from pathlib import Path

from typing import Any



import yaml



_DATA_DIR = Path(__file__).resolve().parents[1] / "data"

_DEFAULT_YAML = _DATA_DIR / "ism_constraints_v0.yaml"

_DEFAULT_JSON = _DATA_DIR / "ism_constraints_v0.json"



_K_BOLTZ = 1.380649e-23  # J/K

_MU0 = 4.0e-7 * math.pi  # H/m





def load_ism_constraints(path: Path | str | None = None) -> dict[str, Any]:

    if path is not None:

        p = Path(path)

        if p.suffix.lower() in {".yaml", ".yml"}:

            with p.open(encoding="utf-8") as f:

                data = yaml.safe_load(f)

        else:

            with p.open(encoding="utf-8") as f:

                data = json.load(f)

    elif _DEFAULT_YAML.is_file():

        with _DEFAULT_YAML.open(encoding="utf-8") as f:

            data = yaml.safe_load(f)

    elif _DEFAULT_JSON.is_file():

        with _DEFAULT_JSON.open(encoding="utf-8") as f:

            data = json.load(f)

    else:

        raise FileNotFoundError("missing data/ism_constraints_v0.yaml or .json")

    if not isinstance(data, dict):

        raise ValueError("invalid ISM constraints file")

    return data





def apply_tau_on_contrast(rms_rel: float, tau: float) -> float:

    """Multiplicative screen on macro contrast (not on micro |z|²)."""

    if rms_rel <= 0.0:

        return 0.0

    return rms_rel * math.exp(-tau)





def nu_damp_contrast(rms_rel: float, nu_passes: float, *, alpha: float) -> float:

    """Proxy for binomial ν-chain: rms ~ rms0 · ν^{-α}."""

    if rms_rel <= 0.0 or nu_passes <= 0.0:

        return 0.0

    return rms_rel * (float(nu_passes) ** (-alpha))





def required_tau_for_target(rms_after_nu: float, target: float) -> float:

    if rms_after_nu <= 0.0 or target <= 0.0:

        return float("inf")

    if rms_after_nu <= target:

        return 0.0

    return math.log(rms_after_nu / target)





def saha_h_ionization_fraction(T_K: float, n_H_cm3: float) -> float:

    """Primary H ionization fraction x = n_e / n_H (Saha, non-relativistic)."""

    if T_K <= 0.0 or n_H_cm3 <= 0.0:

        return 0.0

    n_m3 = n_H_cm3 * 1.0e6

    h = 6.62607015e-34

    m_e = 9.1093837015e-31

    k = _K_BOLTZ

    chi_ev = 13.5984

    ev_j = 1.602176634e-19

    pref = (2.0 * math.pi * m_e * k * T_K / (h * h)) ** 1.5

    K = (2.0 / n_m3) * pref * math.exp(-chi_ev * ev_j / (k * T_K))

    if K <= 0.0:

        return 0.0

    # x^2 / (1-x) = K  →  x = (-K + sqrt(K^2 + 4K)) / 2

    disc = K * K + 4.0 * K

    if disc < 0.0:

        return 0.0

    x = (-K + math.sqrt(disc)) / 2.0

    return max(0.0, min(1.0, x))





def ne_magnetothermal_cm3(B_nT: float, T_eff_K: float) -> float:

    """n [cm⁻³] when thermal pressure n k T balances B²/(2μ₀) (single-fluid scale)."""

    if T_eff_K <= 0.0:

        return 0.0

    B_t = B_nT * 1.0e-9

    n_m3 = (B_t * B_t) / (2.0 * _MU0 * _K_BOLTZ * T_eff_K)

    return n_m3 * 1.0e-6





def effective_T_from_wall_rms(

    T_ref_K: float,

    rms_rel: float,

    *,

    rms_reference_boil: float,

    thermal_coupling: float,

) -> float:

    """ℬ wall ripple → fractional shift of effective plasma temperature (model v1)."""

    if rms_reference_boil <= 0.0:

        return T_ref_K

    delta = rms_rel / rms_reference_boil - 1.0

    return T_ref_K * (1.0 + thermal_coupling * delta)





def predict_ne_lic_cm3(constraints: dict[str, Any], *, rms_rel: float) -> float:

    """LIC warm gas: Saha + UV floor, modulated by wall rms (no Voyager numbers in formula)."""

    lic = constraints["lic"]

    m = constraints["model_v1"]

    T = float(lic["T_K_warm_nominal"])

    n_H = float(lic["n_H_cm3_nominal"])

    x_saha = saha_h_ionization_fraction(T, n_H)

    x_photo = float(m["photoionization_fraction_floor"])

    rms_ref = float(m["rms_reference_boil"])

    gain = float(m["rms_ionization_gain"])

    if rms_ref > 0.0:

        boost = 1.0 + gain * (rms_rel / rms_ref - 1.0)

    else:

        boost = 1.0

    x = min(float(m["warm_neutral_ionization_max"]), max(min(x_saha, float(m["warm_neutral_ionization_max"])), x_photo) * max(0.0, boost))

    y_he = float(m["Y_He_mass_fraction"])

    return n_H * (1.0 + y_he) * x





def predict_ne_vlism_cm3(

    constraints: dict[str, Any],

    *,

    rms_rel: float,

) -> dict[str, float]:

    """VLISM: observed |B| + literature T_ref, T_eff shifted by measured wall rms."""

    v1 = constraints["vlism_voyager_v1"]

    m = constraints["model_v1"]

    B = float(v1["B_nT_nominal"])

    T_ref = float(v1["T_eff_K_reference"])

    T_eff = effective_T_from_wall_rms(

        T_ref,

        rms_rel,

        rms_reference_boil=float(m["rms_reference_boil"]),

        thermal_coupling=float(m["thermal_coupling"]),

    )

    n_e = ne_magnetothermal_cm3(B, T_eff)

    return {

        "T_eff_K": T_eff,

        "T_ref_K": T_ref,

        "B_nT": B,

        "n_e_cm3": n_e,

    }





def evaluate_ism_screen_v1(

    *,

    log10_T_M_over_CMB: float,

    rms_rel_wall: float | None = None,

    constraints: dict[str, Any] | None = None,

    nu_passes: float | None = None,

    power_alpha: float | None = None,

) -> dict[str, Any]:

    """Verify + forward script: derived n_e and τ; PASS only if anchors match without tautology."""

    c = constraints or load_ism_constraints()

    scr = c["screen_v0"]

    pas = c["pass"]

    cmb = c["cmb_readout"]

    v_obs = c["vlism_voyager_v1"]



    rms0 = float(

        rms_rel_wall if rms_rel_wall is not None else scr["rms_rel_after_wall_typical"]

    )

    nu = float(nu_passes if nu_passes is not None else scr["nu_passes_typical"])

    alpha = float(

        power_alpha if power_alpha is not None else scr["power_law_alpha_typical"]

    )

    target = float(cmb["delta_T_over_T"])



    rms_nu = nu_damp_contrast(rms0, nu, alpha=alpha)

    tau_req = required_tau_for_target(rms_nu, target)

    tau_use = min(tau_req, float(scr["tau_column_max"]))

    rms_final = apply_tau_on_contrast(rms_nu, tau_use)



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



    return {

        "id": "ISM_screen_v1",

        "log10_T_M_over_CMB": log10_T_M_over_CMB,

        "rms_rel_wall": rms0,

        "rms_after_nu": rms_nu,

        "nu_passes": nu,

        "alpha": alpha,

        "tau_required": tau_req,

        "tau_applied": tau_use,

        "rms_after_screen": rms_final,

        "delta_T_over_T_target": target,

        "n_e_lic_pred_cm3": lic_pred,

        "lic_ne_range": lic.get("n_e_cm3_range"),

        "n_e_vlism_pred_cm3": n_e_pred,

        "n_e_vlism_obs_cm3": n_e_obs,

        "vlism_ne_rel_err": rel_err,

        "vlism_ne_range": v_obs["n_e_cm3_range"],

        "vlism_T_eff_K": vl["T_eff_K"],

        "vlism_B_nT": vl["B_nT"],

        "ok_log10_gap": ok_log,

        "ok_tau_feasible": ok_tau,

        "ok_rms_target": ok_rms,

        "ok_lic_ne": ok_lic,

        "ok_vlism_ne": ok_vlism,

        "ok": ok_log and ok_tau and ok_rms and ok_lic and ok_vlism,

        "note": (

            "v1: LIC n_e from Saha+UV floor×ℬ rms; VLISM n_e from |B|, T_ref, "

            "T_eff(rms); Voyager n_e is comparison only — no fill-to-target."

        ),

    }





def evaluate_ism_screen_v0(**kwargs: Any) -> dict[str, Any]:

    """Backward-compatible alias — runs v1 physics."""

    row = evaluate_ism_screen_v1(**kwargs)

    row["id"] = "ISM_screen_v0"

    return row


