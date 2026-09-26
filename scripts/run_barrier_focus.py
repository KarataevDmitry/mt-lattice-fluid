#!/usr/bin/env python3
"""§4.9 GPU leaf: wave interference vs vortex localization macro."""

from __future__ import annotations

import argparse
import json
import sys

import torch

from mt_ca.t_validation import wave_particle_macro


def main() -> int:
    parser = argparse.ArgumentParser(description="§4.9 wave↔particle macro test")
    parser.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    parser.add_argument("--size", type=int, default=512)
    parser.add_argument("--steps", type=int, default=256)
    parser.add_argument("--block", type=int, default=8)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    if args.device == "cuda" and not torch.cuda.is_available():
        print("CUDA unavailable — cpu", file=sys.stderr)
        args.device = "cpu"

    row = wave_particle_macro(args.size, args.steps, args.block, args.device)
    out = {"id": "T_wave_particle", **row}
    if args.json:
        print(json.dumps(out, indent=2))
    else:
        gpu = torch.cuda.get_device_name(0) if args.device == "cuda" else "cpu"
        print(f"device={args.device} ({gpu}) size={args.size} steps={args.steps}")
        status = "PASS" if row["ok"] else "FAIL"
        extra = {k: v for k, v in row.items() if k not in ("ok",)}
        print(f"T_wave_particle  {status}  {extra}")
        print("                 §4.9: interference (wave) vs soliton (particle)")
    return 0 if row["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
