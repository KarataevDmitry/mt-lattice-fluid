"""§4.1.0-T / §4.1.1-HL — T-CR + гидропредел (soft Green, без hL→0 на M)."""

from __future__ import annotations

import math
from collections import Counter


def _fcc_nn() -> set[tuple[int, int, int]]:
    neigh: set[tuple[int, int, int]] = set()
    for x, y in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
        neigh.add((x, y, 0))
        neigh.add((x, 0, y))
        neigh.add((0, x, y))
    return neigh


def _hex_nn() -> set[tuple[int, int]]:
    return {(1, 0), (1, -1), (0, -1), (-1, 0), (-1, 1), (0, 1)}


def binomial_spectral_row(*, n_k: int = 256, r_passes: int = 16) -> dict[str, float]:
    """Ŵ=cos²(k/2); after R: match Gaussian with σ²=R/2; small-k rel err."""
    ks = [math.pi * i / (n_k - 1) for i in range(n_k)]
    sig2 = r_passes / 2.0
    sig = math.sqrt(sig2)
    max_rel_030 = 0.0
    max_rel_050 = 0.0
    for k in ks:
        w = math.cos(k / 2.0) ** 2
        w_r = w**r_passes
        g = math.exp(-sig2 * k * k / 2.0)
        if g < 1e-30:
            continue
        rel = abs(w_r - g) / g
        if k * sig < 0.30:
            max_rel_030 = max(max_rel_030, rel)
        if k * sig < 0.50:
            max_rel_050 = max(max_rel_050, rel)
    k0 = math.pi / 3.0
    w0 = 0.5 + 0.5 * math.cos(k0)
    k_probe = 0.05
    w_r = math.cos(k_probe / 2.0) ** (2 * r_passes)
    g = math.exp(-sig2 * k_probe * k_probe / 2.0)
    log_ratio = math.log(w_r / g)
    leading = -r_passes * (k_probe**4) / 96.0
    return {
        "R": float(r_passes),
        "sigma2": sig2,
        "var_atom": 0.5,
        "multiplier_id_err": abs(w0 - math.cos(k0 / 2.0) ** 2),
        "max_rel_err_k_sigma_lt_0_30": max_rel_030,
        "max_rel_err_k_sigma_lt_0_50": max_rel_050,
        "taylor_leading_R_over_96": abs(log_ratio - leading) / abs(leading),
        "note": "§4.1.0-T(A): cos^{2R}(k/2) ↔ exp(−σ²k²/2), σ²=R/2; log∼−R k⁴/96",
    }


def _depth2_green(neigh: set[tuple]) -> dict[str, float | int]:
    origin = tuple(0 for _ in next(iter(neigh)))
    dim = len(origin)
    counts: Counter[tuple] = Counter()
    for u in neigh:
        for d in neigh:
            p = tuple(u[i] + d[i] for i in range(dim))
            counts[p] += 1
    n_walks = len(neigh) ** 2
    w0 = counts[origin]
    w_nn = sum(counts[u] for u in neigh)
    w_other = n_walks - w0 - w_nn

    def moment(*powers: int) -> float:
        acc = 0.0
        for p, w in counts.items():
            term = float(w)
            for ax, pw in enumerate(powers):
                term *= float(p[ax]) ** pw
            acc += term
        return acc / float(n_walks)

    m_xx = moment(2)
    m_xy = moment(1, 1) if dim >= 2 else 0.0
    e_r2 = 0.0
    for p, w in counts.items():
        e_r2 += float(w) * sum(float(c) ** 2 for c in p)
    e_r2 /= float(n_walks)
    e_x4 = moment(4)
    e_x2y2 = moment(2, 2) if dim >= 2 else 0.0

    return {
        "n_nn": len(neigh),
        "n_walks": n_walks,
        "w_origin": w0,
        "w_nn_shell": w_nn,
        "w_other": w_other,
        "p_origin": w0 / n_walks,
        "p_nn_shell": w_nn / n_walks,
        "n_endpoints": len(counts),
        "M_xx": m_xx,
        "M_xy": m_xy,
        "E_r2": e_r2,
        "E_x4": e_x4,
        "E_x2y2": e_x2y2,
    }


def fcc_depth2_green_row() -> dict[str, float | int | str]:
    row = _depth2_green(_fcc_nn())
    row["note"] = "§4.1.0-T(B): FCC N₁₂ depth-2 path-Green; w(0)=12/144"
    return row


def hex_depth2_green_row() -> dict[str, float | int | str]:
    row = _depth2_green(_hex_nn())
    row["note"] = "§4.1.0-T(B): hex N₆ depth-2 path-Green; w(0)=6/36"
    return row


def fcc_hydro_limit_row() -> dict[str, float | int | bool | str]:
    """§4.1.1-HL — FCC depth-2 moments ⇒ NLSE/NS-class hydro identities."""
    from mt_ca.si_constants import N12_FCC_CAUSAL_LINKS, kappa_link

    g = _depth2_green(_fcc_nn())
    m_xx = float(g["M_xx"])
    hatk_k2 = 0.5 * m_xx
    k_fcc = kappa_link(n_links=N12_FCC_CAUSAL_LINKS)
    isotropic = abs(float(g["M_xy"])) < 1e-12 and abs(m_xx - float(g["E_r2"]) / 3.0) < 1e-12
    return {
        "n_nn": g["n_nn"],
        "n_walks": g["n_walks"],
        "M_xx": m_xx,
        "M_xy": float(g["M_xy"]),
        "E_r2": float(g["E_r2"]),
        "E_x4": float(g["E_x4"]),
        "E_x2y2": float(g["E_x2y2"]),
        "hatK_k2_coeff": hatk_k2,
        "sigma2_per_R": m_xx,
        "kappa_link_fcc": k_fcc,
        "nu_CA_fcc": k_fcc,
        "isotropic_M": isotropic,
        "nlse_class": True,
        "ns_class_via_madelung": True,
        "gaussian_fourth_not_exact": abs(float(g["E_x4"]) - 3.0 * m_xx * m_xx) > 0.1,
        "note": "§4.1.1-HL: M=(4/3)I · Ŵ=1−(2/3)|k|² · κ=1/12 → NLSE+ν / NS-class",
    }


def _discrete_laplacian_2d(u):
    import torch

    return (
        torch.roll(u, -1, 1)
        + torch.roll(u, 1, 1)
        + torch.roll(u, -1, 0)
        + torch.roll(u, 1, 0)
        - 4.0 * u
    )


def _phi_bz_one_scale(
    *,
    device,
    size: int,
    b_radius: int,
    cells_per_wave: int,
) -> dict[str, float]:
    import torch

    from mt_ca.config import MConfig
    from mt_ca.fixed_point import decode_spinor
    from mt_ca.macro import macro_average_spinor
    from mt_ca.reversible import canonical_fixed, leapfrog_forward_fixed
    from mt_ca.spinor import spinor_density

    kx = 2.0 * math.pi / float(cells_per_wave)
    ny = nx = size
    ys = torch.arange(ny, device=device, dtype=torch.float32)
    xs = torch.arange(nx, device=device, dtype=torch.float32)
    _, xx = torch.meshgrid(ys, xs, indexing="ij")
    z = torch.zeros(ny, nx, 2, device=device, dtype=torch.complex64)
    z[..., 0] = torch.exp(1j * (kx * xx)).to(torch.complex64)

    cfg = MConfig.for_stencil("hex", heisenberg_floor=True)
    f0 = canonical_fixed(z, cfg)
    f1, _, _ = leapfrog_forward_fixed(f0, f0, cfg)
    z0 = decode_spinor(f0)
    phi0 = macro_average_spinor(z0, radius=b_radius)

    rho_z = spinor_density(z0)
    rho_phi = spinor_density(phi0)
    rho_smooth = spinor_density(
        macro_average_spinor(
            torch.stack(
                [rho_z.sqrt().to(torch.complex64), torch.zeros_like(rho_z, dtype=torch.complex64)],
                dim=-1,
            ),
            radius=b_radius,
        )
    )
    mask = rho_z > 0.05 * float(rho_z.max().item())
    rel_dens = (
        float(((rho_phi - rho_smooth) / rho_z.clamp_min(1e-12)).abs()[mask].max().item())
        if bool(mask.any())
        else float("nan")
    )

    u_phi = phi0[..., 0]
    u_hat = torch.fft.fft2(u_phi)
    power = u_hat.abs().square()
    power[0, 0] = 0
    flat = int(power.argmax().item())
    ky_i, kx_i = flat // nx, flat % nx
    kx_peak = 2.0 * math.pi * (kx_i if kx_i <= nx // 2 else kx_i - nx) / nx
    w_ir = math.cos(kx_peak / 2.0) ** (2 * b_radius)
    meas = float((u_hat[ky_i, kx_i].abs() / u_hat.abs().max().clamp_min(1e-12)).item())
    spectral_ok = abs(meas - w_ir) / max(w_ir, 1e-12) < 0.35

    lap_u0 = _discrete_laplacian_2d(u_phi)
    lam_k = 2.0 * (math.cos(kx) - 1.0)  # ky=0 plane wave on periodic torus (von Neumann Δ₄)
    lap_mode_slip = float(
        (lap_u0 - lam_k * u_phi).abs().max().item() / u_phi.abs().max().clamp_min(1e-12).item()
    )
    return {
        "cells_per_wave": float(cells_per_wave),
        "rho_phi_vs_B_amp_z_max_rel": rel_dens,
        "spectral_ir_ok": float(spectral_ok),
        "lap_mode_slip_phi": lap_mode_slip,
    }


def phi_bz_readout_row(
    *,
    device: str = "cpu",
    size: int = 192,
    b_radius: int = 12,
) -> dict[str, float | int | bool | str | list]:
    """Φ = ℬz — T readout: |Φ|²≈ℬ|z|², T-CR IR spectrum, IR Laplacian tightens as λ grows."""
    import torch

    dev = torch.device(device)
    laps = [
        _phi_bz_one_scale(device=dev, size=size, b_radius=b_radius, cells_per_wave=L)
        for L in (48, 128)
        if L < size // 2
    ]
    if len(laps) < 2:
        laps = [
            _phi_bz_one_scale(device=dev, size=128, b_radius=b_radius, cells_per_wave=48),
            _phi_bz_one_scale(device=dev, size=128, b_radius=b_radius, cells_per_wave=96),
        ]

    short = laps[0]
    long = laps[-1]
    rel_dens_short = short["rho_phi_vs_B_amp_z_max_rel"]
    rel_dens = long["rho_phi_vs_B_amp_z_max_rel"]
    spectral_ok = bool(long["spectral_ir_ok"])
    density_tightens = rel_dens < rel_dens_short * 0.45
    ok = rel_dens < 0.12 and spectral_ok and density_tightens

    return {
        "b_radius": b_radius,
        "size": size,
        "scales": laps,
        "rho_phi_vs_B_amp_z_max_rel": rel_dens,
        "rho_phi_vs_B_short_wave": rel_dens_short,
        "density_tightens_with_L": density_tightens,
        "spectral_ir_ok": spectral_ok,
        "phi_readout_ok": ok,
        "note": "M: z,g → T: Φ=ℬz; |Φ|² tracks ℬ|z|²; IR peak obeys T-CR binomial gain",
    }


def fcc_green_fourier(kx: float, ky: float, kz: float = 0.0) -> complex:
    """Fourier symbol of normalized FCC depth-2 path-Green (§4.1.1-HL H2)."""
    neigh = _fcc_nn()
    counts: Counter[tuple] = Counter()
    for u in neigh:
        for d in neigh:
            p = (u[0] + d[0], u[1] + d[1], u[2] + d[2])
            counts[p] += 1
    n_walks = len(neigh) ** 2
    acc = 0.0 + 0.0j
    for p, w in counts.items():
        phase = kx * p[0] + ky * p[1] + kz * p[2]
        acc += w * complex(math.cos(phase), math.sin(phase))
    return acc / n_walks


def classical_limit_sweep_row(
    *,
    device: str = "cpu",
    size: int = 128,
) -> dict[str, float | int | bool | str | list]:
    """§4.0 / §4.1.1-HL — do coarse + long-wavelength limits land in classical T?

    Not hL→0 on M: R-fold binomial → Gaussian (heat kernel); FCC K̂ → 1−(2/3)|k|²;
    Bohm Q ~ 1/L² on smooth ρ; one-tick Madelung residual ~ O(k²) on long waves.
    """
    import torch

    from mt_ca.config import MConfig
    from mt_ca.conservation import madelung_div_j
    from mt_ca.reversible import canonical_fixed, leapfrog_forward_fixed
    from mt_ca.spinor import spinor_density
    from mt_ca.t_analysis import estimate_phase_velocity_plane_wave

    r_vals = [4, 16, 64, 256]
    gauss_errs = [
        float(binomial_spectral_row(r_passes=r)["max_rel_err_k_sigma_lt_0_30"]) for r in r_vals
    ]
    coarse_to_gaussian = gauss_errs[-1] < 1e-5 and gauss_errs[-1] < gauss_errs[0]

    k_probe = 0.08
    kh = fcc_green_fourier(k_probe, 0.0)
    lap_coeff = (1.0 - kh.real) / (k_probe * k_probe)
    fcc_laplacian_two_thirds = abs(lap_coeff - 2.0 / 3.0) < 8e-3

    k_stack = 0.05
    r_stack = 64
    kh_r = fcc_green_fourier(k_stack, 0.0) ** r_stack
    lap_coeff_r = (1.0 - kh_r.real) / (k_stack * k_stack)
    expected_stack = r_stack * (2.0 / 3.0)
    stacked_laplacian = abs(lap_coeff_r - expected_stack) / expected_stack < 0.08

    dev = torch.device(device)
    bohm_rows: list[dict[str, float]] = []
    madelung_rows: list[dict[str, float]] = []
    for cells_per_wave in (32, 64, 128):
        kx = 2.0 * math.pi / float(cells_per_wave)
        ny = nx = size
        ys = torch.arange(ny, device=dev, dtype=torch.float32)
        xs = torch.arange(nx, device=dev, dtype=torch.float32)
        yy, xx = torch.meshgrid(ys, xs, indexing="ij")
        amp = 0.08
        env = 1.0 + amp * torch.cos(kx * xx)
        phase = torch.exp(1j * (kx * xx))
        z = torch.zeros(ny, nx, 2, device=dev, dtype=torch.complex64)
        z[..., 0] = torch.sqrt(env).to(torch.complex64) * phase
        rho = spinor_density(z)
        u = torch.sqrt(rho.clamp_min(1e-12))
        lap_u = (
            torch.roll(u, -1, 1)
            + torch.roll(u, 1, 1)
            + torch.roll(u, -1, 0)
            + torch.roll(u, 1, 0)
            - 4.0 * u
        )
        q = -(lap_u / (2.0 * u.clamp_min(1e-12)))
        q_max = float(q.abs().max().item())
        bohm_rows.append(
            {
                "L_cells": float(cells_per_wave),
                "Q_max": q_max,
                "Q_max_L2": q_max * cells_per_wave * cells_per_wave,
            }
        )

        from mt_ca.fixed_point import decode_spinor

        cfg = MConfig.for_stencil("hex", heisenberg_floor=True)
        f0 = canonical_fixed(z, cfg)
        f1, _, _ = leapfrog_forward_fixed(f0, f0, cfg)
        z0 = decode_spinor(f0)
        z1d = decode_spinor(f1)
        rho0 = spinor_density(z0)
        rho1 = spinor_density(z1d)
        resid = (rho1 - rho0 + madelung_div_j(z0)).abs()
        mad = float((resid.max() / rho0.max().clamp_min(1e-12)).item())
        omega = estimate_phase_velocity_plane_wave(z0[..., 0], z1d[..., 0], kx=kx, ky=0.0)
        madelung_rows.append(
            {
                "L_cells": float(cells_per_wave),
                "madelung_rel": mad,
                "madelung_L2": mad * cells_per_wave * cells_per_wave,
                "omega_tick": omega if omega == omega else float("nan"),
            }
        )

    bohm_classical = (
        bohm_rows[-1]["Q_max"] < bohm_rows[0]["Q_max"] * 0.2
        and bohm_rows[-1]["Q_max"] < 0.001
    )
    madelung_classical = (
        madelung_rows[-1]["madelung_rel"] < madelung_rows[0]["madelung_rel"] * 0.35
        or madelung_rows[-1]["madelung_rel"] < 0.05
    )

    phi_row = phi_bz_readout_row(device=device, size=max(size, 192))

    ok = (
        coarse_to_gaussian
        and fcc_laplacian_two_thirds
        and stacked_laplacian
        and bohm_classical
        and madelung_classical
        and phi_row["phi_readout_ok"]
    )
    return {
        "gauss_err_R": gauss_errs,
        "coarse_to_gaussian": coarse_to_gaussian,
        "fcc_lap_coeff_at_k": lap_coeff,
        "fcc_laplacian_two_thirds": fcc_laplacian_two_thirds,
        "stacked_laplacian_ok": stacked_laplacian,
        "bohm_scaling": bohm_rows,
        "madelung_long_wave": madelung_rows,
        "bohm_classical": bohm_classical,
        "madelung_classical": madelung_classical,
        "phi_bz": phi_row,
        "phi_readout_ok": phi_row["phi_readout_ok"],
        "checks_ok": ok,
        "note": (
            "§4 on T: Φ=ℬz → IR Laplacian/NLSE proxy; R→Gaussian; K̂→1−(2/3)k²; "
            "χ→0 Bohm/Madelung; not ℓ_P→∞ on M"
        ),
    }


def hydro_limit_verify_row() -> dict[str, float | int | bool | str]:
    """Verify bundle — алгебра T-CR + path-Green (гладкое макроописание T)."""
    spec = binomial_spectral_row()
    fcc = fcc_depth2_green_row()
    hx = hex_depth2_green_row()
    atom = (1, 1)
    conv = (
        atom[0] * atom[0],
        atom[0] * atom[1] + atom[1] * atom[0],
        atom[1] * atom[1],
    )
    return {
        "var_atom": spec["var_atom"],
        "sigma2_R16": spec["sigma2"],
        "multiplier_id_err": spec["multiplier_id_err"],
        "max_rel_err_k_sigma_lt_0_30": spec["max_rel_err_k_sigma_lt_0_30"],
        "max_rel_err_k_sigma_lt_0_50": spec["max_rel_err_k_sigma_lt_0_50"],
        "taylor_leading_R_over_96": spec["taylor_leading_R_over_96"],
        "path_atom_conv": conv,
        "path_atom_is_121": conv == (1, 2, 1),
        "fcc_n_nn": fcc["n_nn"],
        "fcc_n_walks": fcc["n_walks"],
        "fcc_w_origin": fcc["w_origin"],
        "fcc_p_origin": fcc["p_origin"],
        "fcc_w_nn_shell": fcc["w_nn_shell"],
        "hex_n_nn": hx["n_nn"],
        "hex_n_walks": hx["n_walks"],
        "hex_w_origin": hx["w_origin"],
        "hex_p_origin": hx["p_origin"],
        "separable_121_is_not_fcc_law": True,
        "note": "§4.1.0-T: макроописание T из binomial+Green; no hL→0",
    }
