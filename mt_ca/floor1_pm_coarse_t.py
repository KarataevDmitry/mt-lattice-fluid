"""§5.0.3 · floor1 — M pm annihilation → T coarse dipole proxy on VACUUM_BOIL.

Mid-plane coarse |Φ| delta after pm_nn vs pp_nn control; bridges floor1_two_body to Annihilation_T_stats.
DEVLOG / verify only.
"""
from __future__ import annotations

import time
from typing import Any

import torch

from mt_ca.annihilation_t_stats import _dipole_axis_angle
from mt_ca.app.dimension import LatticeDimension
from mt_ca.app.lattice import build_run_spec, open_lattice
from mt_ca.config import MConfig
from mt_ca.floor1_two_body import (
    default_sim_device,
    make_two_planckon_field,
    pair_annihilated,
    pair_like_persisted,
    scenario_charges,
    _probe_tracked_pair,
)
from mt_ca.spinor import spinor_density
from mt_ca.t_validation import coarse_grain, collision_peak_count, covariance_isotropy


def _mid_plane_coarse_delta(
    z_before: torch.Tensor,
    z_after: torch.Tensor,
    *,
    iz: int,
    block: int,
) -> dict[str, float | int | None]:
    z_b = z_before[iz]
    z_a = z_after[iz]
    coarse_b = coarse_grain(z_b, block).detach().cpu()
    coarse_a = coarse_grain(z_a, block).detach().cpu()
    delta = (coarse_a - coarse_b).clamp_min(0.0)
    elong = covariance_isotropy(delta) if float(delta.max()) > 1e-9 else float("inf")
    peaks = collision_peak_count(delta, min_frac=0.22)
    return {
        "peaks_on_delta": peaks,
        "elongation_delta": elong if elong == elong else None,
        "axis_angle": _dipole_axis_angle(delta),
    }


def _run_pm_snapshot(
    *,
    size: int,
    relaxation: int,
    n_max: int,
    device: str,
    scenario: str,
) -> dict[str, Any]:
    q_a, q_b, graph_sep = scenario_charges(scenario)  # type: ignore[arg-type]
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
    dev = torch.device(device)
    z0, site_a, site_b = make_two_planckon_field(
        nz,
        sim.ny,
        sim.nx,
        q_a=q_a,
        q_b=q_b,
        graph_sep=graph_sep,
        device=dev,
        dtype=sim.dtype,
        mod_bits=cfg.mod_bits,
        frac_bits=cfg.frac_bits,
    )
    sim.set_field(z0)
    if relaxation > 0:
        sim.step(relaxation)
    z_relax = sim.z.detach().clone()
    iz = nz // 2
    sim.step(n_max)
    z_late = sim.z.detach().clone()
    rho = spinor_density(sim.z)
    pa, pb, _, _ = _probe_tracked_pair(
        sim.z, site_a, site_b, site_a, site_b, contour_radius=2, cfg=cfg, rho=rho
    )
    ann = pair_annihilated(pa, pb)
    like_ok = pair_like_persisted(pa, pb, 1) if scenario == "pp_nn" else None
    return {
        "scenario": scenario,
        "z_relax": z_relax,
        "z_late": z_late,
        "iz": iz,
        "pair_annihilated_final": ann,
        "like_persisted_final": like_ok,
    }


def run_pm_coarse_dipole_probe(
    *,
    size: int = 24,
    relaxation: int = 12,
    n_max: int = 72,
    block: int = 4,
    device: str | None = None,
) -> dict[str, Any]:
    device = device or default_sim_device()
    t0 = time.perf_counter()
    pm = _run_pm_snapshot(
        size=size, relaxation=relaxation, n_max=n_max, device=device, scenario="pm_nn"
    )
    pp = _run_pm_snapshot(
        size=size, relaxation=relaxation, n_max=n_max, device=device, scenario="pp_nn"
    )
    pm_m = _mid_plane_coarse_delta(pm["z_relax"], pm["z_late"], iz=pm["iz"], block=block)
    pp_m = _mid_plane_coarse_delta(pp["z_relax"], pp["z_late"], iz=pp["iz"], block=block)

    pm_elong = pm_m["elongation_delta"]
    elong_ok = pm_elong is not None and pm_elong == pm_elong and pm_elong > 1.15
    pm_dipole = (
        pm["pair_annihilated_final"]
        and pm_m["peaks_on_delta"] is not None
        and pm_m["peaks_on_delta"] >= 2
        and (elong_ok or pm_m["peaks_on_delta"] >= 3)
    )
    pp_control = not pp["pair_annihilated_final"]
    contrast = (
        pm_m["peaks_on_delta"] is not None
        and pp_m["peaks_on_delta"] is not None
        and pm_m["peaks_on_delta"] >= pp_m["peaks_on_delta"] + 1
    )

    checks_ok = pm_dipole and pp_control and contrast
    return {
        "size": size,
        "relaxation": relaxation,
        "n_max": n_max,
        "block": block,
        "device": device,
        "pm_annihilated": pm["pair_annihilated_final"],
        "pp_annihilated": pp["pair_annihilated_final"],
        "pm_peaks_on_delta": pm_m["peaks_on_delta"],
        "pp_peaks_on_delta": pp_m["peaks_on_delta"],
        "pm_elongation_delta": pm_m["elongation_delta"],
        "pp_elongation_delta": pp_m["elongation_delta"],
        "pm_dipole_proxy": pm_dipole,
        "pp_control_ok": pp_control,
        "pm_vs_pp_contrast": contrast,
        "checks_ok": checks_ok,
        "wall_s": time.perf_counter() - t0,
        "note": (
            "pm_nn on VACUUM_BOIL: coarse Δ|Φ| on mid plane shows dual-front dipole proxy; "
            "pp_nn control without annihilation — weaker or fewer peaks."
        ),
    }


def run_pm_coarse_dipole_harness(**kwargs: Any) -> dict[str, Any]:
    row = run_pm_coarse_dipole_probe(**kwargs)
    return {**row, "derivation_closed": False}
