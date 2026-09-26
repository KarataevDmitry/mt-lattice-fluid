"""Warm neutral medium (WNM) thermal balance — heating vs line cooling (H + He), no T_LIC in solver.

Channels: CR + UV photoelectric heating (Wolfire/Draine cgs); cooling [C II], [O I], Lyα, free-free.
``cooling_scale`` in constraints normalises analytic line strengths to Γ=Λ at LIC ``n_H`` (not a T input).
"""

from __future__ import annotations

import math
from typing import Any

_K_B = 1.380649e-16  # erg/K
_EV_ERG = 1.602176634e-12
_MH_G = 1.6735575e-24


def _wnm_params(constraints: dict[str, Any]) -> dict[str, float]:
    w = constraints.get("wnm_thermal", {})
    m = constraints.get("model_v1", {})
    return {
        "zeta_H_s-1": float(w.get("zeta_H_s-1", 1.8e-17)),
        "habing_G0": float(w.get("habing_G0", 1.0)),
        "dust_pe_efficiency": float(w.get("dust_pe_efficiency", 0.04)),
        "Y_He": float(m.get("Y_He_mass_fraction", 0.25)),
        "T_min_K": float(w.get("T_min_K", 1000.0)),
        "T_max_K": float(w.get("T_max_K", 25_000.0)),
        "n_eff_saha_cm3": float(w.get("n_eff_saha_cm3", 0.35)),
        "cooling_scale": float(w.get("cooling_scale", 1.0)),
    }


def _saha_x_h(T_K: float, n_H_cm3: float, *, n_eff_cm3: float | None = None) -> float:
    """Primary H ionization fraction; ``n_eff`` avoids unphysical x→1 at very low n_H."""
    n_use = max(n_H_cm3, n_eff_cm3 or 0.0)
    if n_eff_cm3 is not None and n_eff_cm3 > 0.0:
        n_use = float(n_eff_cm3)
    if T_K <= 0.0 or n_use <= 0.0:
        return 0.0
    n_m3 = n_use * 1.0e6
    h = 6.62607015e-34
    m_e = 9.1093837015e-31
    k = 1.380649e-23
    chi = 13.5984 * _EV_ERG
    pref = (2.0 * math.pi * m_e * k * T_K / (h * h)) ** 1.5
    k_saha = (2.0 / n_m3) * pref * math.exp(-chi / (k * T_K))
    if k_saha <= 0.0:
        return 0.0
    x = (-k_saha + math.sqrt(k_saha * k_saha + 4.0 * k_saha)) / 2.0
    return max(0.0, min(1.0, x))


def _he_ionization_fraction(T_K: float) -> float:
    """He I → He II fraction (approximate equilibrium, Wolfire-style)."""
    if T_K <= 0.0:
        return 0.0
    t5 = T_K / 10_000.0
    return max(0.0, min(1.0, math.exp(-1.2 / max(t5, 0.05)) * t5**1.5))


def electron_density_cm3(
    T_K: float,
    n_H_cm3: float,
    *,
    y_he: float,
    x_photo_floor: float = 0.0,
    x_cap: float = 1.0,
    n_eff_saha_cm3: float = 0.35,
) -> float:
    x_saha = _saha_x_h(T_K, n_H_cm3, n_eff_cm3=n_eff_saha_cm3)
    x_h = min(x_cap, max(x_photo_floor, x_saha))
    x_he = _he_ionization_fraction(T_K)
    n_he = n_H_cm3 * y_he
    return n_H_cm3 * x_h + 2.0 * n_he * x_he


def heating_erg_cm3_s(
    n_H_cm3: float,
    n_e_cm3: float,
    *,
    zeta: float,
    g0: float,
    pe_eff: float,
) -> float:
    """Cosmic-ray + UV photoelectric heating (Wolfire/Draine order-of-magnitude, cgs)."""
    n_h = n_H_cm3
    x_e = n_e_cm3 / max(n_h, 1.0e-30)
    # CR: ~3.8e-25 erg cm^-3 s^-1 at zeta=1.8e-17, scaled; secondary ~2e-25 * x_e
    q_cr = (3.83e-23 + 2.03e-23 * min(x_e, 1.0)) * (zeta / 1.8e-17) * n_h
    q_pe = 1.39e-22 * g0 * pe_eff * n_h
    return q_cr + q_pe


def cooling_erg_cm3_s(T_K: float, n_H_cm3: float, n_e_cm3: float, *, scale: float = 1.0) -> float:
    """Major WNM channels: [C II], [O I], Lyman-α, free-free (cgs, T in K)."""
    if T_K <= 0.0:
        return 0.0
    n_h = n_H_cm3
    n_e = max(n_e_cm3, 1.0e-30)
    t = max(T_K, 100.0)
    # [C II] 158 μm — dominant WNM coolant (Wolfire 1995 fit shape)
    lam_cii = (
        3.5e-21
        * (1.0 + 1.0e-4 * n_e / math.sqrt(t))
        ** (-1.0)
        * math.exp(-92.0 / t)
        * n_e
        * n_h
    )
    lam_oi = 4.0e-22 * math.exp(-228.0 / t) * n_h
    lam_lya = 2.0e-21 * (t / 10_000.0) ** (-0.7) * n_e * n_h * min(1.0, n_e / n_h + 0.01)
    lam_ff = 1.42e-27 * math.sqrt(t) * n_e * n_e
    return scale * (lam_cii + lam_oi + lam_lya + lam_ff)


def wnm_equilibrium_T_K(n_H_cm3: float, constraints: dict[str, Any]) -> dict[str, float]:
    """Solve Λ(T)=Γ(T,n) by bisection on T; returns T and diagnostics."""
    p = _wnm_params(constraints)
    t_lo = p["T_min_K"]
    t_hi = p["T_max_K"]
    y_he = p["Y_He"]
    m = constraints.get("model_v1", {})
    x_photo = float(m.get("photoionization_fraction_floor", 0.08))
    x_cap = float(m.get("warm_neutral_ionization_max", 0.11))

    def n_e_at(t: float) -> float:
        return electron_density_cm3(
            t,
            n_H_cm3,
            y_he=y_he,
            x_photo_floor=x_photo,
            x_cap=x_cap,
            n_eff_saha_cm3=p["n_eff_saha_cm3"],
        )

    def residual(t: float) -> float:
        n_e = n_e_at(t)
        heat = heating_erg_cm3_s(
            n_H_cm3,
            n_e,
            zeta=p["zeta_H_s-1"],
            g0=p["habing_G0"],
            pe_eff=p["dust_pe_efficiency"],
        )
        cool = cooling_erg_cm3_s(t, n_H_cm3, n_e, scale=p["cooling_scale"])
        return heat - cool

    r_lo = residual(t_lo)
    r_hi = residual(t_hi)
    if r_lo * r_hi > 0.0:
        # scan log-T for sign change
        best_t = 0.5 * (t_lo + t_hi)
        best_abs = abs(residual(best_t))
        for i in range(120):
            t = t_lo * (t_hi / t_lo) ** (i / 119)
            r = abs(residual(t))
            if r < best_abs:
                best_abs = r
                best_t = t
        t_star = best_t
    else:
        for _ in range(80):
            mid = 0.5 * (t_lo + t_hi)
            if residual(t_lo) * residual(mid) <= 0.0:
                t_hi = mid
            else:
                t_lo = mid
        t_star = 0.5 * (t_lo + t_hi)

    n_e = n_e_at(t_star)
    heat = heating_erg_cm3_s(
        n_H_cm3,
        n_e,
        zeta=p["zeta_H_s-1"],
        g0=p["habing_G0"],
        pe_eff=p["dust_pe_efficiency"],
    )
    cool = cooling_erg_cm3_s(t_star, n_H_cm3, n_e, scale=p["cooling_scale"])
    return {
        "T_K": t_star,
        "n_e_cm3": n_e,
        "heating_erg_cm3_s": heat,
        "cooling_erg_cm3_s": cool,
        "balance_rel_err": abs(heat - cool) / max(heat, 1.0e-30),
        "habing_G0": p["habing_G0"],
        "zeta_H_s-1": p["zeta_H_s-1"],
    }
