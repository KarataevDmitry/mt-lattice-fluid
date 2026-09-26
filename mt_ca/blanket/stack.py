"""Apply blanket preset on a simulator that already holds boil ocean."""

from __future__ import annotations

from typing import Any

import torch

from mt_ca.blanket.constraints import load_ism_constraints
from mt_ca.blanket.preset import BlanketPreset
from mt_ca.blanket.surface import apply_ism_blanket, tau_uniform_ism_blanket
from mt_ca.simulator import LatticeFluidSimulator


def apply_blanket_preset(
    sim: LatticeFluidSimulator,
    preset: BlanketPreset,
    *,
    thickness: int = 6,
    constraints: dict[str, Any] | None = None,
) -> torch.Tensor | None:
    """Mutate ``sim.z`` when preset ≠ NONE; returns τ map or None."""
    if preset is BlanketPreset.NONE:
        return None
    if preset is not BlanketPreset.HOMOGENEOUS_MZW:
        raise ValueError(f"unsupported blanket preset: {preset}")
    c = constraints or load_ism_constraints()
    ny, nx = sim.ny, sim.nx
    tau = tau_uniform_ism_blanket(ny, nx, c, device=sim.device)
    z2 = apply_ism_blanket(
        sim.z,
        tau,
        thickness=thickness,
        frac_bits=sim.cfg.frac_bits,
        mod_bits=sim.cfg.mod_bits,
    )
    sim.set_field(z2)
    return tau
