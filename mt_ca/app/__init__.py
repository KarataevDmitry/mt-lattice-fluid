"""Simulation application — SSOT for habitat, scenarios, and run results.

Physics remains in ``mt_ca/``; MODEL in ``model/``. This package wires
reproducible experiments (filled boiling ocean default, planckon on boil, …).

Quick start::

    python -m mt_ca.app list
    python -m mt_ca.app run floor0_planckon --size 64 --steps 0 --settle 64 --track 32
"""
from mt_ca.app.brick import BrickSpec, brick_axis_configs
from mt_ca.app.gates import gate_b, peak_stats
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

__all__ = [
    "BrickSpec",
    "HabitatPreset",
    "RunResult",
    "RunSpec",
    "SCENARIOS",
    "SCHEMA_VERSION",
    "ScenarioSpec",
    "apply_scenario",
    "brick_axis_configs",
    "READOUT_SCHEMA",
    "born_survey",
    "dual_lanes",
    "gate_b",
    "gates_at_z",
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
