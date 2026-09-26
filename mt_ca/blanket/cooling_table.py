"""Ploeckinger & Schaye (2020) / Hybrid-CHIMES lineage table lookup."""

from __future__ import annotations

import json
import math
from functools import lru_cache
from pathlib import Path
from typing import Any

_REPO_DATA = Path(__file__).resolve().parents[2] / "data"
_DEFAULT_JSON = _REPO_DATA / "wnm_cooling_ps20_fiducial_z0_v1.json"


@lru_cache(maxsize=4)
def _load_table(path: str) -> dict[str, Any]:
    with Path(path).open(encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError("invalid cooling table JSON")
    return data


def default_cooling_table_path() -> Path:
    return _DEFAULT_JSON


def resolve_cooling_table_path(constraints: dict[str, Any]) -> Path:
    w = constraints.get("wnm_thermal", {})
    rel = w.get("cooling_table_json", "wnm_cooling_ps20_fiducial_z0_v1.json")
    p = Path(rel)
    if not p.is_file():
        p = _REPO_DATA / rel
    if not p.is_file():
        raise FileNotFoundError(
            f"cooling table not found: {rel} — run scripts/build_wnm_cooling_table.py after placing HDF5 in data/_cache/"
        )
    return p


def _bracket(x: float, xs: list[float]) -> tuple[int, float, float]:
    if x <= xs[0]:
        return 0, xs[0], xs[1]
    for i in range(len(xs) - 1):
        if x <= xs[i + 1]:
            return i, xs[i], xs[i + 1]
    i = len(xs) - 2
    return i, xs[i], xs[i + 1]


def _lerp(x: float, x0: float, x1: float, y0: float, y1: float) -> float:
    if abs(x1 - x0) < 1.0e-30:
        return y0
    t = (x - x0) / (x1 - x0)
    return y0 + t * (y1 - y0)


def _bilinear(log_n: float, log_t: float, grid: list[list[float]], n_bins: list[float], t_bins: list[float]) -> float:
    i, ln0, ln1 = _bracket(log_n, n_bins)
    j, lt0, lt1 = _bracket(log_t, t_bins)
    v00 = grid[i][j]
    v10 = grid[i + 1][j]
    v01 = grid[i][j + 1]
    v11 = grid[i + 1][j + 1]
    v0 = _lerp(log_t, lt0, lt1, v00, v01)
    v1 = _lerp(log_t, lt0, lt1, v10, v11)
    return _lerp(log_n, ln0, ln1, v0, v1)


def log10_heat_cool_per_nh2(
    log_n_h: float,
    log_t: float,
    table: dict[str, Any],
) -> tuple[float, float]:
    n_bins: list[float] = table["log10_n_H"]
    t_bins: list[float] = table["log10_T"]
    lh = _bilinear(log_n_h, log_t, table["log10_heating_per_nH2"], n_bins, t_bins)
    lc = _bilinear(log_n_h, log_t, table["log10_cooling_per_nH2"], n_bins, t_bins)
    return lh, lc


def rates_erg_cm3_s(
    n_H_cm3: float,
    T_K: float,
    *,
    table_path: Path | None = None,
    table: dict[str, Any] | None = None,
) -> tuple[float, float]:
    tab = table or _load_table(str(table_path or _DEFAULT_JSON))
    log_n = math.log10(max(n_H_cm3, 1.0e-30))
    log_t = math.log10(max(T_K, 1.0))
    log_h, log_c = log10_heat_cool_per_nh2(log_n, log_t, tab)
    nh2 = n_H_cm3 * n_H_cm3
    return nh2 * math.pow(10.0, log_h), nh2 * math.pow(10.0, log_c)


def net_erg_cm3_s(
    n_H_cm3: float,
    T_K: float,
    *,
    table_path: Path | None = None,
    table: dict[str, Any] | None = None,
) -> float:
    heat, cool = rates_erg_cm3_s(n_H_cm3, T_K, table_path=table_path, table=table)
    return heat - cool


def n_e_cm3_from_table(
    n_H_cm3: float,
    T_K: float,
    *,
    table_path: Path | None = None,
    table: dict[str, Any] | None = None,
) -> float:
    tab = table or _load_table(str(table_path or _DEFAULT_JSON))
    if "log10_ne_over_nH" not in tab:
        return 0.08 * n_H_cm3
    log_n = math.log10(max(n_H_cm3, 1.0e-30))
    log_t = math.log10(max(T_K, 1.0))
    log_ne = _bilinear(log_n, log_t, tab["log10_ne_over_nH"], tab["log10_n_H"], tab["log10_T"])
    return n_H_cm3 * math.pow(10.0, log_ne)
