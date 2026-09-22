from __future__ import annotations

import math
from enum import Enum

import torch

from mt_ca.fixed_point import vacuum_amplitude_quantum


class SeedClass(str, Enum):
    VACUUM = "vacuum"
    IMPULSE = "impulse"
    PLANE_WAVE = "plane_wave"
    VORTEX_P = "vortex_p"
    VORTEX_M = "vortex_m"
    VORTEX_N2 = "vortex_n2"


def _mesh(ny: int, nx: int, device: torch.device, dtype: torch.dtype) -> tuple[torch.Tensor, torch.Tensor]:
    ys = torch.arange(ny, device=device, dtype=dtype)
    xs = torch.arange(nx, device=device, dtype=dtype)
    yy, xx = torch.meshgrid(ys, xs, indexing="ij")
    return yy, xx


def make_wave_packet(
    ny: int,
    nx: int,
    *,
    device: torch.device,
    dtype: torch.dtype = torch.complex64,
    amplitude: float = 0.5,
    sigma: float = 6.0,
) -> torch.Tensor:
    real_dtype = torch.float32 if dtype == torch.complex64 else torch.float64
    ys = torch.arange(ny, device=device, dtype=real_dtype)
    xs = torch.arange(nx, device=device, dtype=real_dtype)
    yy, xx = torch.meshgrid(ys, xs, indexing="ij")
    cy, cx = ny / 2.0, nx / 2.0
    env = (amplitude * torch.exp(-((yy - cy) ** 2 + (xx - cx) ** 2) / (2.0 * sigma ** 2))).to(dtype)
    c, s = math.cos(0.15), math.sin(0.15)
    return torch.stack([c * env, s * env], dim=-1)


def make_seed(
    seed_class: SeedClass,
    ny: int,
    nx: int,
    *,
    device: torch.device,
    dtype: torch.dtype = torch.complex64,
    amplitude: float | None = None,
    impulse_amplitude: float = 0.35,
    nz: int | None = None,
) -> torch.Tensor:
    """Spinor z=(z₁,z₂) ∈ ℂ² per cell. nz= → 3D (FCC)."""
    if amplitude is None:
        amplitude = vacuum_amplitude_quantum()
    real_dtype = torch.float32 if dtype == torch.complex64 else torch.float64

    if nz is not None:
        # 3D vacuum / impulse / soft vortex along z mid-plane
        if seed_class is SeedClass.VACUUM:
            shape = (nz, ny, nx)
            re1 = amplitude * torch.randn(*shape, device=device, dtype=real_dtype)
            im1 = amplitude * torch.randn(*shape, device=device, dtype=real_dtype)
            re2 = amplitude * torch.randn(*shape, device=device, dtype=real_dtype)
            im2 = amplitude * torch.randn(*shape, device=device, dtype=real_dtype)
            return torch.stack(
                [torch.complex(re1, im1).to(dtype), torch.complex(re2, im2).to(dtype)],
                dim=-1,
            )
        if seed_class is SeedClass.IMPULSE:
            z = torch.zeros(nz, ny, nx, 2, device=device, dtype=dtype)
            z[nz // 2, ny // 2, nx // 2, 0] = impulse_amplitude + 0j
            z[nz // 2, ny // 2, nx // 2, 1] = 0.1 * impulse_amplitude + 0j
            return z
        # soft 3D blob with azimuthal phase in xy (vortex tube)
        charge_map = {
            SeedClass.VORTEX_P: 1,
            SeedClass.VORTEX_M: -1,
            SeedClass.VORTEX_N2: 2,
            SeedClass.PLANE_WAVE: 0,
        }
        if seed_class in charge_map or seed_class is SeedClass.PLANE_WAVE:
            zs = torch.arange(nz, device=device, dtype=real_dtype)
            ys = torch.arange(ny, device=device, dtype=real_dtype)
            xs = torch.arange(nx, device=device, dtype=real_dtype)
            zz, yy, xx = torch.meshgrid(zs, ys, xs, indexing="ij")
            cz, cy, cx = nz / 2.0, ny / 2.0, nx / 2.0
            if seed_class is SeedClass.PLANE_WAVE:
                kx, ky, kz = 0.12, 0.08, 0.05
                wave = torch.exp(1j * (kx * xx + ky * yy + kz * zz))
                bump = torch.exp(
                    -((zz - cz) ** 2 + (yy - cy) ** 2 + (xx - cx) ** 2)
                    / (0.12 * min(nz, ny, nx)) ** 2
                )
                env = impulse_amplitude * bump * wave
                c, s = math.cos(0.125), math.sin(0.125)
                return torch.stack([(c * env).to(dtype), (s * env).to(dtype)], dim=-1)
            charge = charge_map[seed_class]
            radius = 0.08 * min(ny, nx)
            dy = yy - cy
            dx = xx - cx
            dz = zz - cz
            theta = torch.atan2(dy, dx)
            env = torch.exp(-(dy * dy + dx * dx + dz * dz) / (2.0 * radius * radius))
            chi = 1.2 * env
            z1 = torch.cos(chi / 2.0) * env
            z2 = torch.sin(chi / 2.0) * env * torch.exp(1j * charge * theta)
            return torch.stack([z1.to(dtype), z2.to(dtype)], dim=-1)
        raise ValueError(f"Unknown seed class: {seed_class}")

    yy, xx = _mesh(ny, nx, device, real_dtype)
    cy, cx = ny / 2.0, nx / 2.0

    if seed_class is SeedClass.VACUUM:
        re1 = amplitude * torch.randn(ny, nx, device=device, dtype=real_dtype)
        im1 = amplitude * torch.randn(ny, nx, device=device, dtype=real_dtype)
        re2 = amplitude * torch.randn(ny, nx, device=device, dtype=real_dtype)
        im2 = amplitude * torch.randn(ny, nx, device=device, dtype=real_dtype)
        z1 = torch.complex(re1, im1).to(dtype)
        z2 = torch.complex(re2, im2).to(dtype)
        return torch.stack([z1, z2], dim=-1)

    if seed_class is SeedClass.IMPULSE:
        z = torch.zeros(ny, nx, 2, device=device, dtype=dtype)
        z[int(cy), int(cx), 0] = impulse_amplitude + 0j
        z[int(cy), int(cx), 1] = 0.1 * impulse_amplitude + 0j
        return z

    if seed_class is SeedClass.PLANE_WAVE:
        kx, ky = 0.12, 0.08
        wave = torch.exp(1j * (kx * xx + ky * yy))
        bump = torch.exp(-((yy - cy) ** 2 + (xx - cx) ** 2) / (0.12 * min(ny, nx)) ** 2)
        env = impulse_amplitude * bump * wave
        c, s = math.cos(0.125), math.sin(0.125)
        return torch.stack([(c * env).to(dtype), (s * env).to(dtype)], dim=-1)

    charge_map = {
        SeedClass.VORTEX_P: 1,
        SeedClass.VORTEX_M: -1,
        SeedClass.VORTEX_N2: 2,
    }
    if seed_class in charge_map:
        charge = charge_map[seed_class]
        radius = 0.08 * min(ny, nx) if seed_class is not SeedClass.VORTEX_N2 else 0.1 * min(ny, nx)
        dy = yy - cy
        dx = xx - cx
        theta = torch.atan2(dy, dx)
        env = torch.exp(-(dy * dy + dx * dx) / (2.0 * radius * radius))
        chi = 1.2 * env
        z1 = torch.cos(chi / 2.0) * env
        z2 = torch.sin(chi / 2.0) * env * torch.exp(1j * charge * theta)
        return torch.stack([z1.to(dtype), z2.to(dtype)], dim=-1)

    raise ValueError(f"Unknown seed class: {seed_class}")
