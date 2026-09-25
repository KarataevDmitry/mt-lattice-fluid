"""SIFloor0Rows — §5.0.4-A internal planckon spectrum (one v_p, floor 0)."""
from __future__ import annotations

import math

import torch


# Q(frac_bits=6) grid: distinct Bloch directions after decode_spinor (probe 2026-09).
_BLOCH_DISTINCT_Q6 = 2_967_474


class SIFloor0Rows:
    """Ask/row probes for floor-0 planckon internal spectrum."""

    def internal_state_catalog_row(self) -> dict[str, float | int | str | bool | list]:
        """§5.0.4-A — structure of the finite internal-state catalog (one hV).

        Algebra tier (closed): phase ring Z_512, (k_phi, phi_f) bijection, n_E ladder.
        Amplitude tier: mu in Z_{2^frac_bits}; spinor orientation = Bloch on S^2.
        Bekenstein cap 2^B_hV binds total distinguishable cell states — registers are
        not independent (naive product >> cap).
        """
        from mt_ca.si_constants import (
            elementary_quanta_row,
            hv_bit_budget,
            internal_phase_coords_row,
        )

        bb = hv_bit_budget()
        ipc = internal_phase_coords_row()
        eq = elementary_quanta_row()
        ticks = int(eq["energy_ticks_per_E0"])
        n_e_max = int(bb.N_ring) // ticks
        n_e_classes = n_e_max + 1
        amp_levels = 1 << int(bb.frac_bits)
        q_configs = amp_levels**4 - 1
        phase_states = int(bb.N_ring)
        cap = int(round(bb.n_states))
        bloch = _BLOCH_DISTINCT_Q6
        naive_phase_n_e = phase_states * n_e_classes
        naive_phase_bloch = phase_states * bloch
        tiers: list[dict[str, str | int]] = [
            {
                "id": "landmarks",
                "status": "closed",
                "count": 4,
                "note": "E0_1, E0_2, pauli_pi, ring_2pi on Z_512",
            },
            {
                "id": "phase_ring",
                "status": "closed",
                "count": phase_states,
                "note": "phi_disc bijection (k_phi, phi_f); seam=21 ticks",
            },
            {
                "id": "n_E_ladder",
                "status": "closed_algebra",
                "count": n_e_classes,
                "note": f"n_E=0..{n_e_max} from floor(|Phi|/{ticks})",
            },
            {
                "id": "amplitude_mu",
                "status": "closed_width",
                "count": amp_levels,
                "note": "Q(2^-frac_bits) per spinor lane",
            },
            {
                "id": "bloch_orientation",
                "status": "partial",
                "count": bloch,
                "note": "distinct Bloch directions on Q6 grid (not full orbit catalog)",
            },
            {
                "id": "bekenstein_cap",
                "status": "closed_bound",
                "count": cap,
                "note": "2^B_hV upper bound on distinguishable hV states",
            },
        ]
        cap_binds = cap < bloch and cap < naive_phase_n_e
        return {
            "phase_states": phase_states,
            "k_phi_sectors": int(ipc["N_phi"]),
            "phi_f_steps": int(ipc["delta_phi_disc"]),
            "seam_ticks": int(ipc["seam_ticks"]),
            "n_E_max": n_e_max,
            "n_E_classes": n_e_classes,
            "amplitude_levels": amp_levels,
            "q_grid_spinor_configs": q_configs,
            "bloch_distinct_q6": bloch,
            "bekenstein_cap_states": cap,
            "naive_phase_times_n_E": naive_phase_n_e,
            "naive_phase_times_bloch": naive_phase_bloch,
            "cap_binds_registers": cap_binds,
            "tiers": tiers,
            "full_table_open": True,
            "checks_ok": (
                phase_states == 512
                and n_e_classes == 13
                and int(ipc["seam_ticks"]) == 21
                and ipc["canonical_bijection_ok"]
                and cap_binds
            ),
            "note": (
                "§5.0.4-A catalog probe: algebra closed; Bloch count on Q6 pinned; "
                "full state list + g iterations still open."
            ),
        }

    def floor0_phase_space_row(
        self,
        *,
        size: int = 64,
        settle: int = 64,
        track: int = 32,
        device: str = "cpu",
    ) -> dict[str, float | int | str | bool | list]:
        """§5.0.4-A — discrete phase space Γ_hV for one planckon (native q, p).

        Configuration q (generalized coords on one hV, x fixed at floor 0):
          φ_disc ∈ ℤ_{N_ring}, canonical (k_φ, φ_f), Bloch orientation, |z|².
        Momentum p (conjugate ledger, dh=dt=1 natural):
          Φ kick per tick (ℤ_{N_ring} ticks, Heisenberg floor), n_E, π/p₀ at core.

        Sim: VORTEX_P ground → one fixed point in Γ under g (iteration stable).
        """
        from mt_ca.config import MConfig
        from mt_ca.ledger import ledger_step_probe, momentum_density, n_E_field
        from mt_ca.seeds import SeedClass
        from mt_ca.simulator import LatticeFluidSimulator
        from mt_ca.si_constants import (
            elementary_quanta_row,
            hv_bit_budget,
            internal_phase_decode,
            kappa_link,
        )
        from mt_ca.spinor import bloch_vector, spinor_density, saturating_phase

        bb = hv_bit_budget()
        eq = elementary_quanta_row()
        n_ring = int(eq["N_ring"])
        dphi_disc = int(eq["delta_phi_min_disc"])
        ticks_per_e0 = int(eq["energy_ticks_per_E0"])
        n_e_classes = n_ring // ticks_per_e0 + 1
        p0_nat = float(kappa_link())
        cap = int(round(bb.n_states))

        q_axes: list[dict[str, int | str]] = [
            {"id": "phi_disc", "states": n_ring, "note": "ring position mod N_ring"},
            {"id": "k_phi", "states": int(bb.N_phi), "note": "Heisenberg sector"},
            {"id": "phi_f", "states": dphi_disc, "note": "fine phase in sector"},
            {"id": "bloch", "states": _BLOCH_DISTINCT_Q6, "note": "Q(frac_bits) orientation classes"},
        ]
        p_axes: list[dict[str, int | str]] = [
            {"id": "Phi_kick", "states": n_ring, "note": "kick ticks per dt; 0 or |Φ|≥Δφ_disc"},
            {"id": "n_E", "states": n_e_classes, "note": "E₀ ledger from |Φ|"},
            {"id": "pi_p0", "states": -1, "note": "π/p₀ integer at core; width open-bound"},
        ]
        naive_q = n_ring * int(bb.N_phi) * dphi_disc * _BLOCH_DISTINCT_Q6
        naive_p = n_ring * n_e_classes
        naive_gamma = naive_q * naive_p

        dev = torch.device(device)
        cfg = MConfig.for_stencil("hex")
        cy = cx = size // 2
        sim = LatticeFluidSimulator(size, size, cfg, device=dev)
        sim.reset(SeedClass.VORTEX_P)
        for _ in range(settle):
            sim.step(1)

        def _sample(z: torch.Tensor, z_past: torch.Tensor) -> tuple:
            phi = saturating_phase(z, cfg)
            phi_ticks = int(phi[cy, cx].round().item()) % n_ring
            k_phi, phi_f = internal_phase_decode(phi_ticks)
            n_e = int(n_E_field(phi, cfg)[cy, cx].item())
            bv = bloch_vector(z[cy : cy + 1, cx : cx + 1])[0, 0]
            bloch_key = tuple(round(float(bv[i].item()), 3) for i in range(3))
            rho = float(spinor_density(z[cy : cy + 1, cx : cx + 1])[0, 0].item())
            px, py = momentum_density(z)
            pi_x = int(round(float(px[cy, cx].item()) / p0_nat))
            pi_y = int(round(float(py[cy, cx].item()) / p0_nat))
            kick = int(ledger_step_probe(z, z_past, cfg)["phi"][cy, cx].item())
            return (phi_ticks, k_phi, phi_f, n_e, kick, pi_x, pi_y, bloch_key, round(rho, 4))

        z = sim.z
        z_past = sim.z_past.clone() if sim.z_past is not None else z.clone()
        samples: list[tuple] = [_sample(z, z_past)]
        for _ in range(track):
            z_past = z.clone()
            sim.step(1)
            z = sim.z
            samples.append(_sample(z, z_past))

        unique = {s[:8] for s in samples}
        ground = samples[-1]
        ground_fixed = len(unique) == 1
        ground_n_e_zero = ground[3] == 0
        ground_kick_zero = ground[4] == 0

        return {
            "p0_natural": p0_nat,
            "N_ring": n_ring,
            "delta_phi_disc": dphi_disc,
            "n_E_classes": n_e_classes,
            "bekenstein_cap_states": cap,
            "q_axes": q_axes,
            "p_axes": p_axes,
            "naive_q_times_p": naive_gamma,
            "cap_below_naive_gamma": cap < naive_gamma,
            "ground_phi_disc": ground[0],
            "ground_k_phi": ground[1],
            "ground_phi_f": ground[2],
            "ground_n_E": ground[3],
            "ground_Phi_kick": ground[4],
            "ground_pi_p0_x": ground[5],
            "ground_pi_p0_y": ground[6],
            "ground_bloch": list(ground[7]),
            "ground_rho": ground[8],
            "iteration_unique_points": len(unique),
            "iteration_ticks": track + 1,
            "ground_fixed_point": ground_fixed,
            "ground_n_E_zero": ground_n_e_zero,
            "ground_kick_zero": ground_kick_zero,
            "checks_ok": (
                ground_fixed
                and ground_n_e_zero
                and ground_kick_zero
                and cap < naive_gamma
                and abs(p0_nat - 0.25) < 1e-9
            ),
            "derivation_closed": False,
            "note": (
                "§5.0.4-A: native (q,p) phase space Γ_hV; vortex ground is g-fixed point. "
                "Full Γ enumeration + excited branches still open."
            ),
        }

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
            saturating_phase,
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
        phi = saturating_phase(z, cfg)
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
