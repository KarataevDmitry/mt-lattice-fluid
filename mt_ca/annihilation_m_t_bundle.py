"""§5.0.3 — M (floor1 pm on boil) + T (head-on ensemble) dipole linkage dogfood.

Single entry: both probes must pass and agree on dual-front coarse structure
(same ``_dipole_axis_angle`` path as ``Annihilation_T_stats``).
"""
from __future__ import annotations

import time
from typing import Any

from mt_ca.annihilation_pdg_tau import run_annihilation_pdg_tau_bridge
from mt_ca.annihilation_t_stats import annihilation_t_stats_probe
from mt_ca.floor1_pm_coarse_t import default_sim_device, run_pm_coarse_dipole_probe


def run_annihilation_m_t_bundle(
    *,
    device: str | None = None,
    pm_size: int = 24,
    t_size: int = 160,
    t_steps: int = 64,
    t_ensemble: int = 12,
) -> dict[str, Any]:
    device = device or default_sim_device()
    t0 = time.perf_counter()
    pm = run_pm_coarse_dipole_probe(size=pm_size, device=device)
    t_row = annihilation_t_stats_probe(
        size=t_size,
        steps=t_steps,
        ensemble=t_ensemble,
        device=device,
    )

    m_dual = bool(pm["pm_dipole_proxy"]) and int(pm["pm_peaks_on_delta"] or 0) >= 2
    t_dual = bool(t_row["back_to_back_proxy"]) and int(t_row["peaks_on_delta"] or 0) >= 2
    axis_shared = pm.get("pm_axis_angle") is not None and bool(t_row["axis_tracks_pi"])

    pdg = run_annihilation_pdg_tau_bridge(device=device)

    checks_ok = (
        bool(pm["checks_ok"])
        and bool(t_row["ok"])
        and bool(pdg["checks_ok"])
        and m_dual
        and t_dual
        and axis_shared
    )

    return {
        "device": device,
        "checks_ok": checks_ok,
        "m_floor1_pm": {
            "checks_ok": pm["checks_ok"],
            "pm_annihilated": pm["pm_annihilated"],
            "pm_peaks_on_delta": pm["pm_peaks_on_delta"],
            "pm_axis_angle": pm.get("pm_axis_angle"),
            "wall_s": pm["wall_s"],
        },
        "t_head_on": {
            "ok": t_row["ok"],
            "back_to_back_proxy": t_row["back_to_back_proxy"],
            "peaks_on_delta": t_row["peaks_on_delta"],
            "mean_axis_pi_err_rad": t_row["mean_axis_pi_err_rad"],
            "axis_tracks_pi": t_row["axis_tracks_pi"],
        },
        "link_dual_front_both_paths": m_dual and t_dual,
        "link_shared_dipole_instrument": axis_shared,
        "pdg_tau_bridge": {
            "checks_ok": pdg["checks_ok"],
            "tau_qed_rel_err": pdg["tau_qed_rel_err"],
            "tau_M_over_tau_PDG": pdg["tau_M_over_tau_PDG"],
        },
        "wall_s": time.perf_counter() - t0,
        "note": (
            "§5.0.3 chain: pm_nn annihilation on A5 boil → coarse Δ|Φ| dipole; "
            "independent T2 head-on ensemble → same dipole axis instrument + mod-π tracking."
        ),
    }
