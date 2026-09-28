"""§5.0.3 · para-Ps τ — PDG T-door vs M ladder (not head-on tick_focus).

Leading QED: τ = 2ℏ/(m_e c² α⁵).
Ladder: τ = (N_c/α⁵)·2ℏ/(m_P c²),  N_c = m_P/m_e.
Head-on T2 ``tick_focus·hT`` is a different scale (collision focus), not bound-state τ.
"""
from __future__ import annotations

import math
from typing import Any

from mt_ca.annihilation_t_stats import annihilation_t_stats_probe
from mt_ca.si_constants import SI, TAU_PARA_PS_PDG_S


def tau_para_ps_qed_leading(*, m_e_kg: float, alpha: float) -> float:
    """Leading-order para-Ps lifetime [s] (T-layer QED, not full Γ radiative corrections)."""
    c = SI.c
    return 2.0 * SI.hbar / (m_e_kg * c * c * alpha**5)


def tau_para_ps_ladder(*, m_P_kg: float, m_e_kg: float, alpha: float) -> float:
    """Same τ from Compton rung N_c = m_P/m_e (§6 ladder k=8)."""
    n_c = m_P_kg / m_e_kg
    c = SI.c
    return (n_c / alpha**5) * (2.0 * SI.hbar / (m_P_kg * c * c))


def run_annihilation_pdg_tau_bridge(
    *,
    device: str = "cpu",
    tau_pdg_s: float = TAU_PARA_PS_PDG_S,
    rtol_qed: float = 0.012,
) -> dict[str, Any]:
    """Compare PDG τ to QED leading + ladder; separate head-on τ_M from T-stats probe."""
    m_e = SI.m_e_CODATA
    alpha = SI.alpha_fs
    m_p = SI.m_P
    h_t = SI.hT

    tau_qed = tau_para_ps_qed_leading(m_e_kg=m_e, alpha=alpha)
    tau_ladder = tau_para_ps_ladder(m_P_kg=m_p, m_e_kg=m_e, alpha=alpha)
    n_c = m_p / m_e

    t_probe = annihilation_t_stats_probe(size=160, steps=64, ensemble=4, device=device)
    tau_m_collision = float(t_probe["tau_M_s"])

    qed_ok = abs(tau_qed - tau_pdg_s) / tau_pdg_s <= rtol_qed
    ladder_ok = abs(tau_ladder - tau_pdg_s) / tau_pdg_s <= rtol_qed
    identities_ok = abs(tau_qed - tau_ladder) / tau_pdg_s <= 1e-9
    collision_separate = tau_m_collision / tau_pdg_s < 1e-20

    n_ticks_pdg = tau_pdg_s / h_t
    n_ticks_collision = tau_m_collision / h_t

    checks_ok = qed_ok and ladder_ok and identities_ok and collision_separate

    return {
        "tau_para_PDG_s": tau_pdg_s,
        "tau_qed_leading_s": tau_qed,
        "tau_ladder_s": tau_ladder,
        "tau_qed_rel_err": abs(tau_qed - tau_pdg_s) / tau_pdg_s,
        "tau_ladder_rel_err": abs(tau_ladder - tau_pdg_s) / tau_pdg_s,
        "N_c": n_c,
        "N_ticks_PDG": n_ticks_pdg,
        "N_ticks_collision_head_on": n_ticks_collision,
        "tau_M_collision_s": tau_m_collision,
        "tau_M_over_tau_PDG": tau_m_collision / tau_pdg_s,
        "Gamma_PDG_Hz": SI.hbar / tau_pdg_s,
        "qed_matches_PDG": qed_ok,
        "ladder_matches_PDG": ladder_ok,
        "qed_equals_ladder": identities_ok,
        "collision_clock_separate_from_PDG": collision_separate,
        "checks_ok": checks_ok,
        "derivation_closed": False,
        "note": (
            "PDG para-Ps τ is T-door; leading QED and N_c/α⁵·2ℏ/(m_P c²) agree at ~0.5%. "
            "M tick count τ/hT ~ (N_c/α⁵)·2ℏ/(m_P c² hT). Head-on tick_focus·hT is not bound-state τ."
        ),
    }
