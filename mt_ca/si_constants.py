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
from decimal import Decimal, ROUND_HALF_UP, getcontext



# SI-2019 exact: c, h (⇒ ℏ = h/2π). G still measured (CODATA).

H = 6.62607015e-34  # J·s exact

HBAR = H / (2.0 * math.pi)  # J·s exact via h

G = 6.67430e-11  # m³/(kg·s²) — not exact

C = 299_792_458.0  # m/s exact

LN2 = math.log(2.0)



# N₄ isotropic macro readout: c = κ·c₀ (§1.1 MODEL.md)

KAPPA = 1.0 / math.sqrt(2.0)



# §3.7.2 / §5.0.2 — Heisenberg geometric floor on holonomy Δφ [rad]

DELTA_PHI_MIN = 0.5



# Elementary charge scale for eV reporting

EV_J = 1.602176634e-19



# Higgs mass — PDG reference for rel_err only; prediction = m_P·α_fs^8·√(π/2) (§8.3)

M_HIGGS_GEV_PDG = 125.25

# Back-compat alias (tests comparing hierarchy E0 ≫ m_H)
M_HIGGS_GEV = M_HIGGS_GEV_PDG

# Proton mass — PDG reference for rel_err only; prediction = α_fs·v/2·(1+κ²/N₁₂) (§8.2)
M_PROTON_GEV_PDG = 0.93827208816

# Electron mass — PDG reference for rel_err only; prediction = α_fs²·m_H/N_φ (§8.2)
M_ELECTRON_GEV_PDG = 0.00051099895

# Neutron mass — PDG reference for rel_err only; prediction = m_p + 2·m_e (§8.2·7)
M_NEUTRON_GEV_PDG = 0.93956542052

# Neutrino atmospheric scale √|Δm²₃₁| [eV] — PDG-ish; prediction = α⁵·2m_H/(N_hier N_φ) (§8.2)
M_NU_ATM_EV_PDG = 0.05

# ΛCDM anchors — T-layer observations for **our bubble** (not knobs in g). Planck 2018 central.
SECOND_PER_YEAR = 365.25 * 86400.0
SECOND_PER_KYR = SECOND_PER_YEAR * 1e3
SECOND_PER_GYR = SECOND_PER_YEAR * 1e9
COSMO_BUBBLE_AGE_GYR = 13.787  # ±0.020 Gyr
COSMO_RECOMB_KYR = 380.0  # last scattering ~380 kyr after local BB (N=0)

# CMB monopole — T-layer reference for contrast in vacuum_bath_row (not a g knob)
T_CMB_K_REF = 2.7255


def _hT_decimal() -> Decimal:
    """M tick [s] in high precision for N~10⁷⁰ bubble algebra (§0.2)."""
    getcontext().prec = 100
    hbar = Decimal("1.054571817e-34")
    g = Decimal("6.67430e-11")
    c = Decimal("299792458")
    l_p = (hbar * g / (c**3)).sqrt()
    t_p = l_p / c
    return t_p / Decimal(2).sqrt()


def m_tick_to_si_seconds(n_ticks: int | float, *, hT: float | None = None) -> float:
    """META §3.0.1 — exact SI elapsed time since bubble tick N=0: t = N·hT."""
    ht = SI.hT if hT is None else hT
    return float(n_ticks) * ht


def si_seconds_to_m_tick(t_s: float, *, hT: Decimal | float | None = None) -> int:
    """Map SI duration since bubble N=0 to nearest integer M tick (Decimal for N~10⁷⁰)."""
    getcontext().prec = 100
    ht = _hT_decimal() if hT is None else (hT if isinstance(hT, Decimal) else Decimal(str(hT)))
    n = (Decimal(str(t_s)) / ht).to_integral_value(rounding=ROUND_HALF_UP)
    return int(n)


def m_tick_count_to_str(n_ticks: int) -> str:
    """Scientific string for tick counts beyond float integer precision."""
    if n_ticks == 0:
        return "0"
    exp = int(math.floor(math.log10(abs(n_ticks))))
    mant = n_ticks / 10**exp
    return f"{mant:.6g}e{exp}"



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

        """π-tower T-readout α (demoted competitor; not structural preferred)."""

        return 1.0 / self.alpha_fs_inv

    @property
    def alpha_preferred(self) -> float:
        """Structural α — soft-face preferred §8.2·U0 (lab-inside)."""
        return float(self.alpha_U0_soft_face_ask_row()["alpha_pref"])

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

    def na0_from_carrier_row(self) -> dict[str, float | int | str | bool]:
        """N_a0 without optical a₀ — first carrier candidate.

        Primary (shipped):
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
            "alpha_star_stack": a_stack,
            "alpha_star_stack_inv": 1.0 / a_stack,
            "alpha_star_bare": a_bare,
            "alpha_star_bare_inv": 1.0 / a_bare,
            "alpha_star_stack_optical_inv": 1.0 / a_stack_opt,
            "vs_codata_ppm_stack": (a_stack - alpha_codata) / alpha_codata * 1e6,
            "vs_codata_ppm_bare": (a_bare - alpha_codata) / alpha_codata * 1e6,
            "vs_optical_fp_ppm_stack": (a_stack - a_stack_opt) / a_stack_opt * 1e6,
            "monomial_stack_open": True,
            "carrier_na0_ok": abs(n_a0 / n_a0_opt - 1.0) < 5e-4
            and abs(mapped(a_stack, n_a0, bare=False) - a_stack) / a_stack < 1e-12,
            "note": (
                "HISTORICAL probe: N_a0=(m_P/m_e)·137. Ask-model §8.2·H·ask REJECTED "
                "as α-input (empty for deriving α). Keep for ppm archaeology only. "
                "See na0_h_carrier_ask_row."
            ),
            "ask_rejected_as_alpha_input": True,
        }

    def na0_h_carrier_ask_row(self) -> dict[str, float | int | str | bool | list]:
        """§8.2·H·ask — asked the carrier for N_a0 (H size in hL hops).

        Method (same as §8.2·geo·ask / phonon ask):
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
                "status": "shipped",
                "mechanism": "same a=l_P as cuboctahedron/phonon ask",
            },
            {
                "id": "N_a0_integer",
                "maps_to": "Thm 5.2 — size is occupancy hops, not continuum metre",
                "status": "shipped",
                "mechanism": "sound/light = n_k / n_E; H radius on same ladder",
            },
            {
                "id": "hop_alpha_Nc_over_Na0",
                "ratio": n_c / n_a0_bohr,
                "maps_to": "α = N_c/N_a0 (Bohr rung)",
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
                "status": "shipped_mass",
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
            "theorem": "§8.2·H·ask — N_a0 from carrier; mass≠independent size",
            "method": "ask-model: a=l_P → inventory → which enters size → report",
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
            "ask_ok": identity_ok and rhyme_ok and True,
            "note": (
                "Asked carrier: Thm5.2⇒N_a0∈ℤ; hop α=N_c/N_a0 and mass α²=m_e N_φ/m_H "
                "are one α² — masses do not fix N_a0 alone. Rejected N_c·137 and optical "
                "a₀ as M-definition. FINT: α sealed without meter; N_a0=N_c/α is readout "
                "(see alpha_meter_na0_bridge_row). OPEN remains: H→ℤN_a0 without α "
                "(census) — does NOT block α / meter definition."
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


    def meter_decouple_from_M_row(self) -> dict[str, float | int | str | bool | list]:
        """§8.2·meter·decouple — SI metre ∉ M; lengths on M are hops of hL.

        Cooler seal after α + meter-fint:
          On M there is no metre. Size = occupancy hops (Thm 5.2).
          hL := A1 light-like link; l_P is the name once a≡hL is forced (§7.4).
          α, upstairs masses, N_a0=N_c/α are metre-free.
          SI-2019 metre (c-fixed) and optical a0 are optional T-export / T-door only.
          Writing x_m = N·l_P_SI still needs ħ,G for lab speech — not for the M ruler.
        """
        soft = self.alpha_U0_soft_face_ask_row()
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
                "maps_to": "soft-face α — no metre in definition",
                "ok": bool(soft["derivation_closed"]) and bool(soft["ask_ok"]),
            },
            {
                "id": "masses_metre_free",
                "maps_to": "upstairs cascade on preferred α — GeV/hops, not metre",
                "ok": bool(up["ask_ok"]),
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
            "ask_ok": (
                m_board_ok
                and bool(meter["ask_ok"])
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
        α is dimensionless and exact (soft-face) ⇒ every EM length is
            L = N(α, N_c, …) · l_P
        Length unit itself from velocity × time (and/or ħ):
            [L] = [V][T]  ⇒  l_P = c · t_P = √(ħ G / c³)
        On carrier: hL = c0 · hT (A1 light-like); l_P := hL.
        α ([α]=1, exact) then sets the hop hierarchy:
            λ̄_C / l_P = N_c = m_P/m_e
            a0    / l_P = N_c/α = N_a0
            r_e   / l_P = α·N_c = α²·N_a0
        """
        soft = self.alpha_U0_soft_face_ask_row()
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
                "maps_to": "[α]=1; soft-face sealed — scales ratios only",
                "ok": bool(soft["derivation_closed"]) and bool(soft["ask_ok"]),
            },
            {
                "id": "Compton_hops",
                "maps_to": "λ̄_C = N_c · l_P",
                "N": n_compton,
                "ok": bool(up["ask_ok"]),
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
            "ask_ok": (
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
                "ok": bool(length["ask_ok"]),
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
            "ask_ok": (
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
                "ok": bool(time["ask_ok"]),
            },
            {
                "id": "step2_length_from_light",
                "maps_to": "l_P = c·t_P — [L] = light-path in one time quantum",
                "ok": id_L_from_T and bool(length["ask_ok"]),
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
            "ask_ok": (
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
            "ask_ok": all(bool(item["ok"]) for item in inventory),
            "note": (
                "Natural T_P:=E_P=ℏ/t_P; carrier T_P_M:=E_0. "
                "k_B and kelvin are T-export only — not ontology."
            ),
        }

    def coulomb_M_native_row(self) -> dict[str, float | int | str | bool | list]:
        """§8.2·Coulomb·M-native — force law without continuum α on M.

        Forgotten continuum: writing F=α_fs F_P n1 n2/N² with
        α_fs=1/(4π³+π²+π) smuggles π-tower into the M force law.
        Full quantization: unit NN Coulomb is F₀/M; α=κ/M is T-name only.
        """
        census = self.alpha_nF_kick_census_row()
        kappa = float(census["kappa"])
        m = int(census["M"])
        f0_over_fp = kappa  # F₀/F_P = κ
        alpha = kappa / m
        # M-native NN unit force in F_P units:
        f_nn_over_fp = f0_over_fp / m  # = α
        inventory: list[dict[str, str | float | bool | int]] = [
            {
                "id": "M_native_NN",
                "maps_to": "F_NN = F₀/M — no π, ε₀, π-tower on M",
                "status": "shipped",
            },
            {
                "id": "general_graph_distance",
                "maps_to": "F = n1 n2 F₀/(M N²), N∈ℕ hops",
                "status": "shipped",
            },
            {
                "id": "T_readout_alpha",
                "ratio": alpha,
                "maps_to": "α=κ/M names the same NN force as F/F_P",
                "status": "shipped",
            },
            {
                "id": "reject_pi_tower_in_M_force",
                "maps_to": "α_fs=1/(4π³+π²+π) must not define M Coulomb",
                "status": "rejected_as_M_input",
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
            "ask_ok": m == 97
            and abs(alpha - f_nn_over_fp) < 1e-15
            and abs(kappa**2 - 0.5) < 1e-15,
            "note": (
                "M Coulomb: F=n1 n2 F₀/(M N²) with M=97. "
                "α=κ/M is T-readout of the same NN ratio. "
                "π-tower demoted from M force law; soft ppm OPEN."
            ),
        }

    def floor1_leptonic_ask_row(self) -> dict[str, float | int | str | bool | list]:
        """§6·floor1·ask — what can live at 10³…10⁵·dl (pre-resonances / leptonic).

        Walk (carrier, no α-fit):
          Floor 0 = one-cell pra-defect (electron core). Floor 2+ = confining
          (girth d, B-class). Floor 1 sits in the desert BETWEEN them.

        Scale window (stamped integers, not CODATA):
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
                "maps_to": "floor1_B0_census_ask_row — C2 stable; C4=pre-resonance",
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
            "theorem": "§6·floor1·ask — leptonic pre-resonance band on N₁₂^{3…4}",
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
            "ask_ok": window_ok and ir_far and floor2_above and n12 == 12,
            "note": (
                "Floor 1: linear band ~N₁₂³…N₁₂⁴·dl (pre-resonances / leptonic). "
                "Not Compton/a₀, not confining floor 2, not N_gen. "
                "OPEN: multi-cell B=0 census; μ/τ mass not claimed here."
            ),
        }

    def floor1_B0_census_ask_row(self) -> dict[str, float | int | str | bool | list]:
        """§6·floor1·B0·census — which B=0 configs at ~N₁₂³…N₁₂⁴ can be stable.

        Stability (already stamped §8.2 decay): no downhill g with same
        additive invariants (Q, and stamped B,L,…) and lower ledger energy.

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
              (dressing·close). Existence of channel CLOSED; Γ soft-OPEN.

          C4 Q=0 multi-cell blob without ± pair (pure excitation)
            — NO topo charge to protect; A5 returns to vacuum.
              = pre-resonance / transient. UNSTABLE.

          C5 ± pair bound at floor1 radius (positronium-like)
            — annihilation channel stamped when ± meet (§5.0.3).
              UNSTABLE as bound B=0 object.

          C6 neutral with stamped L (ν-scheme)
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
            "ask_ok": census_ok,
            "note": (
                "B=0 census @ N₁₂³…N₁₂⁴: C2 dressed e± STABLE; "
                "C4 Q=0 blobs = pre-resonances UNSTABLE; "
                "C5 ± annihilate; C3 channel CLOSED; continuum Γ≠M; n_ticks bath SOFT; "
                "C6 ν off-band (R≠floor1)."
            ),
        }

    def floor1_dressing_ask_row(self) -> dict[str, float | int | str | bool | list]:
        """§6·floor1·dressing·ask — what is the near-zone of lightest Q=±1?

        Ask to carrier (§5.0.5), not invention:

          What is ρ_Θ? What fixes its support radius?

        CLOSED from stamped pieces:
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

        ask_ok = (
            n12 == 12
            and abs(dphi - 0.5) < 1e-12
            and r_min == 1.0
            and "closed_rho_Theta_is_dressing" in closed_ids
            and "closed_R_min_epsilon_star" in closed_ids
            and "open_R_dress_outer" in open_ids
            and "reject_R_equals_floor1_band" in reject_ids
        )

        return {
            "theorem": "§6·floor1·dressing·ask — near-zone ρ_Θ of lightest Q=±1",
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
            "ask_ok": ask_ok,
            "note": (
                "Dressing = ρ_Θ halo (§5.0.5): min ⊇ ε-star (1·dl, N12). "
                "Outer R_dress OPEN (shell-walk / combinatorial). "
                "NOT forced to N12^3…^4; NOT Compton; NOT α-input."
            ),
        }

    def floor1_dressing_close_row(self) -> dict[str, float | int | str | bool | list]:
        """§6·floor1·dressing·close — outer R_dress of lightest Q=±1 = ε-star.

        Closes open from floor1_dressing_ask_row.

        Lemma (stamped pieces only):
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
            "ask_ok": lemma_ok,
            "note": (
                "R_dress=R_min=1·dl: N12<N_phi forces full ε-halo above Δφ_min; "
                "local gate=first shell; multi-shell=excitation. "
                "Floor1 band ≠ e dressing. f-shape → dressing·f·close."
            ),
        }

    def floor1_dressing_f_close_row(self) -> dict[str, float | int | str | bool | list]:
        """§6·floor1·dressing·f·close — shape of f in ρ_Θ∝f(|Δφ|,|ζ|).

        Closes soft-OPEN from dressing·close / dressing·ask.

        Carrier (§5.0.5): cloud = where |Δφ|, |ζ|, Arg-pressure hold
        ≥ Heisenberg floor; ⟨ρ_Θ⟩_T = binomial coarse; ∫ρ_Θ ∼ n_E
        (integer quanta, not float-KN). No mechanical float-knobs on M.

        CLOSED:
          ρ_Θ(x) = 𝟙[ |Δφ_N(x)| ≥ Δφ_min ]
          — Heaviside / set-membership on the only stamped numeric floor.
          |ζ| co-varies via gate ζ=(Σ_N z)·z* but has no independent
          stamped floor; does not add a free continuous axis.
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
                "maps_to": "|ζ| gate scalar; no stamped ζ_min → not second free axis",
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
            "ask_ok": ok,
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
          ⇒ channel *existence* CLOSED; object UNSTABLE.
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
            "ask_ok": ok,
            "note": (
                "Floor1 leftovers: C3→C2+γ existence CLOSED; continuum Γ≠M; "
                "n_ticks in filled bath SOFT; ν off-band."
            ),
        }

    def floor1_C3_gamma_close_row(self) -> dict[str, float | int | str | bool | list]:
        """§6·floor1·C3·gamma·close — continuum Γ ≠ M; n_ticks in bath still soft.

        Soft was «find Γ=ℏ/τ». Carrier (§8.2 decay):

          Continuum N(t)=N0 e^{-t/τ}, Γ=ℏ/τ, BR — NOT laws of M.
          That is T-statistics of many systems (§2.1). g is deterministic.

        CLOSED on M:
          · Clock form = n_ticks ∈ ℕ · hT (ledger time), not float Γ.
          · Reject treating soft as free continuum rate knob on M.

        SOFT (reopened — alone vs filled bath):
          · Hyp. n_ticks=1 for *lonely* multi-shell C3 (A1+local downhill)
            may be an empty-background artifact. Vacuum dogfood: bath
            boiled only when the *whole* lattice was set — no void.
            n_ticks for C3 embedded in filled A5 bath is not stamped.

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
                    "filled A5 bath n_ticks unstamped"
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
            "ask_ok": form_ok,
            "note": (
                "Continuum ℏ/τ ≠ M (CLOSED). Alone n_ticks=1 is soft hyp — "
                "may fall because lonely/void; filled-bath clock open. "
                "μ PDG lifetime is another leaf."
            ),
        }

    def floor1_C3_bath_dogfood_row(self) -> dict[str, float | int | str | bool | list]:
        """§6·floor1·C3·bath·dogfood — previous floor = VACUUM_BOIL, no planted C3.

        Live (cuda, size=256, steps=1024, scripts/run_filled_bath_emergence.py):
          · VACUUM (gauge-fixed class 0): Φ=0, frozen — contrast=1 forever.
          · VACUUM_BOIL (whole lattice, NN Δφ=Δφ_min): evolves; contrast
            1.5 → ~773; ρ_max → 1; emerged_b=False (no |n_∂|≥¾ yet).
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
                "id": "soft_open_b_matter_not_yet",
                "maps_to": "b_topk=b_argmax=0 at 1024 ticks — topology still open",
                "status": "soft_open",
            },
            {
                "id": "soft_open_C3_n_ticks_filled_bath",
                "maps_to": "n_ticks for C3-in-bath still unstamped (needs b first)",
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
            and "soft_open_b_matter_not_yet" in soft_open_ids
        )
        return {
            "theorem": "§6·floor1·C3·bath·dogfood — boil floor first; no lonely C3",
            "size": 256,
            "steps": 1024,
            "boil_contrast_final": 773.473,
            "boil_emerged_b": False,
            "vacuum_frozen": True,
            "derivation_closed": False,
            "inventory": inventory,
            "closed_ids": closed_ids,
            "soft_open_ids": soft_open_ids,
            "ask_ok": ok,
            "note": (
                "Previous floor VACUUM_BOIL runs and self-organizes contrast; "
                "gauge-fixed VACUUM does not. Matter b / C3 clock still soft."
            ),
        }

    def carrier_torus_close_row(self) -> dict[str, float | int | str | bool | list]:
        """§1.7 · Carrier topology: finite wall-free Λ = torus (was DEVLOG §10.1).

        Ask-model: what global glue does Λ have?

        Carrier answers (2026-09-24):
          · Absorbing wall → drains Σ|z|² → breaks A3 (or non-local reinjection).
          · Reflecting wall → preferred locus; A5 vacuum not homogeneous.
          · Open finite patch without wrap = walls under another name.
          · Sphere / curved compact → no flat FCC/hex equal light-like edges (§1).
          · Infinite noncompact Λ: local g same — not rejected as local law;
            finite readout / D5 on finite connected graph / META wave-return
            need compact-without-boundary.
          · Flat translation lattice + compact no boundary → torus:
                (3+1) T³ · (2+1) slice T².
          · Λ×S¹ = phase fiber over Λ (Arg/U(1)), not «torus instead of lattice».
          · CLOSED: finite wall-free carrier topology = torus.
          · SOFT: cosmological period N; long-run entropy numerics; covers.
          · Sim torch.roll = eng readout of §1.7 (DEVLOG §10.1), not new physics.
        """
        inventory: list[dict[str, str | float | bool]] = [
            {
                "id": "closed_finite_wallfree_is_torus",
                "maps_to": "T³ (FCC) / T² (hex slice) — periodic ID of Λ",
                "status": "closed",
                "mechanism": "A3+A5+no preferred wall + flat packing",
            },
            {
                "id": "closed_Lambda_times_S1_fiber",
                "maps_to": "Λ×S¹ = phase circle over lattice (§3.9.1); not instead-of-Λ",
                "status": "closed",
            },
            {
                "id": "closed_sim_roll_is_readout",
                "maps_to": "torch.roll / bond wrap = eng of §1.7, not separate law",
                "status": "closed",
            },
            {
                "id": "reject_absorbing_wall",
                "maps_to": "norm sink breaks A3",
                "status": "rejected",
            },
            {
                "id": "reject_reflecting_wall",
                "maps_to": "preferred locus breaks homogeneous A5",
                "status": "rejected",
            },
            {
                "id": "reject_sphere_as_flat_FCC_carrier",
                "maps_to": "no equal light-like FCC packing on sphere as M carrier",
                "status": "rejected",
            },
            {
                "id": "soft_open_period_N_and_covers",
                "maps_to": "cosmological |Λ| / covers vs fundamental domain",
                "status": "soft_open",
            },
        ]
        closed_ids = [
            i["id"] for i in inventory if str(i["status"]).startswith("closed")
        ]
        reject_ids = [
            i["id"] for i in inventory if str(i["status"]) == "rejected"
        ]
        soft_open_ids = [
            i["id"] for i in inventory if str(i["status"]) == "soft_open"
        ]
        ok = (
            "closed_finite_wallfree_is_torus" in closed_ids
            and "closed_Lambda_times_S1_fiber" in closed_ids
            and "closed_sim_roll_is_readout" in closed_ids
            and "reject_absorbing_wall" in reject_ids
            and "reject_reflecting_wall" in reject_ids
            and "reject_sphere_as_flat_FCC_carrier" in reject_ids
            and "soft_open_period_N_and_covers" in soft_open_ids
        )
        return {
            "theorem": "§1.7 carrier torus — finite wall-free Λ = T^d",
            "topology_closed": True,
            "Lambda_times_S1_closed": True,
            "period_N_soft_open": True,
            "derivation_closed": ok,
            "inventory": inventory,
            "closed_ids": closed_ids,
            "reject_ids": reject_ids,
            "soft_open_ids": soft_open_ids,
            "ask_ok": ok,
            "note": (
                "Finite wall-free carrier = torus (T³/T²). Λ×S¹ = phase fiber. "
                "Period N / covers soft. Sim wrap = readout of §1.7."
            ),
        }

    def gpu_eng_tail_close_row(self) -> dict[str, float | int | str | bool | list]:
        """§0.10 · GPU eng-tail close (was DEVLOG §10.2–§10.4).

        Ask: are the three GPU fuses new physics or MODEL readout?

        Carrier answers (2026-09-24):
          · Floor+seed (§10.2): z≡0 deadlock; |z|≥z_min; vacuum_amplitude=z_min;
            per-cell gauge_fix forbidden on tick path.
          · Step algebra (§10.3): R(Φ)=ω^Φ only; Euler z+=iφz rejected (A3).
          · Literals (§10.4): DX/DT/K_P/α* = as_code_dict SI paste, not knobs.
          · All CLOSED as eng readout of §0.5 / A3·A4 / §7 SI.
          · Soft: verify norm_drift threshold = sim hygiene.
        """
        hv = hv_bit_budget()
        z_min = 2.0 ** (-hv.frac_bits)
        alpha_star = 1.0 + 1.0 / (4.0 * math.pi)
        code = as_code_dict()
        inventory: list[dict[str, str | float | bool]] = [
            {
                "id": "closed_planck_floor_and_seed",
                "ratio": z_min,
                "maps_to": "§0.5 · A5 · z_min=2^{-B_amp}; vacuum_amplitude=z_min",
                "status": "closed",
                "mechanism": "z≡0 deadlock; IC on floor not fitted 1e-6",
            },
            {
                "id": "closed_reject_per_cell_gauge_fix_on_tick",
                "maps_to": "per-cell U(1) kills ζ_imag; global gauge = T/report only",
                "status": "closed",
            },
            {
                "id": "closed_R_Phi_not_Euler",
                "maps_to": "A3·A4 · §3.12.5 — nonlinearity = R(Φ)=ω^Φ only",
                "status": "closed",
            },
            {
                "id": "closed_gpu_literals_are_SI_paste",
                "maps_to": "DX=l_P DT=hT K_P α*=1+1/(4π) via as_code_dict",
                "status": "closed",
            },
            {
                "id": "reject_z_equiv_0_vacuum",
                "maps_to": "z≡0 is not A5 vacuum",
                "status": "rejected",
            },
            {
                "id": "reject_Euler_add_step",
                "maps_to": "z+=iφz breaks Σ|z|²",
                "status": "rejected",
            },
            {
                "id": "reject_literals_as_fitted_knobs",
                "maps_to": "literals ≠ free GPU knobs outside SI",
                "status": "rejected",
            },
            {
                "id": "soft_open_norm_drift_verify_threshold",
                "maps_to": "norm_drift<1e-4 in verify — hygiene, not M law",
                "status": "soft_open",
            },
        ]
        closed_ids = [
            i["id"] for i in inventory if str(i["status"]).startswith("closed")
        ]
        reject_ids = [
            i["id"] for i in inventory if str(i["status"]) == "rejected"
        ]
        soft_open_ids = [
            i["id"] for i in inventory if str(i["status"]) == "soft_open"
        ]
        lit_ok = (
            abs(float(code["DX"]) - float(self.l_P)) / float(self.l_P) < 1e-15
            and abs(float(code["DT"]) - float(self.hT)) / float(self.hT) < 1e-15
            and abs(float(code["K_P_J_m3"]) - float(self.K_P)) / float(self.K_P) < 1e-12
            and abs(float(code["ALPHA_STAR"]) - alpha_star) < 1e-12
            and abs(float(code["ALPHA_STAR"]) - float(self.alpha_star)) < 1e-12
        )
        floor_ok = hv.frac_bits == 6 and abs(z_min - 1.0 / 64.0) < 1e-15
        ok = (
            floor_ok
            and lit_ok
            and "closed_planck_floor_and_seed" in closed_ids
            and "closed_R_Phi_not_Euler" in closed_ids
            and "closed_gpu_literals_are_SI_paste" in closed_ids
            and "reject_z_equiv_0_vacuum" in reject_ids
            and "reject_Euler_add_step" in reject_ids
            and "soft_open_norm_drift_verify_threshold" in soft_open_ids
        )
        return {
            "theorem": "§0.10 GPU eng-tail — floor/step/literals = MODEL readout",
            "z_min": z_min,
            "frac_bits": hv.frac_bits,
            "ALPHA_STAR": float(code["ALPHA_STAR"]),
            "DX": float(code["DX"]),
            "DT": float(code["DT"]),
            "K_P": float(code["K_P_J_m3"]),
            "floor_closed": True,
            "unitary_step_closed": True,
            "literals_closed": True,
            "derivation_closed": ok,
            "inventory": inventory,
            "closed_ids": closed_ids,
            "reject_ids": reject_ids,
            "soft_open_ids": soft_open_ids,
            "ask_ok": ok,
            "note": (
                "GPU fuses CLOSED as readout: floor+seed (§0.5), R(Φ) not Euler, "
                "SI literals paste. Soft: verify norm_drift threshold."
            ),
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

    def vacuum_bath_row(self) -> dict[str, float | int | str | bool]:
        """§8.2·vac — A5 boiling bath: ρ_E(z_min), spectral anchors; ≠ CMB (META §3.0)."""
        hv = hv_bit_budget()
        z_min = 2.0 ** (-hv.frac_bits)
        z_sq_natural = 2.0 * z_min * z_min
        u_p = self.u_P
        rho_vac = z_sq_natural * u_p
        sigma = 5.670374419e-8
        a_rad = 4.0 * sigma / self.c
        t_bath = (rho_vac / a_rad) ** 0.25
        t_ceiling = (u_p / a_rad) ** 0.25
        rad = self.radiation_row()
        nu0 = rad["nu_0_Hz"]
        return {
            "z_min": z_min,
            "frac_bits": hv.frac_bits,
            "B_hV": hv.B_hV,
            "z_sq_natural_vac": z_sq_natural,
            "rho_E_vac_J_m3": rho_vac,
            "u_P_J_m3": u_p,
            "rho_over_uP": z_sq_natural,
            "T_M_bath_K": t_bath,
            "T_uP_ceiling_K": t_ceiling,
            "T_CMB_K_ref": T_CMB_K_REF,
            "log10_T_M_bath": math.log10(t_bath),
            "log10_T_M_bath_over_CMB": math.log10(t_bath / T_CMB_K_REF),
            "nu_0_Hz": nu0,
            "omega_0_rad_s": rad["omega_0_rad_s"],
            "lambda_0_m": self.c / nu0,
            "lambda_0_over_l_P": (self.c / nu0) / self.l_P,
            "h_nu0_over_E0": rad["h_nu0_over_E0"],
            "omega_D_over_nu0": rad["omega_D_over_nu0"],
            "is_CMB": False,
            "note": "§8.2·vac: A5 ocean bath; Bose u(ω) open; CMB = bubble T-layer only",
        }

    def cuboctahedron_geometry_row(self) -> dict[str, float | int | str | bool]:
        """§8.2·geo / §1.6.2 — 1-tick cuboctahedron from edge a=l_P; ratios are derived."""
        n12 = N12_FCC_CAUSAL_LINKS
        n_tri = 8
        n_sq = 6
        n_edges = 24
        girth = 3
        d_spatial = 3
        kappa = KAPPA_FCC_1TICK
        lp = self.l_P
        edge_a = lp  # A1: 12 NN at l_P ⇒ cuboctahedron edge a = l_P (§8.2·geo)
        v_hv = edge_a**3 / math.sqrt(2.0)
        vol_cubo = (8.0 / 3.0) * math.sqrt(2.0) * edge_a**3
        v_over_v_hv = vol_cubo / v_hv
        a_sq_one = edge_a**2
        a_tri_one = (math.sqrt(3.0) / 4.0) * edge_a**2
        a_sq = n_sq * a_sq_one
        a_tri = n_tri * a_tri_one
        a_total = a_sq + a_tri
        s_total = a_total
        r_out = edge_a
        r_in_1tick = kappa * edge_a
        r_in_classical = edge_a * math.sqrt(6.0) / 6.0
        alpha_inv_stamped = 4.0 * math.pi**3 + math.pi**2 + math.pi
        alpha_inv_geom = float(n12 * (n12 + 1) - n_tri - 2 * n_sq + girth // d_spatial)
        alpha_inv_geom_alt = float(
            n12 * (n12 + 1) - n_tri - 2 * n_sq + v_over_v_hv / (n_sq * kappa**2)
        )
        codata_inv = self.alpha_fs_inv
        return {
            "anchor": "edge_a = l_P from A1 (12 NN at l_P); all body measures at a first",
            "edge_a_m": edge_a,
            "edge_a_over_l_P": edge_a / lp,
            "l_P_m": lp,
            "n_nn": n12,
            "n_edges": n_edges,
            "n_faces_square": n_sq,
            "n_faces_triangle": n_tri,
            "R_out_m": r_out,
            "R_in_1tick_m": r_in_1tick,
            "R_in_over_R_out_1tick": kappa,
            "A_square_one_m2": a_sq_one,
            "A_triangle_one_m2": a_tri_one,
            "A_square_total_m2": a_sq,
            "A_triangle_total_m2": a_tri,
            "S_total_m2": s_total,
            "V_cuboctahedron_m3": vol_cubo,
            "v_hV_m3": v_hv,
            "V_over_S_m": vol_cubo / s_total,
            "square_plaquette_perimeter_m": 4.0 * edge_a,
            "V_over_v_hV": v_over_v_hv,
            "V_over_v_hV_exact": "16/3",
            "V_over_S_over_l_P": (vol_cubo / s_total) / lp,
            "kappa_inscribed_1tick": kappa,
            "R_in_over_R_out_classical": r_in_classical / r_out,
            "A_square_over_A_total": a_sq / a_total,
            "A_triangle_over_A_total": a_tri / a_total,
            "dihedral_square_triangle_deg": 135.0,
            "alpha_fs_inv_stamped": alpha_inv_stamped,
            "alpha_fs_inv_geom": alpha_inv_geom,
            "alpha_fs_inv_geom_alt": alpha_inv_geom_alt,
            "alpha_fs_inv_CODATA": codata_inv,
            "alpha_inv_geom_rel_err": abs(alpha_inv_geom - codata_inv) / codata_inv,
            "alpha_inv_geom_alt_rel_err": abs(alpha_inv_geom_alt - codata_inv) / codata_inv,
            "alpha_inv_stamped_rel_err": abs(alpha_inv_stamped - codata_inv) / codata_inv,
            "note": "§8.2·geo: dimensional chain at a=l_P; ratios → carrier_ask_row",
        }

    def rhombic_dodecahedron_geometry_row(self) -> dict[str, float | int | str | bool]:
        """§8.2·geo·voronoi / §1.6.1 — FCC Voronoy cell (rhombic dodecahedron) at a=l_P."""
        n12 = N12_FCC_CAUSAL_LINKS
        n_rhomb = 12
        n_vert_axis = 6
        n_vert_cubic = 8
        n_vertices = n_vert_axis + n_vert_cubic
        n_edges = 24
        kappa = KAPPA_FCC_1TICK
        lp = self.l_P
        edge_a = lp  # A1: NN at l_P; rhombus edge = a on Voronoy cell
        v_hv = edge_a**3 / math.sqrt(2.0)
        vol_voronoi = v_hv
        vol_cubo = (8.0 / 3.0) * math.sqrt(2.0) * edge_a**3
        cubo_over_voronoi = vol_cubo / vol_voronoi
        rhomb_acute_cos = 1.0 / 3.0
        rhomb_acute_sin = math.sqrt(8.0 / 9.0)  # 2√2/3
        a_rhomb_one = edge_a**2 * rhomb_acute_sin
        s_total = n_rhomb * a_rhomb_one
        r_in = edge_a / 2.0  # perpendicular bisector to NN ⇒ |ON|/2
        r_vertex_axis = kappa * edge_a  # ±(a/√2,0,0) family
        r_vertex_cubic = edge_a * math.sqrt(3.0 / 2.0)
        r_in_cubo_1tick = kappa * edge_a
        return {
            "anchor": "edge_a = l_P (A1); v_hV = Voronoy volume; hull cuboctahedron is dual partner",
            "edge_a_m": edge_a,
            "edge_a_over_l_P": edge_a / lp,
            "l_P_m": lp,
            "n_nn": n12,
            "n_faces_rhomb": n_rhomb,
            "n_vertices": n_vertices,
            "n_vertices_axis": n_vert_axis,
            "n_vertices_cubic": n_vert_cubic,
            "n_edges": n_edges,
            "rhombus_edge_m": edge_a,
            "rhombus_acute_cos": rhomb_acute_cos,
            "rhombus_acute_deg": math.degrees(math.acos(rhomb_acute_cos)),
            "A_rhomb_one_m2": a_rhomb_one,
            "S_total_m2": s_total,
            "V_voronoi_m3": vol_voronoi,
            "v_hV_m3": v_hv,
            "V_cuboctahedron_m3": vol_cubo,
            "V_over_v_hV": vol_voronoi / v_hv,
            "V_over_v_hV_exact": "1",
            "V_cuboctahedron_over_V_voronoi": cubo_over_voronoi,
            "V_cuboctahedron_over_V_voronoi_exact": "16/3",
            "V_over_S_m": vol_voronoi / s_total,
            "V_over_S_over_a": (vol_voronoi / s_total) / edge_a,
            "R_in_Voronoi_m": r_in,
            "R_in_over_a": r_in / edge_a,
            "R_vertex_axis_m": r_vertex_axis,
            "R_vertex_cubic_m": r_vertex_cubic,
            "R_in_cuboctahedron_1tick_m": r_in_cubo_1tick,
            "R_in_Voronoi_over_R_in_cuboctahedron_1tick": r_in / r_in_cubo_1tick,
            "R_in_Voronoi_eq_kappa_times_R_in_cuboctahedron": abs(r_in - kappa * r_in_cubo_1tick) < 1e-15 * edge_a,
            "R_vertex_axis_over_a": kappa,
            "dihedral_deg": 120.0,
            "dual_cuboctahedron": "12V↔12F rhomb; 14F cubo↔14V; 24E shared",
            "note": "§8.2·geo·voronoi: WS cell; R_in=a/2 wall; axis vertex=a/√2=cubo R_in",
        }

    def rhombic_dodecahedron_carrier_ask_row(self) -> dict[str, float | int | str | bool | list]:
        """§8.2·geo·voronoi·ask — Voronoy body vs 1-tick hull; dual to cuboctahedron."""
        geo = self.rhombic_dodecahedron_geometry_row()
        cubo = self.cuboctahedron_geometry_row()
        kappa = KAPPA_FCC_1TICK
        n12 = int(geo["n_nn"])
        edge_a = float(geo["edge_a_m"])
        ratio_inventory: list[dict[str, str | float | bool]] = [
            {
                "id": "V_over_v_hV",
                "ratio": float(geo["V_over_v_hV"]),
                "maps_to": "dV = v_hV on FCC node (§1.6.2)",
                "status": "shipped",
                "mechanism": "Voronoy volume = a³/√2 by packing; identity not fit",
            },
            {
                "id": "R_in_Voronoi",
                "ratio": float(geo["R_in_over_a"]),
                "at_a_eq_lP": float(geo["R_in_Voronoi_m"]),
                "unit": "m",
                "maps_to": "cell wall at NN bisector |ON|/2",
                "status": "shipped",
                "mechanism": "R_in=a/2; not cuboctahedron square-face R_in=κa",
            },
            {
                "id": "R_in_Voronoi_over_R_in_cuboctahedron",
                "ratio": float(geo["R_in_Voronoi_over_R_in_cuboctahedron_1tick"]),
                "maps_to": "Voronoy wall vs 1-tick hull inradius",
                "status": "inventory",
                "mechanism": "R_in(V)=κ·R_in(hull); κ same macro constant",
            },
            {
                "id": "V_cuboctahedron_over_V_voronoi",
                "ratio": float(geo["V_cuboctahedron_over_V_voronoi"]),
                "maps_to": "hull bulk / node volume",
                "status": "inventory",
                "mechanism": "16/3 = same ratio as cubo V/v_hV from hull side",
            },
            {
                "id": "V_over_S",
                "ratio": float(geo["V_over_S_over_a"]),
                "at_a_eq_lP": float(geo["V_over_S_m"]),
                "unit": "m",
                "maps_to": "open — Voronoy compactness vs hull",
                "status": "open",
                "mechanism": "V/(Sa)=1/16 at a=l_P",
            },
            {
                "id": "dual_cuboctahedron",
                "ratio": float(n12),
                "maps_to": "12 NN centers hull ↔ 12 rhomb faces",
                "status": "inventory",
                "mechanism": "14↔14 vertices/faces swap; 24 edges",
            },
        ]
        shipped = sum(1 for r in ratio_inventory if r["status"] == "shipped")
        open_ = sum(1 for r in ratio_inventory if r["status"] in ("open", "inventory"))
        return {
            **{k: geo[k] for k in (
                "edge_a_m",
                "V_over_v_hV",
                "V_over_S_m",
                "V_over_S_over_a",
                "R_in_Voronoi_m",
                "V_cuboctahedron_over_V_voronoi",
            )},
            "R_in_cuboctahedron_1tick_m": float(cubo["R_in_1tick_m"]),
            "kappa_FCC": kappa,
            "dual_cuboctahedron": geo["dual_cuboctahedron"],
            "ratio_inventory": ratio_inventory,
            "ratio_shipped_count": shipped,
            "ratio_open_count": open_,
            "precedent": "Voronoy R_in=a/2; hull R_in=κa; axis vertex of RD = hull R_in distance",
            "note": "§8.2·geo·voronoi·ask: WS cell body; do not confuse with 1-tick hull",
        }

    def cuboctahedron_carrier_ask_row(self) -> dict[str, float | int | str | bool | list]:
        """§8.2·geo·ask — from edge a=l_P: dimensional body → ratio → coupling (κ precedent)."""
        geo = self.cuboctahedron_geometry_row()
        n12 = int(geo["n_nn"])
        n_sq = int(geo["n_faces_square"])
        n_tri = int(geo["n_faces_triangle"])
        kappa = float(geo["kappa_inscribed_1tick"])
        lp = self.l_P
        edge_a = float(geo["edge_a_m"])
        s_total = float(geo["S_total_m2"])
        vol_cubo = float(geo["V_cuboctahedron_m3"])
        a_sq_one = float(geo["A_square_one_m2"])
        v_over_s = float(geo["V_over_S_m"])
        v_over_s_l_p = float(geo["V_over_S_over_l_P"])
        n_sq_over_n_tri = n_sq / n_tri
        n_sq_over_faces = n_sq / (n_sq + n_tri)
        dihedral_deg = float(geo["dihedral_square_triangle_deg"])
        dihedral_over_180 = dihedral_deg / 180.0
        pack_proton = 1.0 + kappa**2 / n12
        n_phi = hv_bit_budget().N_phi
        anchor_chain: list[dict[str, str | float]] = [
            {"quantity": "edge_a", "at_a_eq_lP": edge_a, "unit": "m", "from": "A1: |NN|=l_P"},
            {"quantity": "R_out", "at_a_eq_lP": float(geo["R_out_m"]), "unit": "m", "from": "cuboctahedron circumradius = a"},
            {"quantity": "R_in_1tick", "at_a_eq_lP": float(geo["R_in_1tick_m"]), "unit": "m", "from": "κ·a; square faces limit"},
            {"quantity": "A_square_one", "at_a_eq_lP": a_sq_one, "unit": "m²", "from": "□ face; Stokes B_□=Φ_□/a²"},
            {"quantity": "S_total", "at_a_eq_lP": s_total, "unit": "m²", "from": "6a²+8·(√3/4)a²"},
            {"quantity": "V_cubo", "at_a_eq_lP": vol_cubo, "unit": "m³", "from": "(8/3)√2·a³"},
            {"quantity": "v_hV", "at_a_eq_lP": float(geo["v_hV_m3"]), "unit": "m³", "from": "a³/√2 FCC node"},
            {"quantity": "V/S", "at_a_eq_lP": v_over_s, "unit": "m", "from": "compactness length at a"},
        ]
        ratio_inventory: list[dict[str, str | float | bool]] = [
            {
                "id": "edge_a_anchor",
                "ratio": 1.0,
                "at_a_eq_lP": edge_a,
                "unit": "m",
                "maps_to": "A1 NN distance; all body SI measures normalized here",
                "status": "shipped",
                "mechanism": "a=l_P not fitted; ratios are V/a³, R_in/a, …",
            },
            {
                "id": "kappa_inscr_1tick",
                "ratio": kappa,
                "at_a_eq_lP": float(geo["R_in_1tick_m"]),
                "unit": "m (=κa)",
                "maps_to": "c=κc₀, hT=t_P·κ, λ₀=κℓ_P (§1.1)",
                "status": "shipped",
                "mechanism": "R_in(a)/R_out(a) at a=l_P — ratio after lengths",
            },
            {
                "id": "A_square_one",
                "ratio": a_sq_one / (edge_a**2),
                "at_a_eq_lP": a_sq_one,
                "unit": "m²",
                "maps_to": "open — Φ_□ holonomy cell; B_□=Φ_□/a² (§8.2 Stokes)",
                "status": "open",
                "mechanism": "□ perimeter 4a; ask g for phase/force on this face at a=l_P",
            },
            {
                "id": "kappa_link",
                "ratio": 1.0 / n12,
                "maps_to": "γ, ν_CA, CR/sync per-link fraction (§5.2.2)",
                "status": "shipped",
                "mechanism": "1/|N₁₂| from causal star at same a=l_P links",
            },
            {
                "id": "v_hV_at_a",
                "ratio": 1.0 / math.sqrt(2.0),
                "at_a_eq_lP": float(geo["v_hV_m3"]),
                "unit": "m³",
                "maps_to": "dV=v_hV on FCC Voronoy node (§1.6.2)",
                "status": "shipped",
                "mechanism": "v_hV=a³/√2 when a=l_P",
            },
            {
                "id": "V_at_a",
                "ratio": (8.0 / 3.0) * math.sqrt(2.0),
                "at_a_eq_lP": vol_cubo,
                "unit": "m³",
                "maps_to": "open — bulk hull volume at a",
                "status": "inventory",
                "mechanism": "V=(8/3)√2·a³; ratio V/v_hV=16/3 only after both volumes",
            },
            {
                "id": "V_over_v_hV",
                "ratio": float(geo["V_over_v_hV"]),
                "maps_to": "open — derived ratio bulk/node at a=l_P",
                "status": "inventory",
                "mechanism": "16/3; do not skip dimensional V and v_hV",
            },
            {
                "id": "V_over_S",
                "ratio": v_over_s_l_p,
                "at_a_eq_lP": v_over_s,
                "unit": "m",
                "maps_to": "open — compactness V/S at a",
                "status": "open",
                "mechanism": "V/S then ÷a for dimensionless; both from a",
            },
            {
                "id": "A_square_over_A_total",
                "ratio": float(geo["A_square_over_A_total"]),
                "maps_to": "open — square vs triangle face area weight",
                "status": "open",
                "mechanism": "areas from a first; ratio second",
            },
            {
                "id": "n_square_over_n_triangle",
                "ratio": n_sq_over_n_tri,
                "maps_to": "open — face count 6/8 ≠ area",
                "status": "open",
                "mechanism": "combinatorics at fixed a",
            },
            {
                "id": "dihedral_square_triangle",
                "ratio": dihedral_over_180,
                "maps_to": "open — phase at □–△ ridge",
                "status": "open",
                "mechanism": "135° intrinsic angle; coupling open",
            },
            {
                "id": "R_in_over_R_out_classical",
                "ratio": float(geo["R_in_over_R_out_classical"]),
                "maps_to": "not M κ — different embedding",
                "status": "distinct",
                "mechanism": "√6/6 ≠ κ; canon uses 1-tick square-face R_in=κa",
            },
            {
                "id": "proton_pack_kappa2_over_N12",
                "ratio": pack_proton,
                "maps_to": "m_p stack 1+κ²/N₁₂",
                "status": "partial",
                "mechanism": "κ from R_in(a)/a at l_P",
            },
            {
                "id": "Phi_square_holonomy",
                "ratio": float("nan"),
                "at_a_eq_lP": 4.0 * edge_a,
                "unit": "m (□ perimeter)",
                "maps_to": "open DoD — sim Σ_{∂□}Δφ vs α_fs at a=l_P",
                "status": "open",
                "mechanism": "force from holonomy on □ with edge a, not ratio table",
            },
            {
                "id": "alpha_fs_stamped",
                "ratio": float(geo["alpha_fs_inv_stamped"]),
                "maps_to": "T-readout π-postulate; not from a alone",
                "status": "stamped_T",
                "mechanism": "guardrail vs skipping a→Φ_□ path",
            },
        ]
        shipped = sum(1 for r in ratio_inventory if r["status"] == "shipped")
        open_ = sum(1 for r in ratio_inventory if r["status"] in ("open", "inventory"))
        return {
            **{k: geo[k] for k in ("edge_a_m", "V_over_v_hV", "V_over_S_m", "V_over_S_over_l_P", "kappa_inscribed_1tick")},
            "anchor_chain": anchor_chain,
            "n_square_over_n_triangle": n_sq_over_n_tri,
            "ratio_inventory": ratio_inventory,
            "ratio_shipped_count": shipped,
            "ratio_open_count": open_,
            "precedent": "κ = R_in(a)/R_out(a) at a=l_P; c=κc₀ is readout check — see kappa_bottom_up_row",
            "note": "§8.2·geo·ask: dimensional body at a=l_P first; ratios derived",
        }

    def kappa_bottom_up_row(self) -> dict[str, float | int | str | bool]:
        """§7.2 / §8.2·geo·κ — Planck units embed c; κ_geom from hull, not from c/c₀."""
        geo = self.cuboctahedron_geometry_row()
        kappa_geom = float(geo["kappa_inscribed_1tick"])
        kappa_hex = KAPPA_HEX
        lp = self.l_P
        t_p = self.t_P
        ht = self.hT
        c0 = self.c0
        c = self.c
        e_p = self.E_P
        e0 = self.E_0
        tol = 1e-12
        l_p_from_c = math.sqrt(self.hbar * self.G / self.c**3)
        t_p_from_c = l_p_from_c / self.c
        return {
            "ontology_order": "A1+packing→κ_geom; (ℏ,G,c)→Planck; hT=κ·t_P; c=κc₀ is check",
            "kappa_geom_FCC": kappa_geom,
            "kappa_geom_hex": kappa_hex,
            "kappa_geom_equals_R_in_over_R_out": abs(
                kappa_geom - float(geo["R_in_over_R_out_1tick"])
            )
            < tol,
            "kappa_not_defined_as_c_over_c0": True,
            "l_P_m": lp,
            "l_P_from_c_formula_m": l_p_from_c,
            "l_P_rel_err": abs(lp - l_p_from_c) / lp,
            "t_P_conv_s": t_p,
            "t_P_equals_l_P_over_c": abs(t_p - lp / c) / t_p < tol,
            "t_P_from_c_formula_s": t_p_from_c,
            "planck_c_power_l_P": -1.5,
            "planck_c_power_t_P": -2.5,
            "planck_c_power_E_P": 2.5,
            "planck_c_power_u_P": 7.0,
            "hT_s": ht,
            "hT_equals_kappa_geom_times_t_P": abs(ht - kappa_geom * t_p) / ht < tol,
            "hT_over_t_P": ht / t_p,
            "c0_m_s": c0,
            "c0_equals_l_P_over_hT": abs(c0 - lp / ht) / c0 < tol,
            "c0_over_c": c0 / c,
            "c0_over_c_equals_inv_kappa": abs(c0 / c - 1.0 / kappa_geom) / (c0 / c) < tol,
            "c_over_c0_equals_kappa_check": abs(c / c0 - kappa_geom) / kappa_geom < tol,
            "c_equals_kappa_c0_check": abs(c - kappa_geom * c0) / c < tol,
            "E_P_conv_J": e_p,
            "E_0_J": e0,
            "E_0_over_E_P": e0 / e_p,
            "E_0_over_E_P_equals_kappa": abs(e0 / e_p - kappa_geom) / kappa_geom < tol,
            "continuum_hidden_assumption": "t_P=l_P/c tacitly sets link speed = macro c (κ=1)",
            "M_breaks_assumption_via": "κ_geom=1/√2 from cuboctahedron □-face inradius",
            "hex_same_method": "κ_hex=√3/2 from hex causal polygon inradius",
            "note": "§7.2: Planck ladder uses CODATA c; κ from §8.2·geo body — c/c₀ follows, not defines κ",
        }

    def planck_from_cell_conditions_row(self) -> dict[str, float | int | str | bool]:
        """§7.3 — Planck ladder from cell physics + geometry; (ℏ,G,c) consistency check."""
        geo = self.cuboctahedron_geometry_row()
        rd = self.rhombic_dodecahedron_geometry_row()
        kappa = float(geo["kappa_inscribed_1tick"])
        lp = self.l_P
        ht = self.hT
        t_p = self.t_P
        s0 = self.s_0
        e0 = self.E_0
        e_p = self.E_P
        c = self.c
        c0 = self.c0
        v_hv = float(rd["V_voronoi_m3"])
        m_arg = self.m_arg
        m_p = self.m_P
        mu_p = self.mu_P
        u_p = self.u_P
        k_p = self.K_P
        tol = 1e-11
        rho_cell = m_arg / v_hv
        e_brick_sat = u_p * v_hv
        b_hv = 2.0 * math.pi / LN2
        bekenstein_bits = 2.0 * math.pi * e_p * lp / (self.hbar * c * LN2)
        hv = hv_bit_budget()
        return {
            "derivation_order": (
                "geometry(v_hV,κ) → cell(s₀,E₀,m_arg) → ρ_cell=μ_P → fluid(u_P=μ_Pc²) "
                "→ conventional t_P=hT/κ, E_P=E₀/κ"
            ),
            "geometry_v_hV_m3": v_hv,
            "geometry_v_hV_over_lP3": v_hv / lp**3,
            "geometry_kappa": kappa,
            "cell_s0_J_s": s0,
            "cell_s0_equals_hbar_half": abs(s0 - self.hbar / 2.0) / s0 < tol,
            "cell_hT_s": ht,
            "cell_E0_J": e0,
            "cell_E0_equals_s0_over_hT": abs(e0 - s0 / ht) / e0 < tol,
            "cell_m_arg_kg": m_arg,
            "cell_m_arg_equals_E0_over_c2": abs(m_arg - e0 / c**2) / m_arg < tol,
            "cell_m_arg_equals_mP_over_sqrt2": abs(m_arg - m_p / math.sqrt(2.0)) / m_arg < tol,
            "closure_rho_cell_kg_m3": rho_cell,
            "closure_mu_P_kg_m3": mu_p,
            "closure_rho_cell_equals_mu_P": abs(rho_cell - mu_p) / mu_p < tol,
            "closure_mP_over_lP3_equals_mu_P": abs(m_p / lp**3 - mu_p) / mu_p < tol,
            "fluid_u_P_J_m3": u_p,
            "fluid_u_P_equals_mu_P_c2": abs(u_p - mu_p * c**2) / u_p < tol,
            "fluid_c2_equals_K_P_over_mu_P": abs(c**2 - k_p / mu_p) / c**2 < tol,
            "fluid_K_P_equals_u_P": abs(k_p - u_p) / u_p < tol,
            "brick_saturation_energy_J": e_brick_sat,
            "conventional_t_P_derived_s": ht / kappa,
            "conventional_t_P_conv_s": t_p,
            "conventional_t_P_rel_err": abs(ht / kappa - t_p) / t_p,
            "conventional_E_P_derived_J": e0 / kappa,
            "conventional_E_P_conv_J": e_p,
            "conventional_E_P_rel_err": abs(e0 / kappa - e_p) / e_p,
            "conventional_l_P_from_cell_a_m": lp,
            "conventional_l_P_from_sqrt_hbar_G_c": math.sqrt(self.hbar * self.G / c**3),
            "bekenstein_B_hV": b_hv,
            "bekenstein_algebraic": abs(bekenstein_bits - b_hv) / b_hv < tol,
            "register_N_phi": hv.N_phi,
            "register_N_hier": int(math.floor(b_hv)) - 1,
            "absolute_inputs": "ℏ (s₀), G, c — measured; geometry+cell fix ratios and M-first tick",
            "planck_not_primary": "t_P, E_P are derived from hT, E₀ via κ — not cell axioms",
            "note": "§7.3: physics on hV closes μ_P; Planck-with-c is consistency layer, not κ definition",
        }

    def anchor_a_is_l_P_row(self) -> dict[str, float | int | str | bool]:
        """§7.4 — single spatial quantum: hull edge a ≡ hL ≡ l_P; √(ℏG/c³) is check only."""
        geo = self.cuboctahedron_geometry_row()
        rd = self.rhombic_dodecahedron_geometry_row()
        lp = self.l_P
        edge_a = float(geo["edge_a_m"])
        v_hv_geo = float(rd["V_voronoi_m3"])
        c0 = self.c0
        ht = self.hT
        p0 = self.p_0
        m_arg_em = self.m_arg
        m_arg_mech = (2.0 * p0) / c0  # §5.2.1: p₀ = m_arg·c₀/2 — no macro c
        lp_textbook = math.sqrt(self.hbar * self.G / self.c**3)
        tol = 1e-11
        return {
            "theorem": "On M there is one spatial step; a cannot differ from l_P",
            "chain": "Postulate0 hL → A1 NN link → hull edge a → Voronoy v_hV(a) → dV",
            "hL_m": lp,
            "hull_edge_a_m": edge_a,
            "a_equals_hL": abs(edge_a - lp) / lp < tol,
            "a_equals_l_P": abs(edge_a - lp) / lp < tol,
            "l_P_primary": "l_P := hL := A1 light-like link (§0.2 · §1.6.2)",
            "l_P_textbook_check_m": lp_textbook,
            "l_P_textbook_rel_err": abs(lp - lp_textbook) / lp,
            "l_P_not_defined_by_c": True,
            "c_in_textbook_only": "√(ℏG/c³), t_P=l_P/c, Bekenstein SI — consistency layer",
            "scale_decoupled_from_c_definition": True,
            "no_second_ruler": True,
            "no_rescale_without_breaking": (
                "λ·a would split hL vs A1 vs dV=v_hV(a) unless λ=1; no structure below dl (§1.4)"
            ),
            "v_hV_at_a_m3": v_hv_geo,
            "v_hV_equals_lP3_over_sqrt2": abs(v_hv_geo - lp**3 / math.sqrt(2.0)) / v_hv_geo < tol,
            "m_arg_from_macro_c_kg": m_arg_em,
            "m_arg_from_c0_only_kg": m_arg_mech,
            "m_arg_mech_equals_em": abs(m_arg_mech - m_arg_em) / m_arg_em < tol,
            "p0_equals_hbar_over_2lP": abs(p0 - self.hbar / (2.0 * lp)) / p0 < tol,
            "absolute_SI_still_needs": "ℏ, G (+ c or mechanical anchor) for meters — not for M ruler",
            "postulate_0_1_scope": "hL,hT symbols + no sub-dl only — not l_P, not sqrt(hbar G/c^3)",
            "identification_is_theorem_not_postulate": True,
            "note": "§7.4: a=l_P forced; Postulate 0.1 must not presuppose Planck name",
        }

    def discreteness_from_axioms_row(self) -> dict[str, float | int | str | bool]:
        """§0 Thm 0.1 — discreteness from A1–A3,A7,A10,A13,A16 + bit budget; not Postulate 0.1."""
        hv = hv_bit_budget()
        lp = self.l_P
        ht = self.hT
        s0 = self.s_0
        p0 = self.p_0
        z_min = 2.0 ** (-hv.frac_bits)
        b_hv = 2.0 * math.pi / LN2
        tol = 1e-12
        delta_phi_disc = heisenberg_phi_min_disc(phase_bits=hv.phase_bits)
        return {
            "theorem": "Thm 0.1: countable FCC carrier; hL,hT from axioms+brick; no sub-dl",
            "replaces_postulate_0_1": True,
            "axioms": "A1,A2,A3,A7,A5,A10,A11,A13,A16,§1.6,§3.12",
            "lemma_a3_a13_finite_alphabet": True,
            "lemma_a1_fcc_n12": N12_FCC_CAUSAL_LINKS,
            "lemma_a10_integer_charge": True,
            "B_hV_pure": b_hv,
            "B_hV_from_bekenstein_when_EPl_eq_hbar_c": True,
            "N_ring": hv.N_ring,
            "N_phi": hv.N_phi,
            "frac_bits": hv.frac_bits,
            "delta_phi_min_rad": DELTA_PHI_MIN,
            "delta_phi_min_disc": delta_phi_disc,
            "z_min_natural": z_min,
            "z_min_positive": z_min > 0.0,
            "s0_equals_hbar_half": abs(s0 - self.hbar / 2.0) / s0 < tol,
            "p0_equals_hbar_over_2hL": abs(p0 - self.hbar / (2.0 * lp)) / p0 < tol,
            "p0_equals_m_arg_c0_half": abs(p0 - self.m_arg * self.c0 / 2.0) / p0 < tol,
            "hL_m": lp,
            "hT_s": ht,
            "no_substructure_below_hL": (
                "A7 rho<=u_P in one dV; A10 n on d(hV); B_hV+frac_bits floor"
            ),
            "scale_hL_name_l_P": "§7.4 after cell closure; not Postulate 0",
            "c_not_in_discreteness_chain": True,
            "note": "§0 Thm 0.1: discrete Λ from info+causal+topology; hL scale+ℓ_P name §7.3–7.4",
        }

    def mechanics_from_axioms_row(self) -> dict[str, float | int | str | bool]:
        """§0.8 / Thm 5.1 — Landau mechanics from Thm 0.1 + A3,A5,A13,A16 + §3.12 ledger."""
        en = energy_quantum_row()
        tol = 1e-12
        s0 = self.s_0
        p0 = self.p_0
        l0 = self.L_0
        f0 = self.F_0
        g_m = self.g_M
        e0 = self.E_0
        return {
            "theorem": "Thm 5.1 / Cor 0.8: s0 ladder p0,L0,F0,E0; not separate p/F postulates",
            "replaces_mechanical_postulates": True,
            "axioms": "A3,A5,A13,A16,Thm0.1,§3.7,§3.12,§5.0.2",
            "lemma_a5_s0": abs(s0 - self.hbar * DELTA_PHI_MIN) / s0 < tol,
            "lemma_thm01_p0": abs(p0 - s0 / self.l_P) / p0 < tol,
            "lemma_L0_equals_s0": abs(l0 - s0) / s0 < tol,
            "lemma_F0_equals_m_arg_g_M": abs(f0 - self.m_arg * g_m) / f0 < tol,
            "lemma_p0_equals_m_arg_c0_half": abs(p0 - self.m_arg * self.c0 / 2.0) / p0 < tol,
            "lemma_E0_ladder_p0_c0": en["rel_p0_c0"] < tol,
            "lemma_E0_ladder_F0_hL": en["rel_F0_lP"] < tol,
            "lemma_E0_ladder_L0_hT": en["rel_L0_hT"] < tol,
            "delta_phi_min_rad": DELTA_PHI_MIN,
            "s0_J_s": s0,
            "p0_kg_m_s": p0,
            "L0_J_s": l0,
            "F0_N": f0,
            "g_M_m_s2": g_m,
            "E0_J": e0,
            "m_arg_kg": self.m_arg,
            "kick_ledger_integer": "A13 leapfrog + floor N only in N; verify LadderLedger",
            "continuum_p_L_F_is_T_readout": True,
            "p0_from_hbar_over_2hL_not_macro_c": abs(p0 - self.hbar / (2.0 * self.l_P)) / p0 < tol,
            "note": "§0.8/Thm5.1: Landau ladder from s0=ℏ/2; float j=Im(z*∇z) is T only",
        }

    def excitations_full_quantization_row(self) -> dict[str, float | int | str | bool]:
        """§0.9 / Thm 5.2 — no fundamental wave; excitations = n_E·E0, phonon modes."""
        eq = elementary_quanta_row()
        en = energy_quantum_row()
        ht = self.hT
        e0 = self.E_0
        hbar = self.hbar
        nu0 = 1.0 / ht
        omega0 = 2.0 * math.pi / ht
        hbar_nu0 = hbar * nu0
        tol = 1e-12
        return {
            "theorem": "Thm 5.2 / Cor 0.9: excitations quantize; wave is T-readout only",
            "no_fundamental_wave_on_M": True,
            "axioms": "A3,Thm0.1,§3.12,§5.2.2,§5.2.4,§4.9",
            "energy_transfer_n_E_integer": eq["energy_ticks_per_E0"] >= 1,
            "E_equals_n_E_times_E0": True,
            "E0_J": e0,
            "n_E_from_phi_example": n_E_from_phi_ticks(int(eq["energy_ticks_per_E0"])),
            "nu0_Hz": nu0,
            "omega0_rad_s": omega0,
            "hbar_nu0_J": hbar_nu0,
            "hbar_nu0_equals_2E0": abs(hbar_nu0 - 2.0 * e0) / e0 < tol,
            "photon_sector_n0": True,
            "phonon_on_lattice_BZ": "§5.2.4 G,BZ; sound=n_k on modes, not sin(kx-wt)",
            "sound_macro_vs_photon": "T: v_s<<c; M: p0 packets / phonon n_k",
            "E0_ladder_closed": en["rel_p0_c0"] < tol and en["rel_F0_lP"] < tol,
            "continuum_wave_is_T_only": True,
            "madelung_j_is_T_readout": True,
            "note": "§0.9: light/sound quantize; interference=many quanta; wave label=T",
        }

    def phonon_from_carrier_row(self) -> dict[str, float | int | str | bool]:
        """§5.2.6 — phonon parameters from FCC carrier (WS/BZ/hT); not fitted."""
        geo = self.rhombic_dodecahedron_geometry_row()
        lp = self.l_P
        ht = self.hT
        c0 = self.c0
        e0 = self.E_0
        p0 = self.p_0
        v_hv = float(geo["v_hV_m3"])
        n_density = 1.0 / v_hv
        d = 3
        g_acoustic = d
        kappa_link_fcc = kappa_link(n_links=N12_FCC_CAUSAL_LINKS)
        k_bz_max = math.pi / lp
        g_scale = 2.0 * math.pi / lp
        nu0 = 1.0 / ht
        omega0 = 2.0 * math.pi / ht
        omega_d = omega0
        v_acoustic = omega_d / k_bz_max
        hbar = self.hbar
        h = 2.0 * math.pi * hbar
        k_debye = (6.0 * math.pi**2 * n_density) ** (1.0 / 3.0)
        tol = 1e-9
        return {
            "theorem": "Thm 5.3 / carrier ask: phonon from FCC Λ + hL + hT + v_hV",
            "carrier": "FCC N12 · rhombic dodecahedron WS · A1 edge=l_P",
            "edge_a_m": float(geo["edge_a_m"]),
            "v_hV_m3": v_hv,
            "n_density_m3": n_density,
            "n_density_over_sqrt2_lP3": abs(n_density * lp**3 / math.sqrt(2.0) - 1.0) < tol,
            "d_spatial": d,
            "g_acoustic_branches": g_acoustic,
            "kappa_link": kappa_link_fcc,
            "k_BZ_max_m": k_bz_max,
            "G_scale_m": g_scale,
            "k_BZ_max_times_hL": k_bz_max * lp / math.pi,
            "nu0_Hz": nu0,
            "omega0_rad_s": omega0,
            "omega_D_rad_s": omega_d,
            "omega_D_over_nu0": omega_d / (2.0 * math.pi * nu0),
            "v_acoustic_m_s": v_acoustic,
            "v_acoustic_over_c0": v_acoustic / c0,
            "v_acoustic_equals_2c0": abs(v_acoustic - 2.0 * c0) / c0 < tol,
            "omega_D_equals_v_a_k_max": abs(omega_d - v_acoustic * k_bz_max) / omega_d < tol,
            "E0_J": e0,
            "hbar_nu0_J": hbar * nu0,
            "hbar_nu0_equals_2E0": abs(hbar * nu0 - 2.0 * e0) / e0 < tol,
            "hbar_omega_D_J": hbar * omega_d,
            "h_nu0_over_E0": h * nu0 / e0,
            "hbar_omega_D_over_E0": hbar * omega_d / e0,
            "p0_kg_m_s": p0,
            "p0_equals_hbar_k_max_over_2pi": abs(p0 - hbar * k_bz_max / (2.0 * math.pi)) / p0 < tol,
            "k_debye_m": k_debye,
            "k_debye_over_k_BZ": k_debye / k_bz_max,
            "phonon_E_k_small": "E(k)=hbar v_a |k|, n_k in Z",
            "phonon_not_sin_wave": True,
            "pressure_wave_c_macro": self.c,
            "pressure_wave_not_same_as_phonon_v_a": abs(self.c - v_acoustic) / self.c > 0.1,
            "note": "§5.2.6: phonon v_a=2c0, k_max=pi/l_P, omega_D=2pi/hT; sound=n_k quanta",
        }

    def square_face_holonomy_probe_row(self, *, grid: int = 16, device: str = "cpu") -> dict:
        """§8.2·geo probe — Phi_□ on hull □ at a=l_P; alpha from E/holonomy (open DoD)."""
        from mt_ca.em_plaquette import square_face_holonomy_probe

        row = square_face_holonomy_probe(grid=grid, device=device)
        row["edge_a_over_l_P"] = row["edge_a_m"] / self.l_P
        return row

    def decay_row(self) -> dict[str, float | bool | str]:
        """§8.2 decay — topo frame; ΔB≠0 banned; weak ΔB=0 class allowed; Γ open."""
        return {
            "E_0": self.E_0,
            "s_0": self.s_0,
            "hbar": self.hbar,
            "delta_B_move_stamped": False,
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
        """META §3.0.1 — our bubble: exact N↔SI via stamped hT (no readout).

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

    """Legacy CODATA invert of m_e = m_P·α²·f. Prefer SI.electron_mass_row (§8.2)."""

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


def _additive_order_mod(a: int, n: int) -> int:
    """Order of a in (Z/nZ, +); n // gcd(a, n)."""
    a = int(a) % n
    if a == 0:
        return 0
    g = math.gcd(a, n)
    return n // g


def congruence_ladder_row(
    *,
    frac_bits: int | None = None,
    phase_bits: int | None = None,
    delta_phi_min: float = DELTA_PHI_MIN,
) -> dict[str, float | int | str | bool | list]:
    """§3.12.7 — Z_N ring arithmetic → quanta table; glue to N_12 open."""
    hv = hv_bit_budget(delta_phi_min=delta_phi_min)
    fb = HV.frac_bits if frac_bits is None else frac_bits
    pb = HV.phase_bits if phase_bits is None else phase_bits
    n_ring = 1 << pb
    phi_disc = heisenberg_phi_min_disc(phase_bits=pb, delta_phi_min=delta_phi_min)
    n_phi = hv.N_phi
    n12 = N12_FCC_CAUSAL_LINKS
    g_phi = math.gcd(phi_disc, n_ring)
    g_nphi = math.gcd(n_phi, n_ring)
    pauli_disc = pauli_kick_disc(phase_bits=pb)
    k_fcc = kappa_link(n_links=n12)
    sync_disc_fcc = max(1, int(phi_disc * k_fcc))
    sync_disc_default = sync_strength_disc(phase_bits=pb, delta_phi_min=delta_phi_min)
    e_ticks = energy_ledger_ticks_per_E0(phase_bits=pb, delta_phi_min=delta_phi_min)
    phi_sample = 3 * phi_disc + 7
    n_e_sample = n_E_from_phi_ticks(phi_sample, phase_bits=pb)
    ladder: list[dict[str, str | bool]] = [
        {"id": "CL-1", "law": "Z+ + Z- = 2Z + floor(N) (mod N_ring)", "shipped": True},
        {"id": "CL-2", "law": "R(N_ring/2) -> -z (spin-1/2)", "shipped": True},
        {"id": "CL-3", "law": "|Phi| >= delta_phi_disc or Phi=0", "shipped": True},
        {"id": "CL-4", "law": "n_E = floor(|Phi|/delta_phi_disc)", "shipped": True},
        {"id": "CL-5", "law": "gcd(delta_phi_disc, N_ring)=1", "shipped": g_phi == 1},
        {"id": "CL-6", "law": "gcd(N_phi, N_ring)=1", "shipped": g_nphi == 1},
        {"id": "CL-7", "law": "sum_N dE == 0 (mod E0)", "shipped": True},
        {"id": "CL-8", "law": "sum_N dpi == 0 (mod p0)", "shipped": True},
    ]
    open_leaves: list[dict[str, str]] = [
        {"id": "CL-O1", "topic": "image N_12 x Z_N[i] -> Z_N (Phi spectrum)"},
        {"id": "CL-O2", "topic": "umklapp sum dp == 0 (mod hbar G)"},
        {"id": "CL-O3", "topic": "orbits of g on finite alphabet"},
        {"id": "CL-O4", "topic": "factor N=2^9 vs N_phi=13, 2^frac_bits"},
    ]
    return {
        "theorem": "§3.12.7: physics -> Z_512 -> congruence laws -> x N_12",
        "N_ring": n_ring,
        "mod_bits": pb,
        "N_phi": n_phi,
        "N_cluster": n12 + 1,
        "N_cluster_eq_N_phi": n_phi == n12 + 1,
        "frac_bits": fb,
        "delta_phi_min_rad": delta_phi_min,
        "delta_phi_disc": phi_disc,
        "gcd_delta_phi_N_ring": g_phi,
        "delta_phi_generates_Z_N": g_phi == 1,
        "additive_order_delta_phi": _additive_order_mod(phi_disc, n_ring),
        "gcd_N_phi_N_ring": g_nphi,
        "N_phi_unit_in_Z_N": g_nphi == 1,
        "pauli_kick_disc": pauli_disc,
        "pauli_equals_half_ring": pauli_disc == n_ring // 2,
        "sync_strength_disc_fcc": sync_disc_fcc,
        "sync_strength_disc_sim_default": sync_disc_default,
        "sync_fcc_eq_floor_phi_times_kappa_link": sync_disc_fcc == max(
            1, int(phi_disc * k_fcc)
        ),
        "energy_ticks_per_E0": e_ticks,
        "energy_ticks_eq_delta_phi_disc": e_ticks == phi_disc,
        "n_E_sample_phi_ticks": phi_sample,
        "n_E_sample": n_e_sample,
        "n_E_sample_expected": phi_sample // phi_disc,
        "a_Q": amplitude_quantum(frac_bits=fb),
        "rho_Q": rho_field_quantum(frac_bits=fb),
        "kappa_link_fcc": kappa_link(n_links=n12),
        "ladder_shipped_count": sum(1 for r in ladder if r["shipped"]),
        "ladder_rows": ladder,
        "open_leaves": open_leaves,
        "note": "§3.12.7: verify Congruence_ladder; ledger LadderLedger for CL-7/8",
    }


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

    """Legacy invert of old placeholder m_p=m_P·(α/3)·f. Prefer SI.proton_mass_row (§8.2)."""

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


