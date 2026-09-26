"""WNM thermal balance — PS20 / Hybrid-CHIMES lineage tables (net Γ=Λ), no T_LIC in solver."""

from __future__ import annotations

import math
from typing import Any, Callable

from mt_ca.blanket.cooling_table import (
    n_e_cm3_from_table,
    net_erg_cm3_s,
    rates_erg_cm3_s,
    resolve_cooling_table_path,
)


def _wnm_params(constraints: dict[str, Any]) -> dict[str, float | str]:
    w = constraints.get("wnm_thermal", {})
    return {
        "T_min_K": float(w.get("T_min_K", 1500.0)),
        "T_max_K": float(w.get("T_max_K", 20000.0)),
        "P_th_over_k_cm3": float(w.get("P_th_over_k_cm3", 3500.0)),
        "equilibrium_mode": str(w.get("equilibrium_mode", "wnm_ridge")),
        "wnm_T_floor_K": float(w.get("wnm_T_floor_K", 4000.0)),
        "wnm_reference_log_nH": float(w.get("wnm_reference_log_nH", -2.85)),
    }


def _bisect_root(f: Callable[[float], float], t_lo: float, t_hi: float) -> float:
    r_lo = f(t_lo)
    r_hi = f(t_hi)
    if r_lo * r_hi > 0.0:
        return 0.5 * (t_lo + t_hi)
    for _ in range(64):
        mid = 0.5 * (t_lo + t_hi)
        if r_lo * f(mid) <= 0.0:
            t_hi = mid
        else:
            t_lo = mid
    return 0.5 * (t_lo + t_hi)


def _scan_wnm_roots(
    f: Callable[[float], float],
    *,
    t_lo: float,
    t_hi: float,
    t_floor: float,
    n_samples: int = 240,
) -> list[float]:
    roots: list[float] = []
    ts = [t_lo * (t_hi / t_lo) ** (k / (n_samples - 1)) for k in range(n_samples)]
    prev_t, prev_r = ts[0], f(ts[0])
    for t in ts[1:]:
        r = f(t)
        if prev_r * r <= 0.0 and t >= t_floor:
            roots.append(_bisect_root(f, prev_t, t))
        prev_t, prev_r = t, r
    return roots


def _pick_wnm_root(roots: list[float], *, t_floor: float) -> float | None:
    warm = [t for t in roots if t >= t_floor]
    if not warm:
        return None
    return max(warm)


def _thermal_n_for_balance(n_H_cm3: float, p: dict[str, float | str], table_path: Any) -> tuple[float, str]:
    mode = str(p["equilibrium_mode"])
    n_ref = math.pow(10.0, float(p["wnm_reference_log_nH"]))

    def roots_at(n: float) -> list[float]:
        return _scan_wnm_roots(
            lambda t: net_erg_cm3_s(n, t, table_path=table_path),
            t_lo=float(p["T_min_K"]),
            t_hi=float(p["T_max_K"]),
            t_floor=float(p["wnm_T_floor_K"]),
        )

    if mode == "at_nH":
        return n_H_cm3, "at_nH"
    if mode == "wnm_ridge":
        if _pick_wnm_root(roots_at(n_H_cm3), t_floor=float(p["wnm_T_floor_K"])) is not None:
            return n_H_cm3, "at_nH"
        return n_ref, "wnm_ridge_ref"
    if mode == "isobaric_wnm":
        p_th = float(p["P_th_over_k_cm3"])
        roots = _scan_wnm_roots(
            lambda t: net_erg_cm3_s(p_th / max(t, 1.0), t, table_path=table_path),
            t_lo=float(p["T_min_K"]),
            t_hi=float(p["T_max_K"]),
            t_floor=float(p["wnm_T_floor_K"]),
        )
        if _pick_wnm_root(roots, t_floor=float(p["wnm_T_floor_K"])) is not None:
            return p_th, "isobaric"  # sentinel: use isobaric lambda
        return n_ref, "wnm_ridge_ref"
    return n_H_cm3, "at_nH"


def wnm_equilibrium_T_K(n_H_cm3: float, constraints: dict[str, Any]) -> dict[str, float]:
    """Solve net heating−cooling=0 from tabulated PS20 / Hybrid-CHIMES lineage data."""
    p = _wnm_params(constraints)
    t_floor = float(p["wnm_T_floor_K"])
    table_path = resolve_cooling_table_path(constraints)
    n_bal, branch = _thermal_n_for_balance(n_H_cm3, p, table_path)

    if branch == "isobaric":
        p_th = float(p["P_th_over_k_cm3"])

        def f_iso(t: float) -> float:
            return net_erg_cm3_s(p_th / max(t, 1.0), t, table_path=table_path)

        roots = _scan_wnm_roots(
            f_iso,
            t_lo=float(p["T_min_K"]),
            t_hi=float(p["T_max_K"]),
            t_floor=t_floor,
        )
    else:
        roots = _scan_wnm_roots(
            lambda t: net_erg_cm3_s(n_bal, t, table_path=table_path),
            t_lo=float(p["T_min_K"]),
            t_hi=float(p["T_max_K"]),
            t_floor=t_floor,
        )

    t_star = _pick_wnm_root(roots, t_floor=t_floor)
    if t_star is None:
        raise RuntimeError(
            f"no WNM table root for n_H={n_H_cm3} branch={branch}; check cooling table / wnm_reference_log_nH"
        )

    heat, cool = rates_erg_cm3_s(n_bal, t_star, table_path=table_path)
    n_e = n_e_cm3_from_table(n_H_cm3, t_star, table_path=table_path)
    w = constraints.get("wnm_thermal", {})
    return {
        "T_K": t_star,
        "n_e_cm3": n_e,
        "heating_erg_cm3_s": heat,
        "cooling_erg_cm3_s": cool,
        "balance_rel_err": abs(heat - cool) / max(heat, 1.0e-30),
        "equilibrium_mode": str(p["equilibrium_mode"]),
        "thermal_balance_branch": branch,
        "n_thermal_balance_cm3": n_bal if branch != "isobaric" else float(p["P_th_over_k_cm3"]) / t_star,
        "cooling_table": str(table_path.name),
        "P_th_over_k_cm3": float(p["P_th_over_k_cm3"]),
        "wnm_reference_log_nH": float(p["wnm_reference_log_nH"]),
        "wnm_roots_K": roots[:8],
        "habing_G0": float(w.get("habing_G0", 1.0)),
        "zeta_H_s-1": float(w.get("zeta_H_s-1", 1.8e-17)),
    }


def equilibrium_T_wnm_K(n_H_cm3: float, constraints: dict[str, Any]) -> float:
    return float(wnm_equilibrium_T_K(n_H_cm3, constraints)["T_K"])


def heating_erg_cm3_s(n_H_cm3: float, n_e_cm3: float, **kwargs: Any) -> float:
    del n_e_cm3, kwargs
    raise NotImplementedError("use rates_erg_cm3_s via wnm_equilibrium_T_K (table SSOT)")


def cooling_erg_cm3_s(T_K: float, n_H_cm3: float, n_e_cm3: float, **kwargs: Any) -> float:
    del n_e_cm3, kwargs
    _, cool = rates_erg_cm3_s(n_H_cm3, T_K)
    return cool


def electron_density_cm3(T_K: float, n_H_cm3: float, *, constraints: dict[str, Any] | None = None, **kwargs: Any) -> float:
    del kwargs
    if constraints is None:
        return 0.08 * n_H_cm3
    return n_e_cm3_from_table(n_H_cm3, T_K, table_path=resolve_cooling_table_path(constraints))
