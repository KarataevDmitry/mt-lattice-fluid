"""Instrument panel — catalog wired to sim."""
from __future__ import annotations


def check_instrument_panel_vortex(size: int = 64, device: str = "cpu") -> dict:
    from mt_ca.config import MConfig
    from mt_ca.instruments import REGISTRY, sample_panel
    from mt_ca.seeds import SeedClass
    from mt_ca.simulator import LatticeFluidSimulator

    dev = __import__("torch").device(device)
    cfg = MConfig.for_stencil("hex")
    sim = LatticeFluidSimulator(size, size, cfg, device=dev)
    sim.reset(SeedClass.VORTEX_P)
    sim.step(32)
    panel = sample_panel(sim.z, cfg, z_past=sim.z_past)
    site = panel["site"]
    ok = (
        len(REGISTRY) >= 15
        and site["b_matter"] == 1
        and site["rho_field"] > 0
        and site["n_E"] >= 0
        and "phi_kick_tick" in site
    )
    return {
        "id": "Instrument_panel_vortex",
        "ok": ok,
        "catalog_count": len(REGISTRY),
        "b_matter": site["b_matter"],
        "n_topo": site["n_topo"],
        "n_E": site["n_E"],
        "rho_contrast": panel["field"]["rho_contrast"],
        "note": "§5 panel: ρ, b, n, Φ, n_E, π, j, L_z, ledger tick at anchor",
    }
