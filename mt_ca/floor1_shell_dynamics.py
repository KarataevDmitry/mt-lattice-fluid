"""§5.0.4-B dogfood — ρ_Θ shell activity under g on VACUUM_BOIL.

Single planted VORTEX_P; per-coordination-shell |Δφ| vs Δφ_min (dressing proxy).
Partial inter-shell graph: ground shell-1 halo persists; shell 2–3 do not dominate.
DEVLOG / verify only — not MODEL.
"""
from __future__ import annotations

import time
from typing import Any

import torch

from mt_ca.app.dimension import LatticeDimension
from mt_ca.app.lattice import build_run_spec, open_lattice
from mt_ca.config import MConfig
from mt_ca.floor1_shells import sites_on_shell
from mt_ca.floor1_two_body import default_sim_device
from mt_ca.matter_survey import MatterSite, survey_at_site
from mt_ca.seeds import SeedClass, make_seed
from mt_ca.si_constants import DELTA_PHI_MIN
from mt_ca.spinor import arg_phase_defect, spinor_density
from mt_ca.topology import winding_nearest_int

_WINDING_MIN = 0.75


def _torus_index(
    core: tuple[int, int, int],
    off: tuple[int, int, int],
    nz: int,
    ny: int,
    nx: int,
) -> tuple[int, int, int]:
    cz, cy, cx = core
    return (
        (cz + off[0]) % nz,
        (cy + off[1]) % ny,
        (cx + off[2]) % nx,
    )


def shell_halo_profile(
    z: torch.Tensor,
    core: tuple[int, int, int],
    *,
    cfg: MConfig,
    dphi_min: float = DELTA_PHI_MIN,
    max_k: int = 3,
) -> dict[int, dict[str, float | bool]]:
    nz, ny, nx = z.shape[0], z.shape[1], z.shape[2]
    dphi = arg_phase_defect(z, cfg, apply_floor=False).abs()
    out: dict[int, dict[str, float | bool]] = {}
    for k in range(1, max_k + 1):
        sites = sites_on_shell(k, ball_max_k=max_k)
        vals: list[float] = []
        for off in sites:
            iz, iy, ix = _torus_index(core, off, nz, ny, nx)
            vals.append(float(dphi[iz, iy, ix].item()))
        mx = max(vals) if vals else 0.0
        frac = sum(1 for v in vals if v >= dphi_min) / max(len(vals), 1)
        out[k] = {
            "max_abs_dphi": mx,
            "frac_above_floor": frac,
            "active": mx >= dphi_min,
        }
    return out


def _core_stable(z: torch.Tensor, core: tuple[int, int, int], cfg: MConfig, rho: torch.Tensor) -> bool:
    iz, iy, ix = core
    row = survey_at_site(z, MatterSite(iz, iy, ix), contour_radius=2, cfg=cfg, rho=rho)
    if row.b != 1 or row.winding_auto != row.winding_auto:
        return False
    if abs(float(row.winding_auto)) < _WINDING_MIN:
        return False
    return abs(winding_nearest_int(float(row.winding_auto))) == 1


def _vortex_on_boil_field(
    sim: Any,
    *,
    cfg: MConfig,
    dev: torch.device,
) -> torch.Tensor:
    nz = sim.nz
    assert nz is not None
    kw = {
        "device": dev,
        "dtype": sim.dtype,
        "mod_bits": cfg.mod_bits,
        "frac_bits": cfg.frac_bits,
        "nz": nz,
    }
    from mt_ca.floor1_two_body import _excitation_only_3d, _roll_site

    z = make_seed(SeedClass.VACUUM_BOIL, sim.ny, sim.nx, **kw)
    z = z + _excitation_only_3d(
        SeedClass.VORTEX_P,
        nz,
        sim.ny,
        sim.nx,
        device=dev,
        dtype=sim.dtype,
        mod_bits=cfg.mod_bits,
        frac_bits=cfg.frac_bits,
    )
    return z


def _shell_excess(
    z: torch.Tensor,
    core: tuple[int, int, int],
    far: tuple[int, int, int],
    *,
    cfg: MConfig,
    k: int,
) -> float:
    prof = shell_halo_profile(z, core, cfg=cfg)
    ref = shell_halo_profile(z, far, cfg=cfg)
    return float(prof[k]["frac_above_floor"]) - float(ref[k]["frac_above_floor"])


def run_shell2_excitation_relax(
    *,
    size: int = 24,
    relaxation: int = 12,
    n_relax_after_bump: int = 36,
    bump_scale: float = 0.22,
    device: str | None = None,
) -> dict[str, Any]:
    """Pulse on one shell-2 site; expect partial relax toward ground shell profile (C3→C2 tendency)."""
    device = device or default_sim_device()
    dev = torch.device(device)
    cfg = MConfig.for_stencil("fcc", heisenberg_floor=True)
    spec = build_run_spec(
        "habitat_boil",
        size,
        embedding=LatticeDimension.VOLUME_3P1,
        device=device,
        steps=0,
    )
    sim = open_lattice(spec)
    nz = sim.nz
    assert nz is not None
    cz, cy, cx = nz // 2, sim.ny // 2, sim.nx // 2
    core = (cz, cy, cx)
    far = ((cz + nz // 2) % nz, (cy + sim.ny // 2) % sim.ny, (cx + sim.nx // 2) % sim.nx)
    from mt_ca.floor1_two_body import _excitation_only_3d, _roll_site

    sim.set_field(_vortex_on_boil_field(sim, core, cfg=cfg, dev=dev))
    n0 = sim.norm()
    t0 = time.perf_counter()
    if relaxation > 0:
        sim.step(relaxation)

    shell2_before_bump = _shell_excess(sim.z, core, far, cfg=cfg, k=2)
    off = sites_on_shell(2, ball_max_k=3)[0]
    bump = bump_scale * _excitation_only_3d(
        SeedClass.VORTEX_P,
        nz,
        sim.ny,
        sim.nx,
        device=dev,
        dtype=sim.dtype,
        mod_bits=cfg.mod_bits,
        frac_bits=cfg.frac_bits,
    )
    sim.set_field(sim.z + _roll_site(bump, off[0], off[1], off[2]))
    shell2_post_bump = _shell_excess(sim.z, core, far, cfg=cfg, k=2)
    sim.step(n_relax_after_bump)

    rho = spinor_density(sim.z)
    prof_f = shell_halo_profile(sim.z, core, cfg=cfg)
    shell2_final = _shell_excess(sim.z, core, far, cfg=cfg, k=2)
    shell1_active = bool(prof_f[1]["active"])
    core_ok = _core_stable(sim.z, core, cfg, rho)
    n_late = sim.norm()
    norm_ok = n_late < 12.0 * max(n0, 1e-12) and not (n_late != n_late)

    relaxed_toward_ground = shell2_final <= shell2_post_bump + 0.02 or shell2_final <= shell2_before_bump + 0.18
    scenario_ok = core_ok and shell1_active and relaxed_toward_ground and norm_ok

    return {
        "size": size,
        "relaxation": relaxation,
        "n_relax_after_bump": n_relax_after_bump,
        "bump_scale": bump_scale,
        "device": device,
        "shell2_excess_before_bump": shell2_before_bump,
        "shell2_excess_post_bump": shell2_post_bump,
        "shell2_excess_final": shell2_final,
        "shell2_relax_delta": shell2_post_bump - shell2_final,
        "core_stable_final": core_ok,
        "shell1_active_final": shell1_active,
        "norm_ok": norm_ok,
        "scenario_ok": scenario_ok,
        "wall_s": time.perf_counter() - t0,
        "note": (
            "Single-site shell-2 pulse on dressed vortex; under g on boil the excess on shell 2 "
            "should not remain a runaway excitation attractor (partial decay vs post-bump)."
        ),
    }


def run_shell_excitation_harness(
    *,
    size: int = 24,
    relaxation: int = 12,
    n_relax_after_bump: int = 36,
    device: str | None = None,
) -> dict[str, Any]:
    bumped = run_shell2_excitation_relax(
        size=size,
        relaxation=relaxation,
        n_relax_after_bump=n_relax_after_bump,
        device=device,
    )
    checks_ok = bumped["scenario_ok"] and bumped["shell2_relax_delta"] >= -0.05
    return {
        "shell2_bump": bumped,
        "checks_ok": checks_ok,
        "derivation_closed": False,
    }


def run_shell_dynamics_on_boil(
    *,
    size: int = 24,
    relaxation: int = 12,
    n_max: int = 72,
    device: str | None = None,
    tick_resolve: bool = False,
    sample_stride: int = 8,
) -> dict[str, Any]:
    device = device or default_sim_device()
    dev = torch.device(device)
    cfg = MConfig.for_stencil("fcc", heisenberg_floor=True)
    spec = build_run_spec(
        "habitat_boil",
        size,
        embedding=LatticeDimension.VOLUME_3P1,
        device=device,
        steps=0,
    )
    sim = open_lattice(spec)
    nz = sim.nz
    assert nz is not None
    cz, cy, cx = nz // 2, sim.ny // 2, sim.nx // 2
    core = (cz, cy, cx)
    sim.set_field(_vortex_on_boil_field(sim, core, cfg=cfg, dev=dev))
    n0 = sim.norm()

    t0 = time.perf_counter()
    if relaxation > 0:
        sim.step(relaxation)

    ticks: list[dict[str, Any]] = []
    sustained_shell2_without_shell1 = 0
    max_sustained = 0

    def _record(t: int) -> dict[str, Any]:
        rho = spinor_density(sim.z)
        prof = shell_halo_profile(sim.z, core, cfg=cfg)
        stable = _core_stable(sim.z, core, cfg, rho)
        snap = {
            "t": t,
            "core_stable": stable,
            "shells": prof,
        }
        ticks.append(snap)
        s1 = bool(prof[1]["active"])
        s2 = bool(prof[2]["active"])
        nonlocal sustained_shell2_without_shell1, max_sustained
        if s2 and not s1:
            sustained_shell2_without_shell1 += 1
            max_sustained = max(max_sustained, sustained_shell2_without_shell1)
        else:
            sustained_shell2_without_shell1 = 0
        return snap

    if tick_resolve:
        for t in range(1, n_max + 1):
            sim.step(1)
            if t == n_max or t % sample_stride == 0:
                _record(t)
    else:
        sim.step(n_max)
        _record(n_max)

    final = ticks[-1]
    prof_f = final["shells"]
    far = ((cz + nz // 2) % nz, (cy + sim.ny // 2) % sim.ny, (cx + sim.nx // 2) % sim.nx)
    prof_ref = shell_halo_profile(sim.z, far, cfg=cfg)
    wall_s = time.perf_counter() - t0
    n_late = sim.norm()
    norm_ok = n_late < 12.0 * max(n0, 1e-12) and not (n_late != n_late)

    shell1_active = bool(prof_f[1]["active"])
    shell2_excess = float(prof_f[2]["frac_above_floor"]) - float(prof_ref[2]["frac_above_floor"])
    shell3_excess = float(prof_f[3]["frac_above_floor"]) - float(prof_ref[3]["frac_above_floor"])
    shell1_excess = float(prof_f[1]["frac_above_floor"]) - float(prof_ref[1]["frac_above_floor"])

    ground_persists = shell1_active and final["core_stable"]
    vortex_star_signature = shell1_excess >= 0.08
    no_sustained_excited_without_ground = max_sustained < 2

    scenario_ok = ground_persists and vortex_star_signature and norm_ok
    if tick_resolve:
        scenario_ok = scenario_ok and no_sustained_excited_without_ground

    return {
        "size": size,
        "relaxation": relaxation,
        "n_max": n_max,
        "device": device,
        "tick_resolve": tick_resolve,
        "norm_ok": norm_ok,
        "core_stable_final": final["core_stable"],
        "shell1_active_final": shell1_active,
        "shell1_excess_frac": shell1_excess,
        "shell2_excess_frac": shell2_excess,
        "shell3_excess_frac": shell3_excess,
        "shell2_frac_above_floor": float(prof_f[2]["frac_above_floor"]),
        "shell3_frac_above_floor": float(prof_f[3]["frac_above_floor"]),
        "shell1_max_abs_dphi": float(prof_f[1]["max_abs_dphi"]),
        "shell2_max_abs_dphi": float(prof_f[2]["max_abs_dphi"]),
        "max_sustained_shell2_without_shell1": max_sustained,
        "ground_persists": ground_persists,
        "vortex_star_signature": vortex_star_signature,
        "scenario_ok": scenario_ok,
        "wall_s": wall_s,
        "ticks_sample": ticks,
        "note": (
            "Planted VORTEX_P on VACUUM_BOIL; ρ_Θ proxy = |Δφ|≥Δφ_min on FCC coordination shells. "
            "Expect shell-1 halo under g; shell 2–3 bounded — not a new ground attractor."
        ),
    }


def run_shell_dynamics_harness(
    *,
    size: int = 24,
    relaxation: int = 12,
    n_max: int = 72,
    device: str | None = None,
    tick_resolve: bool = False,
) -> dict[str, Any]:
    row = run_shell_dynamics_on_boil(
        size=size,
        relaxation=relaxation,
        n_max=n_max,
        device=device,
        tick_resolve=tick_resolve,
    )
    return {
        "checks_ok": row["scenario_ok"],
        "derivation_closed": False,
        "partial_inter_shell_graph": True,
        **row,
    }
