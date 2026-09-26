"""§8.2 time-first ontology → instrument SI export (single SSOT).

Simulation natural units: **hL = hT = 1** (one cell = ``l_P``, one tick = ``hT``);
field density **|z|²_nat = 1 ↔ u_P**. SI labels are T-export via the cascade
``t_P → l_P = c·t_P → m_P = ℏ/(c² t_P)`` plus carrier tick ``hT = κ·t_P`` and
Arg ladder ``E₀ = s₀/hT`` (not ``s₀/t_P``).
"""
from __future__ import annotations

from dataclasses import dataclass

from mt_ca.si_constants import DELTA_PHI_MIN, SI, energy_quantum_row

_KB_CODATA = 1.380649e-23  # T-export only (§8.2·units·T_P)


@dataclass(frozen=True, slots=True)
class TimeFirstInstrumentLadder:
    """Closed bridge row for all ``si_per_nat`` in :mod:`scales`."""

    theorem: str
    ontology_order: tuple[str, ...]
    cascade_checks_ok: bool
    energy_ladder_rel_max: float

    t_P_s: float
    hT_s: float
    l_P_m: float
    m_P_kg: float
    c_m_s: float

    s_0_Js: float
    E_0_J: float
    E_P_J: float
    p_0_kg_m_s: float
    F_0_N: float
    L_0_Js: float
    u_P_J_m3: float
    rho_P_kg_m3: float
    m_arg_kg: float

    k_B_T_export_J_per_K: float

    @classmethod
    def build(cls) -> TimeFirstInstrumentLadder:
        cascade = SI.units_time_first_cascade_row()
        eq = energy_quantum_row()
        s0 = float(SI.hbar * DELTA_PHI_MIN)
        ht = float(SI.hT)
        lp = float(SI.l_P)
        mp = float(SI.m_P)
        tp = float(SI.t_P)
        e0 = float(eq["E_0_J"])
        p0 = s0 / lp
        f0 = p0 / ht
        e_p = float(SI.hbar / tp)
        rels = [
            float(eq["rel_p0_c0"]),
            float(eq["rel_F0_lP"]),
            float(eq["rel_L0_hT"]),
        ]
        return cls(
            theorem=str(cascade["theorem"]),
            ontology_order=tuple(cascade["ontology_order"]),
            cascade_checks_ok=bool(cascade["checks_ok"]),
            energy_ladder_rel_max=max(rels),
            t_P_s=tp,
            hT_s=ht,
            l_P_m=lp,
            m_P_kg=mp,
            c_m_s=float(SI.c),
            s_0_Js=s0,
            E_0_J=e0,
            E_P_J=e_p,
            p_0_kg_m_s=p0,
            F_0_N=f0,
            L_0_Js=s0,
            u_P_J_m3=float(SI.u_P),
            rho_P_kg_m3=float(SI.rho_P),
            m_arg_kg=float(SI.m_arg),
            k_B_T_export_J_per_K=_KB_CODATA,
        )

    def to_dict(self) -> dict[str, float | str | bool | list[str]]:
        return {
            "ssot": "§8.2·units·time-first",
            "theorem": self.theorem,
            "ontology_order": list(self.ontology_order),
            "cascade_checks_ok": self.cascade_checks_ok,
            "energy_ladder_rel_max": self.energy_ladder_rel_max,
            "sim_nat": {"hL": "1·l_P", "hT": "1·hT", "rho_nat_1": "u_P"},
            "t_P_s": self.t_P_s,
            "hT_s": self.hT_s,
            "l_P_m": self.l_P_m,
            "m_P_kg": self.m_P_kg,
            "E_0_J": self.E_0_J,
            "E_P_J": self.E_P_J,
            "s_0_Js": self.s_0_Js,
            "u_P_J_m3": self.u_P_J_m3,
        }


_ladder: TimeFirstInstrumentLadder | None = None


def instrument_ladder() -> TimeFirstInstrumentLadder:
    global _ladder
    if _ladder is None:
        _ladder = TimeFirstInstrumentLadder.build()
    return _ladder
