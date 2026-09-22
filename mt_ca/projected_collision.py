"""Projected collision — Z_N[i] modular DA holonomy + saturating Φ + LUT rot (§3.12.5–6)."""

from __future__ import annotations

import math

import torch

from mt_ca.config import MConfig
from mt_ca.fixed_point import decode_spinor
from mt_ca.si_constants import heisenberg_phi_min_disc
from mt_ca.laplacian import neighbor_sum
from mt_ca.z_ring import bekenstein_scale_spinor, leapfrog_next, mod_lane

LUT_BITS = 12
LUT_SIZE = 1 << LUT_BITS
TRIG_SHIFT = 30


def _build_trig_lut(device: torch.device) -> tuple[torch.Tensor, torch.Tensor]:
    idx = torch.arange(LUT_SIZE, device=device, dtype=torch.float64)
    ang = 2.0 * math.pi * idx / LUT_SIZE
    cu = torch.round(torch.cos(ang) * (1 << TRIG_SHIFT)).to(torch.int64)
    sv = torch.round(torch.sin(ang) * (1 << TRIG_SHIFT)).to(torch.int64)
    return cu, sv


_TRIG_CACHE: dict[str, tuple[torch.Tensor, torch.Tensor]] = {}


def trig_lut(device: torch.device) -> tuple[torch.Tensor, torch.Tensor]:
    key = str(device)
    if key not in _TRIG_CACHE:
        _TRIG_CACHE[key] = _build_trig_lut(device)
    return _TRIG_CACHE[key]


def k_p_int(cfg: MConfig) -> int:
    """K_P in fixed-point natural units (ε ↔ u_P)."""
    from mt_ca.fixed_point import scale

    return max(1, int(round(cfg.epsilon * scale(cfg.frac_bits))))


def heisenberg_phi_min_int(cfg: MConfig) -> int:
    """Δφ_min = ½ rad → integer ticks mod N_ring (§3.12.6)."""
    return heisenberg_phi_min_disc(
        phase_bits=cfg.phase_bits,
        delta_phi_min=cfg.heisenberg_phi_min,
    )


def int_neighbor_sum(f: torch.Tensor, stencil: str) -> torch.Tensor:
    """Σ_N on each fixed lane (N₄ / N₆ / N₁₂)."""
    out = torch.zeros_like(f, dtype=torch.int64)
    for lane_i in range(f.shape[-1]):
        out[..., lane_i] = neighbor_sum(f[..., lane_i].to(torch.float32), stencil).to(torch.int64)
    return out


def holonomy_zeta_int(
    u: torch.Tensor,
    v: torch.Tensor,
    su: torch.Tensor,
    sv: torch.Tensor,
    *,
    frac_bits: int,
) -> tuple[torch.Tensor, torch.Tensor]:
    """ζ_real = ⟨U⟩U+⟨V⟩V, ζ_imag = ⟨V⟩U−⟨U⟩V with bit-shift renormalization."""
    zeta_r = (su * u + sv * v) >> frac_bits
    zeta_i = (sv * u - su * v) >> frac_bits
    return zeta_r, zeta_i


def saturating_phi_kick(
    zeta_r: torch.Tensor,
    zeta_i: torch.Tensor,
    rho2: torch.Tensor,
    cfg: MConfig,
) -> torch.Tensor:
    """Φ = ⌊K_P·ζ_imag / (ζ_real + |Z|² + K_P)⌋ in Z_{2^phase_bits} (+ Heisenberg floor)."""
    kp = k_p_int(cfg)
    denom = zeta_r + rho2 + kp
    denom = torch.where(denom > 0, denom, torch.ones_like(denom))
    phi = (kp * zeta_i) // denom

    if cfg.heisenberg_floor:
        phi_min = heisenberg_phi_min_int(cfg)
        # stagger on spatial lattice (2D or 3D)
        shape = zeta_i.shape
        coords = []
        for dim, size in enumerate(shape):
            view = [1] * len(shape)
            view[dim] = size
            coords.append(torch.arange(size, device=zeta_i.device, dtype=torch.int64).view(*view))
        parity = coords[0]
        for c in coords[1:]:
            parity = parity + c
        stagger = torch.where(parity % 2 == 0, torch.ones_like(zeta_i), -torch.ones_like(zeta_i))
        below = phi.abs() < phi_min
        sign = torch.sign(phi)
        sign = torch.where(sign == 0, stagger, sign)
        phi = torch.where(
            below,
            stagger * phi_min,
            sign * torch.maximum(phi.abs(), torch.full_like(phi, phi_min)),
        )

    return mod_lane(phi, cfg.mod_bits)


def projected_phi_int(f: torch.Tensor, cfg: MConfig) -> torch.Tensor:
    """Integer Φ ticks per cell before Rot_LUT (§3.12.5 · §5.2.3 ledger)."""
    fb = cfg.frac_bits
    u0 = f[..., 0].to(torch.int64)
    v0 = f[..., 1].to(torch.int64)
    sum_n = int_neighbor_sum(f, cfg.stencil)
    su0, sv0 = sum_n[..., 0], sum_n[..., 1]
    zeta_r, zeta_i = holonomy_zeta_int(u0, v0, su0, sv0, frac_bits=fb)
    rho2 = rho2_int(u0, v0, frac_bits=fb)
    phi = saturating_phi_kick(zeta_r, zeta_i, rho2, cfg)
    return mod_lane(phi + pauli_phi_int(f, cfg), cfg.mod_bits)


def rot_kick_uv(
    u: torch.Tensor,
    v: torch.Tensor,
    phi: torch.Tensor,
    *,
    phase_bits: int,
) -> tuple[torch.Tensor, torch.Tensor]:
    """δU, δV from LUT rotation by Φ (mod 2^phase_bits).

    Φ ticks live on N_ring = 2^phase_bits; finer Rot_LUT subsamples that circle.
    """
    cu, sv = trig_lut(u.device)
    phi_i = phi.to(torch.int64)
    if phase_bits >= LUT_BITS:
        idx = (phi_i >> (phase_bits - LUT_BITS)) % LUT_SIZE
    else:
        idx = (phi_i << (LUT_BITS - phase_bits)) % LUT_SIZE
    cos_v = cu[idx]
    sin_v = sv[idx]
    ur = (u * cos_v - v * sin_v) >> TRIG_SHIFT
    vr = (u * sin_v + v * cos_v) >> TRIG_SHIFT
    return ur - u, vr - v


def rho2_int(u: torch.Tensor, v: torch.Tensor, *, frac_bits: int) -> torch.Tensor:
    return (u * u + v * v) >> frac_bits


def pauli_phi_int(f: torch.Tensor, cfg: MConfig) -> torch.Tensor:
    """§3.10.4: parallel spinors on v_p → extra Φ ticks (decode probe → ℤ)."""
    if not cfg.pauli_exclusion:
        return torch.zeros(f.shape[:-1], device=f.device, dtype=torch.int64)
    from mt_ca.topology import pauli_phi

    z = decode_spinor(f, frac_bits=cfg.frac_bits, mod_bits=cfg.mod_bits)
    extra = pauli_phi(z, cfg)
    from mt_ca.si_constants import pauli_kick_disc

    kick = float(pauli_kick_disc(phase_bits=cfg.phase_bits))
    ticks = torch.where(extra > 0, torch.full_like(extra, kick), torch.zeros_like(extra))
    return mod_lane(ticks.to(torch.int64), cfg.mod_bits)


def projected_collision_kick(f: torch.Tensor, cfg: MConfig) -> torch.Tensor:
    """⌊𝒩⌋: integer saturating Φ + LUT rot kick on both spinor components (§3.12.5)."""
    u0 = f[..., 0].to(torch.int64)
    v0 = f[..., 1].to(torch.int64)
    u1 = f[..., 2].to(torch.int64)
    v1 = f[..., 3].to(torch.int64)

    phi = projected_phi_int(f, cfg)

    du0, dv0 = rot_kick_uv(u0, v0, phi, phase_bits=cfg.phase_bits)
    du1, dv1 = rot_kick_uv(u1, v1, phi, phase_bits=cfg.phase_bits)

    return mod_lane(torch.stack([du0, dv0, du1, dv1], dim=-1), cfg.mod_bits)


def projected_step_fixed(
    f_curr: torch.Tensor,
    f_past: torch.Tensor,
    cfg: MConfig,
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    """One modular leapfrog tick: Z⁺ + Z⁻ = 2Z + ⌊𝒩⌋ in Z_N[i], then A7 integer scale."""
    n_kick = projected_collision_kick(f_curr, cfg)
    f_raw = leapfrog_next(f_curr, f_past, n_kick, mod_bits=cfg.mod_bits)
    rho_max_int = max(1, int(round(cfg.rho_max * (1 << cfg.frac_bits))))
    f_next = bekenstein_scale_spinor(
        f_raw,
        frac_bits=cfg.frac_bits,
        rho_max_int=rho_max_int,
        mod_bits=cfg.mod_bits,
    )
    n_kick_eff = mod_lane(
        f_next.to(torch.int64) + f_past.to(torch.int64) - 2 * f_curr.to(torch.int64),
        cfg.mod_bits,
    )
    return f_next, f_curr, n_kick_eff
