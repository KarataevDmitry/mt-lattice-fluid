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


HV = hv_bit_budget()

# §8.2·α·nF·Thm — force seats on one charged FCC core (not a free fit).
N_HIER_CHANNELS = int(HV.mod_bits) - 1  # ⌊B_hV⌋−1; B_hV=2π/ln2 → ⌊…⌋−1=8 (occupancy bit out)
M_FORCE_SEATS = 1 + N12_FCC_CAUSAL_LINKS * N_HIER_CHANNELS  # = 97
D_SOFT = N4_CAUSAL_LINKS + 3  # von Neumann cross + SU(2) Pauli = 7
U_SOFT = (D_SOFT + 1) / D_SOFT  # = 8/7 = 1/(1−κ⁶)


def alpha_from_fundamentals(
    *,
    kappa: float = KAPPA_FCC_1TICK,
    m: int = M_FORCE_SEATS,
    d: int = D_SOFT,
    u: float = U_SOFT,
) -> float:
    """Structural α — only carrier fundamentals (§8.2·U0). No lab / π."""
    m_f = float(m)
    d_f = float(d)
    return (m_f * m_f) * kappa * (d_f * m_f + kappa) / (
        d_f * m_f**4 - m_f * kappa**3 - u
    )


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
        "alpha_fs_inv": 1.0 / alpha_from_fundamentals(),
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
        "alpha_fs_inv": 1.0 / alpha_from_fundamentals(),
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



def lepton_geometry_factor(m_e: float | None = None) -> float:

    """Legacy CODATA invert of m_e = m_P·α²·f. Prefer SI.electron_mass_row (§8.2)."""

    m_e = m_e if m_e is not None else SI.m_e_CODATA

    return m_e / (SI.m_P * SI.alpha_fs**2)


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

    """Legacy invert of old placeholder m_p=m_P·(α/3)·f. Prefer SI.proton_mass_row (§8.2)."""

    a = alpha_fs if alpha_fs is not None else SI.alpha_fs

    return m_p / (SI.m_P * (a / 3.0))


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


from mt_ca.si_alpha_rows import SIAlphaRows
from mt_ca.si_floor1_rows import SIFloor1Rows
from mt_ca.si_units_rows import SIUnitsRows
from mt_ca.si_carrier_rows import SICarrierRows
from mt_ca.si_sm_rows import SISmRows


@dataclass(frozen=True)
class SIConstants(SIAlphaRows, SIFloor1Rows, SIUnitsRows, SICarrierRows, SISmRows):

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
    def alpha_preferred(self) -> float:
        """Structural alpha from carrier fundamentals (sec 8.2 U0)."""
        return alpha_from_fundamentals()

    @property
    def alpha_fs(self) -> float:
        """alpha — alias of alpha_preferred (pi-tower removed)."""
        return self.alpha_preferred

    @property
    def alpha_fs_inv(self) -> float:
        """1/alpha — structural fundamentals (pi-tower removed)."""
        return 1.0 / self.alpha_preferred












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




