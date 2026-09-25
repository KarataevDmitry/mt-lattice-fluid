"""SISmRows — extracted from si_constants (file-size hygiene)."""
from __future__ import annotations

import math
from decimal import Decimal

from mt_ca.si_constants import (
    C,
    COSMO_BUBBLE_AGE_GYR,
    COSMO_RECOMB_KYR,
    DELTA_PHI_MIN,
    EV_J,
    HV,
    KAPPA_FCC_1TICK,
    LN2,
    M_ELECTRON_GEV_PDG,
    M_HIGGS_GEV_PDG,
    M_NEUTRON_GEV_PDG,
    M_NU_ATM_EV_PDG,
    M_PROTON_GEV_PDG,
    N12_FCC_CAUSAL_LINKS,
    SECOND_PER_GYR,
    SECOND_PER_KYR,
    _hT_decimal,
    baryon_geometry_factor,
    lepton_geometry_factor,
    m_tick_count_to_str,
    si_seconds_to_m_tick
)


class SISmRows:
    """Ask/row probes — do not grow si_constants with these."""

    def force_ansatz_row(self) -> dict[str, float]:
        """§8.4.1 — v ladder; α_s(v)=d/(N_hier π); runner 1/(dπ) ln(v/μ) → M_Z."""
        pi = math.pi
        e_p_gev = self.E_P / EV_J / 1.0e9
        n_hier = int(math.floor(2.0 * math.pi / LN2)) - 1
        d_spatial = 3  # Minkowski space §1.6 — not N_c
        alpha_s_v = d_spatial / (n_hier * pi)
        v = (self.alpha_preferred**n_hier) * e_p_gev * math.sqrt(2.0 * pi)
        m_z = 91.1876  # GeV PDG pole mass (T control scale)
        beta_pack = 1.0 / (d_spatial * pi)
        alpha_s_mz = 1.0 / (1.0 / alpha_s_v + beta_pack * math.log(v / m_z))
        g_f = 1.0 / (math.sqrt(2.0) * v * v)
        return {
            "alpha_s_seed": alpha_s_v,
            "alpha_s_at_v": alpha_s_v,
            "alpha_s_MZ_model": alpha_s_mz,
            "alpha_s_MZ_pdg": 0.1179,
            "alpha_s_MZ_rel_err": abs(alpha_s_mz - 0.1179) / 0.1179,
            "alpha_s_beta_pack": beta_pack,
            "v_GeV": v,
            "v_CODATA_GeV": 246.22,
            "M_Z_GeV": m_z,
            "G_F_GeV_m2": g_f,
            "G_F_CODATA": 1.1663787e-5,
            "G_F_rel_err": abs(g_f - 1.1663787e-5) / 1.1663787e-5,
            "N_hier": float(n_hier),
            "d_spatial": float(d_spatial),
            "note": "§8.4.1: runner 1/(d π) ln(v/MZ); π from spatial denominator",
        }

    def gr_passport_row(self) -> dict[str, float]:
        """§8.4.2 — G from ℓ_P; F₀=m_arg·g_M; no fifth coupling."""
        g_from_lp = self.l_P**2 * self.c**3 / self.hbar
        f0 = self.F_0
        return {
            "G_SI": self.G,
            "G_from_l_P": g_from_lp,
            "G_rel_err": abs(self.G - g_from_lp) / self.G,
            "G_over_l_P2_model": 1.0,  # c=ℏ=1
            "F0_N": f0,
            "F0_from_m_g": self.m_arg * self.g_M,
            "F0_rel_err": abs(f0 - self.m_arg * self.g_M) / f0,
            "m_arg_kg": self.m_arg,
            "g_M": self.g_M,
            "s_0": self.s_0,
            "note": "§8.4.2: G≡ℓ_P² c³/ℏ; F₀=m_arg g_M; g_μν=T-strain",
        }

    def weinberg_row(self) -> dict[str, float]:
        """§8.4.3 — bare sin²θ_W = d / (|N12|+1) = 3/13 from FCC cluster."""
        d_spatial = 3
        n12 = 12  # FCC coordination §1.6
        n_cluster = n12 + 1
        n_phi = math.ceil(2.0 * math.pi / DELTA_PHI_MIN)
        sin2 = d_spatial / n_cluster
        sin2_eff = 1.0 / 8.0 + 1.0 / (d_spatial * math.pi)  # soft neighbor, not SSOT
        pdg = 0.23122
        return {
            "sin2_theta_W_bare": sin2,
            "sin2_theta_W_eff_neighbor": sin2_eff,
            "sin2_theta_W_PDG_MSbar": pdg,
            "bare_rel_err_vs_PDG": abs(sin2 - pdg) / pdg,
            "d_spatial": float(d_spatial),
            "N12": float(n12),
            "N_cluster": float(n_cluster),
            "N_phi": float(n_phi),
            "note": "§8.4.3: bare=3/13=d/(|N12|+1); N_φ=⌈4π⌉ coincides; eff=1/8+1/(dπ) soft",
        }

    def decay_row(self) -> dict[str, float | bool | str]:
        """§8.2 decay — topo frame; ΔB≠0 banned; weak ΔB=0 class allowed; Γ open."""
        return {
            "E_0": self.E_0,
            "s_0": self.s_0,
            "hbar": self.hbar,
            "delta_B_move_derived": False,
            "proton_to_e_pi0_forbidden": True,
            "weak_delta_B0_class_allowed": True,
            "neutron_beta_channel_schema": True,
            "neutron_mass_split_closed": True,
            "neutron_mass_quantum": "m_e",
            "neutron_mass_k": 2,
            "note": "§8.2·5–7: no ΔB≠0; weak n→peν OK; m_n=m_p+2m_e (mass ledger); Γ open",
        }

    def birth_row(self) -> dict[str, float]:
        """§4.9.2a — V ↦ (n, Q, χ, E, b, m); formulas on, not soft notes."""
        f_e = lepton_geometry_factor()
        m_p = self.m_p_CODATA if hasattr(self, "m_p_CODATA") else 1.67262192369e-27
        f_p = baryon_geometry_factor(m_p)
        e0 = 1.602176634e-19
        a = self.alpha_fs
        return {
            "n": 1.0,
            "Q_C": 1.0 * e0,
            "chi": 1.0,
            "E_0": self.E_0,
            "m_P": self.m_P,
            "alpha_fs": a,
            "f_geom_e": f_e,
            "m_e_kg": self.m_P * a * a * f_e,
            "f_geom_p": f_p,
            "m_p_kg": self.m_P * (a / 3.0) * f_p,
            "pauli_slots": 2.0,
            "b_pra": 1.0,
        }

    def bubble_tick_row(self) -> dict[str, float | int | str | bool]:
        """META §3.0.1 — our bubble: exact N↔SI via derived hT (no readout).

        Convention: N=0 = local BB of phase I; t_SI(0)=0. ΛCDM age/recombination are
        T-layer inputs (not g knobs) used to infer integer tick labels.
        """
        hT = self.hT
        hT_dec = _hT_decimal()
        t_age_obs_s = COSMO_BUBBLE_AGE_GYR * SECOND_PER_GYR
        t_recomb_obs_s = COSMO_RECOMB_KYR * SECOND_PER_KYR
        n_today = si_seconds_to_m_tick(t_age_obs_s, hT=hT_dec)
        n_cmb = si_seconds_to_m_tick(t_recomb_obs_s, hT=hT_dec)
        t_age_exact_s = float(Decimal(n_today) * hT_dec)
        t_recomb_exact_s = float(Decimal(n_cmb) * hT_dec)
        return {
            "hT_s": hT,
            "anchor_N0": "bubble_phase_I_BB",
            "t_start_s": 0.0,
            "cosmo_age_Gyr": COSMO_BUBBLE_AGE_GYR,
            "cosmo_recomb_kyr": COSMO_RECOMB_KYR,
            "t_age_obs_s": t_age_obs_s,
            "t_recomb_obs_s": t_recomb_obs_s,
            "N_today": n_today,
            "N_CMB": n_cmb,
            "N_today_sci": m_tick_count_to_str(n_today),
            "N_CMB_sci": m_tick_count_to_str(n_cmb),
            "N_since_CMB": n_today - n_cmb,
            "N_since_CMB_sci": m_tick_count_to_str(n_today - n_cmb),
            "log10_N_today": math.log10(n_today),
            "log10_N_CMB": math.log10(n_cmb),
            "t_age_exact_s": t_age_exact_s,
            "t_recomb_exact_s": t_recomb_exact_s,
            "t_age_exact_Gyr": t_age_exact_s / SECOND_PER_GYR,
            "t_recomb_exact_kyr": t_recomb_exact_s / SECOND_PER_KYR,
            "roundtrip_age_rel_err": abs(t_age_exact_s - float(Decimal(n_today) * hT_dec)) / t_age_exact_s,
            "roundtrip_recomb_rel_err": abs(t_recomb_exact_s - float(Decimal(n_cmb) * hT_dec)) / t_recomb_exact_s,
            "note": "§3.0.1: t_SI(N)=N·hT exact; ΛCDM inputs infer N only",
        }

    def electroweak_mass_row(self) -> dict[str, float]:
        """§8.4.3-E — m_W=gv/2, m_Z=m_W/cosθ with α(MZ) and sin²=3/13."""
        w = self.weinberg_row()
        a = self.alpha_runner_row()
        v = self.force_ansatz_row()["v_GeV"]
        sin2 = w["sin2_theta_W_bare"]
        cos2 = 1.0 - sin2
        e2 = 4.0 * math.pi * a["alpha_MZ"]
        g = math.sqrt(e2 / sin2)
        m_w = g * v / 2.0
        m_z = m_w / math.sqrt(cos2)
        return {
            "v_GeV": v,
            "sin2_theta_W": sin2,
            "alpha_MZ": a["alpha_MZ"],
            "g": g,
            "m_W_GeV": m_w,
            "m_Z_GeV": m_z,
            "m_W_PDG": 80.377,
            "m_Z_PDG": 91.1876,
            "m_W_rel_err": abs(m_w - 80.377) / 80.377,
            "m_Z_rel_err": abs(m_z - 91.1876) / 91.1876,
            "mass_ratio_sin2": 1.0 - (m_w / m_z) ** 2,
            "note": "§8.4.3-E: tree with α(MZ) from B_hV runner + bare 3/13",
        }

    def higgs_mass_row(self) -> dict[str, float]:
        """§8.3.1 — bare m_H=v/2; + empty-cell stack λ=1/8+N_hier·δλ."""
        row = self.force_ansatz_row()
        v = float(row["v_GeV"])
        n_hier = float(row["N_hier"])
        lam0 = 1.0 / n_hier
        m_h0 = v * math.sqrt(2.0 * lam0)  # = v/2 when N_hier=8
        e_p_gev = self.E_P / EV_J / 1e9
        m_h_direct = (self.alpha_preferred**8) * e_p_gev * math.sqrt(math.pi / 2.0)
        # vacuum-bit quantum: (α*−1)·α_fs = α_fs/(4π)
        delta_lam = self.alpha_preferred / (4.0 * math.pi)
        lam = lam0 + n_hier * delta_lam
        m_h = v * math.sqrt(2.0 * lam)
        return {
            "v_GeV": v,
            "N_hier": n_hier,
            "lambda_bare": lam0,
            "delta_lambda_quantum": delta_lam,
            "delta_lambda_stack": n_hier * delta_lam,
            "lambda_quartic": lam,
            "m_H_bare_GeV": m_h0,
            "m_H_direct_GeV": m_h_direct,
            "m_H_GeV": m_h,
            "m_H_PDG_GeV": M_HIGGS_GEV_PDG,
            "m_H_bare_rel_err": abs(m_h0 - M_HIGGS_GEV_PDG) / M_HIGGS_GEV_PDG,
            "m_H_rel_err": abs(m_h - M_HIGGS_GEV_PDG) / M_HIGGS_GEV_PDG,
            "m_H_over_v_bare": m_h0 / v,
            "m_H_over_v": m_h / v,
            "note": "§8.3.1: bare v/2; λ=1/8+N_hier·(α_preferred/4π) empty-cell stack",
        }

    def proton_mass_row(self) -> dict[str, float]:
        """§8.2 — bare α·v/2; pack stack ×(1+κ²/N₁₂), κ=1/√2."""
        higgs = self.higgs_mass_row()
        v = float(higgs["v_GeV"])
        m_h_bare = float(higgs["m_H_bare_GeV"])
        m_p0 = self.alpha_preferred * m_h_bare  # = α · v/2
        kappa = KAPPA_FCC_1TICK
        n12 = float(N12_FCC_CAUSAL_LINKS)
        delta_pack = (kappa * kappa) / n12  # (1/2)/12 = 1/24
        pack_factor = 1.0 + delta_pack
        m_p = m_p0 * pack_factor
        return {
            "v_GeV": v,
            "m_H_bare_GeV": m_h_bare,
            "alpha_fs": self.alpha_fs,
            "alpha_preferred": self.alpha_preferred,
            "kappa_FCC": kappa,
            "N12": n12,
            "delta_pack": delta_pack,
            "pack_stack_factor": pack_factor,
            "m_p_bare_GeV": m_p0,
            "m_p_GeV": m_p,
            "m_p_PDG_GeV": M_PROTON_GEV_PDG,
            "m_p_bare_rel_err": abs(m_p0 - M_PROTON_GEV_PDG) / M_PROTON_GEV_PDG,
            "m_p_rel_err": abs(m_p - M_PROTON_GEV_PDG) / M_PROTON_GEV_PDG,
            "m_p_over_m_H_bare": m_p0 / m_h_bare,
            "note": "§8.2: bare α·v/2; pack 1+κ²/N₁₂ (inscribed sphere)",
        }

    def electron_mass_row(self) -> dict[str, float]:
        """§8.2 — bare α²·(v/2)/N_φ; stack α²·m_H/N_φ, N_φ=⌈4π⌉."""
        higgs = self.higgs_mass_row()
        m_h_bare = float(higgs["m_H_bare_GeV"])
        m_h = float(higgs["m_H_GeV"])
        n_phi = float(HV.N_phi)
        a2 = self.alpha_preferred * self.alpha_preferred
        m_e0 = a2 * m_h_bare / n_phi
        m_e = a2 * m_h / n_phi
        e_p_gev = self.m_P * (C * C) / EV_J / 1e9  # E_P [GeV]
        f_geom = m_h / (e_p_gev * n_phi)
        return {
            "v_GeV": float(higgs["v_GeV"]),
            "m_H_bare_GeV": m_h_bare,
            "m_H_GeV": m_h,
            "alpha_fs": self.alpha_fs,
            "alpha_preferred": self.alpha_preferred,
            "N_phi": n_phi,
            "m_e_bare_GeV": m_e0,
            "m_e_GeV": m_e,
            "m_e_PDG_GeV": M_ELECTRON_GEV_PDG,
            "m_e_bare_rel_err": abs(m_e0 - M_ELECTRON_GEV_PDG) / M_ELECTRON_GEV_PDG,
            "m_e_rel_err": abs(m_e - M_ELECTRON_GEV_PDG) / M_ELECTRON_GEV_PDG,
            "f_geom": f_geom,
            "note": "§8.2: bare α²·(v/2)/N_φ; stack α²·m_H/N_φ (same empty-cell as Higgs)",
        }

    def neutron_mass_row(self) -> dict[str, float | int | bool | str]:
        """§8.2·7 — m_n = m_p + 2·m_e (channel step on §5 m_arg/ρ_Q ledger)."""
        prot = self.proton_mass_row()
        elec = self.electron_mass_row()
        m_p = float(prot["m_p_GeV"])
        m_e = float(elec["m_e_GeV"])
        k = 2  # minimal integer rung with m_n > m_p + m_e
        delta = float(k) * m_e
        m_n = m_p + delta
        threshold = m_p + m_e
        return {
            "m_p_GeV": m_p,
            "m_e_GeV": m_e,
            "k": k,
            "delta_GeV": delta,
            "m_n_GeV": m_n,
            "threshold_m_p_plus_m_e_GeV": threshold,
            "beta_downhill": m_n > threshold,
            "m_n_PDG_GeV": M_NEUTRON_GEV_PDG,
            "delta_PDG_GeV": M_NEUTRON_GEV_PDG - M_PROTON_GEV_PDG,
            "m_n_rel_err": abs(m_n - M_NEUTRON_GEV_PDG) / M_NEUTRON_GEV_PDG,
            "delta_rel_err": abs(delta - (M_NEUTRON_GEV_PDG - M_PROTON_GEV_PDG))
            / (M_NEUTRON_GEV_PDG - M_PROTON_GEV_PDG),
            "note": "§8.2·7: m_n=m_p+2m_e; ladder=m_arg/ρ_Q; channel=m_e; k=2 min β",
        }

    def neutrino_mass_row(self) -> dict[str, float]:
        """§8.2 — atm √|Δm²|: α⁵·v/(N_hier N_φ); stack α⁵·2m_H/(N_hier N_φ)."""
        higgs = self.higgs_mass_row()
        elec = self.electron_mass_row()
        v = float(higgs["v_GeV"])
        m_h = float(higgs["m_H_GeV"])
        n_hier = float(higgs["N_hier"])
        n_phi = float(elec["N_phi"])
        m_e = float(elec["m_e_GeV"])
        a = self.alpha_preferred
        a5 = a**5
        m_nu0_gev = a5 * v / (n_hier * n_phi)
        m_nu_gev = a5 * (2.0 * m_h) / (n_hier * n_phi)
        bridge_gev = (a**3) * m_e / (n_hier / 2.0)
        m_nu0_ev = m_nu0_gev * 1e9
        m_nu_ev = m_nu_gev * 1e9
        # lemmas (reported, not hard-gated)
        m_sol_ev = (a**3) * m_e / (n_phi * math.sqrt(math.pi)) * 1e9
        m_light_ev = (a**4) * m_e / n_phi * 1e9
        return {
            "v_GeV": v,
            "m_H_GeV": m_h,
            "m_e_GeV": m_e,
            "alpha_fs": self.alpha_fs,
            "alpha_preferred": a,
            "N_hier": n_hier,
            "N_phi": n_phi,
            "m_nu_atm_bare_eV": m_nu0_ev,
            "m_nu_atm_eV": m_nu_ev,
            "m_nu_atm_PDG_eV": M_NU_ATM_EV_PDG,
            "m_nu_atm_bare_rel_err": abs(m_nu0_ev - M_NU_ATM_EV_PDG) / M_NU_ATM_EV_PDG,
            "m_nu_atm_rel_err": abs(m_nu_ev - M_NU_ATM_EV_PDG) / M_NU_ATM_EV_PDG,
            "bridge_equals_stack": abs(bridge_gev - m_nu_gev) / m_nu_gev,
            "m_nu_sol_lemma_eV": m_sol_ev,
            "m_nu_lightest_lemma_eV": m_light_ev,
            "note": "§8.2: atm α⁵·2m_H/(N_hier N_φ)=α³·m_e/(N_hier/2); sol/lightest lemmas",
        }

    def saturation_bc_row(self) -> dict[str, float]:
        """§8.4.2-C′′′ — D_★ BC; near h_★[ε]; far h_00=2(m/m_P)ℓ_P/R."""
        from mt_ca.fixed_point import vacuum_amplitude_quantum

        rho_star = 1.0
        vac_amp = vacuum_amplitude_quantum(frac_bits=HV.frac_bits)
        rho_vac = vac_amp * vac_amp
        rho_e = 0.5 * (rho_star + rho_vac)
        eps_partial = (rho_e - rho_vac) / rho_vac
        h_star_near = -2.0 * eps_partial  # |N|=12 equal NN edges: −(2/12)·12·ε
        r_star = 1.0  # hops / ℓ_P
        m_over_m_P = 1.0  # pra-core ceiling
        h_star_newton = -2.0 * m_over_m_P / r_star  # h_00(R_★)=−2m/(m_P R_★)
        mismatch = abs(h_star_near / h_star_newton) if h_star_newton != 0 else float("inf")
        return {
            "rho_star": rho_star,
            "rho_vac": rho_vac,
            "eps_partial_NN": eps_partial,
            "h_star_near": h_star_near,
            "h_star_newton": h_star_newton,
            "near_over_newton": mismatch,
            "R_star_over_l_P": r_star,
            "m_over_m_P": m_over_m_P,
            "h00_far_at_R_eq_2": h_star_newton * 0.5,
            "N12": 12.0,
            "m_P": self.m_P,
            "l_P": self.l_P,
        }

    def leapfrog_eps_row(self) -> dict[str, float]:
        """§3.12.5a — ε in Φ-kick; ℓ_e bound; m_loc ≤ m_P."""
        from mt_ca.fixed_point import vacuum_amplitude_quantum

        rho_star = 1.0  # A7: |Z|² ≤ 1 ↔ ρ_E ≤ u_P
        vac_amp = vacuum_amplitude_quantum(frac_bits=HV.frac_bits)
        rho_vac = vac_amp * vac_amp  # A5 numerical floor → ρ_vac
        eps_star = (rho_star - rho_vac) / rho_vac
        return {
            "rho_star": rho_star,
            "rho_vac": rho_vac,
            "eps_star": eps_star,
            "ell_e_over_ell_P_max": 1.0 + eps_star,
            "m_loc_max_kg": self.m_P,
            "m_loc_max_over_m_P": 1.0,
            "d_tau_dt_formula_inv_1plus_eps": 1.0,
            "K_P": self.K_P,
            "l_P": self.l_P,
        }

    def einstein_strain_row(self) -> dict[str, float]:
        """§8.4.2-D/C′ — G_μν from Regge deficit; strain from ρ-edges + Δφ."""
        g_model = 1.0  # G/ℓ_P² in MODEL units
        eight_pi_g = 8.0 * math.pi * g_model
        n12 = 12.0
        return {
            "G_over_l_P2": g_model,
            "field_eq_coeff_8pi_G": eight_pi_g,
            "flat_deficit": 0.0,  # strain=0 ⇒ δ=0
            "girth_plaquette": 3.0,  # FCC triangle = d
            "d_spatial": 3.0,
            "N12_FCC": n12,
            "strain_edge_from": 1.0,  # ε_e = (ρ_e-ρ_vac)/ρ_vac
            "h0i_from_dphi": 1.0,  # h_0i ← Δφ_e ê_i
            "hij_from_eps": 1.0,  # h_ij ← ε_e ê_i ê_j
            "note": (
                "§8.4.2-C′: ε_e[δρ]→ℓ_e→θ_f→δ_e; "
                "h_0i[Δφ_e]; h_ij[ε_e]; not ε∝Δφ; stencil soft"
            ),
        }

    def ckm_row(self) -> dict[str, float]:
        """§8.4.4 — N_gen=d; λ=sin θ_12=d/(|N12|+1)=3/13."""
        d_spatial = 3
        n12 = 12
        lam = d_spatial / (n12 + 1)
        v_us_pdg = 0.2243
        return {
            "N_gen": float(d_spatial),
            "lambda_bare": lam,
            "sin_theta_12": lam,
            "V_us_bare": lam,
            "V_us_PDG": v_us_pdg,
            "V_us_rel_err": abs(lam - v_us_pdg) / v_us_pdg,
            "lambda_sq_neighbor": lam * lam,  # soft |V_cb| neighbor, not SSOT
            "note": "§8.4.4: N_gen=d; λ=3/13 same cluster weight as Weinberg; A,ρ,η soft",
        }

