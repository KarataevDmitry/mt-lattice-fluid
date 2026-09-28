"""Two planckons on FCC boil — §5.0.3 dogfood (floor1-two-body-nn).

  python tools/floor1_two_body_probe.py
  python tools/floor1_two_body_probe.py --scenario pm_nn --size 24 --device cuda
"""
from __future__ import annotations

import argparse
import json

from mt_ca.floor1_two_body import run_two_body_harness, run_two_body_scenario


def _summary_row(row: dict) -> dict:
    return {
        "scenario": row["scenario"],
        "scenario_ok": row["scenario_ok"],
        "norm_ok": row["norm_ok"],
        "norm_drift_rel": row["norm_drift_rel"],
        "event_tick": row["event_tick"],
        "pair_annihilated_final": row["pair_annihilated_final"],
        "like_persisted_final": row["like_persisted_final"],
        "Q_final": (row["Q_a_final"], row["Q_b_final"]),
    }


def main() -> None:
    p = argparse.ArgumentParser(description="Floor1 two-body NN probe on VACUUM_BOIL")
    p.add_argument("--scenario", choices=["pp_nn", "mm_nn", "pm_nn", "pm_d2", "all"], default="all")
    p.add_argument("--size", type=int, default=24)
    p.add_argument("--relaxation", type=int, default=32)
    p.add_argument("--n-max", type=int, default=384)
    p.add_argument("--device", default="cuda" if __import__("torch").cuda.is_available() else "cpu")
    p.add_argument("--full-ticks", action="store_true")
    args = p.parse_args()

    if args.scenario == "all":
        out = run_two_body_harness(
            size=args.size,
            relaxation=args.relaxation,
            n_max=args.n_max,
            device=args.device,
        )
        slim = {
            k: _summary_row(v) for k, v in out["scenarios"].items()
        }
        print(
            json.dumps(
                {
                    "checks_ok": out["checks_ok"],
                    "annihilation_faster_than_like_like": out["annihilation_faster_than_like_like"],
                    "pm_event_tick": out["pm_event_tick"],
                    "scenarios": slim,
                },
                indent=2,
            )
        )
        return

    row = run_two_body_scenario(
        args.scenario,
        size=args.size,
        relaxation=args.relaxation,
        n_max=args.n_max,
        device=args.device,
    )
    if not args.full_ticks:
        row = {k: v for k, v in row.items() if k != "ticks"}
    print(json.dumps(row, indent=2))


if __name__ == "__main__":
    main()
