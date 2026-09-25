#!/usr/bin/env python3
"""Scan all SeedClass families for b birth / persistence (§5.0 · A10 dual channel).

Families (enum — few):
  VACUUM, VACUUM_BOIL — filled ocean (no planted topo)
  IMPULSE, PLANE_WAVE — energy on ocean
  VORTEX_P/M/N2 — planted matter (positive control: b at t=0)

Rejected elsewhere: free N_ring stripe ramp (run_seed_ring_scan).
Brick-offset sweep was one BOIL sub-family; this is the class switch.

Gate: b≥1 at density peak (|n_∂|≥¾), channels rel/u1/auto.
"""

from __future__ import annotations

import argparse
import json
import time

import torch

from mt_ca.app import RunSpec, gate_b, scenario_for_seed
from mt_ca.app.runner import apply_scenario
from mt_ca.config import MConfig
from mt_ca.seeds import SeedClass, make_seed
from mt_ca.simulator import LatticeFluidSimulator

# Seek birth here; vortices are planted controls.
BIRTH_FAMILIES = (
    SeedClass.VACUUM,
    SeedClass.VACUUM_BOIL,
    SeedClass.IMPULSE,
    SeedClass.PLANE_WAVE,
)
PLANTED_FAMILIES = (
    SeedClass.VORTEX_P,
    SeedClass.VORTEX_M,
    SeedClass.VORTEX_N2,
)
ALL_FAMILIES = BIRTH_FAMILIES + PLANTED_FAMILIES


def run_one(
    *,
    sim: LatticeFluidSimulator,
    seed: SeedClass,
    steps: int,
    nz: int | None = None,
) -> dict:
    if nz is None:
        apply_scenario(sim, scenario_for_seed(seed))
    else:
        z = make_seed(
            seed,
            sim.ny,
            sim.nx,
            nz=nz,
            device=sim.device,
            dtype=sim.dtype,
            mod_bits=sim.cfg.mod_bits,
            frac_bits=sim.cfg.frac_bits,
            phase_bits=sim.cfg.phase_bits,
        )
        sim.set_field(z)
    g0 = gate_b(sim.z)
    sim.step(steps)
    g1 = gate_b(sim.z)
    planted = seed in PLANTED_FAMILIES
    return {
        "seed": seed.value,
        "role": "planted_control" if planted else "birth_candidate",
        "gate0": g0,
        "gate1": g1,
        "passed": bool(g1["passed"]),
        "born": bool(g1["passed"] and not g0["passed"]),
        "persisted": bool(planted and g0["passed"] and g1["passed"]),
        "lost_plant": bool(planted and g0["passed"] and not g1["passed"]),
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--size", type=int, default=128)
    p.add_argument("--steps", type=int, default=1024)
    p.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    p.add_argument("--json-out", type=str, default="")
    p.add_argument("--json", action="store_true")
    p.add_argument(
        "--skip-planted",
        action="store_true",
        help="only birth candidates (skip VORTEX_* controls)",
    )
    p.add_argument(
        "--fcc",
        action="store_true",
        help="3+1 FCC stencil (canon §1.6); default 2+1 hex slice",
    )
    p.add_argument(
        "--nz",
        type=int,
        default=0,
        help="FCC depth (default: same as --size when --fcc)",
    )
    args = p.parse_args()
    if args.device == "cuda" and not torch.cuda.is_available():
        args.device = "cpu"

    families = BIRTH_FAMILIES if args.skip_planted else ALL_FAMILIES
    stencil = "fcc" if args.fcc else "hex"
    nz = (args.nz if args.nz > 0 else args.size) if args.fcc else None
    cfg = MConfig.for_stencil(stencil)
    sim = LatticeFluidSimulator(
        args.size,
        args.size,
        cfg,
        nz=nz,
        device=args.device,
    )

    rows: list[dict] = []
    t0 = time.perf_counter()
    for i, seed in enumerate(families):
        row = run_one(sim=sim, seed=seed, steps=args.steps, nz=nz)
        rows.append(row)
        print(
            f"{i + 1}/{len(families)} {seed.value}: "
            f"b0={int(row['gate0']['passed'])} b1={int(row['gate1']['passed'])} "
            f"born={int(row['born'])} contrast {row['gate0']['contrast']:.3g}→{row['gate1']['contrast']:.3g} "
            f"|n|_auto {row['gate1']['winding_abs_max']:.3g} "
            f"(rel {row['gate1']['winding_rel_max']:.3g} u1 {row['gate1']['winding_u1_max']:.3g})",
            flush=True,
        )

    elapsed = time.perf_counter() - t0
    born = [r for r in rows if r["born"]]
    hits = [r for r in rows if r["passed"]]
    persisted = [r for r in rows if r["persisted"]]
    lost = [r for r in rows if r["lost_plant"]]
    out = {
        "id": "seed_family_scan",
        "families": [s.value for s in families],
        "stencil": stencil,
        "dims": f"{nz}x{args.size}x{args.size}" if nz else f"{args.size}x{args.size}",
        "size": args.size,
        "nz": nz,
        "steps": args.steps,
        "device": args.device,
        "scanned": len(rows),
        "seconds": round(elapsed, 3),
        "hits_final_b": len(hits),
        "born": len(born),
        "planted_persisted": len(persisted),
        "planted_lost": len(lost),
        "born_keys": [r["seed"] for r in born],
        "hit_keys": [r["seed"] for r in hits],
        "persisted_keys": [r["seed"] for r in persisted],
        "lost_keys": [r["seed"] for r in lost],
        "rows": rows,
        "gate": "b≥1 at density peak (|n_∂|≥¾) dual rel/u1/auto",
    }
    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8") as fh:
            json.dump(out, fh, indent=2)
        print(f"wrote {args.json_out}")
    if args.json:
        slim = {k: out[k] for k in out if k != "rows"}
        print(json.dumps(slim, indent=2))
    else:
        gpu = torch.cuda.get_device_name(0) if args.device == "cuda" else "cpu"
        print(
            f"device={args.device} ({gpu}) stencil={stencil} dims={out['dims']} steps={args.steps} "
            f"scanned={out['scanned']} in {out['seconds']}s"
        )
        print(
            f"born={out['born']} hits_final={out['hits_final_b']} "
            f"planted_ok={out['planted_persisted']} planted_lost={out['planted_lost']}"
        )
        print(f"born_keys={out['born_keys']}")
        print(f"hit_keys={out['hit_keys']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
