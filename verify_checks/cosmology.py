"""verify_checks.cosmology — ISM screen / CMB-readout dogfood (META §3.0.1 exploratory)."""

from __future__ import annotations

from mt_ca.ism_screen import evaluate_ism_screen_v1
from mt_ca.si_constants import SI


def check_ism_screen_v0(device: str = "cpu") -> dict:
    """v1 physics (verify id legacy): ν+τ screen; VLISM n_e from B,T_eff(rms)."""
    del device
    bath = SI.vacuum_bath_row()
    log10_gap = float(bath["log10_T_M_bath_over_CMB"])
    row = evaluate_ism_screen_v1(log10_T_M_over_CMB=log10_gap)
    row["T_M_bath_K"] = bath["T_M_bath_K"]
    return row


def check_ism_screen_v0_sim(size: int = 32, device: str = "cpu") -> dict:
    """Optional heavier row: measured boil-wall rms on small 3D FCC grid."""
    import sys
    from pathlib import Path

    import torch

    from mt_ca.config import MConfig
    from mt_ca.simulator import LatticeFluidSimulator

    scripts = Path(__file__).resolve().parents[1] / "scripts"
    if str(scripts) not in sys.path:
        sys.path.insert(0, str(scripts))
    from run_cmb_forward_envelope import calibrate_wall_row  # noqa: WPS433

    if device == "cuda" and not torch.cuda.is_available():
        device = "cpu"

    nz = size
    cfg = MConfig.for_stencil("fcc")
    sim = LatticeFluidSimulator(nz, nz, cfg, nz=nz, device=device)
    nu_list = [1, 4, 16, 64]
    cal = calibrate_wall_row(
        sim,
        cfg,
        nz=nz,
        settle=128,
        delta_angle=0.125,
        axis="x",
        block=4,
        iz=nz // 2,
        nu_passes=nu_list,
    )
    bath = SI.vacuum_bath_row()
    row = evaluate_ism_screen_v1(
        log10_T_M_over_CMB=float(bath["log10_T_M_bath_over_CMB"]),
        rms_rel_wall=float(cal["rms_rel"]),
    )
    row["id"] = "ISM_screen_v1_sim"
    row["dims"] = f"{nz}^3"
    row["settle"] = cal["settle"]
    row["delta_angle"] = cal["delta_angle"]
    row["measured_max_rel"] = cal["max_rel"]
    return row
