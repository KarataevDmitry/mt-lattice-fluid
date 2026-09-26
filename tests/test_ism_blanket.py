"""ISM blanket over ocean — smoke."""

from __future__ import annotations

from mt_ca.config import MConfig
from mt_ca.ism_blanket import apply_ism_blanket, blanket_distribution_report, tau_map_ism_blanket
from mt_ca.ism_screen import load_ism_constraints
from mt_ca.seeds import boil_ocean_spinor_3d
from mt_ca.simulator import LatticeFluidSimulator


def test_blanket_attensuates_top() -> None:
    c = load_ism_constraints()
    nz = 24
    cfg = MConfig.for_stencil("fcc")
    sim = LatticeFluidSimulator(nz, nz, cfg, nz=nz, device="cpu")
    kw = {
        "device": sim.device,
        "dtype": sim.dtype,
        "mod_bits": cfg.mod_bits,
        "frac_bits": cfg.frac_bits,
        "phase_bits": cfg.phase_bits,
    }
    sim.set_field(boil_ocean_spinor_3d(nz, nz, nz, **kw))
    sim.step(32)
    z0 = sim.z.clone()
    tau = tau_map_ism_blanket(nz, nz, c, device=sim.device, dtype=sim.dtype)
    zb = apply_ism_blanket(sim.z, tau, thickness=4, frac_bits=cfg.frac_bits, mod_bits=cfg.mod_bits)
    rep = blanket_distribution_report(z0, zb, thickness=4, block=4, tau_2d=tau)
    assert rep["contrast_ratio_mean"] < 1.0
    assert rep["tau_max"] > rep["tau_min"]
