"""verify_checks.floor0 — §5.0.4-A planckon internal spectrum."""
from __future__ import annotations


def check_brick_internal_spectrum(device: str = "cpu") -> dict:
    """§5.0.4-A — internal ring landmarks + vortex ground + SU(2) monodromy."""
    from mt_ca.si_constants import SI

    row = SI.brick_internal_spectrum_row(device=device)
    ok = (
        bool(row["checks_ok"])
        and bool(row["algebra_ok"])
        and bool(row["ground_ok"])
        and bool(row["su2_monodromy_ok"])
        and not bool(row["derivation_closed"])
        and int(row["N_ring"]) == 512
        and int(row["delta_phi_min_disc"]) == 41
        and int(row["pauli_kick_disc"]) == 256
    )
    return {
        "id": "Brick_internal_spectrum",
        "ok": ok,
        "algebra_ok": row["algebra_ok"],
        "ground_ok": row["ground_ok"],
        "su2_monodromy_ok": row["su2_monodromy_ok"],
        "ground_winding": row["ground_winding_auto"],
        "ground_dphi_core": row["ground_dphi_core"],
        "su2_dot_2pi": row["su2_dot_2pi"],
        "su2_dot_4pi": row["su2_dot_4pi"],
        "landmark_ids": [r["id"] for r in row["landmarks"]],
        "n_E_excitation_sim_open": row["n_E_excitation_sim_open"],
        "note": row["note"],
    }
