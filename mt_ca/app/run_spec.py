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

    @classmethod
    def from_id(
        cls,
        scenario_id: str,
        *,
        ny: int,
        nx: int | None = None,
        steps: int,
        **kwargs: object,
    ) -> RunSpec:
        return cls(scenario=get_scenario(scenario_id), ny=ny, nx=nx if nx is not None else ny, steps=steps, **kwargs)
