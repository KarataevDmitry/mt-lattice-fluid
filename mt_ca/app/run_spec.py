"""Run specification — scenario conditions + embedding + grid + duration."""
from __future__ import annotations

from dataclasses import dataclass

from mt_ca.app.dimension import LatticeDimension, nz_for_dimension, stencil_for_dimension
from mt_ca.app.scenario import ScenarioSpec, get_scenario, resolve_scenario_id


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
    run_id: str | None = None
    """Original scenario/alias id passed to ``from_id`` (for logging)."""

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
        embedding: LatticeDimension | None = None,
        nz: int | None = None,
        **kwargs: object,
    ) -> RunSpec:
        base_id, emb_alias = resolve_scenario_id(scenario_id)
        scenario = get_scenario(base_id)
        emb = embedding or emb_alias or LatticeDimension.VOLUME_3P1
        nx = nx if nx is not None else ny
        if nz is None:
            nz = nz_for_dimension(emb, ny)
        elif emb is LatticeDimension.SLICE_2P1:
            nz = None
        return cls(
            scenario=scenario,
            embedding=emb,
            ny=ny,
            nx=nx,
            nz=nz,
            steps=steps,
            run_id=scenario_id,
            **kwargs,
        )
