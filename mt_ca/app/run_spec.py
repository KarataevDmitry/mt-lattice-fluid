"""Run specification — scenario conditions + embedding + grid + duration."""
from __future__ import annotations

from dataclasses import dataclass

from mt_ca.app.dimension import LatticeDimension, nz_for_dimension, stencil_for_dimension
from mt_ca.app.scenario import ScenarioSpec, get_scenario


@dataclass(frozen=True, slots=True)
class RunSpec:
    """One executable run: *what* (scenario) × *where* (embedding) × grid size."""

    scenario: ScenarioSpec
    embedding: LatticeDimension
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
    def dimension(self) -> LatticeDimension:
        return self.embedding

    @property
    def stencil(self) -> str:
        return stencil_for_dimension(self.embedding)

    @classmethod
    def from_id(
        cls,
        scenario_id: str,
        *,
        ny: int,
        nx: int | None = None,
        steps: int,
        embedding: LatticeDimension = LatticeDimension.VOLUME_3P1,
        nz: int | None = None,
        **kwargs: object,
    ) -> RunSpec:
        scenario = get_scenario(scenario_id)
        nx = nx if nx is not None else ny
        if nz is None:
            nz = nz_for_dimension(embedding, ny)
        elif embedding is LatticeDimension.SLICE_2P1:
            nz = None
        return cls(
            scenario=scenario,
            embedding=embedding,
            ny=ny,
            nx=nx,
            nz=nz,
            steps=steps,
            **kwargs,
        )
