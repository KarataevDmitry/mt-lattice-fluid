#!/usr/bin/env python3
"""Dogfood META §3.2 phase IV→I: ice + deterministic phase shift → birth?

Arms:
  ice_uniform      — synchronous ω (uniform class), no shift
  ice_disk_d1      — local +1 class bump in disk (domain nucleation)
  ice_wall_d1      — half-plane class wall
  ice_ripple       — minimal coherent k·r on ice (not PLANE_WAVE seed)
  boil_control     — live VACUUM_BOIL (known born=0)
  boil_relax_wall  — boil settle then spinor phase wall on result

Gate: b≥1 at density peak (|n_∂|≥¾), dual rel/u1/auto — same as family scan.
"""

from __future__ import annotations

import argparse
import json
import time
from typing import Any, Callable

import torch

from mt_ca.app import gate_b
from mt_ca.app.runner import apply_scenario
from mt_ca.app.scenario import get_scenario
from mt_ca.config import MConfig
from mt_ca.fixed_point import decode_spinor, encode_spinor
from mt_ca.seeds import ice_ocean_spinor
from mt_ca.simulator import LatticeFluidSimulator


def _apply_spinor_phase_wall(
    z: torch.Tensor,
    *,
    frac_bits: int,
    mod_bits: int,
    dtype: torch.dtype,
    half_plane_x: bool = True,
    delta_angle: float = 0.25,
) -> torch.Tensor:
    """Post-relax deterministic wall: rotate spinor phase on half the lattice."""
    ny, nx = z.shape[0], z.shape[1]
    xx = torch.arange(nx, device=z.device).view(1, nx)
    mask = (xx >= nx // 2) if half_plane_x else (xx < nx // 2)
    mask = mask.expand(ny, nx)
    factor = torch.exp(torch.tensor(1j * delta_angle, device=z.device, dtype=dtype))
    z2 = z.clone()
    z2[mask] = z2[mask] * factor
    f = encode_spinor(z2, frac_bits=frac_bits, mod_bits=mod_bits, gauge_fix=False)
    return decode_spinor(f, frac_bits=frac_bits, mod_bits=mod_bits).to(dtype)


def run_arm(
    *,
    sim: LatticeFluidSimulator,
    ic_fn: Callable[[], None],
    steps: int,
    label: str,
    premise: str,
) -> dict[str, Any]:
    ic_fn()
    g0 = gate_b(sim.z)
    sim.step(steps)
    g1 = gate_b(sim.z)
    return {
        "arm": label,
        "premise": premise,
        "gate0": g0,
        "gate1": g1,
        "passed": bool(g1["passed"]),
        "born": bool(g1["passed"] and not g0["passed"]),
        "contrast0": g0["contrast"],
        "contrast1": g1["contrast"],
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--size", type=int, default=128)
    p.add_argument("--steps", type=int, default=1024)
    p.add_argument("--settle", type=int, default=512, help="boil_relax settle ticks")
    p.add_argument("--disk-radius", type=int, default=16)
    p.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    p.add_argument("--json-out", type=str, default="")
    p.add_argument("--json", action="store_true")
    args = p.parse_args()
    if args.device == "cuda" and not torch.cuda.is_available():
        args.device = "cpu"

    cfg = MConfig.for_stencil("hex")
    sim = LatticeFluidSimulator(args.size, args.size, cfg, device=args.device)
    ny, nx = args.size, args.size
    kw = {
        "device": sim.device,
        "dtype": sim.dtype,
        "mod_bits": cfg.mod_bits,
        "frac_bits": cfg.frac_bits,
        "phase_bits": cfg.phase_bits,
    }

    def set_ice(**ice_kw: Any) -> None:
        sim.set_field(ice_ocean_spinor(ny, nx, **kw, **ice_kw))

    arms_spec: list[tuple[str, str, Callable[[], None]]] = [
        (
            "ice_uniform",
            "phase III ice, no shift",
            lambda: set_ice(),
        ),
        (
            "ice_disk_d1",
            f"ice + disk Δclass=1 r={args.disk_radius}",
            lambda: set_ice(shift_kind="disk", radius=args.disk_radius, delta_class=1),
        ),
        (
            "ice_disk_d2",
            f"ice + disk Δclass=2 r={args.disk_radius}",
            lambda: set_ice(shift_kind="disk", radius=args.disk_radius, delta_class=2),
        ),
        (
            "ice_wall_d1",
            "ice + half-plane class wall Δclass=1",
            lambda: set_ice(shift_kind="wall", delta_class=1),
        ),
        (
            "ice_ripple",
            "ice + minimal coherent k·r ripple (Δclass=1)",
            lambda: set_ice(shift_kind="ripple", delta_class=1),
        ),
        (
            "boil_control",
            "live VACUUM_BOIL (no shift)",
            lambda: apply_scenario(sim, get_scenario("habitat_boil")),
        ),
    ]

    results: list[dict[str, Any]] = []
    t0 = time.perf_counter()
    for i, (label, premise, ic_fn) in enumerate(arms_spec):
        row = run_arm(sim=sim, ic_fn=ic_fn, steps=args.steps, label=label, premise=premise)
        results.append(row)
        print(
            f"{i + 1}/{len(arms_spec)} {label:16} "
            f"b0={row['gate0']['b_hits_topk']} b1={row['gate1']['b_hits_topk']} "
            f"born={int(row['born'])} contrast {row['contrast0']:.2f}→{row['contrast1']:.1f}",
            flush=True,
        )

    # boil relax → spinor phase wall (post heat-death proxy)
    apply_scenario(sim, get_scenario("habitat_boil"))
    if args.settle > 0:
        sim.step(args.settle)
    z_wall = _apply_spinor_phase_wall(
        sim.z,
        frac_bits=cfg.frac_bits,
        mod_bits=cfg.mod_bits,
        dtype=sim.dtype,
    )
    sim.set_field(z_wall)
    g0 = gate_b(sim.z)
    sim.step(args.steps)
    g1 = gate_b(sim.z)
    relax_row = {
        "arm": "boil_relax_wall",
        "premise": f"boil settle={args.settle} then spinor half-plane phase wall",
        "gate0": g0,
        "gate1": g1,
        "passed": bool(g1["passed"]),
        "born": bool(g1["passed"] and not g0["passed"]),
        "contrast0": g0["contrast"],
        "contrast1": g1["contrast"],
        "settle_steps": args.settle,
    }
    results.append(relax_row)
    print(
        f"{len(arms_spec) + 1}/{len(arms_spec) + 1} boil_relax_wall  "
        f"b0={relax_row['gate0']['b_hits_topk']} b1={relax_row['gate1']['b_hits_topk']} "
        f"born={int(relax_row['born'])} contrast {relax_row['contrast0']:.2f}→{relax_row['contrast1']:.1f}",
        flush=True,
    )

    elapsed = time.perf_counter() - t0
    born_arms = [r["arm"] for r in results if r["born"]]
    out = {
        "id": "phase_iv_to_i",
        "premise": "META §3.2: ice + deterministic shift → spontaneous b?",
        "size": args.size,
        "steps": args.steps,
        "settle": args.settle,
        "device": args.device,
        "seconds": round(elapsed, 3),
        "arms": results,
        "born_count": len(born_arms),
        "born_arms": born_arms,
        "gate": "b≥1 at density peak (|n_∂|≥¾) dual rel/u1/auto",
    }
    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8") as fh:
            json.dump(out, fh, indent=2)
    if args.json:
        print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
