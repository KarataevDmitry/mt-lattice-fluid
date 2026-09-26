"""Lattice SSOT — bind scenario conditions to an embedding grid."""
from __future__ import annotations

from mt_ca.app.dimension import (
    LatticeDimension,
    grid_shape_label,
    nz_for_dimension,
    stencil_for_dimension,
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
    "run_spec_cube",
    "open_simulator",
    "nz_for_scenario",
]


def nz_for_scenario(scenario: ScenarioSpec, edge: int, embedding: LatticeDimension) -> int | None:
    del scenario  # conditions do not set nz; embedding does
    return nz_for_dimension(embedding, edge)


def build_run_spec(
    scenario_id: str,
    edge: int,
    *,
    embedding: LatticeDimension | None = None,
    device: str = "cpu",
    steps: int = 0,
    **kwargs: object,
) -> RunSpec:
    return RunSpec.from_id(
        scenario_id,
        ny=edge,
        nx=edge,
        steps=steps,
        device=device,
        embedding=embedding,
        **kwargs,
    )


def open_lattice(spec: RunSpec) -> LatticeFluidSimulator:
    from mt_ca.app.runner import apply_scenario

    cfg = MConfig.for_stencil(spec.stencil)
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
    return {
        "run_id": spec.run_id or spec.scenario.id,
        "scenario_id": spec.scenario.id,
        "embedding": spec.embedding.value,
        "dimension": spec.embedding.value,
        "stencil": spec.stencil,
        "habitat": spec.scenario.habitat_label,
        "grid": grid_shape_label(spec.embedding, spec.ny),
        "ny": spec.ny,
        "nx": spec.nx,
        "nz": spec.nz,
    }


run_spec_cube = build_run_spec
open_simulator = open_lattice
