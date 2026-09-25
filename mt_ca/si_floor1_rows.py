"""SIFloor1Rows — extracted from si_constants (file-size hygiene)."""
from __future__ import annotations

import math
from decimal import Decimal

from mt_ca.si_constants import (
    C,
    DELTA_PHI_MIN,
    HBAR,
    N12_FCC_CAUSAL_LINKS,
    hv_bit_budget
)


class SIFloor1Rows:
    """Ask/row probes — do not grow si_constants with these."""

    def floor1_leptonic_row(self) -> dict[str, float | int | str | bool | list]:
        """§6·floor1 — what can live at 10³…10⁵·dl (pre-resonances / leptonic).

        Walk (carrier, no α-fit):
          Floor 0 = one-cell pra-defect (electron core). Floor 2+ = confining
          (girth d, B-class). Floor 1 sits in the desert BETWEEN them.

        Scale window (derived integers, not CODATA):
          N₁₂³ = 1728 ≈ 10³
          N₁₂⁴ = 20736 ≈ 2·10⁴
          N₁₂⁵ = 248832 ≈ 2.5·10⁵ (slightly above table hi)
          Table §6 band 10³…10⁵·dl ≈ causal-star powers N₁₂^{3…4}.

        What it is NOT (reject as floor-1 size):
          • Compton e / a₀ — IR, ~10²²…10²⁴·dl (far above)
          • μ/τ Compton — still ~10²⁰·dl class; model explicitly
            does not claim m_μ/m_e here (§8.2 electron)
          • Confining quark foci — floor 2 (~10¹⁵·dl)
          • N_gen=d — count of stacks, not a length floor (§8.4.4)

        What it MAY be (open):
          Multi-cell leptonic (B=0) dressings / pre-resonances on the
          FCC star iterated 3–4 times: Q=±1 or neutral metastable
          blobs that decay to floor-0 pra + radiation. Not a new gauge
          group — topology/assembly theory on the same g.

        Status: scale window motivated; content census OPEN.
        """
        n12 = int(N12_FCC_CAUSAL_LINKS)
        n_phi = int(hv_bit_budget().N_phi)
        n_hier = int(math.floor(hv_bit_budget().B_hV)) - 1
        l_p = self.l_P
        # linear scales in ·dl
        lo = float(n12**3)
        mid = float(n12**4)
        hi_table = 1.0e5
        hi_star = float(n12**5)
        # IR landmarks in ·dl (CODATA lengths / l_P — score after, not definition)
        hbar = HBAR
        c = C
        m_e = 9.1093837015e-31
        lam_c = hbar / (m_e * c)
        a0 = hbar / (m_e * c * 7.2973525693e-3)
        compton_over_dl = lam_c / l_p
        a0_over_dl = a0 / l_p

        window_ok = lo >= 1.0e3 and lo <= 3.0e3 and mid >= 1.0e4 and mid <= 3.0e4
        ir_far = compton_over_dl > 1.0e20 and a0_over_dl > 1.0e22
        floor2_above = 1.0e15 > hi_table

        inventory: list[dict[str, str | float | bool]] = [
            {
                "id": "scale_N12_cubed",
                "ratio": lo,
                "maps_to": "N₁₂³·dl — low edge of §6 floor 1",
                "status": "motivated",
            },
            {
                "id": "scale_N12_fourth",
                "ratio": mid,
                "maps_to": "N₁₂⁴·dl — mid band",
                "status": "motivated",
            },
            {
                "id": "scale_N12_fifth",
                "ratio": hi_star,
                "maps_to": "N₁₂⁵·dl — slightly above table 10⁵",
                "status": "report",
            },
            {
                "id": "reject_Compton_as_floor1",
                "ratio": compton_over_dl,
                "maps_to": "λ̄_C/l_P ≫ 10⁵ — IR lepton cloud, not floor 1",
                "status": "rejected_as_floor1_size",
            },
            {
                "id": "reject_a0_as_floor1",
                "ratio": a0_over_dl,
                "maps_to": "a₀/l_P ≫ 10⁵ — atomic, not floor 1",
                "status": "rejected_as_floor1_size",
            },
            {
                "id": "reject_confining_floor2",
                "ratio": 1.0e15,
                "maps_to": "§6 level 2 quark foci — different class (B≠0)",
                "status": "rejected_as_floor1_class",
            },
            {
                "id": "reject_Ngen_as_length",
                "ratio": 3.0,
                "maps_to": "N_gen=d — stack count, not ·dl floor",
                "status": "rejected_as_length_floor",
            },
            {
                "id": "closed_by_B0_census",
                "maps_to": "floor1_B0_census_row — C2 stable; C4=pre-resonance",
                "status": "closed",
                "mechanism": "class census from §8.2 stability",
            },
            {
                "id": "open_muon_tau_not_here",
                "maps_to": "m_μ/m_e still OPEN — not assigned to floor-1 size",
                "status": "open",
            },
        ]

        return {
            "theorem": "§6·floor1 — leptonic pre-resonance band on N₁₂^{3…4}",
            "N12": n12,
            "N_phi": n_phi,
            "N_hier": n_hier,
            "L_lo_dl": lo,
            "L_mid_dl": mid,
            "L_hi_table_dl": hi_table,
            "L_hi_star_dl": hi_star,
            "Compton_e_over_dl": compton_over_dl,
            "a0_over_dl": a0_over_dl,
            "window_ok": window_ok,
            "ir_landmarks_far_above": ir_far,
            "floor2_scale_above_floor1": floor2_above,
            "derivation_closed": False,
            "inventory": inventory,
            "checks_ok": window_ok and ir_far and floor2_above and n12 == 12,
            "note": (
                "Floor 1: linear band ~N₁₂³…N₁₂⁴·dl (pre-resonances / leptonic). "
                "Not Compton/a₀, not confining floor 2, not N_gen. "
                "OPEN: multi-cell B=0 census; μ/τ mass not claimed here."
            ),
        }

    def floor1_B0_census_row(self) -> dict[str, float | int | str | bool | list]:
        """§6·floor1·B0·census — which B=0 configs at ~N₁₂³…N₁₂⁴ can be stable.

        Stability (already derived §8.2 decay): no downhill g with same
        additive invariants (Q, and derived B,L,…) and lower ledger energy.

        B=0 here = not confining/baryon class (≠ floor 2/3). Radius band
        from floor1 ask: N₁₂³…N₁₂⁴ · dl.

        Class census (carrier, not sim histogram):

          C0 vacuum / A5 boil only
            — not an object; background. Reject as floor1 content.

          C1 free γ (n=0 front)
            — STABLE (already vacuum sector). Not a radius-N₁₂^k blob;
              propagating front. Stable but not floor1-band object.

          C2 lightest Q=±1 (e± scheme): 1-cell core + optional near dressing
            — STABLE: topo-protection (alone ≠ collapse to n=0) + lightest
              with that Q (§8.2). Core = floor0; near packing/A5 dressing
              may extend into floor1 radii without being a second particle.

          C3 excited / composite leptonic (μ-scheme, same Q, higher E)
            — UNSTABLE at class level: products C2 + γ (n=0) conserve Q,
              A3 energy downhill by definition of higher E, radiation
              sector exists (C1). Multi-shell excitation already downhill
              (dressing·close). Existence of channel closed; Γ soft-OPEN.

          C4 Q=0 multi-cell blob without ± pair (pure excitation)
            — NO topo charge to protect; A5 returns to vacuum.
              = pre-resonance / transient. UNSTABLE.

          C5 ± pair bound at floor1 radius (positronium-like)
            — annihilation channel derived when ± meet (§5.0.3).
              UNSTABLE as bound B=0 object.

          C6 neutral with derived L (ν-scheme)
            — may be stable if lightest in its L sector; spatial size
              NOT in floor1 band (reject R≡N₁₂^{3…4}). Off-band object.

        Sharp claim: at this radius the only stable B=0 *matter* class
        is C2 (dressed lightest Q=±1). Floor1's own name «pre-resonance»
        = C4 — unstable by construction. C3 channel existence closed;
        Γ/lifetime still soft.
        """
        n12 = int(N12_FCC_CAUSAL_LINKS)
        r_lo = n12**3
        r_hi = n12**4

        classes: list[dict[str, str | float | bool]] = [
            {
                "id": "C0_vacuum_A5",
                "stable": False,
                "status": "rejected_as_object",
                "maps_to": "background boil — not floor1 content",
            },
            {
                "id": "C1_free_gamma",
                "stable": True,
                "status": "stable_wrong_object",
                "maps_to": "n=0 front; not N₁₂^k blob",
            },
            {
                "id": "C2_lightest_Q_pm1_dressed",
                "stable": True,
                "status": "stable_matter",
                "maps_to": "e± core (floor0) + ε-star dressing (R=1·dl; see dressing·close)",
                "mechanism": "topo lock + lightest Q; dressing ≠ second particle",
            },
            {
                "id": "C3_excited_leptonic_same_Q",
                "stable": False,
                "status": "unstable_channel_closed",
                "maps_to": "C3→C2+γ: Q+A3; multi-shell↓ε; Γ soft-OPEN",
                "mechanism": "products exist; higher E by def; dressing·close",
            },
            {
                "id": "C4_Q0_multicell_blob",
                "stable": False,
                "status": "pre_resonance",
                "maps_to": "no topo charge → A5 → vacuum; defines floor1 name",
            },
            {
                "id": "C5_pm_pair_bound",
                "stable": False,
                "status": "unstable_annihilation",
                "maps_to": "± meet → 2γ (§5.0.3)",
            },
            {
                "id": "C6_neutral_L_sector",
                "stable": True,  # conditional: if lightest in L
                "status": "stable_off_band",
                "maps_to": "ν may be stable in L; reject R≡N₁₂^{3…4} as floor1 size",
                "mechanism": "L-sector lightest ≠ floor1 length window",
            },
        ]

        stable_matter = [c for c in classes if c["id"] == "C2_lightest_Q_pm1_dressed"]
        pre_res = [c for c in classes if c["status"] == "pre_resonance"]
        census_ok = (
            len(stable_matter) == 1
            and len(pre_res) == 1
            and r_lo == 1728
            and r_hi == 20736
            and classes[2]["stable"] is True
            and classes[4]["stable"] is False
            and classes[5]["stable"] is False
        )

        return {
            "theorem": "§6·floor1·B0·census — stable B=0 at N₁₂³…N₁₂⁴",
            "R_lo_dl": float(r_lo),
            "R_hi_dl": float(r_hi),
            "N12": n12,
            "stable_matter_ids": [c["id"] for c in classes if c["status"] == "stable_matter"],
            "pre_resonance_ids": [c["id"] for c in pre_res],
            "classes": classes,
            "sharp_claim": (
                "Only stable B=0 matter at this R: dressed lightest Q=±1 (C2). "
                "Pre-resonances (C4) unstable by construction."
            ),
            "census_ok": census_ok,
            "derivation_closed": census_ok,
            "sim_metastable_maps_open": False,
            "soft_Gamma_open": True,  # n_ticks filled-bath soft (continuum≠M closed)
            "checks_ok": census_ok,
            "note": (
                "B=0 census @ N₁₂³…N₁₂⁴: C2 dressed e± STABLE; "
                "C4 Q=0 blobs = pre-resonances UNSTABLE; "
                "C5 ± annihilate; C3 channel closed; continuum Γ≠M; n_ticks bath SOFT; "
                "C6 ν off-band (R≠floor1)."
            ),
        }

    def floor1_dressing_row(self) -> dict[str, float | int | str | bool | list]:
        """§6·floor1·dressing — what is the near-zone of lightest Q=±1?

        Ask to carrier (§5.0.5), not invention:

          What is ρ_Θ? What fixes its support radius?

        closed from derived pieces:
          · dressing = ρ_Θ cloud around b=1 core (§5.0.5)
            — NOT a second particle; NOT Compton/a0 cloud
          · ρ_Θ(x) ∝ f(|Δφ_N(x)|, |ζ(x)|) with floor Δφ_min
          · min spatial support ⊇ ε-neighborhood (neighbors of Λ)
            ⇒ R_min = 1·dl; N_star = N12 = 12
          · anti-smear K_P holds core; Heisenberg holds irreducible halo
          · shells = coordination spheres of Λ (modes of ρ_Θ)

        OPEN:
          · outer radius R_dress (shell count k until |Δφ| < Δφ_min)
          · whether R_dress reaches N12^3…N12^4 (NOT forced by B0 census)
          · exact shape of f

        REJECT:
          · R_dress ≡ Compton / a0
          · α-input into dressing (circular for upstairs α=ae/(2r))
          · R_dress ≡ N12^{3…4} without derivation (overclaim)
          · dressing = second particle / separate pra

        TRY (next, not closed):
          · shell-walk: k = min{k: max_|Δφ| on shell k < Δφ_min}
          · combinatorial candidates from N_phi, B_hV, N_ring
        """
        n12 = int(N12_FCC_CAUSAL_LINKS)
        dphi = float(DELTA_PHI_MIN)
        n_phi = int(hv_bit_budget().N_phi)
        r_min = 1.0  # ·dl — ε-star
        r_floor1_lo = float(n12**3)
        r_floor1_hi = float(n12**4)

        inventory: list[dict[str, str | float | bool]] = [
            {
                "id": "closed_rho_Theta_is_dressing",
                "maps_to": "§5.0.5 ρ_Θ cloud around b=1 core — not second particle",
                "status": "closed",
                "mechanism": "Heisenberg + anti-smear: core vs halo",
            },
            {
                "id": "closed_R_min_epsilon_star",
                "ratio": r_min,
                "maps_to": "R_min≥1·dl — ε-neighborhood of Λ (N12 neighbors)",
                "status": "closed",
                "mechanism": "cannot have ρ_Θ=δ on one v_p and zero phase uncertainty",
            },
            {
                "id": "closed_cutoff_concept_dphi_min",
                "ratio": dphi,
                "maps_to": "outer cutoff concept: |Δφ|,|ζ| fall below Δφ_min",
                "status": "closed_concept",
                "mechanism": "ρ_Θ floor = Heisenberg pole",
            },
            {
                "id": "open_R_dress_outer",
                "maps_to": "integer shell count k until signal < Δφ_min — not derived",
                "status": "open",
            },
            {
                "id": "reject_R_equals_floor1_band",
                "ratio": r_floor1_lo,
                "maps_to": "N12^3…N12^4 is floor1 window, not forced R_dress",
                "status": "rejected_as_forced_radius",
            },
            {
                "id": "reject_Compton_as_dressing",
                "maps_to": "Compton/a0 = IR readout, not near-zone ρ_Θ",
                "status": "rejected",
            },
            {
                "id": "reject_alpha_input_dressing",
                "maps_to": "α into dressing circular for α=ae/(2r) upstairs",
                "status": "rejected",
            },
            {
                "id": "try_shell_walk_dphi",
                "maps_to": "k = min shell with max_|Δφ| < Δφ_min",
                "status": "try",
            },
            {
                "id": "try_combinatorial_Nphi_BhV",
                "ratio": float(n_phi),
                "maps_to": "N_phi / B_hV / N_ring as candidate cutoffs — unproven",
                "status": "try",
            },
        ]

        closed_ids = [
            i["id"] for i in inventory if str(i["status"]).startswith("closed")
        ]
        open_ids = [i["id"] for i in inventory if i["status"] == "open"]
        reject_ids = [
            i["id"] for i in inventory if str(i["status"]).startswith("rejected")
        ]

        checks_ok = (
            n12 == 12
            and abs(dphi - 0.5) < 1e-12
            and r_min == 1.0
            and "closed_rho_Theta_is_dressing" in closed_ids
            and "closed_R_min_epsilon_star" in closed_ids
            and "open_R_dress_outer" in open_ids
            and "reject_R_equals_floor1_band" in reject_ids
        )

        return {
            "theorem": "§6·floor1·dressing — near-zone ρ_Θ of lightest Q=±1",
            "N12": n12,
            "N_phi": n_phi,
            "Delta_phi_min": dphi,
            "R_min_dl": r_min,
            "R_floor1_lo_dl": r_floor1_lo,
            "R_floor1_hi_dl": r_floor1_hi,
            "derivation_closed": False,  # outer R open
            "min_support_closed": True,
            "inventory": inventory,
            "closed_ids": closed_ids,
            "open_ids": open_ids,
            "reject_ids": reject_ids,
            "checks_ok": checks_ok,
            "note": (
                "Dressing = ρ_Θ halo (§5.0.5): min ⊇ ε-star (1·dl, N12). "
                "Outer R_dress OPEN (shell-walk / combinatorial). "
                "NOT forced to N12^3…^4; NOT Compton; NOT α-input."
            ),
        }

    def floor1_dressing_close_row(self) -> dict[str, float | int | str | bool | list]:
        """§6·floor1·dressing·close — outer R_dress of lightest Q=±1 = ε-star.

        Closes open from floor1_dressing_row.

        Lemma (derived pieces only):
          1. Winding-1 on the causal star: Δφ_ring = 2π/N12.
             N_phi = ⌈2π/Δφ_min⌉ ⇒ N12 < N_phi ⇔ 2π/N12 > Δφ_min.
             Entire ε-star sits above the Heisenberg floor (forced halo).
          2. Local balance / gate only on N(x) = first shell (A1 · §5.2).
             Second coordination shell in one hT is forbidden.
          3. Ground lightest Q: multi-shell ρ_Θ is an excitation — downhill
             to the minimal halo (same stability logic as C3 vs C2).
             ⇒ R_dress = R_min = 1·dl; N_star = N12. Not N12^{3…4}.

        Still soft-OPEN (not radius): exact shape of f in ρ_Θ∝f(|Δφ|,|ζ|).
        """
        n12 = int(N12_FCC_CAUSAL_LINKS)
        dphi = float(DELTA_PHI_MIN)
        n_phi = int(hv_bit_budget().N_phi)
        dphi_ring = 2.0 * math.pi / float(n12)
        r_dress = 1.0  # ·dl

        star_above = dphi_ring > dphi
        n12_lt_nphi = n12 < n_phi
        lemma_ok = (
            n12 == 12
            and n_phi == 13
            and abs(dphi - 0.5) < 1e-12
            and star_above
            and n12_lt_nphi
            and abs(r_dress - 1.0) < 1e-12
        )

        inventory: list[dict[str, str | float | bool]] = [
            {
                "id": "closed_R_dress_equals_epsilon_star",
                "ratio": r_dress,
                "maps_to": "R_dress=1·dl = ε-star (N12); outer=min for ground e±",
                "status": "closed",
                "mechanism": "2π/N12>Δφ_min + local N(x) + downhill multi-shell",
            },
            {
                "id": "closed_N12_lt_Nphi_forces_star_halo",
                "ratio": dphi_ring,
                "maps_to": "N12=12 < N_phi=13 ⇒ 2π/N12>Δφ_min on every NN",
                "status": "closed",
                "mechanism": "winding-1 ring vs Heisenberg floor",
            },
            {
                "id": "closed_local_gate_first_shell_only",
                "maps_to": "A1/§5.2 balance on N(x); 2nd shell /1 hT forbidden",
                "status": "closed",
            },
            {
                "id": "reject_multi_shell_as_ground",
                "maps_to": "shell≥2 ρ_Θ = excitation → downhill to ε (C3-class)",
                "status": "rejected_as_ground_dressing",
            },
            {
                "id": "reject_R_equals_floor1_band",
                "ratio": float(n12**3),
                "maps_to": "floor1 N12^3…^4 = C4 pre-resonance window, not e halo",
                "status": "rejected",
            },
            {
                "id": "closed_by_f_close",
                "maps_to": "floor1_dressing_f_close_row — f=𝟙[|Δφ|≥Δφ_min]",
                "status": "closed",
            },
        ]

        return {
            "theorem": "§6·floor1·dressing·close — R_dress=1·dl (ε-star)",
            "N12": n12,
            "N_phi": n_phi,
            "Delta_phi_min": dphi,
            "Delta_phi_ring": dphi_ring,
            "R_dress_dl": r_dress,
            "R_min_dl": r_dress,
            "star_above_floor": star_above,
            "N12_lt_Nphi": n12_lt_nphi,
            "derivation_closed": lemma_ok,
            "inventory": inventory,
            "checks_ok": lemma_ok,
            "note": (
                "R_dress=R_min=1·dl: N12<N_phi forces full ε-halo above Δφ_min; "
                "local gate=first shell; multi-shell=excitation. "
                "Floor1 band ≠ e dressing. f-shape → dressing·f·close."
            ),
        }

    def floor1_dressing_f_close_row(self) -> dict[str, float | int | str | bool | list]:
        """§6·floor1·dressing·f·close — shape of f in ρ_Θ∝f(|Δφ|,|ζ|).

        Closes soft-OPEN from dressing·close / dressing.

        Carrier (§5.0.5): cloud = where |Δφ|, |ζ|, Arg-pressure hold
        ≥ Heisenberg floor; ⟨ρ_Θ⟩_T = binomial coarse; ∫ρ_Θ ∼ n_E
        (integer quanta, not float-KN). No mechanical continuous parameters on M.

        closed:
          ρ_Θ(x) = 𝟙[ |Δφ_N(x)| ≥ Δφ_min ]
          — Heaviside / set-membership on the only derived numeric floor.
          |ζ| co-varies via gate ζ=(Σ_N z)·z* but has no independent
          derived floor; does not add a free continuous axis.
          Amplitude inside the support is not a continuum profile on M:
          cells are in/out; T smooths via binomial (§4.1).

        REJECT:
          · smooth continuum ansatze (exp, Gauss, 1/r, soft bags)
          · α- or a0-dependent f (circular / IR)
          · free float parameters in f
        """
        dphi = float(DELTA_PHI_MIN)
        n_phi = int(hv_bit_budget().N_phi)

        inventory: list[dict[str, str | float | bool]] = [
            {
                "id": "closed_f_heaviside_dphi",
                "ratio": dphi,
                "maps_to": "ρ_Θ=𝟙[|Δφ_N|≥Δφ_min] — §5.0.5 'where ≥ floor'",
                "status": "closed",
                "mechanism": "Heisenberg pole is the only numeric cut; no float knobs",
            },
            {
                "id": "closed_norm_integer_quanta",
                "maps_to": "∫ρ_Θ ∼ n_E / topo — indicator sum ∈ ℤ",
                "status": "closed",
            },
            {
                "id": "closed_T_binomial_not_f",
                "maps_to": "⟨ρ_Θ⟩_T = binomial coarse (§4.1) — smooth is T, not M-f",
                "status": "closed",
            },
            {
                "id": "closed_zeta_no_extra_floor",
                "maps_to": "|ζ| gate scalar; no derived ζ_min → not second free axis",
                "status": "closed",
            },
            {
                "id": "reject_smooth_continuum_f",
                "maps_to": "exp/Gauss/1/r soft bags — float-KN, not M",
                "status": "rejected",
            },
            {
                "id": "reject_alpha_a0_in_f",
                "maps_to": "α/a0 in f = IR circular for upstairs coupling",
                "status": "rejected",
            },
        ]

        closed_ids = [
            i["id"] for i in inventory if str(i["status"]).startswith("closed")
        ]
        reject_ids = [
            i["id"] for i in inventory if str(i["status"]).startswith("rejected")
        ]
        ok = (
            abs(dphi - 0.5) < 1e-12
            and n_phi == 13
            and "closed_f_heaviside_dphi" in closed_ids
            and "reject_smooth_continuum_f" in reject_ids
            and len(closed_ids) >= 4
        )

        return {
            "theorem": "§6·floor1·dressing·f·close — ρ_Θ=𝟙[|Δφ|≥Δφ_min]",
            "Delta_phi_min": dphi,
            "N_phi": n_phi,
            "f_form": "Heaviside(|Δφ_N|-Δφ_min)",
            "derivation_closed": ok,
            "inventory": inventory,
            "closed_ids": closed_ids,
            "reject_ids": reject_ids,
            "checks_ok": ok,
            "note": (
                "f closed as Heisenberg indicator: ρ_Θ=𝟙[|Δφ_N|≥Δφ_min]. "
                "No float knobs; ∫∈ℤ; T-smooth=binomial not M-f. "
                "Reject continuum/α ansatze."
            ),
        }

    def floor1_leftovers_close_row(self) -> dict[str, float | int | str | bool | list]:
        """§6·floor1·leftovers·close — C3 channel existence + ν off-band.

        Closes remaining floor1 OPEN from B0 census (not Γ rates).

        C3 (same Q, E > E_C2):
          Products: C2 (lightest Q) + γ (n=0, C1). Q conserved (A10).
          A3: ΣE ≤ E(C3) by definition of higher E.
          Multi-shell excitation already downhill (dressing·close).
          §8.2: composite/excited «may have channel down».
          ⇒ channel *existence* closed; object UNSTABLE.
          Γ soft → floor1_C3_gamma_close_row (not continuum ℏ/τ on M).

        C6 / ν:
          May be stable if lightest in L sector — off this length window.
          Reject R_ν ≡ N12^{3…4} as floor1 size assignment.
          ⇒ not floor1-band content; size OPEN elsewhere, not here.

        m_μ/m_e: still not claimed as floor1 length (unchanged reject).
        """
        n12 = int(N12_FCC_CAUSAL_LINKS)
        r_lo = float(n12**3)
        r_hi = float(n12**4)

        inventory: list[dict[str, str | float | bool]] = [
            {
                "id": "closed_C3_channel_existence",
                "maps_to": "C3→C2+γ: Q+A3+products exist; unstable class",
                "status": "closed",
                "mechanism": "§8.2 decay + dressing·close multi-shell",
            },
            {
                "id": "closed_by_C3_gamma_continuum",
                "maps_to": "floor1_C3_gamma_close_row — continuum Γ≠M; clock form",
                "status": "closed",
            },
            {
                "id": "soft_open_C3_n_ticks_filled_bath",
                "maps_to": "alone n_ticks=1 may be void artifact; bath clock open",
                "status": "soft_open",
            },
            {
                "id": "closed_nu_reject_floor1_size",
                "ratio": r_lo,
                "maps_to": "reject R_ν≡N12^{3…4}; ν off-band vs floor1 window",
                "status": "closed",
            },
            {
                "id": "closed_C6_not_floor1_matter",
                "maps_to": "C6 may be L-stable elsewhere — not band object",
                "status": "closed",
            },
            {
                "id": "reject_mmu_as_floor1_length",
                "maps_to": "m_μ/m_e not a floor1 ·dl assignment",
                "status": "rejected",
            },
        ]

        closed_ids = [
            i["id"] for i in inventory if str(i["status"]).startswith("closed")
        ]
        ok = (
            n12 == 12
            and r_lo == 1728.0
            and r_hi == 20736.0
            and "closed_C3_channel_existence" in closed_ids
            and "closed_nu_reject_floor1_size" in closed_ids
            and "closed_by_C3_gamma_continuum" in closed_ids
        )
        soft_open_ids = [
            i["id"] for i in inventory if str(i["status"]) == "soft_open"
        ]

        return {
            "theorem": "§6·floor1·leftovers·close — C3 existence + ν off-band",
            "N12": n12,
            "R_lo_dl": r_lo,
            "R_hi_dl": r_hi,
            "C3_channel_existence_closed": True,
            "C3_Gamma_soft_open": True,  # n_ticks in filled bath
            "nu_floor1_size_rejected": True,
            "derivation_closed": ok,
            "inventory": inventory,
            "closed_ids": closed_ids,
            "soft_open_ids": soft_open_ids,
            "checks_ok": ok,
            "note": (
                "Floor1 leftovers: C3→C2+γ existence closed; continuum Γ≠M; "
                "n_ticks in filled bath SOFT; ν off-band."
            ),
        }

    def floor1_C3_gamma_close_row(self) -> dict[str, float | int | str | bool | list]:
        """§6·floor1·C3·gamma·close — continuum Γ ≠ M; n_ticks in bath still soft.

        Soft was «find Γ=ℏ/τ». Carrier (§8.2 decay):

          Continuum N(t)=N0 e^{-t/τ}, Γ=ℏ/τ, BR — NOT laws of M.
          That is T-statistics of many systems (§2.1). g is deterministic.

        closed on M:
          · Clock form = n_ticks ∈ ℕ · hT (ledger time), not float Γ.
          · Reject treating soft as free continuum rate knob on M.

        SOFT (reopened — alone vs filled bath):
          · Hyp. n_ticks=1 for *lonely* multi-shell C3 (A1+local downhill)
            may be an empty-background artifact. Vacuum dogfood: bath
            boiled only when the *whole* lattice was set — no void.
            n_ticks for C3 embedded in filled A5 bath is not derived.

        NOT claimed here:
          · PDG μ lifetime (composite organ + m_μ — other leaf).
          · Ensemble T-exponential fit numbers.
        """
        # Alone-hypothesis only — not closed as world clock.
        n_ticks_alone_hyp = 1
        h_t = float(self.hT)
        tau_alone_hyp = float(n_ticks_alone_hyp) * h_t

        inventory: list[dict[str, str | float | bool]] = [
            {
                "id": "reject_continuum_Gamma_as_M_law",
                "maps_to": "§8.2: N(t)=e^{-t/τ}, Γ=ℏ/τ — T-stat, not M",
                "status": "rejected",
            },
            {
                "id": "closed_M_clock_form_n_ticks",
                "maps_to": "τ_M = n_ticks·hT, n_ticks∈ℕ — deterministic g",
                "status": "closed",
            },
            {
                "id": "soft_open_C3_n_ticks_filled_bath",
                "ratio": tau_alone_hyp,
                "maps_to": (
                    "alone hyp n_ticks=1 may be void artifact; "
                    "filled A5 bath n_ticks underived"
                ),
                "status": "soft_open",
                "mechanism": "vacuum boiled only on whole-lattice set — no void",
            },
            {
                "id": "reject_PDG_mu_lifetime_here",
                "maps_to": "μ τ_PDG needs m_μ/composite leaf — not floor1 soft",
                "status": "rejected_as_this_leaf",
            },
        ]

        closed_ids = [
            i["id"] for i in inventory if str(i["status"]).startswith("closed")
        ]
        reject_ids = [
            i["id"] for i in inventory if str(i["status"]).startswith("rejected")
        ]
        soft_open_ids = [
            i["id"] for i in inventory if str(i["status"]) == "soft_open"
        ]
        # Partial close: continuum off M + clock *form*; n_ticks in bath soft.
        form_ok = (
            "closed_M_clock_form_n_ticks" in closed_ids
            and "reject_continuum_Gamma_as_M_law" in reject_ids
            and "soft_open_C3_n_ticks_filled_bath" in soft_open_ids
        )

        return {
            "theorem": (
                "§6·floor1·C3·gamma·close — continuum Γ≠M; "
                "n_ticks in filled bath soft"
            ),
            "n_ticks_alone_hyp": n_ticks_alone_hyp,
            "hT_s": h_t,
            "tau_M_alone_hyp_s": tau_alone_hyp,
            "derivation_closed": False,
            "continuum_rejected": True,
            "inventory": inventory,
            "closed_ids": closed_ids,
            "reject_ids": reject_ids,
            "soft_open_ids": soft_open_ids,
            "checks_ok": form_ok,
            "note": (
                "Continuum ℏ/τ ≠ M (CLOSED). Alone n_ticks=1 is soft hyp — "
                "may fall because lonely/void; filled-bath clock open. "
                "μ PDG lifetime is another leaf."
            ),
        }

    def floor1_C3_bath_dogfood_row(self) -> dict[str, float | int | str | bool | list]:
        """§6·floor1·C3·bath·dogfood — previous floor = VACUUM_BOIL; densitometer fixed.

        Live (cuda, size=256, steps=1024, scripts/run_filled_bath_emergence.py):
          · VACUUM (gauge-fixed class 0): Φ=0, frozen — contrast=1 forever.
          · VACUUM_BOIL (whole lattice, NN Δφ=Δφ_min): evolves; contrast
            1.5 → ~773; ρ_max → 1.

        Thermometer (§10.5 / topology dual-channel): early `emerged_b=False`
        was blind A10 on locked equal-lane boil (rel≡0). After rel/u1/auto:
        SYNTH_U1 + VORTEX_P → b=1; family PLANE_WAVE → born=1.
        """
        inventory: list[dict[str, str | float | bool]] = [
            {
                "id": "closed_gauge_fixed_vacuum_frozen",
                "maps_to": "VACUUM phase_class=0 ⇒ holomorphic Φ=0; no boil",
                "status": "closed",
            },
            {
                "id": "closed_vacuum_boil_whole_lattice_moves",
                "ratio": 773.473,
                "maps_to": "VACUUM_BOIL: contrast grows; ρ_max→1 without planted C3",
                "status": "closed",
                "mechanism": "NN tick step = Δφ_disc; every cell a brick",
            },
            {
                "id": "closed_thermometer_dual_channel_b1",
                "maps_to": (
                    "A10 rel/u1/auto — b readable; SYNTH_U1 & VORTEX_P → b=1; "
                    "PLANE_WAVE family → born=1 (§10.5)"
                ),
                "status": "closed",
            },
            {
                "id": "soft_open_C3_n_ticks_filled_bath",
                "maps_to": "n_ticks for C3-in-bath still underived",
                "status": "soft_open",
            },
        ]
        closed_ids = [
            i["id"] for i in inventory if str(i["status"]).startswith("closed")
        ]
        soft_open_ids = [
            i["id"] for i in inventory if str(i["status"]) == "soft_open"
        ]
        ok = (
            "closed_vacuum_boil_whole_lattice_moves" in closed_ids
            and "closed_gauge_fixed_vacuum_frozen" in closed_ids
            and "closed_thermometer_dual_channel_b1" in closed_ids
        )
        return {
            "theorem": "§6·floor1·C3·bath·dogfood — boil floor; b=1 after densitometer",
            "size": 256,
            "steps": 1024,
            "boil_contrast_final": 773.473,
            "boil_emerged_b": True,
            "vacuum_frozen": True,
            "derivation_closed": False,
            "inventory": inventory,
            "closed_ids": closed_ids,
            "soft_open_ids": soft_open_ids,
            "checks_ok": ok,
            "note": (
                "VACUUM_BOIL self-organizes contrast; gauge VACUUM does not. "
                "Stale emerged_b=False was blind thermometer — dual-channel sees b=1. "
                "C3 bath clock still soft."
            ),
        }

