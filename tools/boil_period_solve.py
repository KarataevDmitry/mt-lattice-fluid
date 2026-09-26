#!/usr/bin/env python3
"""Solve period equations on exact g: symbolic FCC λ_st(k) + O∘g^T + CA cycle (small grids).

Usage:
  python tools/boil_period_solve.py
  python tools/boil_period_solve.py --size 8 --ticks 4096 --ca-cycle
"""
from __future__ import annotations

import argparse
import json

from mt_ca.analysis.period_solver import solve_ca_trajectory_period, solve_observable_period
from mt_ca.analysis.stencil_symbol import scan_fcc_low_k
from mt_ca.app.lab import open_lab
from mt_ca.instruments.catalog import InstrumentId


def run(
    *,
    size: int,
    settle: int,
    ticks: int,
    t_max: int,
    mse_threshold: float,
    ca_cycle: bool,
    max_k: int,
) -> dict:
    lab = open_lab("habitat_boil", size, device="cpu")
    shape = (lab.sim.nz, lab.sim.ny, lab.sim.nx)
    symbol = scan_fcc_low_k(shape, max_k=max_k)

    lab.step(settle)
    contrast: list[float] = []
    f_currs: list = []
    f_pasts: list = []

    for _ in range(ticks):
        z_p = lab.sim.z_past.clone() if lab.sim.z_past is not None else lab.sim.z.clone()
        if ca_cycle:
            assert lab.sim._f_curr is not None and lab.sim._f_past is not None
            f_currs.append(lab.sim._f_curr.detach().cpu().clone())
            f_pasts.append(lab.sim._f_past.detach().cpu().clone())
        lab.step(1)
        fld = lab.field_row(z_past=z_p)
        contrast.append(float(fld[InstrumentId.RHO_CONTRAST.value]))

    obs = solve_observable_period(contrast, t_max=t_max, mse_threshold=mse_threshold)
    out: dict = {
        **lab.meta,
        "settle": settle,
        "ticks": ticks,
        "symbolic_fcc_low_k": symbol[:16],
        "rho_contrast_period": obs,
    }
    if ca_cycle and f_currs:
        out["ca_cycle"] = solve_ca_trajectory_period(f_currs, f_pasts)
    out["human_solution"] = _human(out)
    return out


def _human(rep: dict) -> list[str]:
    lines: list[str] = []
    sym = rep.get("symbolic_fcc_low_k") or []
    if sym:
        top = sym[0]
        lines.append(
            f"Symbolica (FCC stencil): для k={top['k']} |λ_st|={top['abs_lambda_st']} — "
            "закрытая сумма 12 смещений на торе (не полная g, только Σ_N12)."
        )
    obs = rep.get("rho_contrast_period") or {}
    if obs.get("solved"):
        lines.append(
            f"Readout ρ_contrast: РЕШЕНО T={obs['period_T']} при mse≤{obs['mse_threshold']} "
            f"(mse={obs['period_mse']})."
        )
    else:
        lines.append(
            f"Readout ρ_contrast: за T≤{obs.get('t_max')} периода с mse≤{obs.get('mse_threshold')} "
            "НЕТ — уравнение O∘g^T=O для contrast в этом окне не выполняется."
        )
    ca = rep.get("ca_cycle")
    if ca:
        if ca.get("solved"):
            lines.append(
                f"CA (полная g): РЕШЕНО — пара состояния повторилась; cycle_period_T={ca['cycle_period_T']} "
                f"(тики {ca['cycle_start_tick']}→{ca['cycle_end_tick']})."
            )
        else:
            lines.append(
                f"CA: за {ca.get('trajectory_ticks')} тиков повтора пары не было — "
                "увеличь --ticks или уменьши --size для exact cycle search."
            )
    lines.append(
        "Полная g: сим = exact композиция; symbolica T(O,k,boil) для kick/floor/LUT — open, не «невозможна»."
    )
    return lines


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--size", type=int, default=16)
    p.add_argument("--settle", type=int, default=64)
    p.add_argument("--ticks", type=int, default=512)
    p.add_argument("--t-max", type=int, default=256)
    p.add_argument("--mse-threshold", type=float, default=1e-4)
    p.add_argument("--max-k", type=int, default=2)
    p.add_argument("--ca-cycle", action="store_true", help="Store pairs and solve exact cycle (memory!)")
    p.add_argument("--json", action="store_true")
    args = p.parse_args()
    rep = run(
        size=args.size,
        settle=args.settle,
        ticks=args.ticks,
        t_max=args.t_max,
        mse_threshold=args.mse_threshold,
        ca_cycle=args.ca_cycle,
        max_k=args.max_k,
    )
    if args.json:
        print(json.dumps(rep, indent=2))
        return
    print("grid:", rep.get("grid"), "scenario:", rep.get("scenario_id"))
    print("symbolic |λ_st| top:", rep["symbolic_fcc_low_k"][:3])
    print("contrast solve:", rep["rho_contrast_period"])
    if "ca_cycle" in rep:
        print("ca cycle:", rep["ca_cycle"])
    print("=== РЕШЕНИЕ ===")
    for line in rep["human_solution"]:
        print(line)


if __name__ == "__main__":
    main()
