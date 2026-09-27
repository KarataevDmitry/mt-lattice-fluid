"""§5.0.4-A — internal n_E selection rules (schema + audit on ledger track)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from mt_ca.si_constants import elementary_quanta_row, hv_bit_budget


@dataclass(frozen=True)
class Floor0SelectionSchema:
    """M-level selection rules between internal n_E classes (one v_p, topology fixed)."""

    n_ring: int
    delta_phi_disc: int
    ticks_per_e0: int
    n_e_max: int
    rule_ids: tuple[str, ...]

    @classmethod
    def from_phase_bits(cls, phase_bits: int | None = None) -> Floor0SelectionSchema:
        eq = elementary_quanta_row(phase_bits=phase_bits)
        n_ring = int(eq["N_ring"])
        delta = int(eq["delta_phi_min_disc"])
        unit = int(eq["energy_ticks_per_E0"])
        n_e_max = n_ring // unit
        return cls(
            n_ring=n_ring,
            delta_phi_disc=delta,
            ticks_per_e0=unit,
            n_e_max=n_e_max,
            rule_ids=("S1", "S2", "S3", "S4"),
        )


def floor0_selection_schema_row(*, phase_bits: int | None = None) -> dict[str, Any]:
    """Closed algebra for §5.0.4-A selection (no sim)."""
    schema = Floor0SelectionSchema.from_phase_bits(phase_bits=phase_bits)
    bb = hv_bit_budget()
    return {
        "N_ring": schema.n_ring,
        "delta_phi_disc": schema.delta_phi_disc,
        "ticks_per_E0": schema.ticks_per_e0,
        "n_E_max": schema.n_e_max,
        "n_E_classes": schema.n_e_max + 1,
        "rule_ids": list(schema.rule_ids),
        "rules": [
            {
                "id": "S1",
                "name": "ledger",
                "statement": "n_E = floor(|Phi_kick| / ticks_per_E0)",
            },
            {
                "id": "S2",
                "name": "heisenberg",
                "statement": "|Phi_kick| = 0 or |Phi_kick| >= delta_phi_disc (CL-3)",
            },
            {
                "id": "S3",
                "name": "excitation",
                "statement": "if n_E rises vs prior tick then |Phi| >= n_E * ticks_per_E0",
            },
            {
                "id": "S4",
                "name": "ceiling",
                "statement": f"n_E <= {schema.n_e_max} on Z_{schema.n_ring}",
            },
        ],
        "atom_analog_note": (
            "T dipole |Delta ell|=1 is not an M law at floor 0; multi-quantum |Delta n_E|>1 "
            "is allowed when kick magnitude carries the ladder jump."
        ),
        "B_hV": float(bb.B_hV),
        "checks_ok": (
            schema.n_ring == 512
            and schema.delta_phi_disc == 41
            and schema.ticks_per_e0 == 41
            and schema.n_e_max == 12
            and len(schema.rule_ids) == 4
        ),
    }


def audit_n_E_tick(
    *,
    phi_ticks: int,
    n_e: int,
    prev_n_e: int | None,
    schema: Floor0SelectionSchema,
) -> list[str]:
    """Return violation rule ids for one planckon-core sample (empty if allowed)."""
    unit = schema.ticks_per_e0
    phi_min = schema.delta_phi_disc
    violations: list[str] = []

    if n_e != abs(phi_ticks) // unit:
        violations.append("S1")
    if 0 < abs(phi_ticks) < phi_min:
        violations.append("S2")
    if n_e > schema.n_e_max:
        violations.append("S4")
    if prev_n_e is not None and n_e > prev_n_e and abs(phi_ticks) < n_e * unit:
        violations.append("S3")
    return violations


def summarize_transition_histogram(deltas: list[int]) -> dict[str, Any]:
    """Histogram of Delta n_E on planckon track."""
    if not deltas:
        return {
            "transitions": 0,
            "elastic": 0,
            "inelastic": 0,
            "multi_quantum": 0,
            "delta_histogram": {},
        }
    elastic = sum(1 for d in deltas if d == 0)
    inelastic = sum(1 for d in deltas if d != 0)
    multi = sum(1 for d in deltas if abs(d) > 1)
    hist: dict[str, int] = {}
    for d in deltas:
        key = str(d)
        hist[key] = hist.get(key, 0) + 1
    return {
        "transitions": len(deltas),
        "elastic": elastic,
        "inelastic": inelastic,
        "multi_quantum": multi,
        "delta_histogram": hist,
    }
