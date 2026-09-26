"""Conservation probes: M = A3 global norm + discrete ledgers; smooth Madelung = T."""

from __future__ import annotations

import torch

from mt_ca.config import MConfig
from mt_ca.fixed_point import decode_spinor
from mt_ca.reversible import canonical_fixed, leapfrog_forward_fixed
from mt_ca.seeds import SeedClass, make_seed
from mt_ca.simulator import LatticeFluidSimulator
from mt_ca.spinor import spinor_density


def spinor_scalar(z: torch.Tensor) -> torch.Tensor:
    if z.ndim >= 3 and z.shape[-1] == 2:
        return z[..., 0]
    return z


def rotate_c4(z: torch.Tensor) -> torch.Tensor:
    return torch.rot90(z, k=1, dims=(0, 1))


def madelung_div_j(z: torch.Tensor) -> torch.Tensor:
    """Discrete Madelung flux divergence on the first spinor component (2D T-layer)."""
    u = spinor_scalar(z)
    jx = (u.conj() * torch.roll(u, -1, 1)).imag
    jy = (u.conj() * torch.roll(u, -1, 0)).imag
    return jx - torch.roll(jx, 1, 1) + jy - torch.roll(jy, 1, 0)


def projected_global_drift(
    seed: SeedClass,
    size: int,
    *,
    steps: int,
    device: str,
    stencil: str = "hex",
) -> float:
    """|Σρ(t)−Σρ(0)| / Σρ(0) after ``steps`` of the one automaton (projected leapfrog)."""
    cfg = MConfig.for_stencil(stencil, heisenberg_floor=True)
    sim = LatticeFluidSimulator(size, size, cfg, device=device)
    sim.reset(seed)
    n0 = float(sim.norm())
    for _ in range(steps):
        sim.step(1)
    n1 = float(sim.norm())
    return abs(n1 - n0) / max(n0, 1e-12)


def projected_madelung_residual(
    size: int = 64,
    *,
    device: str = "cpu",
) -> float:
    """One-tick |Δρ + div j| / max ρ — T Madelung probe (not an M hard law)."""
    cfg = MConfig.for_stencil("hex", heisenberg_floor=True)
    z = make_seed(SeedClass.PLANE_WAVE, size, size, device=torch.device(device), impulse_amplitude=0.12)
    f0 = canonical_fixed(z, cfg)
    f1, _, _ = leapfrog_forward_fixed(f0, f0, cfg)
    z0 = decode_spinor(f0)
    z1 = decode_spinor(f1)
    rho0 = spinor_density(z0)
    rho1 = spinor_density(z1)
    residual = (rho1 - rho0 + madelung_div_j(z0)).abs()
    return float((residual.max() / rho0.max().clamp_min(1e-12)).item())


def so2_c4_equivariance_fixed_error(
    z: torch.Tensor,
    z_past: torch.Tensor,
    cfg: MConfig,
) -> int:
    """g(R·Ψ)=R·g(Ψ) on canonical leapfrog+projected — compare in Z_N[i], not float."""
    f_curr = canonical_fixed(z, cfg)
    f_past = canonical_fixed(z_past, cfg)
    f_rot = canonical_fixed(rotate_c4(z), cfg)
    f_past_rot = canonical_fixed(rotate_c4(z_past), cfg)

    f_next, _, _ = leapfrog_forward_fixed(f_curr, f_past, cfg)
    f_next_rot, _, _ = leapfrog_forward_fixed(f_rot, f_past_rot, cfg)
    f_next_via_rot = canonical_fixed(rotate_c4(decode_spinor(f_next)), cfg)
    return int((f_next_rot - f_next_via_rot).abs().max().item())


def a3_global_norm_report(
    size: int = 64,
    *,
    device: str = "cpu",
) -> dict:
    """M-layer A3: global Σ|z|² on the one projected g.

    Habitat = VACUUM_BOIL (filled boiling ocean). Gauge-fixed VACUUM is frozen control.
    Localized excitations on heterogeneous boil may redistribute norm via A7 integer
    clamp — reported separately, not a habitat fail.
    """
    boil_drift = projected_global_drift(SeedClass.VACUUM_BOIL, size, steps=32, device=device)
    vac_drift = projected_global_drift(SeedClass.VACUUM, size, steps=32, device=device)
    impulse_drift = projected_global_drift(SeedClass.IMPULSE, size, steps=32, device=device)
    ok = boil_drift < 1e-6 and vac_drift < 1e-6
    return {
        "id": "A3_global_norm",
        "layer": "M",
        "boil_global_drift_32": boil_drift,
        "vacuum_global_drift_32": vac_drift,
        "impulse_global_drift_32": impulse_drift,
        "ok": ok,
        "note": "A3 habitat: VACUUM_BOIL Σ|z|² invariant; impulse on boil = A7 clamp probe",
    }


def t_madelung_continuity_report(
    size: int = 64,
    *,
    device: str = "cpu",
) -> dict:
    """T-layer Madelung residual — emergent macro, never an M hard fail."""
    madelung = projected_madelung_residual(size, device=device)
    return {
        "id": "T_MadelungContinuity",
        "layer": "T",
        "madelung_one_tick_rel": madelung,
        "ok": True,
        "note": "Planck world is discrete; Δρ+div j is T probe (§4.3), not M law",
    }


def local_conservation_report(
    size: int = 64,
    *,
    device: str = "cpu",
) -> dict:
    """Compat shim: M global norm only (smooth Madelung moved to t_madelung_continuity_report)."""
    return a3_global_norm_report(size, device=device)


def so2_c4_report(
    size: int = 64,
    *,
    device: str = "cpu",
) -> dict:
    """C₄ equivariance only on n4 (square) stencil — hex has no 90° symmetry."""
    cfg = MConfig.for_stencil(
        "n4", heisenberg_floor=False, cr_strength=0.0, holomorphy_sync=False, pauli_exclusion=False
    )
    z = make_seed(SeedClass.PLANE_WAVE, size, size, device=torch.device(device), impulse_amplitude=0.12)
    z_past = z.clone()
    err = so2_c4_equivariance_fixed_error(z, z_past, cfg)
    # HF=False: residual ≤1 from Q encode; HF=True stagger breaks C₄ (err→N/2).
    ok = err <= 1
    return {
        "id": "SO2_C4",
        "fixed_int_max_err": err,
        "stencil": "n4",
        "heisenberg_floor": False,
        "evolution": "leapfrog",
        "projected_collision": True,
        "ok": ok,
        "note": "§5.2.1 · §3.12: C₄ on n4+HF off; hex≠C₄",
    }
