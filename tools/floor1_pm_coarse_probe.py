"""pm_nn coarse dipole proxy on boil — §5.0.3 M→T bridge."""
from __future__ import annotations

import argparse
import json

import torch

from mt_ca.floor1_pm_coarse_t import run_pm_coarse_dipole_probe


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--size", type=int, default=24)
    p.add_argument("--relaxation", type=int, default=12)
    p.add_argument("--n-max", type=int, default=72)
    p.add_argument("--block", type=int, default=4)
    p.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    args = p.parse_args()
    row = run_pm_coarse_dipole_probe(
        size=args.size,
        relaxation=args.relaxation,
        n_max=args.n_max,
        block=args.block,
        device=args.device,
    )
    print(json.dumps({k: row[k] for k in row if k != "note"}, indent=2))
    print("note:", row["note"])


if __name__ == "__main__":
    main()
