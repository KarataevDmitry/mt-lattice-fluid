#!/usr/bin/env python3
"""Verify M-layer axioms after first-principles rebuild.

Check bodies: verify_checks/*.py · grouping: verify_checks/suites.py (SSOT).
"""

from __future__ import annotations

import argparse
import json
import sys

import torch

from verify_checks.suites import (
    SHIP_SUITE_IDS,
    SUITE_ORDER,
    VERIFY_SUITES,
    failed_rows,
    get_suite,
    run_suites,
)


def cmd_list(_: argparse.Namespace) -> int:
    print(f"{'suite':22}  {'ship':4}  description")
    print("-" * 88)
    for sid in SUITE_ORDER:
        spec = VERIFY_SUITES[sid]
        ship = "yes" if spec.ship else "no"
        print(f"{sid:22}  {ship:4}  {spec.description}")
    print("\nRun: verify_principles.py [--ship | --suite t_macro ...]")
    return 0


def _print_results(device: str, rows: list[dict], *, by_suite: bool) -> None:
    print(f"device={device}")
    print("-" * 60)
    if not by_suite:
        for row in rows:
            _print_row(row)
        return

    current: str | None = None
    for row in rows:
        sid = row.get("suite", "?")
        if sid != current:
            current = sid
            spec = VERIFY_SUITES.get(sid)
            desc = spec.description if spec else ""
            print(f"\n=== {sid} ===  {desc}")
        _print_row(row)


def _print_row(row: dict) -> None:
    status = "PASS" if row["ok"] else "FAIL"
    payload = {k: v for k, v in row.items() if k not in ("id", "ok", "suite")}
    print(f"{row['id']:22}  {status}  {payload}")


def main() -> int:
    parser = argparse.ArgumentParser(description="First-principles verification (suites)")
    parser.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--list", action="store_true", help="List verify suites (like sim scenario list).")
    parser.add_argument(
        "--ship",
        action="store_true",
        help=f"Ship profile: {', '.join(SHIP_SUITE_IDS)} (excludes m_evolution_open, cosmology).",
    )
    parser.add_argument(
        "--suite",
        action="append",
        dest="suites",
        metavar="ID",
        help="Run one suite; repeat for several. Default: all suites in SSOT order.",
    )
    args = parser.parse_args()

    if args.list:
        return cmd_list(args)

    if args.ship:
        suite_ids = SHIP_SUITE_IDS
    elif args.suites:
        suite_ids = []
        for raw in args.suites:
            for part in raw.split(","):
                part = part.strip()
                if part:
                    get_suite(part)
                    suite_ids.append(part)
    else:
        suite_ids = list(SUITE_ORDER)

    if args.device == "cuda" and not torch.cuda.is_available():
        args.device = "cpu"

    rows = run_suites(args.device, suite_ids)
    failed = failed_rows(rows)

    if args.json:
        print(
            json.dumps(
                {
                    "device": args.device,
                    "suites": suite_ids,
                    "failed_count": len(failed),
                    "results": rows,
                },
                indent=2,
                default=float,
            )
        )
    else:
        _print_results(args.device, rows, by_suite=True)
        print("-" * 60)
        print(f"suites={len(suite_ids)}  checks={len(rows)}  failed={len(failed)}")
        if failed:
            print("failed:", ", ".join(r["id"] for r in failed))

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
