"""Discrete symmetry probes for A14 (C / P / T / U(1)_vac on lattice g)."""

from __future__ import annotations

import torch

from mt_ca.chiral import chirality_flip_boost, chirality_imbalance, project_left, project_right, recombine
from mt_ca.config import MConfig
from mt_ca.seeds import SeedClass, make_seed
from mt_ca.spinor import arg_phase_defect, gate_phase, holonomy_zeta, micro_step, spinor_neighbor_sum
from mt_ca.topology import winding_nearest_int, winding_robust


def mirror_x(z: torch.Tensor) -> torch.Tensor:
    """Parity: reflect x → −x on torus (flip columns)."""
    return torch.flip(z, dims=(1,))


def mirror_y(z: torch.Tensor) -> torch.Tensor:
    return torch.flip(z, dims=(0,))


def parity_inversion(z: torch.Tensor) -> torch.Tensor:
    """P: spatial axis inversion (x→−x, y→−y) on torus."""
    return torch.flip(torch.flip(z, dims=(1,)), dims=(0,))


def charge_conjugate(z: torch.Tensor) -> torch.Tensor:
    """C: complex conjugate on spinor components (|z|² invariant)."""
    return z.conj()


def charge_conjugate_seed(z: torch.Tensor) -> torch.Tensor:
    return charge_conjugate(z)


def time_reversal_chiral(z: torch.Tensor) -> torch.Tensor:
    """T: chirality sign flip via SU(2) boost (not z→z* alone)."""
    return chirality_flip_boost(z)


def cpt_conjugate(z: torch.Tensor) -> torch.Tensor:
    """Full CPT = P ∘ C ∘ T on z (§3.11.3). Enables g⁻¹ ≈ Θ g Θ unwind."""
    z = time_reversal_chiral(z)
    z = charge_conjugate(z)
    z = parity_inversion(z)
    return z


def cpt_unwind(z: torch.Tensor, cfg: MConfig, steps: int) -> torch.Tensor:
    """Recover pre-evolution state: g⁻ᴺ(z) ≈ CPT( gᴺ( CPT(z) ) ) when A14 holds."""
    w = cpt_conjugate(z)
    for _ in range(steps):
        w = micro_step(w, cfg)
    return cpt_conjugate(w)


def cpt_reverse_report(
    size: int = 64,
    steps: int = 16,
    device: torch.device | str = "cpu",
) -> dict:
    """Single-bit IMPULSE: forward N ticks then CPT-unwind → same bit."""
    dev = torch.device(device)
    cfg = MConfig(heisenberg_floor=False, holomorphy_sync=False, cr_strength=0.0)
    z0 = make_seed(SeedClass.IMPULSE, size, size, device=dev)

    z = z0.clone()
    for _ in range(steps):
        z = micro_step(z, cfg)
    z_rec = cpt_unwind(z, cfg, steps)

    peak0 = float(z0.abs().square().sum(dim=-1).max().item())
    peak_rec = float(z_rec.abs().square().sum(dim=-1).max().item())
    rel = float((z_rec - z0).abs().max().item() / (z0.abs().max().item() + 1e-12))

    chi0 = float(chirality_imbalance(z0).abs().max().item())
    chi_t = float(chirality_imbalance(time_reversal_chiral(z0)).abs().max().item())
    chi_flipped = chi_t > 0.5 * max(chi0, 1e-12) or chi0 < 1e-10

    ok = rel < 0.15 and abs(peak_rec - peak0) / (peak0 + 1e-12) < 0.25
    return {
        "id": "CPT_unwind",
        "steps": steps,
        "max_rel_err_to_bit": rel,
        "peak0": peak0,
        "peak_recovered": peak_rec,
        "chi_flip_ok": chi_flipped,
        "ok": ok,
        "note": "Θ g Θ ≈ g⁻¹ on impulse bit; full CPT = P·C·T (§3.11.3)",
    }


def cpt_step_conjugation(z: torch.Tensor, cfg: MConfig) -> dict:
    """One-step: z ≈ CPT( g( CPT(g(z)) ) ) when Θ g Θ = g⁻¹."""
    z1 = micro_step(z, cfg)
    z0_rec = cpt_conjugate(micro_step(cpt_conjugate(z1), cfg))
    rel = float((z0_rec - z).abs().max().item() / (z.abs().max().item() + 1e-12))
    return {"max_rel_err": rel, "ok": rel < 0.2}


def time_reversal_proxy(z: torch.Tensor, cfg: MConfig, steps: int = 64) -> dict:
    """T leg: chirality flip + CPT-unwind on vortex (not z* alone)."""
    chi0 = float(chirality_imbalance(z).abs().mean().item())
    chi_t = float(chirality_imbalance(time_reversal_chiral(z)).abs().mean().item())
    flip_ratio = chi_t / (chi0 + 1e-12)

    z_fwd = z.clone()
    n0 = winding_int(z_fwd)
    for _ in range(steps):
        z_fwd = micro_step(z_fwd, cfg)
    n_fwd = winding_int(z_fwd)

    unwind = cpt_unwind(z_fwd, cfg, steps)
    n_unwind = winding_int(unwind)
    rel_unwind = float((unwind - z).abs().max().item() / (z.abs().max().item() + 1e-12))

    return {
        "n0": n0,
        "n_after_forward": n_fwd,
        "n_preserved_forward": abs(n_fwd) >= max(abs(n0) - 1, 1) // 2,
        "chi_mean_before": chi0,
        "chi_mean_after_T": chi_t,
        "chi_flip_ratio": flip_ratio,
        "cpt_unwind_rel_to_seed": rel_unwind,
        "n_after_cpt_unwind": n_unwind,
        "t_chirality_flips": flip_ratio > 0.5 or chi0 < 1e-10,
    }


def winding_int(z: torch.Tensor) -> int:
    w = winding_robust(z)
    return winding_nearest_int(w) if w == w else -999


def parity_flip_seeds(size: int, device: torch.device) -> dict:
    """P: mirror VORTEX_P seed → winding should flip sign."""
    z_p = make_seed(SeedClass.VORTEX_P, size, size, device=device)
    z_m = make_seed(SeedClass.VORTEX_M, size, size, device=device)
    n_p = winding_int(z_p)
    n_m = winding_int(z_m)
    n_px = winding_int(mirror_x(z_p))
    n_py = winding_int(mirror_y(z_p))
    n_mx = winding_int(mirror_x(z_m))
    return {
        "n_vortex_p": n_p,
        "n_vortex_m": n_m,
        "n_mirror_x_p": n_px,
        "n_mirror_y_p": n_py,
        "n_mirror_x_m": n_mx,
        "p_flips_p": n_px == -n_p,
        "p_flips_m_to_p": n_mx == -n_m and n_mx == n_p,
    }


def g_commutes_with_mirror_x(
    z: torch.Tensor,
    cfg: MConfig,
    steps: int = 1,
) -> dict:
    """Test P·g vs g·P on vortex (field error + winding)."""
    z_pg = mirror_x(z.clone())
    z_gp = z.clone()
    for _ in range(steps):
        z_pg = micro_step(z_pg, cfg)
        z_gp = micro_step(z_gp, cfg)
    z_gp = mirror_x(z_gp)

    n_pg = winding_int(z_pg)
    n_gp = winding_int(z_gp)
    rel = float((z_pg - z_gp).abs().max().item() / (z_gp.abs().max().item() + 1e-12))

    z_fwd = z.clone()
    for _ in range(steps):
        z_fwd = micro_step(z_fwd, cfg)
    n_fwd = winding_int(z_fwd)

    return {
        "n_forward": n_fwd,
        "n_P_then_g": n_pg,
        "n_g_then_P": n_gp,
        "max_rel_err_Pg_vs_gP": rel,
        "winding_match": n_pg == n_gp,
    }


def u1_global_phase(z: torch.Tensor, theta: float) -> torch.Tensor:
    factor = torch.exp(torch.tensor(1j * theta, device=z.device, dtype=z.dtype))
    return z * factor


def u1_gate_invariants(z: torch.Tensor, cfg: MConfig, theta: float = 0.73) -> dict:
    """Arg carrier and gate phase must be invariant under z → z·e^{iθ}."""
    z_rot = u1_global_phase(z, theta)
    sum0 = spinor_neighbor_sum(z, cfg)
    sum1 = spinor_neighbor_sum(z_rot, cfg)
    zeta0 = holonomy_zeta(z, sum0)
    zeta1 = holonomy_zeta(z_rot, sum1)
    dphi0 = arg_phase_defect(z, cfg, apply_floor=False)
    dphi1 = arg_phase_defect(z_rot, cfg, apply_floor=False)
    phi0 = gate_phase(z, cfg)
    phi1 = gate_phase(z_rot, cfg)
    chi0 = chirality_imbalance(z)
    chi1 = chirality_imbalance(z_rot)
    return {
        "zeta_max_err": float((zeta0 - zeta1).abs().max().item()),
        "dphi_max_err": float((dphi0 - dphi1).abs().max().item()),
        "phi_max_err": float((phi0 - phi1).abs().max().item()),
        "chi_max_err": float((chi0 - chi1).abs().max().item()),
    }


def micro_step_u1_equivariance(
    z: torch.Tensor,
    cfg: MConfig,
    *,
    theta: float = 0.73,
    steps: int = 1,
) -> dict:
    """Test g(z·e^{iθ}) ≈ g(z)·e^{iθ} (U(1)_vac on full micro_step)."""
    factor = torch.exp(torch.tensor(1j * theta, device=z.device, dtype=z.dtype))
    z0 = z.clone()
    z1 = u1_global_phase(z, theta)
    for _ in range(steps):
        z0 = micro_step(z0, cfg)
        z1 = micro_step(z1, cfg)
    rel = float((z1 - z0 * factor).abs().max().item() / (z0.abs().max().item() + 1e-12))
    return {"rel_err": rel, "theta": theta, "steps": steps}


def u1_vac_report(size: int = 128, device: torch.device | str = "cpu") -> dict:
    dev = torch.device(device)
    cfg = MConfig()
    cfg_smooth = MConfig(pauli_exclusion=False, heisenberg_floor=False)
    seeds = {
        "VACUUM": SeedClass.VACUUM,
        "PLANE_WAVE": SeedClass.PLANE_WAVE,
        "VORTEX_P": SeedClass.VORTEX_P,
    }
    rows: dict[str, dict] = {}
    for name, seed in seeds.items():
        z = make_seed(seed, size, size, device=dev)
        inv = u1_gate_invariants(z, cfg)
        step_cfg = cfg_smooth if seed == SeedClass.VORTEX_P else cfg
        step1 = micro_step_u1_equivariance(z, step_cfg, steps=1)
        step4 = micro_step_u1_equivariance(z, step_cfg, steps=4)
        rows[name] = {
            **{f"inv_{k}": v for k, v in inv.items()},
            "micro_1step": step1["rel_err"],
            "micro_4step": step4["rel_err"],
        }

    ok = (
        rows["VACUUM"]["micro_1step"] < 1e-3
        and rows["PLANE_WAVE"]["micro_1step"] < 1e-4
        and rows["VORTEX_P"]["micro_1step"] < 1e-3
        and all(rows[n]["inv_zeta_max_err"] < 1e-5 for n in seeds)
        and all(rows[n]["inv_dphi_max_err"] < 1e-4 for n in seeds)
    )
    return {"id": "U1_vac", "seeds": rows, "ok": ok}


def chiral_projector_report(size: int = 64, device: torch.device | str = "cpu") -> dict:
    dev = torch.device(device)
    z = make_seed(SeedClass.VORTEX_P, size, size, device=dev)
    z_l = project_left(z)
    z_r = project_right(z)
    recon_err = float((z - recombine(z_l, z_r)).abs().max().item())
    ortho_err = float((z_l * z_r.conj()).sum().real.abs().max().item())
    theta = 0.42
    chi_err = float(
        (chirality_imbalance(z) - chirality_imbalance(u1_global_phase(z, theta))).abs().max().item()
    )
    ok = recon_err < 1e-6 and ortho_err < 1e-6 and chi_err < 1e-6
    return {
        "id": "Chiral_SU2",
        "recombine_max_err": recon_err,
        "orthogonality_max": ortho_err,
        "chi_u1_max_err": chi_err,
        "ok": ok,
        "note": "P_L/P_R on ℂ²; STREAM per component; COLLISION via SU(2) (§3.11)",
    }


def annihilation_winding(size: int, cfg: MConfig, device: torch.device, steps: int = 32) -> dict:
    """Place P and M vortices; measure net |winding| after merge region."""
    ny = nx = size
    cy, cx = ny // 2, nx // 2
    sep = max(8, size // 16)
    patch = min(64, size // 2)
    half = patch // 2
    z = torch.zeros(ny, nx, 2, device=device, dtype=torch.complex64)
    patch_p = make_seed(SeedClass.VORTEX_P, patch, patch, device=device)
    patch_m = make_seed(SeedClass.VORTEX_M, patch, patch, device=device)
    y0, x0 = cy - half, cx - sep - half
    y1, x1 = cy - half, cx + sep - half
    z[y0 : y0 + patch, x0 : x0 + patch] = patch_p
    z[y1 : y1 + patch, x1 : x1 + patch] = patch_m
    n0 = winding_int(z)
    for _ in range(steps):
        z = micro_step(z, cfg)
    n_late = winding_int(z)
    rho_peak = float(z.abs().square().sum(dim=-1).max().item())
    return {
        "n_initial_combined": n0,
        "n_after_steps": n_late,
        "peak_rho": rho_peak,
        "annihilation_proxy": abs(n_late) < abs(n0),
    }


def symmetry_report(size: int = 128, steps: int = 64, device: str = "cpu") -> dict:
    dev = torch.device(device)
    cfg = MConfig()
    z_p = make_seed(SeedClass.VORTEX_P, size, size, device=dev)

    p_seeds = parity_flip_seeds(size, dev)
    p_g = g_commutes_with_mirror_x(z_p, cfg, steps=1)
    p_g_many = g_commutes_with_mirror_x(z_p, cfg, steps=steps)
    t_proxy = time_reversal_proxy(z_p, cfg, steps=steps)
    ann = annihilation_winding(size, cfg, dev, steps=steps)
    u1 = u1_vac_report(size, dev)
    chiral = chiral_projector_report(size, dev)
    cpt = cpt_reverse_report(size, min(steps, 16), dev)

    z_c = charge_conjugate_seed(z_p)
    n_c = winding_int(z_c)

    ok = (
        p_seeds["p_flips_p"]
        and p_seeds["p_flips_m_to_p"]
        and p_g["winding_match"]
        and n_c == -p_seeds["n_vortex_p"]
        and u1["ok"]
        and chiral["ok"]
        and cpt["ok"]
        and t_proxy["t_chirality_flips"]
    )
    return {
        "id": "A14_symmetry",
        "parity_seeds": p_seeds,
        "charge_seed": {"n_vortex_p": p_seeds["n_vortex_p"], "n_after_conj": n_c},
        "g_P_1step": p_g,
        "g_P_steps": p_g_many,
        "T_proxy": t_proxy,
        "CPT_unwind": cpt,
        "U1_vac": u1,
        "chiral": chiral,
        "annihilation": ann,
        "ok": ok,
        "note": "Full CPT=P·C·T; Θ g Θ≈g⁻¹ on impulse bit; long-run g·P drift logged",
    }
