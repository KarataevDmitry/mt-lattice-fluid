"""Instrument catalog — MODEL refs and registry (§5.0 · §5.2 · A10).

M-layer: readout from ``z`` (and ``z_past`` for one-tick ledger), not separate fields.
T-layer: macro/coarse instruments live in ``mt_ca.macro`` (binomial Φ) — listed for routing.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Literal

InstrumentLayer = Literal["M_site", "M_field", "M_ledger_tick", "T_macro"]


class InstrumentId(str, Enum):
    """Stable ids for JSON / scripts."""

    RHO_FIELD = "rho_field"
    B_MATTER = "b_matter"
    N_TOPO = "n_topo"
    N_TOPO_REL = "n_topo_rel"
    N_TOPO_U1 = "n_topo_u1"
    DELTA_PHI = "delta_phi"
    PHI_GATE = "phi_gate"
    N_E = "n_E"
    PI_X = "pi_x"
    PI_Y = "pi_y"
    J_X = "j_x"
    J_Y = "j_y"
    L_Z = "L_z"
    RHO_CONTRAST = "rho_contrast"
    NORM_GLOBAL = "norm_global"
    PHI_KICK_TICK = "phi_kick_tick"
    ENERGY_STAR = "energy_star"
    MOMENTUM_STAR_X = "momentum_star_x"
    MOMENTUM_STAR_Y = "momentum_star_y"


@dataclass(frozen=True, slots=True)
class InstrumentSpec:
    id: InstrumentId
    title: str
    model_ref: str
    layer: InstrumentLayer
    unit: str
    note: str


REGISTRY: tuple[InstrumentSpec, ...] = (
    InstrumentSpec(
        InstrumentId.RHO_FIELD,
        "ρ_field = |z|²",
        "§5.0 A7 · field energy density (not ρ_matter)",
        "M_site",
        "natural",
        "≠ matter occupancy; see b_matter",
    ),
    InstrumentSpec(
        InstrumentId.B_MATTER,
        "b matter occupancy",
        "§5.0 b=min(1,|n_∂|)",
        "M_site",
        "{0,1}",
        "matter_readout instrument (survey/anchor)",
    ),
    InstrumentSpec(
        InstrumentId.N_TOPO,
        "topological charge n",
        "§5.0 A10 auto channel",
        "M_site",
        "ℤ (contour)",
        "dual rel/u1; boil may blind rel",
    ),
    InstrumentSpec(
        InstrumentId.N_TOPO_REL,
        "n_∂ rel",
        "§5.0 ∮ d arg(z₂/z₁)",
        "M_site",
        "ℤ (contour)",
        "",
    ),
    InstrumentSpec(
        InstrumentId.N_TOPO_U1,
        "n_∂ U(1)",
        "§5.0 ∮ d arg(z₁+z₂)",
        "M_site",
        "ℤ (contour)",
        "ocean-locked boil",
    ),
    InstrumentSpec(
        InstrumentId.DELTA_PHI,
        "Arg defect Δφ",
        "§5.0.1 · §3.4.1",
        "M_site",
        "rad",
        "mass carrier; not SM electric charge",
    ),
    InstrumentSpec(
        InstrumentId.PHI_GATE,
        "gate phase Φ",
        "§5.1.1 saturating phase",
        "M_site",
        "rad",
        "local gate angle before ring quantize",
    ),
    InstrumentSpec(
        InstrumentId.N_E,
        "n_E ladder",
        "§5.2.3 · §5.0.4 internal temperature proxy",
        "M_site",
        "E₀ quanta",
        "ring energy rung, not Kelvin",
    ),
    InstrumentSpec(
        InstrumentId.PI_X,
        "π_x momentum density",
        "§5.2.1",
        "M_site",
        "natural",
        "T name for Im(z*∇z); 2D xy slice",
    ),
    InstrumentSpec(
        InstrumentId.PI_Y,
        "π_y momentum density",
        "§5.2.1",
        "M_site",
        "natural",
        "2D xy slice",
    ),
    InstrumentSpec(
        InstrumentId.J_X,
        "j_x Madelung flux",
        "§5.2 bond flux (T-readout)",
        "M_site",
        "natural",
        "2D; diagnostic not M hard law",
    ),
    InstrumentSpec(
        InstrumentId.J_Y,
        "j_y Madelung flux",
        "§5.2",
        "M_site",
        "natural",
        "2D",
    ),
    InstrumentSpec(
        InstrumentId.L_Z,
        "L_z angular momentum density",
        "§5.2.1",
        "M_site",
        "natural",
        "2D grid",
    ),
    InstrumentSpec(
        InstrumentId.RHO_CONTRAST,
        "ρ_max/⟨ρ⟩",
        "§5.0 boil contrast",
        "M_field",
        "1",
        "ocean densitometer background",
    ),
    InstrumentSpec(
        InstrumentId.NORM_GLOBAL,
        "Σ|z|²",
        "A3 global norm",
        "M_field",
        "natural",
        "",
    ),
    InstrumentSpec(
        InstrumentId.PHI_KICK_TICK,
        "Φ kick (ring ticks)",
        "§3.12 ledger",
        "M_ledger_tick",
        "ℤ_N_ring",
        "needs z_past",
    ),
    InstrumentSpec(
        InstrumentId.ENERGY_STAR,
        "Σ_N ΔE star",
        "§5.2.3 energy ledger",
        "M_ledger_tick",
        "n_E·E₀",
        "needs z_past",
    ),
    InstrumentSpec(
        InstrumentId.MOMENTUM_STAR_X,
        "Σ_N Δπ_x star",
        "§5.2.1",
        "M_ledger_tick",
        "p₀ packets",
        "needs z_past",
    ),
    InstrumentSpec(
        InstrumentId.MOMENTUM_STAR_Y,
        "Σ_N Δπ_y star",
        "§5.2.1",
        "M_ledger_tick",
        "p₀ packets",
        "needs z_past",
    ),
)


def instrument_index() -> dict[str, InstrumentSpec]:
    return {s.id.value: s for s in REGISTRY}
