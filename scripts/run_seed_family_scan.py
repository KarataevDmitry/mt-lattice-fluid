#!/usr/bin/env python3
"""Scan all SeedClass families for b birth / persistence (§5.0 · A10 dual channel).

Families (enum — few):
  VACUUM, VACUUM_BOIL — filled ocean (no planted topo)
  IMPULSE, PLANE_WAVE — energy on ocean
  VORTEX_P/M/N2 — planted matter (positive control: b at t=0)

Rejected elsewhere: free N_ring stripe ramp (run_seed_ring_scan).
Brick-offset sweep was one BOIL sub-family; this is the class switch.

Readout instrument (``READOUT_SCHEMA``):
  **survey** — spontaneous birth hunt (local ρ maxima, torus-safe)
  **anchor** — lattice-center column (planted vortex persistence)
"""

from __future__ import annotations

import argparse
import json
import time

import torch

from mt_ca.app import (
    READOUT_SCHEMA,
    born_survey,
    dual_lanes,
    gates_at_z,
    planted_lost,
    planted_persisted,
    scenario_for_seed,
)
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
    sample_every: int | None = None,
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
    g0 = gates_at_z(sim.z, with_anchor=True)
    planted = seed in PLANTED_FAMILIES
    born_ever = False
    first_born_t: int | None = None
    samples: list[dict] = []
    if sample_every is not None and sample_every > 0:
        done = 0
        while done < steps:
            chunk = min(sample_every, steps - done)
            sim.step(chunk)
            done += chunk
            g = gates_at_z(sim.z, with_anchor=True)
            born_now = born_survey(g0, g)
            if born_now and not born_ever:
                first_born_t = done
            born_ever = born_ever or born_now
            row = dual_lanes(g)
            row["t"] = done
            row["born_survey"] = born_now
            samples.append(row)
        g1 = gates_at_z(sim.z, with_anchor=True)
    else:
        sim.step(steps)
        g1 = gates_at_z(sim.z, with_anchor=True)
    born_final = born_survey(g0, g1)
    born_ever = born_ever or born_final
    if born_final and first_born_t is None:
        first_born_t = steps
    lanes0 = dual_lanes(g0)
    lanes1 = dual_lanes(g1)
    return {
        "seed": seed.value,
        "role": "planted_control" if planted else "birth_candidate",
        "readout_schema": READOUT_SCHEMA,
        "gate0": g0,
        "gate1": g1,
        "lanes0": lanes0,
        "lanes1": lanes1,
        "passed_survey": bool(g1["passed_survey"]),
        "passed_anchor": bool(g1["passed_anchor"]),
        "born": born_final,
        "born_ever": born_ever,
        "first_born_t": first_born_t,
        "persisted": planted_persisted(g0, g1) if planted else False,
        "lost_plant": planted_lost(g0, g1) if planted else False,
        "samples": samples,
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
    p.add_argument(
        "--sample-every",
        type=int,
        default=0,
        help="if >0, sample gate every N ticks (born_ever, first_born_t)",
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

    sample_every = args.sample_every if args.sample_every > 0 else None
    rows: list[dict] = []
    t0 = time.perf_counter()
    for i, seed in enumerate(families):
        row = run_one(
            sim=sim,
            seed=seed,
            steps=args.steps,
            nz=nz,
            sample_every=sample_every,
        )
        rows.append(row)
        ever_s = f" ever={int(row['born_ever'])}@t{row['first_born_t']}" if sample_every else ""
        sv = row["lanes1"]["survey"]
        an = row["lanes1"]["anchor"]
        print(
            f"{i + 1}/{len(families)} {seed.value}: "
            f"survey={int(sv['passed'])} anchor={int(an['passed'])} "
            f"born={int(row['born'])}{ever_s} "
            f"contrast {row['lanes0']['survey']['contrast']:.3g}→{sv['contrast']:.3g} "
            f"|n|_auto {sv['w_max']:.3g} "
            f"(rel {sv['w_rel']:.3g} u1 {sv['w_u1']:.3g})",
            flush=True,
        )

    elapsed = time.perf_counter() - t0
    born = [r for r in rows if r["born"]]
    born_ever_rows = [r for r in rows if r["born_ever"]]
    hits = [r for r in rows if r["passed_survey"]]
    persisted = [r for r in rows if r["persisted"]]
    lost = [r for r in rows if r["lost_plant"]]
    out = {
        "id": "seed_family_scan",
        "readout_schema": READOUT_SCHEMA,
        "families": [s.value for s in families],
        "stencil": stencil,
        "dims": f"{nz}x{args.size}x{args.size}" if nz else f"{args.size}x{args.size}",
        "size": args.size,
        "nz": nz,
        "steps": args.steps,
        "sample_every": sample_every,
        "device": args.device,
        "scanned": len(rows),
        "seconds": round(elapsed, 3),
        "hits_final_survey": len(hits),
        "born": len(born),
        "born_ever": len(born_ever_rows),
        "born_ever_keys": [r["seed"] for r in born_ever_rows],
        "first_born_t": {r["seed"]: r["first_born_t"] for r in born_ever_rows},
        "planted_persisted": len(persisted),
        "planted_lost": len(lost),
        "born_keys": [r["seed"] for r in born],
        "hit_keys": [r["seed"] for r in hits],
        "persisted_keys": [r["seed"] for r in persisted],
        "lost_keys": [r["seed"] for r in lost],
        "rows": rows,
        "readout": "survey=birth; anchor=planted persistence (center column)",
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
            f"born_final={out['born']} born_ever={out['born_ever']} hits_survey={out['hits_final_survey']} "
            f"planted_ok={out['planted_persisted']} planted_lost={out['planted_lost']}"
        )
        print(f"born_keys={out['born_keys']}")
        if sample_every:
            print(f"born_ever_keys={out['born_ever_keys']} first_born_t={out['first_born_t']}")
        print(f"hit_keys={out['hit_keys']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
