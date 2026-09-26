"""Instrument scales — natural (Planck lattice) ↔ SI (§7.1 · §5.2).

Simulation stores **natural** numbers (hL=hT=1, |z|² in u_P units). Each instrument
declares a :class:`QuantityKind`; SI is ``value_si = value_nat * si_per_nat``.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum

from mt_ca.si_constants import SI

_KB = 1.380649e-23


class QuantityKind(str, Enum):
    DIMENSIONLESS = "dimensionless"
    PHASE_RAD = "phase_rad"
    RHO_FIELD = "rho_field"
    FIELD_AMPLITUDE = "field_amplitude"
    ENERGY_E0 = "energy_E0"
    ENERGY_EP = "energy_EP"
    MASS_MP = "mass_mP"
    MASS_MARG = "mass_m_arg"
    MOMENTUM_P0 = "momentum_p0"
    MOMENTUM_DENSITY = "momentum_density"
    ACTION_S0 = "action_s0"
    ANGULAR_MOMENTUM_L0 = "angular_L0"
    FORCE_F0 = "force_F0"
    TIME_HT = "time_hT"
    LENGTH_LP = "length_lP"
    FREQUENCY = "frequency"
    ENERGY_DENSITY_UP = "energy_density_uP"
    MASS_DENSITY_RHOP = "mass_density_rhoP"
    CURRENT_DENSITY = "current_density"
    TEMPERATURE_E_OVER_KB = "temperature_E0_over_kB"
    MACRO_MASS_READOUT = "macro_mass_readout"


@dataclass(frozen=True, slots=True)
class ScaleSpec:
    kind: QuantityKind
    unit_nat: str
    unit_si: str
    si_per_nat: float
    note: str = ""


def scale_spec(kind: QuantityKind) -> ScaleSpec:
    si = SI
    table: dict[QuantityKind, ScaleSpec] = {
        QuantityKind.DIMENSIONLESS: ScaleSpec(kind, "1", "1", 1.0),
        QuantityKind.PHASE_RAD: ScaleSpec(kind, "rad", "rad", 1.0),
        QuantityKind.RHO_FIELD: ScaleSpec(
            kind, "|z|² (×u_P)", "J/m³", si.u_P, "|z|²_nat=1 ↔ u_P",
        ),
        QuantityKind.FIELD_AMPLITUDE: ScaleSpec(
            kind, "|z| (×√u_P)", "J^½/m^{3/2}", math.sqrt(si.u_P), "√(energy density)",
        ),
        QuantityKind.ENERGY_E0: ScaleSpec(kind, "E₀", "J", si.E_0),
        QuantityKind.ENERGY_EP: ScaleSpec(kind, "E_P", "J", si.E_P),
        QuantityKind.MASS_MP: ScaleSpec(kind, "m_P", "kg", si.m_P),
        QuantityKind.MASS_MARG: ScaleSpec(kind, "m_arg", "kg", si.m_arg),
        QuantityKind.MOMENTUM_P0: ScaleSpec(kind, "p₀", "kg·m/s", si.p_0),
        QuantityKind.MOMENTUM_DENSITY: ScaleSpec(
            kind, "π (×p₀/l_P³)", "kg/(m²·s)", si.p_0 / si.l_P**3,
        ),
        QuantityKind.ACTION_S0: ScaleSpec(kind, "s₀", "J·s", si.s_0),
        QuantityKind.ANGULAR_MOMENTUM_L0: ScaleSpec(kind, "L₀", "J·s", si.L_0),
        QuantityKind.FORCE_F0: ScaleSpec(kind, "F₀", "N", si.F_0),
        QuantityKind.TIME_HT: ScaleSpec(kind, "hT", "s", si.hT),
        QuantityKind.LENGTH_LP: ScaleSpec(kind, "hL=l_P", "m", si.l_P),
        QuantityKind.FREQUENCY: ScaleSpec(kind, "hT⁻¹", "Hz", 1.0 / si.hT),
        QuantityKind.ENERGY_DENSITY_UP: ScaleSpec(kind, "u_P", "J/m³", si.u_P),
        QuantityKind.MASS_DENSITY_RHOP: ScaleSpec(kind, "ρ_P", "kg/m³", si.rho_P),
        QuantityKind.CURRENT_DENSITY: ScaleSpec(
            kind,
            "j (×p₀/(l_P⁴c))",
            "A/m²",
            si.p_0 / (si.l_P**4 * si.c),
            "Madelung j proxy",
        ),
        QuantityKind.TEMPERATURE_E_OVER_KB: ScaleSpec(
            kind, "E₀/k_B", "K", si.E_0 / _KB, "n_E ladder proxy, not CMB bath",
        ),
        QuantityKind.MACRO_MASS_READOUT: ScaleSpec(
            kind,
            "Σ|Φ|² coarse",
            "kg·m²",
            si.m_P * si.l_P**2,
            "integrated T mass readout (2+1 coarse sum)",
        ),
    }
    return table[kind]


@dataclass(frozen=True, slots=True)
class ScaledReading:
    """One instrument reading — natural value + SI via declared scale."""

    id: str
    kind: QuantityKind
    value_nat: float
    unit_nat: str
    value_si: float
    unit_si: str
    si_per_nat: float

    def to_dict(self) -> dict[str, float | str]:
        return {
            "id": self.id,
            "kind": self.kind.value,
            "value_nat": self.value_nat,
            "unit_nat": self.unit_nat,
            "value_si": self.value_si,
            "unit_si": self.unit_si,
            "si_per_nat": self.si_per_nat,
        }


def reading(instrument_id: str, kind: QuantityKind, value_nat: float) -> ScaledReading:
    spec = scale_spec(kind)
    v = float(value_nat)
    return ScaledReading(
        id=instrument_id,
        kind=kind,
        value_nat=v,
        unit_nat=spec.unit_nat,
        value_si=v * spec.si_per_nat,
        unit_si=spec.unit_si,
        si_per_nat=spec.si_per_nat,
    )
