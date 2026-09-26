"""Exact Fourier symbols for translation-invariant stencils on a 3D torus (FCC N12)."""
from __future__ import annotations

import cmath
import math

from mt_ca.laplacian import _FCC_OFFSETS


def fcc_structure_factor(
    k: tuple[int, int, int],
    shape: tuple[int, int, int],
) -> complex:
    """λ_st(k) = Σ_{δ∈N12} exp(2π i k·δ / L) on nz×ny×nx torus."""
    nz, ny, nx = shape
    lengths = (nz, ny, nx)
    acc = 0.0 + 0.0j
    for dz, dy, dx in _FCC_OFFSETS:
        phase = 2.0 * math.pi * (
            (k[0] * dz / nz) + (k[1] * dy / ny) + (k[2] * dx / nx)
        )
        acc += cmath.exp(1j * phase)
    return acc


def scan_fcc_low_k(
    shape: tuple[int, int, int],
    *,
    max_k: int = 2,
) -> list[dict]:
    rows: list[dict] = []
    for kz in range(-max_k, max_k + 1):
        for ky in range(-max_k, max_k + 1):
            for kx in range(-max_k, max_k + 1):
                if kz == 0 and ky == 0 and kx == 0:
                    continue
                k = (kz, ky, kx)
                lam = fcc_structure_factor(k, shape)
                rows.append(
                    {
                        "k": k,
                        "lambda_st_re": round(lam.real, 6),
                        "lambda_st_im": round(lam.imag, 6),
                        "abs_lambda_st": round(abs(lam), 6),
                    }
                )
    rows.sort(key=lambda r: r["abs_lambda_st"], reverse=True)
    return rows
