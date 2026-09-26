"""Sample multiple instruments at once — the lab panel (not one gate)."""
from __future__ import annotations

from typing import Any

import torch

from mt_ca.config import MConfig
from mt_ca.conservation import madelung_div_j
from mt_ca.instruments.catalog import InstrumentId, REGISTRY
from mt_ca.instruments.scales import QuantityKind, reading
from mt_ca.instruments.t_panel import sample_t_field
from mt_ca.ledger import (
    angular_momentum_density,
    ledger_step_probe,
    momentum_density,
    n_E_field,
)
from mt_ca.matter_readout import MatterSite, default_anchor, plane_mconfig, readout_at_site, spinor_plane
from mt_ca.metrics import total_norm_squared
from mt_ca.spinor import arg_phase_defect, saturating_phase, spinor_density
from mt_ca.topology import winding_nearest_int

PANEL_SCHEMA = 2
_CONTOUR_DEFAULT = 2


def _site_on_plane(z: torch.Tensor, site: MatterSite) -> tuple[torch.Tensor, int, int]:
    plane = spinor_plane(z, site)
    return plane, site.y, site.x


def sample_site(
    z: torch.Tensor,
    site: MatterSite,
    cfg: MConfig,
    *,
    contour_radius: int = _CONTOUR_DEFAULT,
    z_past: torch.Tensor | None = None,
) -> dict[str, Any]:
    """All M_site (+ optional ledger tick) readings at one ``hV``."""
    plane, y, x = _site_on_plane(z, site)
    rho = float(spinor_density(z)[site.iz, y, x].item()) if site.iz is not None else float(
        spinor_density(z)[y, x].item()
    )
    matter = readout_at_site(z, site, contour_radius=contour_radius, cfg=cfg)
    plane_cfg = plane_mconfig(plane, cfg)
    phi = saturating_phase(plane, plane_cfg)
    dphi = arg_phase_defect(plane, plane_cfg, apply_floor=False)
    n_e = int(n_E_field(phi, plane_cfg)[y, x].item())

    row: dict[str, Any] = {
        "schema": PANEL_SCHEMA,
        "site": {"iz": site.iz, "y": y, "x": x},
        InstrumentId.RHO_FIELD.value: rho,
        InstrumentId.B_MATTER.value: matter.b,
        InstrumentId.N_TOPO.value: (
            int(winding_nearest_int(matter.winding_auto))
            if matter.winding_auto == matter.winding_auto
            else None
        ),
        InstrumentId.N_TOPO_REL.value: matter.winding_rel,
        InstrumentId.N_TOPO_U1.value: matter.winding_u1,
        InstrumentId.DELTA_PHI.value: float(dphi[y, x].abs().item()),
        InstrumentId.PHI_GATE.value: float(phi[y, x].item()),
        InstrumentId.N_E.value: n_e,
    }

    if plane.ndim == 3:
        pi_x, pi_y = momentum_density(plane)
        row[InstrumentId.PI_X.value] = float(pi_x[y, x].item())
        row[InstrumentId.PI_Y.value] = float(pi_y[y, x].item())
        u = plane[..., 0]
        row[InstrumentId.J_X.value] = float((u.conj() * torch.roll(u, -1, 1)).imag[y, x].item())
        row[InstrumentId.J_Y.value] = float((u.conj() * torch.roll(u, -1, 0)).imag[y, x].item())
        lz = angular_momentum_density(plane)
        row[InstrumentId.L_Z.value] = float(lz[y, x].item())
    else:
        row[InstrumentId.PI_X.value] = None
        row[InstrumentId.PI_Y.value] = None
        row[InstrumentId.J_X.value] = None
        row[InstrumentId.J_Y.value] = None
        row[InstrumentId.L_Z.value] = None

    if z_past is not None:
        zpp, _, _ = _site_on_plane(z_past, site)
        probe = ledger_step_probe(plane, zpp, plane_cfg)
        row[InstrumentId.PHI_KICK_TICK.value] = int(probe["phi"][y, x].item())
        row[InstrumentId.ENERGY_STAR.value] = float(probe["energy_star"][y, x].item())
        row[InstrumentId.MOMENTUM_STAR_X.value] = float(probe["momentum_star_x"][y, x].item())
        row[InstrumentId.MOMENTUM_STAR_Y.value] = float(probe["momentum_star_y"][y, x].item())
    row["scaled"] = {
        InstrumentId.RHO_FIELD.value: reading(
            InstrumentId.RHO_FIELD.value, QuantityKind.RHO_FIELD, rho
        ).to_dict(),
        InstrumentId.B_MATTER.value: reading(
            InstrumentId.B_MATTER.value, QuantityKind.DIMENSIONLESS, float(matter.b)
        ).to_dict(),
        InstrumentId.N_E.value: reading(
            InstrumentId.N_E.value, QuantityKind.ENERGY_E0, float(n_e)
        ).to_dict(),
        InstrumentId.DELTA_PHI.value: reading(
            InstrumentId.DELTA_PHI.value, QuantityKind.PHASE_RAD, float(dphi[y, x].abs().item())
        ).to_dict(),
    }
    return row


def sample_field(
    z: torch.Tensor,
    cfg: MConfig,
    *,
    z_past: torch.Tensor | None = None,
) -> dict[str, Any]:
    """Field-level scalars and optional Madelung diagnostic (2D)."""
    rho = spinor_density(z)
    rho_mean = float(rho.mean().item())
    rho_max = float(rho.max().item())
    out: dict[str, Any] = {
        "schema": PANEL_SCHEMA,
        InstrumentId.RHO_CONTRAST.value: rho_max / (rho_mean + 1e-30),
        InstrumentId.NORM_GLOBAL.value: total_norm_squared(z),
        "rho_mean": rho_mean,
        "rho_max": rho_max,
    }
    if z.ndim == 3 and z_past is not None:
        rho0 = spinor_density(z_past)
        divj = madelung_div_j(z)
        residual = (rho - rho0 + divj).abs()
        out["madelung_residual_max"] = float((residual.max() / rho.max().clamp_min(1e-12)).item())
    return out


def sample_panel(
    z: torch.Tensor,
    cfg: MConfig,
    *,
    site: MatterSite | None = None,
    z_past: torch.Tensor | None = None,
    contour_radius: int = _CONTOUR_DEFAULT,
    macro_block: int = 8,
    steps_for_nu: int = 0,
) -> dict[str, Any]:
    """Full panel: M field + M site + T macro (default anchor; SI scales on readings)."""
    site = site or default_anchor(z)
    return {
        "schema": PANEL_SCHEMA,
        "catalog": [s.id.value for s in REGISTRY],
        "field": sample_field(z, cfg, z_past=z_past),
        "site": sample_site(z, site, cfg, contour_radius=contour_radius, z_past=z_past),
        "t": sample_t_field(
            z,
            cfg,
            block=macro_block,
            z_past=z_past,
            steps_for_nu=steps_for_nu,
        ),
    }
