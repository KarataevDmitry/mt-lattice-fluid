"""Column optical depth — shared by homogeneous blanket τ₀ and screen forward."""

from __future__ import annotations

from typing import Any


def r_au_to_pc(r_au: float, geometry: dict[str, Any]) -> float:
    return float(r_au) * float(geometry["AU_cm"]) / float(geometry["pc_cm"])


def cumulative_N_H_cm2(segments: list[dict[str, Any]], r_pc: float) -> float:
    """Line-of-sight column built from radial shells (fractional inner segment)."""
    total = 0.0
    for seg in segments:
        r0 = float(seg["r_start_pc"])
        r1 = float(seg["r_end_pc"])
        if r1 <= r0:
            continue
        n_col = float(seg["N_H_cm2"])
        if r_pc <= r0:
            continue
        if r_pc >= r1:
            total += n_col
        else:
            total += n_col * (r_pc - r0) / (r1 - r0)
    return total


def tau_from_column(N_H_cm2: float, sigma_eff_cm2: float) -> float:
    return max(0.0, float(N_H_cm2) * float(sigma_eff_cm2))


def column_tau_at_r(constraints: dict[str, Any], r_pc: float) -> dict[str, float]:
    col = constraints["column_screen"]
    sigma = float(col["sigma_eff_cm2"])
    n_h = cumulative_N_H_cm2(col["segments"], r_pc)
    return {"r_pc": r_pc, "N_H_cm2": n_h, "tau": tau_from_column(n_h, sigma)}
