"""Run specification — grid, duration, device."""
from __future__ import annotations

from dataclasses import dataclass

from mt_ca.app.scenario import ScenarioSpec, get_scenario


@dataclass(frozen=True, slots=True)
class RunSpec:
    """One executable simulation run."""

    scenario: ScenarioSpec
    ny: int
    nx: int
    steps: int
    device: str = "cpu"
    nz: int | None = None
    block: int = 8
    sample_every: int | None = None
    settle: int = 0
    track: int = 0

    @property
    def dimension(self):
        return self.scenario.dimension

    @classmethod
    def from_id(
        cls,
        scenario_id: str,
        *,
        ny: int,
        nx: int | None = None,
        steps: int,
        nz: int | None = None,
        **kwargs: object,
    ) -> RunSpec:
        scenario = get_scenario(scenario_id)
        nx = nx if nx is not None else ny
        if scenario.stencil == "fcc" and nz is None:
            nz = ny
        if scenario.stencil != "fcc":
            nz = None
        return cls(scenario=scenario, ny=ny, nx=nx, nz=nz, steps=steps, **kwargs)
