#!/usr/bin/env python3
"""Verify kappa geometry + sim front speed (not doc hand-waving)."""

from __future__ import annotations

import math
import sys

import torch

from mt_ca.config import MConfig
from mt_ca.seeds import make_wave_packet
from mt_ca.simulator import LatticeFluidSimulator
from mt_ca.t_validation import coarse_grain, radial_front_radii


def analytic_diamond() -> None:
    print("=== ANALYTIC: L1 diamond |x|+|y| <= R, R = c0*t ===")
    for r in (1, 10, 100):
        r_axis = float(r)
        r_diag = r / math.sqrt(2.0)
        r_inscribed = r / math.sqrt(2.0)
        print(
            f"R={r}: axis k={r_axis/r:.4f}; diagonal k={r_diag/r:.4f}; "
            f"inscribed circle k={r_inscribed/r:.4f}"
        )
    print(f"WRONG if forgot sqrt: k=1/2 = {0.5:.4f}")
    print(f"inscribed circle: k=1/sqrt(2) = {1.0/math.sqrt(2.0):.4f}")


def light_cone_si() -> None:
    c = 299_792_458.0
    l_p = 1.616255e-35
    t_p = 5.391247e-44
    c0 = l_p / t_p
    print("\n=== LIGHT CONE SI ===")
    print(f"c0=lP/tP = {c0:.6e} m/s  (c = {c:.6e})")
    print(f"rel err = {abs(c0 - c) / c:.3e}")
    for name, dx in ("axis", l_p), ("diag", math.sqrt(2.0) * l_p):
        ds2 = c * c * t_p * t_p - dx * dx
        kind = "light-like" if abs(ds2) < 1e-60 else "space-like" if ds2 < 0 else "time-like"
        print(f"{name}: ds2 = {ds2:.3e} ({kind})")


def axis_extent(rho: torch.Tensor, cy: int, cx: int, thr_frac: float = 0.15) -> float:
    row = rho[cy, :]
    peak = float(row.max())
    if peak <= 1e-12:
        return float("nan")
    thr = thr_frac * peak
    xs = torch.where(row >= thr)[0]
    if len(xs) == 0:
        return float("nan")
    return float(max(abs(int(x) - cx) for x in xs))


def sim_kappa(device: str) -> None:
    print(f"\n=== SIM device={device} ===")
    size, block = 512, 8
    z0 = make_wave_packet(size, size, device=torch.device(device), amplitude=0.55, sigma=5.0)
    cy, cx = size // 2, size // 2

    for steps in (64, 128, 256):
        sim = LatticeFluidSimulator(size, size, MConfig(), device=device)
        sim.set_field(z0.clone())
        c0 = coarse_grain(sim.z, block)
        sim.step(steps)
        c1 = coarse_grain(sim.z, block)
        r0 = radial_front_radii(c0)
        r1 = radial_front_radii(c1)
        valid = torch.isfinite(r0) & torch.isfinite(r1) & (r1 > r0)
        speeds_coarse = (r1[valid] - r0[valid]) / steps
        mean_coarse = float(speeds_coarse.mean())
        mean_micro = mean_coarse * block
        cv = float(speeds_coarse.std(unbiased=False) / mean_coarse) if mean_coarse > 0 else float("inf")
        print(
            f"steps={steps}: kappa~{mean_micro:.4f} lP/tick  "
            f"(0.5={0.5:.4f}, 1/sqrt2={1/math.sqrt(2):.4f})  angle-CV={cv:.4f}"
        )

    sim = LatticeFluidSimulator(size, size, MConfig(), device=device)
    sim.set_field(z0.clone())
    ext0 = axis_extent(sim.z.abs(), cy, cx)
    steps = 256
    sim.step(steps)
    ext1 = axis_extent(sim.z.abs(), cy, cx)
    v_axis = (ext1 - ext0) / steps
    print(f"axis micro front speed = {v_axis:.4f} lP/tick (c0=1.0)")


def main() -> int:
    analytic_diamond()
    light_cone_si()
    device = "cuda" if torch.cuda.is_available() else "cpu"
    sim_kappa(device)
    return 0


if __name__ == "__main__":
    sys.exit(main())
