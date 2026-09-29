#!/usr/bin/env python3
"""Emit book/sources/generated/lab-auto-floors.tex from mt_ca probes."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from mt_ca.lab_records_tex import generate_floors_lab_fragments  # noqa: E402


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--device", default="cpu")
    p.add_argument(
        "--sources-dir",
        type=Path,
        default=ROOT / "book" / "sources",
    )
    args = p.parse_args()
    fragments = generate_floors_lab_fragments(device=args.device)
    for rel, tex in fragments.items():
        out = args.sources_dir / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(tex, encoding="utf-8")
        print(f"wrote {out} ({len(tex)} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
