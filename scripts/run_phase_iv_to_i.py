#!/usr/bin/env python3
"""Dogfood META §3.2 phase IV→I: ice + deterministic phase shift → birth?

Arms (2+1 hex or 3+1 FCC via --fcc):
  ice_uniform, ice_disk_d1, ice_wall_d1, ice_ripple, boil_control, boil_relax_wall

Tracks born_final / born_ever via **survey** readout (with --sample-every).
"""

from __future__ import annotations

import argparse
import json
import time
from typing import Any, Callable

import torch

from mt_ca.app import READOUT_SCHEMA, born_survey, dual_lanes, gates_at_z
from mt_ca.app.runner import apply_scenario
from mt_ca.app.scenario import get_scenario
from mt_ca.config import MConfig
from mt_ca.fixed_point import decode_spinor, encode_spinor
from mt_ca.seeds import (
    boil_ocean_spinor_3d,
    ice_ocean_spinor,
    ice_ocean_spinor_3d,
    make_seed,
    SeedClass,
)
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
    """Deterministic half-space spinor phase rotation."""
    if z.ndim == 4:
        nz, ny, nx = z.shape[:3]
        xx = torch.arange(nx, device=z.device).view(1, 1, nx)
        mask = (xx >= nx // 2) if half_plane_x else (xx < nx // 2)
        mask = mask.expand(nz, ny, nx)
    else:
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
    sample_every: int | None = None,
) -> dict[str, Any]:
    ic_fn()
    g0 = gates_at_z(sim.z, with_anchor=True)
    born_ever = False
    first_born_t: int | None = None
    samples: list[dict[str, Any]] = []
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
    lanes1 = dual_lanes(g1)
    return {
        "arm": label,
        "premise": premise,
        "readout_schema": READOUT_SCHEMA,
        "gate0": g0,
        "gate1": g1,
        "lanes1": lanes1,
        "passed_survey": bool(g1["passed_survey"]),
        "born": born_final,
        "born_ever": born_ever,
        "first_born_t": first_born_t,
        "contrast0": float(dual_lanes(g0)["survey"]["contrast"]),
        "contrast1": float(lanes1["survey"]["contrast"]),
        "samples": samples,
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--size", type=int, default=48)
    p.add_argument("--steps", type=int, default=1024)
    p.add_argument("--settle", type=int, default=512, help="boil_relax settle ticks")
    p.add_argument("--disk-radius", type=int, default=16)
    p.add_argument("--sample-every", type=int, default=64)
    p.add_argument("--fcc", action="store_true", help="3+1 FCC (canon §1.6)")
    p.add_argument("--nz", type=int, default=0)
    p.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    p.add_argument("--json-out", type=str, default="")
    p.add_argument("--json", action="store_true")
    args = p.parse_args()
    if args.device == "cuda" and not torch.cuda.is_available():
        args.device = "cpu"

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
    ny, nx = args.size, args.size
    kw = {
        "device": sim.device,
        "dtype": sim.dtype,
        "mod_bits": cfg.mod_bits,
        "frac_bits": cfg.frac_bits,
        "phase_bits": cfg.phase_bits,
    }
    sample_every = args.sample_every if args.sample_every > 0 else None
    disk_kind = "sphere" if args.fcc else "disk"

    def set_ice(**ice_kw: Any) -> None:
        if nz is not None:
            sim.set_field(ice_ocean_spinor_3d(nz, ny, nx, **kw, **ice_kw))
        else:
            sim.set_field(ice_ocean_spinor(ny, nx, **kw, **ice_kw))

    def set_boil() -> None:
        if nz is not None:
            sim.set_field(boil_ocean_spinor_3d(nz, ny, nx, **kw))
        else:
            apply_scenario(sim, get_scenario("habitat_boil"))

    arms_spec: list[tuple[str, str, Callable[[], None]]] = [
        ("ice_uniform", "phase III ice, no shift", lambda: set_ice()),
        (
            "ice_disk_d1",
            f"ice + {disk_kind} Δclass=1 r={args.disk_radius}",
            lambda: set_ice(shift_kind=disk_kind, radius=args.disk_radius, delta_class=1),
        ),
        (
            "ice_wall_d1",
            "ice + half-space class wall Δclass=1",
            lambda: set_ice(shift_kind="wall", delta_class=1),
        ),
        (
            "ice_ripple",
            "ice + minimal coherent k·r ripple",
            lambda: set_ice(shift_kind="ripple", delta_class=1),
        ),
        ("boil_control", "live VACUUM_BOIL", set_boil),
    ]

    results: list[dict[str, Any]] = []
    t0 = time.perf_counter()
    for i, (label, premise, ic_fn) in enumerate(arms_spec):
        row = run_arm(
            sim=sim,
            ic_fn=ic_fn,
            steps=args.steps,
            label=label,
            premise=premise,
            sample_every=sample_every,
        )
        results.append(row)
        ever_s = (
            f" ever={int(row['born_ever'])}@t{row['first_born_t']}"
            if sample_every
            else ""
        )
        sv0 = int(dual_lanes(row["gate0"])["survey"]["b"])
        sv1 = int(row["lanes1"]["survey"]["b"])
        print(
            f"{i + 1}/{len(arms_spec)} {label:16} "
            f"survey_b {sv0}→{sv1} born={int(row['born'])}{ever_s} "
            f"contrast {row['contrast0']:.2f}→{row['contrast1']:.1f}",
            flush=True,
        )

    set_boil()
    if args.settle > 0:
        sim.step(args.settle)
    z_wall = _apply_spinor_phase_wall(
        sim.z,
        frac_bits=cfg.frac_bits,
        mod_bits=cfg.mod_bits,
        dtype=sim.dtype,
    )
    sim.set_field(z_wall)
    relax_row = run_arm(
        sim=sim,
        ic_fn=lambda: None,
        steps=args.steps,
        label="boil_relax_wall",
        premise=f"boil settle={args.settle} then spinor half-space phase wall",
        sample_every=sample_every,
    )
    relax_row["settle_steps"] = args.settle
    results.append(relax_row)
    ever_s = (
        f" ever={int(relax_row['born_ever'])}@t{relax_row['first_born_t']}"
        if sample_every
        else ""
    )
    sv0 = int(dual_lanes(relax_row["gate0"])["survey"]["b"])
    sv1 = int(relax_row["lanes1"]["survey"]["b"])
    print(
        f"{len(arms_spec) + 1}/{len(arms_spec) + 1} boil_relax_wall  "
        f"survey_b {sv0}→{sv1} born={int(relax_row['born'])}{ever_s} "
        f"contrast {relax_row['contrast0']:.2f}→{relax_row['contrast1']:.1f}",
        flush=True,
    )

    elapsed = time.perf_counter() - t0
    born_final = [r["arm"] for r in results if r["born"]]
    born_ever = [r["arm"] for r in results if r["born_ever"]]
    out = {
        "id": "phase_iv_to_i",
        "readout_schema": READOUT_SCHEMA,
        "premise": "META §3.2: ice + deterministic shift → spontaneous b?",
        "stencil": stencil,
        "dims": f"{nz}x{args.size}x{args.size}" if nz else f"{args.size}x{args.size}",
        "size": args.size,
        "nz": nz,
        "steps": args.steps,
        "settle": args.settle,
        "sample_every": sample_every,
        "device": args.device,
        "seconds": round(elapsed, 3),
        "arms": results,
        "born_final_count": len(born_final),
        "born_final_arms": born_final,
        "born_ever_count": len(born_ever),
        "born_ever_arms": born_ever,
        "readout": "born_* = survey lane; anchor in lanes* for diagnostics",
    }
    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8") as fh:
            json.dump(out, fh, indent=2)
    if args.json:
        print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
