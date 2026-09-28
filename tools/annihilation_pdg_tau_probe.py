"""PDG para-Ps τ bridge — QED, ladder, vs head-on τ_M."""
from __future__ import annotations

import argparse
import json

from mt_ca.annihilation_pdg_tau import run_annihilation_pdg_tau_bridge, run_annihilation_pdg_tau_strict


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--device", default="cpu")
    p.add_argument("--strict", action="store_true")
    args = p.parse_args()
    row = (
        run_annihilation_pdg_tau_strict(device=args.device)
        if args.strict
        else run_annihilation_pdg_tau_bridge(device=args.device)
    )
    print(json.dumps({k: v for k, v in row.items() if k != "note"}, indent=2))
    print("note:", row["note"])


if __name__ == "__main__":
    main()
