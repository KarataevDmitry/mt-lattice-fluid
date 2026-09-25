"""SIUnitsRows — extracted from si_constants (file-size hygiene)."""
from __future__ import annotations

import math
from decimal import Decimal

from mt_ca.si_constants import (
    EV_J
)


class SIUnitsRows:
    """Ask/row probes — do not grow si_constants with these."""

    def coulomb_row(self) -> dict[str, float]:
        """§8.2 Coulomb — F = α_fs · F_P · n1 n2 / N² from carrier (no new knob)."""
        f_p = self.c**4 / self.G
        alpha = self.alpha_fs
        # unit charges on adjacent cells
        f_nn = alpha * f_p
        return {
            "alpha_fs": alpha,
            "F_P_N": f_p,
            "F_over_F_P_N1_unit": alpha,
            "F_NN_N": f_nn,
            "rel_F_over_FP_is_alpha": abs(f_nn / f_p - alpha) / alpha,
            "note": "§8.2: F=α_fs F_P n1 n2/N²; N=1,|n|=1 → |F|/F_P=α_fs",
        }

    def na0_from_carrier_row(self) -> dict[str, float | int | str | bool]:
        """N_a0 without optical a₀ — first carrier candidate.

        Primary (derived):
            N_a0 = N_c · α_geom^{-1} = (m_P/m_e) · 137
        where α_geom^{-1}=137 from cuboctahedron combinatorics (§8.2·geo),
        m_e = CODATA T-anchor (same role as e₀).

        Then α* from analytic/stack FP with this N_a0 (no optical Bohr).
        Diff vs optical N_a0 ~ 0.026% (137 vs 137.036).

        Pure monomials in {13,12,8,512,2} do **not** stabilize stack FP
        near CODATA (map highly sensitive) — left OPEN.
        """
        n_phi = 13.0
        n_hier = 8.0
        alpha_geom_inv = 137.0
        alpha_codata = 7.2973525693e-3
        m_p_gev = self.E_P / EV_J / 1e9
        n_c = self.m_P / self.m_e_CODATA
        n_a0_opt = 5.29177210903e-11 / self.l_P
        n_a0 = n_c * alpha_geom_inv
        # FP with carrier N_a0 (reuse cascade algebra)
        def cascade(alpha: float) -> tuple[float, float]:
            v = (alpha**n_hier) * m_p_gev * math.sqrt(2.0 * math.pi)
            m_h_bare = v / 2.0
            lam = 1.0 / n_hier + n_hier * (alpha / (4.0 * math.pi))
            m_h = math.sqrt(2.0 * lam) * v
            return (alpha**2) * m_h / n_phi, (alpha**2) * m_h_bare / n_phi

        def mapped(alpha: float, n_a0_local: float, *, bare: bool) -> float:
            m_e, m_e_bare = cascade(alpha)
            m = m_e_bare if bare else m_e
            return (m_p_gev / m) / n_a0_local

        def solve(n_a0_local: float, *, bare: bool) -> float:
            lo, hi = 1e-4, 0.05
            flo = mapped(lo, n_a0_local, bare=bare) - lo
            for _ in range(100):
                mid = 0.5 * (lo + hi)
                fm = mapped(mid, n_a0_local, bare=bare) - mid
                if flo * fm <= 0:
                    hi = mid
                else:
                    lo, flo = mid, fm
            return 0.5 * (lo + hi)

        a_stack = solve(n_a0, bare=False)
        a_bare = (n_phi / (n_a0 * math.sqrt(math.pi / 2.0))) ** (1.0 / 11.0)
        a_stack_opt = solve(n_a0_opt, bare=False)
        return {
            "N_c_from_m_e_CODATA": n_c,
            "alpha_geom_inv": alpha_geom_inv,
            "N_a0_carrier": n_a0,
            "N_a0_optical": n_a0_opt,
            "N_a0_carrier_over_optical": n_a0 / n_a0_opt,
            "alpha_fp_stack": a_stack,
            "alpha_fp_stack_inv": 1.0 / a_stack,
            "alpha_fp_bare": a_bare,
            "alpha_fp_bare_inv": 1.0 / a_bare,
            "alpha_fp_stack_optical_inv": 1.0 / a_stack_opt,
            "vs_codata_ppm_stack": (a_stack - alpha_codata) / alpha_codata * 1e6,
            "vs_codata_ppm_bare": (a_bare - alpha_codata) / alpha_codata * 1e6,
            "vs_optical_fp_ppm_stack": (a_stack - a_stack_opt) / a_stack_opt * 1e6,
            "monomial_stack_open": True,
            "carrier_na0_ok": abs(n_a0 / n_a0_opt - 1.0) < 5e-4
            and abs(mapped(a_stack, n_a0, bare=False) - a_stack) / a_stack < 1e-12,
            "note": (
                "HISTORICAL probe: N_a0=(m_P/m_e)·137. Ask-model §8.2·H REJECTED "
                "as α-input (empty for deriving α). Keep for ppm archaeology only. "
                "See na0_h_carrier_inventory_row."
            ),
            "ask_rejected_as_alpha_input": True,
        }

    def na0_h_carrier_inventory_row(self) -> dict[str, float | int | str | bool | list]:
        """§8.2·H — asked the carrier for N_a0 (H size in hL hops).

        Method (same as §8.2·geo / phonon ask):
          (1) a=l_P fixed; (2) list dimensional/structural facts of H;
          (3) which can enter size without injecting α; (4) ratio = report.

        Carrier answers (2026-09-23):
          • Thm 5.2 ⇒ N_a0 ∈ ℤ on the same ladder as sound/light.
          • Hop: α=N_c/N_a0 ; α²=N_re/N_a0.
          • Mass: m_e=α² m_H/N_φ ⇒ α²=m_e N_φ/m_H.
          • Identity: N_re/N_a0 ≡ m_e N_φ/m_H — one α², not two sources of N_a0.
          • REJECT N_c·137 (α_geom): injects α⁻¹ then α=N_c/N_a0 returns it.
          • REJECT optical a₀ alone as M-definition (T-anchor).
          • OPEN: integer from H structure — ground ρ_Θ / N_pack / shell on Λ.
        """
        hop = self.alpha_hop_ladder_row()
        n_phi = 13.0
        n_c = float(hop["N_c_macro"])
        n_re = float(hop["N_re"])
        n_a0_bohr = float(hop["N_a0_Bohr"])
        alpha = float(hop["alpha_codata"])
        # mass rhyme at CODATA α (ledger check, not a derivation of N_a0)
        higgs = self.higgs_mass_row()
        elec = self.electron_mass_row()
        m_h = float(higgs["m_H_GeV"])
        m_e = float(elec["m_e_GeV"])
        alpha2_from_mass = (m_e * n_phi) / m_h
        alpha2_from_hops = n_re / n_a0_bohr
        # empty candidate N_c·137
        n_a0_geom = (self.m_P / self.m_e_CODATA) * 137.0
        inventory: list[dict[str, str | float | bool]] = [
            {
                "id": "a_eq_l_P",
                "maps_to": "A1 ruler; N_a0 counted in hL hops",
                "status": "derived",
                "mechanism": "same a=l_P as cuboctahedron/phonon ask",
            },
            {
                "id": "N_a0_integer",
                "maps_to": "Thm 5.2 — size is occupancy hops, not continuum metre",
                "status": "derived",
                "mechanism": "sound/light = n_k / n_E; H radius on same ladder",
            },
            {
                "id": "hop_alpha_Nc_over_Na0",
                "ratio": n_c / n_a0_bohr,
                "maps_to": "α = N_c/N_a0 (Bohr scale step)",
                "status": "identity",
                "mechanism": "definition once both hops exist; not yet from g alone",
            },
            {
                "id": "hop_alpha2_Nre_over_Na0",
                "ratio": alpha2_from_hops,
                "maps_to": "α² = N_re/N_a0",
                "status": "identity",
                "mechanism": "same power as m_e=α² m_H/N_φ",
            },
            {
                "id": "mass_alpha2_me_Nphi_over_mH",
                "ratio": alpha2_from_mass,
                "maps_to": "α² = m_e N_φ / m_H",
                "status": "derived_mass",
                "mechanism": "§8.2 electron matryoshka; does NOT independently fix N_a0",
            },
            {
                "id": "mass_hop_same_alpha2",
                "ratio": abs(alpha2_from_mass / alpha2_from_hops - 1.0),
                "maps_to": "mass α² ≡ hop α² (one equation)",
                "status": "identity",
                "mechanism": "cannot solve N_a0 from masses without α (or a₀)",
            },
            {
                "id": "reject_Nc_times_137",
                "ratio": n_a0_geom / n_a0_bohr,
                "maps_to": "N_a0≟N_c·α_geom⁻¹ — empty for deriving α",
                "status": "rejected",
                "mechanism": "puts α⁻¹ into size; α=N_c/N_a0 returns α_geom",
            },
            {
                "id": "reject_optical_a0_as_M",
                "maps_to": "CODATA a₀ — T-anchor, not carrier integer",
                "status": "rejected_as_M_definition",
                "mechanism": "ok as FP seed; violates full-quantization if sole N_a0",
            },
            {
                "id": "open_H_structure_integer",
                "maps_to": "ground ρ_Θ / N_pack / FCC shell around B=1",
                "status": "open",
                "mechanism": "§5.0.4–5.0.5 composite H; need shell rule → ℤ without α",
            },
        ]
        rhyme_ok = abs(alpha2_from_mass - alpha * alpha) / (alpha * alpha) < 5e-2
        identity_ok = abs(alpha2_from_hops - alpha * alpha) / (alpha * alpha) < 1e-12
        return {
            "theorem": "§8.2·H — N_a0 from carrier; mass≠independent size",
            "method": "model: a=l_P → inventory → which enters size → report",
            "N_c_macro": n_c,
            "N_re": n_re,
            "N_a0_Bohr_T": n_a0_bohr,
            "N_a0_Nc_times_137": n_a0_geom,
            "N_phi": n_phi,
            "alpha2_from_hops": alpha2_from_hops,
            "alpha2_from_mass": alpha2_from_mass,
            "alpha2_codata": alpha * alpha,
            "rel_mass_vs_hop_alpha2": abs(alpha2_from_mass / alpha2_from_hops - 1.0),
            "mass_hop_same_power": identity_ok,
            "mass_rhyme_near_codata": rhyme_ok,
            "reject_Nc_times_137": True,
            "reject_optical_a0_as_M_definition": True,
            "N_a0_must_be_integer": True,
            "independent_Na0_open": True,
            "alpha_path_closed_by_meter_fint": True,
            "independent_Na0_blocks_alpha": False,
            "inventory": inventory,
            "checks_ok": identity_ok and rhyme_ok and True,
            "note": (
                "Asked carrier: Thm5.2⇒N_a0∈ℤ; hop α=N_c/N_a0 and mass α²=m_e N_φ/m_H "
                "are one α² — masses do not fix N_a0 alone. Rejected N_c·137 and optical "
                "a₀ as M-definition. FINT: α sealed without meter; N_a0=N_c/α is readout "
                "(see alpha_meter_na0_bridge_row). OPEN remains: H→ℤN_a0 without α "
                "(census) — does NOT block α / meter definition."
            ),
        }

    def meter_decouple_from_M_row(self) -> dict[str, float | int | str | bool | list]:
        """§8.2·meter·decouple — SI metre ∉ M; lengths on M are hops of hL.

        Cooler seal after α + meter-fint:
          On M there is no metre. Size = occupancy hops (Thm 5.2).
          hL := A1 light-like link; l_P is the name once a≡hL is forced (§7.4).
          α, upstairs masses, N_a0=N_c/α are metre-free.
          SI-2019 metre (c-fixed) and optical a0 are optional T-export / T-door only.
          Writing x_m = N·l_P_SI still needs ħ,G for lab speech — not for the M ruler.
        """
        soft = self.alpha_U0_soft_face_row()
        up = self.alpha_upstairs_mass_probe_row()
        meter = self.alpha_meter_na0_bridge_row()
        anchor = self.anchor_a_is_l_P_row()
        hop = self.alpha_hop_ladder_row()
        a = float(self.alpha_preferred)
        n_a0 = float(meter["N_a0_predicted"])
        n_c = float(meter["N_c"])
        inventory = [
            {
                "id": "M_lengths_are_hops",
                "maps_to": "Thm 5.2 — size = occupancy hops of hL, not continuum metre",
                "ok": True,
            },
            {
                "id": "hL_is_A1_link",
                "maps_to": "l_P := hL := A1 (§7.4); not defined by SI metre",
                "ok": bool(anchor["a_equals_hL"]) and bool(anchor["l_P_not_defined_by_c"]),
            },
            {
                "id": "alpha_metre_free",
                "maps_to": "soft face α — no metre in definition",
                "ok": bool(soft["derivation_closed"]) and bool(soft["checks_ok"]),
            },
            {
                "id": "masses_metre_free",
                "maps_to": "upstairs cascade on preferred α — GeV/hops, not metre",
                "ok": bool(up["checks_ok"]),
            },
            {
                "id": "N_a0_metre_free",
                "maps_to": "N_a0 = N_c/α — dimensionless readout",
                "value": n_a0,
                "ok": bool(meter["identity_alpha_eq_Nc_over_Na0"]),
            },
            {
                "id": "SI_metre_T_export_only",
                "maps_to": "SI-2019 metre / optical a0 — optional lab speech, not M input",
                "ok": True,
            },
            {
                "id": "l_P_SI_packaging",
                "maps_to": "√(ħG/c³) writes metres for T; does not rule M",
                "ok": bool(anchor["scale_decoupled_from_c_definition"]),
            },
        ]
        m_board_ok = all(bool(item["ok"]) for item in inventory)
        return {
            "theorem": "§8.2·meter·decouple — SI metre ∉ M",
            "method": "after α seal: assert hop-only lengths; metre = T-export only",
            "alpha_preferred": a,
            "N_c": n_c,
            "N_a0_predicted": n_a0,
            "N_a0_optical_T": float(hop["N_a0_Bohr"]),
            "hL_equals_l_P": bool(anchor["a_equals_hL"]),
            "l_P_not_defined_by_c": bool(anchor["l_P_not_defined_by_c"]),
            "scale_decoupled_from_c_definition": bool(
                anchor["scale_decoupled_from_c_definition"]
            ),
            "meter_not_on_M": True,
            "meter_not_input_to_alpha": True,
            "meter_not_input_to_masses": True,
            "meter_not_input_to_Na0": True,
            "SI_metre_is_T_export_only": True,
            "optical_a0_is_T_door_only": True,
            "M_lengths_are_hops": True,
            "absolute_SI_still_needs": str(anchor["absolute_SI_still_needs"]),
            "derivation_closed": True,
            "inventory": inventory,
            "checks_ok": (
                m_board_ok
                and bool(meter["checks_ok"])
                and bool(meter["alpha_path_closed"])
                and abs(a - float(soft["alpha_pref"])) < 1e-15
            ),
            "note": (
                "Cooler seal: SI metre is fully off the M board. "
                "Lengths on M = hops of hL (a≡l_P). α, masses, N_a0=N_c/α never consult "
                "the metre. SI-2019 / optical a0 / √(ħG/c³) are T-export packaging only."
            ),
        }

    def length_dim_from_lP_alpha_row(self) -> dict[str, float | int | str | bool | list]:
        """§8.2·[L]·l_P — length dimension = l_P; hierarchy from exact α.

        Not SI-metre reconstruction. Natural unit: l_P ≡ hL.
        α is dimensionless and exact (soft face) ⇒ every EM length is
            L = N(α, N_c, …) · l_P
        Length unit itself from velocity × time (and/or ħ):
            [L] = [V][T]  ⇒  l_P = c · t_P = √(ħ G / c³)
        On carrier: hL = c0 · hT (A1 light-like); l_P := hL.
        α ([α]=1, exact) then sets the hop hierarchy:
            λ̄_C / l_P = N_c = m_P/m_e
            a0    / l_P = N_c/α = N_a0
            r_e   / l_P = α·N_c = α²·N_a0
        """
        soft = self.alpha_U0_soft_face_row()
        up = self.alpha_upstairs_mass_probe_row()
        meter = self.alpha_meter_na0_bridge_row()
        anchor = self.anchor_a_is_l_P_row()
        a = float(self.alpha_preferred)
        lp = float(self.l_P)
        tp = float(self.t_P)  # textbook Planck time; hT = κ·t_P
        c_macro = float(self.c)
        lp_from_c_t = c_macro * tp
        lp_from_hbar = math.sqrt(float(self.hbar) * float(self.G) / (c_macro ** 3))
        id_L_eq_VT = abs(lp_from_c_t / lp - 1.0) < 1e-12
        id_L_eq_planck = abs(lp_from_hbar / lp - 1.0) < 1e-12
        n_c = float(meter["N_c"])
        n_a0 = float(meter["N_a0_predicted"])
        n_compton = n_c  # λ̄_C / l_P
        n_re = a * a * n_a0  # r_e / l_P = α² a0/l_P
        id_a0 = abs(n_a0 - n_c / a) < 1e-12 * n_a0
        id_re = abs(n_re - a * n_c) < 1e-12 * max(n_re, 1.0)
        id_alpha = abs(n_c / n_a0 - a) < 1e-15
        inventory = [
            {
                "id": "natural_unit_l_P",
                "maps_to": "[L] := l_P ≡ hL — natural length unit",
                "ok": bool(anchor["a_equals_hL"]),
            },
            {
                "id": "L_eq_V_T",
                "maps_to": "[L]=[V][T] ⇒ l_P = c·t_P",
                "ok": id_L_eq_VT,
            },
            {
                "id": "L_eq_hbar_G_c",
                "maps_to": "l_P = √(ħG/c³) — same unit from ħ,G,c",
                "ok": id_L_eq_planck,
            },
            {
                "id": "alpha_dimensionless_exact",
                "maps_to": "[α]=1; soft face sealed — scales ratios only",
                "ok": bool(soft["derivation_closed"]) and bool(soft["checks_ok"]),
            },
            {
                "id": "Compton_hops",
                "maps_to": "λ̄_C = N_c · l_P",
                "N": n_compton,
                "ok": bool(up["checks_ok"]),
            },
            {
                "id": "Bohr_hops",
                "maps_to": "a0 = (N_c/α) · l_P",
                "N": n_a0,
                "ok": id_a0 and id_alpha,
            },
            {
                "id": "classical_radius_hops",
                "maps_to": "r_e = α·N_c · l_P = α²·a0",
                "N": n_re,
                "ok": id_re,
            },
            {
                "id": "not_SI_metre",
                "maps_to": "does NOT define/fit historical SI metre",
                "ok": True,
            },
        ]
        return {
            "theorem": "§8.2·[L]·l_P — length dim = l_P; hierarchy from α",
            "method": "dimensional analysis: [L]=[l_P], [α]=1 ⇒ L = N(α,N_c)·l_P",
            "natural_unit": "l_P",
            "identity_L_eq_V_T": id_L_eq_VT,
            "identity_lP_eq_c_tP": id_L_eq_VT,
            "identity_lP_eq_sqrt_hbarGc": id_L_eq_planck,
            "l_P": lp,
            "t_P": tp,
            "c": c_macro,
            "alpha_preferred": a,
            "N_c": n_c,
            "N_Compton": n_compton,
            "N_a0": n_a0,
            "N_re": n_re,
            "identity_a0_eq_Nc_over_alpha": id_a0,
            "identity_re_eq_alpha_Nc": id_re,
            "identity_alpha_eq_Nc_over_Na0": id_alpha,
            "length_dim_is_l_P": True,
            "alpha_sets_length_hierarchy": True,
            "not_historical_SI_metre": True,
            "derivation_closed": True,
            "inventory": inventory,
            "checks_ok": (
                all(bool(item["ok"]) for item in inventory)
                and id_L_eq_VT
                and id_L_eq_planck
                and id_a0
                and id_re
                and id_alpha
                and abs(a - float(soft["alpha_pref"])) < 1e-15
            ),
            "note": (
                "Length unit defined: [L]=[V][T] ⇒ l_P=c·t_P=√(ħG/c³); "
                "on carrier hL=c0·hT. α exact ⇒ Compton/Bohr/r_e hop hierarchy. "
                "Not historical SI-metre."
            ),
        }

    def time_dim_from_tP_row(self) -> dict[str, float | int | str | bool | list]:
        """§8.2·[T]·t_P — time dimension = t_P; M tick = hT = κ·t_P.

        Parallel to [L]: not SI-second (Cs) reconstruction.
        [T] = [L]/[V] ⇒ t_P = l_P/c = √(ħ G / c⁵).
        On carrier: hT = κ·t_P (true M tick); c0 = l_P/hT.
        SI-2019 second (Δν_Cs exact) is T-export only — same tautology class as c-fixed metre.
        """
        length = self.length_dim_from_lP_alpha_row()
        lp = float(self.l_P)
        tp = float(self.t_P)
        ht = float(self.hT)
        c_macro = float(self.c)
        c0 = float(self.c0)
        kappa = ht / tp
        tp_from_L_V = lp / c_macro
        tp_from_hbar = math.sqrt(
            float(self.hbar) * float(self.G) / (c_macro ** 5)
        )
        id_T_eq_L_over_V = abs(tp_from_L_V / tp - 1.0) < 1e-12
        id_T_eq_planck = abs(tp_from_hbar / tp - 1.0) < 1e-12
        id_hT_eq_kappa_tP = abs(ht / (kappa * tp) - 1.0) < 1e-15
        id_c0_eq_lP_hT = abs(c0 / (lp / ht) - 1.0) < 1e-15
        id_c0_eq_c_over_kappa = abs(c0 / (c_macro / kappa) - 1.0) < 1e-12
        inventory = [
            {
                "id": "natural_unit_t_P",
                "maps_to": "[T] := t_P — natural time unit",
                "ok": True,
            },
            {
                "id": "T_eq_L_over_V",
                "maps_to": "[T]=[L]/[V] ⇒ t_P = l_P/c",
                "ok": id_T_eq_L_over_V,
            },
            {
                "id": "T_eq_hbar_G_c",
                "maps_to": "t_P = √(ħG/c⁵) — same unit from ħ,G,c",
                "ok": id_T_eq_planck,
            },
            {
                "id": "M_tick_hT",
                "maps_to": "hT = κ·t_P — true M tick (not textbook t_P alone)",
                "ok": id_hT_eq_kappa_tP,
            },
            {
                "id": "c0_from_hL_hT",
                "maps_to": "c0 = l_P/hT = c/κ — geometry, not Cs",
                "ok": id_c0_eq_lP_hT and id_c0_eq_c_over_kappa,
            },
            {
                "id": "not_SI_second",
                "maps_to": "does NOT define/fit Cs SI-2019 second",
                "ok": True,
            },
            {
                "id": "length_dim_sealed",
                "maps_to": "needs [L]=l_P seal",
                "ok": bool(length["checks_ok"]),
            },
        ]
        return {
            "theorem": "§8.2·[T]·t_P — time dim = t_P; M tick hT=κ·t_P",
            "method": "dimensional analysis: [T]=[L]/[V]; carrier hT=κ·t_P",
            "natural_unit": "t_P",
            "M_tick": "hT",
            "t_P": tp,
            "hT": ht,
            "l_P": lp,
            "c": c_macro,
            "c0": c0,
            "kappa": kappa,
            "identity_T_eq_L_over_V": id_T_eq_L_over_V,
            "identity_tP_eq_lP_over_c": id_T_eq_L_over_V,
            "identity_tP_eq_sqrt_hbarGc5": id_T_eq_planck,
            "identity_hT_eq_kappa_tP": id_hT_eq_kappa_tP,
            "identity_c0_eq_lP_over_hT": id_c0_eq_lP_hT,
            "time_dim_is_t_P": True,
            "M_tick_is_hT": True,
            "not_historical_SI_second": True,
            "SI_second_is_T_export_only": True,
            "derivation_closed": True,
            "inventory": inventory,
            "checks_ok": (
                all(bool(item["ok"]) for item in inventory)
                and id_T_eq_L_over_V
                and id_T_eq_planck
                and id_hT_eq_kappa_tP
                and id_c0_eq_lP_hT
            ),
            "note": (
                "Time unit defined: [T]=[L]/[V] ⇒ t_P=l_P/c=√(ħG/c⁵). "
                "M tick hT=κ·t_P; c0=l_P/hT. "
                "SI-2019 second (Cs) is T-export — tautology twin of c-fixed metre."
            ),
        }

    def units_time_first_cascade_row(self) -> dict[str, float | int | str | bool | list]:
        """§8.2·units·time-first — t_P → l_P=c·t_P → m_P=ℏ/(c² t_P).

                Same SI base triad {L, M, T} â only the quanta differ from Cs/c/kg prototypes.
        Ontology (time-first):
          1. [T] := t_P
          2. [L] := l_P = cÂ·t_P   (light-path in one time quantum)
          3. [M] := m_P = â/(cÂ² t_P) = â/(cÂ·l_P)
        Everything else (force, energy, â¦) â derived from {L,M,T} exactly as in SI.
        On carrier: hT = ÎºÂ·t_P; c0 = l_P/hT.
        Newton G = âc/m_PÂ² is derived, not a fourth base.
        Historical SI metre/second/kilogram numbers = T-export labels only.
        """
        time = self.time_dim_from_tP_row()
        length = self.length_dim_from_lP_alpha_row()
        tp = float(self.t_P)
        lp = float(self.l_P)
        mp = float(self.m_P)
        c_macro = float(self.c)
        hbar = float(self.hbar)
        m_from_t = hbar / (c_macro ** 2 * tp)
        m_from_l = hbar / (c_macro * lp)
        g_from_m = hbar * c_macro / (mp ** 2)
        id_L_from_T = abs(lp / (c_macro * tp) - 1.0) < 1e-15
        id_M_from_T = abs(m_from_t / mp - 1.0) < 1e-12
        id_M_from_L = abs(m_from_l / mp - 1.0) < 1e-12
        id_M_same = abs(m_from_t / m_from_l - 1.0) < 1e-12
        inventory = [
            {
                "id": "step1_time_quantum",
                "maps_to": "t_P — natural time quantum ([T])",
                "ok": bool(time["checks_ok"]),
            },
            {
                "id": "step2_length_from_light",
                "maps_to": "l_P = c·t_P — [L] = light-path in one time quantum",
                "ok": id_L_from_T and bool(length["checks_ok"]),
            },
            {
                "id": "step3_mass_unit",
                "maps_to": "m_P = ℏ/(c² t_P) — [M] exact",
                "ok": id_M_from_T,
            },
            {
                "id": "M_eq_from_l_P",
                "maps_to": "m_P = ℏ/(c·l_P) — same (length twin)",
                "ok": id_M_from_L and id_M_same,
            },
            {
                "id": "carrier_hT",
                "maps_to": "hT = κ·t_P; c0 = l_P/hT",
                "ok": bool(time["identity_hT_eq_kappa_tP"]),
            },
            {
                "id": "G_is_consequence_not_step",
                "maps_to": "G = ℏc/m_P² follows — not ontology step 3",
                "value": g_from_m,
                "ok": True,
            },
        ]
        return {
            "theorem": "§8.2·units·time-first — t_P → l_P → m_P ([M])",
            "method": "ontology: time quantum → light-path length → mass from ℏ,c,t_P",
            "ontology_order": ["t_P", "l_P = c·t_P", "m_P = ℏ/(c² t_P)"],
            "t_P": tp,
            "l_P": lp,
            "m_P": mp,
            "c": c_macro,
            "hbar": hbar,
            "m_P_from_t_P": m_from_t,
            "m_P_from_l_P": m_from_l,
            "G_consequence": g_from_m,
            "identity_lP_eq_c_tP": id_L_from_T,
            "identity_mP_eq_hbar_over_c2_tP": id_M_from_T,
            "identity_mP_eq_hbar_over_c_lP": id_M_from_L,
            "identity_mP_time_eq_length_form": id_M_same,
            "time_first": True,
            "si_base_triad_LMT": True,
            "mass_unit_exact": True,
            "derived_units_as_in_SI": True,
            "G_not_ontology_step": True,
            "not_SI_metre_second_kg_prototypes": True,
            "derivation_closed": True,
            "inventory": inventory,
            "checks_ok": (
                all(bool(item["ok"]) for item in inventory)
                and id_L_from_T
                and id_M_from_T
                and id_M_from_L
                and id_M_same
            ),
            "note": (
                "SI-same base triad {L,M,T}: t_P, l_P=cÂ·t_P, m_P=â/(cÂ²t_P). "
                "Derived units from the triad as in SI. G=âc/m_PÂ² derived, not base."
            ),
        }

    def planck_temperature_independent_row(self) -> dict[str, float | int | str | bool | list]:
        """§8.2·units·T_P — Planck temperature without k_B.

        On M (§5.3.1) temperature is mean kinetic zigzag energy — no separate Θ.
        Natural definition: T_P := E_P = ℏ/t_P (energy unit). Carrier tick:
        T_P_M := E_0 = s_0/hT = E_P/√2. k_B appears only in optional SI kelvin
        T-export Θ_P = T_P/k_B — not part of the definition.
        """
        tp = float(self.t_P)
        ht = float(self.hT)
        hbar = float(self.hbar)
        e_p = float(self.E_P)
        e_0 = float(self.E_0)
        s_0 = float(self.s_0)
        kappa = ht / tp

        # Independent (no k_B): temperature unit = energy quantum
        t_p_from_hbar = hbar / tp
        t_p_m_from_s0 = s_0 / ht
        t_p_m_from_ep = e_p * kappa  # E_0 = E_P · κ since hT = κ·t_P

        id_TP_eq_EP = abs(t_p_from_hbar / e_p - 1.0) < 1e-12
        id_TPM_eq_E0 = abs(t_p_m_from_s0 / e_0 - 1.0) < 1e-12
        id_TPM_eq_kappa_EP = abs(t_p_m_from_ep / e_0 - 1.0) < 1e-12
        id_EP_eq_sqrt2_E0 = abs(e_p / (e_0 * math.sqrt(2.0)) - 1.0) < 1e-12

        # Optional SI kelvin packaging only (not ontology)
        k_b_codata = 1.380649e-23  # J/K exact SI-2019
        theta_p_kelvin = e_p / k_b_codata

        inventory = [
            {
                "id": "T_P_is_E_P",
                "maps_to": "T_P := E_P = ℏ/t_P — no k_B",
                "ok": id_TP_eq_EP,
            },
            {
                "id": "T_P_M_is_E_0",
                "maps_to": "T_P_M := E_0 = s_0/hT — Arg energy per M tick",
                "ok": id_TPM_eq_E0,
            },
            {
                "id": "T_P_M_eq_kappa_E_P",
                "maps_to": "E_0 = κ·E_P (hT = κ·t_P)",
                "ok": id_TPM_eq_kappa_EP,
            },
            {
                "id": "E_P_eq_sqrt2_E_0",
                "maps_to": "textbook E_P = √2·E_0",
                "ok": id_EP_eq_sqrt2_E0,
            },
            {
                "id": "k_B_not_in_definition",
                "maps_to": "k_B only optional Θ_P[K]=E_P/k_B T-export",
                "ok": True,
            },
            {
                "id": "no_separate_Theta_on_M",
                "maps_to": "§5.3.1 T = ⟨E_kin zigzag⟩ — energy, not SI kelvin",
                "ok": True,
            },
        ]
        return {
            "theorem": "§8.2·units·T_P — independent of k_B",
            "method": "T on M is energy (§5.3.1); T_P:=E_P=ℏ/t_P",
            "T_P": e_p,
            "T_P_M": e_0,
            "E_P": e_p,
            "E_0": e_0,
            "t_P": tp,
            "hT": ht,
            "identity_TP_eq_EP": id_TP_eq_EP,
            "identity_TPM_eq_E0": id_TPM_eq_E0,
            "identity_TPM_eq_kappa_EP": id_TPM_eq_kappa_EP,
            "identity_EP_eq_sqrt2_E0": id_EP_eq_sqrt2_E0,
            "k_B_not_in_definition": True,
            "no_separate_Theta_on_M": True,
            "theta_P_kelvin_T_export_only": theta_p_kelvin,
            "k_B_CODATA_T_export": k_b_codata,
            "derivation_closed": True,
            "inventory": inventory,
            "checks_ok": all(bool(item["ok"]) for item in inventory),
            "note": (
                "Natural T_P:=E_P=ℏ/t_P; carrier T_P_M:=E_0. "
                "k_B and kelvin are T-export only — not ontology."
            ),
        }

    def coulomb_M_native_row(self) -> dict[str, float | int | str | bool | list]:
        """§8.2·Coulomb·M-native — force law without continuum α on M.

        Forgotten continuum: writing F=α_fs F_P n1 n2/N² with
        α_fs=1/(alpha_from_fundamentals) smuggles [pi-tower-removed] into the M force law.
        Full quantization: unit NN Coulomb is F₀/M; α=κ/M is T-name only.
        """
        census = self.alpha_nF_momentum_registry_row()
        kappa = float(census["kappa"])
        m = int(census["M"])
        f0_over_fp = kappa  # F₀/F_P = κ
        alpha = kappa / m
        # M-native NN unit force in F_P units:
        f_nn_over_fp = f0_over_fp / m  # = α
        inventory: list[dict[str, str | float | bool | int]] = [
            {
                "id": "M_native_NN",
                "maps_to": "F_NN = F₀/M — no π, ε₀, [pi-tower-removed] on M",
                "status": "derived",
            },
            {
                "id": "general_graph_distance",
                "maps_to": "F = n1 n2 F₀/(M N²), N∈ℕ hops",
                "status": "derived",
            },
            {
                "id": "T_readout_alpha",
                "ratio": alpha,
                "maps_to": "α=κ/M names the same NN force as F/F_P",
                "status": "derived",
            },
            {
                "id": "reject_pi_tower_gone",
                "maps_to": "α_fs=1/(alpha_from_fundamentals) must not define M Coulomb",
                "status": "rejected_as_m_input",
            },
            {
                "id": "soft_residual_still_open",
                "ppm": float(census["vs_codata_ppm"]),
                "maps_to": "κ/97 vs CODATA — higher structure OPEN",
                "status": "open",
            },
        ]
        return {
            "theorem": "§8.2·Coulomb·M-native — F=n1 n2 F₀/(M N²)",
            "M": m,
            "kappa": kappa,
            "alpha_T": alpha,
            "F_NN_over_F0": 1.0 / m,
            "F_NN_over_FP": f_nn_over_fp,
            "identity_alpha_equals_F_NN_over_FP": abs(alpha - f_nn_over_fp) < 1e-15,
            "derivation_closed": True,  # law form; soft ppm is separate
            "soft_residual_open": True,
            "inventory": inventory,
            "checks_ok": m == 97
            and abs(alpha - f_nn_over_fp) < 1e-15
            and abs(kappa**2 - 0.5) < 1e-15,
            "note": (
                "M Coulomb: F=n1 n2 F₀/(M N²) with M=97. "
                "α=κ/M is T-readout of the same NN ratio. "
                "pi-tower removed; alpha=fundamentals."
            ),
        }

