"""Lattice SSOT — scenario → RunSpec → initialized simulator."""
from __future__ import annotations

from mt_ca.app.dimension import (
    LatticeDimension,
    dimension_for_stencil,
    grid_shape_label,
    nz_for_dimension,
)
from mt_ca.app.run_spec import RunSpec
from mt_ca.app.scenario import ScenarioSpec
from mt_ca.app.stencil import CANON_STENCIL, SLICE_STENCIL
from mt_ca.config import MConfig
from mt_ca.simulator import LatticeFluidSimulator

__all__ = [
    "CANON_STENCIL",
    "SLICE_STENCIL",
    "LatticeDimension",
    "build_run_spec",
    "describe_lattice",
    "open_lattice",
    # backward-compatible names
    "run_spec_cube",
    "open_simulator",
    "nz_for_scenario",
]


def nz_for_scenario(scenario: ScenarioSpec, edge: int) -> int | None:
    return nz_for_dimension(scenario.dimension, edge)


def build_run_spec(
    scenario_id: str,
    edge: int,
    *,
    device: str = "cpu",
    steps: int = 0,
    **kwargs: object,
) -> RunSpec:
    """Executable ``RunSpec`` with correct ``nz`` for 3+1 vs 2+1."""
    return RunSpec.from_id(
        scenario_id,
        ny=edge,
        nx=edge,
        steps=steps,
        device=device,
        **kwargs,
    )


def open_lattice(spec: RunSpec) -> LatticeFluidSimulator:
    """SSOT: habitat + seed + grid geometry → stepped-ready simulator."""
    from mt_ca.app.runner import apply_scenario

    cfg = MConfig.for_stencil(spec.scenario.stencil)
    sim = LatticeFluidSimulator(
        spec.ny,
        spec.nx,
        cfg,
        nz=spec.nz,
        device=spec.device,
    )
    apply_scenario(sim, spec.scenario)
    return sim


def describe_lattice(spec: RunSpec) -> dict[str, str | int | None]:
    dim = spec.scenario.dimension
    return {
        "scenario_id": spec.scenario.id,
        "dimension": dim.value,
        "stencil": spec.scenario.stencil,
        "habitat": spec.scenario.habitat_label,
        "grid": grid_shape_label(dim, spec.ny),
        "ny": spec.ny,
        "nx": spec.nx,
        "nz": spec.nz,
    }


# Aliases (older call sites)
run_spec_cube = build_run_spec
open_simulator = open_lattice
