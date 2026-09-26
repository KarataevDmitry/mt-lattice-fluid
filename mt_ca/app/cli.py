"""CLI for the simulation application SSOT."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import torch

from mt_ca.app.lattice import build_run_spec
from mt_ca.app.runner import run
from mt_ca.app.scenario import SCENARIOS


def _device_default() -> str:
    return "cuda" if torch.cuda.is_available() else "cpu"


def cmd_list(_: argparse.Namespace) -> int:
    print(f"{'scenario':28}  {'dim':4}  {'stencil':4}  {'habitat':16}  {'seed':12}  description")
    print("-" * 100)
    for sid, spec in sorted(SCENARIOS.items()):
        print(
            f"{sid:28}  {spec.dimension.value:4}  {spec.stencil:4}  {spec.habitat.value:16}  "
            f"{spec.seed.value:12}  {spec.description}"
        )
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    if args.device == "cuda" and not torch.cuda.is_available():
        args.device = "cpu"
    spec = build_run_spec(
        args.scenario,
        args.size,
        device=args.device,
        steps=args.steps,
        block=args.block,
        sample_every=args.sample_every,
        settle=args.settle,
        track=args.track,
    )
    result = run(spec)
    payload = result.to_dict()
    payload["lattice"] = spec.scenario.grid_label(spec.ny) if spec.ny else None
    if args.json_out:
        Path(args.json_out).write_text(json.dumps(payload, indent=2), encoding="utf-8")
    if args.json or not args.json_out:
        print(json.dumps(payload, indent=2))
    return 0


def cmd_panel(args: argparse.Namespace) -> int:
    from mt_ca.app.lab import open_lab_from_spec

    if args.device == "cuda" and not torch.cuda.is_available():
        args.device = "cpu"
    spec = build_run_spec(args.scenario, args.size, device=args.device, steps=0)
    lab = open_lab_from_spec(spec)
    if args.settle:
        lab.settle(args.settle)
    if args.steps:
        lab.step(args.steps)
    panel = lab.panel()
    payload = {"lattice": lab.meta, "panel": panel}
    if args.json or not args.json_out:
        print(json.dumps(payload, indent=2, default=str))
    if args.json_out:
        Path(args.json_out).write_text(
            json.dumps(payload, indent=2, default=str), encoding="utf-8"
        )
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="mt-lattice-fluid simulation application (SSOT)")
    sub = p.add_subparsers(dest="command", required=True)

    list_p = sub.add_parser("list", help="List registered scenarios")
    list_p.set_defaults(func=cmd_list)

    run_p = sub.add_parser("run", help="Run one scenario")
    run_p.add_argument("scenario", choices=sorted(SCENARIOS))
    run_p.add_argument("--size", type=int, default=32, help="cube edge (3+1) or side (2+1 slice)")
    run_p.add_argument("--steps", type=int, default=128)
    run_p.add_argument("--settle", type=int, default=0)
    run_p.add_argument("--track", type=int, default=0)
    run_p.add_argument("--sample-every", type=int, default=None)
    run_p.add_argument("--block", type=int, default=8)
    run_p.add_argument("--device", default=_device_default())
    run_p.add_argument("--json", action="store_true")
    run_p.add_argument("--json-out", type=str, default=None)
    run_p.set_defaults(func=cmd_run)

    panel_p = sub.add_parser("panel", help="Instrument panel (lab SSOT) on one scenario")
    panel_p.add_argument("scenario", choices=sorted(SCENARIOS))
    panel_p.add_argument("--size", type=int, default=32)
    panel_p.add_argument("--settle", type=int, default=32)
    panel_p.add_argument("--steps", type=int, default=0)
    panel_p.add_argument("--device", default=_device_default())
    panel_p.add_argument("--json", action="store_true")
    panel_p.add_argument("--json-out", type=str, default=None)
    panel_p.set_defaults(func=cmd_panel)
    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
