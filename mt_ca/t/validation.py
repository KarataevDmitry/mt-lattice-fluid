"""T-layer self-checks (validate_mt, §4 probes)."""

from mt_ca.t_validation import (
    coarse_grain,
    collision_peak_count,
    covariance_isotropy,
    isotropy_ratio,
    macro_mass,
    nu_readout_passes,
    profile_correlation,
    radial_front_radii,
    radial_speed_uniformity,
    soliton_peak_track,
    wave_particle_readout,
)

__all__ = [
    "coarse_grain",
    "collision_peak_count",
    "covariance_isotropy",
    "isotropy_ratio",
    "macro_mass",
    "nu_readout_passes",
    "profile_correlation",
    "radial_front_radii",
    "radial_speed_uniformity",
    "soliton_peak_track",
    "wave_particle_readout",
]
