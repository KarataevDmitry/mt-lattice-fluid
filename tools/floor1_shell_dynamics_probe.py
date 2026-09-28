"""ρ_Θ shell activity on boil under g — §5.0.4-B dogfood.

  python tools/floor1_shell_dynamics_probe.py
  python tools/floor1_shell_dynamics_probe.py --tick
  python tools/floor1_shell_dynamics_probe.py --shell2-bump
"""
from __future__ import annotations

import argparse
import json

import torch

from mt_ca.floor1_shell_dynamics import run_shell_dynamics_on_boil


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--size", type=int, default=24)
    p.add_argument("--relaxation", type=int, default=12)
    p.add_argument("--n-max", type=int, default=72)
    p.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    p.add_argument("--tick", action="store_true")
    p.add_argument("--shell2-bump", action="store_true")
    args = p.parse_args()

    if args.shell2_bump:
        from mt_ca.floor1_shell_dynamics import run_shell_excitation_harness

        out = run_shell_excitation_harness(
            size=args.size,
            relaxation=args.relaxation,
            n_relax_after_bump=args.n_max,
            device=args.device,
        )
        print(json.dumps({"checks_ok": out["checks_ok"], "shell2_bump": out["shell2_bump"]}, indent=2))
        return

    row = run_shell_dynamics_on_boil(
        size=args.size,
        relaxation=args.relaxation,
        n_max=args.n_max,
        device=args.device,
        tick_resolve=args.tick,
    )
    print(
        json.dumps(
            {
                "device": args.device,
                "tick_resolve": args.tick,
                "scenario_ok": row["scenario_ok"],
                "core_stable_final": row["core_stable_final"],
                "shell1_active_final": row["shell1_active_final"],
                "shell1_excess_frac": row["shell1_excess_frac"],
                "shell2_excess_frac": row["shell2_excess_frac"],
                "shell3_excess_frac": row["shell3_excess_frac"],
                "max_sustained_shell2_without_shell1": row["max_sustained_shell2_without_shell1"],
                "wall_s": round(row["wall_s"], 3),
                "ticks_sample": row["ticks_sample"] if args.tick else row["ticks_sample"][-1:],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
