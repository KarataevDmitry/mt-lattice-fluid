"""Homogeneous ISM blanket — derived T_eq, no T_LIC in formula."""

from __future__ import annotations

import copy

import torch

from mt_ca.config import MConfig
from mt_ca.ism_blanket import apply_ism_blanket, blanket_distribution_report, ism_T_map_K, tau_uniform_ism_blanket
from mt_ca.ism_screen import equilibrium_T_wnm_K, load_ism_constraints
from mt_ca.seeds import boil_ocean_spinor_3d
from mt_ca.simulator import LatticeFluidSimulator


def test_uniform_tau() -> None:
    c = load_ism_constraints()
    tau = tau_uniform_ism_blanket(16, 16, c, device=torch.device("cpu"))
    assert float((tau.max() - tau.min()).item()) < 1.0e-6


def test_T_map_ignores_observed_T_LIC_in_yaml() -> None:
    c = load_ism_constraints()
    phi = torch.ones(8, 8) * 0.02
    base = ism_T_map_K(phi, phi, c)
    c2 = copy.deepcopy(c)
    c2["lic"]["T_K_warm_nominal"] = 999_999.0
    alt = ism_T_map_K(phi, phi, c2)
    assert torch.allclose(base, alt)


def test_derived_T_eq_in_thousands_K() -> None:
    c = load_ism_constraints()
    t_eq = equilibrium_T_wnm_K(float(c["lic"]["n_H_cm3_nominal"]), c)
    assert 4_000.0 <= t_eq <= 10_000.0


def test_blanket_log10_T_not_planck() -> None:
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
    tau = tau_uniform_ism_blanket(nz, nz, c, device=sim.device)
    zb = apply_ism_blanket(sim.z, tau, thickness=th, frac_bits=cfg.frac_bits, mod_bits=cfg.mod_bits)
    rep = blanket_distribution_report(z0, zb, thickness=th, block=4, tau_2d=tau, constraints=c)
    assert rep["T_ism"]["T_ism_map_K"]["log10_mean"] < 5.0
