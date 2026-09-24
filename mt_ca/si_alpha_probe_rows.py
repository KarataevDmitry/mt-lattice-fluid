"""SIAlphaProbeRows — α rows (split from si_alpha_rows)."""
from __future__ import annotations

import math

from mt_ca.si_constants import (
    C,
    DELTA_PHI_MIN,
    EV_J,
    HBAR,
    KAPPA_FCC_1TICK,
    N12_FCC_CAUSAL_LINKS,
    N4_CAUSAL_LINKS,
    hv_bit_budget,
)


class SIAlphaProbeRows:
    """α ask/row methods."""

    def alpha_hop_ladder_row(self) -> dict[str, float | int | str | bool]:
        """Probe: α from hop ladder after ℓ_P⊄c (§7.2–7.4) + H-atom rung.

        M-native Compton uses link speed c₀:
            N_c0 = ℏ/(m_e c₀ hL) = κ·(m_P/m_e)
        Classical radius with textbook m c²:
            N_re = r_e/hL = α·(m_P/m_e)
        Detached rewrite (identity, not derivation):
            α = κ · N_re / N_c0
        Equivalent mixed-energy form (one macro-c, one link-c₀):
            U(r_★)=e²/(4πϵ₀ r_★)=m_e c c₀  ⇒  α = N_★ / N_c0

        Hydrogen (Bohr) — next rung on the same hL ladder:
            N_a0 = a₀/hL = N_c/α
            N_re --α-- N_c --α-- N_a0
            α² = N_re/N_a0   (same power as m_e = α²·m_H/N_φ in §8.2)
            v_Bohr/c₀ = α·κ

        Status: structural rewrite of CODATA α into hL-hops + κ.
        Does **not** replace π-ansatz until one of {N_★, N_re, N_a0}
        comes from carrier without ϵ₀/α. Geom near-miss: N₁₂(N₁₂+1)=156 vs α⁻¹≈137.
        """
        kappa = KAPPA_FCC_1TICK
        m_e = self.m_e_CODATA
        hL = self.l_P
        # CODATA α (measured); π-ansatz kept separate for ppm compare
        alpha_codata = 7.2973525693e-3
        alpha_codata_inv = 1.0 / alpha_codata
        N_c = self.hbar / (m_e * self.c * hL)
        N_c0 = self.hbar / (m_e * self.c0 * hL)
        # r_e via α·λ̄_C (SI-consistent; ϵ₀ route is the same identity)
        N_re = alpha_codata * N_c
        # classical balance against m·c·c₀ (detachment-native)
        N_star = alpha_codata * N_c0  # ≡ r_★/hL with U=m c c₀
        # Bohr radius rungs
        N_a0 = N_c / alpha_codata
        N_a0_c0 = N_c0 / alpha_codata
        alpha_from_kappa_hops = kappa * N_re / N_c0
        alpha_from_star = N_star / N_c0
        alpha_from_bohr = N_c / N_a0
        alpha2_from_ladder = N_re / N_a0
        v_over_c0 = alpha_codata * kappa  # = v_Bohr/c₀ with v=α c
        n12 = N12_FCC_CAUSAL_LINKS
        geom_156 = float(n12 * (n12 + 1))
        return {
            "kappa": kappa,
            "N_c_macro": N_c,
            "N_c0_link": N_c0,
            "N_re": N_re,
            "N_star_m_c_c0": N_star,
            "N_a0_Bohr": N_a0,
            "N_a0_c0": N_a0_c0,
            "alpha_codata": alpha_codata,
            "alpha_from_kappa_Nre_over_Nc0": alpha_from_kappa_hops,
            "alpha_from_Nstar_over_Nc0": alpha_from_star,
            "alpha_from_Nc_over_Na0": alpha_from_bohr,
            "alpha2_from_Nre_over_Na0": alpha2_from_ladder,
            "v_Bohr_over_c0": v_over_c0,
            "rel_kappa_form": abs(alpha_from_kappa_hops - alpha_codata) / alpha_codata,
            "rel_star_form": abs(alpha_from_star - alpha_codata) / alpha_codata,
            "rel_bohr_form": abs(alpha_from_bohr - alpha_codata) / alpha_codata,
            "rel_alpha2_ladder": abs(alpha2_from_ladder - alpha_codata**2) / alpha_codata**2,
            "alpha_pi_ansatz": self.alpha_fs,
            "alpha_pi_inv": self.alpha_fs_inv,
            "alpha_codata_inv": alpha_codata_inv,
            "N12_times_N12p1": geom_156,
            "geom_156_over_codata_inv": geom_156 / alpha_codata_inv,
            "identity_ok": abs(alpha_from_kappa_hops - alpha_codata) / alpha_codata < 1e-12
            and abs(alpha_from_star - alpha_codata) / alpha_codata < 1e-12
            and abs(alpha_from_bohr - alpha_codata) / alpha_codata < 1e-12
            and abs(alpha2_from_ladder - alpha_codata**2) / alpha_codata**2 < 1e-12,
            "derivation_open": True,
            "note": (
                "§7.4+§4.8+H: α=κ·N_re/N_c0=N_★/N_c0=N_c/N_a0; "
                "α²=N_re/N_a0 (rhymes m_e=α² m_H/N_φ); v_Bohr/c₀=ακ. "
                "Identity rewrite; one hop from g without α still OPEN. "
                "π-ansatz not replaced. See also alpha_fixed_point_row."
            ),
        }

    def alpha_fixed_point_row(self) -> dict[str, float | int | str | bool]:
        """First fixed-point for α: cascade m_e(α) + fixed optical N_a0.

        Map (macro Compton hops):
            m_e(α) = α² · m_H(α) / N_φ     (§8.2; m_H from α⁸·E_P·√(2π) + λ-stack)
            N_c(α) = m_P / m_e(α)
            α'     = N_c(α) / N_a0
        with N_a0 = a₀/hL from CODATA Bohr radius (α-independent optical length).

        Analytic (bare, λ=1/8 ⇒ m_H=v/2):
            m_e = α¹⁰ E_P √(π/2) / N_φ
            α* = [ N_φ / (N_a0 √(π/2)) ]^{1/11}

        Analytic (stack, λ=1/8 + 2α/π):
            α¹¹ √λ(α) = N_φ / (2 N_a0 √π)
            ⇔ (2/π) α²³ + (1/8) α²² − [N_φ/(2 N_a0 √π)]² = 0

        Exponent 11 = N_hier(=8) + 2(from m_e∝α²) + 1(from α=N_c/N_a0).

        First use of fixed-point closure in this model (2026-09-23).
        """
        n_phi = 13.0
        n_hier = 8.0
        a0_m = 5.29177210903e-11
        n_a0 = a0_m / self.l_P
        alpha_codata = 7.2973525693e-3
        m_p_gev = self.E_P / EV_J / 1e9
        # closed-form bare
        k_bare = n_phi / (n_a0 * math.sqrt(math.pi / 2.0))
        a_bare_analytic = k_bare ** (1.0 / 11.0)
        # stack polynomial RHS
        rhs = n_phi / (2.0 * n_a0 * math.sqrt(math.pi))
        rhs2 = rhs * rhs

        def cascade(alpha: float) -> tuple[float, float, float, float]:
            v = (alpha**n_hier) * m_p_gev * math.sqrt(2.0 * math.pi)
            m_h_bare = v / 2.0
            delta_lam = alpha / (4.0 * math.pi)
            lam = 1.0 / n_hier + n_hier * delta_lam
            m_h = math.sqrt(2.0 * lam) * v
            m_e = (alpha**2) * m_h / n_phi
            m_e_bare = (alpha**2) * m_h_bare / n_phi
            return m_e, m_e_bare, m_h, v

        def mapped(alpha: float, *, bare: bool) -> float:
            m_e, m_e_bare, _, _ = cascade(alpha)
            m = m_e_bare if bare else m_e
            return (m_p_gev / m) / n_a0

        def solve_stack() -> float:
            lo, hi = 1e-4, 0.05
            flo = mapped(lo, bare=False) - lo
            for _ in range(100):
                mid = 0.5 * (lo + hi)
                fm = mapped(mid, bare=False) - mid
                if flo * fm <= 0:
                    hi = mid
                else:
                    lo, flo = mid, fm
            return 0.5 * (lo + hi)

        a_stack = solve_stack()
        a_bare = a_bare_analytic  # closed form — no need to bisect
        m_e_s, _, m_h_s, v_s = cascade(a_stack)
        _, m_e_bare_b, _, _ = cascade(a_bare)
        lam_s = 1.0 / n_hier + 2.0 * a_stack / math.pi
        # poly identity at stack root
        poly_stack = (a_stack**22) * ((2.0 / math.pi) * a_stack + 0.125)
        # seed invariance on stack map
        seeds_ok = True
        for seed in (1e-3, 1e-2, 2e-2, alpha_codata, self.alpha_fs):
            a = seed
            for _ in range(400):
                a = 0.85 * a + 0.15 * mapped(a, bare=False)
            if abs(a - a_stack) / a_stack > 1e-10:
                seeds_ok = False
                break
        analytic_bare_ok = abs(mapped(a_bare, bare=True) - a_bare) / a_bare < 1e-12
        analytic_stack_poly_ok = abs(poly_stack - rhs2) / rhs2 < 1e-12
        return {
            "N_a0_optical": n_a0,
            "a0_m": a0_m,
            "N_phi": n_phi,
            "N_hier": n_hier,
            "exponent": 11,
            "K_bare": k_bare,
            "alpha_bare_analytic": a_bare_analytic,
            "alpha_bare_analytic_inv": 1.0 / a_bare_analytic,
            "stack_RHS": rhs,
            "stack_poly_RHS2": rhs2,
            "alpha_star_stack": a_stack,
            "alpha_star_stack_inv": 1.0 / a_stack,
            "alpha_star_bare": a_bare,
            "alpha_star_bare_inv": 1.0 / a_bare,
            "lambda_at_stack": lam_s,
            "stack_poly_at_star": poly_stack,
            "map_stack_at_star": mapped(a_stack, bare=False),
            "map_bare_at_star": mapped(a_bare, bare=True),
            "residual_stack": abs(mapped(a_stack, bare=False) - a_stack) / a_stack,
            "residual_bare": abs(mapped(a_bare, bare=True) - a_bare) / a_bare,
            "vs_codata_ppm_stack": (a_stack - alpha_codata) / alpha_codata * 1e6,
            "vs_codata_ppm_bare": (a_bare - alpha_codata) / alpha_codata * 1e6,
            "vs_pi_ppm_stack": (a_stack - self.alpha_fs) / self.alpha_fs * 1e6,
            "m_e_star_stack_GeV": m_e_s,
            "m_e_star_bare_GeV": m_e_bare_b,
            "m_H_star_stack_GeV": m_h_s,
            "v_star_stack_GeV": v_s,
            "alpha_codata": alpha_codata,
            "alpha_pi_ansatz": self.alpha_fs,
            "seed_invariant": seeds_ok,
            "analytic_bare_ok": analytic_bare_ok,
            "analytic_stack_poly_ok": analytic_stack_poly_ok,
            "fixed_point_ok": seeds_ok
            and analytic_bare_ok
            and analytic_stack_poly_ok
            and abs(mapped(a_stack, bare=False) - a_stack) / a_stack < 1e-12,
            "derivation_open": True,
            "note": (
                "Analytic bare: α*=[N_φ/(N_a0√(π/2))]^{1/11}. "
                "Stack: (2/π)α²³+(1/8)α²²=[N_φ/(2 N_a0√π)]². "
                "Exponent 11=8+2+1. "
                "N_a0 optical or carrier N_c·137 (α_geom); see na0_from_carrier_row."
            ),
        }

    def alpha_force_lattice_ask_row(self) -> dict[str, float | int | str | bool | list]:
        """§8.2·F·ask — Coulomb lands on F₀ lattice; α=soft-face (α₀ demoted).

        Thm 5.1: force transfers as n_F·F₀. Unit NN Coulomb F=α F_P.
        F₀/F_P = κ (geometry). One EM quantum at N=1:
            α F_P = F₀/M  ⇒  α₀ = κ/M (demoted) , M∈ℕ.

        Probe (2026-09-23):
          • target M = F₀/(α_c F_P) ≈ 96.899
          • cleanest carrier M = N₁₂·N_hier = 96 (= n_△·N₁₂ = N_hier·(N_φ−1))
            → α₀=κ/96 (demoted), inv≈135.76, ~+9366 ppm vs CODATA
          • nearest int M = 97 = N₁₂·N_hier+1 → α₀=κ/97 (demoted; α=soft-face), inv≈137.18, ~−1040 ppm
          • M=137/√2 recovers α=1/137 — injects α_geom, empty for derivation
          • π-ansatz still ~2 ppm; force path does **not** replace it yet
        OPEN: which M from g (why 96 vs 97 / shell rule).
        """
        kappa = KAPPA_FCC_1TICK
        n12 = float(N12_FCC_CAUSAL_LINKS)
        n_hier = 8.0
        n_phi = 13.0
        n_tri = 8.0
        alpha_c = 7.2973525693e-3
        f0 = self.F_0
        f_p = self.c**4 / self.G
        m_target = f0 / (alpha_c * f_p)
        m_96 = n12 * n_hier
        m_97 = m_96 + 1.0
        m_geom = 137.0 / math.sqrt(2.0)  # = 137·κ — not ℤ

        def pack(m: float, name: str, status: str) -> dict[str, float | str]:
            a = kappa / m
            return {
                "id": name,
                "M": m,
                "alpha": a,
                "alpha_inv": 1.0 / a,
                "vs_codata_ppm": (a - alpha_c) / alpha_c * 1e6,
                "status": status,
            }

        cands = [
            pack(m_96, "N12*N_hier", "cleanest_combinatorics"),
            pack(m_97, "N12*N_hier+1", "nearest_int_ppm"),
            pack(n_tri * n12, "n_tri*N12", "alias_of_96"),
            pack(n_hier * (n_phi - 1.0), "N_hier*(N_phi-1)", "alias_of_96"),
            pack(m_geom, "137/sqrt(2)=137*kappa", "rejects_injects_alpha_geom"),
        ]
        a96 = kappa / m_96
        a97 = kappa / m_97
        inventory: list[dict[str, str | float | bool]] = [
            {
                "id": "F0_over_FP_is_kappa",
                "ratio": f0 / f_p,
                "maps_to": "κ from hull; force ladder vs Planck force",
                "status": "shipped",
            },
            {
                "id": "Coulomb_NN_on_F0",
                "maps_to": "α F_P = F₀/M ⇒ α₀=κ/M",
                "status": "constraint",
                "mechanism": "Thm5.1 force quanta + §8.2 Coulomb form",
            },
            {
                "id": "M_target_CODATA",
                "ratio": m_target,
                "maps_to": "F₀/(α_c F_P) ≈ 96.899 — near 96|97",
                "status": "report",
            },
            {
                "id": "prefer_M96_story",
                "maps_to": "N₁₂×N_hier — links × hierarchy budget",
                "status": "candidate",
                "mechanism": "ppm worse than 97; combinatorics cleaner",
            },
            {
                "id": "prefer_M97_ppm",
                "maps_to": "N₁₂×N_hier+1",
                "status": "candidate",
                "mechanism": "~−1040 ppm; +1 not yet from g",
            },
            {
                "id": "reject_M_137_kappa",
                "maps_to": "non-integer M; sneaks α_geom",
                "status": "rejected",
            },
        ]
        return {
            "theorem": "§8.2·F·ask — F₀ lattice seats; α=soft-face (α₀ demoted)",
            "kappa": kappa,
            "F0_N": f0,
            "F_P_N": f_p,
            "F0_over_FP": f0 / f_p,
            "M_target_CODATA": m_target,
            "M_N12_Nhier": m_96,
            "M_N12_Nhier_plus1": m_97,
            "alpha_M96": a96,
            "alpha_M96_inv": 1.0 / a96,
            "vs_codata_ppm_M96": (a96 - alpha_c) / alpha_c * 1e6,
            "alpha_M97": a97,
            "alpha_M97_inv": 1.0 / a97,
            "vs_codata_ppm_M97": (a97 - alpha_c) / alpha_c * 1e6,
            "alpha_pi_ansatz": self.alpha_fs,
            "vs_codata_ppm_pi": (self.alpha_fs - alpha_c) / alpha_c * 1e6,
            "candidates": cands,
            "inventory": inventory,
            "replaces_pi_ansatz": False,
            "M_from_g_open": True,
            "ask_ok": abs(f0 / f_p - kappa) / kappa < 1e-12
            and abs(m_96 - 96.0) < 1e-12
            and abs(m_target - 96.899) < 0.01,
            "note": (
                "Force lattice seats M=97; α=soft-face. Demoted α₀ (−1040 ppm); incomplete M=96 "
                "(+9366 ppm). M=137κ rejects (α_geom). π-ansatz not replaced; M from g OPEN."
            ),
        }

    def alpha_meaning_ask_row(self) -> dict[str, float | int | str | bool | list]:
        """§8.2·α·meaning — restart from physical meaning of α (not F-lattice / N_a0).

        Meaning (already stamped §8.2 / §7.1 / §8.4.1):
          α = dimensionless **phase coupling** of unit charge to vacuum
              (EM channel; solid-angle / phase-volume of emergent 3D),
          NOT the definition of force, NOT a hop count by itself.

        Foot (empty cell, b=0):
          α*−1 = Δφ_min/(2π) = 1/(4π)  — vacuum residue per tick.

        Readouts (consequences, not meanings):
          F = α F_P / N² ;  α = N_c/N_a0 ;  α₀ = κ/M (demoted)  — expressions of the same coupling.

        Number today (T): π-tower 1/(4π³+π²+π) ~−2 ppm — competitor readout.
        Seats M=97 + soft-face α shipped (force law F₀/M); α₀ demoted.
        Soft OPEN: −1040 ppm vs CODATA; holonomy that closes soft without π-ansatz.
        """
        alpha_star = self.alpha_star
        residue = alpha_star - 1.0
        alpha = self.alpha_fs
        alpha_c = 7.2973525693e-3
        four_pi = 4.0 * math.pi
        inventory: list[dict[str, str | float | bool]] = [
            {
                "id": "meaning_phase_coupling",
                "maps_to": "α = EM phase↔vacuum coupling (solid angle / phase volume)",
                "status": "shipped_meaning",
                "mechanism": "§8.2; not |N| tile; not Newton force primary",
            },
            {
                "id": "foot_vacuum_residue",
                "ratio": residue,
                "maps_to": "α*−1 = Δφ_min/(2π) = 1/(4π)",
                "status": "shipped",
                "mechanism": "empty cell gate §7.1; occupancy bit separate (§8.4.1)",
            },
            {
                "id": "tower_solid_angle",
                "ratio": self.alpha_fs_inv,
                "maps_to": "α⁻¹ = 4π³+π²+π — continuum T-readout tower on foot 4π",
                "status": "shipped_number",
                "mechanism": "~2 ppm CODATA; π-guardrail: 4π≠|N|",
            },
            {
                "id": "identity_4pi_alpha_eq_alpha_over_residue",
                "ratio": four_pi * alpha,
                "maps_to": "4π·α = α/(α*−1) — tower sits on residue foot",
                "status": "identity",
            },
            {
                "id": "readout_force_not_meaning",
                "maps_to": "F=α F_P/N² — consequence of coupling, not definition",
                "status": "readout",
            },
            {
                "id": "readout_hops_not_meaning",
                "maps_to": "α=N_c/N_a0 — length expression of same coupling",
                "status": "readout",
            },
            {
                "id": "readout_force_lattice_not_meaning",
                "maps_to": "F₀ landing; M=97 seats; α=soft-face (α₀ demoted)",
                "status": "readout_shipped",
            },
            {
                "id": "M_native_force_law",
                "maps_to": "F=n1 n2 F₀/(M N²) — no continuum α/π on M",
                "status": "shipped",
                "mechanism": "§8.2·Coulomb·M-native",
            },
            {
                "id": "open_soft_residual_holonomy",
                "maps_to": "demoted α₀=κ/97 vs CODATA −1040 ppm — holonomy without π-ansatz",
                "status": "open",
                "mechanism": "π-tower still competing T-number ~−2 ppm",
            },
        ]
        return {
            "theorem": "§8.2·α·meaning — α is phase↔vacuum coupling",
            "alpha_star": alpha_star,
            "vacuum_residue": residue,
            "residue_equals_1_over_4pi": abs(residue - 1.0 / four_pi) < 1e-15,
            "alpha_fs": alpha,
            "alpha_fs_inv": self.alpha_fs_inv,
            "four_pi_times_alpha": four_pi * alpha,
            "alpha_over_residue": alpha / residue,
            "vs_codata_ppm_pi": (alpha - alpha_c) / alpha_c * 1e6,
            "inventory": inventory,
            "replaces_pi_ansatz": False,
            "discrete_coupling_open": True,  # soft ppm / holonomy; force law shipped
            "ask_ok": abs(residue - 1.0 / four_pi) < 1e-15
            and abs(four_pi * alpha - alpha / residue) < 1e-12,
            "note": (
                "Meaning: α=phase↔vacuum coupling; foot α*−1=1/(4π). "
                "F=F₀/M + soft-face α shipped; α₀ demoted. "
                "OPEN: soft −1040 ppm (holonomy vs π-tower T)."
            ),
        }

    def alpha_descent_ask_row(self) -> dict[str, float | int | str | bool | list]:
        """§8.2·α·descent — forget α; descend vacuum→residue→Ω→charge→coupling.

        Amnesia construction (no α_fs / CODATA / π-poly as input):
          1. A5 + Heisenberg: Δφ_min = 1/2
          2. Tick cycle 2π ⇒ residue r = Δφ_min/(2π) = 1/(4π); α* = 1+r
          3. Emergent d=3 ⇒ Ω = 1/r = 4π; discrete N_φ = ⌈Ω⌉ = 13
          4. FCC body ⇒ κ, N₁₂, faces (6□+8△)
          5. Charge n∈ℤ appears (A10)
          6. Ask: what dimensionless EM coupling falls out?

        Natural landings near table (scored only AFTER):
          • continuum completion: 1/(4π³+π²+π) — T solid-angle tower on foot
          • discrete body: α_geom⁻¹ = N₁₂(N₁₂+1)−n_△−2n_□+1 = 137
        Raw residue / r² / κ_link·r — wrong scale.
        OPEN: why tower or face-formula from g (holonomy), not ansatz.
        """
        dphi = 0.5
        cycle = 2.0 * math.pi
        residue = dphi / cycle
        omega = 1.0 / residue
        n_phi = int(math.ceil(omega))
        n12 = int(N12_FCC_CAUSAL_LINKS)
        n_hier = 8
        n_sq, n_tri = 6, 8
        kappa = KAPPA_FCC_1TICK
        k_link = 1.0 / n12
        alpha_geom_inv = n12 * (n12 + 1) - n_tri - 2 * n_sq + 1
        alpha_c = 7.2973525693e-3  # score only
        pi_tower_inv = 4.0 * math.pi**3 + math.pi**2 + math.pi

        def scored(name: str, a: float, status: str) -> dict[str, float | str]:
            return {
                "id": name,
                "alpha": a,
                "alpha_inv": 1.0 / a,
                "vs_codata_ppm": (a - alpha_c) / alpha_c * 1e6,
                "status": status,
            }

        cands = [
            scored("pi_tower_AFTER", 1.0 / pi_tower_inv, "continuum_completion"),
            scored("alpha_geom", 1.0 / float(alpha_geom_inv), "discrete_body_completion"),
            scored("kappa_over_97", kappa / (n12 * n_hier + 1), "force_lattice_side"),
            scored("kappa_over_96", kappa / (n12 * n_hier), "force_lattice_side"),
            scored("kappa_link_times_r", k_link * residue, "wrong_scale"),
            scored("r_squared", residue * residue, "wrong_scale"),
            scored("residue_alone", residue, "wrong_scale_foot_not_coupling"),
        ]
        steps: list[dict[str, str | float | int | bool]] = [
            {"step": 1, "physics": "A5 vacuum + Δφ_min=1/2", "out": dphi},
            {"step": 2, "physics": "tick cycle 2π → residue r=Δφ_min/(2π)", "out": residue},
            {"step": 3, "physics": "d=3 → Ω=1/r; N_φ=⌈Ω⌉", "out_Omega": omega, "out_Nphi": n_phi},
            {"step": 4, "physics": "FCC hull → κ, N12, faces", "kappa": kappa, "N12": n12},
            {"step": 5, "physics": "A10 charge n∈ℤ", "status": "shipped"},
            {
                "step": 6,
                "physics": "dimensionless EM coupling = ?",
                "status": "open_completion",
                "note": "foot+Ω known; fraction through Ω not yet from g",
            },
        ]
        return {
            "theorem": "§8.2·α·descent — amnesia path vacuum→coupling",
            "delta_phi_min": dphi,
            "vacuum_residue": residue,
            "Omega": omega,
            "N_phi": n_phi,
            "alpha_geom_inv": alpha_geom_inv,
            "kappa": kappa,
            "steps": steps,
            "candidates": cands,
            "pi_tower_inv": pi_tower_inv,
            "vs_codata_ppm_pi_AFTER": (1.0 / pi_tower_inv - alpha_c) / alpha_c * 1e6,
            "vs_codata_ppm_geom": (1.0 / alpha_geom_inv - alpha_c) / alpha_c * 1e6,
            "residue_is_not_alpha": True,
            "coupling_fraction_open": True,
            "used_alpha_fs_as_input": False,
            "ask_ok": abs(residue - 1.0 / (4.0 * math.pi)) < 1e-15
            and n_phi == 13
            and alpha_geom_inv == 137,
            "note": (
                "Forgot α. Descent yields foot r=1/(4π) and Ω=4π/N_φ=13; coupling "
                "fraction OPEN. AFTER-score: π-tower ~2ppm; α_geom=137 ~263ppm."
            ),
        }

    def alpha_mass_defect_optics_row(self) -> dict[str, float | int | str | bool | list]:
        """§8.2·α·mass-defect — QM-floor optics: H binding Δm is upstairs α.

        QM (previous floor): BE = ½ α² m_e c², Δm = BE/c² ⇒ α = √(2 Δm/m_e).
        DoD descent: Arg-binding of composite H must coarse-grain to this Δm.

        Same α identities on M (no new knob):
          U(a₀) = α E_P / N_a0 = α² m_e c² ; BE = U/2  (virial)
          E_coul(N=1)/E₀ = α/κ = F_NN/F₀     (force lattice)
          BE/E₀ = Δm/m_arg ≪ 1               (soft Arg ledger, not one E₀ click)

        Optics: charge↔vacuum coupling, F₀ landing, hop ladder, and QM mass defect
        are one α. Deriving any one without α derives all.
        """
        alpha_c = 7.2973525693e-3
        hop = self.alpha_hop_ladder_row()
        n_a0 = float(hop["N_a0_Bohr"])
        kappa = KAPPA_FCC_1TICK
        m_e = self.m_e_CODATA
        be = 0.5 * alpha_c**2 * m_e * self.c**2
        dm = be / self.c**2
        f_p = self.c**4 / self.G
        e_coul_nn = alpha_c * f_p * self.l_P
        u_a0 = alpha_c * self.E_P / n_a0
        inventory: list[dict[str, str | float | bool]] = [
            {
                "id": "qm_floor_alpha_from_mass_defect",
                "ratio": math.sqrt(2.0 * dm / m_e),
                "maps_to": "α = √(2 Δm/m_e) — H Rydberg mass defect",
                "status": "qm_floor_DoD",
            },
            {
                "id": "virial_U_a0",
                "ratio": u_a0 / (alpha_c**2 * m_e * self.c**2),
                "maps_to": "U(a₀)=α E_P/N_a0 = α² m_e c²",
                "status": "identity",
            },
            {
                "id": "virial_BE_half_U",
                "ratio": u_a0 / be,
                "maps_to": "BE = U/2",
                "status": "identity",
            },
            {
                "id": "force_lattice_same_alpha",
                "ratio": e_coul_nn / self.E_0,
                "maps_to": "E_coul(N=1)/E₀ = α/κ",
                "status": "identity",
            },
            {
                "id": "soft_Arg_ledger",
                "ratio": be / self.E_0,
                "maps_to": "BE ≪ E₀ — binding is coarse Arg, not one E₀ quantum",
                "status": "shipped_scale",
            },
            {
                "id": "open_Arg_binding_without_alpha",
                "maps_to": "derive Δm from Arg p–e bond on Λ without inserting α",
                "status": "open",
            },
        ]
        return {
            "theorem": "§8.2·α·mass-defect — QM Δm and α are one upstairs",
            "BE_J": be,
            "delta_m_kg": dm,
            "delta_m_over_m_e": dm / m_e,
            "alpha_from_mass_defect": math.sqrt(2.0 * dm / m_e),
            "alpha_codata": alpha_c,
            "rel_alpha_from_dm": abs(math.sqrt(2.0 * dm / m_e) - alpha_c) / alpha_c,
            "U_a0_over_BE": u_a0 / be,
            "E_coul_NN_over_E0": e_coul_nn / self.E_0,
            "alpha_over_kappa": alpha_c / kappa,
            "BE_over_E0": be / self.E_0,
            "inventory": inventory,
            "ask_ok": abs(math.sqrt(2.0 * dm / m_e) - alpha_c) / alpha_c < 1e-12
            and abs(u_a0 / be - 2.0) < 1e-12
            and abs(e_coul_nn / self.E_0 - alpha_c / kappa) < 1e-12,
            "note": (
                "Optics: α=√(2Δm/m_e) on QM floor; same α in U(a₀), F₀ lattice. "
                "DoD: Arg-binding → Δm. OPEN: Δm without α-input."
            ),
        }

    def alpha_arg_binding_try_row(self) -> dict[str, float | int | str | bool | list]:
        """§8.2·α·Arg-try — try Δm from Arg ledger without α-input.

        Exact bridge (no new knob; demoted α₀=κ/M in identities, U=E₀/(M N_a0), BE=U/2):
            Δm / m_arg = BE/E₀ = 1/(2 M N_a0)
            Δm / m_e   = κ²/(2 M²) = α²/2

        Try without inserting α:
          • int M∈{96,97} → Δm/m_e (same score as F-ask; ~±2e3 ppm at 97)
          • reject 1/(2·137²) — injects α_geom
          • reject m_e² N_φ/(2 m_H) as derivation — m_e cascade already has α
          • reject fraction=1/11 on foot r=1/(4π) — ~8.6e3 ppm, worse than M=97

        Still OPEN: M and/or N_a0 from g/shell without α. Identity unifies
        F-ask, H-ask, and QM mass-defect into one Arg ledger.
        """
        alpha_c = 7.2973525693e-3
        kappa = KAPPA_FCC_1TICK
        hop = self.alpha_hop_ladder_row()
        n_a0 = float(hop["N_a0_Bohr"])
        n_c = float(hop["N_c_macro"])
        m_e = self.m_e_CODATA
        m_target = alpha_c**2 / 2.0
        m_star = kappa / alpha_c  # ≈96.899
        be = 0.5 * alpha_c**2 * m_e * self.c**2
        dm = be / self.c**2
        # exact Arg identity at continuous M*
        arg_ratio = 1.0 / (2.0 * m_star * n_a0)
        dm_from_arg = self.m_arg * arg_ratio

        def ppm_dm(frac: float) -> float:
            return (frac - m_target) / m_target * 1e6

        cand_96 = (kappa / 96.0) ** 2 / 2.0
        cand_97 = (kappa / 97.0) ** 2 / 2.0
        cand_137 = 1.0 / (2.0 * 137.0**2)
        cand_11 = (1.0 / (4.0 * math.pi * 11.0)) ** 2 / 2.0
        # circular mass route (score only)
        elec = self.electron_mass_row()
        higgs = self.higgs_mass_row()
        cand_mass = float(elec["m_e_GeV"]) * 13.0 / (2.0 * float(higgs["m_H_GeV"]))

        inventory: list[dict[str, str | float | bool]] = [
            {
                "id": "arg_ledger_identity",
                "ratio": abs(dm_from_arg / dm - 1.0),
                "maps_to": "Δm = m_arg/(2 M N_a0) — Arg ticks of H binding",
                "status": "identity",
            },
            {
                "id": "be_over_e0_is_arg_count",
                "ratio": abs(be / self.E_0 - arg_ratio),
                "maps_to": "BE/E₀ = 1/(2 M N_a0)",
                "status": "identity",
            },
            {
                "id": "try_M97",
                "ratio": cand_97,
                "ppm": ppm_dm(cand_97),
                "maps_to": "Δm/m_e = κ²/(2·97²) — best int M from F-ask",
                "status": "probe_best_int",
            },
            {
                "id": "try_M96",
                "ratio": cand_96,
                "ppm": ppm_dm(cand_96),
                "maps_to": "Δm/m_e = κ²/(2·96²) — N₁₂·N_hier",
                "status": "probe",
            },
            {
                "id": "reject_137_square",
                "ratio": cand_137,
                "ppm": ppm_dm(cand_137),
                "maps_to": "1/(2·137²) injects α_geom",
                "status": "rejected",
            },
            {
                "id": "reject_foot_times_1_over_11",
                "ratio": cand_11,
                "ppm": ppm_dm(cand_11),
                "maps_to": "α≟1/(4π·11); 11=FP exp — wrong scale",
                "status": "rejected",
            },
            {
                "id": "reject_mass_cascade_as_derivation",
                "ratio": cand_mass,
                "ppm": ppm_dm(cand_mass),
                "maps_to": "m_e N_φ/(2 m_H) — m_e already α-built",
                "status": "rejected_circular",
            },
            {
                "id": "open_M_or_Na0_from_g",
                "maps_to": "need M and/or N_a0 from shell/holonomy without α",
                "status": "open",
            },
        ]
        return {
            "theorem": "§8.2·α·Arg-try — Arg ledger of H binding; derivation still open",
            "M_star": m_star,
            "N_a0": n_a0,
            "N_c": n_c,
            "delta_m_over_m_arg": arg_ratio,
            "delta_m_over_m_e_target": m_target,
            "BE_over_E0": be / self.E_0,
            "rel_arg_identity": abs(dm_from_arg / dm - 1.0),
            "try_M97_dm_over_me": cand_97,
            "try_M97_ppm": ppm_dm(cand_97),
            "try_M96_ppm": ppm_dm(cand_96),
            "reject_137_ppm": ppm_dm(cand_137),
            "reject_1_over_11_ppm": ppm_dm(cand_11),
            "derivation_closed": False,
            "inventory": inventory,
            "ask_ok": abs(dm_from_arg / dm - 1.0) < 1e-12
            and abs(be / self.E_0 - arg_ratio) < 1e-12
            and abs(ppm_dm(cand_97) + 2079.655) < 1.0,
            "note": (
                "Arg identity Δm=m_arg/(2MN_a0) closed. Best α-free int try: M=97 "
                "(~−2080 ppm). Derivation OPEN — need M or N_a0 from g."
            ),
        }

    def alpha_schwinger_ask_row(self) -> dict[str, float | int | str | bool | list]:
        """§8.2·α·Schwinger — start from ae (lab door), not from π-tower.

        Experiment (Kusch / Schwinger → geonium): measure ae=(g−2)/2, then
            ae = α/(2π) + O(α²)   (one-loop)
            α = 2π ae + higher

        Carrier rhyme (exact identity, no new knob):
            vacuum foot r = Δφ_min/(2π) = 1/(4π)   (§8.2·descent)
            α/(2π) = 2 α r
        ⇒ leading Schwinger = twice foot × α. Factor 1/(2π) is geometric
        (Heisenberg floor on the tick cycle), not a fitted QED constant.

        Ask / DoD:
          • Dirac g=2 for charge vortex n=±1 — topology? (bare)
          • A5 bath dresses magnetic moment → ae without inserting α
          • then α = ae/(2r) = 2π ae is upstairs readout

        One-loop vs CODATA ae ≈ +1516 ppm (higher loops); identity 2αr holds exact.
        """
        alpha_c = 7.2973525693e-3
        # CODATA 2018 ae (electron)
        ae_codata = 1.15965218128e-3
        dphi = DELTA_PHI_MIN
        r = dphi / (2.0 * math.pi)  # = 1/(4π)
        ae_schwinger = alpha_c / (2.0 * math.pi)
        two_a_r = 2.0 * alpha_c * r
        alpha_from_ae_1loop = 2.0 * math.pi * ae_codata
        inventory: list[dict[str, str | float | bool]] = [
            {
                "id": "lab_door_ae",
                "maps_to": "measure ae in Penning (geonium); α from QED series",
                "status": "shipped_experiment",
            },
            {
                "id": "schwinger_one_loop",
                "ratio": ae_schwinger,
                "maps_to": "ae = α/(2π) + O(α²)",
                "status": "identity_leading",
            },
            {
                "id": "foot_times_two_alpha",
                "ratio": abs(two_a_r / ae_schwinger - 1.0),
                "maps_to": "α/(2π) = 2 α r with r=Δφ_min/(2π)=1/(4π)",
                "status": "identity",
            },
            {
                "id": "factor_1_over_2pi_is_geometry",
                "ratio": abs(ae_schwinger / alpha_c - 1.0 / (2.0 * math.pi)),
                "maps_to": "1/(2π) = 2r — Heisenberg foot on tick, not fitted",
                "status": "shipped_geometry",
            },
            {
                "id": "one_loop_vs_codata_ae",
                "ppm": (ae_schwinger - ae_codata) / ae_codata * 1e6,
                "maps_to": "higher loops ~1.5e3 ppm — expected",
                "status": "expected_gap",
            },
            {
                "id": "open_Dirac_g2_on_vortex",
                "maps_to": "→ §8.2·α·g2·ask (closed bare)",
                "status": "delegated",
            },
            {
                "id": "open_A5_dressing_ae_without_alpha",
                "maps_to": "→ §8.2·α·g2·ask (still open)",
                "status": "delegated",
            },
        ]
        return {
            "theorem": "§8.2·α·Schwinger — lab door ae; foot explains 1/(2π)",
            "alpha_codata": alpha_c,
            "ae_CODATA": ae_codata,
            "ae_Schwinger_1loop": ae_schwinger,
            "vacuum_foot_r": r,
            "two_alpha_r": two_a_r,
            "rel_2ar_vs_schwinger": abs(two_a_r / ae_schwinger - 1.0),
            "ae_over_alpha": ae_schwinger / alpha_c,
            "one_over_2pi": 1.0 / (2.0 * math.pi),
            "alpha_from_ae_1loop": alpha_from_ae_1loop,
            "vs_codata_alpha_ppm_1loop": (alpha_from_ae_1loop - alpha_c)
            / alpha_c
            * 1e6,
            "one_loop_vs_ae_ppm": (ae_schwinger - ae_codata) / ae_codata * 1e6,
            "derivation_closed": False,
            "inventory": inventory,
            "ask_ok": abs(two_a_r / ae_schwinger - 1.0) < 1e-15
            and abs(ae_schwinger / alpha_c - 1.0 / (2.0 * math.pi)) < 1e-15,
            "note": (
                "Start here: ae lab door. Identity ae^(1)=2αr with r=1/(4π). "
                "Bare g=2 + A5→ae: see alpha_dirac_g2_ask_row."
            ),
        }

    def alpha_dirac_g2_ask_row(self) -> dict[str, float | int | str | bool | list]:
        """§8.2·α·g2·ask — asked carrier: bare g=2 and A5→ae without α.

        Method (same as §8.2·H·ask / geo·ask):
          (1) list stamped facts of n=±1 vortex + spinor;
          (2) what fixes gyromagnetic ratio without α;
          (3) what A5 bath can dress into ae;
          (4) reject circular / wrong-scale; report.

        Carrier answers (2026-09-24):
          • A4 + A16 / §3.10: spin-½ double cover — 2π→−1, 4π→+1.
          • Thm 5.1: L₀=s₀=ℏ/2 — one spin quantum on hV.
          • A10: charge n=±1 on electron pra-vortex.
          • Orbital circulating charge → g_orb=1 (μ=(Q/2m)L).
          • Double cover doubles spin magnetic response vs orbital → bare g_s=2.
          • ⇒ μ_bare = e ℏ/(2m) = μ_B for |S|=ℏ/2, |Q|=e — no α.
          • A5 bath: ρ_field>0 dresses moment; ae=(g−2)/2.
          • Identity (Schwinger door): ae^(1)=2α r with r=Δφ_min/(2π).
          • REJECT ae≟r or ae≟2r (⇒ α=1 or ½).
          • REJECT ae≟|z|_vac² (Planck z_min scale, not ~10⁻³).
          • REJECT α-input into dressing (circular for upstairs α=ae/(2r)).
          • REJECT CODATA ae as M-definition of α (T-anchor / series).
          • OPEN: A5 holonomy-cloud fraction → ae without α; then α=ae/(2r).
        """
        dphi = DELTA_PHI_MIN
        r = dphi / (2.0 * math.pi)  # = 1/(4π)
        two_r = 2.0 * r  # = 1/(2π)
        g_orb = 1.0
        double_cover = 2.0  # A16: 4π identity / 2π charge cycle
        g_bare = g_orb * double_cover  # = 2
        ae_bare = (g_bare - 2.0) / 2.0  # = 0
        # wrong-scale / circular candidates (report only)
        bath = self.vacuum_bath_row()
        z_sq = float(bath["z_sq_natural_vac"])
        alpha_c = 7.2973525693e-3
        ae_codata = 1.15965218128e-3
        ae_from_alpha = alpha_c * two_r  # Schwinger 1-loop via identity
        inventory: list[dict[str, str | float | bool]] = [
            {
                "id": "spinor_double_cover",
                "maps_to": "A16 / §3.10: 2π→−1, 4π→+1 on pra-vortex",
                "status": "shipped",
                "mechanism": "A4 SU(2) spinor; CL-2 R(N/2)→−z",
            },
            {
                "id": "L0_equals_s0",
                "ratio": self.s_0,
                "maps_to": "Thm 5.1: L₀=s₀=ℏ/2 — one spin quantum",
                "status": "shipped",
                "mechanism": "Landau ladder; |n_L|=1 for spin-½",
            },
            {
                "id": "charge_n_pm1",
                "maps_to": "A10: ∮ d arg=2πn; electron n=±1",
                "status": "shipped",
                "mechanism": "pra-vortex hV; not α",
            },
            {
                "id": "g_orb_equals_1",
                "ratio": g_orb,
                "maps_to": "circulating charge: μ=(Q/2m)L → g_orb=1",
                "status": "shipped_classical",
                "mechanism": "orbital baseline before spinor",
            },
            {
                "id": "bare_g_equals_2",
                "ratio": g_bare,
                "maps_to": "g_s = g_orb × double_cover = 2",
                "status": "shipped",
                "mechanism": "spatial 2π = half spinor cycle → ×2 magnetic response",
            },
            {
                "id": "ae_bare_zero",
                "ratio": ae_bare,
                "maps_to": "bare ae=(g−2)/2=0 — Dirac floor",
                "status": "shipped",
                "mechanism": "anomaly is dressing, not topology",
            },
            {
                "id": "identity_ae_eq_2alpha_r",
                "ratio": abs(ae_from_alpha / (alpha_c * two_r) - 1.0),
                "maps_to": "ae^(1)=2αr — Schwinger door geometry",
                "status": "identity",
                "mechanism": "not a derivation of ae; upstairs α=ae/(2r)",
            },
            {
                "id": "reject_ae_eq_r",
                "ratio": abs(r / ae_codata - 1.0),
                "maps_to": "ae≟r=1/(4π) ⇒ α=1 — wrong",
                "status": "rejected",
                "mechanism": "foot alone is not the anomaly",
            },
            {
                "id": "reject_ae_eq_2r",
                "ratio": abs(two_r / ae_codata - 1.0),
                "maps_to": "ae≟2r=1/(2π) ⇒ α=1 — wrong",
                "status": "rejected",
                "mechanism": "geometry factor without coupling",
            },
            {
                "id": "reject_ae_eq_z_vac_sq",
                "ratio": z_sq,
                "maps_to": "ae≟|z|_vac² — Planck z_min scale",
                "status": "rejected",
                "mechanism": "A5 floor amplitude ≠ magnetic anomaly ~10⁻³",
            },
            {
                "id": "reject_alpha_input_dressing",
                "maps_to": "insert α to get ae then α=ae/(2r) — circular",
                "status": "rejected",
                "mechanism": "DoD: ae from bath first; α upstairs",
            },
            {
                "id": "reject_codata_ae_as_M_alpha",
                "maps_to": "CODATA ae alone as M-definition of α",
                "status": "rejected_as_M_definition",
                "mechanism": "T-anchor / QED series; ok as lab door, not carrier ae",
            },
            {
                "id": "open_A5_holonomy_cloud_ae",
                "maps_to": "A5 cloud around vortex → ae without α",
                "status": "open",
                "mechanism": "Φ_□ / soft holonomy dressing fraction; then α=ae/(2r)",
            },
        ]
        return {
            "theorem": "§8.2·α·g2·ask — bare g=2 closed; A5→ae open",
            "method": "ask-model: spinor+charge inventory → g → dressing",
            "g_orb": g_orb,
            "double_cover": double_cover,
            "g_bare": g_bare,
            "ae_bare": ae_bare,
            "vacuum_foot_r": r,
            "two_r": two_r,
            "z_sq_natural_vac": z_sq,
            "ae_CODATA": ae_codata,
            "ae_from_alpha_1loop": ae_from_alpha,
            "bare_g2_closed": abs(g_bare - 2.0) < 1e-15 and abs(ae_bare) < 1e-15,
            "derivation_ae_closed": False,
            "reject_ae_eq_r": True,
            "reject_ae_eq_2r": True,
            "reject_ae_eq_z_vac": True,
            "reject_alpha_input": True,
            "inventory": inventory,
            "ask_ok": abs(g_bare - 2.0) < 1e-15
            and abs(ae_bare) < 1e-15
            and abs(two_r - 1.0 / (2.0 * math.pi)) < 1e-15
            and abs(ae_from_alpha / (alpha_c * two_r) - 1.0) < 1e-15,
            "note": (
                "Asked carrier: bare g=2 from A16 double cover × g_orb=1. "
                "A5 dresses ae; reject r/2r/z_vac/α-input. "
                "OPEN: holonomy-cloud → ae; then α=ae/(2r)."
            ),
        }

    def alpha_ae_cloud_ask_row(self) -> dict[str, float | int | str | bool | list]:
        """§8.2·α·ae·ask — asked carrier: A5 holonomy-cloud → ae without α.

        Method: (1) name the cloud on Λ; (2) what dimensionless excess of μ;
        (3) try α-free fractions; (4) reject circular; report.

        Carrier answers (2026-09-24):
          • Cloud = ρ_Θ halo (Heisenberg §5.0.5) + Φ_□ Stokes channel + A5 bath.
          • Factorization (Schwinger door = carrier reading):
                ae^(1) = α · 2r ,  2r = Δφ_min/π = 1/(2π)
            = coupling × tick-cycle geometry. Geometry CLOSED; coupling OPEN
            (same OPEN as §8.2·α·meaning / descent).
          • Pure-geo tries (no α / no 137) land wrong scale — reject as ae.
          • REJECT ae≟2r/137 or α/(2π) as M-derivation (injects α or α_geom).
          • Conclusion: Schwinger door does NOT bypass coupling OPEN;
            it splits α=ae/(2r) with 2r known. ae without α ⇔ coupling fraction
            (or lab ae). Same mountain, sharper factorization.
        """
        dphi = DELTA_PHI_MIN
        r = dphi / (2.0 * math.pi)
        two_r = 2.0 * r
        n12 = int(N12_FCC_CAUSAL_LINKS)
        n_phi = 13
        n_hier = 8
        n_ring = 1 << int(math.floor(2.0 * math.pi / math.log(2.0)))  # 512
        kappa = KAPPA_FCC_1TICK
        alpha_c = 7.2973525693e-3
        ae_codata = 1.15965218128e-3
        ae_1loop = alpha_c * two_r
        # α-free geometric candidates (report ppm vs CODATA ae)
        tries: dict[str, float] = {
            "dphi/N_ring": dphi / n_ring,
            "kappa/N_ring": kappa / n_ring,
            "1/N_ring": 1.0 / n_ring,
            "1/(4pi·N12·N_hier)": 1.0 / (4.0 * math.pi * n12 * n_hier),
            "1/(N12·N_phi·N_hier)": 1.0 / (n12 * n_phi * n_hier),
            "r/N12": r / n12,
            "r/N_phi": r / n_phi,
            "kappa²/N12": (kappa * kappa) / n12,
            "r²": r * r,
        }
        # circular / α-injecting (same scale as one-loop — not a derivation)
        circular = {
            "2r/137": two_r / 137.0,
            "alpha/(2pi)": ae_1loop,
        }

        def ppm(v: float) -> float:
            return (v - ae_codata) / ae_codata * 1e6

        best_geo_name = min(tries, key=lambda k: abs(ppm(tries[k])))
        best_geo_ppm = ppm(tries[best_geo_name])
        inventory: list[dict[str, str | float | bool]] = [
            {
                "id": "cloud_rho_Theta_halo",
                "maps_to": "§5.0.5 ρ_Θ — Heisenberg halo around b=1 core",
                "status": "shipped",
                "mechanism": "|Δφ|,|ζ| ≥ Δφ_min; not δ on one v_p",
            },
            {
                "id": "cloud_Phi_square_channel",
                "maps_to": "Φ_□ Stokes — EM plaquette read of phase cloud",
                "status": "shipped_channel",
                "mechanism": "§8.2 Planck EM; alpha_match_open on probe",
            },
            {
                "id": "cloud_A5_bath",
                "maps_to": "A5 ocean dresses μ; bare ae=0 (g2 ask)",
                "status": "shipped",
                "mechanism": "anomaly = dressing, not topology",
            },
            {
                "id": "factorization_ae_eq_alpha_times_2r",
                "ratio": abs(ae_1loop / (alpha_c * two_r) - 1.0),
                "maps_to": "ae^(1)=α·2r — coupling × geometry",
                "status": "identity",
                "mechanism": "2r closed (foot); α = coupling OPEN",
            },
            {
                "id": "geometry_2r_closed",
                "ratio": two_r,
                "maps_to": "2r=Δφ_min/π=1/(2π)",
                "status": "shipped_geometry",
                "mechanism": "Heisenberg foot on tick cycle",
            },
            {
                "id": "reject_pure_geo_ae",
                "ppm": best_geo_ppm,
                "maps_to": f"best α-free try {best_geo_name} — wrong scale",
                "status": "rejected",
                "mechanism": "|ppm|≫1e3; pure combinatorics ≠ anomaly",
            },
            {
                "id": "reject_2r_over_137",
                "ppm": ppm(circular["2r/137"]),
                "maps_to": "ae≟2r/137 — injects α_geom",
                "status": "rejected",
                "mechanism": "then α=ae/(2r) returns 1/137; empty",
            },
            {
                "id": "reject_alpha_over_2pi_as_M_ae",
                "ppm": ppm(circular["alpha/(2pi)"]),
                "maps_to": "ae≟α/(2π) as M-derivation — circular",
                "status": "rejected",
                "mechanism": "identity ok; not a source of ae without α",
            },
            {
                "id": "open_same_coupling_fraction",
                "maps_to": "ae without α ⇔ discrete coupling fraction",
                "status": "open",
                "mechanism": "same mountain as meaning/descent; door only factors",
            },
        ]
        return {
            "theorem": "§8.2·α·ae·ask — ae=α·2r factors; cloud ≠ new α path",
            "method": "ask-model: name cloud → try fractions → reject → report",
            "vacuum_foot_r": r,
            "two_r": two_r,
            "ae_CODATA": ae_codata,
            "ae_1loop_from_alpha": ae_1loop,
            "one_loop_vs_ae_ppm": ppm(ae_1loop),
            "best_geo_try": best_geo_name,
            "best_geo_ppm": best_geo_ppm,
            "try_ppm": {k: ppm(v) for k, v in tries.items()},
            "circular_ppm": {k: ppm(v) for k, v in circular.items()},
            "factorization_closed": True,
            "derivation_ae_closed": False,
            "bypasses_coupling_open": False,
            "inventory": inventory,
            "ask_ok": abs(ae_1loop / (alpha_c * two_r) - 1.0) < 1e-15
            and abs(best_geo_ppm) > 1e3
            and abs(ppm(circular["2r/137"])) < 5e3,
            "note": (
                "Asked carrier: A5 cloud = ρ_Θ+Φ_□+bath. ae^(1)=α·2r factors "
                "(2r closed, α open). Pure-geo ae rejects; 2r/137 and α/(2π) "
                "circular. Schwinger door does not bypass coupling OPEN."
            ),
        }

    def alpha_rydberg_hall_ask_row(self) -> dict[str, float | int | str | bool | list]:
        """§8.2·α·Rydberg·Hall — lab doors next to Schwinger; same mountain?

        Lab (spectroscopy / QHE):
          R_∞ from H/D lines → α²·m_e (with QED theory).
          R_K = h/e² (von Klitzing) → historically α=μ₀c/(2 R_K);
          SI-2019: e,h exact ⇒ R_K exact; α no longer from Hall alone (μ₀ measured).

        Carrier rhymes (identities, no new knob):
          vacuum foot r = Δφ_min/(2π) = 1/(4π)
          R_∞ = α² · r / λ̄_C = (α² m_e c / ℏ) · r
            — Rydberg = α² × Compton⁻¹ × same foot as Schwinger.
          Hop already: α² = N_re/N_a0 ; α = √(2Δm/m_e) — same α² power.
          Hall: R_K = h/e₀² — conductance quantum; topological plateau.
            Factor 2 in α=μ₀c/(2 R_K) is SI EM (≠ 2r).

        Ask answers:
          • Both doors read α (or α²) from outside — do NOT derive coupling on M.
          • Rydberg factors α²·r — geometry r closed; α² still needs coupling or hops.
          • Hall post-2019 is metrology of h/e², not an α source.
          • REJECT optical a₀ / R_∞ alone as M-definition of α (T-anchors).
          • REJECT inventing α from R_K without μ₀/ε₀ bridge (SI dress).
          • Same OPEN: discrete coupling fraction (or lab α via any door).
        """
        alpha_c = 7.2973525693e-3
        r = DELTA_PHI_MIN / (2.0 * math.pi)
        # CODATA-ish anchors (SI exact e,h,c; R_∞ 2018/2022 class)
        r_inf_codata = 10973731.568160  # m⁻¹
        m_e = self.m_e_CODATA
        hbar = self.hbar
        c = self.c
        e = 1.602176634e-19  # exact SI
        h_pl = 6.62607015e-34  # exact SI
        r_k = h_pl / (e * e)  # exact after 2019
        mu0_legacy = 4.0e-7 * math.pi  # pre-2019 exact μ₀
        # Rydberg identity with foot r
        lambar_c = hbar / (m_e * c)
        r_inf_from_foot = (alpha_c * alpha_c) * r / lambar_c
        r_inf_classic = (alpha_c * alpha_c) * m_e * c / (4.0 * math.pi * hbar)
        # Hall legacy readout (μ₀ exact era)
        alpha_from_hall_legacy = mu0_legacy * c / (2.0 * r_k)
        hop = self.alpha_hop_ladder_row()
        alpha2_hop = float(hop["alpha2_from_Nre_over_Na0"])
        inventory: list[dict[str, str | float | bool]] = [
            {
                "id": "lab_door_rydberg",
                "maps_to": "measure R_∞ (H/D spectroscopy); α² from R_∞+m_e+QED",
                "status": "shipped_experiment",
            },
            {
                "id": "lab_door_hall",
                "maps_to": "QHE plateau R_H=R_K/i; R_K=h/e²",
                "status": "shipped_experiment",
            },
            {
                "id": "rydberg_foot_identity",
                "ratio": abs(r_inf_from_foot / r_inf_classic - 1.0),
                "maps_to": "R_∞ = α²·r/λ̄_C — same foot r as Schwinger",
                "status": "identity",
                "mechanism": "1/(4π)=r; not a derivation of α",
            },
            {
                "id": "rydberg_vs_codata",
                "ppm": (r_inf_from_foot - r_inf_codata) / r_inf_codata * 1e6,
                "maps_to": "identity vs R_∞ CODATA (α input)",
                "status": "identity_check",
            },
            {
                "id": "hop_alpha2_same_power",
                "ratio": abs(alpha2_hop / (alpha_c * alpha_c) - 1.0),
                "maps_to": "α²=N_re/N_a0 — Rydberg power already on ladder",
                "status": "identity",
                "mechanism": "§8.2 hop; N_a0 still open from g",
            },
            {
                "id": "hall_RK_exact_SI2019",
                "ratio": r_k,
                "maps_to": "R_K=h/e² exact after SI-2019",
                "status": "shipped_metrology",
                "mechanism": "e,h fixed; Hall no longer independent α source",
            },
            {
                "id": "hall_legacy_alpha_mu0",
                "ppm": (alpha_from_hall_legacy - alpha_c) / alpha_c * 1e6,
                "maps_to": "α=μ₀c/(2 R_K) — pre-2019 door",
                "status": "legacy_identity",
                "mechanism": "factor 2 is SI EM, not 2r",
            },
            {
                "id": "reject_Rinf_as_M_alpha",
                "maps_to": "R_∞ alone as M-definition of α",
                "status": "rejected_as_M_definition",
                "mechanism": "T-anchor + needs m_e; circular with α² in formula",
            },
            {
                "id": "reject_optical_a0_as_M",
                "maps_to": "a₀ from Rydberg chain as M N_a0",
                "status": "rejected_as_M_definition",
                "mechanism": "already H·ask; T optical length",
            },
            {
                "id": "reject_RK_without_mu0_bridge",
                "maps_to": "α from R_K alone without μ₀/ε₀ (post-2019)",
                "status": "rejected",
                "mechanism": "R_K exact ≠ α; need separate coupling or μ₀",
            },
            {
                "id": "open_same_coupling_fraction",
                "maps_to": "discrete coupling on FCC — same mountain",
                "status": "open",
                "mechanism": "Rydberg/Hall/Schwinger all factor geometry×α^n",
            },
        ]
        return {
            "theorem": "§8.2·α·Rydberg·Hall — lab doors; foot in R_∞; same OPEN",
            "vacuum_foot_r": r,
            "R_inf_CODATA": r_inf_codata,
            "R_inf_from_alpha2_r_over_lambar": r_inf_from_foot,
            "rel_Rinf_foot_vs_classic": abs(r_inf_from_foot / r_inf_classic - 1.0),
            "Rinf_vs_codata_ppm": (r_inf_from_foot - r_inf_codata)
            / r_inf_codata
            * 1e6,
            "R_K_ohm_exact": r_k,
            "alpha_from_Hall_legacy_mu0": alpha_from_hall_legacy,
            "Hall_legacy_vs_codata_ppm": (alpha_from_hall_legacy - alpha_c)
            / alpha_c
            * 1e6,
            "alpha2_hop": alpha2_hop,
            "alpha2_codata": alpha_c * alpha_c,
            "factorization_rydberg_closed": True,
            "hall_is_alpha_source_post2019": False,
            "derivation_closed": False,
            "bypasses_coupling_open": False,
            "inventory": inventory,
            "ask_ok": abs(r_inf_from_foot / r_inf_classic - 1.0) < 1e-15
            and abs((r_inf_from_foot - r_inf_codata) / r_inf_codata) < 1e-8
            and abs((alpha_from_hall_legacy - alpha_c) / alpha_c) < 1e-8
            and abs(alpha2_hop / (alpha_c * alpha_c) - 1.0) < 1e-12,
            "note": (
                "Rydberg: R_∞=α²·r/λ̄_C (foot r). Hall: R_K exact SI-2019; "
                "legacy α=μ₀c/(2R_K). Neither bypasses coupling OPEN."
            ),
        }

    def alpha_em_face_weight_ask_row(self) -> dict[str, float | int | str | bool | list]:
        """§8.2·α·EM·faces — asked carrier: A_□/A_tot, dihedral, V/S → α?

        Method (geo·ask leaf 1): dimensional areas/angles at a=l_P first;
        ask which ratio can be EM coupling; score vs α only AFTER.

        Carrier answers (2026-09-24):
          • Shipped body facts: w_□=A_□/A_tot, w_△, dihedral=135°=3/4·π rad/
            (wait: 135/180=3/4), V/(S a) compactness.
          • Precedent κ=R_in/R_out works because it couples to c,hT,λ₀.
          • Raw weights O(0.1–1) — wrong scale vs α~1/137 (~10⁷ ppm).
          • Scaled tries (w/N₁₂, w·r, V/(Sa)·r, …) still |ppm|≫10³ — reject.
          • α_geom⁻¹=137 uses face *counts* (6□+8△), not area weights —
            different object; already exploratory (~263 ppm), not this leaf.
          • REJECT equating area weight or dihedral fraction with α.
          • Channel that remains: Φ_□ on □ (Stokes) — weight ≠ holonomy.
          • Same OPEN: coupling fraction / live Φ_□ — not face-area α.
        """
        geo = self.cuboctahedron_geometry_row()
        alpha_c = 7.2973525693e-3
        w_sq = float(geo["A_square_over_A_total"])
        w_tri = float(geo["A_triangle_over_A_total"])
        v_sa = float(geo["V_over_S_over_l_P"])
        dihedral_over_180 = float(geo["dihedral_square_triangle_deg"]) / 180.0
        n12 = int(N12_FCC_CAUSAL_LINKS)
        r = DELTA_PHI_MIN / (2.0 * math.pi)
        kappa = KAPPA_FCC_1TICK
        tries: dict[str, float] = {
            "w_square": w_sq,
            "w_triangle": w_tri,
            "dihedral/180": dihedral_over_180,
            "V/(S a)": v_sa,
            "w_square/N12": w_sq / n12,
            "w_triangle/N12": w_tri / n12,
            "w_square/N12²": w_sq / (n12 * n12),
            "w_square·r": w_sq * r,
            "w_triangle·r": w_tri * r,
            "V/(Sa)·r": v_sa * r,
            "dihedral/180/N12": dihedral_over_180 / n12,
            "κ²·w_tri/N12": (kappa * kappa) * w_tri / n12,
        }

        def ppm(v: float) -> float:
            return (v - alpha_c) / alpha_c * 1e6

        best_name = min(tries, key=lambda k: abs(ppm(tries[k])))
        best_ppm = ppm(tries[best_name])
        alpha_geom_inv = float(geo["alpha_fs_inv_geom"])
        inventory: list[dict[str, str | float | bool]] = [
            {
                "id": "body_w_square",
                "ratio": w_sq,
                "maps_to": "A_□ tot / A_tot at a=l_P — dimensional→ratio",
                "status": "shipped_body",
                "mechanism": "6a² vs 6a²+8·(√3/4)a²",
            },
            {
                "id": "body_w_triangle",
                "ratio": w_tri,
                "maps_to": "A_△ tot / A_tot",
                "status": "shipped_body",
            },
            {
                "id": "body_dihedral",
                "ratio": dihedral_over_180,
                "maps_to": "135°/180° = 3/4 — □–△ ridge",
                "status": "shipped_body",
            },
            {
                "id": "body_compactness",
                "ratio": v_sa,
                "maps_to": "V/(S a) at a=l_P",
                "status": "shipped_body",
            },
            {
                "id": "precedent_kappa_not_face_weight",
                "ratio": kappa,
                "maps_to": "κ=R_in/R_out couples c,hT — face weight does not",
                "status": "shipped_precedent",
                "mechanism": "geo·ask: only κ closed as coupling so far",
            },
            {
                "id": "reject_raw_weights_as_alpha",
                "ppm": ppm(w_sq),
                "maps_to": "w_□,w_△,dihedral,V/(Sa) O(0.1–1) ≠ α",
                "status": "rejected",
                "mechanism": "wrong scale ~10⁷ ppm",
            },
            {
                "id": "reject_scaled_face_tries",
                "ppm": best_ppm,
                "maps_to": f"best try {best_name} still wrong scale",
                "status": "rejected",
                "mechanism": "|ppm|≫10³; cooking N₁₂/r does not save",
            },
            {
                "id": "distinct_alpha_geom_counts",
                "ratio": alpha_geom_inv,
                "maps_to": "α_geom⁻¹=137 from face *counts* — not area weight",
                "status": "distinct_exploratory",
                "mechanism": "descent ask; ~263 ppm; not this leaf",
            },
            {
                "id": "open_Phi_square_not_weight",
                "maps_to": "Φ_□ Stokes on □ — channel open; weight ≠ holonomy",
                "status": "open",
                "mechanism": "geo·ask Phi_square; alpha_match_open",
            },
            {
                "id": "open_coupling_fraction",
                "maps_to": "same mountain — discrete coupling / live Φ_□",
                "status": "open",
            },
        ]
        return {
            "theorem": "§8.2·α·EM·faces — area/dihedral ≠ α; Φ_□ still open",
            "method": "ask-model: body areas → try ratios → reject scale",
            "w_square": w_sq,
            "w_triangle": w_tri,
            "dihedral_over_180": dihedral_over_180,
            "V_over_S_over_l_P": v_sa,
            "best_try": best_name,
            "best_ppm": best_ppm,
            "try_ppm": {k: ppm(v) for k, v in tries.items()},
            "alpha_geom_inv": alpha_geom_inv,
            "face_weight_is_alpha": False,
            "derivation_closed": False,
            "bypasses_coupling_open": False,
            "inventory": inventory,
            "ask_ok": abs(w_sq + w_tri - 1.0) < 1e-12
            and abs(best_ppm) > 1e3
            and abs(ppm(w_sq)) > 1e6,
            "note": (
                "Asked carrier: EM face weights/dihedral/V/S are body facts "
                "but wrong scale for α. α_geom=137 is counts≠areas. "
                "OPEN: Φ_□ holonomy, not area weight."
            ),
        }

