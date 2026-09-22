from __future__ import annotations

from dataclasses import dataclass
import math

from mt_ca.si_constants import DELTA_PHI_MIN, HV, SI
from mt_ca.fixed_point import vacuum_amplitude_quantum


@dataclass(frozen=True)
class MConfig:
    """Planck-lattice M-layer parameters in natural units (hL=l_P, hT=t_P, c=1)."""

    # hL / hT in SI — semantic anchors for T-layer reporting (simulation uses natural units)
    hL: float = SI.l_P
    hT: float = SI.hT

    # linear_mode: isotropic (§3.6 default) | local_ca (§3.6 bond-sweeps) | diffusive (A3↔A6 anti-pattern)
    linear_mode: str = "isotropic"

    # Kinetic coupling: dispersion ω(k)≈γ|k|² at small k (A15 calibration)
    gamma: float = 0.25

    # Vacuum gate (§7.1): ε=1 ↔ u_P; α*=1+1/(4π) from ω·hT=2π + zero-point ½ℏω
    epsilon: float = SI.epsilon
    alpha_factor: float = SI.alpha_star

    # A8: extra macro suppression w(ρ)=1/(1+ρ/ρ_macro); 0 = gate asymptotics only
    macro_rho: float = 1.0
    macro_weight: bool = True

    # t=0 «первичный бульон»: one Q(frac_bits) quanta (§3.12.6)
    vacuum_amplitude: float = vacuum_amplitude_quantum(frac_bits=HV.frac_bits)

    # A9: discrete CR coupling in gate (§3.9)
    cr_strength: float = 0.25

    # §3.9 global holomorphy sync on same Δt
    holomorphy_sync: bool = True
    sync_strength: float = 0.12

    # §3.10.4 Pauli pressure on same v_p
    pauli_exclusion: bool = True
    pauli_kick: float = 3.0
    pauli_rho_min: float = 0.35
    pauli_overlap_cos: float = 0.92

    # A7 hard Planck density ceiling (|z|² in natural units)
    rho_max: float = 1.0

    # §3.7.2 Heisenberg physical floor: Δφ_min = s₀/ℏ = ½ rad (Planck, not 1/2^F)
    heisenberg_floor: bool = True
    heisenberg_phi_min: float = DELTA_PHI_MIN

    # §3.8: n4 (weak waves) | hex (vortex contour — ladder step 1 after deformation test)
    stencil: str = "hex"

    # §3.12 M-canonical evolution: leapfrog on Planck fixed-point lattice (§3.12.6)
    evolution: str = "leapfrog"
    mod_bits: int = HV.mod_bits
    frac_bits: int = HV.frac_bits
    use_projected_collision: bool = True
    phase_bits: int = HV.phase_bits

    @property
    def is_leapfrog(self) -> bool:
        return self.evolution == "leapfrog"

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
