"""verify_checks.cosmology — ISM screen / CMB-readout dogfood (META §3.0.1 exploratory)."""

from __future__ import annotations

from mt_ca.ism_screen import evaluate_ism_screen_v1, evaluate_ism_screen_v2
from mt_ca.si_constants import SI


def check_ism_screen_v0(device: str = "cpu") -> dict:
    """Fast verify: v1 gates (v2 physics, no sim decay / N_CMB)."""
    del device
    bath = SI.vacuum_bath_row()
    log10_gap = float(bath["log10_T_M_bath_over_CMB"])
    row = evaluate_ism_screen_v1(log10_T_M_over_CMB=log10_gap)
    row["T_M_bath_K"] = bath["T_M_bath_K"]
    return row


def check_ism_screen_v0_sim(size: int = 32, device: str = "cpu") -> dict:
    """Heavier row: wall rms + ν decay extrapolation to N_CMB (v2)."""
    import sys
    from pathlib import Path

    import torch

    from mt_ca.config import MConfig
    from mt_ca.simulator import LatticeFluidSimulator
    from mt_ca.t_validation import nu_readout_passes

    scripts = Path(__file__).resolve().parents[1] / "scripts"
    if str(scripts) not in sys.path:
        sys.path.insert(0, str(scripts))
    from run_cmb_forward_envelope import calibrate_wall_row  # noqa: WPS433

    if device == "cuda" and not torch.cuda.is_available():
        device = "cpu"

    block = 4
    nz = size
    cfg = MConfig.for_stencil("fcc")
    sim = LatticeFluidSimulator(nz, nz, cfg, nz=nz, device=device)
    nu_list = [1, 4, 16, 64, 256]
    cal = calibrate_wall_row(
        sim,
        cfg,
        nz=nz,
        settle=128,
        delta_angle=0.125,
        axis="x",
        block=block,
        iz=nz // 2,
        nu_passes=nu_list,
    )
    bath = SI.vacuum_bath_row()
    bubble = SI.bubble_tick_row()
    nu_ncmb = float(nu_readout_passes(int(bubble["N_CMB"]), block))
    row = evaluate_ism_screen_v2(
        log10_T_M_over_CMB=float(bath["log10_T_M_bath_over_CMB"]),
        rms_rel_wall=float(cal["rms_rel"]),
        smooth_decay=cal["smooth_decay"],
        nu_at_N_CMB=nu_ncmb,
        block=block,
    )
    row["dims"] = f"{nz}^3"
    row["settle"] = cal["settle"]
    row["delta_angle"] = cal["delta_angle"]
    row["measured_max_rel"] = cal["max_rel"]
    row["N_CMB_sci"] = bubble["N_CMB_sci"]
    return row
