"""Simulation application — SSOT for habitat, scenarios, lattice, and lab instruments.

Physics remains in ``mt_ca/``; MODEL in ``model/``. This package wires
reproducible experiments (filled boiling ocean default, planckon on boil, …).

Layers::

    scenario.py   — named IC + habitat + stencil (FCC vs hex slice)
    lattice.py    — scenario → RunSpec → open_lattice(sim)
    lab.py          — LabSession: instruments always use sim.cfg
    runner.py       — batch runs / floor0 probes

Quick start::

    python -m mt_ca.app list
    python -m mt_ca.app run floor0_planckon --size 32 --steps 0 --settle 32
    python -m mt_ca.app panel habitat_boil --size 32 --settle 64
"""
from mt_ca.app.brick import BrickSpec, brick_axis_configs
from mt_ca.app.dimension import LatticeDimension, dimension_for_stencil, grid_shape_label, nz_for_dimension
from mt_ca.app.gates import gate_b, peak_stats
from mt_ca.instruments import REGISTRY as INSTRUMENT_REGISTRY
from mt_ca.instruments import sample_panel
from mt_ca.app.lab import LabSession, open_lab, open_lab_from_spec, planckon_lab_report
from mt_ca.app.lattice import build_run_spec, describe_lattice, open_lattice
from mt_ca.app.readout_probe import (
    READOUT_SCHEMA,
    born_survey,
    dual_lanes,
    gates_at_z,
    planted_lost,
    planted_persisted,
    sample_row,
)
from mt_ca.app.habitat import HabitatPreset
from mt_ca.app.results import RunResult, SCHEMA_VERSION
from mt_ca.app.run_spec import RunSpec
from mt_ca.app.runner import apply_scenario, run, run_floor0_phase_space, track_gamma_points
from mt_ca.app.scenario import SCENARIOS, ScenarioSpec, get_scenario, scenario_for_seed
from mt_ca.app.stencil import CANON_STENCIL, SLICE_STENCIL

__all__ = [
    "BrickSpec",
    "CANON_STENCIL",
    "SLICE_STENCIL",
    "HabitatPreset",
    "LabSession",
    "LatticeDimension",
    "RunResult",
    "RunSpec",
    "SCENARIOS",
    "SCHEMA_VERSION",
    "ScenarioSpec",
    "apply_scenario",
    "brick_axis_configs",
    "build_run_spec",
    "describe_lattice",
    "dimension_for_stencil",
    "grid_shape_label",
    "INSTRUMENT_REGISTRY",
    "READOUT_SCHEMA",
    "sample_panel",
    "born_survey",
    "dual_lanes",
    "gate_b",
    "gates_at_z",
    "open_lab",
    "open_lab_from_spec",
    "open_lattice",
    "planckon_lab_report",
    "planted_lost",
    "planted_persisted",
    "sample_row",
    "get_scenario",
    "scenario_for_seed",
    "peak_stats",
    "run",
    "run_floor0_phase_space",
    "track_gamma_points",
]
