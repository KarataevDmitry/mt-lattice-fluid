"""§5.0.4-A — Γ_V orbit table + ground/excited branches under free g (one V_P)."""
from __future__ import annotations

from typing import Any

from mt_ca.local_balance import balance_step_probe, momentum_density, n_E_field
from mt_ca.matter_survey import plane_mconfig, spinor_plane
from mt_ca.projected_collision import projected_phi_int
from mt_ca.reversible import canonical_fixed
from mt_ca.spinor import bloch_vector
from mt_ca.topology import matter_occupancy_b, winding_channels


def _phi_int_at(phi: torch.Tensor, site) -> torch.Tensor:
    if phi.ndim == 2:
        return phi[site.y, site.x]
    iz = site.iz if site.iz is not None else 0
    return phi[iz, site.y, site.x]


def _gamma_key(sample: tuple) -> tuple:
    """Same 8-component key as ``track_gamma_points`` (excludes density)."""
    return sample[:8]


def _sample_core_tick(
    sim,
    *,
    site,
    n_ring: int,
    p0_nat: float,
    winding_min: float,
) -> tuple | None:
    z = sim.z
    z_past = sim.z_past.clone() if sim.z_past is not None else z.clone()
    cfg = sim.cfg
    plane = spinor_plane(z, site)
    zpp = spinor_plane(z_past, site)
    y, x = site.y, site.x
    f = canonical_fixed(z, cfg)
    phi = projected_phi_int(f, cfg)
    phi_ticks = int(_phi_int_at(phi, site).round().item()) % n_ring
    from mt_ca.si_constants import internal_phase_decode

    k_phi, phi_f = internal_phase_decode(phi_ticks)
    n_e = int(n_E_field(phi, cfg)[y, x].item()) if phi.ndim == 2 else int(
        n_E_field(phi, cfg)[site.iz or 0, y, x].item()
    )
    plane_cfg = plane_mconfig(plane, cfg)
    bv = bloch_vector(plane[y : y + 1, x : x + 1])[0, 0]
    bloch_key = tuple(round(float(bv[i].item()), 3) for i in range(3))
    px, py = momentum_density(plane)
    pi_x = int(round(float(px[y, x].item()) / p0_nat))
    pi_y = int(round(float(py[y, x].item()) / p0_nat))
    impulse = int(balance_step_probe(plane, zpp, plane_cfg)["phi"][y, x].item())
    b_core = int(matter_occupancy_b(z, y=y, x=x, iz=site.iz))
    w_abs = abs(float(winding_channels(plane, center=(y, x), radius=2)["auto"]))
    if b_core != 1 or w_abs < winding_min:
        return None
    return (phi_ticks, k_phi, phi_f, n_e, impulse, pi_x, pi_y, bloch_key)


def build_gamma_orbit_table(
    sim,
    *,
    site,
    track: int,
    n_ring: int,
    p0_nat: float,
    winding_min: float = 0.75,
) -> dict[str, Any]:
    """Collect planckon-core Γ samples over ``track`` ticks; partition branches by n_E."""
    rows: list[dict[str, Any]] = []
    agg: dict[tuple, dict[str, Any]] = {}

    sample = _sample_core_tick(
        sim, site=site, n_ring=n_ring, p0_nat=p0_nat, winding_min=winding_min
    )
    if sample is not None:
        key = _gamma_key(sample)
        agg[key] = {
            "ticks": 1,
            "n_E_min": sample[3],
            "n_E_max": sample[3],
            "phi_impulse_min": sample[4],
            "phi_impulse_max": sample[4],
        }

    for _ in range(track):
        sim.step(1)
        sample = _sample_core_tick(
            sim, site=site, n_ring=n_ring, p0_nat=p0_nat, winding_min=winding_min
        )
        if sample is None:
            continue
        key = _gamma_key(sample)
        n_e = sample[3]
        imp = sample[4]
        if key not in agg:
            agg[key] = {
                "ticks": 0,
                "n_E_min": n_e,
                "n_E_max": n_e,
                "phi_impulse_min": imp,
                "phi_impulse_max": imp,
            }
        rec = agg[key]
        rec["ticks"] += 1
        rec["n_E_min"] = min(rec["n_E_min"], n_e)
        rec["n_E_max"] = max(rec["n_E_max"], n_e)
        rec["phi_impulse_min"] = min(rec["phi_impulse_min"], imp)
        rec["phi_impulse_max"] = max(rec["phi_impulse_max"], imp)

    for key, rec in sorted(agg.items(), key=lambda kv: (kv[0][0], kv[0][3], kv[0][7])):
        branch = "excited" if rec["n_E_max"] >= 1 else "ground"
        rows.append(
            {
                "branch": branch,
                "phi_disc": key[0],
                "k_phi": key[1],
                "phi_f": key[2],
                "n_E": key[3],
                "phi_impulse": key[4],
                "pi_p0": [key[5], key[6]],
                "bloch": list(key[7]),
                "visit_ticks": rec["ticks"],
                "n_E_range": [rec["n_E_min"], rec["n_E_max"]],
            }
        )

    ground = [r for r in rows if r["branch"] == "ground"]
    excited = [r for r in rows if r["branch"] == "excited"]
    n_e_excited = sorted({r["n_E"] for r in excited if r["n_E"] >= 1})

    return {
        "table_rows": rows,
        "orbit_unique": len(rows),
        "ground_branch_rows": len(ground),
        "excited_branch_rows": len(excited),
        "excited_n_E_values": n_e_excited,
        "planckon_ticks_sampled": track + 1,
    }


def summarize_gamma_branches(table: dict[str, Any], *, cap: int) -> dict[str, Any]:
    orbit = int(table["orbit_unique"])
    ground_n = int(table["ground_branch_rows"])
    excited_n = int(table["excited_branch_rows"])
    excited_n_e = table["excited_n_E_values"]
    ok = (
        orbit >= 2
        and ground_n >= 1
        and excited_n >= 1
        and len(excited_n_e) >= 1
        and max(excited_n_e) >= 1
        and orbit <= cap
    )
    return {
        "orbit_unique": orbit,
        "ground_branch_rows": ground_n,
        "excited_branch_rows": excited_n,
        "excited_n_E_values": excited_n_e,
        "orbit_within_cap": orbit <= cap,
        "checks_ok": ok,
    }
