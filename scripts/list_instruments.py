#!/usr/bin/env python3
"""Print MODEL instrument catalog (§5 panel routing)."""
from __future__ import annotations

import argparse
import json

from mt_ca.instruments import REGISTRY


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--json", action="store_true")
    args = p.parse_args()
    rows = [
        {
            "id": s.id.value,
            "title": s.title,
            "layer": s.layer,
            "unit": s.unit,
            "model_ref": s.model_ref,
            "note": s.note,
        }
        for s in REGISTRY
    ]
    if args.json:
        print(json.dumps(rows, indent=2, ensure_ascii=False))
        return 0
    for s in REGISTRY:
        print(f"{s.id.value:22} [{s.layer:14}] {s.title} — {s.model_ref}")
    print(f"\n{len(REGISTRY)} instruments · sample via mt_ca.instruments.sample_panel")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
