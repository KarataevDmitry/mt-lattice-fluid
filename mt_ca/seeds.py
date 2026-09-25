from __future__ import annotations

import math
from enum import Enum

import torch

from mt_ca.fixed_point import decode_spinor, encode_spinor
from mt_ca.si_constants import HV, heisenberg_phi_min_disc
from mt_ca.z_ring import mod_lane


class SeedClass(str, Enum):
    """Physical IC classes on the lattice (§0.5 · §5 · Seed taxonomy).

    VACUUM — control only: gauge-fixed class 0 (Φ=0 frozen), not live habitat.
    VACUUM_BOIL — live habitat: every cell a brick; NN Δclass=±1 ⇒ Δφ=Δφ_min (A5).
    IMPULSE / PLANE_WAVE / VORTEX_* — excitations on VACUUM_BOIL (2D); no void, no dead ocean.
    """

    VACUUM = "vacuum"
    VACUUM_BOIL = "vacuum_boil"
    IMPULSE = "impulse"
    PLANE_WAVE = "plane_wave"
    VORTEX_P = "vortex_p"
    VORTEX_M = "vortex_m"
    VORTEX_N2 = "vortex_n2"


def heisenberg_phase_tick(
    phase_class: int,
    *,
    phase_bits: int = HV.phase_bits,
    n_phi: int = HV.N_phi,
) -> int:
    """Tick on N_ring for Heisenberg phase class k ∈ {0,…,N_φ−1} (§3.12.6).

    N_φ = ⌈2π/Δφ_min⌉ = 13; step = Δφ_disc = round(N_ring·Δφ_min/2π).
    Not a free angle and not RNG — discrete physical orientations of the brick.
    """
    if not 0 <= phase_class < n_phi:
        raise ValueError(f"phase_class must be in 0..{n_phi - 1}, got {phase_class}")
    delta = heisenberg_phi_min_disc(phase_bits=phase_bits)
    n_ring = 1 << phase_bits
    return int(phase_class * delta) % n_ring


def _mesh(ny: int, nx: int, device: torch.device, dtype: torch.dtype) -> tuple[torch.Tensor, torch.Tensor]:
    ys = torch.arange(ny, device=device, dtype=dtype)
    xs = torch.arange(nx, device=device, dtype=dtype)
    yy, xx = torch.meshgrid(ys, xs, indexing="ij")
    return yy, xx


def vacuum_ocean_fixed(
    *spatial: int,
    device: torch.device,
    mod_bits: int = HV.mod_bits,
    frac_bits: int = HV.frac_bits,
    phase_bits: int = HV.phase_bits,
    phase_class: int = 0,
) -> torch.Tensor:
    """Full-lattice vacuum IC on Z_N[i] — every cell a complete brick (§0.5 · §3.12.6).

    Each cell: one amplitude quantum + one Heisenberg phase class (N_φ = 13 bins).
    Default ``phase_class=0`` is the U(1)_vac gauge-fixed representative — not RNG.
    Both spinor components share the class (vacuum has no relative topological charge).
    Returns int32 (…, 4).
    """
    if not spatial:
        raise ValueError("spatial shape required")
    _ = frac_bits
    n_ring = 1 << phase_bits
    q = 1  # one Planck amplitude quantum in fixed-point lanes
    tick = heisenberg_phase_tick(phase_class, phase_bits=phase_bits)
    tick1 = torch.full(spatial, tick, device=device, dtype=torch.int64)
    tick2 = torch.full(spatial, tick, device=device, dtype=torch.int64)
    ang1 = tick1.to(torch.float64) * (2.0 * math.pi / n_ring)
    ang2 = tick2.to(torch.float64) * (2.0 * math.pi / n_ring)
    re1 = torch.round(q * torch.cos(ang1)).to(torch.int64)
    im1 = torch.round(q * torch.sin(ang1)).to(torch.int64)
    re2 = torch.round(q * torch.cos(ang2)).to(torch.int64)
    im2 = torch.round(q * torch.sin(ang2)).to(torch.int64)
    dead1 = (re1 == 0) & (im1 == 0)
    dead2 = (re2 == 0) & (im2 == 0)
    re1 = torch.where(dead1, torch.ones_like(re1), re1)
    re2 = torch.where(dead2, torch.ones_like(re2), re2)
    f = torch.stack([re1, im1, re2, im2], dim=-1)
    return mod_lane(f, mod_bits).to(torch.int32)


def _filled_brick_from_phase_class(
    phase_class: torch.Tensor,
    *,
    device: torch.device,
    mod_bits: int = HV.mod_bits,
    phase_bits: int = HV.phase_bits,
) -> torch.Tensor:
    """Encode a per-cell Heisenberg class grid into Z_N[i] (filled lattice, no void)."""
    if phase_class.dim() not in (2, 3):
        raise ValueError("phase_class must be 2D (ny,nx) or 3D (nz,ny,nx)")
    n_ring = 1 << phase_bits
    delta = heisenberg_phi_min_disc(phase_bits=phase_bits)
    tick = (phase_class.to(torch.int64) * int(delta)) % n_ring
    q = 1
    ang = tick.to(torch.float64) * (2.0 * math.pi / n_ring)
    re = torch.round(q * torch.cos(ang)).to(torch.int64)
    im = torch.round(q * torch.sin(ang)).to(torch.int64)
    dead = (re == 0) & (im == 0)
    re = torch.where(dead, torch.ones_like(re), re)
    f = torch.stack([re, im, re, im], dim=-1)
    return mod_lane(f, mod_bits).to(torch.int32)


def vacuum_boil_fixed(
    *spatial: int,
    device: torch.device,
    mod_bits: int = HV.mod_bits,
    frac_bits: int = HV.frac_bits,
    phase_bits: int = HV.phase_bits,
    n_phi: int = HV.N_phi,
    class_dy: int = 1,
    class_dx: int = 1,
    class_offset: int = 0,
) -> torch.Tensor:
    """Full-lattice A5 boil — every cell a Heisenberg brick (§5.0 · §3.12.6 · §6 bath).

    Canon: пустоты нет; пространство заполнено. Brick = one amplitude quantum +
    one phase class k∈{0,…,N_φ−1}. NN along axes differ by ±1 class ⇒ Δφ=Δφ_min.

    phase_class(y,x) = (class_dy·y + class_dx·x + class_offset) mod N_φ
    tick = heisenberg_phase_tick(class) — discrete brick orientations, NOT a free
    N_ring plane-wave ramp (that was the rejected «stripe» ring-scan family).

    Default class_dy=class_dx=1, offset=0. No RNG.
    """
    if len(spatial) != 2:
        raise ValueError("vacuum_boil_fixed currently 2D (ny, nx) only")
    _ = frac_bits
    ny, nx = spatial
    dy = int(class_dy) % n_phi
    dx = int(class_dx) % n_phi
    off = int(class_offset) % n_phi
    yy, xx = torch.meshgrid(
        torch.arange(ny, device=device, dtype=torch.int64),
        torch.arange(nx, device=device, dtype=torch.int64),
        indexing="ij",
    )
    phase_class = (dy * yy + dx * xx + off) % n_phi
    return _filled_brick_from_phase_class(
        phase_class, device=device, mod_bits=mod_bits, phase_bits=phase_bits
    )


def vacuum_ice_fixed(
    ny: int,
    nx: int,
    *,
    device: torch.device,
    mod_bits: int = HV.mod_bits,
    frac_bits: int = HV.frac_bits,
    phase_bits: int = HV.phase_bits,
    n_phi: int = HV.N_phi,
    phase_class: int = 0,
) -> torch.Tensor:
    """META §3.2 phase III — synchronous ω, uniform Heisenberg brick (filled, no void).

    Macro-T: «лёд» / пустота. Micro-M: every hV occupied, NN Δclass=0 (not boil).
    """
    _ = frac_bits
    base = int(phase_class) % n_phi
    pc = torch.full((ny, nx), base, device=device, dtype=torch.int64)
    return _filled_brick_from_phase_class(
        pc, device=device, mod_bits=mod_bits, phase_bits=phase_bits
    )


def vacuum_boil_fixed_3d(
    nz: int,
    ny: int,
    nx: int,
    *,
    device: torch.device,
    mod_bits: int = HV.mod_bits,
    frac_bits: int = HV.frac_bits,
    phase_bits: int = HV.phase_bits,
    n_phi: int = HV.N_phi,
    class_dz: int = 1,
    class_dy: int = 1,
    class_dx: int = 1,
    class_offset: int = 0,
) -> torch.Tensor:
    """3+1 FCC habitat — filled brick ocean (§1.6 · §0.5)."""
    _ = frac_bits
    dz = int(class_dz) % n_phi
    dy = int(class_dy) % n_phi
    dx = int(class_dx) % n_phi
    off = int(class_offset) % n_phi
    zz, yy, xx = torch.meshgrid(
        torch.arange(nz, device=device, dtype=torch.int64),
        torch.arange(ny, device=device, dtype=torch.int64),
        torch.arange(nx, device=device, dtype=torch.int64),
        indexing="ij",
    )
    phase_class = (dz * zz + dy * yy + dx * xx + off) % n_phi
    return _filled_brick_from_phase_class(
        phase_class, device=device, mod_bits=mod_bits, phase_bits=phase_bits
    )


def vacuum_ice_fixed_3d(
    nz: int,
    ny: int,
    nx: int,
    *,
    device: torch.device,
    mod_bits: int = HV.mod_bits,
    frac_bits: int = HV.frac_bits,
    phase_bits: int = HV.phase_bits,
    n_phi: int = HV.N_phi,
    phase_class: int = 0,
) -> torch.Tensor:
    """3+1 synchronous ice — uniform Heisenberg class on filled FCC lattice."""
    _ = frac_bits
    base = int(phase_class) % n_phi
    pc = torch.full((nz, ny, nx), base, device=device, dtype=torch.int64)
    return _filled_brick_from_phase_class(
        pc, device=device, mod_bits=mod_bits, phase_bits=phase_bits
    )


def boil_ocean_spinor_3d(
    nz: int,
    ny: int,
    nx: int,
    *,
    device: torch.device,
    dtype: torch.dtype = torch.complex64,
    mod_bits: int = HV.mod_bits,
    frac_bits: int = HV.frac_bits,
    phase_bits: int = HV.phase_bits,
    class_dz: int = 1,
    class_dy: int = 1,
    class_dx: int = 1,
    class_offset: int = 0,
) -> torch.Tensor:
    f = vacuum_boil_fixed_3d(
        nz,
        ny,
        nx,
        device=device,
        mod_bits=mod_bits,
        frac_bits=frac_bits,
        phase_bits=phase_bits,
        class_dz=class_dz,
        class_dy=class_dy,
        class_dx=class_dx,
        class_offset=class_offset,
    )
    return decode_spinor(f, frac_bits=frac_bits, mod_bits=mod_bits).to(dtype)


def vacuum_ice_phase_shift_fixed_3d(
    nz: int,
    ny: int,
    nx: int,
    *,
    device: torch.device,
    mod_bits: int = HV.mod_bits,
    frac_bits: int = HV.frac_bits,
    phase_bits: int = HV.phase_bits,
    n_phi: int = HV.N_phi,
    base_class: int = 0,
    shift_kind: str = "sphere",
    center: tuple[int, int, int] | None = None,
    radius: int = 12,
    delta_class: int = 1,
) -> torch.Tensor:
    """3+1 IV→I: uniform ice + deterministic local class bump."""
    _ = frac_bits
    base = int(base_class) % n_phi
    delta = int(delta_class) % n_phi
    zz, yy, xx = torch.meshgrid(
        torch.arange(nz, device=device, dtype=torch.int64),
        torch.arange(ny, device=device, dtype=torch.int64),
        torch.arange(nx, device=device, dtype=torch.int64),
        indexing="ij",
    )
    pc = torch.full((nz, ny, nx), base, device=device, dtype=torch.int64)
    if shift_kind == "sphere":
        cz, cy, cx = center if center is not None else (nz // 2, ny // 2, nx // 2)
        mask = (zz - cz) ** 2 + (yy - cy) ** 2 + (xx - cx) ** 2 <= int(radius) ** 2
        pc = torch.where(mask, (pc + delta) % n_phi, pc)
    elif shift_kind == "wall":
        mask = xx >= nx // 2
        pc = torch.where(mask, (pc + delta) % n_phi, pc)
    elif shift_kind == "ripple":
        pc = (pc + delta * ((xx + yy + zz) % n_phi)) % n_phi
    else:
        raise ValueError(f"Unknown shift_kind: {shift_kind}")
    return _filled_brick_from_phase_class(
        pc, device=device, mod_bits=mod_bits, phase_bits=phase_bits
    )


def ice_ocean_spinor_3d(
    nz: int,
    ny: int,
    nx: int,
    *,
    device: torch.device,
    dtype: torch.dtype = torch.complex64,
    mod_bits: int = HV.mod_bits,
    frac_bits: int = HV.frac_bits,
    phase_bits: int = HV.phase_bits,
    n_phi: int = HV.N_phi,
    phase_class: int = 0,
    shift_kind: str | None = None,
    center: tuple[int, int, int] | None = None,
    radius: int = 12,
    delta_class: int = 1,
) -> torch.Tensor:
    """Decode 3+1 ice (+ optional deterministic shift) to ℂ²."""
    if shift_kind is None:
        f = vacuum_ice_fixed_3d(
            nz,
            ny,
            nx,
            device=device,
            mod_bits=mod_bits,
            frac_bits=frac_bits,
            phase_bits=phase_bits,
            n_phi=n_phi,
            phase_class=phase_class,
        )
    else:
        f = vacuum_ice_phase_shift_fixed_3d(
            nz,
            ny,
            nx,
            device=device,
            mod_bits=mod_bits,
            frac_bits=frac_bits,
            phase_bits=phase_bits,
            n_phi=n_phi,
            base_class=phase_class,
            shift_kind=shift_kind,
            center=center,
            radius=radius,
            delta_class=delta_class,
        )
    return decode_spinor(f, frac_bits=frac_bits, mod_bits=mod_bits).to(dtype)


def vacuum_ice_phase_shift_fixed(
    ny: int,
    nx: int,
    *,
    device: torch.device,
    mod_bits: int = HV.mod_bits,
    frac_bits: int = HV.frac_bits,
    phase_bits: int = HV.phase_bits,
    n_phi: int = HV.N_phi,
    base_class: int = 0,
    shift_kind: str = "disk",
    center: tuple[int, int] | None = None,
    radius: int = 12,
    delta_class: int = 1,
) -> torch.Tensor:
    """META §3.2 IV→I: uniform ice + deterministic local class bump (no RNG).

    shift_kind:
      disk — bump class in a disk (domain nucleation)
      wall — half-plane offset (domain wall)
      ripple — minimal coherent k·r on top of ice (not full PLANE_WAVE seed)
    """
    _ = frac_bits
    base = int(base_class) % n_phi
    delta = int(delta_class) % n_phi
    yy, xx = torch.meshgrid(
        torch.arange(ny, device=device, dtype=torch.int64),
        torch.arange(nx, device=device, dtype=torch.int64),
        indexing="ij",
    )
    pc = torch.full((ny, nx), base, device=device, dtype=torch.int64)
    if shift_kind == "disk":
        cy, cx = center if center is not None else (ny // 2, nx // 2)
        mask = (yy - cy) ** 2 + (xx - cx) ** 2 <= int(radius) ** 2
        pc = torch.where(mask, (pc + delta) % n_phi, pc)
    elif shift_kind == "wall":
        mask = xx >= nx // 2
        pc = torch.where(mask, (pc + delta) % n_phi, pc)
    elif shift_kind == "ripple":
        kx, ky = 1, 1
        ripple = ((kx * xx + ky * yy) % n_phi).to(torch.int64)
        pc = (pc + delta * ripple) % n_phi
    else:
        raise ValueError(f"Unknown shift_kind: {shift_kind}")
    return _filled_brick_from_phase_class(
        pc, device=device, mod_bits=mod_bits, phase_bits=phase_bits
    )


def ice_ocean_spinor(
    ny: int,
    nx: int,
    *,
    device: torch.device,
    dtype: torch.dtype = torch.complex64,
    mod_bits: int = HV.mod_bits,
    frac_bits: int = HV.frac_bits,
    phase_bits: int = HV.phase_bits,
    n_phi: int = HV.N_phi,
    phase_class: int = 0,
    shift_kind: str | None = None,
    center: tuple[int, int] | None = None,
    radius: int = 12,
    delta_class: int = 1,
) -> torch.Tensor:
    """Decode ice (+ optional deterministic shift) to ℂ²."""
    if shift_kind is None:
        f = vacuum_ice_fixed(
            ny,
            nx,
            device=device,
            mod_bits=mod_bits,
            frac_bits=frac_bits,
            phase_bits=phase_bits,
            n_phi=n_phi,
            phase_class=phase_class,
        )
    else:
        f = vacuum_ice_phase_shift_fixed(
            ny,
            nx,
            device=device,
            mod_bits=mod_bits,
            frac_bits=frac_bits,
            phase_bits=phase_bits,
            n_phi=n_phi,
            base_class=phase_class,
            shift_kind=shift_kind,
            center=center,
            radius=radius,
            delta_class=delta_class,
        )
    return decode_spinor(f, frac_bits=frac_bits, mod_bits=mod_bits).to(dtype)


def vacuum_ocean_spinor(
    *spatial: int,
    device: torch.device,
    dtype: torch.dtype = torch.complex64,
    mod_bits: int = HV.mod_bits,
    frac_bits: int = HV.frac_bits,
    phase_bits: int = HV.phase_bits,
    phase_class: int = 0,
) -> torch.Tensor:
    """Decode vacuum ocean to ℂ² readout (evolution still owns Z_N)."""
    f = vacuum_ocean_fixed(
        *spatial,
        device=device,
        mod_bits=mod_bits,
        frac_bits=frac_bits,
        phase_bits=phase_bits,
        phase_class=phase_class,
    )
    return decode_spinor(f, frac_bits=frac_bits, mod_bits=mod_bits).to(dtype)


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


def _excitation_2d(
    seed_class: SeedClass,
    ny: int,
    nx: int,
    *,
    device: torch.device,
    dtype: torch.dtype,
    impulse_amplitude: float,
) -> torch.Tensor:
    real_dtype = torch.float32 if dtype == torch.complex64 else torch.float64
    yy, xx = _mesh(ny, nx, device, real_dtype)
    cy, cx = ny / 2.0, nx / 2.0

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


def _excitation_3d(
    seed_class: SeedClass,
    nz: int,
    ny: int,
    nx: int,
    *,
    device: torch.device,
    dtype: torch.dtype,
    impulse_amplitude: float,
) -> torch.Tensor:
    real_dtype = torch.float32 if dtype == torch.complex64 else torch.float64
    zs = torch.arange(nz, device=device, dtype=real_dtype)
    ys = torch.arange(ny, device=device, dtype=real_dtype)
    xs = torch.arange(nx, device=device, dtype=real_dtype)
    zz, yy, xx = torch.meshgrid(zs, ys, xs, indexing="ij")
    cz, cy, cx = nz / 2.0, ny / 2.0, nx / 2.0

    if seed_class is SeedClass.IMPULSE:
        z = torch.zeros(nz, ny, nx, 2, device=device, dtype=dtype)
        z[nz // 2, ny // 2, nx // 2, 0] = impulse_amplitude + 0j
        z[nz // 2, ny // 2, nx // 2, 1] = 0.1 * impulse_amplitude + 0j
        return z

    if seed_class is SeedClass.PLANE_WAVE:
        kx, ky, kz = 0.12, 0.08, 0.05
        wave = torch.exp(1j * (kx * xx + ky * yy + kz * zz))
        bump = torch.exp(
            -((zz - cz) ** 2 + (yy - cy) ** 2 + (xx - cx) ** 2) / (0.12 * min(nz, ny, nx)) ** 2
        )
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
    mod_bits: int = HV.mod_bits,
    frac_bits: int = HV.frac_bits,
    phase_bits: int = HV.phase_bits,
) -> torch.Tensor:
    """Spinor field on a filled lattice (§0.5 · A5 — no void).

    VACUUM = frozen gauge control (Φ=0). Habitat for physics sims = VACUUM_BOIL.
    Excitations (2D) sit on boiling ocean, not on dead class-0 ocean.
    """
    _ = amplitude
    spatial = (nz, ny, nx) if nz is not None else (ny, nx)
    if seed_class is SeedClass.VACUUM:
        return vacuum_ocean_spinor(
            *spatial,
            device=device,
            dtype=dtype,
            mod_bits=mod_bits,
            frac_bits=frac_bits,
            phase_bits=phase_bits,
            phase_class=0,
        )

    if seed_class is SeedClass.VACUUM_BOIL:
        if nz is not None:
            return boil_ocean_spinor_3d(
                nz,
                ny,
                nx,
                device=device,
                dtype=dtype,
                mod_bits=mod_bits,
                frac_bits=frac_bits,
                phase_bits=phase_bits,
            )
        f_boil = vacuum_boil_fixed(
            ny,
            nx,
            device=device,
            mod_bits=mod_bits,
            frac_bits=frac_bits,
            phase_bits=phase_bits,
        )
        return decode_spinor(f_boil, frac_bits=frac_bits, mod_bits=mod_bits).to(dtype)

    if nz is None:
        f_boil = vacuum_boil_fixed(
            ny,
            nx,
            device=device,
            mod_bits=mod_bits,
            frac_bits=frac_bits,
            phase_bits=phase_bits,
        )
        ocean = decode_spinor(f_boil, frac_bits=frac_bits, mod_bits=mod_bits).to(dtype)
    else:
        ocean = boil_ocean_spinor_3d(
            nz,
            ny,
            nx,
            device=device,
            dtype=dtype,
            mod_bits=mod_bits,
            frac_bits=frac_bits,
            phase_bits=phase_bits,
        )

    if nz is not None:
        exc = _excitation_3d(
            seed_class, nz, ny, nx, device=device, dtype=dtype, impulse_amplitude=impulse_amplitude
        )
    else:
        exc = _excitation_2d(
            seed_class, ny, nx, device=device, dtype=dtype, impulse_amplitude=impulse_amplitude
        )
    z = ocean + exc
    f = encode_spinor(z, frac_bits=frac_bits, mod_bits=mod_bits, gauge_fix=False)
    return decode_spinor(f, frac_bits=frac_bits, mod_bits=mod_bits).to(dtype)
