#!/usr/bin/env python3
"""Scan filled Heisenberg-brick boil ICs for birth of b (§5.0 · §6 bath).

Canon: no void — every cell is a brick (amplitude quantum + N_φ class).
Family: phase_class(y,x)=(dy·y + dx·x + offset) mod N_φ with |dy|=|dx|=1
so axis NN differ by one class ⇒ Δφ=Δφ_min. Enumerate offset∈0..N_φ−1 and
the four axis sign pairs. Rejected family: free N_ring plane-wave ramp.

Gate: b≥1 at density peak (|n_∂|≥¾).
"""

from __future__ import annotations

import argparse
import json
import time

import torch

from mt_ca.config import MConfig
from mt_ca.fixed_point import decode_spinor
from mt_ca.seeds import HV, vacuum_boil_fixed
from mt_ca.simulator import LatticeFluidSimulator
from mt_ca.spinor import spinor_density
from mt_ca.topology import matter_occupancy_b, winding_nearest_int, winding_number


def gate_b(z: torch.Tensor, *, top_k: int = 4, contour_radius: int = 2) -> dict:
    rho = spinor_density(z)
    flat = rho.reshape(-1)
    k = min(top_k, flat.numel())
    _, idx = torch.topk(flat, k)
    ny, nx = rho.shape
    b_hits = 0
    w_abs_max = 0.0
    margin = contour_radius + 1
    for i in range(k):
        y = int(idx[i].item() // nx)
        x = int(idx[i].item() % nx)
        if y < margin or x < margin or y >= ny - margin or x >= nx - margin:
            continue
        w = winding_number(z, center=(y, x), radius=contour_radius)
        if w == w:
            w_abs_max = max(w_abs_max, abs(float(w)))
            if abs(w) >= 0.75:
                b_hits += min(1, abs(winding_nearest_int(w)))
    b_argmax = matter_occupancy_b(z, contour_radius=contour_radius)
    return {
        "b_hits_topk": int(b_hits),
        "b_argmax": int(b_argmax),
        "passed": bool(b_hits > 0 or b_argmax > 0),
        "rho_max": float(rho.max().item()),
        "contrast": float((rho.max() / (rho.mean() + 1e-30)).item()),
        "winding_abs_max": w_abs_max,
    }


def run_one(
    *,
    sim: LatticeFluidSimulator,
    class_dy: int,
    class_dx: int,
    class_offset: int,
    size: int,
    steps: int,
    cfg: MConfig,
) -> dict:
    f = vacuum_boil_fixed(
        size,
        size,
        device=sim.device,
        mod_bits=cfg.mod_bits,
        frac_bits=cfg.frac_bits,
        phase_bits=cfg.phase_bits,
        n_phi=HV.N_phi,
        class_dy=class_dy,
        class_dx=class_dx,
        class_offset=class_offset,
    )
    z = decode_spinor(f, frac_bits=cfg.frac_bits, mod_bits=cfg.mod_bits).to(
        device=sim.device, dtype=sim.dtype
    )
    sim.set_field(z)
    g0 = gate_b(sim.z)
    sim.step(steps)
    g1 = gate_b(sim.z)
    return {
        "class_dy": int(class_dy),
        "class_dx": int(class_dx),
        "class_offset": int(class_offset),
        "gate0": g0,
        "gate1": g1,
        "passed": bool(g1["passed"]),
        "born": bool(g1["passed"] and not g0["passed"]),
    }


def brick_configs(n_phi: int) -> list[tuple[int, int, int]]:
    """Axis NN |Δclass|=1 on filled lattice: slopes ±1, all offsets."""
    slopes = ((1, 1), (1, -1), (-1, 1), (-1, -1))
    out: list[tuple[int, int, int]] = []
    for dy, dx in slopes:
        for off in range(n_phi):
            out.append((dy, dx, off))
    return out


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--size", type=int, default=128)
    p.add_argument("--steps", type=int, default=1024)
    p.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    p.add_argument("--json-out", type=str, default="")
    p.add_argument("--json", action="store_true")
    args = p.parse_args()
    if args.device == "cuda" and not torch.cuda.is_available():
        args.device = "cpu"

    n_phi = int(HV.N_phi)
    configs = brick_configs(n_phi)
    cfg = MConfig.for_stencil("hex")

    hits: list[dict] = []
    born: list[dict] = []
    sim = LatticeFluidSimulator(args.size, args.size, cfg, device=args.device)
    t0 = time.perf_counter()
    for i, (dy, dx, off) in enumerate(configs):
        row = run_one(
            sim=sim,
            class_dy=dy,
            class_dx=dx,
            class_offset=off,
            size=args.size,
            steps=args.steps,
            cfg=cfg,
        )
        if row["passed"]:
            hits.append(row)
        if row["born"]:
            born.append(row)
        if i % 13 == 0 or i == len(configs) - 1:
            print(
                f"scan {i + 1}/{len(configs)} hits={len(hits)} born={len(born)}",
                flush=True,
            )

    elapsed = time.perf_counter() - t0
    out = {
        "id": "seed_brick_scan",
        "N_phi": n_phi,
        "family": "filled_Heisenberg_brick_NN_dclass_1",
        "rejected_family": "N_ring_plane_wave_ramp",
        "size": args.size,
        "steps": args.steps,
        "device": args.device,
        "scanned": len(configs),
        "seconds": round(elapsed, 3),
        "hits": len(hits),
        "born": len(born),
        "hit_keys": [
            (h["class_dy"], h["class_dx"], h["class_offset"]) for h in hits
        ],
        "born_keys": [
            (h["class_dy"], h["class_dx"], h["class_offset"]) for h in born
        ],
        "hit_rows": hits,
        "born_rows": born,
        "gate": "b≥1 at density peak (|n_∂|≥¾)",
    }
    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8") as fh:
            json.dump(out, fh, indent=2)
        print(f"wrote {args.json_out}")
    if args.json:
        print(
            json.dumps(
                {k: out[k] for k in out if k not in ("hit_rows", "born_rows")},
                indent=2,
            )
        )
    else:
        gpu = torch.cuda.get_device_name(0) if args.device == "cuda" else "cpu"
        print(
            f"device={args.device} ({gpu}) N_phi={n_phi} size={args.size} "
            f"steps={args.steps} scanned={out['scanned']} in {out['seconds']}s"
        )
        print(f"hits(b≥1)={out['hits']} born(new b)={out['born']}")
        print(f"hit_keys={out['hit_keys'][:32]}{'...' if out['hits'] > 32 else ''}")
        print(f"born_keys={out['born_keys'][:32]}{'...' if out['born'] > 32 else ''}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
