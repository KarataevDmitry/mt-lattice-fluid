"""SIFloor0Rows — §5.0.4-A internal planckon spectrum (one v_p, floor 0)."""
from __future__ import annotations

import math

import torch


class SIFloor0Rows:
    """Ask/row probes for floor-0 planckon internal spectrum."""

    def brick_internal_spectrum_row(
        self,
        *,
        size: int = 64,
        settle: int = 64,
        track: int = 32,
        device: str = "cpu",
    ) -> dict[str, float | int | str | bool | list]:
        """§5.0.4-A — internal levels on Z_N_ring + SU(2) at one v_p.

        Algebra (closed): landmark ticks on phase ring N_ring=512 and n_E ladder.
        Sim (floor-0 dogfood): VORTEX_P ground — b=1, |Δφ|≪Δφ_min, stable Bloch axis;
        SU(2) monodromy on core spinor: 2π→−1, 4π→+1 (not separate ontological field).

        Open (explicit): gate Φ≥41 ticks (n_E≥1) not observed in free evolution of
        standard seeds — excitation ladder above ground needs dedicated kick harness.
        """
        from mt_ca.config import MConfig
        from mt_ca.ledger import n_E_field
        from mt_ca.seeds import SeedClass
        from mt_ca.simulator import LatticeFluidSimulator
        from mt_ca.si_constants import (
            elementary_quanta_row,
            hv_bit_budget,
            n_E_from_phi_ticks,
        )
        from mt_ca.spinor import (
            arg_phase_defect,
            bloch_vector,
            gate_phase,
            su2_apply,
        )
        from mt_ca.topology import matter_occupancy_b, winding_channels

        eq = elementary_quanta_row()
        bb = hv_bit_budget()
        n_ring = int(eq["N_ring"])
        dphi_disc = int(eq["delta_phi_min_disc"])
        pauli_disc = int(eq["pauli_kick_disc"])
        ticks_per_e0 = int(eq["energy_ticks_per_E0"])

        landmarks: list[dict[str, float | int | str]] = [
            {
                "id": "E0_1",
                "ticks": dphi_disc,
                "n_E": n_E_from_phi_ticks(dphi_disc),
                "role": "one E₀ quantum (Heisenberg Δφ_min)",
            },
            {
                "id": "E0_2",
                "ticks": 2 * dphi_disc,
                "n_E": n_E_from_phi_ticks(2 * dphi_disc),
                "role": "second rung on n_E·E₀ ladder",
            },
            {
                "id": "pauli_pi",
                "ticks": pauli_disc,
                "n_E": n_E_from_phi_ticks(pauli_disc),
                "role": "Pauli exchange kick = N_ring/2 ticks",
            },
            {
                "id": "ring_2pi",
                "ticks": n_ring,
                "n_E": n_E_from_phi_ticks(n_ring),
                "role": "full U(1) cycle on ℤ_N_ring",
            },
        ]

        algebra_ok = (
            ticks_per_e0 == dphi_disc
            and pauli_disc == n_ring // 2
            and all(int(row["n_E"]) == int(row["ticks"]) // ticks_per_e0 for row in landmarks)
            and int(bb.N_ring) == n_ring
        )

        dev = torch.device(device)
        cfg = MConfig.for_stencil("hex")
        cy = cx = size // 2
        sim = LatticeFluidSimulator(size, size, cfg, device=dev)
        sim.reset(SeedClass.VORTEX_P)
        for _ in range(settle):
            sim.step(1)

        z = sim.z
        dphi = arg_phase_defect(z, cfg, apply_floor=False)
        phi = gate_phase(z, cfg)
        n_e = n_E_field(phi, cfg)
        ch = winding_channels(z, center=(cy, cx), radius=2)
        b = matter_occupancy_b(z)
        b_sum = int(b.sum().item()) if hasattr(b, "sum") else int(b)

        dphi_core = float(dphi[cy, cx].abs().item())
        phi_core = float(phi[cy, cx].abs().item())
        n_e_core = int(n_e[cy, cx].item())

        bloch_tail: list[list[float]] = []
        dphi_tail: list[float] = []
        for _ in range(track):
            sim.step(1)
            z = sim.z
            dphi_tail.append(float(arg_phase_defect(z, cfg, apply_floor=False)[cy, cx].abs()))
            bv = bloch_vector(z[cy : cy + 1, cx : cx + 1])[0, 0]
            bloch_tail.append([float(bv[i].item()) for i in range(3)])

        bloch_drift = 0.0
        if len(bloch_tail) >= 2:
            bloch_drift = max(
                abs(bloch_tail[-1][i] - bloch_tail[-2][i]) for i in range(3)
            )

        z_core = z[cy, cx]
        axis = bloch_vector(z_core.unsqueeze(0).unsqueeze(0))[0, 0]

        def su2_overlap(phi_rad: float) -> float:
            z_rot = su2_apply(
                z_core.unsqueeze(0).unsqueeze(0),
                torch.tensor([[phi_rad]], device=dev),
                axis.unsqueeze(0).unsqueeze(0),
            )[0, 0]
            return float((z_core * z_rot.conj()).sum().real.item())

        dot_2pi = su2_overlap(2.0 * math.pi)
        dot_4pi = su2_overlap(4.0 * math.pi)

        ground_ok = (
            b_sum == 1
            and abs(float(ch["auto"])) >= 0.75
            and dphi_core < float(eq["delta_phi_min_rad"])
            and n_e_core == 0
            and bloch_drift < 0.02
            and max(dphi_tail) < float(eq["delta_phi_min_rad"])
        )
        su2_ok = dot_2pi < -0.9 and dot_4pi > 0.9

        return {
            "N_ring": n_ring,
            "N_phi": int(bb.N_phi),
            "B_hV": float(bb.B_hV),
            "delta_phi_min_disc": dphi_disc,
            "delta_phi_min_rad": float(eq["delta_phi_min_rad"]),
            "pauli_kick_disc": pauli_disc,
            "ticks_per_E0": ticks_per_e0,
            "landmarks": landmarks,
            "algebra_ok": algebra_ok,
            "ground_b_sum": b_sum,
            "ground_winding_auto": float(ch["auto"]),
            "ground_dphi_core": dphi_core,
            "ground_phi_ticks_core": phi_core,
            "ground_n_E_core": n_e_core,
            "ground_bloch": bloch_tail[-1] if bloch_tail else [],
            "ground_bloch_drift": bloch_drift,
            "ground_dphi_max_track": max(dphi_tail) if dphi_tail else dphi_core,
            "su2_dot_2pi": dot_2pi,
            "su2_dot_4pi": dot_4pi,
            "su2_monodromy_ok": su2_ok,
            "ground_ok": ground_ok,
            "n_E_excitation_sim_open": True,
            "checks_ok": algebra_ok and ground_ok and su2_ok,
            "derivation_closed": False,
            "note": (
                "§5.0.4-A: algebra landmarks on Z_512 + vortex ground + SU(2) 2π/4π on core. "
                "n_E≥1 excitation sim still open."
            ),
        }
