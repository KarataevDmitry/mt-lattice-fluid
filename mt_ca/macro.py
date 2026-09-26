"""T-layer macro-averaging operator (MODEL §4.1.1).

Integer binomial (1-2-1) separable filter — isotropic on von Neumann stencil,
not float Gaussian (avoids false reflections and exp() on macro-T).
"""

from __future__ import annotations

import torch
import torch.nn.functional as F

# Separable [1, 2, 1] / 4 — one pass ≡ 3×3 kernel with weights 1,2,1,2,4,2,1,2,1 over 16.
_BINOMIAL_1D = (1, 2, 1)


def binomial121_kernels(
    device: torch.device,
    dtype: torch.dtype,
) -> tuple[torch.Tensor, torch.Tensor]:
    """Horizontal and vertical (1-2-1)/4 conv weights for one von Neumann pass."""
    w = torch.tensor(_BINOMIAL_1D, device=device, dtype=dtype) / 4.0
    w_h = w.view(1, 1, 1, 3)
    w_v = w.view(1, 1, 3, 1)
    return w_h, w_v


def binomial121_pass(plane: torch.Tensor) -> torch.Tensor:
    """One isotropic (1-2-1)⊗(1-2-1) pass on a real scalar field."""
    x = plane.unsqueeze(0).unsqueeze(0)
    w_h, w_v = binomial121_kernels(plane.device, plane.dtype)
    x = F.conv2d(x, w_h, padding=(0, 1))
    x = F.conv2d(x, w_v, padding=(1, 0))
    return x.squeeze(0).squeeze(0)


def binomial121_smooth(plane: torch.Tensor, *, passes: int) -> torch.Tensor:
    """Repeat separable (1-2-1) passes — effective macro radius ≈ passes."""
    if passes < 1:
        raise ValueError("passes must be >= 1")
    out = plane
    for _ in range(passes):
        out = binomial121_pass(out)
    return out


def macro_average_spinor(
    z: torch.Tensor,
    *,
    radius: int,
    stride: int = 1,
    sigma: float | None = None,  # deprecated; ignored — binomial only
) -> torch.Tensor:
    """Φ(X) = (1-2-1)^{⊗2·R} z — integer binomial macro coarse on spinor components."""
    del sigma  # API compat; §4.1.1 uses binomial stencil only
    if z.ndim != 3 or z.shape[-1] != 2:
        raise ValueError(f"expected spinor (ny, nx, 2), got {tuple(z.shape)}")
    if radius < 1:
        raise ValueError("radius must be >= 1")

    comps: list[torch.Tensor] = []
    for c in (0, 1):
        re = binomial121_smooth(z[..., c].real, passes=radius)
        im = binomial121_smooth(z[..., c].imag, passes=radius)
        comps.append(torch.complex(re, im))

    phi = torch.stack(comps, dim=-1)
    if stride > 1:
        phi = phi[radius::stride, radius::stride]
    return phi


def macro_amplitude(
    z: torch.Tensor,
    *,
    radius: int,
    stride: int = 1,
    sigma: float | None = None,
    nu_viscosity_passes: int = 0,
) -> torch.Tensor:
    """|Φ| on macro grid — T amplitude macro (field density)."""
    phi = macro_average_spinor(z, radius=radius, stride=stride, sigma=sigma)
    amp = phi.abs().square().sum(dim=-1).sqrt()
    if nu_viscosity_passes > 0:
        amp = binomial121_smooth(amp, passes=nu_viscosity_passes)
    return amp


def macro_matter_b(
    z: torch.Tensor,
    *,
    radius: int,
    stride: int = 1,
) -> torch.Tensor:
    """⟨b⟩ macro coarse — ρ_matter primary, not |z|² (§5.0 · §5.2.3 IV)."""
    from mt_ca.topology import matter_occupancy_b_field

    b = matter_occupancy_b_field(z).to(torch.float32)
    coarse = binomial121_smooth(b, passes=radius)
    if stride > 1:
        coarse = coarse[radius::stride, radius::stride]
    return coarse


# Legacy name — returns 3×3 binomial stencil for one pass (sum = 1).
def gaussian_kernel(
    radius: int,
    *,
    sigma: float | None = None,
    device: torch.device | None = None,
    dtype: torch.dtype = torch.float32,
) -> torch.Tensor:
    del radius, sigma
    dev = device or torch.device("cpu")
    w = torch.tensor(_BINOMIAL_1D, device=dev, dtype=dtype)
    k = torch.outer(w, w)
    return k / k.sum()
