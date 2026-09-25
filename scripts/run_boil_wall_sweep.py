#!/usr/bin/env python3
"""Sweep boil → settle → spinor half-space wall (META §3.2 dogfood).

Axes: settle_ticks × delta_angle × wall_axis (x|y|z).
Metrics: born_final, born_ever, first_born_t, b_final, max_b, min_pair_dist.
"""

from __future__ import annotations

import argparse
import itertools
import json
import sys
import time
from pathlib import Path
from typing import Any

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

import torch

from mt_ca.app import gate_b
from mt_ca.config import MConfig
from mt_ca.fixed_point import decode_spinor, encode_spinor
from mt_ca.seeds import boil_ocean_spinor_3d
from mt_ca.simulator import LatticeFluidSimulator

# Reuse defect peak finder from tracker (light import)
from run_defect_tracker import find_defect_peaks, pairwise_distances


def apply_half_space_wall(
    z: torch.Tensor,
    *,
    axis: str,
    frac_bits: int,
    mod_bits: int,
    dtype: torch.dtype,
    delta_angle: float,
) -> torch.Tensor:
    nz, ny, nx = z.shape[:3]
    z2 = z.clone()
    factor = torch.exp(torch.tensor(1j * delta_angle, device=z.device, dtype=dtype))
    if axis == "x":
        mask = torch.arange(nx, device=z.device).view(1, 1, nx) >= nx // 2
        mask = mask.expand(nz, ny, nx)
    elif axis == "y":
        mask = torch.arange(ny, device=z.device).view(1, ny, 1) >= ny // 2
        mask = mask.expand(nz, ny, nx)
    elif axis == "z":
        mask = torch.arange(nz, device=z.device).view(nz, 1, 1) >= nz // 2
        mask = mask.expand(nz, ny, nx)
    else:
        raise ValueError(axis)
    z2[mask] = z2[mask] * factor
    f = encode_spinor(z2, frac_bits=frac_bits, mod_bits=mod_bits, gauge_fix=False)
    return decode_spinor(f, frac_bits=frac_bits, mod_bits=mod_bits).to(dtype)


def run_config(
    *,
    sim: LatticeFluidSimulator,
    cfg: MConfig,
    nz: int,
    ny: int,
    nx: int,
    settle: int,
    delta_angle: float,
    axis: str,
    steps: int,
    sample_every: int,
) -> dict[str, Any]:
    kw = {
        "device": sim.device,
        "dtype": sim.dtype,
        "mod_bits": cfg.mod_bits,
        "frac_bits": cfg.frac_bits,
        "phase_bits": cfg.phase_bits,
    }
    sim.set_field(boil_ocean_spinor_3d(nz, ny, nx, **kw))
    if settle > 0:
        sim.step(settle)
    sim.set_field(
        apply_half_space_wall(
            sim.z,
            axis=axis,
            frac_bits=cfg.frac_bits,
            mod_bits=cfg.mod_bits,
            dtype=sim.dtype,
            delta_angle=delta_angle,
        )
    )
    g0 = gate_b(sim.z)
    born_ever = False
    first_born_t: int | None = None
    max_b = int(g0["b_hits_topk"])
    max_w = float(g0["winding_abs_max"])
    min_pair: float | None = None
    done = 0
    while done < steps:
        chunk = min(sample_every, steps - done)
        sim.step(chunk)
        done += chunk
        g = gate_b(sim.z)
        born_now = bool(g["passed"] and not g0["passed"])
        if born_now and not born_ever:
            first_born_t = done
        born_ever = born_ever or born_now
        max_b = max(max_b, int(g["b_hits_topk"]))
        max_w = max(max_w, float(g["winding_abs_max"]))
        defects = find_defect_peaks(sim.z, top_k=16)
        pairs = pairwise_distances(defects)
        if pairs:
            d = min(p["dist_cells"] for p in pairs)
            min_pair = d if min_pair is None else min(min_pair, d)
    g1 = gate_b(sim.z)
    born_final = bool(g1["passed"] and not g0["passed"])
    born_ever = born_ever or born_final
    if born_final and first_born_t is None:
        first_born_t = steps
    net_n = 0
    final_defects = find_defect_peaks(sim.z, top_k=16)
    for d in final_defects:
        net_n += d["n"]
    return {
        "settle": settle,
        "delta_angle": delta_angle,
        "axis": axis,
        "born_final": born_final,
        "born_ever": born_ever,
        "first_born_t": first_born_t,
        "b_final": int(g1["b_hits_topk"]),
        "b_max": max_b,
        "w_max": round(max_w, 4),
        "n_def_final": len(final_defects),
        "net_n_final": net_n,
        "min_pair_dist": round(min_pair, 2) if min_pair is not None else None,
        "contrast_final": round(g1["contrast"], 2),
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--size", type=int, default=48)
    p.add_argument("--steps", type=int, default=512)
    p.add_argument("--sample-every", type=int, default=32)
    p.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    p.add_argument(
        "--settles",
        default="0,128,256,512",
        help="comma-separated settle ticks before wall",
    )
    p.add_argument(
        "--angles",
        default="0.125,0.25,0.5,1.0",
        help="comma-separated delta_angle (rad)",
    )
    p.add_argument(
        "--axes",
        default="x,y,z",
        help="comma-separated wall axes",
    )
    p.add_argument("--json", action="store_true")
    p.add_argument("--top", type=int, default=12, help="print top N by score")
    args = p.parse_args()
    if args.device == "cuda" and not torch.cuda.is_available():
        args.device = "cpu"

    settles = [int(x) for x in args.settles.split(",") if x.strip()]
    angles = [float(x) for x in args.angles.split(",") if x.strip()]
    axes = [x.strip() for x in args.axes.split(",") if x.strip()]
    configs = list(itertools.product(settles, angles, axes))

    cfg = MConfig.for_stencil("fcc")
    nz = ny = nx = args.size
    sim = LatticeFluidSimulator(ny, nx, cfg, nz=nz, device=args.device)

    rows: list[dict[str, Any]] = []
    t0 = time.perf_counter()
    for i, (settle, angle, axis) in enumerate(configs):
        row = run_config(
            sim=sim,
            cfg=cfg,
            nz=nz,
            ny=ny,
            nx=nx,
            settle=settle,
            delta_angle=angle,
            axis=axis,
            steps=args.steps,
            sample_every=args.sample_every,
        )
        rows.append(row)
        print(
            f"{i + 1}/{len(configs)} settle={settle:3d} ang={angle:.3f} {axis} "
            f"born_f={int(row['born_final'])} ever={int(row['born_ever'])} "
            f"b_f={row['b_final']} b_max={row['b_max']} net_n={row['net_n_final']:+.0f} "
            f"@t{row['first_born_t']}",
            flush=True,
        )

    def score(r: dict[str, Any]) -> tuple:
        return (
            int(r["born_final"]),
            int(r["born_ever"]),
            r["b_final"],
            abs(r["net_n_final"]),
            r["b_max"],
        )

    ranked = sorted(rows, key=score, reverse=True)
    elapsed = time.perf_counter() - t0
    out = {
        "id": "boil_wall_sweep",
        "dims": f"{nz}x{ny}x{nx}",
        "steps": args.steps,
        "sample_every": args.sample_every,
        "configs": len(rows),
        "seconds": round(elapsed, 2),
        "rows": rows,
        "top": ranked[: args.top],
    }
    print("\n=== TOP (born_final, ever, b_final, |net_n|, b_max) ===", flush=True)
    for r in ranked[: args.top]:
        print(
            f"  settle={r['settle']:3d} ang={r['delta_angle']:.3f} axis={r['axis']} "
            f"born_f={int(r['born_final'])} b_f={r['b_final']} b_max={r['b_max']} "
            f"net_n={r['net_n_final']:+.0f} min_pair={r['min_pair_dist']} "
            f"contrast={r['contrast_final']}",
            flush=True,
        )
    if args.json:
        print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
