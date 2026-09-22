"""SI bridge for M-layer g — computed from CODATA, not fitted.



Natural-unit simulation (|z|² = ρ_E/u_P, hL=hT=1) uses the collapsed form in

``update.vacuum_phase``.  This module is the dimensional derivation anchor.



Notation (§5.1.1 MODEL.md):

  μ_P  — Planck mass density [kg/m³]

  u_P  — Planck energy density [J/m³]  (gate floor; |z|²=1 ↔ ρ_E=u_P)

  K_P  — bulk modulus [Pa]             K_P = μ_P·c² = u_P

"""



from __future__ import annotations



import math

from dataclasses import dataclass



# CODATA 2018 (exact c; ℏ, G conventional)

HBAR = 1.054571817e-34  # J·s

H = 2.0 * math.pi * HBAR  # J·s

G = 6.67430e-11  # m³/(kg·s²)

C = 299_792_458.0  # m/s

LN2 = math.log(2.0)



# N₄ isotropic macro readout: c = κ·c₀ (§1.1 MODEL.md)

KAPPA = 1.0 / math.sqrt(2.0)



# §3.7.2 / §5.0.2 — Heisenberg geometric floor on holonomy Δφ [rad]

DELTA_PHI_MIN = 0.5



# Elementary charge scale for eV reporting

EV_J = 1.602176634e-19



# Higgs mass scale (T-layer anchor, CODATA-ish)

M_HIGGS_GEV = 125.0





@dataclass(frozen=True)

class HvBitBudget:

    """§3.12.6 — information budget of one Planck brick hV (no free parameters)."""



    B_hV: float

    """Bekenstein bit capacity: 2π E_P l_P / (ℏ c ln 2) = 2π/ln 2."""



    N_phi: int

    """Heisenberg phase bins ⌈2π/Δφ_min⌉ = ⌈4π⌉."""



    mod_bits: int

    """Ring exponent: N_ring = 2^mod_bits = 2^⌊B_hV⌋."""



    N_ring: int

    phase_bits: int

    frac_bits: int

    n_states: float

    B_phase: float

    B_amp: float





def hv_bit_budget(*, delta_phi_min: float = DELTA_PHI_MIN) -> HvBitBudget:
    """Derive M-layer register widths from Planck brick only (§3.12.6).

    Chain:
      B_hV = 2π/ln2  →  N_ring = 2^⌊B_hV⌋
      Δφ_min = s₀/ℏ = ½ rad  →  N_φ = ⌈2π/Δφ_min⌉ = ⌈4π⌉
      frac_bits = ⌈log₂(N_ring / N_φ)⌉  — amplitude resolution inside phase topology
    """
    b_hv = 2.0 * math.pi / LN2
    n_phi = int(math.ceil(2.0 * math.pi / delta_phi_min))
    mod_bits = int(math.floor(b_hv))
    n_ring = 1 << mod_bits
    frac_bits = max(4, int(math.ceil(math.log2(n_ring / n_phi))))
    b_phase = math.log2(n_phi)
    return HvBitBudget(
        B_hV=b_hv,
        N_phi=n_phi,
        mod_bits=mod_bits,
        N_ring=n_ring,
        phase_bits=mod_bits,
        frac_bits=frac_bits,
        n_states=2.0**b_hv,
        B_phase=b_phase,
        B_amp=float(frac_bits),
    )


def bekenshtein_fractional_part() -> float:
    """{B_hV} = B_hV − ⌊B_hV⌋ — unused Bekenstein fraction of one hV brick (§3.12.6)."""
    b_hv = 2.0 * math.pi / LN2
    return b_hv - math.floor(b_hv)


# von Neumann causal star on d=2 square MVP (§3.6, §5.2.2)
N4_CAUSAL_LINKS = 4
# Hex / FCC candidates from packing (§1.4 · §1.6)
N6_CAUSAL_LINKS = 6
N12_FCC_CAUSAL_LINKS = 12
KAPPA_HEX = math.sqrt(3.0) / 2.0  # inscribed circle in 2D causal hexagon
KAPPA_FCC_1TICK = 1.0 / math.sqrt(2.0)  # inscribed sphere in cuboctahedron (12 NN)


def kappa_link(*, n_links: int = N4_CAUSAL_LINKS) -> float:
    """Isotropic per-link fraction 1/|N| — unifies γ, cr_strength, ν_CA_natural (§5.2.2 · §1.4 · §1.6)."""
    return 1.0 / float(n_links)


def hex_bridge_row() -> dict[str, float]:
    """SI bridge if canon = 2D hex (§1.4.2). Defaults remain square KAPPA; α_fs unchanged."""
    t_P = math.sqrt(HBAR * G / C**5)  # l_P/c
    l_P = math.sqrt(HBAR * G / C**3)
    hT = KAPPA_HEX * t_P
    c0 = l_P / hT
    e_P = math.sqrt(HBAR * C**5 / G)
    e0 = (HBAR / 2.0) / hT
    return {
        "kappa": KAPPA_HEX,
        "hT_over_t_P": KAPPA_HEX,
        "hT_s": hT,
        "c0_m_s": c0,
        "c0_over_c": c0 / C,
        "c_macro_rel_err": abs(KAPPA_HEX * c0 - C) / C,
        "E0_over_E_P": e0 / e_P,
        "kappa_link": kappa_link(n_links=N6_CAUSAL_LINKS),
        "nu_CA_natural": kappa_link(n_links=N6_CAUSAL_LINKS),
        "alpha_star": 1.0 + 1.0 / (4.0 * math.pi),
        "alpha_fs_inv": 4.0 * math.pi**3 + math.pi**2 + math.pi,
        "cell_area_over_lP2": math.sqrt(3.0) / 2.0,
    }


def fcc_bridge_row() -> dict[str, float]:
    """SI bridge if canon = 3D FCC (§1.6). κ from 1-tick cuboctahedron; α_fs unchanged."""
    t_P = math.sqrt(HBAR * G / C**5)
    l_P = math.sqrt(HBAR * G / C**3)
    hT = KAPPA_FCC_1TICK * t_P
    c0 = l_P / hT
    e_P = math.sqrt(HBAR * C**5 / G)
    e0 = (HBAR / 2.0) / hT
    return {
        "kappa_1tick": KAPPA_FCC_1TICK,
        "hT_over_t_P": KAPPA_FCC_1TICK,
        "hT_s": hT,
        "c0_m_s": c0,
        "c0_over_c": c0 / C,
        "c_macro_rel_err": abs(KAPPA_FCC_1TICK * c0 - C) / C,
        "E0_over_E_P": e0 / e_P,
        "kappa_link": kappa_link(n_links=N12_FCC_CAUSAL_LINKS),
        "nu_CA_natural": kappa_link(n_links=N12_FCC_CAUSAL_LINKS),
        "v_hV_over_lP3": 1.0 / math.sqrt(2.0),
        "alpha_star": 1.0 + 1.0 / (4.0 * math.pi),
        "alpha_fs_inv": 4.0 * math.pi**3 + math.pi**2 + math.pi,
        "note": "asymptotic FCC graph-ball κ — open leaf",
    }


def nu_CA_natural() -> float:
    """ν_CA in natural units (c₀ = l_P = 1): κ_link·c₀·l_P = ¼ (§4.1.2, §5.2.2)."""
    return kappa_link()


def cr_seed_ceiling() -> float:
    """A9 pre-burn-in ceiling for smooth envelope seeds: ν_CA·{B_hV}² (§3.9.6)."""
    frac = bekenshtein_fractional_part()
    return nu_CA_natural() * frac * frac


def cr_dispersion_ceiling() -> float:
    """A9 stationary CR ceiling after N₄ dispersion + ν_CA: ν_CA·(1+{B_hV}) (§3.9.6)."""
    return nu_CA_natural() * (1.0 + bekenshtein_fractional_part())


def heisenberg_phi_min_physical(*, delta_phi_min: float = DELTA_PHI_MIN) -> float:
    """Physical Heisenberg floor Δφ_min = s₀/ℏ = ½ rad (Planck / Arg, §5.0.2)."""
    return delta_phi_min


def heisenberg_phi_min_rad(*, delta_phi_min: float = DELTA_PHI_MIN) -> float:
    """Alias — same physical constant, not 1/2^frac_bits."""
    return heisenberg_phi_min_physical(delta_phi_min=delta_phi_min)


def heisenberg_phi_min_disc(*, phase_bits: int, delta_phi_min: float = DELTA_PHI_MIN) -> int:
    """Δφ_min [rad] → integer phase ticks mod N_ring (strict Z_512 verify)."""
    n_ring = 1 << phase_bits
    return max(1, int(round(delta_phi_min * n_ring / (2.0 * math.pi))))


def phase_disc_to_rad(phi_disc: int, *, phase_bits: int) -> float:
    n_ring = 1 << phase_bits
    tick = int(phi_disc) % n_ring
    return tick * (2.0 * math.pi / n_ring)


@dataclass(frozen=True)
class SIConstants:

    """Planck lattice steps and gate parameters in SI."""



    hbar: float = HBAR

    G: float = G

    c: float = C



    @property

    def l_P(self) -> float:

        """DX — spatial step hL [m]."""

        return math.sqrt(self.hbar * self.G / self.c**3)



    @property

    def t_P(self) -> float:

        """Conventional Planck time l_P/c [s] — textbook, **not** M tick (§7.1)."""

        return self.l_P / self.c



    @property

    def hT(self) -> float:

        """DT — true M-layer tick [s]. hT = t_P·κ = t_P/√2; c₀ = l_P/hT = √2·c."""

        return self.t_P * KAPPA



    @property

    def c0(self) -> float:

        """Tactical CA link speed on N₄ axes [m/s]. c₀ = l_P/hT = √2·c."""

        return self.l_P / self.hT



    @property

    def c_macro(self) -> float:

        """Macro vacuum light speed [m/s]. κ·c₀ = c (CODATA)."""

        return KAPPA * self.c0



    @property

    def nu_CA(self) -> float:

        """Kinematic lattice viscosity ν_CA = ¼·c₀·l_P [m²/s] — N₄ causal cross (§4.1.2)."""

        return 0.25 * self.c0 * self.l_P



    @property

    def mu_P(self) -> float:

        """Planck mass density μ_P = ρ_P [kg/m³]. c⁵/(ℏG²)."""

        return self.c**5 / (self.hbar * self.G**2)



    @property

    def rho_P(self) -> float:

        """Fundamental matter density ρ₀ = m_P/l_P³ = μ_P (§5.0 binary M)."""

        return self.mu_P



    @property

    def u_P(self) -> float:

        """Planck energy density u_P [J/m³]. Gate β; |z|²=1 ↔ ρ_E=u_P. Same as K_P."""

        return self.c**7 / (self.hbar * self.G**2)



    @property

    def K_P(self) -> float:

        """Bulk modulus of vacuum fluid [Pa = J/m³]. K_P = μ_P·c² = u_P (§5.1.1)."""

        return self.mu_P * self.c**2



    @property

    def omega(self) -> float:

        """OMEGA — one full vacuum phase cycle per M tick [rad/s].  ω = 2π/hT."""

        return 2.0 * math.pi / self.hT



    @property

    def phase_scale(self) -> float:

        """hT·ω = 2π — dimensionless tick phase budget."""

        return self.hT * self.omega



    @property

    def alpha_star(self) -> float:

        """ALPHA* — dimensionless gate numerator after |z|² = ρ_E/u_P."""

        return 1.0 + 1.0 / (4.0 * math.pi)



    @property

    def alpha_SI(self) -> float:

        """α in SI [J/m³] before density normalization: (2π + ½)·u_P."""

        return (2.0 * math.pi + 0.5) * self.u_P



    @property

    def epsilon(self) -> float:

        """Dimensionless density floor in |z|² units (= 1 ↔ u_P in SI)."""

        return 1.0



    @property

    def alpha_fs_inv(self) -> float:

        """Inverse fine-structure constant from gate phase geometry (§8.2)."""

        pi = math.pi

        return 4.0 * pi**3 + pi**2 + pi



    @property

    def alpha_fs(self) -> float:

        """Fine-structure constant α — computed, not fitted."""

        return 1.0 / self.alpha_fs_inv



    def force_ansatz_row(self) -> dict[str, float]:
        """§8.4.1 — v ladder; α_s(v)=d/(N_hier π); runner 1/(dπ) ln(v/μ) → M_Z."""
        pi = math.pi
        e_p_gev = self.E_P / EV_J / 1.0e9
        n_hier = int(math.floor(2.0 * math.pi / LN2)) - 1
        d_spatial = 3  # Minkowski space §1.6 — not N_c
        alpha_s_v = d_spatial / (n_hier * pi)
        v = (self.alpha_fs**n_hier) * e_p_gev * math.sqrt(2.0 * pi)
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
            "note": "§8.4.1: runner 1/(d π) ln(v/MZ); π=α_fs foot",
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

    def maxwell_row(self) -> dict[str, float]:
        """§8.2 macro Maxwell — light = K_P/μ_P; T-readout (not Planck ∇)."""
        mu_p = self.mu_P
        k_p = self.K_P
        u_p = self.u_P
        c = self.c
        c_from_fluid = math.sqrt(k_p / mu_p)
        return {
            "mu_P": mu_p,
            "K_P": k_p,
            "u_P": u_p,
            "c": c,
            "c_from_K_over_mu": c_from_fluid,
            "rel_c_fluid": abs(c_from_fluid - c) / c,
            "rel_K_eq_u": abs(k_p - u_p) / u_p,
            "kappa": KAPPA,
            "note": "§8.2 macro: c²=K_P/μ_P; Planck EM = planck_em_row",
        }

    def planck_em_row(self) -> dict[str, float]:
        """§8.2 Planck EM — discrete Arg/j/F₀ ladder; Coulomb N=1 = α F_P (no ∇ on ℓ_P)."""
        f_p = self.c**4 / self.G
        f0 = self.F_0
        alpha = self.alpha_fs
        f_nn = alpha * f_p
        return {
            "s_0": self.s_0,
            "E_0": self.E_0,
            "p_0": self.p_0,
            "F_0": f0,
            "F_P": f_p,
            "F_over_F_P_N1_unit": alpha,
            "F_NN_N": f_nn,
            "c0": self.c0,
            "c": self.c,
            "c0_over_c": self.c0 / self.c,
            "rel_F0_mg": abs(f0 - self.m_arg * self.g_M) / f0,
            "note": "§8.2 Planck: s0/E0/F0 ladder; |F|/F_P=α at N=1; c0=√2 c",
        }

    def radiation_row(self) -> dict[str, float]:
        """§8.2 radiation — s0/E0 ladder + Debye UV; Bose/Planck spectrum still open."""
        e0 = self.E_0
        nu0 = 1.0 / self.hT
        h = 2.0 * math.pi * self.hbar
        h_nu0 = h * nu0
        return {
            "s_0": self.s_0,
            "E_0": e0,
            "nu_0_Hz": nu0,
            "omega_0_rad_s": 2.0 * math.pi * nu0,
            "h_nu0_J": h_nu0,
            "h_nu0_over_E0": h_nu0 / e0,
            "c0": self.c0,
            "c": self.c,
            "kappa_FCC": KAPPA_FCC_1TICK,
            "omega_D_over_nu0": 1.0,
            "note": "§8.2 rad: h ν0=4π E0; ω_D∼1/hT; Bose u(ω) open",
        }

    def decay_row(self) -> dict[str, float]:
        """§8.2 decay — topo frame; Γ/τ/BR still open (T-stats)."""
        return {
            "E_0": self.E_0,
            "s_0": self.s_0,
            "hbar": self.hbar,
            "note": "§8.2 decay: annihilation≠decay; free γ stable; Γ=ℏ/τ open",
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

    def einstein_strain_row(self) -> dict[str, float]:
        """§8.4.2-D — G_μν from Regge deficit of strain; 8π ℓ_P² from Newton."""
        g_model = 1.0  # G/ℓ_P² in MODEL units
        eight_pi_g = 8.0 * math.pi * g_model
        return {
            "G_over_l_P2": g_model,
            "field_eq_coeff_8pi_G": eight_pi_g,
            "flat_deficit": 0.0,  # strain=0 ⇒ δ=0
            "girth_plaquette": 3.0,  # FCC triangle = d
            "d_spatial": 3.0,
            "note": "§8.4.2-D: G_μν=ℰ(δ[strain])=8π ℓ_P² T_μν; stencil soft",
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

    @property
    def m_P(self) -> float:
        """Planck mass [kg]."""
        return math.sqrt(self.hbar * self.c / self.G)

    @property
    def E_P(self) -> float:
        """Conventional Planck energy ℏ/t_P [J] — textbook tick, not M (§7.1)."""
        return self.hbar / self.t_P

    @property
    def bekenstein_bits_hv(self) -> float:
        """I_hV = 2π E_P l_P / (ℏ c ln 2) = 2π/ln 2 — §3.12.6."""
        return 2.0 * math.pi * self.E_P * self.l_P / (self.hbar * self.c * LN2)

    @property
    def delta_phi_min(self) -> float:
        """Heisenberg holonomy floor Δφ_min [rad] — §3.7.2, §5.0.2."""
        return DELTA_PHI_MIN

    @property
    def s_0(self) -> float:
        """Fundamental Arg action quantum s₀ = ℏ·Δφ_min = ℏ/2 [J·s] (§5.0.2)."""
        return self.hbar * self.delta_phi_min

    @property
    def E_0(self) -> float:
        """Arg-carrier energy per M tick E₀ = s₀/hT = E_P/√2 [J] (§5.0.2)."""
        return self.s_0 / self.hT



    @property

    def m_arg(self) -> float:

        """Local E₀/c² on one hV — m_P/√2 [kg]; not a rest-mass particle (§5.0.2)."""

        return self.E_0 / self.c**2



    @property

    def v_arg(self) -> float:

        """Arg-carrier propagation speed on N₄ axes — equals c₀ [m/s] (§5.0.2)."""

        return self.c0



    @property

    def p_0(self) -> float:

        """Mechanical momentum quantum p₀ = s₀/l_P = ℏ/(2l_P) [kg·m/s] (§5.2.1)."""

        return self.s_0 / self.l_P



    @property

    def L_0(self) -> float:

        """Mechanical angular-momentum quantum L₀ = p₀·l_P = s₀ [J·s] (§5.2.1)."""

        return self.s_0



    @property

    def F_0(self) -> float:

        """Mechanical force quantum F₀ = p₀/hT = E₀/(c₀·hT) = m_arg·g_M [N] (§5.2.1)."""

        return self.p_0 / self.hT



    @property

    def g_M(self) -> float:

        """M-tick acceleration quantum g_M = c₀/(2hT); F₀ = m_arg·g_M, p₀ = m_arg·c₀/2 (§5.2.1)."""

        return self.c0 / (2.0 * self.hT)



    @property

    def m_e_CODATA(self) -> float:

        """Electron mass [kg] — external anchor for M→T check (§4.0.1)."""

        return 9.1093837015e-31





# CODATA 2018 (exact)

N_AVOGADRO = 6.02214076e23





SI = SIConstants()


def fcc_nn_plaquette_row() -> dict[str, float | int | bool]:
    """§8.4.1-D3: FCC equal-NN girth = 3 = d_spatial (algebra, not CA sim)."""
    neigh: set[tuple[int, int, int]] = set()
    for x, y in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
        neigh.add((x, y, 0))
        neigh.add((x, 0, y))
        neigh.add((0, x, y))
    assert len(neigh) == 12
    triangles = 0
    for u in neigh:
        for v in neigh:
            if u >= v:
                continue
            duv = (u[0] - v[0]) ** 2 + (u[1] - v[1]) ** 2 + (u[2] - v[2]) ** 2
            if duv == 2:  # same NN length^2 ⇒ edge of packing graph
                triangles += 1
    girth = 3 if triangles > 0 else 0
    d_spatial = 3
    return {
        "n_nn": len(neigh),
        "n_triangles_at_origin": triangles,
        "girth": girth,
        "d_spatial": d_spatial,
        "girth_eq_d": girth == d_spatial,
        "note": "§8.4.1-D3 census algebra",
    }

HV = hv_bit_budget()





def planck_density_from_cell(*, m_P: float | None = None, l_P: float | None = None) -> float:

    """ρ₀ = m_P/l_P³ — must equal μ_P (§5.0)."""

    m = SI.m_P if m_P is None else m_P

    lp = SI.l_P if l_P is None else l_P

    return m / lp**3





def macro_density_illusion(*, occupied_fraction: float) -> float:

    """T-readout: ρ_macro ≈ ⟨b⟩ · ρ_P (§5.0); ⟨b⟩ = mean occupancy, not mean |z|²."""

    return occupied_fraction * SI.rho_P




def matter_density_from_b(*, b: int) -> float:

    """ρ_matter(x) = ρ_P · b(x), b ∈ {0,1} (§5.0)."""

    return float(b) * SI.rho_P




def matter_cell_mass_from_b(*, b: int) -> float:

    """m_cell(x) = m_P · b(x) (§5.0, §8.1)."""

    return float(b) * SI.m_P





def hV_volume(*, l_P: float | None = None) -> float:

    """Elementary cell volume hV = l_P³ [m³]."""

    lp = SI.l_P if l_P is None else l_P

    return lp**3





def vdw_core_volume(*, l_P: float | None = None) -> float:

    """Excluded causal core per macro node: b₀ ≈ 4·hV (§5.3.3, N₄ Heisenberg shell)."""

    return 4.0 * hV_volume(l_P=l_P)





def vdw_b(

    n_moles: float,

    *,

    n_vortices_per_molecule: float,

    N_A: float = N_AVOGADRO,

) -> float:

    """Van der Waals excluded volume b [m³] — §5.3.3."""

    return n_moles * N_A * n_vortices_per_molecule * vdw_core_volume()





def vdw_a(

    *,

    n_vortices_per_molecule: float,

    N_A: float = N_AVOGADRO,

) -> float:

    """Van der Waals attraction coefficient a [Pa·m⁶/mol²] — §5.3.3."""

    nv = n_vortices_per_molecule

    lp = SI.l_P

    return N_A**2 * nv**2 * SI.K_P * lp**6 * SI.alpha_fs





def vdw_pressure(

    n_moles: float,

    volume_m3: float,

    temperature_k: float,

    *,

    n_vortices_per_molecule: float,

    R: float = 8.314462618,

) -> float:

    """Real-gas pressure from Da-derived Van der Waals (§5.3.3)."""

    a = vdw_a(n_vortices_per_molecule=n_vortices_per_molecule)

    b = vdw_b(n_moles, n_vortices_per_molecule=n_vortices_per_molecule)

    return n_moles * R * temperature_k / (volume_m3 - b) - a * n_moles**2 / volume_m3**2





@dataclass(frozen=True)

class SystemQuanta:

    """Individual fractal quanta for a macro system (MODEL.md §4.7.5)."""



    mass_kg: float

    tau_frame_s: float

    radius_m: float | None



    dx: float          # λ̄_C = ℏ/(Mc) — reduced Compton wavelength

    dt: float          # dx/c0

    n_frame: float     # tau_frame/dt

    dx_over_l_P: float

    dt_over_hT: float

    lambda_compton: float  # λ_C = h/(Mc) = 2π·dx

    i_max_bits: float | None = None





def reduced_compton_wavelength(mass_kg: float) -> float:

    """λ̄_C = ℏ/(Mc) — same as Δx_sys in §4.7.5."""

    return HBAR / (mass_kg * C)





def compton_wavelength(mass_kg: float) -> float:

    """λ_C = h/(Mc) = 2π λ̄_C."""

    return H / (mass_kg * C)





def compton_scattering_shift(mass_kg: float, theta_rad: float) -> float:

    """Δλ = λ_C (1 − cos θ) — textbook Compton shift on mass scale M."""

    return compton_wavelength(mass_kg) * (1.0 - math.cos(theta_rad))





def system_quanta(

    mass_kg: float,

    tau_frame_s: float,

    *,

    radius_m: float | None = None,

) -> SystemQuanta:

    """Compute Δx, Δt, N_frame for a coherent macro system (§4.7.5)."""

    dx = reduced_compton_wavelength(mass_kg)

    dt = dx / SI.c0

    n_frame = tau_frame_s / dt

    i_max = None

    if radius_m is not None:

        e = mass_kg * C**2

        i_max = 2.0 * math.pi * e * radius_m / (HBAR * LN2)

    return SystemQuanta(

        mass_kg=mass_kg,

        tau_frame_s=tau_frame_s,

        radius_m=radius_m,

        dx=dx,

        dt=dt,

        n_frame=n_frame,

        dx_over_l_P=dx / SI.l_P,

        dt_over_hT=dt / SI.hT,

        lambda_compton=compton_wavelength(mass_kg),

        i_max_bits=i_max,

    )





def lepton_geometry_factor(m_e: float | None = None) -> float:

    """f_геометрия(e): m_e = m_P · α_fs² · f (§8.2, §1.3)."""

    m_e = m_e if m_e is not None else SI.m_e_CODATA

    return m_e / (SI.m_P * SI.alpha_fs**2)





def arg_quantum_row(*, delta_phi_min: float = DELTA_PHI_MIN) -> dict[str, float]:

    """§5.0.2 Arg-carrier SI row — algebra from ℏ, G, c + Heisenberg floor."""

    s0 = SI.hbar * delta_phi_min

    e0 = s0 / SI.hT

    e_p = SI.hbar / SI.t_P

    m_arg = e0 / SI.c**2

    e0_ev = e0 / EV_J

    e_higgs_ev = M_HIGGS_GEV * 1e9

    return {

        "delta_phi_min_rad": delta_phi_min,

        "s_0_J_s": s0,

        "E_P_J": e_p,

        "E_0_J": e0,

        "E_0_eV": e0_ev,

        "m_arg_kg": m_arg,

        "m_P_kg": SI.m_P,

        "v_arg_m_s": SI.c0,

        "c_macro_m_s": SI.c_macro,

        "E_0_over_E_Higgs": e0_ev / e_higgs_ev,

    }





def mechanical_quantum_row(*, delta_phi_min: float = DELTA_PHI_MIN) -> dict[str, float]:

    """§5.2.1 — p₀, L₀, F₀ ladder from s₀ = ℏ·Δφ_min (no free parameters)."""

    arg = arg_quantum_row(delta_phi_min=delta_phi_min)

    s0 = arg["s_0_J_s"]

    p0 = s0 / SI.l_P

    l0 = s0

    f0 = p0 / SI.hT

    g_m = SI.c0 / (2.0 * SI.hT)

    return {

        "p_0_kg_m_s": p0,

        "L_0_J_s": l0,

        "F_0_N": f0,

        "g_M_m_s2": g_m,

        "p_0_over_half_mP_c": p0 / (0.5 * SI.m_P * SI.c),

        "F_0_over_planck_force": f0 / (SI.c**4 / SI.G),

        "L_0_over_hbar": l0 / SI.hbar,

        "p_0_equals_m_arg_c0_over_2": p0 / (arg["m_arg_kg"] * SI.c0 / 2.0),

        "F_0_equals_m_arg_g_M": f0 / (arg["m_arg_kg"] * g_m),

        "F_0_equals_p_0_over_hT": f0 / (p0 / SI.hT),

    }




def quarter_quantum_row(*, n_links: int = N4_CAUSAL_LINKS) -> dict[str, float | int]:
    """§5.2.2 — κ_link = 1/|N₄| unifies γ, cr_strength, ν_CA_natural."""
    k = kappa_link(n_links=n_links)
    nu = nu_CA_natural()
    return {
        "N4_links": n_links,
        "kappa_link": k,
        "gamma": k,
        "cr_strength": k,
        "nu_CA_natural": nu,
        "gamma_equals_cr": k / k,
        "gamma_equals_nu_CA": k / nu if nu else float("inf"),
        "cr_seed_ceiling": cr_seed_ceiling(),
        "cr_dispersion_ceiling": cr_dispersion_ceiling(),
    }




def energy_quantum_row(*, delta_phi_min: float = DELTA_PHI_MIN) -> dict[str, float]:
    """§5.2.2 — E₀ ladder: E₀ = p₀·c₀ = F₀·l_P = L₀/hT = s₀/hT."""
    s0 = SI.hbar * delta_phi_min
    e0 = s0 / SI.hT
    p0 = s0 / SI.l_P
    f0 = p0 / SI.hT
    l0 = s0
    return {
        "E_0_J": e0,
        "E_0_from_p0_c0": p0 * SI.c0,
        "E_0_from_F0_lP": f0 * SI.l_P,
        "E_0_from_L0_over_hT": l0 / SI.hT,
        "E_0_equals_s0_over_hT": e0,
        "rel_p0_c0": abs(p0 * SI.c0 - e0) / e0,
        "rel_F0_lP": abs(f0 * SI.l_P - e0) / e0,
        "rel_L0_hT": abs(l0 / SI.hT - e0) / e0,
        "alpha_fs_from_gate": SI.alpha_fs,
    }


def amplitude_quantum(*, frac_bits: int | None = None) -> float:
    """a_Q = 2^{−frac_bits} — smallest nonzero |z| on Q lattice (§5.2.3)."""
    fb = HV.frac_bits if frac_bits is None else frac_bits
    return 1.0 / float(1 << fb)


def rho_field_quantum(*, frac_bits: int | None = None) -> float:
    """ρ_Q = a_Q² — one field-density quanta in natural |z|² units (§5.2.3)."""
    a = amplitude_quantum(frac_bits=frac_bits)
    return a * a


def sync_strength_rad(*, delta_phi_min: float = DELTA_PHI_MIN) -> float:
    """Holomorphy sync: κ_link share of Heisenberg step [rad] (§5.2.3)."""
    return kappa_link() * delta_phi_min


def sync_strength_disc(
    *,
    phase_bits: int | None = None,
    delta_phi_min: float = DELTA_PHI_MIN,
) -> int:
    """Integer sync coupling: ⌊Δφ_disc·κ_link⌋ ticks per unit CR pull (§5.2.3)."""
    pb = HV.phase_bits if phase_bits is None else phase_bits
    phi_disc = heisenberg_phi_min_disc(phase_bits=pb, delta_phi_min=delta_phi_min)
    return max(1, int(phi_disc * kappa_link()))


def pauli_kick_rad() -> float:
    """SU(2) exchange antisymmetry phase = π rad (§3.10.4 · §5.2.3)."""
    return math.pi


def pauli_kick_disc(*, phase_bits: int | None = None) -> int:
    """π rad on Z_{N_ring}: N_ring/2 ticks (§5.2.3)."""
    pb = HV.phase_bits if phase_bits is None else phase_bits
    return (1 << pb) // 2


def pauli_rho_min_natural(*, rho_max: float = 1.0) -> float:
    """Dense-component threshold: ρ_max/2 — two fermions share one v_p ceiling (§5.2.3)."""
    return 0.5 * rho_max


def pauli_rho_min_si(*, rho_max_natural: float = 1.0) -> float:
    """SI field-density floor for Pauli probe: κ_link·ρ_max·u_P [J/m³]."""
    return pauli_rho_min_natural(rho_max=rho_max_natural) * SI.u_P


def pauli_overlap_cos(*, delta_phi_min: float = DELTA_PHI_MIN) -> float:
    """Parallel spinors within Heisenberg cone: cos(Δφ_min) (§5.2.3)."""
    return math.cos(delta_phi_min)


def energy_ledger_ticks_per_E0(
    *,
    phase_bits: int | None = None,
    delta_phi_min: float = DELTA_PHI_MIN,
) -> int:
    """Collision Φ ticks equivalent to one E₀ quantum (§5.2.3)."""
    pb = HV.phase_bits if phase_bits is None else phase_bits
    return max(1, heisenberg_phi_min_disc(phase_bits=pb, delta_phi_min=delta_phi_min))


def n_E_from_phi_ticks(phi_ticks: int, *, phase_bits: int | None = None) -> int:
    """Map saturating collision phase [ticks] → integer E₀ ledger units."""
    unit = energy_ledger_ticks_per_E0(phase_bits=phase_bits)
    return abs(int(phi_ticks)) // unit


def elementary_quanta_row(
    *,
    frac_bits: int | None = None,
    phase_bits: int | None = None,
    delta_phi_min: float = DELTA_PHI_MIN,
    rho_max: float = 1.0,
) -> dict[str, float | int]:
    """§5.2.3 — full closure table for verify / MConfig defaults."""
    fb = HV.frac_bits if frac_bits is None else frac_bits
    pb = HV.phase_bits if phase_bits is None else phase_bits
    phi_disc = heisenberg_phi_min_disc(phase_bits=pb, delta_phi_min=delta_phi_min)
    sync_rad = sync_strength_rad(delta_phi_min=delta_phi_min)
    sync_disc = sync_strength_disc(phase_bits=pb, delta_phi_min=delta_phi_min)
    pauli_rad = pauli_kick_rad()
    pauli_disc = pauli_kick_disc(phase_bits=pb)
    return {
        "frac_bits": fb,
        "phase_bits": pb,
        "N_ring": 1 << pb,
        "a_Q": amplitude_quantum(frac_bits=fb),
        "rho_Q": rho_field_quantum(frac_bits=fb),
        "delta_phi_min_rad": delta_phi_min,
        "delta_phi_min_disc": phi_disc,
        "sync_strength_rad": sync_rad,
        "sync_strength_disc": sync_disc,
        "sync_equals_kappa_times_delta_phi": sync_rad / (kappa_link() * delta_phi_min),
        "pauli_kick_rad": pauli_rad,
        "pauli_kick_disc": pauli_disc,
        "pauli_kick_disc_equals_half_ring": pauli_disc == ((1 << pb) // 2),
        "pauli_rho_min_natural": pauli_rho_min_natural(rho_max=rho_max),
        "pauli_rho_min_si_J_m3": pauli_rho_min_si(rho_max_natural=rho_max),
        "pauli_overlap_cos": pauli_overlap_cos(delta_phi_min=delta_phi_min),
        "energy_ticks_per_E0": energy_ledger_ticks_per_E0(
            phase_bits=pb, delta_phi_min=delta_phi_min
        ),
        "E_0_J": SI.E_0,
        "e_0_CODATA_C": 1.602176634e-19,
        "macro_rho_natural": rho_max,
        "macro_rho_si_J_m3": rho_max * SI.u_P,
        "kappa_link": kappa_link(),
    }




def baryon_geometry_factor(m_p: float, *, alpha_fs: float | None = None) -> float:

    """f_геометрия(p): m_p = m_P · (α_fs/3) · f (§8.2)."""

    a = alpha_fs if alpha_fs is not None else SI.alpha_fs

    return m_p / (SI.m_P * (a / 3.0))





def hv_bit_budget_row() -> dict[str, float | int]:

    """§3.12.6 — Planck-derived hV bit budget for verify / configs."""

    row = hv_bit_budget()

    rel = abs(row.B_hV - SI.bekenstein_bits_hv) / row.B_hV

    return {

        "B_hV_bits": row.B_hV,

        "bekenstein_SI_bits": SI.bekenstein_bits_hv,

        "rel_err": rel,

        "N_phi": row.N_phi,

        "mod_bits": row.mod_bits,

        "N_ring": row.N_ring,

        "phase_bits": row.phase_bits,

        "frac_bits": row.frac_bits,

        "n_states": row.n_states,

        "B_phase_bits": row.B_phase,

        "B_amp_bits": row.B_amp,

        "alpha_fs_inv": SI.alpha_fs_inv,
        "heisenberg_phi_min_rad": heisenberg_phi_min_physical(),
        "heisenberg_phi_min_disc": heisenberg_phi_min_disc(phase_bits=row.phase_bits),
        "frac_bits_formula": f"ceil(log2({row.N_ring}/{row.N_phi}))",
    }





# aliases

lepton_mass_factor = lepton_geometry_factor

baryon_mass_factor = baryon_geometry_factor





def as_code_dict() -> dict[str, float]:

    """Drop-in literals for configs / GPU kernels (SI + natural gate)."""

    hv = hv_bit_budget()

    return {

        "DX": SI.l_P,

        "DT": SI.hT,

        "T_P_CONV": SI.t_P,

        "KAPPA": KAPPA,

        "KAPPA_LINK": kappa_link(),

        "GAMMA": kappa_link(),

        "CR_STRENGTH": kappa_link(),

        "NU_CA_NATURAL": nu_CA_natural(),

        "C0_m_s": SI.c0,

        "C_MACRO_m_s": SI.c_macro,

        "MU_P_kg_m3": SI.mu_P,

        "U_P_J_m3": SI.u_P,

        "K_P_J_m3": SI.K_P,

        "OMEGA_rad_s": SI.omega,

        "ALPHA_STAR": SI.alpha_star,

        "ALPHA_SI_J_m3": SI.alpha_SI,

        "EPSILON": SI.epsilon,

        "PHASE_SCALE": SI.phase_scale,

        "ALPHA_FS": SI.alpha_fs,

        "ALPHA_FS_INV": SI.alpha_fs_inv,

        "M_P_kg": SI.m_P,

        "E_P_J": SI.E_P,

        "S_0_J_s": SI.s_0,

        "E_0_J": SI.E_0,

        "M_ARG_kg": SI.m_arg,

        "V_ARG_m_s": SI.v_arg,

        "DELTA_PHI_MIN_rad": SI.delta_phi_min,

        "B_HV_bits": hv.B_hV,

        "N_PHI": hv.N_phi,

        "MOD_BITS": hv.mod_bits,

        "N_RING": hv.N_ring,

        "PHASE_BITS": hv.phase_bits,

        "FRAC_BITS": hv.frac_bits,

        "SYNC_STRENGTH_RAD": sync_strength_rad(),

        "PAULI_KICK_RAD": pauli_kick_rad(),

        "PAULI_RHO_MIN": pauli_rho_min_natural(),

        "PAULI_OVERLAP_COS": pauli_overlap_cos(),

    }


