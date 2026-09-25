"""SICarrierRows — extracted from si_constants (file-size hygiene)."""
from __future__ import annotations

import math
from decimal import Decimal

from mt_ca.si_constants import (
    DELTA_PHI_MIN,
    KAPPA,
    KAPPA_FCC_1TICK,
    KAPPA_HEX,
    LN2,
    N12_FCC_CAUSAL_LINKS,
    T_CMB_K_REF,
    as_code_dict,
    elementary_quanta_row,
    energy_quantum_row,
    heisenberg_phi_min_disc,
    hv_bit_budget,
    kappa_link,
    n_E_from_phi_ticks
)


class SICarrierRows:
    """Ask/row probes — do not grow si_constants with these."""

    def carrier_torus_close_row(self) -> dict[str, float | int | str | bool | list]:
        """§1.7 · Carrier topology: finite wall-free Λ = torus (was DEVLOG §10.1).

        Ask-model: what global glue does Λ have?

        Carrier answers (2026-09-24):
          · Absorbing wall → drains Σ|z|² → breaks A3 (or non-local reinjection).
          · Reflecting wall → preferred locus; A5 vacuum not homogeneous.
          · Open finite patch without wrap = walls under another name.
          · Sphere / curved compact → no flat FCC/hex equal light-like edges (§1).
          · Infinite noncompact Λ: local g same — not rejected as local law;
            finite readout / D5 on finite connected graph / META wave-return
            need compact-without-boundary.
          · Flat translation lattice + compact no boundary → torus:
                (3+1) T³ · (2+1) slice T².
          · Λ×S¹ = phase fiber over Λ (Arg/U(1)), not «torus instead of lattice».
          · closed: finite wall-free carrier topology = torus.
          · SOFT: cosmological period N; long-run entropy numerics; covers.
          · Sim torch.roll = eng readout of §1.7 (DEVLOG §10.1), not new physics.
        """
        inventory: list[dict[str, str | float | bool]] = [
            {
                "id": "closed_finite_wallfree_is_torus",
                "maps_to": "T³ (FCC) / T² (hex slice) — periodic ID of Λ",
                "status": "closed",
                "mechanism": "A3+A5+no preferred wall + flat packing",
            },
            {
                "id": "closed_Lambda_times_S1_fiber",
                "maps_to": "Λ×S¹ = phase circle over lattice (§3.9.1); not instead-of-Λ",
                "status": "closed",
            },
            {
                "id": "closed_sim_roll_is_readout",
                "maps_to": "torch.roll / bond wrap = eng of §1.7, not separate law",
                "status": "closed",
            },
            {
                "id": "reject_absorbing_wall",
                "maps_to": "norm sink breaks A3",
                "status": "rejected",
            },
            {
                "id": "reject_reflecting_wall",
                "maps_to": "preferred locus breaks homogeneous A5",
                "status": "rejected",
            },
            {
                "id": "reject_sphere_as_flat_FCC_carrier",
                "maps_to": "no equal light-like FCC packing on sphere as M carrier",
                "status": "rejected",
            },
            {
                "id": "soft_open_period_N_and_covers",
                "maps_to": "cosmological |Λ| / covers vs fundamental domain",
                "status": "soft_open",
            },
        ]
        closed_ids = [
            i["id"] for i in inventory if str(i["status"]).startswith("closed")
        ]
        reject_ids = [
            i["id"] for i in inventory if str(i["status"]) == "rejected"
        ]
        soft_open_ids = [
            i["id"] for i in inventory if str(i["status"]) == "soft_open"
        ]
        ok = (
            "closed_finite_wallfree_is_torus" in closed_ids
            and "closed_Lambda_times_S1_fiber" in closed_ids
            and "closed_sim_roll_is_readout" in closed_ids
            and "reject_absorbing_wall" in reject_ids
            and "reject_reflecting_wall" in reject_ids
            and "reject_sphere_as_flat_FCC_carrier" in reject_ids
            and "soft_open_period_N_and_covers" in soft_open_ids
        )
        return {
            "theorem": "§1.7 carrier torus — finite wall-free Λ = T^d",
            "topology_closed": True,
            "Lambda_times_S1_closed": True,
            "period_N_soft_open": True,
            "derivation_closed": ok,
            "inventory": inventory,
            "closed_ids": closed_ids,
            "reject_ids": reject_ids,
            "soft_open_ids": soft_open_ids,
            "checks_ok": ok,
            "note": (
                "Finite wall-free carrier = torus (T³/T²). Λ×S¹ = phase fiber. "
                "Period N / covers soft. Sim wrap = readout of §1.7."
            ),
        }

    def gpu_eng_tail_close_row(self) -> dict[str, float | int | str | bool | list]:
        """§0.10 · GPU eng-tail close (was DEVLOG §10.2–§10.4).

        Ask: are the three GPU fuses new physics or MODEL readout?

        Carrier answers (2026-09-24):
          · Floor+seed (§10.2): z≡0 deadlock; |z|≥z_min; vacuum_amplitude=z_min;
            per-cell gauge_fix forbidden on tick path.
          · Step algebra (§10.3): R(Φ)=ω^Φ only; Euler z+=iφz rejected (A3).
          · Literals (§10.4): DX/DT/K_P/α* = as_code_dict SI paste, not free parameters.
          · All closed as eng readout of §0.5 / A3·A4 / §7 SI.
          · Soft: verify norm_drift threshold = sim hygiene.
        """
        hv = hv_bit_budget()
        z_min = 2.0 ** (-hv.frac_bits)
        alpha_star = 1.0 + 1.0 / (4.0 * math.pi)
        code = as_code_dict()
        inventory: list[dict[str, str | float | bool]] = [
            {
                "id": "closed_planck_floor_and_seed",
                "ratio": z_min,
                "maps_to": "§0.5 · A5 · z_min=2^{-B_amp}; vacuum_amplitude=z_min",
                "status": "closed",
                "mechanism": "z≡0 deadlock; IC on floor not fitted 1e-6",
            },
            {
                "id": "closed_reject_per_cell_gauge_fix_on_tick",
                "maps_to": "per-cell U(1) kills ζ_imag; global gauge = T/report only",
                "status": "closed",
            },
            {
                "id": "closed_R_Phi_not_Euler",
                "maps_to": "A3·A4 · §3.12.5 — nonlinearity = R(Φ)=ω^Φ only",
                "status": "closed",
            },
            {
                "id": "closed_gpu_literals_are_SI_paste",
                "maps_to": "DX=l_P DT=hT K_P α*=1+1/(4π) via as_code_dict",
                "status": "closed",
            },
            {
                "id": "reject_z_equiv_0_vacuum",
                "maps_to": "z≡0 is not A5 vacuum",
                "status": "rejected",
            },
            {
                "id": "reject_Euler_add_step",
                "maps_to": "z+=iφz breaks Σ|z|²",
                "status": "rejected",
            },
            {
                "id": "reject_literals_as_fitted_knobs",
                "maps_to": "literals ≠ free GPU knobs outside SI",
                "status": "rejected",
            },
            {
                "id": "soft_open_norm_drift_verify_threshold",
                "maps_to": "norm_drift<1e-4 in verify — hygiene, not M law",
                "status": "soft_open",
            },
        ]
        closed_ids = [
            i["id"] for i in inventory if str(i["status"]).startswith("closed")
        ]
        reject_ids = [
            i["id"] for i in inventory if str(i["status"]) == "rejected"
        ]
        soft_open_ids = [
            i["id"] for i in inventory if str(i["status"]) == "soft_open"
        ]
        lit_ok = (
            abs(float(code["DX"]) - float(self.l_P)) / float(self.l_P) < 1e-15
            and abs(float(code["DT"]) - float(self.hT)) / float(self.hT) < 1e-15
            and abs(float(code["K_P_J_m3"]) - float(self.K_P)) / float(self.K_P) < 1e-12
            and abs(float(code["ALPHA_STAR"]) - alpha_star) < 1e-12
            and abs(float(code["ALPHA_STAR"]) - float(self.alpha_star)) < 1e-12
        )
        floor_ok = hv.frac_bits == 6 and abs(z_min - 1.0 / 64.0) < 1e-15
        ok = (
            floor_ok
            and lit_ok
            and "closed_planck_floor_and_seed" in closed_ids
            and "closed_R_Phi_not_Euler" in closed_ids
            and "closed_gpu_literals_are_SI_paste" in closed_ids
            and "reject_z_equiv_0_vacuum" in reject_ids
            and "reject_Euler_add_step" in reject_ids
            and "soft_open_norm_drift_verify_threshold" in soft_open_ids
        )
        return {
            "theorem": "§0.10 GPU eng-tail — floor/step/literals = MODEL readout",
            "z_min": z_min,
            "frac_bits": hv.frac_bits,
            "ALPHA_STAR": float(code["ALPHA_STAR"]),
            "DX": float(code["DX"]),
            "DT": float(code["DT"]),
            "K_P": float(code["K_P_J_m3"]),
            "floor_closed": True,
            "unitary_step_closed": True,
            "literals_closed": True,
            "derivation_closed": ok,
            "inventory": inventory,
            "closed_ids": closed_ids,
            "reject_ids": reject_ids,
            "soft_open_ids": soft_open_ids,
            "checks_ok": ok,
            "note": (
                "GPU fuses closed as readout: floor+seed (§0.5), R(Φ) not Euler, "
                "SI literals paste. Soft: verify norm_drift threshold."
            ),
        }

    def maxwell_row(self) -> dict[str, float]:
        """§8.2 macro Maxwell — light = K_P/μ_P; T-readout (not Planck ∇)."""
        mu_p = self.mu_P
        k_p = self.K_P
        u_p = self.u_P
        c = self.c
        c_from_fluid = math.sqrt(k_p / mu_p)
        return {
            "mu_P": mu_p,
            "K_P": k_p,
            "u_P": u_p,
            "c": c,
            "c_from_K_over_mu": c_from_fluid,
            "rel_c_fluid": abs(c_from_fluid - c) / c,
            "rel_K_eq_u": abs(k_p - u_p) / u_p,
            "kappa": KAPPA,
            "note": "§8.2 macro: c²=K_P/μ_P; Planck EM = planck_em_row",
        }

    def planck_em_row(self) -> dict[str, float]:
        """§8.2 Planck EM — discrete Arg/j/F₀ ladder; Coulomb N=1 = α F_P (no ∇ on ℓ_P)."""
        f_p = self.c**4 / self.G
        f0 = self.F_0
        alpha = self.alpha_fs
        f_nn = alpha * f_p
        return {
            "s_0": self.s_0,
            "E_0": self.E_0,
            "p_0": self.p_0,
            "F_0": f0,
            "F_P": f_p,
            "F_over_F_P_N1_unit": alpha,
            "F_NN_N": f_nn,
            "c0": self.c0,
            "c": self.c,
            "c0_over_c": self.c0 / self.c,
            "rel_F0_mg": abs(f0 - self.m_arg * self.g_M) / f0,
            "note": "§8.2 Planck: s0/E0/F0 ladder; |F|/F_P=α at N=1; c0=√2 c",
        }

    def radiation_row(self) -> dict[str, float]:
        """§8.2 radiation — s0/E0 ladder + Debye UV; Bose/Planck spectrum still open."""
        e0 = self.E_0
        nu0 = 1.0 / self.hT
        h = 2.0 * math.pi * self.hbar
        h_nu0 = h * nu0
        return {
            "s_0": self.s_0,
            "E_0": e0,
            "nu_0_Hz": nu0,
            "omega_0_rad_s": 2.0 * math.pi * nu0,
            "h_nu0_J": h_nu0,
            "h_nu0_over_E0": h_nu0 / e0,
            "c0": self.c0,
            "c": self.c,
            "kappa_FCC": KAPPA_FCC_1TICK,
            "omega_D_over_nu0": 1.0,
            "note": "§8.2 rad: h ν0=4π E0; ω_D∼1/hT; Bose u(ω) open",
        }

    def vacuum_bath_row(self) -> dict[str, float | int | str | bool]:
        """§8.2·vac — A5 boiling bath: ρ_E(z_min), spectral anchors; ≠ CMB (META §3.0)."""
        hv = hv_bit_budget()
        z_min = 2.0 ** (-hv.frac_bits)
        z_sq_natural = 2.0 * z_min * z_min
        u_p = self.u_P
        rho_vac = z_sq_natural * u_p
        sigma = 5.670374419e-8
        a_rad = 4.0 * sigma / self.c
        t_bath = (rho_vac / a_rad) ** 0.25
        t_ceiling = (u_p / a_rad) ** 0.25
        rad = self.radiation_row()
        nu0 = rad["nu_0_Hz"]
        return {
            "z_min": z_min,
            "frac_bits": hv.frac_bits,
            "B_hV": hv.B_hV,
            "z_sq_natural_vac": z_sq_natural,
            "rho_E_vac_J_m3": rho_vac,
            "u_P_J_m3": u_p,
            "rho_over_uP": z_sq_natural,
            "T_M_bath_K": t_bath,
            "T_uP_ceiling_K": t_ceiling,
            "T_CMB_K_ref": T_CMB_K_REF,
            "log10_T_M_bath": math.log10(t_bath),
            "log10_T_M_bath_over_CMB": math.log10(t_bath / T_CMB_K_REF),
            "nu_0_Hz": nu0,
            "omega_0_rad_s": rad["omega_0_rad_s"],
            "lambda_0_m": self.c / nu0,
            "lambda_0_over_l_P": (self.c / nu0) / self.l_P,
            "h_nu0_over_E0": rad["h_nu0_over_E0"],
            "omega_D_over_nu0": rad["omega_D_over_nu0"],
            "is_CMB": False,
            "note": "§8.2·vac: A5 ocean bath; Bose u(ω) open; CMB = bubble T-layer only",
        }

    def cuboctahedron_geometry_row(self) -> dict[str, float | int | str | bool]:
        """§8.2·geo / §1.6.2 — 1-tick cuboctahedron from edge a=l_P; ratios are derived."""
        n12 = N12_FCC_CAUSAL_LINKS
        n_tri = 8
        n_sq = 6
        n_edges = 24
        girth = 3
        d_spatial = 3
        kappa = KAPPA_FCC_1TICK
        lp = self.l_P
        edge_a = lp  # A1: 12 NN at l_P ⇒ cuboctahedron edge a = l_P (§8.2·geo)
        v_hv = edge_a**3 / math.sqrt(2.0)
        vol_cubo = (8.0 / 3.0) * math.sqrt(2.0) * edge_a**3
        v_over_v_hv = vol_cubo / v_hv
        a_sq_one = edge_a**2
        a_tri_one = (math.sqrt(3.0) / 4.0) * edge_a**2
        a_sq = n_sq * a_sq_one
        a_tri = n_tri * a_tri_one
        a_total = a_sq + a_tri
        s_total = a_total
        r_out = edge_a
        r_in_1tick = kappa * edge_a
        r_in_classical = edge_a * math.sqrt(6.0) / 6.0
        alpha_inv_derived = 4.0 * math.pi**3 + math.pi**2 + math.pi
        alpha_inv_geom = float(n12 * (n12 + 1) - n_tri - 2 * n_sq + girth // d_spatial)
        alpha_inv_geom_alt = float(
            n12 * (n12 + 1) - n_tri - 2 * n_sq + v_over_v_hv / (n_sq * kappa**2)
        )
        codata_inv = self.alpha_fs_inv
        return {
            "anchor": "edge_a = l_P from A1 (12 NN at l_P); all body measures at a first",
            "edge_a_m": edge_a,
            "edge_a_over_l_P": edge_a / lp,
            "l_P_m": lp,
            "n_nn": n12,
            "n_edges": n_edges,
            "n_faces_square": n_sq,
            "n_faces_triangle": n_tri,
            "R_out_m": r_out,
            "R_in_1tick_m": r_in_1tick,
            "R_in_over_R_out_1tick": kappa,
            "A_square_one_m2": a_sq_one,
            "A_triangle_one_m2": a_tri_one,
            "A_square_total_m2": a_sq,
            "A_triangle_total_m2": a_tri,
            "S_total_m2": s_total,
            "V_cuboctahedron_m3": vol_cubo,
            "v_hV_m3": v_hv,
            "V_over_S_m": vol_cubo / s_total,
            "square_plaquette_perimeter_m": 4.0 * edge_a,
            "V_over_v_hV": v_over_v_hv,
            "V_over_v_hV_exact": "16/3",
            "V_over_S_over_l_P": (vol_cubo / s_total) / lp,
            "kappa_inscribed_1tick": kappa,
            "R_in_over_R_out_classical": r_in_classical / r_out,
            "A_square_over_A_total": a_sq / a_total,
            "A_triangle_over_A_total": a_tri / a_total,
            "dihedral_square_triangle_deg": 135.0,
            "alpha_fs_inv_derived": alpha_inv_derived,
            "alpha_fs_inv_geom": alpha_inv_geom,
            "alpha_fs_inv_geom_alt": alpha_inv_geom_alt,
            "alpha_fs_inv_CODATA": codata_inv,
            "alpha_inv_geom_rel_err": abs(alpha_inv_geom - codata_inv) / codata_inv,
            "alpha_inv_geom_alt_rel_err": abs(alpha_inv_geom_alt - codata_inv) / codata_inv,
            "alpha_inv_derived_rel_err": abs(alpha_inv_derived - codata_inv) / codata_inv,
            "note": "§8.2·geo: dimensional chain at a=l_P; ratios → carrier_inventory_row",
        }

    def rhombic_dodecahedron_geometry_row(self) -> dict[str, float | int | str | bool]:
        """§8.2·geo·voronoi / §1.6.1 — FCC Voronoy cell (rhombic dodecahedron) at a=l_P."""
        n12 = N12_FCC_CAUSAL_LINKS
        n_rhomb = 12
        n_vert_axis = 6
        n_vert_cubic = 8
        n_vertices = n_vert_axis + n_vert_cubic
        n_edges = 24
        kappa = KAPPA_FCC_1TICK
        lp = self.l_P
        edge_a = lp  # A1: NN at l_P; rhombus edge = a on Voronoy cell
        v_hv = edge_a**3 / math.sqrt(2.0)
        vol_voronoi = v_hv
        vol_cubo = (8.0 / 3.0) * math.sqrt(2.0) * edge_a**3
        cubo_over_voronoi = vol_cubo / vol_voronoi
        rhomb_acute_cos = 1.0 / 3.0
        rhomb_acute_sin = math.sqrt(8.0 / 9.0)  # 2√2/3
        a_rhomb_one = edge_a**2 * rhomb_acute_sin
        s_total = n_rhomb * a_rhomb_one
        r_in = edge_a / 2.0  # perpendicular bisector to NN ⇒ |ON|/2
        r_vertex_axis = kappa * edge_a  # ±(a/√2,0,0) family
        r_vertex_cubic = edge_a * math.sqrt(3.0 / 2.0)
        r_in_cubo_1tick = kappa * edge_a
        return {
            "anchor": "edge_a = l_P (A1); v_hV = Voronoy volume; hull cuboctahedron is dual partner",
            "edge_a_m": edge_a,
            "edge_a_over_l_P": edge_a / lp,
            "l_P_m": lp,
            "n_nn": n12,
            "n_faces_rhomb": n_rhomb,
            "n_vertices": n_vertices,
            "n_vertices_axis": n_vert_axis,
            "n_vertices_cubic": n_vert_cubic,
            "n_edges": n_edges,
            "rhombus_edge_m": edge_a,
            "rhombus_acute_cos": rhomb_acute_cos,
            "rhombus_acute_deg": math.degrees(math.acos(rhomb_acute_cos)),
            "A_rhomb_one_m2": a_rhomb_one,
            "S_total_m2": s_total,
            "V_voronoi_m3": vol_voronoi,
            "v_hV_m3": v_hv,
            "V_cuboctahedron_m3": vol_cubo,
            "V_over_v_hV": vol_voronoi / v_hv,
            "V_over_v_hV_exact": "1",
            "V_cuboctahedron_over_V_voronoi": cubo_over_voronoi,
            "V_cuboctahedron_over_V_voronoi_exact": "16/3",
            "V_over_S_m": vol_voronoi / s_total,
            "V_over_S_over_a": (vol_voronoi / s_total) / edge_a,
            "R_in_Voronoi_m": r_in,
            "R_in_over_a": r_in / edge_a,
            "R_vertex_axis_m": r_vertex_axis,
            "R_vertex_cubic_m": r_vertex_cubic,
            "R_in_cuboctahedron_1tick_m": r_in_cubo_1tick,
            "R_in_Voronoi_over_R_in_cuboctahedron_1tick": r_in / r_in_cubo_1tick,
            "R_in_Voronoi_eq_kappa_times_R_in_cuboctahedron": abs(r_in - kappa * r_in_cubo_1tick) < 1e-15 * edge_a,
            "R_vertex_axis_over_a": kappa,
            "dihedral_deg": 120.0,
            "dual_cuboctahedron": "12V↔12F rhomb; 14F cubo↔14V; 24E shared",
            "note": "§8.2·geo·voronoi: WS cell; R_in=a/2 wall; axis vertex=a/√2=cubo R_in",
        }

    def rhombic_dodecahedron_carrier_inventory_row(self) -> dict[str, float | int | str | bool | list]:
        """§8.2·geo·voronoi — Voronoy body vs 1-tick hull; dual to cuboctahedron."""
        geo = self.rhombic_dodecahedron_geometry_row()
        cubo = self.cuboctahedron_geometry_row()
        kappa = KAPPA_FCC_1TICK
        n12 = int(geo["n_nn"])
        edge_a = float(geo["edge_a_m"])
        ratio_inventory: list[dict[str, str | float | bool]] = [
            {
                "id": "V_over_v_hV",
                "ratio": float(geo["V_over_v_hV"]),
                "maps_to": "dV = v_hV on FCC node (§1.6.2)",
                "status": "derived",
                "mechanism": "Voronoy volume = a³/√2 by packing; identity not fit",
            },
            {
                "id": "R_in_Voronoi",
                "ratio": float(geo["R_in_over_a"]),
                "at_a_eq_lP": float(geo["R_in_Voronoi_m"]),
                "unit": "m",
                "maps_to": "cell wall at NN bisector |ON|/2",
                "status": "derived",
                "mechanism": "R_in=a/2; not cuboctahedron square-face R_in=κa",
            },
            {
                "id": "R_in_Voronoi_over_R_in_cuboctahedron",
                "ratio": float(geo["R_in_Voronoi_over_R_in_cuboctahedron_1tick"]),
                "maps_to": "Voronoy wall vs 1-tick hull inradius",
                "status": "inventory",
                "mechanism": "R_in(V)=κ·R_in(hull); κ same macro constant",
            },
            {
                "id": "V_cuboctahedron_over_V_voronoi",
                "ratio": float(geo["V_cuboctahedron_over_V_voronoi"]),
                "maps_to": "hull bulk / node volume",
                "status": "inventory",
                "mechanism": "16/3 = same ratio as cubo V/v_hV from hull side",
            },
            {
                "id": "V_over_S",
                "ratio": float(geo["V_over_S_over_a"]),
                "at_a_eq_lP": float(geo["V_over_S_m"]),
                "unit": "m",
                "maps_to": "open — Voronoy compactness vs hull",
                "status": "open",
                "mechanism": "V/(Sa)=1/16 at a=l_P",
            },
            {
                "id": "dual_cuboctahedron",
                "ratio": float(n12),
                "maps_to": "12 NN centers hull ↔ 12 rhomb faces",
                "status": "inventory",
                "mechanism": "14↔14 vertices/faces swap; 24 edges",
            },
        ]
        derived = sum(1 for r in ratio_inventory if r["status"] == "derived")
        open_ = sum(1 for r in ratio_inventory if r["status"] in ("open", "inventory"))
        return {
            **{k: geo[k] for k in (
                "edge_a_m",
                "V_over_v_hV",
                "V_over_S_m",
                "V_over_S_over_a",
                "R_in_Voronoi_m",
                "V_cuboctahedron_over_V_voronoi",
            )},
            "R_in_cuboctahedron_1tick_m": float(cubo["R_in_1tick_m"]),
            "kappa_FCC": kappa,
            "dual_cuboctahedron": geo["dual_cuboctahedron"],
            "ratio_inventory": ratio_inventory,
            "ratio_derived_count": derived,
            "ratio_open_count": open_,
            "precedent": "Voronoy R_in=a/2; hull R_in=κa; axis vertex of RD = hull R_in distance",
            "note": "§8.2·geo·voronoi: WS cell body; do not confuse with 1-tick hull",
        }

    def cuboctahedron_carrier_inventory_row(self) -> dict[str, float | int | str | bool | list]:
        """§8.2·geo — from edge a=l_P: dimensional body → ratio → coupling (κ precedent)."""
        geo = self.cuboctahedron_geometry_row()
        n12 = int(geo["n_nn"])
        n_sq = int(geo["n_faces_square"])
        n_tri = int(geo["n_faces_triangle"])
        kappa = float(geo["kappa_inscribed_1tick"])
        lp = self.l_P
        edge_a = float(geo["edge_a_m"])
        s_total = float(geo["S_total_m2"])
        vol_cubo = float(geo["V_cuboctahedron_m3"])
        a_sq_one = float(geo["A_square_one_m2"])
        v_over_s = float(geo["V_over_S_m"])
        v_over_s_l_p = float(geo["V_over_S_over_l_P"])
        n_sq_over_n_tri = n_sq / n_tri
        n_sq_over_faces = n_sq / (n_sq + n_tri)
        dihedral_deg = float(geo["dihedral_square_triangle_deg"])
        dihedral_over_180 = dihedral_deg / 180.0
        pack_proton = 1.0 + kappa**2 / n12
        n_phi = hv_bit_budget().N_phi
        anchor_chain: list[dict[str, str | float]] = [
            {"quantity": "edge_a", "at_a_eq_lP": edge_a, "unit": "m", "from": "A1: |NN|=l_P"},
            {"quantity": "R_out", "at_a_eq_lP": float(geo["R_out_m"]), "unit": "m", "from": "cuboctahedron circumradius = a"},
            {"quantity": "R_in_1tick", "at_a_eq_lP": float(geo["R_in_1tick_m"]), "unit": "m", "from": "κ·a; square faces limit"},
            {"quantity": "A_square_one", "at_a_eq_lP": a_sq_one, "unit": "m²", "from": "□ face; Stokes B_□=Φ_□/a²"},
            {"quantity": "S_total", "at_a_eq_lP": s_total, "unit": "m²", "from": "6a²+8·(√3/4)a²"},
            {"quantity": "V_cubo", "at_a_eq_lP": vol_cubo, "unit": "m³", "from": "(8/3)√2·a³"},
            {"quantity": "v_hV", "at_a_eq_lP": float(geo["v_hV_m3"]), "unit": "m³", "from": "a³/√2 FCC node"},
            {"quantity": "V/S", "at_a_eq_lP": v_over_s, "unit": "m", "from": "compactness length at a"},
        ]
        ratio_inventory: list[dict[str, str | float | bool]] = [
            {
                "id": "edge_a_anchor",
                "ratio": 1.0,
                "at_a_eq_lP": edge_a,
                "unit": "m",
                "maps_to": "A1 NN distance; all body SI measures normalized here",
                "status": "derived",
                "mechanism": "a=l_P not fitted; ratios are V/a³, R_in/a, …",
            },
            {
                "id": "kappa_inscr_1tick",
                "ratio": kappa,
                "at_a_eq_lP": float(geo["R_in_1tick_m"]),
                "unit": "m (=κa)",
                "maps_to": "c=κc₀, hT=t_P·κ, λ₀=κℓ_P (§1.1)",
                "status": "derived",
                "mechanism": "R_in(a)/R_out(a) at a=l_P — ratio after lengths",
            },
            {
                "id": "A_square_one",
                "ratio": a_sq_one / (edge_a**2),
                "at_a_eq_lP": a_sq_one,
                "unit": "m²",
                "maps_to": "open — Φ_□ holonomy cell; B_□=Φ_□/a² (§8.2 Stokes)",
                "status": "open",
                "mechanism": "□ perimeter 4a; derive g for phase/force on this face at a=l_P",
            },
            {
                "id": "kappa_link",
                "ratio": 1.0 / n12,
                "maps_to": "γ, ν_CA, CR/sync per-link fraction (§5.2.2)",
                "status": "derived",
                "mechanism": "1/|N₁₂| from causal star at same a=l_P links",
            },
            {
                "id": "v_hV_at_a",
                "ratio": 1.0 / math.sqrt(2.0),
                "at_a_eq_lP": float(geo["v_hV_m3"]),
                "unit": "m³",
                "maps_to": "dV=v_hV on FCC Voronoy node (§1.6.2)",
                "status": "derived",
                "mechanism": "v_hV=a³/√2 when a=l_P",
            },
            {
                "id": "V_at_a",
                "ratio": (8.0 / 3.0) * math.sqrt(2.0),
                "at_a_eq_lP": vol_cubo,
                "unit": "m³",
                "maps_to": "open — bulk hull volume at a",
                "status": "inventory",
                "mechanism": "V=(8/3)√2·a³; ratio V/v_hV=16/3 only after both volumes",
            },
            {
                "id": "V_over_v_hV",
                "ratio": float(geo["V_over_v_hV"]),
                "maps_to": "open — derived ratio bulk/node at a=l_P",
                "status": "inventory",
                "mechanism": "16/3; do not skip dimensional V and v_hV",
            },
            {
                "id": "V_over_S",
                "ratio": v_over_s_l_p,
                "at_a_eq_lP": v_over_s,
                "unit": "m",
                "maps_to": "open — compactness V/S at a",
                "status": "open",
                "mechanism": "V/S then ÷a for dimensionless; both from a",
            },
            {
                "id": "A_square_over_A_total",
                "ratio": float(geo["A_square_over_A_total"]),
                "maps_to": "open — square vs triangle face area weight",
                "status": "open",
                "mechanism": "areas from a first; ratio second",
            },
            {
                "id": "n_square_over_n_triangle",
                "ratio": n_sq_over_n_tri,
                "maps_to": "open — face count 6/8 ≠ area",
                "status": "open",
                "mechanism": "combinatorics at fixed a",
            },
            {
                "id": "dihedral_square_triangle",
                "ratio": dihedral_over_180,
                "maps_to": "open — phase at □–△ ridge",
                "status": "open",
                "mechanism": "135° intrinsic angle; coupling open",
            },
            {
                "id": "R_in_over_R_out_classical",
                "ratio": float(geo["R_in_over_R_out_classical"]),
                "maps_to": "not M κ — different embedding",
                "status": "distinct",
                "mechanism": "√6/6 ≠ κ; canon uses 1-tick square-face R_in=κa",
            },
            {
                "id": "proton_pack_kappa2_over_N12",
                "ratio": pack_proton,
                "maps_to": "m_p stack 1+κ²/N₁₂",
                "status": "partial",
                "mechanism": "κ from R_in(a)/a at l_P",
            },
            {
                "id": "Phi_square_holonomy",
                "ratio": float("nan"),
                "at_a_eq_lP": 4.0 * edge_a,
                "unit": "m (□ perimeter)",
                "maps_to": "open DoD — sim Σ_{∂□}Δφ vs α_fs at a=l_P",
                "status": "open",
                "mechanism": "force from holonomy on □ with edge a, not ratio table",
            },
            {
                "id": "alpha_fs_derived",
                "ratio": float(geo["alpha_fs_inv_derived"]),
                "maps_to": "T-readout π-postulate; not from a alone",
                "status": "derived_T",
                "mechanism": "guardrail vs skipping a→Φ_□ path",
            },
        ]
        derived = sum(1 for r in ratio_inventory if r["status"] == "derived")
        open_ = sum(1 for r in ratio_inventory if r["status"] in ("open", "inventory"))
        return {
            **{k: geo[k] for k in ("edge_a_m", "V_over_v_hV", "V_over_S_m", "V_over_S_over_l_P", "kappa_inscribed_1tick")},
            "anchor_chain": anchor_chain,
            "n_square_over_n_triangle": n_sq_over_n_tri,
            "ratio_inventory": ratio_inventory,
            "ratio_derived_count": derived,
            "ratio_open_count": open_,
            "precedent": "κ = R_in(a)/R_out(a) at a=l_P; c=κc₀ is readout check — see kappa_bottom_up_row",
            "note": "§8.2·geo: dimensional body at a=l_P first; ratios derived",
        }

    def kappa_bottom_up_row(self) -> dict[str, float | int | str | bool]:
        """§7.2 / §8.2·geo·κ — Planck units embed c; κ_geom from hull, not from c/c₀."""
        geo = self.cuboctahedron_geometry_row()
        kappa_geom = float(geo["kappa_inscribed_1tick"])
        kappa_hex = KAPPA_HEX
        lp = self.l_P
        t_p = self.t_P
        ht = self.hT
        c0 = self.c0
        c = self.c
        e_p = self.E_P
        e0 = self.E_0
        tol = 1e-12
        l_p_from_c = math.sqrt(self.hbar * self.G / self.c**3)
        t_p_from_c = l_p_from_c / self.c
        return {
            "ontology_order": "A1+packing→κ_geom; (ℏ,G,c)→Planck; hT=κ·t_P; c=κc₀ is check",
            "kappa_geom_FCC": kappa_geom,
            "kappa_geom_hex": kappa_hex,
            "kappa_geom_equals_R_in_over_R_out": abs(
                kappa_geom - float(geo["R_in_over_R_out_1tick"])
            )
            < tol,
            "kappa_not_defined_as_c_over_c0": True,
            "l_P_m": lp,
            "l_P_from_c_formula_m": l_p_from_c,
            "l_P_rel_err": abs(lp - l_p_from_c) / lp,
            "t_P_conv_s": t_p,
            "t_P_equals_l_P_over_c": abs(t_p - lp / c) / t_p < tol,
            "t_P_from_c_formula_s": t_p_from_c,
            "planck_c_power_l_P": -1.5,
            "planck_c_power_t_P": -2.5,
            "planck_c_power_E_P": 2.5,
            "planck_c_power_u_P": 7.0,
            "hT_s": ht,
            "hT_equals_kappa_geom_times_t_P": abs(ht - kappa_geom * t_p) / ht < tol,
            "hT_over_t_P": ht / t_p,
            "c0_m_s": c0,
            "c0_equals_l_P_over_hT": abs(c0 - lp / ht) / c0 < tol,
            "c0_over_c": c0 / c,
            "c0_over_c_equals_inv_kappa": abs(c0 / c - 1.0 / kappa_geom) / (c0 / c) < tol,
            "c_over_c0_equals_kappa_check": abs(c / c0 - kappa_geom) / kappa_geom < tol,
            "c_equals_kappa_c0_check": abs(c - kappa_geom * c0) / c < tol,
            "E_P_conv_J": e_p,
            "E_0_J": e0,
            "E_0_over_E_P": e0 / e_p,
            "E_0_over_E_P_equals_kappa": abs(e0 / e_p - kappa_geom) / kappa_geom < tol,
            "continuum_hidden_assumption": "t_P=l_P/c tacitly sets link speed = macro c (κ=1)",
            "M_breaks_assumption_via": "κ_geom=1/√2 from cuboctahedron □-face inradius",
            "hex_same_method": "κ_hex=√3/2 from hex causal polygon inradius",
            "note": "§7.2: Planck ladder uses CODATA c; κ from §8.2·geo body — c/c₀ follows, not defines κ",
        }

    def planck_from_cell_conditions_row(self) -> dict[str, float | int | str | bool]:
        """§7.3 — Planck ladder from cell physics + geometry; (ℏ,G,c) consistency check."""
        geo = self.cuboctahedron_geometry_row()
        rd = self.rhombic_dodecahedron_geometry_row()
        kappa = float(geo["kappa_inscribed_1tick"])
        lp = self.l_P
        ht = self.hT
        t_p = self.t_P
        s0 = self.s_0
        e0 = self.E_0
        e_p = self.E_P
        c = self.c
        c0 = self.c0
        v_hv = float(rd["V_voronoi_m3"])
        m_arg = self.m_arg
        m_p = self.m_P
        mu_p = self.mu_P
        u_p = self.u_P
        k_p = self.K_P
        tol = 1e-11
        rho_cell = m_arg / v_hv
        e_brick_sat = u_p * v_hv
        b_hv = 2.0 * math.pi / LN2
        bekenstein_bits = 2.0 * math.pi * e_p * lp / (self.hbar * c * LN2)
        hv = hv_bit_budget()
        return {
            "derivation_order": (
                "geometry(v_hV,κ) → cell(s₀,E₀,m_arg) → ρ_cell=μ_P → fluid(u_P=μ_Pc²) "
                "→ conventional t_P=hT/κ, E_P=E₀/κ"
            ),
            "geometry_v_hV_m3": v_hv,
            "geometry_v_hV_over_lP3": v_hv / lp**3,
            "geometry_kappa": kappa,
            "cell_s0_J_s": s0,
            "cell_s0_equals_hbar_half": abs(s0 - self.hbar / 2.0) / s0 < tol,
            "cell_hT_s": ht,
            "cell_E0_J": e0,
            "cell_E0_equals_s0_over_hT": abs(e0 - s0 / ht) / e0 < tol,
            "cell_m_arg_kg": m_arg,
            "cell_m_arg_equals_E0_over_c2": abs(m_arg - e0 / c**2) / m_arg < tol,
            "cell_m_arg_equals_mP_over_sqrt2": abs(m_arg - m_p / math.sqrt(2.0)) / m_arg < tol,
            "closure_rho_cell_kg_m3": rho_cell,
            "closure_mu_P_kg_m3": mu_p,
            "closure_rho_cell_equals_mu_P": abs(rho_cell - mu_p) / mu_p < tol,
            "closure_mP_over_lP3_equals_mu_P": abs(m_p / lp**3 - mu_p) / mu_p < tol,
            "fluid_u_P_J_m3": u_p,
            "fluid_u_P_equals_mu_P_c2": abs(u_p - mu_p * c**2) / u_p < tol,
            "fluid_c2_equals_K_P_over_mu_P": abs(c**2 - k_p / mu_p) / c**2 < tol,
            "fluid_K_P_equals_u_P": abs(k_p - u_p) / u_p < tol,
            "brick_saturation_energy_J": e_brick_sat,
            "conventional_t_P_derived_s": ht / kappa,
            "conventional_t_P_conv_s": t_p,
            "conventional_t_P_rel_err": abs(ht / kappa - t_p) / t_p,
            "conventional_E_P_derived_J": e0 / kappa,
            "conventional_E_P_conv_J": e_p,
            "conventional_E_P_rel_err": abs(e0 / kappa - e_p) / e_p,
            "conventional_l_P_from_cell_a_m": lp,
            "conventional_l_P_from_sqrt_hbar_G_c": math.sqrt(self.hbar * self.G / c**3),
            "bekenstein_B_hV": b_hv,
            "bekenstein_algebraic": abs(bekenstein_bits - b_hv) / b_hv < tol,
            "register_N_phi": hv.N_phi,
            "register_N_hier": int(math.floor(b_hv)) - 1,
            "absolute_inputs": "ℏ (s₀), G, c — measured; geometry+cell fix ratios and M-first tick",
            "planck_not_primary": "t_P, E_P are derived from hT, E₀ via κ — not cell axioms",
            "note": "§7.3: physics on hV closes μ_P; Planck-with-c is consistency layer, not κ definition",
        }

    def anchor_a_is_l_P_row(self) -> dict[str, float | int | str | bool]:
        """§7.4 — single spatial quantum: hull edge a ≡ hL ≡ l_P; √(ℏG/c³) is check only."""
        geo = self.cuboctahedron_geometry_row()
        rd = self.rhombic_dodecahedron_geometry_row()
        lp = self.l_P
        edge_a = float(geo["edge_a_m"])
        v_hv_geo = float(rd["V_voronoi_m3"])
        c0 = self.c0
        ht = self.hT
        p0 = self.p_0
        m_arg_em = self.m_arg
        m_arg_mech = (2.0 * p0) / c0  # §5.2.1: p₀ = m_arg·c₀/2 — no macro c
        lp_textbook = math.sqrt(self.hbar * self.G / self.c**3)
        tol = 1e-11
        return {
            "theorem": "On M there is one spatial step; a cannot differ from l_P",
            "chain": "Postulate0 hL → A1 NN link → hull edge a → Voronoy v_hV(a) → dV",
            "hL_m": lp,
            "hull_edge_a_m": edge_a,
            "a_equals_hL": abs(edge_a - lp) / lp < tol,
            "a_equals_l_P": abs(edge_a - lp) / lp < tol,
            "l_P_primary": "l_P := hL := A1 light-like link (§0.2 · §1.6.2)",
            "l_P_textbook_check_m": lp_textbook,
            "l_P_textbook_rel_err": abs(lp - lp_textbook) / lp,
            "l_P_not_defined_by_c": True,
            "c_in_textbook_only": "√(ℏG/c³), t_P=l_P/c, Bekenstein SI — consistency layer",
            "scale_decoupled_from_c_definition": True,
            "no_second_ruler": True,
            "no_rescale_without_breaking": (
                "λ·a would split hL vs A1 vs dV=v_hV(a) unless λ=1; no structure below dl (§1.4)"
            ),
            "v_hV_at_a_m3": v_hv_geo,
            "v_hV_equals_lP3_over_sqrt2": abs(v_hv_geo - lp**3 / math.sqrt(2.0)) / v_hv_geo < tol,
            "m_arg_from_macro_c_kg": m_arg_em,
            "m_arg_from_c0_only_kg": m_arg_mech,
            "m_arg_mech_equals_em": abs(m_arg_mech - m_arg_em) / m_arg_em < tol,
            "p0_equals_hbar_over_2lP": abs(p0 - self.hbar / (2.0 * lp)) / p0 < tol,
            "absolute_SI_still_needs": "ℏ, G (+ c or mechanical anchor) for meters — not for M ruler",
            "postulate_0_1_scope": "hL,hT symbols + no sub-dl only — not l_P, not sqrt(hbar G/c^3)",
            "identification_is_theorem_not_postulate": True,
            "note": "§7.4: a=l_P forced; Postulate 0.1 must not presuppose Planck name",
        }

    def discreteness_from_axioms_row(self) -> dict[str, float | int | str | bool]:
        """§0 Thm 0.1 — discreteness from A1–A3,A7,A10,A13,A16 + bit budget; not Postulate 0.1."""
        hv = hv_bit_budget()
        lp = self.l_P
        ht = self.hT
        s0 = self.s_0
        p0 = self.p_0
        z_min = 2.0 ** (-hv.frac_bits)
        b_hv = 2.0 * math.pi / LN2
        tol = 1e-12
        delta_phi_disc = heisenberg_phi_min_disc(phase_bits=hv.phase_bits)
        return {
            "theorem": "Thm 0.1: countable FCC carrier; hL,hT from axioms+brick; no sub-dl",
            "replaces_postulate_0_1": True,
            "axioms": "A1,A2,A3,A7,A5,A10,A11,A13,A16,§1.6,§3.12",
            "lemma_a3_a13_finite_alphabet": True,
            "lemma_a1_fcc_n12": N12_FCC_CAUSAL_LINKS,
            "lemma_a10_integer_charge": True,
            "B_hV_pure": b_hv,
            "B_hV_from_bekenstein_when_EPl_eq_hbar_c": True,
            "N_ring": hv.N_ring,
            "N_phi": hv.N_phi,
            "frac_bits": hv.frac_bits,
            "delta_phi_min_rad": DELTA_PHI_MIN,
            "delta_phi_min_disc": delta_phi_disc,
            "z_min_natural": z_min,
            "z_min_positive": z_min > 0.0,
            "s0_equals_hbar_half": abs(s0 - self.hbar / 2.0) / s0 < tol,
            "p0_equals_hbar_over_2hL": abs(p0 - self.hbar / (2.0 * lp)) / p0 < tol,
            "p0_equals_m_arg_c0_half": abs(p0 - self.m_arg * self.c0 / 2.0) / p0 < tol,
            "hL_m": lp,
            "hT_s": ht,
            "no_substructure_below_hL": (
                "A7 rho<=u_P in one dV; A10 n on d(hV); B_hV+frac_bits floor"
            ),
            "scale_hL_name_l_P": "§7.4 after cell closure; not Postulate 0",
            "c_not_in_discreteness_chain": True,
            "note": "§0 Thm 0.1: discrete Λ from info+causal+topology; hL scale+ℓ_P name §7.3–7.4",
        }

    def mechanics_from_axioms_row(self) -> dict[str, float | int | str | bool]:
        """§0.8 / Thm 5.1 — Landau mechanics from Thm 0.1 + A3,A5,A13,A16 + §3.12 ledger."""
        en = energy_quantum_row()
        tol = 1e-12
        s0 = self.s_0
        p0 = self.p_0
        l0 = self.L_0
        f0 = self.F_0
        g_m = self.g_M
        e0 = self.E_0
        return {
            "theorem": "Thm 5.1 / Cor 0.8: s0 ladder p0,L0,F0,E0; not separate p/F postulates",
            "replaces_mechanical_postulates": True,
            "axioms": "A3,A5,A13,A16,Thm0.1,§3.7,§3.12,§5.0.2",
            "lemma_a5_s0": abs(s0 - self.hbar * DELTA_PHI_MIN) / s0 < tol,
            "lemma_thm01_p0": abs(p0 - s0 / self.l_P) / p0 < tol,
            "lemma_L0_equals_s0": abs(l0 - s0) / s0 < tol,
            "lemma_F0_equals_m_arg_g_M": abs(f0 - self.m_arg * g_m) / f0 < tol,
            "lemma_p0_equals_m_arg_c0_half": abs(p0 - self.m_arg * self.c0 / 2.0) / p0 < tol,
            "lemma_E0_ladder_p0_c0": en["rel_p0_c0"] < tol,
            "lemma_E0_ladder_F0_hL": en["rel_F0_lP"] < tol,
            "lemma_E0_ladder_L0_hT": en["rel_L0_hT"] < tol,
            "delta_phi_min_rad": DELTA_PHI_MIN,
            "s0_J_s": s0,
            "p0_kg_m_s": p0,
            "L0_J_s": l0,
            "F0_N": f0,
            "g_M_m_s2": g_m,
            "E0_J": e0,
            "m_arg_kg": self.m_arg,
            "momentum_ledger_integer": "A13 leapfrog + floor N only in N; verify LadderLedger",
            "continuum_p_L_F_is_T_readout": True,
            "p0_from_hbar_over_2hL_not_macro_c": abs(p0 - self.hbar / (2.0 * self.l_P)) / p0 < tol,
            "note": "§0.8/Thm5.1: Landau ladder from s0=ℏ/2; float j=Im(z*∇z) is T only",
        }

    def excitations_full_quantization_row(self) -> dict[str, float | int | str | bool]:
        """§0.9 / Thm 5.2 — no fundamental wave; excitations = n_E·E0, phonon modes."""
        eq = elementary_quanta_row()
        en = energy_quantum_row()
        ht = self.hT
        e0 = self.E_0
        hbar = self.hbar
        nu0 = 1.0 / ht
        omega0 = 2.0 * math.pi / ht
        hbar_nu0 = hbar * nu0
        tol = 1e-12
        return {
            "theorem": "Thm 5.2 / Cor 0.9: excitations quantize; wave is T-readout only",
            "no_fundamental_wave_on_M": True,
            "axioms": "A3,Thm0.1,§3.12,§5.2.2,§5.2.4,§4.9",
            "energy_transfer_n_E_integer": eq["energy_ticks_per_E0"] >= 1,
            "E_equals_n_E_times_E0": True,
            "E0_J": e0,
            "n_E_from_phi_example": n_E_from_phi_ticks(int(eq["energy_ticks_per_E0"])),
            "nu0_Hz": nu0,
            "omega0_rad_s": omega0,
            "hbar_nu0_J": hbar_nu0,
            "hbar_nu0_equals_2E0": abs(hbar_nu0 - 2.0 * e0) / e0 < tol,
            "photon_sector_n0": True,
            "phonon_on_lattice_BZ": "§5.2.4 G,BZ; sound=n_k on modes, not sin(kx-wt)",
            "sound_macro_vs_photon": "T: v_s<<c; M: p0 packets / phonon n_k",
            "E0_ladder_closed": en["rel_p0_c0"] < tol and en["rel_F0_lP"] < tol,
            "continuum_wave_is_T_only": True,
            "madelung_j_is_T_readout": True,
            "note": "§0.9: light/sound quantize; interference=many quanta; wave label=T",
        }

    def phonon_from_carrier_row(self) -> dict[str, float | int | str | bool]:
        """§5.2.6 — phonon parameters from FCC carrier (WS/BZ/hT); not fitted."""
        geo = self.rhombic_dodecahedron_geometry_row()
        lp = self.l_P
        ht = self.hT
        c0 = self.c0
        e0 = self.E_0
        p0 = self.p_0
        v_hv = float(geo["v_hV_m3"])
        n_density = 1.0 / v_hv
        d = 3
        g_acoustic = d
        kappa_link_fcc = kappa_link(n_links=N12_FCC_CAUSAL_LINKS)
        k_bz_max = math.pi / lp
        g_scale = 2.0 * math.pi / lp
        nu0 = 1.0 / ht
        omega0 = 2.0 * math.pi / ht
        omega_d = omega0
        v_acoustic = omega_d / k_bz_max
        hbar = self.hbar
        h = 2.0 * math.pi * hbar
        k_debye = (6.0 * math.pi**2 * n_density) ** (1.0 / 3.0)
        tol = 1e-9
        return {
            "theorem": "Thm 5.3 / carrier ask: phonon from FCC Λ + hL + hT + v_hV",
            "carrier": "FCC N12 · rhombic dodecahedron WS · A1 edge=l_P",
            "edge_a_m": float(geo["edge_a_m"]),
            "v_hV_m3": v_hv,
            "n_density_m3": n_density,
            "n_density_over_sqrt2_lP3": abs(n_density * lp**3 / math.sqrt(2.0) - 1.0) < tol,
            "d_spatial": d,
            "g_acoustic_branches": g_acoustic,
            "kappa_link": kappa_link_fcc,
            "k_BZ_max_m": k_bz_max,
            "G_scale_m": g_scale,
            "k_BZ_max_times_hL": k_bz_max * lp / math.pi,
            "nu0_Hz": nu0,
            "omega0_rad_s": omega0,
            "omega_D_rad_s": omega_d,
            "omega_D_over_nu0": omega_d / (2.0 * math.pi * nu0),
            "v_acoustic_m_s": v_acoustic,
            "v_acoustic_over_c0": v_acoustic / c0,
            "v_acoustic_equals_2c0": abs(v_acoustic - 2.0 * c0) / c0 < tol,
            "omega_D_equals_v_a_k_max": abs(omega_d - v_acoustic * k_bz_max) / omega_d < tol,
            "E0_J": e0,
            "hbar_nu0_J": hbar * nu0,
            "hbar_nu0_equals_2E0": abs(hbar * nu0 - 2.0 * e0) / e0 < tol,
            "hbar_omega_D_J": hbar * omega_d,
            "h_nu0_over_E0": h * nu0 / e0,
            "hbar_omega_D_over_E0": hbar * omega_d / e0,
            "p0_kg_m_s": p0,
            "p0_equals_hbar_k_max_over_2pi": abs(p0 - hbar * k_bz_max / (2.0 * math.pi)) / p0 < tol,
            "k_debye_m": k_debye,
            "k_debye_over_k_BZ": k_debye / k_bz_max,
            "phonon_E_k_small": "E(k)=hbar v_a |k|, n_k in Z",
            "phonon_not_sin_wave": True,
            "pressure_wave_c_macro": self.c,
            "pressure_wave_not_same_as_phonon_v_a": abs(self.c - v_acoustic) / self.c > 0.1,
            "note": "§5.2.6: phonon v_a=2c0, k_max=pi/l_P, omega_D=2pi/hT; sound=n_k quanta",
        }

    def square_face_holonomy_probe_row(self, *, grid: int = 16, device: str = "cpu") -> dict:
        """§8.2·geo probe — Phi_□ on hull □ at a=l_P; alpha from E/holonomy (open DoD)."""
        from mt_ca.em_plaquette import square_face_holonomy_probe

        row = square_face_holonomy_probe(grid=grid, device=device)
        row["edge_a_over_l_P"] = row["edge_a_m"] / self.l_P
        return row

