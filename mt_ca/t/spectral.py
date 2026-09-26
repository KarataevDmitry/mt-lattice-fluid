"""Spectral helpers on the lattice (DFT) — T calibration, not M micro_step."""

from mt_ca.t_analysis import (
    amplitude_spectrum,
    block_mean,
    estimate_phase_velocity_plane_wave,
    laplacian_eigenvalues,
    macro_readout_amplitude,
    spectral_apply,
    spectral_unitary_reference,
)

macro_amplitude = macro_readout_amplitude

__all__ = [
    "amplitude_spectrum",
    "block_mean",
    "estimate_phase_velocity_plane_wave",
    "laplacian_eigenvalues",
    "macro_amplitude",
    "macro_readout_amplitude",
    "spectral_apply",
    "spectral_unitary_reference",
]
