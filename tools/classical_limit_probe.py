#!/usr/bin/env python3
"""§4 classical limit on T — coarse R, long waves (not ℓ_P→0 on M)."""
from __future__ import annotations

import argparse
import json

from mt_ca.t.hydro_limit import classical_limit_sweep_row


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--device", default="cpu")
    p.add_argument("--size", type=int, default=128)
    p.add_argument("--json", action="store_true")
    args = p.parse_args()
    row = classical_limit_sweep_row(device=args.device, size=args.size)
    if args.json:
        print(json.dumps(row, indent=2, default=float))
        return
    print(row["note"])
    print("checks_ok:", row["checks_ok"])
    print("gauss_err_R:", row["gauss_err_R"])
    print("phi_bz:", row["phi_bz"])
    print("bohm_scaling:", row["bohm_scaling"])
    print("madelung_long_wave:", row["madelung_long_wave"])


if __name__ == "__main__":
    main()
