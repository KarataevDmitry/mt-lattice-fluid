"""§5.0.3 M→T linkage: floor1 pm coarse + head-on T-stats."""
from __future__ import annotations

import argparse
import json

import torch

from mt_ca.annihilation_m_t_bundle import run_annihilation_m_t_bundle


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    p.add_argument("--pm-size", type=int, default=24)
    p.add_argument("--t-size", type=int, default=160)
    args = p.parse_args()
    row = run_annihilation_m_t_bundle(device=args.device, pm_size=args.pm_size, t_size=args.t_size)
    print(json.dumps(row, indent=2))


if __name__ == "__main__":
    main()
