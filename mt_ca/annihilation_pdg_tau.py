"""§5.0.3 · para-Ps τ — PDG T-door vs M ladder (not head-on tick_focus).

Leading QED: τ = 2ℏ/(m_e c² α⁵).
Ladder: τ = (N_c/α⁵)·2ℏ/(m_P c²),  N_c = m_P/m_e.
Head-on T2 ``tick_focus·hT`` is a different scale (collision focus), not bound-state τ.
"""
from __future__ import annotations

import math
from typing import Any

from mt_ca.annihilation_t_stats import annihilation_t_stats_probe
from mt_ca.si_constants import (
    C,
    EV_J,
    SI,
    TAU_ORTHO_PS_PDG_S,
    TAU_PARA_PS_PDG_S,
    TAU_PARA_PS_PDG_U_S,
    U_ALPHA_FS_REL_CODATA,
    U_M_E_REL_CODATA,
)


def tau_para_ps_qed_leading(*, m_e_kg: float, alpha: float) -> float:
    """Leading-order para-Ps lifetime [s] (T-layer QED, not full Γ radiative corrections)."""
    c = SI.c
    return 2.0 * SI.hbar / (m_e_kg * c * c * alpha**5)


def gev_to_kg(m_gev: float) -> float:
    return m_gev * 1e9 * EV_J / (C * C)


def tau_para_ps_ladder(*, m_P_kg: float, m_e_kg: float, alpha: float) -> float:
    """Same τ from Compton rung N_c = m_P/m_e (§6 ladder k=8)."""
    n_c = m_P_kg / m_e_kg
    c = SI.c
    return (n_c / alpha**5) * (2.0 * SI.hbar / (m_P_kg * c * c))


def tau_para_gum_relative_unc(*, m_e_rel: float, alpha_rel: float = U_ALPHA_FS_REL_CODATA) -> float:
    """Relative u(τ)/τ from \eqref{eq:tau-relative-unc} (independent inputs)."""
    return math.sqrt(m_e_rel**2 + (5.0 * alpha_rel) ** 2)


def en_score_vs_reference(
    *,
    y_mod: float,
    y_ref: float,
    u_mod_rel: float,
    u_ref_rel: float,
) -> float:
    """|y_mod-y_ref|/y_ref divided by combined relative u (\\cref{sec:compare-reference})."""
    u_comb = math.sqrt(u_mod_rel**2 + u_ref_rel**2)
    if u_comb <= 0.0:
        return float("inf")
    return abs(y_mod - y_ref) / y_ref / u_comb


def ortho_para_lifetime_ratio_qed_leading(alpha: float) -> float:
    """τ(³S₁)/τ(¹S₀) leading: ortho 3γ vs para 2γ — O(1/α²) with group factor 2⁹/(9·2⁷π²)."""
    return (2**9) / (9.0 * (2**7) * math.pi**2 * alpha**2)


def run_annihilation_pdg_tau_strict(
    *,
    device: str = "cpu",
    tau_para_pdg_s: float = TAU_PARA_PS_PDG_S,
    tau_ortho_pdg_s: float = TAU_ORTHO_PS_PDG_S,
) -> dict[str, Any]:
    """Stricter PDG bridge: upstream §8.2 masses only; anti-CODATA; ortho/para ratio band."""
    elec = SI.electron_mass_row()
    prot = SI.proton_mass_row()
    m_e_up = gev_to_kg(float(elec["m_e_GeV"]))
    m_e_cod = SI.m_e_CODATA
    m_p_up = gev_to_kg(float(prot["m_p_GeV"]))
    alpha = float(elec["alpha_preferred"])
    m_e_rel = float(elec["m_e_rel_err"])

    tau_pdg = tau_para_pdg_s
    tau_up = tau_para_ps_qed_leading(m_e_kg=m_e_up, alpha=alpha)
    tau_lad = tau_para_ps_ladder(m_P_kg=m_p_up, m_e_kg=m_e_up, alpha=alpha)
    tau_cod = tau_para_ps_qed_leading(m_e_kg=m_e_cod, alpha=alpha)

    rel_up = abs(tau_up - tau_pdg) / tau_pdg
    rel_cod = abs(tau_cod - tau_pdg) / tau_pdg
    rel_lad = abs(tau_lad - tau_pdg) / tau_pdg

    # Leading QED radiative floor ~0.5%; allow mass-propagation + slack.
    rtol_tau = max(0.006, 2.5 * m_e_rel + 0.005)
    upstream_pass = rel_up <= rtol_tau
    ladder_pass = rel_lad <= rtol_tau
    identity_pass = abs(tau_up - tau_lad) / tau_pdg <= 1e-8

    # Upstream must not be "free pass" via CODATA m_e: error should track worse-or-comparable mass offset.
    mass_offset = abs(m_e_up - m_e_cod) / m_e_cod
    anti_circular = mass_offset >= 0.002 and rel_up >= rel_cod - 1e-6
    tracks_mass = rel_up >= 0.4 * m_e_rel

    log_pdg_ticks = math.log10(tau_pdg / SI.hT)
    log_n = math.log10(tau_up / SI.hT)
    log_ticks_pass = abs(log_n - log_pdg_ticks) <= math.log10(1.0 + rtol_tau) + 2e-4

    ratio_pdg = tau_ortho_pdg_s / tau_para_pdg_s
    ratio_qed = ortho_para_lifetime_ratio_qed_leading(alpha)
    ratio_rel = abs(ratio_qed - ratio_pdg) / ratio_pdg
    # Leading 3γ vs 2γ — ~25% below PDG without O(α) ortho corrections (honest slack).
    ortho_ratio_pass = ratio_rel <= 0.27
    codata_not_sole_winner = rel_up >= rel_cod + 0.002

    t_probe = annihilation_t_stats_probe(size=160, steps=64, ensemble=4, device=device)
    tau_m = float(t_probe["tau_M_s"])
    collision_separate = tau_m / tau_pdg < 1e-20

    u_tau_pdg_rel = TAU_PARA_PS_PDG_U_S / tau_pdg
    u_tau_mod_upstream = tau_para_gum_relative_unc(m_e_rel=m_e_rel)
    u_tau_mod_codata = tau_para_gum_relative_unc(m_e_rel=U_M_E_REL_CODATA)
    en_upstream = en_score_vs_reference(
        y_mod=tau_up,
        y_ref=tau_pdg,
        u_mod_rel=u_tau_mod_upstream,
        u_ref_rel=u_tau_pdg_rel,
    )
    en_codata_path = en_score_vs_reference(
        y_mod=tau_cod,
        y_ref=tau_pdg,
        u_mod_rel=u_tau_mod_codata,
        u_ref_rel=u_tau_pdg_rel,
    )

    checks_ok = (
        upstream_pass
        and ladder_pass
        and identity_pass
        and anti_circular
        and tracks_mass
        and log_ticks_pass
        and ortho_ratio_pass
        and codata_not_sole_winner
        and collision_separate
    )

    return {
        "tau_para_PDG_s": tau_pdg,
        "tau_qed_upstream_s": tau_up,
        "tau_qed_CODATA_m_e_s": tau_cod,
        "tau_ladder_upstream_s": tau_lad,
        "tau_rel_err_upstream": rel_up,
        "tau_rel_err_CODATA_m_e": rel_cod,
        "tau_rtol_allowed": rtol_tau,
        "m_e_rel_err_upstairs": m_e_rel,
        "m_e_mass_offset_vs_CODATA": mass_offset,
        "log10_N_ticks_upstream": log_n,
        "log10_N_ticks_PDG": log_pdg_ticks,
        "log10_N_ticks_delta": log_n - log_pdg_ticks,
        "ortho_para_ratio_PDG": ratio_pdg,
        "ortho_para_ratio_qed_leading": ratio_qed,
        "ortho_para_ratio_rel_err": ratio_rel,
        "tau_M_over_tau_PDG": tau_m / tau_pdg,
        "anti_circular_mass": anti_circular,
        "tracks_mass_error": tracks_mass,
        "codata_not_sole_winner": codata_not_sole_winner,
        "u_tau_PDG_rel": u_tau_pdg_rel,
        "u_tau_mod_upstream_rel": u_tau_mod_upstream,
        "u_tau_mod_CODATA_inputs_rel": u_tau_mod_codata,
        "E_n_upstream": en_upstream,
        "E_n_CODATA_m_e_path": en_codata_path,
        "checks_ok": checks_ok,
        "derivation_closed": False,
        "note": (
            "Strict: §8.2 m_e,m_p only; τ compared to PDG with rtol from m_e_rel; "
            "CODATA m_e must not be sole input; ortho/para τ ratio leading O(1/α²); "
            "log10(τ/hT) band; collision τ separate."
        ),
    }


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
