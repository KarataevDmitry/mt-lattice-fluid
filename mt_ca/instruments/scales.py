"""Instrument scales — natural (carrier hL=hT=1) ↔ SI via §8.2 time-first ladder.

Natural simulation numbers use **one tick = hT**, **one cell = l_P**, **|z|²=1 ↔ u_P**.
Each :class:`QuantityKind` maps ``value_si = value_nat * si_per_nat`` where
``si_per_nat`` is derived from :func:`instrument_ladder`, not a flat bag of constants.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum

from mt_ca.instruments.time_first_ladder import instrument_ladder


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
    MACRO_MASS_READOUT = "macro_mass_coarse"


@dataclass(frozen=True, slots=True)
class ScaleSpec:
    kind: QuantityKind
    unit_nat: str
    unit_si: str
    si_per_nat: float
    nat_anchor: str = ""
    si_derivation: str = ""
    note: str = ""


def scale_spec(kind: QuantityKind) -> ScaleSpec:
    L = instrument_ladder()
    c = L.c_m_s
    lp, ht = L.l_P_m, L.hT_s

    table: dict[QuantityKind, ScaleSpec] = {
        QuantityKind.DIMENSIONLESS: ScaleSpec(
            kind, "1", "1", 1.0, nat_anchor="1", si_derivation="identity",
        ),
        QuantityKind.PHASE_RAD: ScaleSpec(
            kind, "rad", "rad", 1.0, nat_anchor="Arg phase", si_derivation="identity",
        ),
        QuantityKind.RHO_FIELD: ScaleSpec(
            kind,
            "|z|² (×u_P)",
            "J/m³",
            L.u_P_J_m3,
            nat_anchor="|z|²_nat=1",
            si_derivation="m_P c² / l_P³ (time-first ρ_P c²)",
            note="gate floor; core |z|² may exceed 1 in SI export",
        ),
        QuantityKind.FIELD_AMPLITUDE: ScaleSpec(
            kind,
            "|z| (×√u_P)",
            "J^½/m^{3/2}",
            math.sqrt(L.u_P_J_m3),
            nat_anchor="|z|_nat",
            si_derivation="√u_P",
        ),
        QuantityKind.ENERGY_E0: ScaleSpec(
            kind,
            "E₀",
            "J",
            L.E_0_J,
            nat_anchor="1·E₀ (n_E ladder)",
            si_derivation="s₀/hT = κ·ℏ·Δφ_min/t_P",
        ),
        QuantityKind.ENERGY_EP: ScaleSpec(
            kind,
            "E_P",
            "J",
            L.E_P_J,
            nat_anchor="ℏ/t_P",
            si_derivation="textbook Planck energy per t_P (not M tick)",
        ),
        QuantityKind.MASS_MP: ScaleSpec(
            kind,
            "m_P",
            "kg",
            L.m_P_kg,
            nat_anchor="1·m_P",
            si_derivation="ℏ/(c² t_P)",
        ),
        QuantityKind.MASS_MARG: ScaleSpec(
            kind,
            "m_arg",
            "kg",
            L.m_arg_kg,
            nat_anchor="Arg mass quantum",
            si_derivation="α-ladder mass (SI bridge)",
        ),
        QuantityKind.MOMENTUM_P0: ScaleSpec(
            kind,
            "p₀",
            "kg·m/s",
            L.p_0_kg_m_s,
            nat_anchor="1·p₀",
            si_derivation="s₀/l_P",
        ),
        QuantityKind.MOMENTUM_DENSITY: ScaleSpec(
            kind,
            "π (×p₀/l_P³)",
            "kg/(m²·s)",
            L.p_0_kg_m_s / lp**3,
            nat_anchor="π_nat",
            si_derivation="p₀/l_P³",
        ),
        QuantityKind.ACTION_S0: ScaleSpec(
            kind,
            "s₀",
            "J·s",
            L.s_0_Js,
            nat_anchor="1·s₀",
            si_derivation="ℏ·Δφ_min",
        ),
        QuantityKind.ANGULAR_MOMENTUM_L0: ScaleSpec(
            kind,
            "L₀",
            "J·s",
            L.L_0_Js,
            nat_anchor="1·L₀",
            si_derivation="s₀ (Arg quantum)",
        ),
        QuantityKind.FORCE_F0: ScaleSpec(
            kind,
            "F₀",
            "N",
            L.F_0_N,
            nat_anchor="1·F₀",
            si_derivation="p₀/hT",
        ),
        QuantityKind.TIME_HT: ScaleSpec(
            kind,
            "hT",
            "s",
            L.hT_s,
            nat_anchor="1 sim tick",
            si_derivation="κ·t_P",
        ),
        QuantityKind.LENGTH_LP: ScaleSpec(
            kind,
            "hL=l_P",
            "m",
            L.l_P_m,
            nat_anchor="1 sim cell",
            si_derivation="c·t_P",
        ),
        QuantityKind.FREQUENCY: ScaleSpec(
            kind,
            "hT⁻¹",
            "Hz",
            1.0 / ht,
            nat_anchor="1/tick",
            si_derivation="1/hT",
        ),
        QuantityKind.ENERGY_DENSITY_UP: ScaleSpec(
            kind,
            "u_P",
            "J/m³",
            L.u_P_J_m3,
            nat_anchor="u_P",
            si_derivation="ρ_P c²",
        ),
        QuantityKind.MASS_DENSITY_RHOP: ScaleSpec(
            kind,
            "ρ_P",
            "kg/m³",
            L.rho_P_kg_m3,
            nat_anchor="ρ_P",
            si_derivation="m_P/l_P³",
        ),
        QuantityKind.CURRENT_DENSITY: ScaleSpec(
            kind,
            "j (×p₀/(l_P⁴c))",
            "A/m²",
            L.p_0_kg_m_s / (lp**4 * c),
            nat_anchor="Madelung j proxy",
            si_derivation="p₀/(l_P⁴ c)",
        ),
        QuantityKind.TEMPERATURE_E_OVER_KB: ScaleSpec(
            kind,
            "E/k_B",
            "K",
            L.E_0_J / L.k_B_T_export_J_per_K,
            nat_anchor="E in E₀ units",
            si_derivation="Θ[K] = E/k_B — T-export only (§8.2·units·T_P)",
            note="M layer stores energy; Kelvin is export, not ontology",
        ),
        QuantityKind.MACRO_MASS_READOUT: ScaleSpec(
            kind,
            "Σ|Φ|² coarse",
            "kg·m²",
            L.m_P_kg * lp**2,
            nat_anchor="coarse T sum",
            si_derivation="m_P·l_P²",
            note="integrated T mass readout (2+1 coarse sum)",
        ),
    }
    return table[kind]


@dataclass(frozen=True, slots=True)
class ScaledReading:
    """One instrument reading — natural value + SI via time-first scale."""

    id: str
    kind: QuantityKind
    value_nat: float
    unit_nat: str
    value_si: float
    unit_si: str
    si_per_nat: float
    nat_anchor: str = ""
    si_derivation: str = ""
    scale_ssot: str = "§8.2·units·time-first"

    def to_dict(self) -> dict[str, float | str]:
        return {
            "id": self.id,
            "kind": self.kind.value,
            "value_nat": self.value_nat,
            "unit_nat": self.unit_nat,
            "value_si": self.value_si,
            "unit_si": self.unit_si,
            "si_per_nat": self.si_per_nat,
            "nat_anchor": self.nat_anchor,
            "si_derivation": self.si_derivation,
            "scale_ssot": self.scale_ssot,
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
        nat_anchor=spec.nat_anchor,
        si_derivation=spec.si_derivation,
    )
