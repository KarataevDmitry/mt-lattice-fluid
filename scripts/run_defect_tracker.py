#!/usr/bin/env python3
"""Track transient topological defects in 3+1 FCC: positions, motion, pairwise distance.

Probes whether defects are isolated, drifting, or colliding/merging.
"""

from __future__ import annotations

import argparse
import json
import math
import time
from typing import Any

import torch

from mt_ca.app import gate_b
from mt_ca.config import MConfig
from mt_ca.fixed_point import decode_spinor, encode_spinor
from mt_ca.seeds import SeedClass, boil_ocean_spinor_3d, make_seed
from mt_ca.simulator import LatticeFluidSimulator
from mt_ca.topology import gate_plane_z, unravel_peak_index, winding_channels, winding_nearest_int


def _apply_spinor_phase_wall(
    z: torch.Tensor,
    *,
    frac_bits: int,
    mod_bits: int,
    dtype: torch.dtype,
    delta_angle: float = 0.25,
) -> torch.Tensor:
    nz, ny, nx = z.shape[:3]
    xx = torch.arange(nx, device=z.device).view(1, 1, nx).expand(nz, ny, nx)
    mask = xx >= nx // 2
    factor = torch.exp(torch.tensor(1j * delta_angle, device=z.device, dtype=dtype))
    z2 = z.clone()
    z2[mask] = z2[mask] * factor
    f = encode_spinor(z2, frac_bits=frac_bits, mod_bits=mod_bits, gauge_fix=False)
    return decode_spinor(f, frac_bits=frac_bits, mod_bits=mod_bits).to(dtype)


def find_defect_peaks(
    z: torch.Tensor,
    *,
    top_k: int = 24,
    contour_radius: int = 2,
    merge_r: float = 6.0,
) -> list[dict[str, Any]]:
    """Defects at density peaks with |n_∂|≥¾ on the local readout plane."""
    from mt_ca.spinor import spinor_density

    rho = spinor_density(z)
    flat = rho.reshape(-1)
    k = min(top_k, flat.numel())
    _, idx = torch.topk(flat, k)
    ny, nx = rho.shape[-2:]
    margin = contour_radius + 1
    raw: list[dict[str, Any]] = []
    for i in range(k):
        iz, iy, ix = unravel_peak_index(rho, int(idx[i].item()))
        z_plane = gate_plane_z(z, iz) if iz is not None else z
        if iy < margin or ix < margin or iy >= ny - margin or ix >= nx - margin:
            continue
        ch = winding_channels(z_plane, center=(iy, ix), radius=contour_radius)
        w = ch["auto"]
        if w != w or abs(w) < 0.75:
            continue
        pos = (iz or 0, iy, ix)
        raw.append(
            {
                "iz": pos[0],
                "iy": pos[1],
                "ix": pos[2],
                "n": int(winding_nearest_int(w)),
                "w": round(float(w), 4),
                "rho": round(float(flat[idx[i]].item()), 4),
            }
        )
    # merge peaks within merge_r (same blob, multiple top-k hits)
    merged: list[dict[str, Any]] = []
    for d in raw:
        kept = True
        for m in merged:
            dist = math.dist((d["iz"], d["iy"], d["ix"]), (m["iz"], m["iy"], m["ix"]))
            if dist < merge_r:
                if d["rho"] > m["rho"]:
                    m.update(d)
                kept = False
                break
        if kept:
            merged.append(d)
    return merged


def _match_tracks(
    prev: list[dict[str, Any]],
    curr: list[dict[str, Any]],
    *,
    max_link: float = 12.0,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    """Greedy nearest-neighbor track linking."""
    linked: list[dict[str, Any]] = []
    births = list(curr)
    deaths = list(prev)
    used_curr: set[int] = set()
    for p in prev:
        best_j = -1
        best_d = max_link
        for j, c in enumerate(curr):
            if j in used_curr:
                continue
            d = math.dist((p["iz"], p["iy"], p["ix"]), (c["iz"], c["iy"], c["ix"]))
            if d < best_d:
                best_d = d
                best_j = j
        if best_j >= 0:
            c = curr[best_j]
            used_curr.add(best_j)
            births = [b for b in births if b is not c]
            deaths = [x for x in deaths if x is not p]
            linked.append(
                {
                    "from": (p["iz"], p["iy"], p["ix"]),
                    "to": (c["iz"], c["iy"], c["ix"]),
                    "disp_cells": round(best_d, 2),
                    "n_from": p["n"],
                    "n_to": c["n"],
                }
            )
    return linked, births, deaths


def pairwise_distances(defects: list[dict[str, Any]]) -> list[dict[str, float]]:
    out: list[dict[str, float]] = []
    for i in range(len(defects)):
        for j in range(i + 1, len(defects)):
            a, b = defects[i], defects[j]
            d = math.dist((a["iz"], a["iy"], a["ix"]), (b["iz"], b["iy"], b["ix"]))
            out.append({"i": i, "j": j, "dist_cells": round(d, 2), "ni": a["n"], "nj": b["n"]})
    return out


def track_run(
    *,
    sim: LatticeFluidSimulator,
    label: str,
    steps: int,
    sample_every: int,
    top_k: int,
) -> dict[str, Any]:
    frames: list[dict[str, Any]] = []
    prev_defects: list[dict[str, Any]] = []
    min_pair_dist_ever = float("inf")
    close_encounters: list[dict[str, Any]] = []
    done = 0
    while done <= steps:
        defects = find_defect_peaks(sim.z, top_k=top_k)
        pairs = pairwise_distances(defects)
        if pairs:
            dmin = min(p["dist_cells"] for p in pairs)
            min_pair_dist_ever = min(min_pair_dist_ever, dmin)
            for p in pairs:
                if p["dist_cells"] < 8.0:
                    close_encounters.append({"t": done, **p})
        links, births, deaths = _match_tracks(prev_defects, defects)
        gate = gate_b(sim.z)
        frames.append(
            {
                "t": done,
                "count": len(defects),
                "defects": defects,
                "pairs": pairs,
                "min_pair_dist": min(p["dist_cells"] for p in pairs) if pairs else None,
                "links": links,
                "births": len(births),
                "deaths": len(deaths),
                "gate_b": gate["b_hits_topk"],
                "winding_abs_max": gate["winding_abs_max"],
            }
        )
        if done >= steps:
            break
        chunk = min(sample_every, steps - done)
        sim.step(chunk)
        done += chunk
        prev_defects = defects

    max_disp = max((lnk["disp_cells"] for fr in frames for lnk in fr["links"]), default=0.0)
    return {
        "arm": label,
        "frames": frames,
        "min_pair_dist_ever": None if min_pair_dist_ever == float("inf") else round(min_pair_dist_ever, 2),
        "max_track_disp_per_sample": max_disp,
        "close_encounters_lt8": close_encounters[:20],
        "close_encounter_count": len(close_encounters),
    }


def setup_arm(
    arm: str,
    *,
    sim: LatticeFluidSimulator,
    cfg: MConfig,
    nz: int,
    ny: int,
    nx: int,
    settle: int,
) -> None:
    kw = {
        "device": sim.device,
        "dtype": sim.dtype,
        "mod_bits": cfg.mod_bits,
        "frac_bits": cfg.frac_bits,
        "phase_bits": cfg.phase_bits,
    }
    if arm == "plane_wave":
        z = make_seed(SeedClass.PLANE_WAVE, ny, nx, nz=nz, **kw)
        sim.set_field(z)
    elif arm == "vacuum_boil":
        sim.set_field(boil_ocean_spinor_3d(nz, ny, nx, **kw))
    elif arm == "boil_relax_wall":
        sim.set_field(boil_ocean_spinor_3d(nz, ny, nx, **kw))
        if settle > 0:
            sim.step(settle)
        sim.set_field(
            _apply_spinor_phase_wall(
                sim.z,
                frac_bits=cfg.frac_bits,
                mod_bits=cfg.mod_bits,
                dtype=sim.dtype,
            )
        )
    elif arm == "dual_wave":
        z1 = make_seed(SeedClass.PLANE_WAVE, ny, nx, nz=nz, **kw)
        z2 = make_seed(SeedClass.PLANE_WAVE, ny, nx, nz=nz, **kw)
        # offset second packet in x and flip phase for head-on-ish overlap
        z2 = torch.roll(z2, shifts=(0, 0, nx // 4), dims=(0, 1, 2))
        z2 = -z2
        ocean = boil_ocean_spinor_3d(nz, ny, nx, **kw)
        from mt_ca.fixed_point import encode_spinor, decode_spinor

        z = ocean + 0.5 * (z1 - ocean) + 0.5 * (z2 - ocean)
        f = encode_spinor(z, frac_bits=cfg.frac_bits, mod_bits=cfg.mod_bits, gauge_fix=False)
        sim.set_field(decode_spinor(f, frac_bits=cfg.frac_bits, mod_bits=cfg.mod_bits).to(sim.dtype))
    else:
        raise ValueError(arm)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--size", type=int, default=48)
    p.add_argument("--steps", type=int, default=512)
    p.add_argument("--sample-every", type=int, default=32)
    p.add_argument("--settle", type=int, default=256)
    p.add_argument("--top-k", type=int, default=24)
    p.add_argument(
        "--arm",
        choices=("plane_wave", "vacuum_boil", "boil_relax_wall", "dual_wave", "all"),
        default="all",
    )
    p.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    p.add_argument("--json", action="store_true")
    args = p.parse_args()
    if args.device == "cuda" and not torch.cuda.is_available():
        args.device = "cpu"

    arms = (
        ["plane_wave", "vacuum_boil", "boil_relax_wall", "dual_wave"]
        if args.arm == "all"
        else [args.arm]
    )
    cfg = MConfig.for_stencil("fcc")
    nz = ny = nx = args.size
    results: list[dict[str, Any]] = []
    t0 = time.perf_counter()
    for arm in arms:
        sim = LatticeFluidSimulator(ny, nx, cfg, nz=nz, device=args.device)
        setup_arm(arm, sim=sim, cfg=cfg, nz=nz, ny=ny, nx=nx, settle=args.settle)
        row = track_run(
            sim=sim,
            label=arm,
            steps=args.steps,
            sample_every=args.sample_every,
            top_k=args.top_k,
        )
        results.append(row)
        print(f"\n=== {arm} ===", flush=True)
        for fr in row["frames"]:
            if fr["count"] == 0 and fr["t"] > 0:
                continue
            pos = [
                f"({d['iz']},{d['iy']},{d['ix']})n{d['n']}"
                for d in fr["defects"][:6]
            ]
            mp = fr["min_pair_dist"]
            mp_s = f"{mp:.1f}" if mp is not None else "-"
            print(
                f"  t={fr['t']:4d} n_def={fr['count']} b={fr['gate_b']} "
                f"min_dist={mp_s} max_step_disp="
                f"{max((l['disp_cells'] for l in fr['links']), default=0):.1f} "
                f"births={fr['births']} deaths={fr['deaths']} {pos}",
                flush=True,
            )
        print(
            f"  min_pair_dist_ever={row['min_pair_dist_ever']} "
            f"close_lt8={row['close_encounter_count']}",
            flush=True,
        )

    out = {
        "id": "defect_tracker",
        "dims": f"{nz}x{ny}x{nx}",
        "steps": args.steps,
        "sample_every": args.sample_every,
        "seconds": round(time.perf_counter() - t0, 2),
        "arms": results,
        "note": "dist in lattice cells (hL); merge_r=6 for peak de-dup",
    }
    if args.json:
        print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
