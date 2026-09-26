#!/usr/bin/env python3
"""Boiling ocean only — autocorrelation / FFT on instrument time series (no planckon).

Uses ``mt_ca.app.lab`` SSOT (``habitat_boil``, 3+1 FCC).

Usage:
  python tools/boil_ocean_periodicity.py
  python tools/boil_ocean_periodicity.py --ticks 1024
"""
from __future__ import annotations

import argparse
from collections import defaultdict

import torch

from mt_ca.app.lab import open_lab
from mt_ca.instruments.catalog import InstrumentId
from mt_ca.instruments.panel import sample_field, sample_site


def ac_peak_period(series: list[float], max_lag: int = 96) -> tuple[int | None, float]:
    x = torch.tensor(series, dtype=torch.float64)
    x = x - x.mean()
    std = float(x.std().item())
    if std < 1e-12:
        return None, 0.0
    x = x / std
    n = len(x)
    best_lag, best = None, -1.0
    for lag in range(2, min(max_lag, n // 3)):
        c = float((x[: n - lag] * x[lag:]).mean().item())
        if c > best:
            best, best_lag = c, lag
    return best_lag, best


def fft_peak_period(
    series: list[float], *, min_period: int = 2, max_period: int = 96
) -> tuple[int | None, float]:
    x = torch.tensor(series, dtype=torch.float64)
    x = x - x.mean()
    n = len(x)
    if n < 64:
        return None, 0.0
    spec = torch.fft.rfft(x)
    power = (spec.abs() ** 2)[1:]
    freqs = torch.fft.rfftfreq(n)[1:]
    best_period, best_p = None, -1.0
    for i, f in enumerate(freqs):
        ff = float(f)
        if ff <= 0:
            continue
        period = 1.0 / ff
        if period < min_period or period > max_period:
            continue
        p = float(power[i].item())
        if p > best_p:
            best_p, best_period = p, int(round(period))
    return best_period, best_p


def run_boil_ocean_periodicity(
    *,
    ticks: int = 1024,
    settle: int = 128,
    size: int = 32,
) -> dict:
    lab = open_lab("habitat_boil", size, device="cpu")
    lab.step(settle)

    cy = size // 2
    sites = lab.snap_sites(
        {
            "center": (cy, cy),
            "bath_a": (10, 10),
            "bath_b": (min(size - 4, 50), min(size - 4, 50)),
        }
    )
    series: dict[str, dict[str, list[float]]] = {
        name: defaultdict(list) for name in sites
    }
    contrast: list[float] = []

    for _t in range(ticks):
        z_p = lab.sim.z_past.clone() if lab.sim.z_past is not None else lab.sim.z.clone()
        lab.step(1)
        fld = lab.field_row(z_past=z_p)
        contrast.append(float(fld[InstrumentId.RHO_CONTRAST.value]))
        for name, site in sites.items():
            row = lab.site_row(site, z_past=z_p)
            series[name]["rho"].append(float(row[InstrumentId.RHO_FIELD.value]))
            series[name]["phi_kick"].append(float(row.get(InstrumentId.PHI_KICK_TICK.value) or 0))
            series[name]["n_E"].append(float(row[InstrumentId.N_E.value]))
            series[name]["Phi"].append(float(lab.projected_phi_at(site)))

    out_sites: dict[str, dict] = {}
    for name in sites:
        block: dict[str, dict] = {}
        for key in ("rho", "phi_kick", "n_E", "Phi"):
            s = series[name][key]
            ac_lag, ac = ac_peak_period(s)
            fft_p, fft_pow = fft_peak_period(s)
            block[key] = {
                "mean": round(sum(s) / len(s), 4),
                "ac_period": ac_lag,
                "ac": round(ac, 4),
                "fft_period": fft_p,
                "fft_power": round(fft_pow, 2),
            }
        out_sites[name] = block

    ac_lag, ac = ac_peak_period(contrast)
    fft_p, fft_pow = fft_peak_period(contrast)
    return {
        **lab.meta,
        "ticks": ticks,
        "settle": settle,
        "field_rho_contrast": {
            "ac_period": ac_lag,
            "ac": round(ac, 4),
            "fft_period": fft_p,
            "fft_power": round(fft_pow, 2),
        },
        "sites": out_sites,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ticks", type=int, default=1024)
    parser.add_argument("--settle", type=int, default=128)
    parser.add_argument("--size", type=int, default=32)
    args = parser.parse_args()
    rep = run_boil_ocean_periodicity(ticks=args.ticks, settle=args.settle, size=args.size)
    print("lattice:", rep.get("dimension"), rep.get("grid"), "scenario:", rep.get("scenario_id"))
    print("ticks:", rep["ticks"], "settle:", rep["settle"])
    print("field rho_contrast:", rep["field_rho_contrast"])
    for site, block in rep["sites"].items():
        print(f"--- {site} ---")
        for key, stats in block.items():
            print(
                f"  {key}: mean={stats['mean']}  ac_period={stats['ac_period']} ac={stats['ac']}  "
                f"fft_period={stats['fft_period']} power={stats['fft_power']}"
            )


if __name__ == "__main__":
    main()
