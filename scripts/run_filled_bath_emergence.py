#!/usr/bin/env python3
"""Dogfood: previous floor = full A5 vacuum ocean; no lonely C3 plant.

Run whole-lattice VACUUM, watch whether matter-like (b) / density peaks
appear by themselves. Contrast arm: alone IMPULSE on same grid (not the claim).
"""

from __future__ import annotations

import argparse
import json
import time

import torch

from mt_ca.config import MConfig
from mt_ca.metrics import coarse_amplitude, field_amplitude, has_nan, norm_drift
from mt_ca.seeds import SeedClass
from mt_ca.simulator import LatticeFluidSimulator
from mt_ca.spinor import spinor_density
from mt_ca.topology import matter_occupancy_b, winding_number, winding_nearest_int


def _peak_stats(z: torch.Tensor, *, top_k: int = 16, contour_radius: int = 2) -> dict:
    rho = spinor_density(z)
    amp = field_amplitude(z)
    flat = rho.reshape(-1)
    k = min(top_k, flat.numel())
    vals, idx = torch.topk(flat, k)
    ny, nx = rho.shape
    windings: list[float] = []
    b_hits = 0
    for i in range(k):
        y = int(idx[i].item() // nx)
        x = int(idx[i].item() % nx)
        margin = contour_radius + 1
        if y < margin or x < margin or y >= ny - margin or x >= nx - margin:
            continue
        w = winding_number(z, center=(y, x), radius=contour_radius)
        if w == w:
            windings.append(float(w))
            if abs(w) >= 0.75:
                b_hits += min(1, abs(winding_nearest_int(w)))
    b_argmax = matter_occupancy_b(z, contour_radius=contour_radius)
    return {
        "rho_mean": float(rho.mean().item()),
        "rho_max": float(rho.max().item()),
        "rho_std": float(rho.std().item()),
        "amp_mean": float(amp.mean().item()),
        "amp_max": float(amp.max().item()),
        "contrast": float((rho.max() / (rho.mean() + 1e-30)).item()),
        "top_k": k,
        "b_hits_topk": int(b_hits),
        "b_argmax": int(b_argmax),
        "winding_topk_abs_max": max((abs(w) for w in windings), default=0.0),
        "winding_topk_mean_abs": (
            float(sum(abs(w) for w in windings) / len(windings)) if windings else 0.0
        ),
    }


def run_arm(
    *,
    seed: SeedClass,
    size: int,
    steps: int,
    sample_every: int,
    device: str,
    block: int,
) -> dict:
    sim = LatticeFluidSimulator(
        size, size, MConfig.for_stencil("hex"), device=device
    )
    sim.reset(seed)
    samples = []
    t0 = time.perf_counter()
    samples.append({"t": 0, **_peak_stats(sim.z), "norm": sim.norm()})
    done = 0
    while done < steps:
        chunk = min(sample_every, steps - done)
        sim.step(chunk)
        done += chunk
        samples.append({"t": done, **_peak_stats(sim.z), "norm": sim.norm()})
    elapsed = time.perf_counter() - t0
    coarse = coarse_amplitude(sim.z, block).cpu()
    return {
        "seed": seed.value,
        "size": size,
        "steps": steps,
        "device": device,
        "seconds": round(elapsed, 4),
        "steps_per_sec": round(steps / elapsed, 1) if elapsed > 0 else None,
        "norm0": sim.norm0,
        "norm_final": sim.norm(),
        "norm_drift": norm_drift(sim.norm0, sim.norm()),
        "nan": has_nan(sim.z),
        "coarse_amp_max": float(coarse.max().item()),
        "samples": samples,
        "emerged_b": any(s["b_hits_topk"] > 0 or s["b_argmax"] > 0 for s in samples[1:]),
        "contrast_grew": samples[-1]["contrast"] > samples[0]["contrast"] * 1.05,
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--size", type=int, default=256)
    p.add_argument("--steps", type=int, default=512)
    p.add_argument("--sample-every", type=int, default=64)
    p.add_argument("--block", type=int, default=8)
    p.add_argument(
        "--device", default="cuda" if torch.cuda.is_available() else "cpu"
    )
    p.add_argument("--with-alone", action="store_true", help="also run IMPULSE alone arm")
    p.add_argument("--json", action="store_true")
    args = p.parse_args()
    if args.device == "cuda" and not torch.cuda.is_available():
        args.device = "cpu"

    # Previous floor = whole-lattice boil; gauge-fixed VACUUM = frozen control.
    arms = [
        run_arm(
            seed=SeedClass.VACUUM_BOIL,
            size=args.size,
            steps=args.steps,
            sample_every=args.sample_every,
            device=args.device,
            block=args.block,
        ),
        run_arm(
            seed=SeedClass.VACUUM,
            size=args.size,
            steps=args.steps,
            sample_every=args.sample_every,
            device=args.device,
            block=args.block,
        ),
    ]
    if args.with_alone:
        arms.append(
            run_arm(
                seed=SeedClass.IMPULSE,
                size=args.size,
                steps=args.steps,
                sample_every=args.sample_every,
                device=args.device,
                block=args.block,
            )
        )

    out = {
        "id": "filled_bath_emergence",
        "premise": "previous floor = full VACUUM ocean; no planted C3",
        "arms": arms,
    }
    if args.json:
        print(json.dumps(out, indent=2))
    else:
        gpu = torch.cuda.get_device_name(0) if args.device == "cuda" else "cpu"
        print(f"device={args.device} ({gpu}) size={args.size} steps={args.steps}")
        for arm in arms:
            print("-" * 72)
            print(
                f"{arm['seed']:12} drift={arm['norm_drift']:.4e} "
                f"emerged_b={arm['emerged_b']} contrast_grew={arm['contrast_grew']} "
                f"{arm['steps_per_sec']} steps/s nan={arm['nan']}"
            )
            for s in arm["samples"]:
                print(
                    f"  t={s['t']:4d} contrast={s['contrast']:.3f} "
                    f"rho_max={s['rho_max']:.4e} b_topk={s['b_hits_topk']} "
                    f"b_argmax={s['b_argmax']} |w|_max={s['winding_topk_abs_max']:.3f}"
                )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
