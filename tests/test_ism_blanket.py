"""ISM blanket — T_ISM readout (not Planck bath)."""

from __future__ import annotations

from mt_ca.config import MConfig
from mt_ca.ism_blanket import apply_ism_blanket, blanket_distribution_report, tau_map_ism_blanket
from mt_ca.ism_screen import load_ism_constraints
from mt_ca.seeds import boil_ocean_spinor_3d
from mt_ca.simulator import LatticeFluidSimulator


def test_T_ism_in_thousands_K_not_bath() -> None:
    c = load_ism_constraints()
    nz = 32
    th = 4
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
    sim.step(64)
    z0 = sim.z.clone()
    tau, path = tau_map_ism_blanket(nz, nz, c, device=sim.device, dtype=sim.dtype)
    zb = apply_ism_blanket(sim.z, tau, thickness=th, frac_bits=cfg.frac_bits, mod_bits=cfg.mod_bits)
    rep = blanket_distribution_report(
        z0, zb, thickness=th, block=4, tau_2d=tau, path_2d=path, constraints=c
    )
    t = rep["T_ism"]
    mean = t["T_ism_map_K"]["mean_K"]
    assert 1.0e3 <= mean <= 1.0e5
    assert t["T_ism_map_K"]["log10_mean"] < 10.0
