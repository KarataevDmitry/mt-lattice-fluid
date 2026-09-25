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

from mt_ca.app import BrickSpec, gate_b, brick_axis_configs
from mt_ca.app.habitat import HabitatPreset
from mt_ca.app.runner import apply_scenario
from mt_ca.app.scenario import ScenarioSpec
from mt_ca.config import MConfig
from mt_ca.seeds import HV, SeedClass
from mt_ca.simulator import LatticeFluidSimulator


def run_one(
    *,
    sim: LatticeFluidSimulator,
    brick: BrickSpec,
    steps: int,
) -> dict:
    scenario = ScenarioSpec(
        id="brick_boil",
        seed=SeedClass.VACUUM_BOIL,
        habitat=HabitatPreset.VACUUM_BOIL,
        brick=brick,
    )
    apply_scenario(sim, scenario)
    g0 = gate_b(sim.z)
    sim.step(steps)
    g1 = gate_b(sim.z)
    return {
        "class_dy": brick.class_dy,
        "class_dx": brick.class_dx,
        "class_offset": brick.class_offset,
        "gate0": g0,
        "gate1": g1,
        "passed": bool(g1["passed"]),
        "born": bool(g1["passed"] and not g0["passed"]),
    }


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

    configs = brick_axis_configs(HV.N_phi)
    cfg = MConfig.for_stencil("hex")

    hits: list[dict] = []
    born: list[dict] = []
    sim = LatticeFluidSimulator(args.size, args.size, cfg, device=args.device)
    t0 = time.perf_counter()
    for i, brick in enumerate(configs):
        row = run_one(sim=sim, brick=brick, steps=args.steps)
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
