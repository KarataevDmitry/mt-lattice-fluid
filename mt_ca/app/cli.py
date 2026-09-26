"""CLI — scenario (conditions) + --embedding (grid dimension)."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import torch

from mt_ca.app.dimension import LatticeDimension
from mt_ca.app.lattice import build_run_spec
from mt_ca.app.runner import run
from mt_ca.app.scenario import SCENARIOS


def _device_default() -> str:
    return "cuda" if torch.cuda.is_available() else "cpu"


def _parse_embedding(raw: str) -> LatticeDimension:
    for dim in LatticeDimension:
        if raw in (dim.value, dim.name.lower()):
            return dim
    raise argparse.ArgumentTypeError(f"embedding must be 3+1 or 2+1, got {raw!r}")


def cmd_list(_: argparse.Namespace) -> int:
    print(f"{'scenario':26}  {'habitat':16}  {'seed':12}  description")
    print("-" * 90)
    for sid, spec in sorted(SCENARIOS.items()):
        print(
            f"{sid:26}  {spec.habitat.value:16}  {spec.seed.value:12}  {spec.description}"
        )
    print("\nRun: --embedding 3+1 (default) | 2+1")
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    if args.device == "cuda" and not torch.cuda.is_available():
        args.device = "cpu"
    spec = build_run_spec(
        args.scenario,
        args.size,
        device=args.device,
        steps=args.steps,
        embedding=args.embedding,
        block=args.block,
        sample_every=args.sample_every,
        settle=args.settle,
        track=args.track,
    )
    result = run(spec)
    payload = result.to_dict()
    if args.json_out:
        Path(args.json_out).write_text(json.dumps(payload, indent=2), encoding="utf-8")
    if args.json or not args.json_out:
        print(json.dumps(payload, indent=2))
    return 0


def cmd_panel(args: argparse.Namespace) -> int:
    from mt_ca.app.lab import open_lab_from_spec

    if args.device == "cuda" and not torch.cuda.is_available():
        args.device = "cpu"
    spec = build_run_spec(
        args.scenario, args.size, device=args.device, steps=0, embedding=args.embedding
    )
    lab = open_lab_from_spec(spec)
    if args.settle:
        lab.settle(args.settle)
    if args.steps:
        lab.step(args.steps)
    payload = {"lattice": lab.meta, "panel": lab.panel()}
    if args.json or not args.json_out:
        print(json.dumps(payload, indent=2, default=str))
    if args.json_out:
        Path(args.json_out).write_text(
            json.dumps(payload, indent=2, default=str), encoding="utf-8"
        )
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="mt-lattice-fluid app")
    sub = p.add_subparsers(dest="command", required=True)
    ids = sorted(SCENARIOS)

    sub.add_parser("list").set_defaults(func=cmd_list)

    run_p = sub.add_parser("run")
    run_p.add_argument("scenario", choices=ids)
    run_p.add_argument("--size", type=int, default=32)
    run_p.add_argument(
        "--embedding",
        type=_parse_embedding,
        default=LatticeDimension.VOLUME_3P1,
    )
    run_p.add_argument("--steps", type=int, default=128)
    run_p.add_argument("--settle", type=int, default=0)
    run_p.add_argument("--track", type=int, default=0)
    run_p.add_argument("--sample-every", type=int, default=None)
    run_p.add_argument("--block", type=int, default=8)
    run_p.add_argument("--device", default=_device_default())
    run_p.add_argument("--json", action="store_true")
    run_p.add_argument("--json-out", type=str, default=None)
    run_p.set_defaults(func=cmd_run)

    panel_p = sub.add_parser("panel")
    panel_p.add_argument("scenario", choices=ids)
    panel_p.add_argument("--size", type=int, default=48)
    panel_p.add_argument(
        "--embedding",
        type=_parse_embedding,
        default=LatticeDimension.VOLUME_3P1,
    )
    panel_p.add_argument("--settle", type=int, default=0)
    panel_p.add_argument("--steps", type=int, default=128)
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
