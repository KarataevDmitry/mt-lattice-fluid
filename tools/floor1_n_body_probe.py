"""Four planckons on FCC NN chain — §5.0.3 N-body dogfood.

  python tools/floor1_n_body_probe.py
  python tools/floor1_n_body_probe.py --scenario chain4_alt_pm --tick
"""
from __future__ import annotations

import argparse
import json

import torch

from mt_ca.floor1_n_body import run_n_body_harness, run_n_body_scenario


def main() -> None:
    p = argparse.ArgumentParser(description="Floor1 N-body chain probe on VACUUM_BOIL")
    p.add_argument(
        "--scenario",
        choices=["chain4_alt_pm", "chain4_cluster_ppmm", "chain4_pp", "all"],
        default="all",
    )
    p.add_argument("--size", type=int, default=24)
    p.add_argument("--relaxation", type=int, default=12)
    p.add_argument("--n-max", type=int, default=72)
    p.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    p.add_argument(
        "--tick",
        action="store_true",
        help="per-tick probes (slow; event ticks)",
    )
    args = p.parse_args()
    tick_resolve = args.tick

    if args.scenario == "all":
        out = run_n_body_harness(
            size=args.size,
            relaxation=args.relaxation,
            n_max=args.n_max,
            device=args.device,
            tick_resolve=tick_resolve,
        )
        summary = {
            "device": args.device,
            "tick_resolve": tick_resolve,
            "checks_ok": out["checks_ok"],
            "pm_channel_opens": out["pm_channel_opens"],
            "harness_wall_s": round(out["harness_wall_s"], 3),
            "scenarios": {
                k: {
                    "scenario_ok": v["scenario_ok"],
                    "n_stable_final": v["n_stable_final"],
                    "first_pm_pair_tick": v["first_pm_pair_tick"],
                    "min_graph_dist_final": v["min_graph_dist_final"],
                    "wall_s": round(v["wall_s"], 3),
                }
                for k, v in out["scenarios"].items()
            },
        }
        print(json.dumps(summary, indent=2))
        return

    row = run_n_body_scenario(
        args.scenario,
        size=args.size,
        relaxation=args.relaxation,
        n_max=args.n_max,
        device=args.device,
        tick_resolve=tick_resolve,
    )
    print(
        json.dumps(
            {
                "scenario": row["scenario"],
                "scenario_ok": row["scenario_ok"],
                "n_stable_final": row["n_stable_final"],
                "first_pm_pair_tick": row["first_pm_pair_tick"],
                "min_graph_dist_initial": row["min_graph_dist_initial"],
                "min_graph_dist_final": row["min_graph_dist_final"],
                "ticks_sample": row["ticks_sample"],
                "wall_s": row["wall_s"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
