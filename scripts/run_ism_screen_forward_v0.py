#!/usr/bin/env python3
"""ISM screen forward v0: boil-wall ℬ contrast + ν-damp + τ screen vs external ISM anchors.

Not a full CMB or VLISM MHD solve — order-of-magnitude bridge (META §3.0.1 exploratory).
Constraints: data/ism_constraints_v0.json (LIC + Voyager PWS).
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import time
from pathlib import Path
from typing import Any

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

import torch

from mt_ca.config import MConfig
from mt_ca.ism_screen import evaluate_ism_screen_v0, load_ism_constraints
from mt_ca.simulator import LatticeFluidSimulator
from mt_ca.si_constants import SI, T_CMB_K_REF

from run_cmb_forward_envelope import calibrate_wall_row


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--size", type=int, default=32)
    p.add_argument("--block", type=int, default=4)
    p.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    p.add_argument("--settle", type=int, default=128)
    p.add_argument("--delta", type=float, default=0.125, dest="delta_angle")
    p.add_argument("--constraints", type=Path, default=None)
    p.add_argument("--json", action="store_true")
    args = p.parse_args()
    if args.device == "cuda" and not torch.cuda.is_available():
        args.device = "cpu"

    constraints = load_ism_constraints(args.constraints)
    bath = SI.vacuum_bath_row()
    bubble = SI.bubble_tick_row()

    nz = args.size
    cfg = MConfig.for_stencil("fcc")
    sim = LatticeFluidSimulator(nz, nz, cfg, nz=nz, device=args.device)

    t0 = time.perf_counter()
    cal = calibrate_wall_row(
        sim,
        cfg,
        nz=nz,
        settle=args.settle,
        delta_angle=args.delta_angle,
        axis="x",
        block=args.block,
        iz=nz // 2,
        nu_passes=[1, 4, 16, 64, 256],
    )
    elapsed = time.perf_counter() - t0

    eval_row = evaluate_ism_screen_v0(
        log10_T_M_over_CMB=float(bath["log10_T_M_bath_over_CMB"]),
        rms_rel_wall=float(cal["rms_rel"]),
        constraints=constraints,
    )

    out: dict[str, Any] = {
        "id": "ism_screen_forward_v0",
        "seconds": round(elapsed, 2),
        "dims": f"{nz}^3",
        "calibration": {
            "settle": cal["settle"],
            "delta_angle": cal["delta_angle"],
            "max_rel": cal["max_rel"],
            "rms_rel": cal["rms_rel"],
        },
        "si": {
            "T_M_bath_K": bath["T_M_bath_K"],
            "T_CMB_K": T_CMB_K_REF,
            "log10_T_M_over_CMB": bath["log10_T_M_bath_over_CMB"],
            "N_CMB_sci": bubble["N_CMB_sci"],
        },
        "screen_eval": eval_row,
        "constraints_schema": constraints.get("schema"),
        "interpretation": [
            f"M bath T~{bath['T_M_bath_K']:.2e} K vs CMB {T_CMB_K_REF} K — log10 gap {bath['log10_T_M_bath_over_CMB']:.2f}.",
            f"Measured wall rms/mean={cal['rms_rel']:.4e}; after ν+τ screen rms~{eval_row['rms_after_screen']:.4e} (target {eval_row['delta_T_over_T_target']:.0e}).",
            f"Required τ≈{eval_row['tau_required']:.2f} (applied {eval_row['tau_applied']:.2f}); toy n_e={eval_row['toy_n_e_cm3']:.3f} cm⁻³ vs Voyager band {eval_row['vlism_ne_range']}.",
            "Next: spatial τ(N_H) profile + acoustic growth to N_CMB (not wall-only ν extrapolation).",
        ],
    }

    print("=== ISM screen forward v0 ===", flush=True)
    for line in out["interpretation"]:
        print(f"  · {line}", flush=True)
    status = "PASS" if eval_row["ok"] else "FAIL"
    print(f"{status}  ISM_screen_v0  tau_req={eval_row['tau_required']:.2f}", flush=True)

    if args.json:
        print(json.dumps(out, indent=2))
    return 0 if eval_row["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
