"""Modular factor ring Z_N[i], N = 2^mod_bits — Planck-derived (§3.12.6).

Each lane of the fixed spinor is an element of Z_N; complex pairs (U, V) form Z_N[i].
Default N = 512 = 2^⌊B_hV⌋, B_hV = 2π/ln 2 from Bekenstein on one hV brick.
"""

from __future__ import annotations

import torch

from mt_ca.si_constants import HV


def signed_from_mod(u: torch.Tensor, mod_bits: int = HV.mod_bits) -> torch.Tensor:
    """Interpret ring element in [0, N) as signed integer in (−N/2, N/2]."""
    n = 1 << mod_bits
    half = n >> 1
    x = u.to(torch.int64)
    return torch.where(x >= half, x - n, x)


def mod_lane(x: torch.Tensor, mod_bits: int = HV.mod_bits) -> torch.Tensor:
    """Project into Z_N where N = 2^mod_bits."""
    n = 1 << mod_bits
    return (x.to(torch.int64) % n).to(torch.int32)


def add(a: torch.Tensor, b: torch.Tensor, *, mod_bits: int = HV.mod_bits) -> torch.Tensor:
    return mod_lane(a.to(torch.int64) + b.to(torch.int64), mod_bits)


def sub(a: torch.Tensor, b: torch.Tensor, *, mod_bits: int = HV.mod_bits) -> torch.Tensor:
    return mod_lane(a.to(torch.int64) - b.to(torch.int64), mod_bits)


def double(a: torch.Tensor, *, mod_bits: int = HV.mod_bits) -> torch.Tensor:
    return mod_lane(a.to(torch.int64) << 1, mod_bits)


def leapfrog_next(
    z: torch.Tensor,
    z_past: torch.Tensor,
    n_kick: torch.Tensor,
    *,
    mod_bits: int = HV.mod_bits,
) -> torch.Tensor:
    """Z(x,t+Δt) = 2Z(x,t) + ⌊𝒩⌋ − Z(x,t−Δt)  in Z_N[i] (lane-wise).

    Equivalent symmetric form: Z⁺ + Z⁻ = 2Z + ⌊𝒩⌋.
    """
    acc = 2 * z.to(torch.int64) + n_kick.to(torch.int64) - z_past.to(torch.int64)
    return mod_lane(acc, mod_bits)


def leapfrog_past(
    z: torch.Tensor,
    z_next: torch.Tensor,
    n_kick: torch.Tensor,
    *,
    mod_bits: int = HV.mod_bits,
) -> torch.Tensor:
    """Recover Z(x,t−Δt) from the same modular identity (exact T⁻¹ algebra)."""
    acc = 2 * z.to(torch.int64) + n_kick.to(torch.int64) - z_next.to(torch.int64)
    return mod_lane(acc, mod_bits)


def leapfrog_identity_holds(
    z: torch.Tensor,
    z_past: torch.Tensor,
    z_next: torch.Tensor,
    n_kick: torch.Tensor,
    *,
    mod_bits: int = HV.mod_bits,
) -> bool:
    """Check Z⁺ + Z⁻ = 2Z + ⌊𝒩⌋ (mod N) lane-wise."""
    lhs = add(z_next, z_past, mod_bits=mod_bits)
    rhs = add(double(z, mod_bits=mod_bits), n_kick, mod_bits=mod_bits)
    return bool(torch.equal(lhs, rhs))


def bekenstein_scale_spinor(
    f: torch.Tensor,
    *,
    frac_bits: int,
    rho_max_int: int,
    mod_bits: int = HV.mod_bits,
) -> torch.Tensor:
    """A7 on ℤ: scale full spinor when z†z > ρ_max — one factor on all lanes (§5.0 ρ_field)."""
    if rho_max_int <= 0:
        return mod_lane(f, mod_bits)

    fb = frac_bits
    rho_cap_raw = float(int(rho_max_int)) * float(1 << (2 * fb))
    scale_q = float(1 << fb)
    out = f.to(torch.int64).clone()

    for lane_i in range(out.shape[-1]):
        out[..., lane_i] = signed_from_mod(out[..., lane_i], mod_bits)

    u0, v0, u1, v1 = out[..., 0], out[..., 1], out[..., 2], out[..., 3]
    rho_raw = (u0 * u0 + v0 * v0 + u1 * u1 + v1 * v1).to(torch.float64)
    over = rho_raw > rho_cap_raw
    if not bool(over.any()):
        return mod_lane(out, mod_bits)

    factor = (torch.sqrt(rho_cap_raw / torch.clamp(rho_raw, min=1.0)) * scale_q).floor().to(
        torch.int64
    )
    u0 = torch.where(over, (u0 * factor) >> fb, u0)
    v0 = torch.where(over, (v0 * factor) >> fb, v0)
    u1 = torch.where(over, (u1 * factor) >> fb, u1)
    v1 = torch.where(over, (v1 * factor) >> fb, v1)
    out[..., 0], out[..., 1], out[..., 2], out[..., 3] = u0, v0, u1, v1
    return mod_lane(out, mod_bits)


# Back-compat alias
lane = mod_lane
