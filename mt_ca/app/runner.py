"""Simulation runner — apply ScenarioSpec, step g, return RunResult."""
from __future__ import annotations

import time
from typing import Any

import torch

from mt_ca.app.gates import peak_stats
from mt_ca.app.readout_probe import gates_at_z, planted_persisted
from mt_ca.app.run_spec import RunSpec
from mt_ca.app.results import RunResult
from mt_ca.app.scenario import ScenarioSpec
from mt_ca.config import MConfig
from mt_ca.fixed_point import decode_spinor
from mt_ca.ledger import ledger_step_probe, momentum_density, n_E_field
from mt_ca.metrics import coarse_amplitude, field_amplitude, has_nan, norm_drift
from mt_ca.seeds import SeedClass, make_seed, vacuum_boil_fixed
from mt_ca.si_constants import internal_phase_decode, kappa_link
from mt_ca.simulator import LatticeFluidSimulator
from mt_ca.spinor import bloch_vector, spinor_density, saturating_phase


def apply_scenario(sim: LatticeFluidSimulator, scenario: ScenarioSpec) -> None:
    """Initialize simulator from SSOT scenario (habitat + seed / brick)."""
    kw = {
        "device": sim.device,
        "dtype": sim.dtype,
        "mod_bits": sim.cfg.mod_bits,
        "frac_bits": sim.cfg.frac_bits,
        "phase_bits": sim.cfg.phase_bits,
    }
    if scenario.brick is not None:
        if sim.nz is not None:
            raise ValueError("Brick boil scenarios are 2D-only")
        b = scenario.brick
        f = vacuum_boil_fixed(
            sim.ny,
            sim.nx,
            device=sim.device,
            mod_bits=sim.cfg.mod_bits,
            frac_bits=sim.cfg.frac_bits,
            phase_bits=sim.cfg.phase_bits,
            class_dy=b.class_dy,
            class_dx=b.class_dx,
            class_offset=b.class_offset,
        )
        z = decode_spinor(f, frac_bits=sim.cfg.frac_bits, mod_bits=sim.cfg.mod_bits).to(
            device=sim.device, dtype=sim.dtype
        )
        sim.set_field(z)
        return

    if scenario.seed is SeedClass.VACUUM_BOIL and sim.nz is None:
        z = make_seed(SeedClass.VACUUM_BOIL, sim.ny, sim.nx, **kw)
        sim.set_field(z)
        return

    z = make_seed(
        scenario.seed,
        sim.ny,
        sim.nx,
        nz=sim.nz,
        impulse_amplitude=scenario.impulse_amplitude,
        **kw,
    )
    sim.set_field(z)


def run(spec: RunSpec) -> RunResult:
    """Execute one simulation run and return a typed result."""
    cfg = MConfig.for_stencil(spec.scenario.stencil)
    sim = LatticeFluidSimulator(
        spec.ny,
        spec.nx,
        cfg,
        nz=spec.nz,
        device=spec.device,
    )
    apply_scenario(sim, spec.scenario)

    planted = spec.scenario.seed in (
        SeedClass.VORTEX_P,
        SeedClass.VORTEX_M,
        SeedClass.VORTEX_N2,
    )
    gate0 = gates_at_z(sim.z, with_anchor=True)
    samples: list[dict[str, Any]] = []
    t0 = time.perf_counter()
    ps_anchor = "center" if planted else None

    if spec.sample_every is not None:
        samples.append(
            {"t": 0, **peak_stats(sim.z, anchor=ps_anchor), "norm": sim.norm()}
        )
        done = 0
        while done < spec.steps:
            chunk = min(spec.sample_every, spec.steps - done)
            sim.step(chunk)
            done += chunk
            samples.append(
                {"t": done, **peak_stats(sim.z, anchor=ps_anchor), "norm": sim.norm()}
            )
    else:
        if spec.settle > 0:
            sim.step(spec.settle)
        remaining = max(0, spec.steps - spec.settle)
        if remaining > 0:
            sim.step(remaining)

    elapsed = time.perf_counter() - t0
    gate1 = gates_at_z(sim.z, with_anchor=True)
    coarse = coarse_amplitude(sim.z, spec.block).cpu()

    extra: dict[str, Any] = {}
    if samples:
        extra["emerged_b"] = any(
            s.get("passed_survey", False) or s.get("passed_anchor", False) for s in samples[1:]
        )
        extra["contrast_grew"] = samples[-1]["contrast"] > samples[0]["contrast"] * 1.05

    return RunResult(
        id=spec.scenario.id,
        spec=spec,
        habitat=spec.scenario.habitat_label,
        seed=spec.scenario.seed.value,
        device=spec.device,
        seconds=round(elapsed, 4),
        norm0=float(sim.norm0 or sim.norm()),
        norm_final=sim.norm(),
        norm_drift=norm_drift(sim.norm0, sim.norm()),
        gate0=gate0,
        gate1=gate1,
        samples=samples,
        extra={
            **extra,
            "nan": has_nan(sim.z),
            "coarse_amp_max": float(coarse.max().item()),
            "steps_per_sec": round(spec.steps / elapsed, 1) if elapsed > 0 else None,
        },
        ok=bool(gate1["passed_anchor"]) if planted else None,
    )


def track_gamma_points(
    sim: LatticeFluidSimulator,
    *,
    cells: list[tuple[int, int]],
    track: int,
    n_ring: int,
    p0_nat: float,
) -> dict[str, dict[str, int | list]]:
    """Sample (q,p) Γ points at lattice cells over ``track`` ticks of g."""
    cfg = sim.cfg

    def _sample(z: torch.Tensor, z_past: torch.Tensor, y: int, x: int) -> tuple:
        phi = saturating_phase(z, cfg)
        phi_ticks = int(phi[y, x].round().item()) % n_ring
        k_phi, phi_f = internal_phase_decode(phi_ticks)
        n_e = int(n_E_field(phi, cfg)[y, x].item())
        bv = bloch_vector(z[y : y + 1, x : x + 1])[0, 0]
        bloch_key = tuple(round(float(bv[i].item()), 3) for i in range(3))
        rho = float(spinor_density(z[y : y + 1, x : x + 1])[0, 0].item())
        px, py = momentum_density(z)
        pi_x = int(round(float(px[y, x].item()) / p0_nat))
        pi_y = int(round(float(py[y, x].item()) / p0_nat))
        kick = int(ledger_step_probe(z, z_past, cfg)["phi"][y, x].item())
        return (phi_ticks, k_phi, phi_f, n_e, kick, pi_x, pi_y, bloch_key, round(rho, 4))

    def _summarize(samples: list[tuple]) -> dict[str, int | list]:
        kicks = {s[4] for s in samples}
        last = samples[-1]
        return {
            "unique_points": len({s[:8] for s in samples}),
            "ticks": len(samples),
            "nonzero_kicks": sum(1 for k in kicks if k != 0),
            "phi_disc": last[0],
            "k_phi": last[1],
            "phi_f": last[2],
            "n_E": last[3],
            "Phi_kick": last[4],
            "pi_p0": [last[5], last[6]],
            "bloch": list(last[7]),
        }

    z = sim.z
    z_past = sim.z_past.clone() if sim.z_past is not None else z.clone()
    per_cell: dict[str, list[tuple]] = {f"{y},{x}": [_sample(z, z_past, y, x)] for y, x in cells}
    for _ in range(track):
        z_past = z.clone()
        sim.step(1)
        z = sim.z
        for y, x in cells:
            per_cell[f"{y},{x}"].append(_sample(z, z_past, y, x))

    return {key: _summarize(vals) for key, vals in per_cell.items()}


def run_floor0_phase_space(
    *,
    size: int = 64,
    settle: int = 64,
    track: int = 32,
    device: str = "cpu",
) -> dict[str, Any]:
    """§5.0.4-A — Γ_hV probe on boiling ocean + planckon (uses app runner)."""
    from mt_ca.app.scenario import get_scenario
    from mt_ca.si_constants import elementary_quanta_row, hv_bit_budget

    spec = RunSpec(
        scenario=get_scenario("floor0_planckon"),
        ny=size,
        nx=size,
        steps=0,
        device=device,
        settle=settle,
        track=track,
    )
    cfg = MConfig.for_stencil(spec.scenario.stencil)
    sim = LatticeFluidSimulator(size, size, cfg, device=device)
    apply_scenario(sim, spec.scenario)

    from mt_ca.si_floor0_rows import _BLOCH_DISTINCT_Q6

    bb = hv_bit_budget()
    eq = elementary_quanta_row()
    n_ring = int(eq["N_ring"])
    dphi_disc = int(eq["delta_phi_min_disc"])
    ticks_per_e0 = int(eq["energy_ticks_per_E0"])
    n_e_classes = n_ring // ticks_per_e0 + 1
    p0_nat = float(kappa_link())
    cap = int(round(bb.n_states))
    naive_gamma = (
        n_ring * int(bb.N_phi) * dphi_disc * _BLOCH_DISTINCT_Q6 * n_ring * n_e_classes
    )
    cy = cx = size // 2
    amp0 = float(field_amplitude(sim.z).max().item())
    for _ in range(settle):
        sim.step(1)
    amp_settled = float(field_amplitude(sim.z).max().item())

    tracks = track_gamma_points(
        sim,
        cells=[(cy, cx), (10, 10)],
        track=track,
        n_ring=n_ring,
        p0_nat=p0_nat,
    )
    core = tracks[f"{cy},{cx}"]
    bath = tracks["10,10"]
    ocean_moves = amp_settled > amp0 * 1.01 or core["unique_points"] > 1

    q_axes = [
        {"id": "phi_disc", "states": n_ring, "note": "ring position mod N_ring"},
        {"id": "k_phi", "states": int(bb.N_phi), "note": "Heisenberg sector"},
        {"id": "phi_f", "states": dphi_disc, "note": "fine phase in sector"},
        {"id": "bloch", "states": _BLOCH_DISTINCT_Q6, "note": "Q(frac_bits) orientation classes"},
    ]
    p_axes = [
        {"id": "Phi_kick", "states": n_ring, "note": "kick ticks per dt; 0 or |Φ|≥Δφ_disc"},
        {"id": "n_E", "states": n_e_classes, "note": "E₀ ledger from |Φ|"},
        {"id": "pi_p0", "states": -1, "note": "π/p₀ integer; width open-bound"},
    ]

    return {
        "habitat": spec.scenario.habitat_label,
        "p0_natural": p0_nat,
        "N_ring": n_ring,
        "delta_phi_disc": dphi_disc,
        "n_E_classes": n_e_classes,
        "bekenstein_cap_states": cap,
        "q_axes": q_axes,
        "p_axes": p_axes,
        "naive_q_times_p": naive_gamma,
        "cap_below_naive_gamma": cap < naive_gamma,
        "rho_max_initial": amp0,
        "rho_max_after_settle": amp_settled,
        "ocean_contrast_grows": ocean_moves,
        "planckon_core": core,
        "bath_brick": bath,
        "planckon_iteration_unique": core["unique_points"],
        "planckon_nonzero_kicks": core["nonzero_kicks"],
        "checks_ok": (
            cap < naive_gamma
            and abs(p0_nat - 0.25) < 1e-9
            and ocean_moves
            and core["unique_points"] > 1
        ),
        "derivation_closed": False,
        "note": (
            "§5.0.4-A: Γ_hV on filled boiling ocean; planckon core iterates under g. "
            "Full Γ table still open."
        ),
    }


def run_floor0_nE_excitation_harness(
    *,
    size: int = 64,
    settle: int = 64,
    track: int = 32,
    device: str = "cpu",
    min_n_E: int = 1,
    winding_min: float = 0.75,
) -> dict[str, Any]:
    """§5.0.4-A — post-settle ledger track: n_E≥1 at planckon core under free g.

    Protocol (kick-harness): floor0_planckon on VACUUM_BOIL → settle → track ticks;
    read integer Φ and n_E from ``projected_phi_int`` at the planted core (not the
    settled snapshot alone, which stays n_E=0).
    """
    from mt_ca.app.scenario import get_scenario
    from mt_ca.projected_collision import projected_phi_int
    from mt_ca.reversible import canonical_fixed
    from mt_ca.si_constants import elementary_quanta_row, energy_ledger_ticks_per_E0
    from mt_ca.topology import matter_occupancy_b, winding_channels

    spec = RunSpec(
        scenario=get_scenario("floor0_planckon"),
        ny=size,
        nx=size,
        steps=0,
        device=device,
        settle=0,
        track=0,
    )
    cfg = MConfig.for_stencil(spec.scenario.stencil)
    sim = LatticeFluidSimulator(size, size, cfg, device=device)
    apply_scenario(sim, spec.scenario)
    cy = cx = size // 2
    ticks_per_e0 = energy_ledger_ticks_per_E0(phase_bits=cfg.phase_bits)

    for _ in range(settle):
        sim.step(1)

    hits: list[dict[str, int | float | bool]] = []
    peak_n_e = 0
    peak_phi = 0
    peak_tick = 0

    for tick in range(1, track + 1):
        sim.step(1)
        f = canonical_fixed(sim.z, cfg)
        phi = projected_phi_int(f, cfg)
        n_e = int(n_E_field(phi, cfg)[cy, cx].item())
        phi_core = int(phi[cy, cx].abs().item())
        b_core = int(matter_occupancy_b(sim.z, y=cy, x=cx))
        w_abs = abs(float(winding_channels(sim.z, center=(cy, cx), radius=2)["auto"]))
        if n_e > peak_n_e or (n_e == peak_n_e and phi_core > peak_phi):
            peak_n_e = n_e
            peak_phi = phi_core
            peak_tick = tick
        if n_e >= min_n_E and b_core == 1 and w_abs >= winding_min:
            hits.append(
                {
                    "tick": tick,
                    "n_E": n_e,
                    "phi_ticks": phi_core,
                    "b_core": b_core,
                    "winding_abs": w_abs,
                }
            )

    eq = elementary_quanta_row()
    first = hits[0] if hits else None
    ok = peak_n_e >= min_n_E and len(hits) >= 1

    return {
        "habitat": spec.scenario.habitat_label,
        "settle": settle,
        "track": track,
        "ticks_per_E0": ticks_per_e0,
        "E0_1_ticks": int(eq["delta_phi_min_disc"]),
        "n_E_peak_core": peak_n_e,
        "phi_ticks_peak_core": peak_phi,
        "peak_tick": peak_tick,
        "first_hit": first,
        "hits_planckon": len(hits),
        "hit_samples": hits[:8],
        "min_n_E": min_n_E,
        "checks_ok": ok,
        "derivation_closed": False,
        "note": (
            "§5.0.4-A kick-harness: after planckon settle, free g yields n_E≥1 on core "
            "in ledger track (integer Φ); settled snapshot alone stays n_E=0."
        ),
    }
