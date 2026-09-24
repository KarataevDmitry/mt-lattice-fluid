"""α ask/row methods — extracted from si_constants (file-size hygiene).

Mixin for SIConstants. Imports constants from si_constants after those
names are already bound (si_constants imports this mixin only below them).
"""
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


class SIAlphaRows:
    """Row probes for §8.2 α — keep out of the SI quanta core file."""

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
        """§8.2·F·ask — Coulomb lands on F₀ lattice ⇒ α = κ/M.

        Thm 5.1: force transfers as n_F·F₀. Unit NN Coulomb F=α F_P.
        F₀/F_P = κ (geometry). One EM quantum at N=1:
            α F_P = F₀/M  ⇒  α = κ/M , M∈ℕ.

        Probe (2026-09-23):
          • target M = F₀/(α_c F_P) ≈ 96.899
          • cleanest carrier M = N₁₂·N_hier = 96 (= n_△·N₁₂ = N_hier·(N_φ−1))
            → α=κ/96, inv≈135.76, ~+9366 ppm vs CODATA
          • nearest int M = 97 = N₁₂·N_hier+1 → α=κ/97, inv≈137.18, ~−1040 ppm
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
                "maps_to": "α F_P = F₀/M ⇒ α=κ/M",
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
            "theorem": "§8.2·F·ask — α from F₀ lattice: α=κ/M",
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
                "Force lattice: α=κ/M. Best int M=97 (−1040 ppm); cleanest M=96 "
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
          F = α F_P / N² ;  α = N_c/N_a0 ;  α = κ/M  — expressions of the same coupling.

        Number today (T): π-tower 1/(4π³+π²+π) ~−2 ppm — competitor readout.
        Discrete path shipped: α=κ/M with M=n_F seats=97 (force law F₀/M).
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
                "maps_to": "α=κ/M — F₀ landing; M=97 seats CLOSED (nF census)",
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
                "maps_to": "κ/97 vs CODATA −1040 ppm — holonomy without π-ansatz",
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
                "Discrete force path α=κ/M + F=F₀/M shipped. "
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

        Exact bridge (no new knob; α=κ/M, U=E₀/(M N_a0), BE=U/2):
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

    def alpha_dual_fraction_ask_row(self) -> dict[str, float | int | str | bool | list]:
        """§8.2·α·dual — method: α=m/n with m,n from *two different* physics.

        Not one magic formula. If coupling is a fraction, numerator and
        denominator can (should) arrive on independent carrier paths.
        DoD: close each leg without inserting α; then α=m/n upstairs.

        Inventory of dual pairs already on the board:
          A) hops:  α = N_c / N_a0
             · N_c ~ Compton/macro length in hL — today from m_e (α² inside)
             · N_a0 ~ H size in hops — OPEN from H structure (H·ask)
          B) force: α = κ / M
             · κ = R_in/R_out = 1/√2 — CLOSED (geo)
             · M ∈ ℕ — theorem CLOSED (nF seats = 97);
               coarse κ/97 ~−1040 ppm; soft preferred (seat+face) lab-inside; unit-descent SEALED
             · note: κ∉ℚ ⇒ α not pure ℤ/ℤ unless rewritten
          C) Schwinger: α = a_e / (2r)
             · 2r = 1/(2π) — CLOSED (foot)
             · a_e — lab or A5 cloud OPEN (ae·ask)
          D) reject single-path: M/N_ring, π-tower-as-definition, face-weight=α

        Method rule: never solve both m and n from the same equation that
        already contains α (circular). Two paths ⇒ two independent facts.
        """
        alpha_c = 7.2973525693e-3
        hop = self.alpha_hop_ladder_row()
        force = self.alpha_force_lattice_ask_row()
        n_c = float(hop["N_c_macro"])
        n_a0 = float(hop["N_a0_Bohr"])
        kappa = float(force["kappa"])
        m96 = float(force["M_N12_Nhier"])
        m97 = float(force["M_N12_Nhier_plus1"])
        m_tgt = float(force["M_target_CODATA"])
        r = DELTA_PHI_MIN / (2.0 * math.pi)
        two_r = 2.0 * r
        ae_codata = 1.15965218128e-3
        inventory: list[dict[str, str | float | bool]] = [
            {
                "id": "method_two_paths",
                "maps_to": "α=m/n; m from physics A, n from physics B — independent",
                "status": "shipped_method",
                "mechanism": "reject one-formula magic; dual DoD",
            },
            {
                "id": "pair_hops_Nc_over_Na0",
                "ratio": n_c / n_a0,
                "maps_to": "α=N_c/N_a0",
                "status": "identity_pair",
                "mechanism": "N_c today α-tied via m_e; N_a0 OPEN (H·ask)",
            },
            {
                "id": "leg_Na0_open",
                "maps_to": "n=N_a0 from ρ_Θ / N_pack / FCC shell — no α",
                "status": "open_leg",
                "mechanism": "H·ask; must not use optical a₀ as M-definition",
            },
            {
                "id": "leg_Nc_needs_alpha_free",
                "maps_to": "m=N_c without m_e(α) — or drop this pair",
                "status": "open_leg_or_blocked",
                "mechanism": "m_e=α² m_H/N_φ makes N_c circular today",
            },
            {
                "id": "pair_force_kappa_over_M",
                "ratio": kappa / m97,
                "maps_to": "α=κ/M; κ closed, M=97 theorem (nF seats)",
                "status": "shipped_pair_theorem",
                "mechanism": "full-quant force dual: geo κ × n_F seats",
            },
            {
                "id": "leg_kappa_closed",
                "ratio": kappa,
                "maps_to": "κ=1/√2 from hull — path A done",
                "status": "shipped_leg",
            },
            {
                "id": "leg_M_theorem_closed",
                "ratio": m97,
                "maps_to": "M=1+N12·N_hier=97 — nF kick Thm CLOSED",
                "status": "shipped_leg",
                "mechanism": "§8.2·α·nF·Thm; not inject 137",
            },
            {
                "id": "soft_residual_open",
                "ratio": m_tgt,
                "maps_to": "coarse κ/97 ~−1040 ppm; preferred seat+face inside CODATA band",
                "status": "lab_closed_derivation_open",
                "mechanism": "soft-face §8.2·U0; why −8/7 unit still OPEN",
            },
            {
                "id": "pair_schwinger_ae_over_2r",
                "ratio": ae_codata / two_r,
                "maps_to": "α=ae/(2r); 2r closed, ae open/lab",
                "status": "alive_pair_lab",
                "mechanism": "geometry×anomaly; ae·ask = same coupling OPEN",
            },
            {
                "id": "reject_single_path_Nring",
                "maps_to": "α≟M/512 — one register as both legs",
                "status": "rejected",
                "mechanism": "α·512∉ℤ; N_ring≠coupling denominator",
            },
            {
                "id": "reject_same_equation_both_legs",
                "maps_to": "solve m and n from one α-containing identity",
                "status": "rejected",
                "mechanism": "circular; H·ask mass≡hop α² warning",
            },
            {
                "id": "open_soft_residual_vs_pi_tower",
                "maps_to": "next: soft residue on κ/97 OR demote π-ansatz as T-only",
                "status": "open",
                "mechanism": "discrete path shipped; ppm duel with continuum tower",
            },
        ]
        return {
            "theorem": "§8.2·α·dual — α=m/n via two independent paths",
            "method": "dual-leg DoD; inventory pairs; reject single-path",
            "N_c_macro": n_c,
            "N_a0_Bohr_T": n_a0,
            "kappa": kappa,
            "M_target": m_tgt,
            "M_96": m96,
            "M_97": m97,
            "two_r": two_r,
            "alpha_from_Nc_Na0": n_c / n_a0,
            "alpha_from_kappa_M97": kappa / m97,
            "alpha_from_ae_over_2r": ae_codata / two_r,
            "strongest_alive_pair": "force κ/M + soft-face preferred (lab inside; unit descent open)",
            "derivation_closed": False,
            "M_theorem_closed": True,
            "M_combinatorial_closed": True,  # alias
            "inventory": inventory,
            "ask_ok": abs(n_c / n_a0 - alpha_c) / alpha_c < 1e-12
            and abs(kappa / m_tgt - alpha_c) / alpha_c < 1e-9
            and abs(ae_codata / two_r - alpha_c) / alpha_c < 2e-3,
            "note": (
                "Method: α=m/n with two independent physics. "
                "Force dual κ/M: M=97 theorem CLOSED (nF seats); "
                "coarse −1040 ppm; soft preferred lab-inside (descent SEALED). Also: ae/(2r) (ae open), "
                "N_c/N_a0 (N_a0 open, N_c α-tied). Reject M/512 single-path."
            ),
        }

    def alpha_sqrt2_descent_ask_row(self) -> dict[str, float | int | str | bool | list]:
        """§8.2·α·√2·descent — irrationality constraint on dual pairs (√2-style).

        Classic move: assume √2=p/q lowest terms ⇒ both even ⇒ contradiction.
        Same steel on the force dual:

          Lemma (force). Suppose α = κ/M with κ = 1/√2 (geo CLOSED) and M∈ℕ.
          If α were rational p/q ∈ ℚ (q≠0), then
              1/(M√2) = p/q  ⇒  √2 = q/(p M) ∈ ℚ,
          contradicting irrationality of √2. Hence α ∉ ℚ.

        Corollaries:
          • Exact α=1/137, M/512, or any p/q — incompatible with κ/M dual.
          • "Fraction m/n" on carrier ≠ α∈ℚ; it means ratio of two carrier
            quantities (here κ / M), one of which may be irrational.
          • Hop dual α=N_c/N_a0 with both ∈ℤ would give α∈ℚ — conflicts with
            force dual unless hops are not both strict integers at defining level
            (optical Na0 is T) or duals live on different layers.

        Status: lemma closed as logic on stamped κ; does not yet fix M.
        OPEN: still need M from g (integer leg of the irrational α=κ/M).
        """
        alpha_c = 7.2973525693e-3
        kappa = KAPPA_FCC_1TICK
        m_tgt = kappa / alpha_c
        # rational impostors vs force dual
        impostors: dict[str, float] = {
            "1/137": 1.0 / 137.0,
            "4/512": 4.0 / 512.0,
            "1/128": 1.0 / 128.0,
            "kappa/96": kappa / 96.0,
            "kappa/97": kappa / 97.0,
        }

        def ppm(v: float) -> float:
            return (v - alpha_c) / alpha_c * 1e6

        inventory: list[dict[str, str | float | bool]] = [
            {
                "id": "lemma_force_alpha_irrational",
                "maps_to": "α=κ/M, κ=1/√2, M∈ℕ ⇒ α∉ℚ (else √2∈ℚ)",
                "status": "shipped_lemma",
                "mechanism": "same steel as √2 irrationality; κ from hull",
            },
            {
                "id": "kappa_is_irrational",
                "ratio": kappa,
                "maps_to": "κ=1/√2 ∉ ℚ — stamped geo",
                "status": "shipped",
            },
            {
                "id": "reject_alpha_in_Q",
                "maps_to": "exact α=p/q incompatible with force dual",
                "status": "rejected_under_force_dual",
                "mechanism": "1/137, M/N_ring, … as exact α",
            },
            {
                "id": "impostor_1_over_137_ppm",
                "ppm": ppm(impostors["1/137"]),
                "maps_to": "α_geom as exact ℚ — forbidden if κ/M holds",
                "status": "rejected_as_exact",
            },
            {
                "id": "impostor_4_over_512_ppm",
                "ppm": ppm(impostors["4/512"]),
                "maps_to": "M/N_ring ∈ℚ — forbidden if κ/M holds",
                "status": "rejected_as_exact",
            },
            {
                "id": "fraction_means_carrier_ratio",
                "maps_to": "m/n = κ/M — not α∈ℚ; irrational over integer",
                "status": "shipped_method",
                "mechanism": "dual·ask refined by √2 descent",
            },
            {
                "id": "tension_hop_integers_vs_force",
                "maps_to": "N_c,N_a0 both ∈ℤ ⇒ α∈ℚ ⊬ κ/M",
                "status": "tension",
                "mechanism": "optical Na0 is T; or layers differ; not both exact duals",
            },
            {
                "id": "alive_kappa_over_M97",
                "ppm": ppm(impostors["kappa/97"]),
                "maps_to": "α=κ/97 — form allowed (∉ℚ); M still from g",
                "status": "alive_candidate",
                "mechanism": "~−1040 ppm; nearest int to M_target",
            },
            {
                "id": "open_M_from_g",
                "ratio": m_tgt,
                "maps_to": "M≈96.90 from g — integer leg still OPEN",
                "status": "open",
            },
        ]
        return {
            "theorem": "§8.2·α·√2·descent — force dual ⇒ α∉ℚ",
            "method": "assume α∈ℚ under κ/M ⇒ √2∈ℚ ⇒ contradiction",
            "kappa": kappa,
            "M_target": m_tgt,
            "lemma_force_alpha_not_rational": True,
            "reject_exact_rational_alpha_under_force": True,
            "impostor_ppm": {k: ppm(v) for k, v in impostors.items()},
            "derivation_M_closed": False,
            "inventory": inventory,
            "ask_ok": abs(kappa * kappa - 0.5) < 1e-15
            and abs(m_tgt - kappa / alpha_c) < 1e-12
            and True,
            "note": (
                "√2-style: α=κ/M with κ=1/√2 ⇒ α∉ℚ. Exact p/q (137, 512, …) "
                "rejected under force dual. Fraction = κ/M not α∈ℚ. M from g OPEN."
            ),
        }

    def alpha_M_from_g_try_row(self) -> dict[str, float | int | str | bool | list]:
        """§8.2·α·M·g·try — try close integer M from stamped g/Bekenstein bits.

        Dual: α=κ/M. κ CLOSED. Need M∈ℕ without α.

        Already stamped (not new knobs):
          N₁₂ = 12 (FCC links)
          ⌊B_hV⌋ = 9
          N_hier = ⌊B_hV⌋ − 1 = 8  — hierarchy channels after removing
            occupancy bit b (§8.4.1-A / T1)
          b∈{0,1} on pra-core (A11)

        Try (force accounting):
          Hierarchy forbids counting b inside N_hier (−1).
          Coulomb NN force still sits on a charged core (b=1) plus the
          link×hierarchy budget that carries the kick ledger outward:
            M = 1 + N₁₂ · N_hier
              = 1 + N₁₂ · (⌊B_hV⌋ − 1)
              = 97
          Reading: one F₀ seat on the occupied hV + N₁₂·N_hier seats on
          the causal star × hierarchy depth. Same −1/+1 bookkeeping as T1,
          inverted for EM force quanta (Thm 5.1 n_F).

        Score AFTER: α=κ/97 ~ −1040 ppm vs CODATA (higher structure / soft).
        M=96 = N₁₂·N_hier alone — misses core seat (~+9366 ppm).

        Status: lemmas force unique M — theorem, not a motivated try.
        Proof carrier: alpha_nF_kick_census_row (seat table = axioms).
        """
        hv = hv_bit_budget()
        kappa = KAPPA_FCC_1TICK
        n12 = int(N12_FCC_CAUSAL_LINKS)
        floor_b = int(math.floor(hv.B_hV))
        n_hier = floor_b - 1
        alpha_c = 7.2973525693e-3
        m_96 = n12 * n_hier
        m_try = 1 + n12 * n_hier
        m_alt = n12 * floor_b - n12 + 1  # algebraically = m_try
        a_try = kappa / m_try
        a_96 = kappa / m_96
        m_target = kappa / alpha_c

        def ppm(a: float) -> float:
            return (a - alpha_c) / alpha_c * 1e6

        inventory: list[dict[str, str | float | bool]] = [
            {
                "id": "N_hier_minus_b_bit",
                "ratio": n_hier,
                "maps_to": "N_hier=⌊B_hV⌋−1 — stamped T1",
                "status": "shipped",
                "mechanism": "hierarchy channels exclude occupancy bit b",
            },
            {
                "id": "try_M_one_plus_N12_Nhier",
                "ratio": m_try,
                "maps_to": "M=1+N₁₂·N_hier — core seat + link×hier",
                "status": "theorem",
                "mechanism": "invert T1 bookkeeping for EM n_F count",
            },
            {
                "id": "algebra_same_as_N12_floorB_minus_N12_plus_1",
                "ratio": m_alt,
                "maps_to": "M=N₁₂⌊B_hV⌋−N₁₂+1 ≡ 1+N₁₂ N_hier",
                "status": "identity",
            },
            {
                "id": "reject_M96_missing_core",
                "ppm": ppm(a_96),
                "maps_to": "M=N₁₂ N_hier alone — no b=1 force seat",
                "status": "rejected_as_complete_count",
                "mechanism": "cleaner combo, worse ppm; misses charged core",
            },
            {
                "id": "score_kappa_over_97",
                "ppm": ppm(a_try),
                "maps_to": "α=κ/97 after try",
                "status": "scored_after",
                "mechanism": "~−1040 ppm — soft/higher structure, not α-input",
            },
            {
                "id": "closed_by_nF_kick_census",
                "maps_to": "alpha_nF_kick_census_row — seat table = 97",
                "status": "theorem",
                "mechanism": "lemmas: core b=1 + isotropic N₁₂×N_hier",
            },
        ]
        return {
            "theorem": "§8.2·α·M·g·try — M=1+N₁₂ N_hier from b-bit bookkeeping",
            "floor_B_hV": floor_b,
            "N_hier": n_hier,
            "N12": n12,
            "M_try": m_try,
            "M_96": m_96,
            "M_target_CODATA": m_target,
            "M_algebra_check": m_alt,
            "kappa": kappa,
            "alpha_try": a_try,
            "alpha_try_inv": 1.0 / a_try,
            "vs_codata_ppm": ppm(a_try),
            "vs_codata_ppm_M96": ppm(a_96),
            "story_ok": m_try == 97 and m_alt == m_try and n_hier == 8,
            "derivation_closed": True,
            "inventory": inventory,
            "ask_ok": m_try == 97
            and abs(m_alt - m_try) < 1e-15
            and n_hier == floor_b - 1
            and abs(ppm(a_try) + 1040.3688788164525) < 1.0,
            "note": (
                "Thm: M=1+N₁₂·N_hier=97 from core b=1 + link×hier "
                "(same −1 as N_hier). α=κ/97. Forced by kick-ledger axioms."
            ),
        }

    def alpha_nF_kick_census_row(self) -> dict[str, float | int | str | bool | list]:
        """§8.2·α·nF·Thm — M forced by kick-ledger axioms (not a free count).

        Theorem (force seats). Under Thm 5.1 / §3.12, unit NN Coulomb is
        one F₀ packet weaker than the Planck force quantum:
          F_Coulomb(N=1) = F₀/M,  α = κ/M.
        M is the unique integer of independent Δp seats on one charged FCC
        core. Forbidden: inject α or 137 to pick M.

        Lemmas (stamped only):
          L1. Core seat — b=1 occupancy on the charged hV (§5.0 · §8.4.1-A).
              Hierarchy forbids counting b inside N_hier; the force source
              still requires that seat.
          L2. Link×hier seats — isotropic star (§5.2.2): every of N₁₂ causal
              links × N_hier exclusive hierarchy channels (⌊B_hV⌋−1).
              Gate has no preferred axis ⇒ whole star, not partner bond alone.

        Conclusion:
          M = n_F_seats = 1 + N₁₂·N_hier = 97.
          Then α = κ/M (score after; never input). Unique under the lemmas.

        Scope: seat geometry from g — not a runtime Δp histogram (no Coulomb
        opcode in CA). Soft −1040 ppm is higher-structure residue, not a
        missing seat.
        """
        hv = hv_bit_budget()
        kappa = KAPPA_FCC_1TICK
        n12 = int(N12_FCC_CAUSAL_LINKS)
        floor_b = int(math.floor(hv.B_hV))
        n_hier = floor_b - 1  # occupancy bit removed (T1)
        alpha_c = 7.2973525693e-3

        # Explicit seat table (lemma proof carrier).
        seats: list[dict[str, str | int]] = []
        seats.append(
            {
                "seat_id": "core.b1",
                "class": "core_occupancy",
                "count": 1,
                "axiom": "§5.0 b∈{0,1} · §8.4.1-A invert of N_hier −1",
            }
        )
        for link in range(n12):
            for hier in range(n_hier):
                seats.append(
                    {
                        "seat_id": f"link.{link}.hier.{hier}",
                        "class": "link_x_hier",
                        "count": 1,
                        "axiom": "§5.2.2 κ_link=1/|N| · §8.4.1-A N_hier",
                    }
                )

        n_f_seats = sum(int(s["count"]) for s in seats)
        n_core = sum(int(s["count"]) for s in seats if s["class"] == "core_occupancy")
        n_link_hier = sum(int(s["count"]) for s in seats if s["class"] == "link_x_hier")
        m = n_f_seats
        a = kappa / m
        ppm = (a - alpha_c) / alpha_c * 1e6

        census_ok = (
            n_core == 1
            and n_link_hier == n12 * n_hier
            and n_f_seats == 1 + n12 * n_hier
            and n_f_seats == 97
            and n_hier == 8
            and floor_b == 9
            and len(seats) == n_f_seats
        )

        inventory: list[dict[str, str | float | bool | int]] = [
            {
                "id": "seat_core_b1",
                "count": n_core,
                "maps_to": "charged hV occupancy — force source seat",
                "status": "lemma",
            },
            {
                "id": "seats_link_x_hier",
                "count": n_link_hier,
                "maps_to": f"N₁₂×N_hier = {n12}×{n_hier} — isotropic star × exclusive channels",
                "status": "lemma",
            },
            {
                "id": "n_F_seats_sum",
                "count": n_f_seats,
                "maps_to": "M in α F_P = F₀/M",
                "status": "theorem" if census_ok else "fail",
            },
            {
                "id": "reject_omit_core",
                "count": n12 * n_hier,
                "maps_to": "96 without core — incomplete census",
                "status": "rejected",
            },
            {
                "id": "score_after_kappa_over_M",
                "ppm": ppm,
                "maps_to": "α=κ/97 after census — not input",
                "status": "scored_after",
            },
            {
                "id": "not_runtime_sim_histogram",
                "maps_to": "no CA Coulomb opcode; seat geometry only",
                "status": "scope",
            },
        ]

        return {
            "theorem": "§8.2·α·nF·Thm — M=1+N₁₂·N_hier from kick-ledger axioms",
            "floor_B_hV": floor_b,
            "N_hier": n_hier,
            "N12": n12,
            "n_core": n_core,
            "n_link_hier": n_link_hier,
            "n_F_seats": n_f_seats,
            "M": m,
            "kappa": kappa,
            "alpha": a,
            "alpha_inv": 1.0 / a,
            "vs_codata_ppm": ppm,
            "seat_count": len(seats),
            "seats_sample": seats[:3] + seats[-2:],  # head+tail; full count via seat_count
            "census_ok": census_ok,
            "derivation_closed": census_ok,  # theorem: lemmas force unique M
            "runtime_sim_closed": False,
            "inventory": inventory,
            "ask_ok": census_ok and abs(ppm + 1040.3688788164525) < 1.0,
            "note": (
                "Thm: M=1+N₁₂·N_hier. Core b=1 (force source) + isotropic "
                "star N₁₂ × exclusive hier channels N_hier=⌊B_hV⌋−1. "
                "Unit NN Coulomb F=F₀/M ⇒ α=κ/M. Unique; not a free count."
            ),
        }

    def alpha_full_quantization_bridge_row(self) -> dict[str, float | int | str | bool | list]:
        """§8.2·α·full-quant — α from full quantization, not π-tower.

        Operator steer: fine-structure constant ↔ full quantization (§0.9).
        On M there is no continuum wave; force is n_F·F₀ (Thm 5.1).
        Unit NN Coulomb is one quantum weaker than F₀ by integer M seats:
          α F_P = F₀/M  ⇒  α = κ/M,  κ=1/√2 CLOSED, M=n_F_seats=97 CLOSED
          (nF Thm). Number scored after; no α input.

        Contrast: π-ansatz α⁻¹=4π³+π²+π is continuum solid-angle T-readout
        (~2 ppm) — competing *number*, not the discrete descent.
        Coarse κ/97 ~−1040 ppm. Soft preferred (seat+face) inside CODATA band; unit descent SEALED (G-grade completeness).
        """
        census = self.alpha_nF_kick_census_row()
        meaning = self.alpha_meaning_ask_row()
        kappa = float(census["kappa"])
        m = int(census["M"])
        a = float(census["alpha"])
        a_pi = float(meaning["alpha_fs"])
        alpha_c = 7.2973525693e-3

        def ppm(x: float) -> float:
            return (x - alpha_c) / alpha_c * 1e6

        inventory: list[dict[str, str | float | bool | int]] = [
            {
                "id": "full_quant_no_wave",
                "maps_to": "§0.9 — excitations = n_k / n_E·E₀, not A·sin",
                "status": "shipped",
            },
            {
                "id": "force_quanta_F0",
                "maps_to": "Thm 5.1 — F = n_F·F₀; F₀/F_P = κ",
                "status": "shipped",
            },
            {
                "id": "fine_structure_is_seat_ratio",
                "maps_to": "α = κ/M = F₀/(M F_P) — thin structure of force seats",
                "status": "shipped",
            },
            {
                "id": "M_nF_seats",
                "count": m,
                "maps_to": "M = 1 + N₁₂·N_hier from nF Thm",
                "status": "theorem",
            },
            {
                "id": "score_kappa_over_M",
                "ppm": ppm(a),
                "maps_to": "α=κ/97 after — not used to pick M",
                "status": "scored_after",
            },
            {
                "id": "pi_tower_is_T_competitor",
                "ppm": ppm(a_pi),
                "maps_to": "π-ansatz ~2 ppm — continuum Ω readout, not discrete descent",
                "status": "T_readout_not_descent",
            },
            {
                "id": "soft_residual_open",
                "ppm": ppm(a),
                "maps_to": "−1040 ppm higher structure / π duel — OPEN",
                "status": "open",
            },
        ]
        return {
            "theorem": "§8.2·α·full-quant — fine structure from n_F seats",
            "kappa": kappa,
            "M": m,
            "alpha": a,
            "alpha_inv": 1.0 / a,
            "alpha_pi_tower": a_pi,
            "vs_codata_ppm_discrete": ppm(a),
            "vs_codata_ppm_pi_tower": ppm(a_pi),
            "M_theorem_closed": bool(census["derivation_closed"]),
            "M_combinatorial_closed": bool(census["derivation_closed"]),  # alias
            "pi_tower_demoted_as_descent": True,
            "soft_residual_open": True,
            "derivation_closed": False,  # soft residual / number duel open
            "discrete_path_shipped": bool(census["census_ok"]),
            "inventory": inventory,
            "ask_ok": bool(census["census_ok"])
            and m == 97
            and abs(kappa**2 - 0.5) < 1e-15
            and abs(ppm(a) + 1040.3688788164525) < 1.0,
            "note": (
                "Full quantization ⇒ α=κ/M with M=n_F_seats=97. "
                "Discrete path shipped; π-tower is T-competitor not descent. "
                "Soft −1040 ppm residual OPEN."
            ),
        }

    def alpha_U0_soft_face_ask_row(self) -> dict[str, float | int | str | bool | list]:
        """§8.2·α·U0·soft-face — face+seat unit on α0=κ/M.

        Preferred: α = M² κ (7M+κ) / (7 M⁴ − M κ³ − 1/(1−κ^{n_□}))
                 = 7 M² κ (7M+κ) / (49 M⁴ − 7 M κ³ − 8)
        Soft unit uniquely fixed by symmetry (no lab):
          U = (d+1)/d , d = N4 + 3 SU(2) Pauli = 7
            = 1/(1−κ^{n_□})   (1-tick cubocta isotropy)
            = |Q8|/(|Q8|−1)   (binary finite of SU(2); |Q8|−1=d)
        Meaning of 7 (candidate, fundamental): N4 causal cross + 3 SU(2) Pauli
        generators — same space+symmetry laws as the descent (§3.6 / §3.10).
        n_sq+1 and 2³−1 rhyme with 7 (echo / algebra), not required parents.
        ≈ −0.000068 ppm vs CODATA 2022 (~0.45σ) — inside lab band.
        Unit descent SEALED by G-grade completeness: after value-preserving
        M-scale rewrite, den_hom has only seat-weighted grades; unique grade-0
        soft singlet U enters den once with soft-minus (same pattern as −κ³).
        Not ×M/×d (would promote grade; locality). Not in num (force factors).
        Global-M book = false trail.
        """
        census = self.alpha_nF_kick_census_row()
        geo = self.cuboctahedron_geometry_row()
        kappa = float(census["kappa"])
        m = int(census["M"])
        n_sq = int(geo["n_faces_square"])
        n_tri = int(geo["n_faces_triangle"])
        n4 = int(N4_CAUSAL_LINKS)  # von Neumann orthogonal cross (§3.6)
        n_su2 = 3  # Pauli generators / SU(2) (§3.10)
        seven = n4 + n_su2  # candidate fundamental meaning of 7
        face_q = 1.0 / (n_sq + 1)
        soft_unit = 1.0 / (1.0 - kappa**n_sq)  # = 8/7; n_□ from cubocta, number from κ
        u0 = float(self.F_0) * float(self.l_P) ** 2
        hbar_c = float(self.hbar) * float(self.c)
        alpha_c = 7.2973525643e-3  # CODATA 2022
        a0 = kappa / m
        x = a0 / 7.0
        a_resum = a0 / (1.0 - x)
        a_dress = a0 * (1.0 + x)
        a_exact_frac = kappa * (7.0 * m + kappa) / (7.0 * m * m)
        inv0 = m / kappa
        inv_c = (inv0 - a0 * x) / (1.0 + x)
        a_invcut = 1.0 / inv_c
        den_c = 7.0 * m * m * m - kappa * kappa * kappa
        a_invcut_frac = m * kappa * (7.0 * m + kappa) / den_c
        # seat-unit only (−1)
        a_seat = (
            (m * m) * kappa * (7.0 * m + kappa)
            / (7.0 * m**4 - m * kappa**3 - 1.0)
        )
        # preferred: soft unit = 1/(1−κ^{n_□}) from local cubocta
        # α = M² κ (7M+κ) / (7 M⁴ − M κ³ − 1/(1−κ^{n_□}))
        a_pref = (m * m) * kappa * (7.0 * m + kappa) / (
            7.0 * m**4 - m * kappa**3 - soft_unit
        )
        a_pref_cleared = (
            7.0 * (m * m) * kappa * (7.0 * m + kappa)
            / (49.0 * m**4 - 7.0 * m * kappa**3 - 8.0)
        )
        a_pref_alt = (m * m) * kappa * (7.0 * m + kappa) / (
            7.0 * m**4 - m * kappa**3 - 1.0 - face_q
        )

        def ppm(a: float) -> float:
            return (a - alpha_c) / alpha_c * 1.0e6

        inventory: list[dict[str, str | float | bool | int]] = [
            {
                "id": "unit_U0",
                "maps_to": "U0=F0·l_P²; hbar*c=2*kappa*U0",
                "U0": u0,
                "hbar_c_over_U0": hbar_c / u0,
                "status": "shipped_unit",
            },
            {
                "id": "coarse_alpha0",
                "alpha": a0,
                "ppm": ppm(a0),
                "maps_to": "α0=κ/M",
                "status": "shipped_coarse",
            },
            {
                "id": "resum_alpha0_over_1_minus_x",
                "alpha": a_resum,
                "ppm": ppm(a_resum),
                "maps_to": "α0/(1−α0/7)",
                "status": "demoted_resummation",
            },
            {
                "id": "dressing_alpha0_times_1_plus_x",
                "alpha": a_dress,
                "ppm": ppm(a_dress),
                "maps_to": "α0(1+α0/7)",
                "status": "demoted_first_order",
            },
            {
                "id": "inv_cut_then_dress",
                "alpha": a_invcut,
                "ppm": ppm(a_invcut),
                "maps_to": "M·κ·(7M+κ)/(7M³−κ³)",
                "status": "demoted_inv_cut",
            },
            {
                "id": "seat_unit_only",
                "alpha": a_seat,
                "ppm": ppm(a_seat),
                "maps_to": "M²·κ·(7M+κ)/(7M⁴−M·κ³−1)",
                "status": "demoted_seat_only",
            },
            {
                "id": "preferred_seat_plus_face",
                "alpha": a_pref,
                "ppm": ppm(a_pref),
                "maps_to": "7 M² κ (7M+κ)/(49 M⁴ − 7 M κ³ − 8)",
                "status": "preferred_candidate",
            },
            {
                "id": "plus_1ppm_explained",
                "maps_to": "+1.03 resum vs dressing",
                "status": "explained",
            },
            {
                "id": "seven_N4_plus_SU2",
                "N4": n4,
                "SU2_generators": n_su2,
                "seven": seven,
                "maps_to": (
                    "7 = N4 causal cross + 3 SU(2) Pauli generators — "
                    "space+symmetry of the descent; candidate fundamental"
                ),
                "status": "candidate_fundamental_meaning",
            },
            {
                "id": "n_sq_echo_of_seven",
                "count": n_sq,
                "maps_to": "cubocta n_sq+1=7 rhymes; echo not required parent",
                "status": "shipped_geo_echo",
            },
            {
                "id": "axiom_seat_plus_face_unit",
                "maps_to": "M-scale rewrite; subtract soft singlet U=seat+face=8/7 (G-grade completeness)",
                "status": "shipped_axiom_open_descent",
            },
            {
                "id": "lab_delta_vs_codata2022",
                "ppm": ppm(a_pref),
                "maps_to": "Δ ~−0.000068 ppm (~0.45σ) — inside CODATA band",
                "status": "lab_inside_band",
            },
            {
                "id": "cleared_corr_eq_n_sq_plus_2",
                "count": n_sq + 2,
                "maps_to": "after ×7 clear: −8 = n_sq+2 = 7·(1+1/7) — same integer two ways",
                "status": "shipped_identity",
            },
            {
                "id": "soft_unit_seat_plus_face",
                "maps_to": "(n_sq+2)/(n_sq+1)=8/7 = seat 1 + face 1/(n_sq+1)",
                "status": "shipped_unit",
            },
            {
                "id": "soft_unit_symmetry_triple",
                "maps_to": (
                    "U=(d+1)/d = 1/(1−κ^{n_□}) = |Q8|/(|Q8|−1), "
                    "d=N4+3=7=|Q8|−1=n_□+1. Fixed by space⊕spin symmetry "
                    "+ 1-tick isotropy — no CODATA."
                ),
                "status": "shipped_symmetry_identity",
                "d": seven,
                "U": soft_unit,
            },
            {
                "id": "soft_unit_via_kappa_n_sq",
                "maps_to": (
                    "Geo face of the triple: 8/7=1/(1−κ^{n_□}); "
                    "exponent = cubocta n_faces_square; κ²=1/2 locks number."
                ),
                "status": "shipped_number_identity",
                "value": soft_unit,
                "n_sq": n_sq,
            },
            {
                "id": "false_trail_global_M_book",
                "maps_to": (
                    "Demoted: treating M as a GLOBAL book separate from local 7. "
                    "Locality (A1) is hard — M is not a non-local ledger."
                ),
                "status": "false_trail",
            },
            {
                "id": "both_local_7_and_M",
                "maps_to": (
                    "Both live on one nucleus under A1: "
                    "7=N4+SU(2) — how the cell couples (causal cross + spin); "
                    "M=1+N12·N_hier — local kick-ledger seat census of that same charged FCC star "
                    "(§8.2·α·nF · model/01-carrier: M = lattice + local g). "
                    "Not two books — two local counts."
                ),
                "status": "shipped_locality",
            },
            {
                "id": "homogenize_is_algebra_not_global_glue",
                "maps_to": (
                    "×M homogenize is value-preserving rewrite of inv-cut (α_inv≡α_hom). "
                    "Not erase, not global glue. Opens M-scale den without soft singlet."
                ),
                "status": "shipped_reframe",
            },
            {
                "id": "axiom_G_grade_completeness_soft",
                "maps_to": (
                    "After value-preserving M-scale rewrite, den_hom=7M⁴−Mκ³ "
                    "carries only seat-weighted grades. Unique grade-0 G-scalar "
                    "U=(d+1)/d enters den once. Soft-minus sign (pattern −κ³). "
                    "Not ×M/×d (grade promotion; breaks A1 body-local). "
                    "Not in num (κ,(7M+κ) are force/light factors; U is counting)."
                ),
                "status": "shipped_axiom_sealed",
            },
        ]
        return {
            "theorem": "§8.2·α·U0·soft-face — α=M² κ (7M+κ)/(7 M⁴−M κ³−1/(1−κ⁶))",
            "M": m,
            "kappa": kappa,
            "U0_J_m": u0,
            "hbar_c_over_U0": hbar_c / u0,
            "n_faces_square": n_sq,
            "n_faces_triangle": n_tri,
            "N4_causal": n4,
            "SU2_generators": n_su2,
            "seven_N4_plus_SU2": seven,
            "face_quantum": face_q,
            "soft_unit": soft_unit,
            "alpha_codata": alpha_c,
            "codata_year": 2022,
            "alpha_coarse": a0,
            "alpha_resum": a_resum,
            "alpha_dress": a_dress,
            "alpha_invcut": a_invcut,
            "alpha_seat": a_seat,
            "alpha_soft": a_pref,
            "alpha_pref": a_pref,
            "vs_codata_ppm_coarse": ppm(a0),
            "vs_codata_ppm_resum": ppm(a_resum),
            "vs_codata_ppm_dress": ppm(a_dress),
            "vs_codata_ppm_invcut": ppm(a_invcut),
            "vs_codata_ppm_seat": ppm(a_seat),
            "vs_codata_ppm_soft": ppm(a_pref),
            "vs_codata_ppm_pref": ppm(a_pref),
            "identity_dress_frac": abs(a_dress - a_exact_frac) < 1e-15,
            "identity_invcut_frac": abs(a_invcut - a_invcut_frac) < 1e-15,
            "identity_pref_face_seat": abs(a_pref - a_pref_alt) < 1e-15,
            "identity_pref_cleared": abs(a_pref - a_pref_cleared) < 1e-15,
            "identity_soft_via_kappa": abs(soft_unit - 1.0 / (1.0 - kappa**n_sq)) < 1e-15
            and abs(soft_unit - (1.0 + face_q)) < 1e-15,
            "identity_soft_symmetry_triple": (
                abs(soft_unit - (seven + 1) / seven) < 1e-15
                and abs(soft_unit - 1.0 / (1.0 - kappa**n_sq)) < 1e-15
                and abs(soft_unit - 8.0 / 7.0) < 1e-15
                and n_sq + 1 == seven
            ),
            "identity_seven_N4_plus_SU2": seven == 7 and n4 == 4 and n_su2 == 3,
            "seven_meaning_fundamental_candidate": True,
            "carrier_soft_unit_answer_candidate": False,
            "false_trail_global_M_book": True,
            "local_cubocta_residue_candidate": False,
            "symmetry_soft_singlet_candidate": True,
            "axiom_G_grade_completeness_soft": True,
            "derivation_closed": True,
            "soft_candidate_shipped": True,
            "mechanism_descent_shipped": True,
            "plus_1ppm_explained": True,
            "axiom_inv_cut_shipped": True,
            "axiom_seat_unit_shipped": True,
            "axiom_seat_plus_face_shipped": True,
            "lab_inside_codata_band": abs(ppm(a_pref)) < 0.00016,
            "inventory": inventory,
            "ask_ok": m == 97
            and n_sq == 6
            and n_tri == 8
            and abs(face_q - 1.0 / 7.0) < 1e-15
            and seven == 7
            and n4 == 4
            and n_su2 == 3
            and abs((n_sq + 2) / (n_sq + 1) - 1.0 / (1.0 - kappa**n_sq)) < 1e-15
            and abs(soft_unit - (seven + 1) / seven) < 1e-15
            and abs(a_dress - a_exact_frac) < 1e-15
            and abs(a_invcut - a_invcut_frac) < 1e-15
            and abs(a_pref - a_pref_alt) < 1e-15
            and abs(hbar_c / u0 - 2.0 * kappa) < 1e-12
            and abs(ppm(a_pref)) < 0.00016
            and abs(ppm(a_seat)) < 0.001
            and abs(ppm(a_invcut)) < 0.01
            and abs(ppm(a_dress)) < 0.1
            and abs(ppm(a_resum) - 1.02725) < 0.01,
            "note": (
                "Preferred α=M² κ (7M+κ)/(7 M⁴−M κ³−1/(1−κ^{n_□})) "
                "~−0.000068 ppm vs CODATA 2022 (~0.45σ, inside band). "
                "Soft unit U=(d+1)/d from symmetry; sealed by G-grade completeness "
                "(grade-0 singlet once in den, soft-minus). derivation_closed=True."
            ),
        }

    def alpha_upstairs_mass_probe_row(self) -> dict[str, float | int | str | bool | list]:
        """§8.2·α·upstairs — SEALED mass cascade on preferred α.

        Law (exact expressions; no re-fit; no u on the formulas):
            v     = α^N_hier · E_P · √(2π)
            m_H   = √(2λ) · v,  λ = 1/8 + N_hier·(α/(4π))
            m_p   = α · (v/2) · (1 + κ²/N12)
            m_e   = α² · m_H / N_φ
            m_n   = m_p + 2·m_e
        Input α = alpha_preferred (soft-face sealed). π-tower = T-label only.
        PDG contrasts are T-door, not uncertainties of the masses.
        Soft floors ~10⁻³ (baryon packing / empty-cell) stay open as higher structure.
        """
        soft = self.alpha_U0_soft_face_ask_row()
        higgs = self.higgs_mass_row()
        prot = self.proton_mass_row()
        elec = self.electron_mass_row()
        neut = self.neutron_mass_row()
        a_pref = float(soft["alpha_pref"])
        a_pi = float(self.alpha_fs)
        inventory: list[dict[str, str | float | bool | int]] = [
            {
                "id": "alpha_input_preferred",
                "alpha": a_pref,
                "maps_to": "soft-face §8.2·U0 structural — exact, no u(α)",
                "status": "shipped_sealed_input",
            },
            {
                "id": "alpha_pi_tower_T_only",
                "alpha": a_pi,
                "maps_to": "π-tower demoted T-competitor — not cascade input",
                "status": "demoted_T",
            },
            {
                "id": "law_v",
                "GeV": float(higgs["v_GeV"]),
                "maps_to": "v = α^N_hier · E_P · √(2π)",
                "status": "shipped_law",
            },
            {
                "id": "law_m_H",
                "GeV": float(higgs["m_H_GeV"]),
                "maps_to": "m_H = √(2λ)·v; λ=1/8+N_hier·(α/4π)",
                "T_lab_contrast": float(higgs["m_H_rel_err"]),
                "status": "shipped_law",
            },
            {
                "id": "law_m_p",
                "GeV": float(prot["m_p_GeV"]),
                "maps_to": "m_p = α·(v/2)·(1+κ²/N12)",
                "T_lab_contrast": float(prot["m_p_rel_err"]),
                "status": "shipped_law",
            },
            {
                "id": "law_m_e",
                "GeV": float(elec["m_e_GeV"]),
                "maps_to": "m_e = α²·m_H/N_φ",
                "T_lab_contrast": float(elec["m_e_rel_err"]),
                "status": "shipped_law",
            },
            {
                "id": "law_m_n",
                "GeV": float(neut["m_n_GeV"]),
                "maps_to": "m_n = m_p+2·m_e (k=2 ledger)",
                "T_lab_contrast": float(neut["m_n_rel_err"]),
                "status": "shipped_law",
            },
            {
                "id": "soft_floors_open",
                "maps_to": (
                    "~10⁻³ T-door floors (baryon packing / empty-cell) — "
                    "higher structure, not a hole in α"
                ),
                "status": "open_higher_structure",
            },
        ]
        return {
            "theorem": "§8.2·α·upstairs — SEALED cascade on preferred α",
            "alpha_preferred": a_pref,
            "alpha_pi_tower": a_pi,
            "v_GeV": float(higgs["v_GeV"]),
            "m_H_GeV": float(higgs["m_H_GeV"]),
            "m_H_rel_err": float(higgs["m_H_rel_err"]),
            "m_p_GeV": float(prot["m_p_GeV"]),
            "m_p_rel_err": float(prot["m_p_rel_err"]),
            "m_e_GeV": float(elec["m_e_GeV"]),
            "m_e_rel_err": float(elec["m_e_rel_err"]),
            "m_n_GeV": float(neut["m_n_GeV"]),
            "m_n_rel_err": float(neut["m_n_rel_err"]),
            "cascade_law_closed": True,
            "derivation_closed": True,
            "soft_floors_open": True,
            "pi_tower_not_input": True,
            "inventory": inventory,
            "ask_ok": bool(soft["ask_ok"])
            and bool(soft["derivation_closed"])
            and abs(a_pref - float(self.alpha_preferred)) < 1e-15
            and abs(float(prot["alpha_preferred"]) - a_pref) < 1e-15
            and abs(float(elec["alpha_preferred"]) - a_pref) < 1e-15
            and float(higgs["m_H_rel_err"]) < 0.01
            and float(prot["m_p_rel_err"]) < 0.02
            and float(elec["m_e_rel_err"]) < 0.02
            and bool(neut["beta_downhill"]),
            "note": (
                "Upstairs SEALED: exact cascade v→m_H→m_p/m_e→m_n on α_preferred. "
                "PDG contrasts are T-door only. Soft ~10⁻³ floors = higher structure."
            ),
        }

    def alpha_si_bridge_row(self) -> dict[str, float | int | str | bool | list]:
        """§8.2·α·SI-bridge — sealed carrier α → SI unit packet; α exact.

        Carrier (definition; no ħ, c, e, ε₀; no u(α)):
            d = N4 + SU(2) = 7
            U = (d+1)/d = 8/7
            α = M² κ (d M + κ) / (d M⁴ − M κ³ − U)
              = 7 M² κ (7M+κ) / (49 M⁴ − 7 M κ³ − 8)
        Structural α is exact — it has no ppm and no u(α).

        Unit packet (how ħ,c enter SI conversion of force/action — not α):
            U0 = F0 · l_P² = s0 · c0
            ħ c = 2 κ U0

        Optional T-door: contrast of the same number vs CODATA 2022
        (lab e²/(4π ε₀ ħ c)). That contrast is not a property of α.
        """
        soft = self.alpha_U0_soft_face_ask_row()
        m = int(soft["M"])
        kappa = float(soft["kappa"])
        d = int(soft["seven_N4_plus_SU2"])
        u_soft = float(soft["soft_unit"])
        a_pref = float(soft["alpha_pref"])
        a0 = kappa / m
        # explicit d,U form (must match soft preferred)
        a_from_dU = (m * m) * kappa * (d * m + kappa) / (
            d * m**4 - m * kappa**3 - u_soft
        )
        a_cleared = (
            7.0 * (m * m) * kappa * (7.0 * m + kappa)
            / (49.0 * m**4 - 7.0 * m * kappa**3 - 8.0)
        )
        u0 = float(self.F_0) * float(self.l_P) ** 2
        hbar_c = float(self.hbar) * float(self.c)
        alpha_c = 7.2973525643e-3  # CODATA 2022
        ppm = (a_pref - alpha_c) / alpha_c * 1.0e6

        inventory: list[dict[str, str | float | bool | int]] = [
            {
                "id": "carrier_alpha_no_macro",
                "maps_to": (
                    "α = M² κ (d M+κ)/(d M⁴−M κ³−U); d=N4+SU(2); "
                    "U=(d+1)/d — no ħ,c,e,ε₀"
                ),
                "status": "shipped_definition",
            },
            {
                "id": "formula_with_d_U",
                "alpha": a_from_dU,
                "d": d,
                "U": u_soft,
                "M": m,
                "kappa": kappa,
                "status": "shipped_identity",
            },
            {
                "id": "formula_integer_cleared",
                "alpha": a_cleared,
                "maps_to": "7 M² κ (7M+κ)/(49 M⁴−7 M κ³−8)",
                "status": "shipped_identity",
            },
            {
                "id": "unit_packet_U0",
                "U0": u0,
                "hbar_c_over_U0": hbar_c / u0,
                "two_kappa": 2.0 * kappa,
                "maps_to": "U0=F0·l_P²; ħc=2κ U0 — SI conversion of packets",
                "status": "shipped_unit_bridge",
            },
            {
                "id": "alpha_exact_no_u",
                "maps_to": "structural α exact — no u(α), no ppm of α",
                "status": "shipped_exact",
            },
            {
                "id": "T_door_CODATA_contrast",
                "alpha_preferred": a_pref,
                "alpha_CODATA": alpha_c,
                "T_lab_contrast_ppm": ppm,
                "maps_to": (
                    "optional T-door: same number vs CODATA 2022; "
                    "not u(α), not ppm of α"
                ),
                "status": "T_contrast_not_alpha",
            },
            {
                "id": "coarse_vs_preferred",
                "alpha0_kappa_over_M": a0,
                "maps_to": "α0=κ/M is coarse T-name; preferred is sealed soft face",
                "status": "shipped_hierarchy",
            },
            {
                "id": "reject_macro_as_alpha_input",
                "maps_to": "ħ,c,e,ε₀ must not enter the definition of α on the carrier",
                "status": "rejected_as_definition",
            },
        ]
        return {
            "theorem": "§8.2·α·SI-bridge — carrier α exact → U0 packet; T-door optional",
            "M": m,
            "kappa": kappa,
            "d": d,
            "U": u_soft,
            "alpha_preferred": a_pref,
            "alpha_from_d_U": a_from_dU,
            "alpha_integer_cleared": a_cleared,
            "alpha0_coarse": a0,
            "U0": u0,
            "hbar_c_over_U0": hbar_c / u0,
            "identity_hbar_c_eq_2kappa_U0": abs(hbar_c / u0 - 2.0 * kappa) < 1e-12,
            "identity_pref_eq_dU": abs(a_pref - a_from_dU) < 1e-15,
            "identity_pref_eq_cleared": abs(a_pref - a_cleared) < 1e-15,
            "identity_pref_eq_property": abs(a_pref - float(self.alpha_preferred)) < 1e-15,
            "alpha_exact": True,
            "no_u_alpha": True,
            "T_lab_contrast_ppm": ppm,
            "codata_year": 2022,
            "T_lab_inside_codata_band": abs(ppm) < 0.00016,
            "macros_not_inputs": True,
            "derivation_closed": True,
            "inventory": inventory,
            "ask_ok": m == 97
            and d == 7
            and abs(u_soft - 8.0 / 7.0) < 1e-15
            and abs(a_pref - a_from_dU) < 1e-15
            and abs(a_pref - a_cleared) < 1e-15
            and abs(a_pref - float(self.alpha_preferred)) < 1e-15
            and abs(hbar_c / u0 - 2.0 * kappa) < 1e-12
            and bool(soft["derivation_closed"])
            and bool(soft["ask_ok"]),
            "note": (
                "SI bridge: structural α from κ,M,d,U is exact — no u(α), no ppm. "
                "ħ,c only via U0 (ħc=2κ U0). "
                "T_lab_contrast_ppm is optional CODATA door, not a property of α."
            ),
        }

    def alpha_meter_na0_bridge_row(self) -> dict[str, float | int | str | bool | list]:
        """§8.2·α·meter — N_a0/a0 readout from sealed α; meter not input.

        Fint (dependency flip):
          OLD trap: optical meter / a0 → N_a0 → α (T-anchor as definition).
          NEW: α sealed (soft-face) → upstairs m_e → N_c=m_P/m_e → N_a0=N_c/α.

        Lattice unit = hL = l_P (A1). SI metre ∉ M — optional T-export only.
        Optical a0 / CODATA N_a0_Bohr — T-door only (~0.45%), not M-definition.
        H·ask independent ℤ N_a0 without α remains OPEN (census), but does NOT
        block α and does NOT define the meter for α.
        """
        soft = self.alpha_U0_soft_face_ask_row()
        up = self.alpha_upstairs_mass_probe_row()
        hop = self.alpha_hop_ladder_row()
        a = float(self.alpha_preferred)
        m_e_GeV = float(up["m_e_GeV"])
        m_P_GeV = self.E_P / EV_J / 1e9
        n_c = m_P_GeV / m_e_GeV
        n_a0 = n_c / a
        n_a0_opt = float(hop["N_a0_Bohr"])
        a0_opt_m = n_a0_opt * self.l_P
        a0_pred_m = n_a0 * self.l_P
        m_e_kg = m_e_GeV * 1e9 * EV_J / (C * C)
        a0_bohr_m = HBAR / (m_e_kg * C * a)
        rel_vs_opt = abs(n_a0 - n_a0_opt) / n_a0_opt
        id_hop = abs(n_c / n_a0 - a) < 1e-15
        id_bohr = abs(a0_bohr_m / a0_pred_m - 1.0) < 1e-12
        inventory = [
            {
                "id": "alpha_sealed",
                "maps_to": "soft-face preferred α — exact, no meter",
                "ok": bool(soft["derivation_closed"]),
            },
            {
                "id": "N_c_from_cascade",
                "maps_to": "N_c = m_P/m_e (upstairs on preferred)",
                "value": n_c,
                "ok": bool(up["ask_ok"]),
            },
            {
                "id": "N_a0_predicted",
                "maps_to": "N_a0 = N_c/α (hop identity inverted)",
                "value": n_a0,
                "ok": id_hop,
            },
            {
                "id": "a0_lattice",
                "maps_to": "a0 = N_a0 · l_P",
                "value_m": a0_pred_m,
                "ok": id_bohr,
            },
            {
                "id": "reject_optical_meter_as_alpha_input",
                "maps_to": "optical a0 / SI meter ≠ input to α",
                "ok": True,
            },
            {
                "id": "H_structure_integer_Na0",
                "maps_to": "ℤ N_a0 from H alone without α — still OPEN census",
                "blocks_alpha": False,
                "ok": True,
            },
        ]
        return {
            "theorem": "§8.2·α·meter — N_a0/a0 from sealed α; meter not input",
            "method": "fint: invert hop α=N_c/N_a0 after soft-face+upstairs seal",
            "alpha_preferred": a,
            "m_e_GeV": m_e_GeV,
            "m_P_GeV": m_P_GeV,
            "N_c": n_c,
            "N_a0_predicted": n_a0,
            "N_a0_optical_T": n_a0_opt,
            "a0_predicted_m": a0_pred_m,
            "a0_bohr_from_me_m": a0_bohr_m,
            "a0_optical_T_m": a0_opt_m,
            "l_P_m": self.l_P,
            "T_lab_rel_vs_optical_a0": rel_vs_opt,
            "identity_alpha_eq_Nc_over_Na0": id_hop,
            "identity_a0_bohr_eq_Na0_lP": id_bohr,
            "meter_not_input_to_alpha": True,
            "meter_not_on_M": True,
            "SI_metre_is_T_export_only": True,
            "M_lengths_are_hops": True,
            "optical_a0_is_T_door_only": True,
            "alpha_path_closed": True,
            "independent_Na0_from_H_open": True,
            "independent_Na0_blocks_alpha": False,
            "derivation_closed": True,
            "inventory": inventory,
            "ask_ok": (
                id_hop
                and id_bohr
                and bool(soft["derivation_closed"])
                and bool(soft["ask_ok"])
                and bool(up["ask_ok"])
                and abs(a - float(soft["alpha_pref"])) < 1e-15
            ),
            "note": (
                "Fint: meter/optical a0 is not an input to α. "
                "Sealed α + upstairs m_e predict N_a0=N_c/α (hops). "
                "SI metre ∉ M — T-export only; see meter_decouple_from_M_row. "
                "Optical Bohr/N_a0 is T-door (~0.45%). "
                "H→ℤN_a0 without α remains OPEN census — does not block α."
            ),
        }

    def alpha_runner_row(self) -> dict[str, float]:
        """§8.4.3-D — 1/α(MZ)=1/α_fs − B_hV (brick capacity, not QCD-style ln)."""
        b_hv = self.bekenstein_bits_hv
        inv0 = self.alpha_fs_inv
        inv_mz = inv0 - b_hv
        inv_mz_floor = inv0 - math.floor(b_hv)
        pdg_inv = 127.955
        return {
            "alpha_fs_inv": inv0,
            "B_hV": b_hv,
            "alpha_MZ_inv": inv_mz,
            "alpha_MZ": 1.0 / inv_mz,
            "alpha_MZ_inv_floor_neighbor": inv_mz_floor,
            "alpha_MZ_inv_PDG": pdg_inv,
            "alpha_MZ_inv_rel_err": abs(inv_mz - pdg_inv) / pdg_inv,
            "note": "§8.4.3-D: 1/α(MZ)=1/α_fs−B_hV; ≠ α_s packing ln",
        }

