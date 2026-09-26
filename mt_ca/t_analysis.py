"""T-layer: discrete analysis on the lattice (not M g).

DFT / spectral tools read macro structure and calibrate dispersion — they do not
replace local CA update. Bond continuity + SO(2) on N₄ are M operators (§5.2.1);
spectral continuity is a T spectral aid.
"""

from __future__ import annotations

import torch


def laplacian_eigenvalues(ny: int, nx: int, device: torch.device, dtype: torch.dtype) -> torch.Tensor:
    """Eigenvalues of von Neumann Δ₄ on periodic torus — for spectral macro only."""
    ky = 2.0 * torch.pi * torch.fft.fftfreq(ny, device=device, dtype=dtype)
    kx = 2.0 * torch.pi * torch.fft.fftfreq(nx, device=device, dtype=dtype)
    yy, xx = torch.meshgrid(ky, kx, indexing="ij")
    return 2.0 * (torch.cos(xx) + torch.cos(yy) - 2.0)


def spectral_apply(z: torch.Tensor, operator_fn) -> torch.Tensor:
    """Apply spectral operator f(Δ₄) via DFT — T-layer oracle, not one CA tick."""
    lam = laplacian_eigenvalues(z.shape[0], z.shape[1], z.device, z.real.dtype)
    z_hat = torch.fft.fft2(z)
    return torch.fft.ifft2(z_hat * operator_fn(lam)).to(z.dtype)


def spectral_unitary_reference(z: torch.Tensor, gamma: float) -> torch.Tensor:
    """exp(i·γ·Δ₄) z — calibrate local_ca dispersion / A3 upper bound."""
    return spectral_apply(z, lambda lam: torch.exp(1j * gamma * lam))


def amplitude_spectrum(z: torch.Tensor) -> torch.Tensor:
    """|FFT(z)|² — discrete mode power on the whole field."""
    return torch.fft.fft2(z).abs().square()


def block_mean(z: torch.Tensor, block: int) -> torch.Tensor:
    """Legacy block mean |⟨z⟩_B| — prefer macro_amplitude (§4.1.1)."""
    ny, nx = z.shape
    by, bx = ny // block, nx // block
    trimmed = z[: by * block, : bx * block]
    blocks = trimmed.reshape(by, block, bx, block)
    return blocks.mean(dim=(1, 3))


def macro_amplitude_plane(
    z: torch.Tensor,
    *,
    radius: int,
    stride: int = 8,
    sigma: float | None = None,
) -> torch.Tensor:
    """Integer (1-2-1) binomial macro amplitude |Φ| — canonical T coarse (§4.1.1)."""
    from mt_ca.macro import macro_amplitude

    if z.ndim == 3 and z.shape[-1] == 2:
        return macro_amplitude(z, radius=radius, stride=stride, sigma=sigma)
    return macro_amplitude(
        torch.stack([z, torch.zeros_like(z)], dim=-1),
        radius=radius,
        stride=stride,
        sigma=sigma,
    )


def estimate_phase_velocity_plane_wave(
    z_before: torch.Tensor,
    z_after: torch.Tensor,
    *,
    kx: float,
    ky: float,
) -> float:
    """Crude ω from phase advance of dominant plane-wave component (T diagnostic)."""
    ny, nx = z_before.shape
    ys = torch.arange(ny, device=z_before.device, dtype=z_before.real.dtype)
    xs = torch.arange(nx, device=z_before.device, dtype=z_before.real.dtype)
    yy, xx = torch.meshgrid(ys, xs, indexing="ij")
    mode = torch.exp(1j * (kx * xx + ky * yy))
    c0 = (z_before * mode.conj()).sum()
    c1 = (z_after * mode.conj()).sum()
    if c0.abs() < 1e-12 or c1.abs() < 1e-12:
        return float("nan")
    return float((torch.angle(c1) - torch.angle(c0)).item())
