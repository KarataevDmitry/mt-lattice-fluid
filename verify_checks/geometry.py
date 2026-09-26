"""verify_checks.geometry — extracted from verify_principles"""
from __future__ import annotations

import math
import re
from pathlib import Path

import torch

from mt_ca.cauchy_riemann import cauchy_riemann_energy
from mt_ca.config import MConfig
from mt_ca.metrics import field_amplitude, norm_drift, total_norm_squared
from mt_ca.seeds import SeedClass, make_seed
from mt_ca.simulator import LatticeFluidSimulator
from mt_ca.linear import linear_step, linear_step_local_ca
from mt_ca.reversible import evolve_canonical
from mt_ca.spinor import (
    arg_phase_defect,
    apply_saturating_phase_collision,
    saturating_phase,
    holonomy_zeta,
    spinor_neighbor_sum,
    su2_apply,
)
from mt_ca.update import apply_heisenberg_floor, vacuum_phase, wrapped_phase_diff


def check_vortex_hex_contour(
    size: int = 512,
    steps: int = 256,
    device: str = "cpu",
) -> dict:
    """§3.8: hex stencil + contour axis ratio on micro |z| (§3.7.3)."""
    from mt_ca.metrics import contour_axis_ratio, contour_radius_anisotropy, field_amplitude

    sim = LatticeFluidSimulator(size, size, MConfig.for_stencil('hex'), device=device)
    sim.reset(SeedClass.VORTEX_P)
    sim.step(steps)
    micro = field_amplitude(sim.z)
    axis = contour_axis_ratio(micro, threshold=0.5)
    r_theta = contour_radius_anisotropy(micro, threshold=0.5)
    ok = axis == axis and axis < 1.05
    return {
        "id": "Vortex_hex",
        "contour_axis_ratio": round(axis, 4) if axis == axis else None,
        "contour_r_anisotropy": round(r_theta, 4) if r_theta == r_theta else None,
        "stencil": "hex",
        "ok": ok,
    }

def check_su2_720_sign(size: int = 64, device: str = "cpu") -> dict:
    dev = torch.device(device)
    z = torch.zeros(1, 1, 2, device=dev, dtype=torch.complex64)
    z[..., 0] = 1.0
    axis = torch.tensor([[[0.0, 0.0, 1.0]]], device=dev)
    phi = torch.tensor([[4.0 * torch.pi]], device=dev)
    z_rot = su2_apply(z, phi, axis)
    dot = float((z * z_rot.conj()).sum().real.item())
    ok = dot > 0.5
    return {"id": "SU2_720", "overlap_after_4pi": dot, "ok": ok}

def check_discrete_rot_exp(device: str = "cpu") -> dict:
    """§3.10.3 ↔ §3.12.5: canonical M gate = R(Φ)=ω^Φ via Rot_LUT."""
    import math

    from mt_ca.config import MConfig
    from mt_ca.fixed_point import decode_spinor, encode_spinor
    from mt_ca.projected_collision import rot_kick_uv
    from mt_ca.si_constants import heisenberg_phi_min_disc, phase_disc_to_rad
    from mt_ca.z_ring import mod_lane

    cfg = MConfig.for_stencil('hex')
    dev = torch.device(device)
    n_ring = 1 << cfg.phase_bits

    z = torch.zeros(1, 1, 2, device=dev, dtype=torch.complex64)
    z[..., 0] = 1.0
    f = encode_spinor(z, frac_bits=cfg.frac_bits, mod_bits=cfg.mod_bits)

    def apply_rot(encoded: torch.Tensor, phi_ticks: int) -> torch.Tensor:
        u0 = encoded[..., 0].to(torch.int64)
        v0 = encoded[..., 1].to(torch.int64)
        u1 = encoded[..., 2].to(torch.int64)
        v1 = encoded[..., 3].to(torch.int64)
        phi = torch.tensor([phi_ticks], device=dev, dtype=torch.int64)
        du0, dv0 = rot_kick_uv(u0, v0, phi, phase_bits=cfg.phase_bits)
        du1, dv1 = rot_kick_uv(u1, v1, phi, phase_bits=cfg.phase_bits)
        out = encoded.clone()
        out[..., 0] = mod_lane(u0 + du0, cfg.mod_bits)
        out[..., 1] = mod_lane(v0 + dv0, cfg.mod_bits)
        out[..., 2] = mod_lane(u1 + du1, cfg.mod_bits)
        out[..., 3] = mod_lane(v1 + dv1, cfg.mod_bits)
        return decode_spinor(out, frac_bits=cfg.frac_bits, mod_bits=cfg.mod_bits)

    phi_test = heisenberg_phi_min_disc(phase_bits=cfg.phase_bits, delta_phi_min=cfg.heisenberg_phi_min)
    z_rot = apply_rot(f, phi_test)
    ang = phase_disc_to_rad(phi_test, phase_bits=cfg.phase_bits)
    z_expected = z.clone()
    z_expected[..., 0] = z[..., 0] * complex(math.cos(ang), math.sin(ang))
    lut_rel = float((z_rot[..., 0] - z_expected[..., 0]).abs().item())
    ok_lut = lut_rel < 0.08

    z_half = apply_rot(f, n_ring // 2)
    half_dot = float((z[..., 0].conj() * z_half[..., 0]).real.item())
    ok_half = half_dot < -0.5

    z_full = apply_rot(f, n_ring)
    full_dot = float((z[..., 0].conj() * z_full[..., 0]).real.item())
    ok_full = full_dot > 0.99

    ok = ok_lut and ok_half and ok_full
    return {
        "id": "DiscreteRotExp",
        "ok": ok,
        "lut_rel_err": lut_rel,
        "half_turn_dot": half_dot,
        "full_turn_dot": full_dot,
        "phi_ticks": phi_test,
        "note": "§3.10.3: M gate R(Φ)=ω^Φ; not matrix exp(i·Θ·σ/2)",
    }

def check_fcc_n12(device: str = "cpu") -> dict:
    """§1.6 — default stencil FCC N₁₂; κ_link=1/12; 3D multi-tick with HF ON (A5)."""
    from mt_ca.config import MConfig
    from mt_ca.laplacian import _FCC_OFFSETS, fcc_neighbor_sum, stencil_n_links
    from mt_ca.seeds import SeedClass
    from mt_ca.simulator import LatticeFluidSimulator

    cfg = MConfig()  # canon default = fcc
    n = stencil_n_links(cfg.stencil)
    ok_geom = cfg.stencil == "fcc" and n == 12 and len(_FCC_OFFSETS) == 12
    ok_kappa = abs(cfg.gamma - 1.0 / 12.0) < 1e-15

    # Canon: floor ON. After gate-only Φ (no CR double-count) + N_φ vacuum, multi-tick holds.
    cfg_dyn = MConfig.for_stencil("fcc", heisenberg_floor=True)
    sim = LatticeFluidSimulator(8, 8, cfg_dyn, device=device)
    sim.reset(SeedClass.IMPULSE)
    n0 = sim.norm()
    norms = [n0]
    for _ in range(16):
        sim.step(1)
        norms.append(sim.norm())
    n_late = norms[-1]
    ok_step = (
        abs(n_late - n0) / max(n0, 1e-9) < 1e-6
        and sim.z.ndim == 4
        and sim.z.shape[-1] == 2
        and max(norms) < 10.0 * max(n0, 1e-6)
    )
    s = fcc_neighbor_sum(sim.z[..., 0])
    ok_sum = s.shape == sim.z.shape[:-1]
    ok = ok_geom and ok_kappa and ok_step and ok_sum
    return {
        "id": "FCC_N12",
        "stencil": cfg.stencil,
        "n_links": n,
        "gamma": cfg.gamma,
        "shape": list(sim.z.shape),
        "norm0": n0,
        "norm_late": n_late,
        "ticks": 16,
        "heisenberg_floor": True,
        "ok": ok,
        "note": "§1.6 cuboctahedral ε; multi-tick stable with HF ON (A5)",
    }

def check_t_madelung_continuity(size: int = 64, device: str = "cpu") -> dict:
    from mt_ca.conservation import t_madelung_continuity_report

    return t_madelung_continuity_report(size, device=device)

def check_t_continuum_readout(device: str = "cpu") -> dict:
    from mt_ca.t.hydro_limit import hydro_limit_verify_row

    del device
    row = hydro_limit_verify_row()
    ok = (
        row["path_atom_is_121"] is True
        and row["var_atom"] == 0.5
        and row["multiplier_id_err"] < 1e-15
        and row["max_rel_err_k_sigma_lt_0_30"] < 1e-4
        and row["max_rel_err_k_sigma_lt_0_50"] < 1e-3
        and row["taylor_leading_R_over_96"] < 0.02
        and row["fcc_n_nn"] == 12
        and row["fcc_n_walks"] == 144
        and row["fcc_w_origin"] == 12
        and abs(float(row["fcc_p_origin"]) - 1.0 / 12.0) < 1e-15
        and row["fcc_w_nn_shell"] == 48
        and row["hex_n_nn"] == 6
        and row["hex_n_walks"] == 36
        and row["hex_w_origin"] == 6
        and abs(float(row["hex_p_origin"]) - 1.0 / 6.0) < 1e-15
        and row["separable_121_is_not_fcc_law"] is True
    )
    return {
        "id": "T_continuum_readout",
        "max_rel_err_k_sigma_lt_0_30": row["max_rel_err_k_sigma_lt_0_30"],
        "fcc_p_origin": row["fcc_p_origin"],
        "hex_p_origin": row["hex_p_origin"],
        "ok": ok,
        "note": row["note"],
    }

def check_t_hydro_limit(device: str = "cpu") -> dict:
    from mt_ca.t.hydro_limit import fcc_hydro_limit_row

    del device
    row = fcc_hydro_limit_row()
    ok = (
        abs(float(row["M_xx"]) - 4.0 / 3.0) < 1e-12
        and abs(float(row["M_xy"])) < 1e-12
        and abs(float(row["E_r2"]) - 4.0) < 1e-12
        and abs(float(row["E_x4"]) - 4.0) < 1e-12
        and abs(float(row["E_x2y2"]) - 14.0 / 9.0) < 1e-12
        and abs(float(row["hatK_k2_coeff"]) - 2.0 / 3.0) < 1e-12
        and abs(float(row["kappa_link_fcc"]) - 1.0 / 12.0) < 1e-15
        and abs(float(row["nu_CA_fcc"]) - 1.0 / 12.0) < 1e-15
        and row["isotropic_M"] is True
        and row["nlse_class"] is True
        and row["ns_class_via_madelung"] is True
        and row["gaussian_fourth_not_exact"] is True
        and row["n_nn"] == 12
        and row["n_walks"] == 144
    )
    return {
        "id": "T_hydro_limit",
        "M_xx": row["M_xx"],
        "hatK_k2_coeff": row["hatK_k2_coeff"],
        "nu_CA_fcc": row["nu_CA_fcc"],
        "ok": ok,
        "note": row["note"],
    }

def check_so2_c4(size: int = 64, device: str = "cpu") -> dict:
    from mt_ca.conservation import so2_c4_report

    return so2_c4_report(size, device=device)

def check_u1_vac(size: int = 128, device: str = "cpu") -> dict:
    from mt_ca.symmetry import u1_vac_report

    row = u1_vac_report(size, device)
    return {
        "id": row["id"],
        "seeds": row["seeds"],
        "ok": row["ok"],
        "note": "U(1)_vac: global phase on z; defect_axis fallback = local Bloch (§3.11)",
    }

def check_chiral_su2(size: int = 64, device: str = "cpu") -> dict:
    from mt_ca.symmetry import chiral_projector_report

    row = chiral_projector_report(size, device)
    return {
        "id": row["id"],
        "recombine_max_err": row["recombine_max_err"],
        "chi_u1_max_err": row["chi_u1_max_err"],
        "ok": row["ok"],
        "note": row["note"],
    }

def check_leapfrog_bit_exact(size: int = 64, steps: int = 32, device: str = "cpu") -> dict:
    from mt_ca.reversible import bit_exact_roundtrip_report
    from mt_ca.seeds import SeedClass

    impulse = bit_exact_roundtrip_report(size, steps, device, seed_class=SeedClass.IMPULSE)
    vortex = bit_exact_roundtrip_report(size, min(steps, 16), device, seed_class=SeedClass.VORTEX_P)
    ok = impulse["ok"] and vortex["bit_exact"]
    return {
        "id": "Leapfrog",
        "impulse": {k: impulse[k] for k in ("bit_exact", "max_rel_err", "steps")},
        "vortex": {k: vortex[k] for k in ("bit_exact", "n0", "n_back", "n_stable", "steps")},
        "ok": ok,
        "note": "§3.12: z(t+Δt)=−z(t−Δt)+2z(t)+⌊kick⌋; g⁻¹ without CPT",
    }

def check_spinor_360_sign(size: int = 64, device: str = "cpu") -> dict:
    dev = torch.device(device)
    z = torch.zeros(1, 1, 2, device=dev, dtype=torch.complex64)
    z[..., 0] = 1.0
    axis = torch.tensor([[[0.0, 0.0, 1.0]]], device=dev)
    phi = torch.tensor([[2.0 * torch.pi]], device=dev)
    z_rot = su2_apply(z, phi, axis)
    dot = float((z * z_rot.conj()).sum().real.item())
    ok = dot < -0.5
    return {"id": "SU2_360", "overlap_after_2pi": dot, "ok": ok, "note": "360° → −1 on z=(1,0)"}

def check_no_m_heat_death(device: str = "cpu") -> dict:
    """§2.3 theorem: M has no heat death / no shutdown — A3 + A5 + A13."""
    from verify_checks.axioms import check_a3_unitarity, check_a5_vacuum_floor

    a3 = check_a3_unitarity(device=device)
    a5 = check_a5_vacuum_floor(device=device)
    a13 = check_leapfrog_bit_exact(device=device)
    ok = a3["ok"] and a5["ok"] and a13["ok"]
    return {
        "id": "NoMHeatDeath",
        "ok": ok,
        "a3_norm_drift": a3.get("norm_drift"),
        "a5_ok": a5["ok"],
        "a13_ok": a13["ok"],
        "note": "§2.3 consistency probe (A3+A5+A13); not a proof certificate",
    }

def check_theorem_2_3_8(size: int = 32, device: str = "cpu") -> dict:
    """§2.3.8: D5 on Z_N[i] = constants only; Planck VACUUM ≠ D5."""
    from mt_ca.fixed_point import vacuum_amplitude_quantum
    from mt_ca.projected_collision import projected_collision_kick
    from mt_ca.reversible import canonical_fixed, leapfrog_forward_fixed
    from mt_ca.simulator import LatticeFluidSimulator
    from mt_ca.z_ring import mod_lane

    cfg = MConfig.for_stencil('hex')
    dev = torch.device(device)
    z_min = vacuum_amplitude_quantum(frac_bits=cfg.frac_bits)

    amp = z_min
    z_const = torch.full((size, size, 2), amp, device=dev, dtype=torch.complex64)
    cfg_d5 = MConfig.for_stencil('hex', heisenberg_floor=False)
    f_const = canonical_fixed(z_const, cfg_d5)
    kick_const = projected_collision_kick(f_const, cfg_d5)
    f_next, _, _ = leapfrog_forward_fixed(f_const, f_const, cfg_d5)
    const_kick_zero = int(kick_const.abs().max().item()) == 0
    const_step_fixed = bool(torch.equal(mod_lane(f_next, cfg.mod_bits), mod_lane(f_const, cfg.mod_bits)))

    # Non-constant: orthogonal neighbor bricks at amp large enough that Φ ≥ Δφ_disc.
    f_nc = torch.zeros(size, size, 4, device=dev, dtype=torch.int64)
    f_nc[..., 0] = 64
    yy, xx = torch.meshgrid(
        torch.arange(size, device=dev), torch.arange(size, device=dev), indexing="ij"
    )
    odd = (yy + xx) % 2 == 1
    f_nc[odd, 0] = 0
    f_nc[odd, 1] = 64
    f_nc[..., 2] = f_nc[..., 0]
    f_nc[..., 3] = f_nc[..., 1]
    nonconst_kick = int(projected_collision_kick(f_nc, cfg).abs().max().item()) > 0

    sim = LatticeFluidSimulator(size, size, cfg, device=dev)
    sim.reset(SeedClass.VACUUM)
    kick_vac = projected_collision_kick(sim._f_curr, cfg)
    vac_not_frozen = int(kick_vac.abs().max().item()) > 0
    # Holomorphic ocean (one Heisenberg class) may have ⌊𝒩⌋=0 locally (§2.3.8 remark).
    # Physical claim: VACUUM ≠ c=0 deadlock and ≠ empty lattice; A5 floor holds.
    vac_alive = float(sim.z.abs().square().sum(-1).min().item()) > 0.0
    vac_not_deadlock = vac_alive and float(sim.z.abs().mean().item()) > 0.0

    ok = const_kick_zero and const_step_fixed and nonconst_kick and vac_not_deadlock
    return {
        "id": "Theorem_2_3_8",
        "const_kick_zero": const_kick_zero,
        "const_step_fixed": const_step_fixed,
        "nonconst_kick": nonconst_kick,
        "vac_not_frozen": vac_not_frozen,
        "vac_alive": vac_alive,
        "ok": ok,
        "note": "§2.3.8a–b; VACUUM = Heisenberg-class ocean at z_min (kick may be 0 locally)",
    }

def check_matter_b_readout(size: int = 64, device: str = "cpu") -> dict:
    from mt_ca.macro import macro_amplitude, macro_matter_b
    from mt_ca.spinor import spinor_density
    from mt_ca.topology import matter_occupancy_b, matter_occupancy_b_field, winding_channels, winding_number

    dev = torch.device(device)
    radius = 2

    z_v = make_seed(SeedClass.VACUUM, size, size, device=dev)
    vac_b_mean = float(matter_occupancy_b_field(z_v).float().mean().item())
    vac_macro_b = float(macro_matter_b(z_v, radius=radius).mean().item())
    vac_macro_amp = float(macro_amplitude(z_v, radius=radius).mean().item())

    z_p = make_seed(SeedClass.VORTEX_P, size, size, device=dev)
    cy, cx = torch.unravel_index(spinor_density(z_p).argmax(), z_p.shape[:2])
    cy, cx = int(cy.item()), int(cx.item())
    w = winding_number(z_p, center=(cy, cx), radius=2)
    ch_p = winding_channels(z_p, center=(cy, cx), radius=2)
    core_b = 1 if w == w and abs(w) >= 0.75 else matter_occupancy_b(z_p, y=cy, x=cx)
    vortex_macro_b = float(macro_matter_b(z_p, radius=radius).max().item())

    # Locked equal-lane U(1) vortex: old Arg(z₂/z₁) thermometer was blind (§5.0).
    z_u1 = torch.zeros(size, size, 2, device=dev, dtype=torch.complex64)
    yy, xx = torch.meshgrid(
        torch.arange(size, device=dev),
        torch.arange(size, device=dev),
        indexing="ij",
    )
    ang = torch.atan2((yy - cy).float(), (xx - cx).float())
    amp = 0.5
    z_u1[..., 0] = amp * torch.exp(1j * ang)
    z_u1[..., 1] = amp * torch.exp(1j * ang)
    ch_u1 = winding_channels(z_u1, center=(cy, cx), radius=16)
    u1_b = matter_occupancy_b(z_u1, y=cy, x=cx, contour_radius=16)

    ok = (
        vac_b_mean < 0.05
        and vac_macro_b < 0.05
        and vac_macro_amp > vac_macro_b
        and core_b == 1
        and abs(ch_p["rel"]) >= 0.75
        and vortex_macro_b > 0.1
        and abs(ch_u1["u1"]) >= 0.75
        and abs(ch_u1["rel"]) < 0.25
        and u1_b == 1
    )
    return {
        "id": "MatterOccupancyB",
        "vac_b_mean": vac_b_mean,
        "vac_macro_b": vac_macro_b,
        "vac_macro_amp": vac_macro_amp,
        "vortex_core_b": core_b,
        "vortex_channels": ch_p,
        "vortex_macro_b_max": vortex_macro_b,
        "u1_locked_channels": ch_u1,
        "u1_locked_b": u1_b,
        "ok": ok,
        "note": "§5.0: b=min(1,|n_∂|); dual channel rel+U(1) auto; macro ⟨b⟩ primary over |z|²",
    }


def check_planckon_instrument_fcc(size: int = 48, steps: int = 128, device: str = "cpu") -> dict:
    """§5.0 readout instrument — 3+1 FCC anchor vs ρ-survey (densitometer)."""
    from mt_ca.app.lab import planckon_lab_report

    row = planckon_lab_report(
        "floor0_planckon",
        edge=size,
        settle=0,
        steps=steps,
        device=device,
    )
    ok = bool(row.pop("ok"))
    return {
        "id": "Planckon_instrument_fcc",
        "ok": ok,
        **row,
        "note": "Planted vortex on boil via app.lab; anchor readout SSOT",
    }


def check_model_purity() -> dict:
    """MODEL must not contain DEVLOG/impl pollution (hard gate)."""
    root = Path(__file__).resolve().parent
    model_dir = root / "model"
    patterns: list[tuple[re.Pattern[str], str]] = [
        (re.compile(r"\*\*SSOT-часть MODEL"), "meta header SSOT"),
        (re.compile(r"\*\*Не SSOT"), "meta header DEVLOG pointer"),
        (re.compile(r"\*\*Не сюда:"), "meta header DEVLOG pointer"),
        (re.compile(r"\*\*В теле §3 запрещено:"), "meta header forbidden list"),
        (re.compile(r"\*\*Код:\*\*"), "**Код:**"),
        (re.compile(r"(?<!\*)\bКод:\s*`"), "Код:`"),
        (re.compile(r"verify\s+\*\*"), "verify **"),
        (re.compile(r"✅"), "✅"),
        (re.compile(r"mt_ca/"), "mt_ca/"),
        (re.compile(r"`[^`]+\.py`"), ".py backtick"),
        (re.compile(r"\*\*Impl:\*\*"), "**Impl:**"),
        (re.compile(r"не канон", re.I), "не канон"),
        (re.compile(r"\b[Кк]анон\b"), "канон"),
        (re.compile(r"legacy\s*[··]", re.I), "legacy label"),
        (re.compile(r"\(legacy", re.I), "(legacy"),
        (re.compile(r"\bsim-gap\b", re.I), "sim-gap"),
        (re.compile(r"\*\*Verify / impl:\*\*"), "Verify / impl"),
        (re.compile(r"\*\*Verify `"), "Verify `"),
        (re.compile(r"\bmt_ca\b"), "mt_ca"),
        (re.compile(r"\*\*Fix:\*\*"), "**Fix:**"),
        (re.compile(r"\bburn-in\b", re.I), "burn-in"),
        (re.compile(r"\bbit-exact\b", re.I), "bit-exact"),
        (re.compile(r"\| leaf \|"), "leaf column"),
        (re.compile(r"\*\*Не путать"), "**Не путать"),
        (re.compile(r"\(impl"), "(impl"),
        (re.compile(r"impl v\d", re.I), "impl version"),
        (re.compile(r"DEVLOG\.md"), "DEVLOG link in body"),
        (re.compile(r"\bDEVLOG\b"), "DEVLOG"),
        (re.compile(r"\*\*Claim:\*\*"), "**Claim:**"),
        (re.compile(r"\*\*Итог"), "**Итог"),
        (re.compile(r"\bDoD\b"), "DoD"),
        (re.compile(r"verify_principles"), "verify_principles"),
        (re.compile(r"\bPASS\b"), "PASS"),
        (re.compile(r"\bFAIL\b"), "FAIL"),
        (re.compile(r"\bleaf\b", re.I), "leaf"),
        (re.compile(r"T-leaf", re.I), "T-leaf"),
        (re.compile(r"\*\*Код / verify:\*\*"), "Код / verify"),
        (re.compile(r"Sim \(live"), "Sim (live"),
        (re.compile(r"❌"), "❌"),
        (re.compile(r"sim TODO", re.I), "sim TODO"),
        (re.compile(r"verify DoD", re.I), "verify DoD"),
        (re.compile(r"Не путать", re.I), "Не путать"),
    ]
    allow_fragments = ("GPU-вкусовщина",)
    hits: list[str] = []
    for path in sorted(model_dir.glob("*.md")):
        for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if any(frag in line for frag in allow_fragments):
                continue
            for rx, label in patterns:
                if rx.search(line):
                    hits.append(f"{path.name}:{i}: {label}")
                    break
    return {
        "id": "Model_purity",
        "count": len(hits),
        "violations": hits[:12],
        "ok": len(hits) == 0,
        "note": "MODEL=physics only; impl/verify → DEVLOG.md",
    }

