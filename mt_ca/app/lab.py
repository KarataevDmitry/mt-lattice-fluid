"""Instrument lab SSOT — always pairs sim.cfg with panel / planckon readouts."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import torch

from mt_ca.app.dimension import LatticeDimension
from mt_ca.app.gates import gate_b
from mt_ca.app.lattice import build_run_spec, describe_lattice, open_lattice
from mt_ca.app.run_spec import RunSpec
from mt_ca.instruments.panel import sample_field, sample_panel, sample_site
from mt_ca.matter_readout import (
    MatterSite,
    default_anchor,
    planckon_instrument,
    snap_column_peak,
)
from mt_ca.projected_collision import projected_phi_int
from mt_ca.reversible import canonical_fixed
from mt_ca.simulator import LatticeFluidSimulator
from mt_ca.spinor import spinor_density
from mt_ca.topology import matter_occupancy_b


@dataclass(frozen=True, slots=True)
class LabSession:
    """One open lattice + instrument context (cfg never detached from sim)."""

    spec: RunSpec
    sim: LatticeFluidSimulator
    dimension: LatticeDimension

    @property
    def cfg(self):
        return self.sim.cfg

    @property
    def meta(self) -> dict[str, str | int | None]:
        return describe_lattice(self.spec)

    def step(self, ticks: int = 1) -> None:
        if ticks > 0:
            self.sim.step(ticks)

    def settle(self, ticks: int) -> MatterSite:
        self.step(ticks)
        return default_anchor(self.sim.z)

    def panel(
        self,
        *,
        site: MatterSite | None = None,
        z_past: torch.Tensor | None = None,
        contour_radius: int = 2,
    ) -> dict[str, Any]:
        if z_past is None and self.sim.z_past is not None:
            z_past = self.sim.z_past
        return sample_panel(
            self.sim.z,
            self.cfg,
            site=site,
            z_past=z_past,
            contour_radius=contour_radius,
        )

    def site_row(
        self,
        site: MatterSite,
        *,
        z_past: torch.Tensor | None = None,
        contour_radius: int = 2,
    ) -> dict[str, Any]:
        return sample_site(
            self.sim.z,
            site,
            self.cfg,
            contour_radius=contour_radius,
            z_past=z_past,
        )

    def field_row(self, *, z_past: torch.Tensor | None = None) -> dict[str, Any]:
        return sample_field(self.sim.z, self.cfg, z_past=z_past)

    def projected_phi_at(self, site: MatterSite) -> int:
        phi = projected_phi_int(canonical_fixed(self.sim.z, self.cfg), self.cfg)
        if phi.ndim == 2:
            return int(phi[site.y, site.x].abs().item())
        iz = site.iz if site.iz is not None else 0
        return int(phi[iz, site.y, site.x].abs().item())

    def snap_sites(self, coords: dict[str, tuple[int, int]]) -> dict[str, MatterSite]:
        rho = spinor_density(self.sim.z)
        return {name: snap_column_peak(rho, y, x) for name, (y, x) in coords.items()}


def open_lab(
    scenario_id: str,
    edge: int,
    *,
    embedding: LatticeDimension | None = None,
    device: str = "cpu",
    steps: int = 0,
    **run_kw: object,
) -> LabSession:
    spec = build_run_spec(
        scenario_id, edge, device=device, steps=steps, embedding=embedding, **run_kw
    )
    sim = open_lattice(spec)
    return LabSession(spec=spec, sim=sim, dimension=spec.embedding)


def open_lab_from_spec(spec: RunSpec) -> LabSession:
    sim = open_lattice(spec)
    return LabSession(spec=spec, sim=sim, dimension=spec.embedding)


def planckon_lab_report(
    scenario_id: str = "floor0_planckon",
    *,
    edge: int = 48,
    settle: int = 0,
    steps: int = 128,
    device: str = "cpu",
) -> dict[str, Any]:
    """§5.0 instrument row — boil habitat + anchor (verify / probes)."""
    lab = open_lab(scenario_id, edge, device=device)
    if settle > 0:
        lab.step(settle)
    lab.step(steps)
    anchor = default_anchor(lab.sim.z)
    inst = planckon_instrument(lab.sim.z, anchor=anchor, top_k=8, cfg=lab.cfg)
    gate_survey = gate_b(lab.sim.z, anchor=None)
    gate_core = gate_b(lab.sim.z, anchor=anchor)
    core_b = matter_occupancy_b(
        lab.sim.z, y=anchor.y, x=anchor.x, iz=anchor.iz
    )
    w_auto = float(inst["anchor"]["w_auto"]) if inst.get("anchor") else float("nan")
    ok = (
        inst["b_anchor"] == 1
        and inst["passed_anchor"]
        and gate_core["passed"]
        and core_b == 1
        and w_auto == w_auto
        and abs(w_auto) >= 0.75
    )
    return {
        **lab.meta,
        "settle": settle,
        "steps": steps,
        "anchor": {"iz": anchor.iz, "y": anchor.y, "x": anchor.x},
        "b_anchor": inst["b_anchor"],
        "passed_anchor": inst["passed_anchor"],
        "passed_survey": inst["passed_survey"],
        "gate_survey_passed": gate_survey["passed"],
        "gate_anchor_passed": gate_core["passed"],
        "core_b_fixed_site": core_b,
        "anchor_w_auto": w_auto,
        "ok": ok,
    }
