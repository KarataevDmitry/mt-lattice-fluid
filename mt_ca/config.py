from __future__ import annotations

from dataclasses import dataclass, replace
import math

from mt_ca.si_constants import (
    DELTA_PHI_MIN,
    HV,
    N12_FCC_CAUSAL_LINKS,
    SI,
    elementary_quanta_row,
    kappa_link,
    pauli_kick_rad,
    pauli_overlap_cos,
    pauli_rho_min_natural,
    sync_strength_rad,
)
from mt_ca.fixed_point import vacuum_amplitude_quantum
from mt_ca.laplacian import stencil_n_links


@dataclass(frozen=True)
class MConfig:
    """Planck-lattice M-layer parameters in natural units (hL=l_P, hT=t_P, c=1)."""

    # hL / hT in SI — semantic anchors for T-layer reporting (simulation uses natural units)
    hL: float = SI.l_P
    hT: float = SI.hT

    # linear_mode: isotropic (§3.6 default) | local_ca (§3.6 bond-sweeps) | diffusive (A3↔A6 anti-pattern)
    linear_mode: str = "isotropic"

    # Kinetic coupling: γ = κ_link = 1/|N| (§5.2.2 · §1.6 canon |N|=12)
    gamma: float = kappa_link(n_links=N12_FCC_CAUSAL_LINKS)

    # Vacuum gate (§7.1): ε=1 ↔ u_P; α*=1+1/(4π) from ω·hT=2π + zero-point ½ℏω
    epsilon: float = SI.epsilon
    alpha_factor: float = SI.alpha_star

    # A8: extra macro suppression w(ρ)=1/(1+ρ/ρ_macro); 0 = gate asymptotics only
    macro_rho: float = 1.0
    macro_weight: bool = True

    # t=0 «первичный бульон»: one Q(frac_bits) quanta (§3.12.6)
    vacuum_amplitude: float = vacuum_amplitude_quantum(frac_bits=HV.frac_bits)

    # A9: discrete CR coupling — cr_strength = κ_link (§5.2.2)
    cr_strength: float = kappa_link(n_links=N12_FCC_CAUSAL_LINKS)

    # §3.9 global holomorphy sync on same Δt — κ_link·Δφ_min (§5.2.3)
    holomorphy_sync: bool = True
    sync_strength: float = sync_strength_rad()

    # §3.10.4 Pauli pressure on same v_p — π kick, κ_link·ρ_max thresholds (§5.2.3)
    pauli_exclusion: bool = True
    pauli_kick: float = pauli_kick_rad()
    pauli_rho_min: float = pauli_rho_min_natural()
    pauli_overlap_cos: float = pauli_overlap_cos()

    # A7 hard Planck density ceiling (|z|² in natural units)
    rho_max: float = 1.0

    # §3.7.2 Heisenberg physical floor: Δφ_min = s₀/ℏ = ½ rad (Planck, not 1/2^F)
    heisenberg_floor: bool = True
    heisenberg_phi_min: float = DELTA_PHI_MIN

    # §1.6 canon fcc N₁₂ · hex = (2+1) slice · n4 = MVP archive
    stencil: str = "fcc"

    # §3.12 M-canonical evolution: leapfrog + projected collision on Z_N[i] (§3.12.6)
    evolution: str = "leapfrog"
    mod_bits: int = HV.mod_bits
    frac_bits: int = HV.frac_bits
    use_projected_collision: bool = True
    phase_bits: int = HV.phase_bits

    @property
    def is_leapfrog(self) -> bool:
        return True

    @property
    def c(self) -> float:
        return self.hL / self.hT

    @property
    def omega(self) -> float:
        """One full vacuum phase cycle per tick: ω = 2π/hT [rad/s in SI]."""
        return SI.omega if self.hT == SI.hT else 2.0 * math.pi / self.hT

    @property
    def phase_scale(self) -> float:
        """hT·ω = 2π — dimensionless tick phase (λ absorbed into hT)."""
        return self.hT * self.omega

    @classmethod
    def for_stencil(cls, stencil: str = "fcc", **kw: object) -> "MConfig":
        """Canon κ_link = 1/|N| tied to stencil (§1.6 · §5.2.2)."""
        n = stencil_n_links(stencil)
        k = kappa_link(n_links=n)
        base = cls(stencil=stencil, gamma=k, cr_strength=k)
        return replace(base, **kw) if kw else base  # type: ignore[arg-type]
