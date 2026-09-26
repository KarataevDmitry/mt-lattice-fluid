"""§5.0.4-A — periodic drive on planckon core vs n_E ladder (resonance probe)."""
from __future__ import annotations

import math
from typing import Any

import torch

from mt_ca.app.runner import apply_scenario
from mt_ca.app.scenario import get_scenario
from mt_ca.config import MConfig
from mt_ca.ledger import n_E_field
from mt_ca.projected_collision import projected_phi_int
from mt_ca.reversible import canonical_fixed
from mt_ca.simulator import LatticeFluidSimulator
from mt_ca.spinor import bloch_vector, su2_apply
from mt_ca.topology import matter_occupancy_b


def apply_core_e0_kick(
    sim: LatticeFluidSimulator,
    y: int,
    x: int,
    *,
    e0_quanta: int = 1,
) -> None:
    """One SU(2) pulse on core ≈ ``e0_quanta`` × E₀ phase on Z_N_ring (instrument, not new g)."""
    cfg = sim.cfg
    n_ring = 1 << cfg.phase_bits
    ticks = 41 * max(1, int(e0_quanta))
    phi_rad = 2.0 * math.pi * ticks / n_ring
    z = sim.z.clone()
    z_core = z[y, x]
    axis = bloch_vector(z[y : y + 1, x : x + 1])[0, 0]
    z[y, x] = su2_apply(
        z_core.unsqueeze(0).unsqueeze(0),
        torch.tensor([[phi_rad]], device=sim.device),
        axis.unsqueeze(0).unsqueeze(0),
    )[0, 0]
    sim.set_field(z, z_past=sim.z_past)


def _core_ledger(sim: LatticeFluidSimulator, y: int, x: int) -> tuple[int, int, int]:
    cfg = sim.cfg
    f = canonical_fixed(sim.z, cfg)
    phi = projected_phi_int(f, cfg)
    ne = int(n_E_field(phi, cfg)[y, x].item())
    pt = int(phi[y, x].abs().item())
    b = int(matter_occupancy_b(sim.z, y=y, x=x))
    return ne, pt, b


def run_floor0_resonance_trial(
    *,
    drive_period: int | None,
    size: int = 64,
    settle: int = 64,
    n_periods: int = 64,
    e0_quanta: int = 1,
    response_window: int = 8,
    device: str = "cpu",
) -> dict[str, Any]:
    """Periodic E₀ kick every ``drive_period`` ticks after settle; measure n_E response.

    ``drive_period=None`` — free evolution only (no injected kicks).
    """
    cfg = MConfig.for_stencil("hex")
    sim = LatticeFluidSimulator(size, size, cfg, device=device)
    apply_scenario(sim, get_scenario("floor0_planckon"))
    cy = cx = size // 2
    sim.step(settle)

    use_drive = drive_period is not None and e0_quanta > 0 and drive_period >= 1
    total = (drive_period or 512) * n_periods if use_drive else 512 * n_periods // 4

    matter_ticks = 0
    excited_ticks = 0
    ne_sum = 0
    hits_after_drive = 0
    drive_events = 0
    pending_capture = 0

    for tick in range(1, total + 1):
        if use_drive and tick % drive_period == 0:
            apply_core_e0_kick(sim, cy, cx, e0_quanta=e0_quanta)
            drive_events += 1
            pending_capture = response_window

        sim.step(1)
        ne, _, b = _core_ledger(sim, cy, cx)

        if pending_capture > 0:
            if b == 1 and ne >= e0_quanta:
                hits_after_drive += 1
                pending_capture = 0
            else:
                pending_capture -= 1

        if b == 1:
            matter_ticks += 1
            if ne >= 1:
                excited_ticks += 1
                ne_sum += ne

    excited_frac = excited_ticks / matter_ticks if matter_ticks else 0.0
    mean_ne_excited = ne_sum / excited_ticks if excited_ticks else 0.0
    capture = hits_after_drive / drive_events if drive_events else 0.0

    return {
        "drive_period": drive_period,
        "n_periods": n_periods,
        "e0_quanta": e0_quanta,
        "response_window": response_window,
        "excited_fraction": excited_frac,
        "mean_n_E_when_excited": mean_ne_excited,
        "post_drive_capture": capture,
        "matter_ticks": matter_ticks,
        "drive_events": drive_events,
    }


def run_floor0_resonance_sweep(
    *,
    periods: list[int] | None = None,
    size: int = 64,
    settle: int = 64,
    n_periods: int = 48,
    e0_quanta: int = 1,
    device: str = "cpu",
) -> dict[str, Any]:
    """Sweep drive period; report argmax of post_drive_capture."""
    if periods is None:
        periods = list(range(4, 65))

    rows: list[dict[str, Any]] = []
    for T in periods:
        rows.append(
            run_floor0_resonance_trial(
                drive_period=T,
                size=size,
                settle=settle,
                n_periods=n_periods,
                e0_quanta=e0_quanta,
                device=device,
            )
        )

    best_cap = max(rows, key=lambda r: r["post_drive_capture"])
    baseline = run_floor0_resonance_trial(
        drive_period=None,
        size=size,
        settle=settle,
        n_periods=n_periods,
        e0_quanta=e0_quanta,
        device=device,
    )

    ref_periods = [8, 16, 32, 41, 64, 82]

    return {
        "rows": rows,
        "best_capture_period": best_cap["drive_period"],
        "best_capture": best_cap["post_drive_capture"],
        "baseline_excited_fraction": baseline["excited_fraction"],
        "reference_periods_ticks": ref_periods,
        "e0_quanta": e0_quanta,
        "checks_ok": best_cap["post_drive_capture"] > 0.15,
        "note": (
            "Periodic E0 kick on core; post_drive_capture = drives followed within "
            f"{rows[0]['response_window']} ticks by n_E≥e0_quanta on b=1 core."
        ),
    }
