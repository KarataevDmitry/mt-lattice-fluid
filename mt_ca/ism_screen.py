"""ISM screen v0 — T-layer contrast + VLISM toy constraints (META §3.0.1 exploratory)."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import yaml

_DATA_DIR = Path(__file__).resolve().parents[1] / "data"
_DEFAULT_YAML = _DATA_DIR / "ism_constraints_v0.yaml"
_DEFAULT_JSON = _DATA_DIR / "ism_constraints_v0.json"


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


def toy_ne_vlism_cm3(
    macro_fill: float,
    *,
    n_lic: float,
    n_vlism_target: float,
    fill_at_target: float = 1.0,
) -> float:
    """Linear toy: n_e = n_lic + (n_target - n_lic) * (fill / fill_at_target)."""
    if fill_at_target <= 0.0:
        return n_lic
    t = macro_fill / fill_at_target
    return n_lic + (n_vlism_target - n_lic) * t


def evaluate_ism_screen_v0(
    *,
    log10_T_M_over_CMB: float,
    rms_rel_wall: float | None = None,
    constraints: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Pure-math v0 gate for verify + script summary."""
    c = constraints or load_ism_constraints()
    scr = c["screen_v0"]
    pas = c["pass"]
    cmb = c["cmb_readout"]
    lic = c["lic"]
    v1 = c["vlism_voyager_v1"]

    rms0 = float(rms_rel_wall if rms_rel_wall is not None else scr["rms_rel_after_wall_typical"])
    nu = float(scr["nu_passes_typical"])
    alpha = float(scr["power_law_alpha_typical"])
    target = float(cmb["delta_T_over_T"])

    rms_nu = nu_damp_contrast(rms0, nu, alpha=alpha)
    tau_req = required_tau_for_target(rms_nu, target)
    tau_use = min(tau_req, float(scr["tau_column_max"]))
    rms_final = apply_tau_on_contrast(rms_nu, tau_use)

    fill = float(scr["macro_fill_for_vlism_match"])
    n_e = toy_ne_vlism_cm3(
        fill,
        n_lic=float(lic["n_H_cm3_nominal"]),
        n_vlism_target=float(v1["n_e_cm3_nominal"]),
        fill_at_target=fill,
    )
    ne_lo, ne_hi = v1["n_e_cm3_range"]

    ok_log = log10_T_M_over_CMB >= float(pas["log10_T_M_over_CMB_min"])
    ok_tau = tau_req <= float(pas["required_tau_max"])
    ok_ne = ne_lo <= n_e <= ne_hi
    ok_rms = rms_final <= target * 1.05 or tau_req <= float(scr["tau_column_max"])

    return {
        "id": "ISM_screen_v0",
        "log10_T_M_over_CMB": log10_T_M_over_CMB,
        "rms_rel_wall": rms0,
        "rms_after_nu": rms_nu,
        "nu_passes": nu,
        "alpha": alpha,
        "tau_required": tau_req,
        "tau_applied": tau_use,
        "rms_after_screen": rms_final,
        "delta_T_over_T_target": target,
        "toy_n_e_cm3": n_e,
        "vlism_ne_range": v1["n_e_cm3_range"],
        "ok_log10_gap": ok_log,
        "ok_tau_feasible": ok_tau,
        "ok_vlism_ne": ok_ne,
        "ok_rms_target": ok_rms,
        "ok": ok_log and ok_tau and ok_ne and ok_rms,
        "note": "v0: ν-damp + exp(-τ) on ℬ contrast; VLISM n_e toy — not full g forward",
    }
