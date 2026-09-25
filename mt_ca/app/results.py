"""Typed simulation run results."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from mt_ca.app.run_spec import RunSpec

SCHEMA_VERSION = "1"


@dataclass(slots=True)
class RunResult:
    """Unified envelope for script output, runs/*.json, and verify bridges."""

    id: str
    spec: RunSpec
    habitat: str
    seed: str
    device: str
    seconds: float
    norm0: float
    norm_final: float
    norm_drift: float
    gate0: dict[str, Any] | None = None
    gate1: dict[str, Any] | None = None
    samples: list[dict[str, Any]] = field(default_factory=list)
    extra: dict[str, Any] = field(default_factory=dict)
    ok: bool | None = None
    schema_version: str = SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["spec"] = {
            "scenario_id": self.spec.scenario.id,
            "habitat": self.spec.scenario.habitat_label,
            "seed": self.spec.scenario.seed.value,
            "stencil": self.spec.scenario.stencil,
            "ny": self.spec.ny,
            "nx": self.spec.nx,
            "steps": self.spec.steps,
            "settle": self.spec.settle,
            "track": self.spec.track,
        }
        return d

    def to_verify_row(self, check_id: str) -> dict[str, Any]:
        row: dict[str, Any] = {
            "id": check_id,
            "ok": bool(self.ok),
            "habitat": self.habitat,
            "seed": self.seed,
            "norm_drift": self.norm_drift,
            "note": self.extra.get("note", ""),
        }
        row.update({k: v for k, v in self.extra.items() if k != "note"})
        return row
