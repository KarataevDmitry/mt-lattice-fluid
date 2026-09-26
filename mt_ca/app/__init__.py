"""App SSOT: scenario (conditions) · RunSpec.embedding · lab (instruments)."""
from mt_ca.app.brick import BrickSpec, brick_axis_configs
from mt_ca.app.dimension import LatticeDimension, dimension_for_stencil, grid_shape_label, nz_for_dimension
from mt_ca.app.gates import gate_b, peak_stats
from mt_ca.app.habitat import HabitatPreset
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
from mt_ca.app.results import RunResult, SCHEMA_VERSION
from mt_ca.app.run_spec import RunSpec
from mt_ca.app.runner import apply_scenario, run, run_floor0_phase_space, track_gamma_points
from mt_ca.app.scenario import SCENARIOS, ScenarioSpec, get_scenario, scenario_for_seed
from mt_ca.app.stencil import CANON_STENCIL, SLICE_STENCIL
from mt_ca.instruments import REGISTRY as INSTRUMENT_REGISTRY
from mt_ca.instruments import sample_panel

__all__ = [
    "BrickSpec",
    "CANON_STENCIL",
    "SLICE_STENCIL",
    "HabitatPreset",
    "INSTRUMENT_REGISTRY",
    "LabSession",
    "LatticeDimension",
    "READOUT_SCHEMA",
    "RunResult",
    "RunSpec",
    "SCENARIOS",
    "SCHEMA_VERSION",
    "ScenarioSpec",
    "apply_scenario",
    "born_survey",
    "brick_axis_configs",
    "build_run_spec",
    "describe_lattice",
    "dimension_for_stencil",
    "dual_lanes",
    "gate_b",
    "gates_at_z",
    "get_scenario",
    "grid_shape_label",
    "open_lab",
    "open_lab_from_spec",
    "open_lattice",
    "peak_stats",
    "planckon_lab_report",
    "planted_lost",
    "planted_persisted",
    "run",
    "run_floor0_phase_space",
    "sample_panel",
    "sample_row",
    "scenario_for_seed",
    "track_gamma_points",
]
