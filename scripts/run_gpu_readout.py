#!/usr/bin/env python3
"""GPU/CPU readout: T1 isotropy, collision, vortex contour (MODEL §3.7.3)."""

from __future__ import annotations

import argparse
import json
import sys

import torch

from mt_ca.config import MConfig
from mt_ca.metrics import contour_axis_ratio, contour_radius_anisotropy, field_amplitude
from mt_ca.seeds import SeedClass
from mt_ca.simulator import LatticeFluidSimulator
from validate_mt import test_collision, test_isotropy


def vortex_contour_readout(size: int, steps: int, block: int, device: str) -> dict:
    sim = LatticeFluidSimulator(size, size, MConfig(stencil="hex"), device=device)
    sim.reset(SeedClass.VORTEX_P)
    amp0 = float(sim.snapshot_amplitude().max().item())
    sim.step(steps)
    micro = field_amplitude(sim.z)
    axis = contour_axis_ratio(micro, threshold=0.5)
    r_theta = contour_radius_anisotropy(micro, threshold=0.5)
    amp1 = float(micro.max().item())
    ok = axis == axis and axis < 1.05
    return {
        "id": "vortex_contour",
        "steps": steps,
        "stencil": "hex",
        "contour_axis_ratio": round(axis, 4) if axis == axis else None,
        "contour_r_anisotropy": round(r_theta, 4) if r_theta == r_theta else None,
        "amp_ratio": round(amp1 / (amp0 + 1e-12), 4),
        "ok": ok,
    }


def unitarity_smoke(size: int, steps: int, device: str) -> dict:
    sim = LatticeFluidSimulator(size, size, MConfig.for_stencil('hex'), device=device)
    sim.reset(SeedClass.PLANE_WAVE)
    n0 = sim.norm()
    sim.step(steps)
    drift = abs(sim.norm() - n0) / (n0 + 1e-12)
    return {"id": "unitarity", "norm_drift": round(drift, 6), "ok": drift < 1e-3}


def main() -> int:
    parser = argparse.ArgumentParser(description="M→T GPU readout bundle")
    parser.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    parser.add_argument("--size", type=int, default=512)
    parser.add_argument("--steps", type=int, default=256)
    parser.add_argument("--block", type=int, default=8)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    if args.device == "cuda" and not torch.cuda.is_available():
        print("CUDA unavailable — falling back to cpu", file=sys.stderr)
        args.device = "cpu"

    rows = [
        test_isotropy(args.size, args.steps, args.block, args.device),
        test_collision(args.size, args.steps, args.block, args.device),
        vortex_contour_readout(args.size, args.steps, args.block, args.device),
        unitarity_smoke(min(args.size, 256), args.steps, args.device),
    ]

    if args.json:
        print(json.dumps(rows, indent=2))
    else:
        print(f"device={args.device} size={args.size} steps={args.steps}")
        print("-" * 72)
        for row in rows:
            rid = row["id"]
            note = row.get("note")
            ok = row.get("ok")
            status = "PASS" if ok else "FAIL" if ok is False else ""
            extra = {k: v for k, v in row.items() if k not in ("id", "ok", "note")}
            print(f"{rid:20} {status:5} {extra}")
            if note:
                print(f"                     {note}")

    hard_fail = [r for r in rows if r.get("ok") is False]
    return 1 if hard_fail else 0


if __name__ == "__main__":
    sys.exit(main())
