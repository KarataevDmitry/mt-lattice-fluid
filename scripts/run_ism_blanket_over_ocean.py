#!/usr/bin/env python3
"""Dogfood: settled boil ocean + ISM blanket (ММС) on top — readout distribution on the blanket.

Vertical picture (z up):
  bottom … ocean (vacuum_boil, settled)
  top K layers — «одеяло»: same ℬ as interface, screened by spatial τ(n_H, wind).
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

import torch

from mt_ca.config import MConfig
from mt_ca.ism_blanket import (
    apply_ism_blanket,
    blanket_distribution_report,
    tau_map_ism_blanket,
)
from mt_ca.ism_screen import load_ism_constraints
from mt_ca.seeds import boil_ocean_spinor_3d
from mt_ca.simulator import LatticeFluidSimulator


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--size", type=int, default=48)
    p.add_argument("--block", type=int, default=4)
    p.add_argument("--thickness", type=int, default=6, help="ISM blanket layers (z)")
    p.add_argument("--settle", type=int, default=128)
    p.add_argument("--evolve", type=int, default=0, help="CA steps after blanket")
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

    tau = tau_map_ism_blanket(
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
    )
    elapsed = time.perf_counter() - t0

    o = rep["ocean_before_blanket"]
    u = rep["interface_after_blanket"]
    b = rep["blanket_top"]
    lines = [
        f"Океан до одеяла (интерфейс z={rep['iz_interface']}): |Φ| mean={o['mean']:.4f}, "
        f"рябь rms/mean={o['rms_rel']:.4f}.",
        f"Тот же интерфейс после установки одеяла: mean={u['mean']:.4f} (не трогаем).",
        f"Верх одеяла ММС (z={rep['iz_blanket_top']}): mean={b['mean']:.4f}, rms/mean={b['rms_rel']:.4f} "
        f"— средний уровень ×{rep['contrast_ratio_mean']:.3f}, рябь "
        f"{'сглажена' if rep['blanket_smooths'] else 'как у океана'}.",
        f"τ на одеяле: min={rep['tau_min']:.3f}, max={rep['tau_max']:.1f} "
        f"(ветер {args.wind}: тонко у «Солнца», толще по ветру).",
        "Это распределение на readout-слое T (|Φ| coarse), не карта n_e Voyager.",
    ]
    if args.evolve > 0:
        lines.append(f"После {args.evolve} тактов КА одеяло слегка смешалось с океаном (см. json).")

    out: dict[str, Any] = {
        "id": "ism_blanket_over_ocean",
        "seconds": round(elapsed, 2),
        "dims": f"{nz}^3",
        "blanket_thickness": args.thickness,
        "settle": args.settle,
        "evolve": args.evolve,
        "wind_axis": args.wind,
        "report": rep,
        "interpretation_ru": lines,
    }

    print("=== ISM blanket over boil ocean ===", flush=True)
    for line in lines:
        print(f"  · {line}", flush=True)

    if args.json:
        print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
