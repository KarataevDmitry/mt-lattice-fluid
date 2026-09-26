#!/usr/bin/env python3
"""Dogfood: boil ocean (ST fabric) + ISM blanket — T_ISM map (LIC / VLISM), not CMB."""

from __future__ import annotations

import argparse
import json
import sys
import time
from typing import Any

import torch

from mt_ca.config import MConfig
from mt_ca.ism_blanket import apply_ism_blanket, blanket_distribution_report, tau_map_ism_blanket
from mt_ca.ism_screen import load_ism_constraints
from mt_ca.seeds import boil_ocean_spinor_3d
from mt_ca.simulator import LatticeFluidSimulator


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--size", type=int, default=48)
    p.add_argument("--block", type=int, default=4)
    p.add_argument("--thickness", type=int, default=6)
    p.add_argument("--settle", type=int, default=128)
    p.add_argument("--evolve", type=int, default=0)
    p.add_argument("--wind", default="x", choices=("x", "y"))
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

    tau, path = tau_map_ism_blanket(
        nz,
        nz,
        constraints,
        device=sim.device,
        dtype=sim.dtype,
        wind_axis=args.wind,
    )
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
        path_2d=path,
        constraints=constraints,
    )
    elapsed = time.perf_counter() - t0
    tism = rep["T_ism"]
    q = tism["T_ism_map_K"]["quantiles"]
    reg = tism["regimes"]
    anc = tism["anchors_K"]

    lines = [
        f"T_ISM на одеяле: mean={tism['T_ism_map_K']['mean_K']:.0f} K "
        f"(log10≈{tism['T_ism_map_K']['log10_mean']:.2f}), "
        f"полоса {q['min']:.0f}…{q['max']:.0f} K.",
        f"Небо LIC (path≤{constraints['pass_blanket']['lic_sky_path_max']}): "
        f"median {reg['lic_sky_median_K']:.0f} K vs якорь {anc['T_LIC_nominal']:.0f} K "
        f"(rel err {reg['lic_sky_rel_err']:.2f}).",
        f"Небо VLISM (path≥{constraints['pass_blanket']['vlism_sky_path_min']}): "
        f"median {reg['vlism_sky_median_K']:.0f} K vs ref {anc['T_VLISM_ref']:.0f} K "
        f"(rel err {reg['vlism_sky_rel_err']:.2f}).",
        "Не T_CMB и не T_M_bath — macro readout МЗВ на ткани океана.",
    ]

    out: dict[str, Any] = {
        "id": "ism_blanket_over_ocean",
        "seconds": round(elapsed, 2),
        "dims": f"{nz}^3",
        "report": rep,
        "interpretation_ru": lines,
    }

    print("=== ISM blanket · T_ISM readout ===", flush=True)
    for line in lines:
        print(f"  · {line}", flush=True)
    status = "PASS" if tism["ok_T_ISM_hypothesis"] else "FAIL"
    print(f"{status}  T_ISM_hypothesis", flush=True)

    if args.json:
        print(json.dumps(out, indent=2))
    return 0 if tism["ok_T_ISM_hypothesis"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
