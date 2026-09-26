#!/usr/bin/env python3
"""Boil ocean (ST) + homogeneous ISM blanket — T_МЗВ on full fill (no sky stripes)."""

from __future__ import annotations

import argparse
import json
import time
from typing import Any

import torch

from mt_ca.config import MConfig
from mt_ca.blanket import (
    apply_ism_blanket,
    blanket_distribution_report,
    load_ism_constraints,
    tau_uniform_ism_blanket,
)
from mt_ca.seeds import boil_ocean_spinor_3d
from mt_ca.simulator import LatticeFluidSimulator


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--size", type=int, default=48)
    p.add_argument("--block", type=int, default=4)
    p.add_argument("--thickness", type=int, default=6)
    p.add_argument("--settle", type=int, default=128)
    p.add_argument("--evolve", type=int, default=0)
    p.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    p.add_argument("--json", action="store_true")
    args = p.parse_args()
    if args.device == "cuda" and not torch.cuda.is_available():
        args.device = "cpu"

    constraints = load_ism_constraints()
    nz = args.size
    cfg = MConfig.for_stencil("fcc")
    sim = LatticeFluidSimulator(nz, nz, cfg, nz=nz, device=args.device)
    kw = {
        "device": sim.device,
        "dtype": sim.dtype,
        "mod_bits": cfg.mod_bits,
        "frac_bits": cfg.frac_bits,
        "phase_bits": cfg.phase_bits,
    }

    t0 = time.perf_counter()
    sim.set_field(boil_ocean_spinor_3d(nz, nz, nz, **kw))
    if args.settle > 0:
        sim.step(args.settle)
    z_ocean = sim.z.clone()

    tau = tau_uniform_ism_blanket(nz, nz, constraints, device=sim.device)
    z_blanket = apply_ism_blanket(
        sim.z,
        tau,
        thickness=args.thickness,
        frac_bits=cfg.frac_bits,
        mod_bits=cfg.mod_bits,
    )
    sim.set_field(z_blanket)
    if args.evolve > 0:
        sim.step(args.evolve)
        z_blanket = sim.z.clone()

    rep = blanket_distribution_report(
        z_ocean,
        z_blanket,
        thickness=args.thickness,
        block=args.block,
        tau_2d=tau,
        constraints=constraints,
    )
    tism = rep["T_ism"]
    q = tism["T_ism_map_K"]["quantiles"]
    t_eq = tism["derived_K"]["T_eq_WNM_balance"]
    wnm = tism.get("wnm_balance", {})
    t_obs = tism["observation_K"]["T_LIC_literature"]

    lines = [
        f"МЗВ однородна: τ={rep['tau_ism_uniform']:.4f} (полное заполнение, без полос).",
        f"T_eq WNM balance Γ=Λ: {t_eq:.0f} K "
        f"(G0={wnm.get('habing_G0', '?')}, n_e≈{wnm.get('n_e_cm3', 0):.4f} cm⁻³, "
        f"balance err {wnm.get('balance_rel_err', 0):.2e}).",
        f"Readout T_МЗВ: median={q['p50']:.0f} K, mean={tism['T_ism_map_K']['mean_K']:.0f} K "
        f"vs наблюдение LIC {t_obs:.0f} K (rel {tism['T_ism_map_K']['median_rel_err_vs_LIC_obs']:.2f}).",
        f"Разброс от ℬ: p05…p95 = {q['p05']:.0f}…{q['p95']:.0f} K.",
    ]

    out: dict[str, Any] = {
        "id": "ism_blanket_over_ocean",
        "seconds": round(time.perf_counter() - t0, 2),
        "dims": f"{nz}^3",
        "report": rep,
        "interpretation_ru": lines,
    }

    print("=== ISM blanket · homogeneous T_МЗВ ===", flush=True)
    for line in lines:
        print(f"  · {line}", flush=True)
    status = "PASS" if tism["ok_T_ISM_hypothesis"] else "FAIL"
    obs = "да" if tism.get("ok_match_LIC_observation") else "нет"
    print(f"{status}  T_ISM scale (10³ K)  ·  совпадение с LIC 7000 K: {obs}", flush=True)
    if args.json:
        print(json.dumps(out, indent=2))
    return 0 if tism["ok_T_ISM_hypothesis"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
