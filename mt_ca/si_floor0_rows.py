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

        Habitat: VACUUM_BOIL (every hV filled, A5 boil). Planckon = VORTEX_P on that ocean.
        Sim: track Γ samples at planckon core and at a bath brick under ongoing g.
        """
        from mt_ca.config import MConfig
        from mt_ca.ledger import ledger_step_probe, momentum_density, n_E_field
        from mt_ca.metrics import field_amplitude
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
            {"id": "pi_p0", "states": -1, "note": "π/p₀ integer; width open-bound"},
        ]
        naive_gamma = n_ring * int(bb.N_phi) * dphi_disc * _BLOCH_DISTINCT_Q6 * n_ring * n_e_classes

        dev = torch.device(device)
        cfg = MConfig.for_stencil("hex")
        cy = cx = size // 2
        by = bx = 10
        sim = LatticeFluidSimulator(size, size, cfg, device=dev)
        sim.reset(SeedClass.VORTEX_P)
        amp0 = float(field_amplitude(sim.z).max().item())
        for _ in range(settle):
            sim.step(1)
        amp_settled = float(field_amplitude(sim.z).max().item())

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
        core_samples: list[tuple] = [_sample(z, z_past, cy, cx)]
        bath_samples: list[tuple] = [_sample(z, z_past, by, bx)]
        for _ in range(track):
            z_past = z.clone()
            sim.step(1)
            z = sim.z
            core_samples.append(_sample(z, z_past, cy, cx))
            bath_samples.append(_sample(z, z_past, by, bx))

        core = _summarize(core_samples)
        bath = _summarize(bath_samples)
        ocean_moves = amp_settled > amp0 * 1.01 or core["unique_points"] > 1

        return {
            "habitat": "VACUUM_BOIL",
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
        Sim habitat: VACUUM_BOIL + VORTEX_P (filled lattice, A5 boil, no void).
        Snapshot: planckon at core b=1, |n|≥¾; SU(2) 2π/4π on core spinor.
        Under boil, core Γ drifts (not dead-ocean fixed point).

        Open (explicit): n_E≥1 kick-harness on boiling floor.
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
        phi = saturating_phase(z, cfg)
        n_e = n_E_field(phi, cfg)
        ch = winding_channels(z, center=(cy, cx), radius=2)
        b_core = matter_occupancy_b(z, y=cy, x=cx)
        dphi_core = float(arg_phase_defect(z, cfg, apply_floor=False)[cy, cx].abs().item())
        phi_core = float(phi[cy, cx].abs().item())
        n_e_core = int(n_e[cy, cx].item())

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
        su2_ok = dot_2pi < -0.9 and dot_4pi > 0.9

        snapshot_ok = (
            b_core == 1
            and abs(float(ch["auto"])) >= 0.75
            and n_e_core == 0
        )

        b_hits = 0
        w_abs: list[float] = []
        bloch_tail: list[list[float]] = []
        for _ in range(track):
            sim.step(1)
            z = sim.z
            if matter_occupancy_b(z, y=cy, x=cx) == 1:
                b_hits += 1
            w_abs.append(abs(float(winding_channels(z, center=(cy, cx), radius=2)["auto"])))
            bv = bloch_vector(z[cy : cy + 1, cx : cx + 1])[0, 0]
            bloch_tail.append([float(bv[i].item()) for i in range(3)])

        b_core_rate = b_hits / max(track, 1)
        w_mean = sum(w_abs) / len(w_abs) if w_abs else 0.0
        bloch_drift = 0.0
        if len(bloch_tail) >= 2:
            bloch_drift = max(
                abs(bloch_tail[-1][i] - bloch_tail[-2][i]) for i in range(3)
            )

        ground_ok = snapshot_ok and su2_ok and b_core_rate >= 0.15 and w_mean >= 0.5

        return {
            "habitat": "VACUUM_BOIL",
            "N_ring": n_ring,
            "N_phi": int(bb.N_phi),
            "B_hV": float(bb.B_hV),
            "delta_phi_min_disc": dphi_disc,
            "delta_phi_min_rad": float(eq["delta_phi_min_rad"]),
            "pauli_kick_disc": pauli_disc,
            "ticks_per_E0": ticks_per_e0,
            "landmarks": landmarks,
            "algebra_ok": algebra_ok,
            "ground_b_core": b_core,
            "ground_winding_auto": float(ch["auto"]),
            "ground_dphi_core": dphi_core,
            "ground_phi_ticks_core": phi_core,
            "ground_n_E_core": n_e_core,
            "ground_bloch": bloch_tail[-1] if bloch_tail else [],
            "ground_bloch_drift": bloch_drift,
            "planckon_b_core_rate": b_core_rate,
            "planckon_winding_mean_abs": w_mean,
            "su2_dot_2pi": dot_2pi,
            "su2_dot_4pi": dot_4pi,
            "su2_monodromy_ok": su2_ok,
            "snapshot_ok": snapshot_ok,
            "ground_ok": ground_ok,
            "n_E_excitation_sim_open": True,
            "checks_ok": algebra_ok and ground_ok and su2_ok,
            "derivation_closed": False,
            "note": (
                "§5.0.4-A: algebra + planckon on boiling ocean; SU(2) 2π/4π at settle. "
                "n_E≥1 kick-harness still open."
            ),
        }
