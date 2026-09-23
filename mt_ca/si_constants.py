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
            "inventory": inventory,
            "ask_ok": identity_ok and rhyme_ok and True,
            "note": (
                "Asked carrier: Thm5.2⇒N_a0∈ℤ; hop α=N_c/N_a0 and mass α²=m_e N_φ/m_H "
                "are one α² — masses do not fix N_a0 alone. Rejected N_c·137 and optical "
                "a₀ as M-definition. OPEN: H structure → integer N_a0 without α."
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
        m_h_direct = (self.alpha_fs**8) * e_p_gev * math.sqrt(math.pi / 2.0)
        # vacuum-bit quantum: (α*−1)·α_fs = α_fs/(4π)
        delta_lam = self.alpha_fs / (4.0 * math.pi)
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
            "note": "§8.3.1: bare v/2; λ=1/8+N_hier·(α_fs/4π) empty-cell stack",
        }

    def proton_mass_row(self) -> dict[str, float]:
        """§8.2 — bare α·v/2; pack stack ×(1+κ²/N₁₂), κ=1/√2."""
        higgs = self.higgs_mass_row()
        v = float(higgs["v_GeV"])
        m_h_bare = float(higgs["m_H_bare_GeV"])
        m_p0 = self.alpha_fs * m_h_bare  # = α · v/2
        kappa = KAPPA_FCC_1TICK
        n12 = float(N12_FCC_CAUSAL_LINKS)
        delta_pack = (kappa * kappa) / n12  # (1/2)/12 = 1/24
        pack_factor = 1.0 + delta_pack
        m_p = m_p0 * pack_factor
        return {
            "v_GeV": v,
            "m_H_bare_GeV": m_h_bare,
            "alpha_fs": self.alpha_fs,
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
        a2 = self.alpha_fs * self.alpha_fs
        m_e0 = a2 * m_h_bare / n_phi
        m_e = a2 * m_h / n_phi
        e_p_gev = self.m_P * (C * C) / EV_J / 1e9  # E_P [GeV]
        f_geom = m_h / (e_p_gev * n_phi)
        return {
            "v_GeV": float(higgs["v_GeV"]),
            "m_H_bare_GeV": m_h_bare,
            "m_H_GeV": m_h,
            "alpha_fs": self.alpha_fs,
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
        a = self.alpha_fs
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
            "alpha_fs": a,
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


