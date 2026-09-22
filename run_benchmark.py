#!/usr/bin/env python3
"""Run M-layer validation sweep (4 topological seed classes)."""

from __future__ import annotations

import argparse
import json
import time

import torch

from mt_ca.config import MConfig
from mt_ca.metrics import coarse_amplitude, has_nan, norm_drift, ring_anisotropy
from mt_ca.seeds import SeedClass
from mt_ca.simulator import LatticeFluidSimulator


SEED_SUITE = (
    SeedClass.VACUUM,
    SeedClass.IMPULSE,
    SeedClass.PLANE_WAVE,
    SeedClass.VORTEX_P,
    SeedClass.VORTEX_M,
    SeedClass.VORTEX_N2,
)


def run_case(
    seed: SeedClass,
    size: int,
    steps: int,
    block: int,
    device: str,
) -> dict:
    sim = LatticeFluidSimulator(size, size, MConfig(), device=device)
    sim.reset(seed)
    norm0 = sim.norm0

    t0 = time.perf_counter()
    sim.step(steps)
    elapsed = time.perf_counter() - t0

    amp = sim.snapshot_amplitude()
    coarse = coarse_amplitude(sim.z, block).cpu()
    return {
        "seed": seed.value,
        "steps": steps,
        "size": size,
        "device": device,
        "seconds": round(elapsed, 4),
        "steps_per_sec": round(steps / elapsed, 1) if elapsed > 0 else None,
        "norm0": round(norm0, 6),
        "norm_final": round(sim.norm(), 6),
        "norm_drift": round(norm_drift(norm0, sim.norm()), 6),
        "nan": has_nan(sim.z),
        "anisotropy_coarse": round(ring_anisotropy(coarse), 4),
        "amp_mean": round(float(amp.mean()), 6),
        "amp_max": round(float(amp.max()), 6),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="M-layer lattice fluid benchmark")
    parser.add_argument("--size", type=int, default=512)
    parser.add_argument("--steps", type=int, default=512)
    parser.add_argument("--block", type=int, default=8)
    parser.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    results = [
        run_case(seed, args.size, args.steps, args.block, args.device)
        for seed in SEED_SUITE
    ]

    if args.json:
        print(json.dumps(results, indent=2))
        return

    print(f"device={args.device} size={args.size} steps={args.steps} block={args.block}")
    print("-" * 72)
    for row in results:
        print(
            f"{row['seed']:12}  drift={row['norm_drift']:.4f}  "
            f"ani={row['anisotropy_coarse']:.3f}  "
            f"amp_max={row['amp_max']:.4f}  "
            f"{row['steps_per_sec']:.0f} steps/s  nan={row['nan']}"
        )


if __name__ == "__main__":
    main()
