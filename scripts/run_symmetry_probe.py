#!/usr/bin/env python3
"""Run A14 discrete symmetry probes (§5.0.3 / A14)."""

from __future__ import annotations

import argparse
import json
import sys

import torch

from mt_ca.symmetry import symmetry_report


def main() -> int:
    parser = argparse.ArgumentParser(description="C/P/T symmetry probes on current g")
    parser.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    parser.add_argument("--size", type=int, default=128)
    parser.add_argument("--steps", type=int, default=64)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    if args.device == "cuda" and not torch.cuda.is_available():
        args.device = "cpu"

    row = symmetry_report(args.size, args.steps, args.device)
    if args.json:
        print(json.dumps(row, indent=2, default=str))
    else:
        gpu = torch.cuda.get_device_name(0) if args.device == "cuda" else "cpu"
        print(f"device={args.device} ({gpu}) size={args.size} steps={args.steps}")
        status = "PASS" if row["ok"] else "FAIL"
        print(f"{row['id']:16} {status}")
        for key in ("parity_seeds", "charge_seed", "CPT_unwind", "U1_vac", "chiral", "g_P_1step", "g_P_steps", "T_proxy", "annihilation"):
            print(f"  {key}: {row[key]}")
        print(f"  {row['note']}")
    return 0 if row["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
