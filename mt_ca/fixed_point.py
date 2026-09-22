"""Fixed-point ℂ² spinor as Z_N[i] — reversible leapfrog (§3.12.6).

Four int32 lanes per cell encode Z = U + iV ∈ Z_N[i], N = 2^mod_bits (Planck-derived).
Signed Q(frac_bits) values map to [0, N) via two's-complement fold on decode.
"""

from __future__ import annotations

import torch

from mt_ca.si_constants import HV
from mt_ca.z_ring import leapfrog_next, leapfrog_past, mod_lane, signed_from_mod

DEFAULT_FRAC_BITS = HV.frac_bits
DEFAULT_MOD_BITS = HV.mod_bits


def scale(frac_bits: int = DEFAULT_FRAC_BITS) -> float:
    return float(1 << frac_bits)


def gauge_fix_u1_global(z: torch.Tensor, eps: float = 1e-15) -> torch.Tensor:
    """Remove global U(1) phase before Q encode — preserves spatial ζ (A5, §3.11)."""
    ref = z[..., 0].mean()
    if float(ref.abs().item()) < eps:
        ref = z[..., 1].mean()
    if float(ref.abs().item()) < eps:
        return z
    phase = torch.angle(ref)
    factor = torch.exp(-1j * phase.to(z.real.dtype))
    return z * factor


def gauge_fix_u1(z: torch.Tensor, eps: float = 1e-15, *, per_cell: bool = False) -> torch.Tensor:
    """U(1) gauge before Q encode.

    Default **global** (§3.11 U(1)_vac): preserves neighbor holonomy / A5 boiling.
    ``per_cell=True`` — legacy T-only; kills ζ_imag on M encode (§10.2).
    """
    if not per_cell:
        return gauge_fix_u1_global(z, eps)
    ref = z[..., 0]
    fallback = z[..., 1]
    use_fallback = ref.abs() < eps
    ref = torch.where(use_fallback, fallback, ref)
    mag = ref.abs()
    phase = torch.angle(ref)
    factor = torch.exp(-1j * phase.to(z.real.dtype))
    mask = mag > eps
    return torch.where(mask.unsqueeze(-1), z * factor.unsqueeze(-1), z)


def enforce_planck_cell_floor(
    f: torch.Tensor,
    *,
    mod_bits: int = DEFAULT_MOD_BITS,
) -> torch.Tensor:
    """A5 + §3.12.6: no hV cell is exact zero — one Q(frac_bits) quanta minimum."""
    mag = f.abs().sum(dim=-1)
    dead = mag == 0
    if not bool(dead.any().item()):
        return f
    out = f.clone()
    out[dead, 0] = 1
    return mod_lane(out, mod_bits)


def encode_spinor(
    z: torch.Tensor,
    *,
    frac_bits: int = DEFAULT_FRAC_BITS,
    mod_bits: int = DEFAULT_MOD_BITS,
    gauge_fix: bool = False,
) -> torch.Tensor:
    """complex (...,2) → int32 (...,4) [re1,im1,re2,im2] in Z_N[i].

    Default gauge_fix=False on M encode (§10.2): per-cell gauge kills ζ_imag;
    global gauge optional via gauge_fix_u1_global for T/reporting only.
    """
    if gauge_fix:
        z = gauge_fix_u1(z)
    s = scale(frac_bits)
    out = torch.stack(
        [
            (z[..., 0].real * s).round(),
            (z[..., 0].imag * s).round(),
            (z[..., 1].real * s).round(),
            (z[..., 1].imag * s).round(),
        ],
        dim=-1,
    )
    return enforce_planck_cell_floor(mod_lane(out, mod_bits), mod_bits=mod_bits)


def decode_spinor(
    f: torch.Tensor,
    *,
    frac_bits: int = DEFAULT_FRAC_BITS,
    mod_bits: int = DEFAULT_MOD_BITS,
) -> torch.Tensor:
    """int32 (...,4) → complex (...,2) with signed fixed-point lanes."""
    inv = 1.0 / scale(frac_bits)
    re1 = signed_from_mod(f[..., 0], mod_bits).to(torch.float32) * inv
    im1 = signed_from_mod(f[..., 1], mod_bits).to(torch.float32) * inv
    re2 = signed_from_mod(f[..., 2], mod_bits).to(torch.float32) * inv
    im2 = signed_from_mod(f[..., 3], mod_bits).to(torch.float32) * inv
    z1 = torch.complex(re1, im1)
    z2 = torch.complex(re2, im2)
    dtype = torch.complex64 if f.dtype == torch.int32 else torch.complex128
    return torch.stack([z1, z2], dim=-1).to(dtype)


def quantize_kick(
    delta: torch.Tensor,
    *,
    frac_bits: int = DEFAULT_FRAC_BITS,
    mod_bits: int = DEFAULT_MOD_BITS,
) -> torch.Tensor:
    """Round collision kick to fixed-point lattice (rounding isolated in gate)."""
    return encode_spinor(delta, frac_bits=frac_bits, mod_bits=mod_bits)


def leapfrog_combine(
    f_curr: torch.Tensor,
    f_past: torch.Tensor,
    f_kick: torch.Tensor,
    *,
    mod_bits: int = DEFAULT_MOD_BITS,
) -> torch.Tensor:
    """Z⁺ + Z⁻ = 2Z + ⌊𝒩⌋  ⇔  Z⁺ = 2Z + ⌊𝒩⌋ − Z⁻  in Z_N[i]."""
    return leapfrog_next(f_curr, f_past, f_kick, mod_bits=mod_bits)


def leapfrog_invert(
    f_curr: torch.Tensor,
    f_next: torch.Tensor,
    f_kick: torch.Tensor,
    *,
    mod_bits: int = DEFAULT_MOD_BITS,
) -> torch.Tensor:
    """Recover Z⁻ from the same modular second-order identity (exact T⁻¹)."""
    return leapfrog_past(f_curr, f_next, f_kick, mod_bits=mod_bits)


def vacuum_amplitude_quantum(*, frac_bits: int = DEFAULT_FRAC_BITS) -> float:
    """Smallest nonzero |z| on Q(frac_bits) lattice — one Planck amplitude quanta."""
    return 1.0 / scale(frac_bits)
