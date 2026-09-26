#!/usr/bin/env python3
"""Boiling ocean — functional period O∘g^T ≈ O and optional CA leapfrog match.

Discrete form of f(t+T)=f(t) on instrument series; CA bonus: exact Z_N[i] pair (f_curr,f_past).

Usage:
  python tools/boil_functional_period.py
  python tools/boil_functional_period.py --ticks 512 --ca-state
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict

from mt_ca.analysis.functional_period import scan_ca_leapfrog_period, scan_observable_period
from mt_ca.analysis.human_readout import functional_period_verdict, print_verdict
import torch

from mt_ca.app.lab import open_lab
from mt_ca.instruments.catalog import InstrumentId


def _collect(
    *,
    ticks: int,
    settle: int,
    size: int,
    store_ca: bool,
) -> tuple[dict, list[torch.Tensor] | None, list[torch.Tensor] | None]:

    lab = open_lab("habitat_boil", size, device="cpu")
    lab.step(settle)

    cy = size // 2
    sites = lab.snap_sites(
        {
            "center": (cy, cy),
            "bath_a": (10, 10),
        }
    )
    series: dict[str, dict[str, list[float]]] = {
        name: defaultdict(list) for name in sites
    }
    contrast: list[float] = []
    f_currs: list[torch.Tensor] | None = [] if store_ca else None
    f_pasts: list[torch.Tensor] | None = [] if store_ca else None

    for _t in range(ticks):
        z_p = lab.sim.z_past.clone() if lab.sim.z_past is not None else lab.sim.z.clone()
        if store_ca and f_currs is not None and f_pasts is not None:
            assert lab.sim._f_curr is not None and lab.sim._f_past is not None
            f_currs.append(lab.sim._f_curr.detach().cpu().clone())
            f_pasts.append(lab.sim._f_past.detach().cpu().clone())
        lab.step(1)
        fld = lab.field_row(z_past=z_p)
        contrast.append(float(fld[InstrumentId.RHO_CONTRAST.value]))
        for name, site in sites.items():
            row = lab.site_row(site, z_past=z_p)
            series[name]["rho"].append(float(row[InstrumentId.RHO_FIELD.value]))
            series[name]["phi_kick"].append(float(row.get(InstrumentId.PHI_KICK_TICK.value) or 0))
            series[name]["n_E"].append(float(row[InstrumentId.N_E.value]))
            series[name]["Phi"].append(float(lab.projected_phi_at(site)))

    observables: dict[str, dict] = {
        "field_rho_contrast": scan_observable_period(contrast, max_lag=min(128, ticks // 3)),
    }
    for name in sites:
        observables[name] = {
            key: scan_observable_period(vals, max_lag=min(128, ticks // 3))
            for key, vals in series[name].items()
        }

    meta = {**lab.meta, "ticks": ticks, "settle": settle, "observables": observables}
    return meta, f_currs, f_pasts


def run_boil_functional_period(
    *,
    ticks: int = 512,
    settle: int = 128,
    size: int = 32,
    store_ca: bool = False,
    max_lag: int = 128,
) -> dict:
    meta, f_currs, f_pasts = _collect(
        ticks=ticks, settle=settle, size=size, store_ca=store_ca
    )
    out: dict = dict(meta)
    if store_ca and f_currs and f_pasts:
        out["ca_leapfrog"] = scan_ca_leapfrog_period(
            f_currs, f_pasts, max_lag=min(max_lag, ticks // 3)
        )
    out["human_verdict"] = functional_period_verdict(out)
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ticks", type=int, default=512)
    parser.add_argument("--settle", type=int, default=128)
    parser.add_argument("--size", type=int, default=32)
    parser.add_argument("--max-lag", type=int, default=128)
    parser.add_argument(
        "--ca-state",
        action="store_true",
        help="Store Z_N[i] leapfrog pairs each tick (memory ~ O(ticks * grid))",
    )
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    rep = run_boil_functional_period(
        ticks=args.ticks,
        settle=args.settle,
        size=args.size,
        store_ca=args.ca_state,
        max_lag=args.max_lag,
    )
    if args.json:
        print(json.dumps(rep, indent=2))
        return
    print("lattice:", rep.get("dimension"), rep.get("grid"), "scenario:", rep.get("scenario_id"))
    print("ticks:", rep["ticks"], "settle:", rep["settle"])
    for block_name, block in rep["observables"].items():
        print(f"=== {block_name} ===")
        if isinstance(block, dict) and "best_shift_T" in block:
            _print_scan(block_name, block)
        else:
            for key, scan in block.items():
                _print_scan(f"{block_name}.{key}", scan)
    if "ca_leapfrog" in rep:
        ca = rep["ca_leapfrog"]
        print("=== CA leapfrog (Z_N[i]) ===")
        print("exact_period_T:", ca.get("exact_period_T"))
        for row in ca.get("lags_sample", [])[:16]:
            print(
                f"  T={row['T']:3d}  exact_rate={row['exact_match_rate']:.4f}  "
                f"mismatch={row['mean_mismatch']:.6f}"
            )
    print_verdict("ЧИТАТЬ ТАК", rep.get("human_verdict") or [])


def _print_scan(label: str, scan: dict) -> None:
    print(
        f"  {label}: best_shift_T={scan.get('best_shift_T')} "
        f"mse_norm={scan.get('best_shift_mse_norm')}"
    )
    ring = scan.get("model_ring_lags") or []
    if ring:
        parts = [f"T={r['T']} mse={r['shift_mse_norm']} ac={r['ac']}" for r in ring]
        print("    ring lags:", ", ".join(parts))
    sample = scan.get("lags_sample") or []
    head = ", ".join(f"T{r['T']}:{r['shift_mse_norm']}" for r in sample[:8])
    if head:
        print(f"    lags[1..]: {head}")


if __name__ == "__main__":
    main()
