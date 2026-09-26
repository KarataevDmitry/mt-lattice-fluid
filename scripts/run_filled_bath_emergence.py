#!/usr/bin/env python3
"""Dogfood: previous floor = full A5 vacuum ocean; no lonely C3 plant.

Uses ``mt_ca.app`` SSOT: habitat_boil vs habitat_frozen (+ optional birth_impulse).
"""

from __future__ import annotations

import argparse
import json

import torch

from mt_ca.app import RunSpec, get_scenario, run

def run_arm(
    *,
    scenario_id: str,
    size: int,
    steps: int,
    sample_every: int,
    device: str,
    block: int,
) -> dict:
    spec = RunSpec.from_id(
        scenario_id,
        ny=size,
        nx=size,
        steps=steps,
        device=device,
        block=block,
        sample_every=sample_every,
    )
    result = run(spec)
    out = result.to_dict()
    out["emerged_b"] = result.extra.get("emerged_b", False)
    out["contrast_grew"] = result.extra.get("contrast_grew", False)
    return out


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

    arms = [
        run_arm(
            scenario_id="habitat_boil",
            size=args.size,
            steps=args.steps,
            sample_every=args.sample_every,
            device=args.device,
            block=args.block,
        ),
        run_arm(
            scenario_id="habitat_frozen",
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
                scenario_id="birth_impulse",
                size=args.size,
                steps=args.steps,
                sample_every=args.sample_every,
                device=args.device,
                block=args.block,
            )
        )

    out = {
        "id": "filled_bath_emergence",
        "premise": "filled boiling ocean (VACUUM_BOIL); frozen VACUUM = control",
        "arms": arms,
    }
    if args.json:
        print(json.dumps(out, indent=2))
    else:
        gpu = torch.cuda.get_device_name(0) if args.device == "cuda" else "cpu"
        print(f"device={args.device} ({gpu}) size={args.size} steps={args.steps}")
        for arm in arms:
            print(
                f"  {arm['seed']:12} contrast={arm['samples'][-1]['contrast']:.2f} "
                f"emerged_b={arm['emerged_b']} drift={arm['norm_drift']:.4g}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
