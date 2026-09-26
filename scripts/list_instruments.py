#!/usr/bin/env python3
"""Print MODEL instrument catalog (§5 panel routing)."""
from __future__ import annotations

import argparse
import json

from mt_ca.instruments import REGISTRY, instrument_ladder


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--json", action="store_true")
    p.add_argument("--ladder", action="store_true", help="print §8.2 time-first SI ladder (SSOT)")
    p.add_argument("--layer", choices=("M_site", "M_field", "M_ledger_tick", "T_macro"), default="")
    args = p.parse_args()
    if args.ladder:
        row = instrument_ladder().to_dict()
        print(json.dumps(row, indent=2, ensure_ascii=False) if args.json else row)
        return 0
    specs = [s for s in REGISTRY if not args.layer or s.layer == args.layer]
    rows = []
    for s in specs:
        row = {
            "id": s.id.value,
            "title": s.title,
            "layer": s.layer,
            "unit_nat": s.unit,
            "model_ref": s.model_ref,
            "note": s.note,
        }
        rows.append(row)
    if args.json:
        print(json.dumps(rows, indent=2, ensure_ascii=False))
        return 0
    for s in specs:
        print(f"{s.id.value:28} [{s.layer:14}] {s.title} — {s.model_ref}")
    print(f"\n{len(REGISTRY)} instruments · sample via mt_ca.instruments.sample_panel")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
