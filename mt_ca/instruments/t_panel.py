"""T-layer instrument panel — binomial macro + M→T probes (§4.1 · §5.2)."""
from __future__ import annotations

from typing import Any

import torch

from mt_ca.config import MConfig
from mt_ca.conservation import madelung_div_j
from mt_ca.instruments.catalog import InstrumentId
from mt_ca.instruments.scales import QuantityKind, reading
from mt_ca.m_to_t import arg_mass_load, m_rest_readout, zigzag_activity
from mt_ca.macro import macro_amplitude, macro_matter_b
from mt_ca.matter_readout import default_anchor, plane_mconfig, spinor_plane
from mt_ca.metrics import field_amplitude
from mt_ca.spinor import spinor_density
from mt_ca.t_validation import (
    coarse_grain,
    collision_peak_count,
    covariance_isotropy,
    isotropy_ratio,
    macro_mass,
    nu_readout_passes,
    profile_correlation,
    radial_speed_uniformity,
)

T_PANEL_SCHEMA = 2


def _plane_for_t(z: torch.Tensor) -> torch.Tensor:
    if z.ndim == 4:
        site = default_anchor(z)
        return spinor_plane(z, site)
    return z


def sample_t_field(
    z: torch.Tensor,
    cfg: MConfig,
    *,
    block: int = 8,
    z_past: torch.Tensor | None = None,
    steps_for_nu: int = 0,
    dt_steps: int = 1,
) -> dict[str, Any]:
    """All T_macro meters on one 2+1 slice (FCC: anchor plane)."""
    plane = _plane_for_t(z)
    if plane.ndim != 3:
        raise ValueError("T panel needs spinor (ny,nx,2) plane")

    nu = nu_readout_passes(steps_for_nu, block) if steps_for_nu > 0 else 0
    radius = max(1, block)
    coarse = coarse_grain(plane, block, nu_viscosity_passes=nu)
    amp_macro = macro_amplitude(plane, radius=radius, nu_viscosity_passes=nu)
    b_macro = macro_matter_b(plane, radius=radius)
    rho_micro = spinor_density(plane)
    amp_micro = field_amplitude(plane)

    m_rest = macro_mass(plane, block, nu_viscosity_passes=nu)
    plane_cfg = plane_mconfig(plane, cfg)
    zigzag = zigzag_activity(plane, plane_cfg)
    arg_load = arg_mass_load(plane, plane_cfg)
    m_rest_legacy = m_rest_readout(plane, block)

    iso = isotropy_ratio(amp_macro)
    cov_iso = covariance_isotropy(amp_macro)
    peaks = collision_peak_count(coarse)

    madelung_max = None
    radial_cv = None
    if z_past is not None:
        past_plane = _plane_for_t(z_past)
        if past_plane.shape == plane.shape:
            rho0 = spinor_density(past_plane)
            rho1 = spinor_density(plane)
            divj = madelung_div_j(past_plane)
            residual = (rho1 - rho0 + divj).abs()
            madelung_max = float((residual.max() / rho1.max().clamp_min(1e-12)).item())
            radial_cv = radial_speed_uniformity(rho0, rho1, dt_steps=dt_steps)

    readings: dict[str, Any] = {
        InstrumentId.T_PHI_AMP_MEAN.value: reading(
            InstrumentId.T_PHI_AMP_MEAN.value,
            QuantityKind.FIELD_AMPLITUDE,
            float(amp_macro.mean().item()),
        ).to_dict(),
        InstrumentId.T_PHI_AMP_MAX.value: reading(
            InstrumentId.T_PHI_AMP_MAX.value,
            QuantityKind.FIELD_AMPLITUDE,
            float(amp_macro.max().item()),
        ).to_dict(),
        InstrumentId.T_RHO_FIELD_MEAN.value: reading(
            InstrumentId.T_RHO_FIELD_MEAN.value,
            QuantityKind.RHO_FIELD,
            float(rho_micro.mean().item()),
        ).to_dict(),
        InstrumentId.T_MACRO_B_MEAN.value: reading(
            InstrumentId.T_MACRO_B_MEAN.value,
            QuantityKind.DIMENSIONLESS,
            float(b_macro.mean().item()),
        ).to_dict(),
        InstrumentId.T_MACRO_B_MAX.value: reading(
            InstrumentId.T_MACRO_B_MAX.value,
            QuantityKind.DIMENSIONLESS,
            float(b_macro.max().item()),
        ).to_dict(),
        InstrumentId.T_M_REST.value: reading(
            InstrumentId.T_M_REST.value,
            QuantityKind.MACRO_MASS_READOUT,
            m_rest,
        ).to_dict(),
        InstrumentId.T_M_REST_LEGACY.value: reading(
            InstrumentId.T_M_REST_LEGACY.value,
            QuantityKind.MACRO_MASS_READOUT,
            m_rest_legacy,
        ).to_dict(),
        InstrumentId.T_ZIGZAG_ACTIVITY.value: reading(
            InstrumentId.T_ZIGZAG_ACTIVITY.value,
            QuantityKind.PHASE_RAD,
            zigzag,
        ).to_dict(),
        InstrumentId.T_ARG_MASS_LOAD.value: reading(
            InstrumentId.T_ARG_MASS_LOAD.value,
            QuantityKind.ACTION_S0,
            arg_load,
        ).to_dict(),
        InstrumentId.T_ISOTROPY.value: reading(
            InstrumentId.T_ISOTROPY.value,
            QuantityKind.DIMENSIONLESS,
            iso if iso == iso and iso < 1e30 else float("nan"),
        ).to_dict(),
        InstrumentId.T_COV_ISOTROPY.value: reading(
            InstrumentId.T_COV_ISOTROPY.value,
            QuantityKind.DIMENSIONLESS,
            cov_iso if cov_iso == cov_iso and cov_iso < 1e30 else float("nan"),
        ).to_dict(),
        InstrumentId.T_COARSE_PEAKS.value: reading(
            InstrumentId.T_COARSE_PEAKS.value,
            QuantityKind.DIMENSIONLESS,
            float(peaks),
        ).to_dict(),
        InstrumentId.T_NU_READOUT_PASSES.value: reading(
            InstrumentId.T_NU_READOUT_PASSES.value,
            QuantityKind.DIMENSIONLESS,
            float(nu),
        ).to_dict(),
        InstrumentId.T_MACRO_BLOCK.value: reading(
            InstrumentId.T_MACRO_BLOCK.value,
            QuantityKind.DIMENSIONLESS,
            float(block),
        ).to_dict(),
    }
    if madelung_max is not None:
        readings[InstrumentId.T_MADELUNG_RESIDUAL_MAX.value] = reading(
            InstrumentId.T_MADELUNG_RESIDUAL_MAX.value,
            QuantityKind.DIMENSIONLESS,
            madelung_max,
        ).to_dict()
    if radial_cv is not None and radial_cv == radial_cv:
        readings[InstrumentId.T_RADIAL_SPEED_CV.value] = reading(
            InstrumentId.T_RADIAL_SPEED_CV.value,
            QuantityKind.DIMENSIONLESS,
            radial_cv,
        ).to_dict()

    # Self-correlation if we had past coarse (shape stability)
    if z_past is not None:
        past_plane = _plane_for_t(z_past)
        if past_plane.shape == plane.shape:
            coarse0 = coarse_grain(past_plane, block, nu_viscosity_passes=nu)
            corr = profile_correlation(coarse0, coarse)
            readings[InstrumentId.T_PROFILE_CORR.value] = reading(
                InstrumentId.T_PROFILE_CORR.value,
                QuantityKind.DIMENSIONLESS,
                corr,
            ).to_dict()

    return {
        "schema": T_PANEL_SCHEMA,
        "block": block,
        "nu_viscosity_passes": nu,
        "readings": readings,
    }
