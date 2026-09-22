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
    """A7 on ℤ: scale (U,V) pairs when |z|² > ρ_max — fixed-point ratio, no decode/encode."""
    if rho_max_int <= 0:
        return mod_lane(f, mod_bits)

    fb = frac_bits
    rho_cap = float(int(rho_max_int) << fb)
    scale_q = float(1 << fb)
    out = f.to(torch.int64).clone()

    for re_i, im_i in ((0, 1), (2, 3)):
        u = signed_from_mod(out[..., re_i], mod_bits)
        v = signed_from_mod(out[..., im_i], mod_bits)
        out[..., re_i] = u
        out[..., im_i] = v
        rho2 = (u * u + v * v).to(torch.float64)
        over = rho2 > rho_cap
        if not bool(over.any()):
            continue
        factor = (
            torch.sqrt(rho_cap / torch.clamp(rho2, min=1.0)) * scale_q
        ).floor().to(torch.int64)
        u_s = (u * factor) >> fb
        v_s = (v * factor) >> fb
        out[..., re_i] = torch.where(over, u_s, u)
        out[..., im_i] = torch.where(over, v_s, v)

    return mod_lane(out, mod_bits)


# Back-compat alias
lane = mod_lane
