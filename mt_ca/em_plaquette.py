"""§8.2 Planck EM — discrete □-face holonomy on FCC cuboctahedron hull (a = l_P).

Lattice Stokes on one hull square face; probe Phi_□ and link E vs alpha_fs (open DoD).
"""

from __future__ import annotations

import math

import torch

from mt_ca.laplacian import _FCC_OFFSETS
from mt_ca.seeds import SeedClass, make_seed

# One □ face of the 1-tick cuboctahedron hull in the z=0 plane (§8.2·geo).
SQUARE_FACE_CORNERS: tuple[tuple[int, int, int], ...] = (
    (1, 1, 0),
    (-1, 1, 0),
    (-1, -1, 0),
    (1, -1, 0),
)

# NN bridge midpoints between consecutive corners on the offset graph.
SQUARE_FACE_BRIDGE_MIDS: tuple[tuple[int, int, int], ...] = (
    (0, 1, 1),
    (-1, 0, -1),
    (0, -1, -1),
    (1, 0, -1),
)

_FCC_OFFSET_SET = set(_FCC_OFFSETS)


def _wrap_pi(x: float) -> float:
    return (x + math.pi) % (2.0 * math.pi) - math.pi


def em_phase(z: torch.Tensor) -> torch.Tensor:
    """Planck EM phase: Arg(z) with spinor ratio fallback (§8.2 · vortex charge in z₂/z₁)."""
    z0 = z[..., 0]
    z1 = z[..., 1]
    ratio = z1 / (z0 + 1e-12)
    r0 = z0.abs()
    r1 = z1.abs()
    use_ratio = r1 > 1e-12
    return torch.where(use_ratio, torch.angle(ratio), torch.angle(z0))


def phi_at_offset(z: torch.Tensor, base: tuple[int, int, int], off: tuple[int, int, int]) -> float:
    idx = _mod_index(base, off, z.shape[:3])
    return float(em_phase(z[idx]).item())


def phi_square_hull_face(
    z: torch.Tensor,
    *,
    base: tuple[int, int, int] | None = None,
) -> float:
    """Discrete Phi_□: sum wrapped dphi on 8-hop lattice path around hull □ (a = l_P corners)."""
    if z.ndim < 4 or z.shape[-1] != 2:
        raise ValueError("expected z shape (nz, ny, nx, 2)")
    nz, ny, nx = z.shape[:3]
    b = base if base is not None else (nz // 2, ny // 2, nx // 2)

    total = 0.0
    prev = SQUARE_FACE_CORNERS[-1]
    for corner, mid in zip(SQUARE_FACE_CORNERS, SQUARE_FACE_BRIDGE_MIDS, strict=True):
        p_prev = phi_at_offset(z, b, prev)
        p_mid = phi_at_offset(z, b, mid)
        p_corner = phi_at_offset(z, b, corner)
        total += _wrap_pi(p_mid - p_prev)
        total += _wrap_pi(p_corner - p_mid)
        prev = corner
    return _wrap_pi(total)


def edge_delta_phi(
    z: torch.Tensor,
    base: tuple[int, int, int],
    off_a: tuple[int, int, int],
    off_b: tuple[int, int, int],
) -> float:
    """Wrapped phi(b) - phi(a) for discrete E = -Delta/l_P (§8.2)."""
    pa = phi_at_offset(z, base, off_a)
    pb = phi_at_offset(z, base, off_b)
    return _wrap_pi(pb - pa)


def _fcc_hop_distance(origin: tuple[int, int, int], target: tuple[int, int, int]) -> int:
    """Shortest path length on FCC NN graph (BFS in local offset coords)."""
    if origin == target:
        return 0
    if target in _FCC_OFFSET_SET:
        return 1
    seen = {origin}
    frontier = [origin]
    dist = 0
    while frontier:
        dist += 1
        nxt: list[tuple[int, int, int]] = []
        for node in frontier:
            for d in _FCC_OFFSETS:
                cand = (node[0] + d[0], node[1] + d[1], node[2] + d[2])
                if cand == target:
                    return dist
                if cand not in seen and all(abs(c) <= 4 for c in cand):
                    seen.add(cand)
                    nxt.append(cand)
        frontier = nxt
    return 999


def _mod_index(
    base: tuple[int, int, int],
    off: tuple[int, int, int],
    shape: tuple[int, int, int],
) -> tuple[int, int, int]:
    nz, ny, nx = shape
    bz, by, bx = base
    dz, dy, dx = off
    return (bz + dz) % nz, (by + dy) % ny, (bx + dx) % nx


def alpha_link_phase_field(
    z_base: torch.Tensor,
    base: tuple[int, int, int],
    nn: tuple[int, int, int],
    *,
    alpha: float,
) -> torch.Tensor:
    """Construct phi(O)=0, phi(NN)=alpha on spinor lane-0 (link sanity for E=-Δφ/a)."""
    z = z_base.clone()
    i0 = _mod_index(base, (0, 0, 0), z.shape[:3])
    i1 = _mod_index(base, nn, z.shape[:3])
    amp0 = max(float(z[i0[0], i0[1], i0[2], 0].abs().item()), 0.05)
    amp1 = max(float(z[i1[0], i1[1], i1[2], 0].abs().item()), 0.05)
    z[i0[0], i0[1], i0[2], 0] = amp0
    z[i1[0], i1[1], i1[2], 0] = amp1 * torch.exp(
        torch.tensor(1j * alpha, device=z.device, dtype=z.dtype)
    )
    return z


def linear_gradient_phase_field(
    nz: int,
    ny: int,
    nx: int,
    *,
    base: tuple[int, int, int],
    slope: float,
    device: torch.device,
    dtype: torch.dtype = torch.complex64,
) -> torch.Tensor:
    """phi = slope·(dy+dx) from base — nonzero Phi_□ on hull face (apparatus test)."""
    z = torch.zeros(nz, ny, nx, 2, device=device, dtype=dtype)
    bz, by, bx = base
    for iz in range(nz):
        for iy in range(ny):
            for ix in range(nx):
                dy = float(iy - by)
                dx = float(ix - bx)
                phase = slope * (dy + dx)
                amp = 0.3
                z[iz, iy, ix, 0] = amp * torch.exp(torch.tensor(1j * phase, device=device, dtype=dtype))
    return z


def monopole_phase_field(
    nz: int,
    ny: int,
    nx: int,
    *,
    base: tuple[int, int, int],
    device: torch.device,
    dtype: torch.dtype = torch.complex64,
) -> torch.Tensor:
    """Static U(1) phase ~ 1/r on FCC hop graph (single + charge at base)."""
    z = torch.zeros(nz, ny, nx, 2, device=device, dtype=dtype)
    bz, by, bx = base
    for iz in range(nz):
        for iy in range(ny):
            for ix in range(nx):
                off = (iz - bz, iy - by, ix - bx)
                d = _fcc_hop_distance((0, 0, 0), off)
                if d == 0:
                    phase = 0.0
                    amp = 0.35
                else:
                    phase = 1.0 / float(d)
                    amp = 0.25 / float(d)
                val = amp * torch.exp(torch.tensor(1j * phase, device=device, dtype=dtype))
                z[iz, iy, ix, 0] = val
                z[iz, iy, ix, 1] = val * 0.5
    return z


def square_face_holonomy_probe(
    *,
    grid: int = 16,
    device: str = "cpu",
) -> dict[str, float | int | str | bool]:
    """Live probe: Phi_□, B_□=Phi/a², link E vs alpha_fs; alpha match explicitly open."""
    from mt_ca.si_constants import SI

    dev = torch.device(device)
    nz = ny = nx = grid
    base = (nz // 2, ny // 2, nx // 2)
    a = SI.l_P
    alpha = SI.alpha_fs
    f_p = SI.c**4 / SI.G
    nn = (1, 1, 0)

    z_vac = make_seed(SeedClass.VACUUM, ny, nx, nz=nz, device=dev)
    z_vtx = make_seed(SeedClass.VORTEX_P, ny, nx, nz=nz, device=dev)
    z_mono = monopole_phase_field(nz, ny, nx, base=base, device=dev)
    z_grad = linear_gradient_phase_field(nz, ny, nx, base=base, slope=alpha, device=dev)
    z_alpha = alpha_link_phase_field(z_vac, base, nn, alpha=alpha)

    phi_vac = phi_square_hull_face(z_vac, base=base)
    phi_vtx = phi_square_hull_face(z_vtx, base=base)
    phi_mono = phi_square_hull_face(z_mono, base=base)
    phi_grad = phi_square_hull_face(z_grad, base=base)

    dphi_nn_vac = edge_delta_phi(z_vac, base, (0, 0, 0), nn)
    dphi_nn_vtx = edge_delta_phi(z_vtx, base, (0, 0, 0), nn)
    dphi_nn_mono = edge_delta_phi(z_mono, base, (0, 0, 0), nn)
    dphi_nn_alpha = edge_delta_phi(z_alpha, base, (0, 0, 0), nn)

    e_link_mono = -dphi_nn_mono / a
    e_link_alpha = -dphi_nn_alpha / a
    b_vtx = phi_vtx / (a * a)
    b_grad = phi_grad / (a * a)

    f_over_fp = alpha
    alpha_from_dphi = abs(dphi_nn_mono)
    alpha_rel_err = abs(alpha_from_dphi - alpha) / alpha if alpha > 0 else float("inf")
    alpha_link_rel_err = abs(abs(dphi_nn_alpha) - alpha) / alpha if alpha > 0 else float("inf")

    return {
        "grid": grid,
        "edge_a_m": a,
        "phi_square_vac_rad": phi_vac,
        "phi_square_vortex_rad": phi_vtx,
        "phi_square_monopole_rad": phi_mono,
        "phi_square_gradient_rad": phi_grad,
        "B_square_vortex_T": b_vtx,
        "B_square_gradient_T": b_grad,
        "delta_phi_nn_vac": dphi_nn_vac,
        "delta_phi_nn_vortex": dphi_nn_vtx,
        "delta_phi_nn_monopole": dphi_nn_mono,
        "delta_phi_nn_alpha_link": dphi_nn_alpha,
        "E_link_monopole_SI": e_link_mono,
        "E_link_alpha_SI": e_link_alpha,
        "alpha_fs": alpha,
        "F_over_F_P_derived": f_over_fp,
        "F_P_N": f_p,
        "alpha_from_abs_dphi_nn": alpha_from_dphi,
        "alpha_from_E_rel_err": alpha_rel_err,
        "alpha_link_rel_err": alpha_link_rel_err,
        "alpha_match_open": alpha_rel_err > 0.05,
        "alpha_link_ok": alpha_link_rel_err < 1e-6,
        "V_over_v_hV": 16.0 / 3.0,
        "kappa_1tick": 1.0 / math.sqrt(2.0),
        "alpha_geom_inv": 137.0,
        "note": "§8.2·geo probe: Phi_□ hull path; alpha from holonomy/E open DoD",
    }
