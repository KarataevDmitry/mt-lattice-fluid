#!/usr/bin/env python3
"""Linearized g on habitat_boil — Fourier-mode λ vs functional-period ring lags.

Usage:
  python tools/boil_linear_spectrum.py
  python tools/boil_linear_spectrum.py --size 16 --max-k 1
"""
from __future__ import annotations

import argparse
import json

from mt_ca.analysis.functional_period import scan_observable_period, shift_residual
from mt_ca.analysis.linearized_g import ring_period_candidates, scan_low_k_modes
from mt_ca.app.lab import open_lab
from mt_ca.instruments.catalog import InstrumentId


def run_boil_linear_spectrum(
    *,
    size: int = 16,
    settle: int = 64,
    track_ticks: int = 256,
    max_k: int = 1,
    eps_quanta: float = 2.0,
) -> dict:
    lab = open_lab("habitat_boil", size, device="cpu")
    lab.step(settle)

    z_curr = lab.sim.z.clone()
    z_past = lab.sim.z_past.clone() if lab.sim.z_past is not None else z_curr.clone()

    modes = scan_low_k_modes(z_curr, z_past, lab.cfg, max_k=max_k, eps_quanta=eps_quanta)
    ring = ring_period_candidates(lab.cfg)

    contrast: list[float] = []
    for _ in range(track_ticks):
        z_p = lab.sim.z_past.clone() if lab.sim.z_past is not None else lab.sim.z.clone()
        lab.step(1)
        fld = lab.field_row(z_past=z_p)
        contrast.append(float(fld[InstrumentId.RHO_CONTRAST.value]))

    scan = scan_observable_period(contrast, max_lag=min(128, track_ticks // 3))
    ring_mse = {T: round(shift_residual(contrast, T), 6) for T in ring if T < len(contrast)}

    return {
        **lab.meta,
        "settle": settle,
        "track_ticks": track_ticks,
        "max_k": max_k,
        "eps_quanta": eps_quanta,
        "modes": modes[:24],
        "model_ring_T": ring,
        "contrast_shift_mse_at_ring": ring_mse,
        "contrast_scan": {
            "best_shift_T": scan.get("best_shift_T"),
            "best_shift_mse_norm": scan.get("best_shift_mse_norm"),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--size", type=int, default=16)
    parser.add_argument("--settle", type=int, default=64)
    parser.add_argument("--track-ticks", type=int, default=256)
    parser.add_argument("--max-k", type=int, default=1)
    parser.add_argument("--eps-quanta", type=float, default=2.0)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    rep = run_boil_linear_spectrum(
        size=args.size,
        settle=args.settle,
        track_ticks=args.track_ticks,
        max_k=args.max_k,
        eps_quanta=args.eps_quanta,
    )
    if args.json:
        print(json.dumps(rep, indent=2))
        return
    print("lattice:", rep.get("dimension"), rep.get("grid"), "scenario:", rep.get("scenario_id"))
    print("settle:", rep["settle"], "max_k:", rep["max_k"], "eps_quanta:", rep["eps_quanta"])
    print("--- top |λ| modes (FD on z_curr, component 0) ---")
    for row in rep["modes"][:12]:
        t_note = row.get("inferred_T_ticks") if row.get("stable_mode") else "n/a (|λ|>1)"
        print(
            f"  k={row['k']}  |λ|={row['abs_lambda']}  log|λ|={row.get('log_abs_lambda')}  "
            f"phase={row['phase_rad']}  T~{t_note}"
        )
    print("model ring T:", rep["model_ring_T"])
    print("contrast shift_mse at ring T:", rep["contrast_shift_mse_at_ring"])
    print("contrast best_shift:", rep["contrast_scan"])


if __name__ == "__main__":
    main()
