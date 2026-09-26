"""Grid conventions — 3+1 FCC canon, 2+1 hex slice only when scenario says so."""
from __future__ import annotations

from mt_ca.app.runner import apply_scenario
from mt_ca.app.scenario import ScenarioSpec, get_scenario
from mt_ca.app.stencil import CANON_STENCIL, SLICE_STENCIL
from mt_ca.config import MConfig
from mt_ca.simulator import LatticeFluidSimulator

__all__ = [
    "CANON_STENCIL",
    "SLICE_STENCIL",
    "nz_for_scenario",
    "run_spec_cube",
    "open_simulator",
]


def nz_for_scenario(scenario: ScenarioSpec, edge: int) -> int | None:
    if scenario.stencil == CANON_STENCIL:
        return edge
    return None


def run_spec_cube(
    scenario_id: str,
    edge: int,
    *,
    device: str = "cpu",
    steps: int = 0,
    **kwargs: object,
):
    """``RunSpec`` with ``nz=edge`` when scenario stencil is FCC."""
    from mt_ca.app.run_spec import RunSpec

    scenario = get_scenario(scenario_id)
    return RunSpec(
        scenario=scenario,
        ny=edge,
        nx=edge,
        nz=nz_for_scenario(scenario, edge),
        steps=steps,
        device=device,
        **kwargs,
    )


def open_simulator(spec) -> LatticeFluidSimulator:
    """SSOT: scenario + grid → initialized ``LatticeFluidSimulator``."""
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