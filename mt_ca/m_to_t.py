"""M→T anchor checks (§4.0.1, §5, §5.0.1)."""

from __future__ import annotations

import torch

from mt_ca.config import MConfig
from mt_ca.si_constants import SI, lepton_geometry_factor
from mt_ca.spinor import arg_phase_defect, spinor_density
from mt_ca.t_validation import macro_mass


def electron_v_p_anchor(*, m_e: float | None = None) -> dict[str, float]:
    """Compare CODATA m_e to m_P·α²·f_geometry — external T anchor, not fitted."""
    m_e = m_e if m_e is not None else SI.m_e_CODATA
    f = lepton_geometry_factor(m_e)
    predicted = SI.m_P * SI.alpha_fs**2 * f
    rel = abs(predicted - m_e) / m_e
    return {
        "m_e_CODATA": m_e,
        "f_geometry": f,
        "m_P_alpha2_f": predicted,
        "rel_err": rel,
    }


def zigzag_activity(
    z: torch.Tensor,
    cfg: MConfig,
    *,
    rho_quantile: float | None = None,
) -> float:
    """Mean |Δφ| weighted by ρ — Arg-carrier load (§5.0.1). Optional quantile mask for core-only."""
    phase = arg_phase_defect(z, cfg, apply_floor=False)
    rho = spinor_density(z)
    if rho_quantile is not None:
        flat = rho.reshape(-1)
        if flat.numel() == 0:
            return 0.0
        thresh = torch.quantile(flat, rho_quantile)
        mask = rho >= thresh
        if not mask.any():
            return 0.0
        return float(phase[mask].abs().mean().item())
    mass = float(rho.sum().item())
    if mass <= 1e-12:
        return 0.0
    return float((phase.abs() * rho).sum().item() / mass)


def arg_mass_load(z: torch.Tensor, cfg: MConfig) -> float:
    """Integrated |Δφ|·ρ — total Arg-carrier load (pairs with m_rest, §5.0.1)."""
    phase = arg_phase_defect(z, cfg, apply_floor=False)
    rho = spinor_density(z)
    return float((phase.abs() * rho).sum().item())


def m_rest_readout(z: torch.Tensor, block: int = 8) -> float:
    """Integrated macro amplitude Σ|Φ|² — T mass readout (§5, §5.0.1)."""
    return macro_mass(z, block)


def zigzag_mass_row(z: torch.Tensor, cfg: MConfig, *, block: int = 8) -> dict[str, float]:
    """Joint M Arg-activity + T m_rest readout for correlation leaves."""
    return {
        "zigzag_activity": zigzag_activity(z, cfg),
        "arg_mass_load": arg_mass_load(z, cfg),
        "m_rest": m_rest_readout(z, block),
    }
