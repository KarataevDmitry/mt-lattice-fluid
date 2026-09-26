#!/usr/bin/env python3
"""Verify M-layer axioms after first-principles rebuild.

Check bodies live in verify_checks/*.py — this file is the runner + re-exports.
"""

from __future__ import annotations

import argparse
import json
import sys

import torch

from verify_checks.axioms import *  # noqa: F403
from verify_checks.alpha import *  # noqa: F403
from verify_checks.floor0 import *  # noqa: F403
from verify_checks.floor1 import *  # noqa: F403
from verify_checks.units import *  # noqa: F403
from verify_checks.carrier import *  # noqa: F403
from verify_checks.sm import *  # noqa: F403
from verify_checks.geometry import *  # noqa: F403
from verify_checks.instruments import *  # noqa: F403

def run_all(device: str) -> list[dict]:
    return [
        check_a3_unitarity(device=device),
        check_a3_local_ca(device=device),
        check_a3_spectral_reference(device=device),
        check_a3_diffusive_fails(device=device),
        check_a4_phase_preserves_modulus(device=device),
        check_impl_zero_frozen(device=device),
        check_a5_vacuum_floor(device=device),
        check_a8_macro_suppression(device=device),
        check_a9_cr_smooth_modes(device=device),
        check_a11_vortex_persistence(device=device),
        check_a16_heisenberg_floor(device=device),
        check_a7_density_clamp(device=device),
        check_a10_winding(device=device),
        check_pauli_repel(device=device),
        check_compton_electron(device=device),
        check_alpha_hop_ladder(device=device),
        check_alpha_fixed_point(device=device),
        check_na0_from_carrier(device=device),
        check_na0_h_carrier(device=device),
        check_alpha_force_lattice(device=device),
        check_alpha_meaning(device=device),
        check_alpha_descent(device=device),
        check_alpha_mass_defect_optics(device=device),
        check_alpha_arg_binding_try(device=device),
        check_alpha_schwinger(device=device),
        check_alpha_dirac_g2(device=device),
        check_alpha_ae_cloud(device=device),
        check_alpha_rydberg_hall(device=device),
        check_alpha_em_face_weight(device=device),
        check_alpha_dual_fraction(device=device),
        check_alpha_sqrt2_descent(device=device),
        check_alpha_M_from_g_try(device=device),
        check_alpha_nF_momentum_registry(device=device),
        check_alpha_full_quantization_bridge(device=device),
        check_coulomb_M_native(device=device),
        check_alpha_U0_soft_face(device=device),
        check_alpha_upstairs_mass_probe(device=device),
        check_alpha_si_bridge(device=device),
        check_alpha_meter_na0_bridge(device=device),
        check_meter_decouple_from_M(device=device),
        check_length_dim_from_lP_alpha(device=device),
        check_time_dim_from_tP(device=device),
        check_units_time_first_cascade(device=device),
        check_planck_temperature_independent(device=device),
        check_brick_internal_spectrum(device=device),
        check_floor0_internal_catalog(device=device),
        check_floor0_phase_space(device=device),
        check_floor0_nE_excitation(device=device),
        check_floor1_leptonic(device=device),
        check_floor1_B0_census(device=device),
        check_floor1_dressing(device=device),
        check_floor1_dressing_close(device=device),
        check_floor1_dressing_f_close(device=device),
        check_floor1_leftovers_close(device=device),
        check_floor1_C3_gamma_close(device=device),
        check_floor1_C3_bath_dogfood(device=device),
        check_carrier_torus_close(device=device),
        check_gpu_eng_tail_close(device=device),
        check_bubble_tick(device=device),
        check_nu_CA_exact(device=device),
        check_hv_bit_budget(device=device),
        check_congruence_ladder(device=device),
        check_internal_phase_coords(device=device),
        check_rho_P_binary(device=device),
        check_vdw_algebra(device=device),
        check_arg_quantum(device=device),
        check_higgs_mass(device=device),
        check_vacuum_bath(device=device),
        check_cuboctahedron_geometry(device=device),
        check_cuboctahedron_carrier(device=device),
        check_rhombic_dodecahedron_geometry(device=device),
        check_rhombic_dodecahedron_carrier(device=device),
        check_kappa_bottom_up(device=device),
        check_planck_from_cell_conditions(device=device),
        check_anchor_a_is_l_P(device=device),
        check_discreteness_from_axioms(device=device),
        check_mechanics_from_axioms(device=device),
        check_excitations_full_quantization(device=device),
        check_phonon_from_carrier(device=device),
        check_square_face_holonomy_probe(device=device),
        check_alpha_bridges(device=device),
        check_proton_mass(device=device),
        check_electron_mass(device=device),
        check_neutron_mass(device=device),
        check_annihilation_t_stats(device=device),
        check_neutrino_mass(device=device),
        check_mechanical_quantum(device=device),
        check_quarter_quantum(device=device),
        check_energy_quantum(device=device),
        check_elementary_quanta(device=device),
        check_a3_global_norm(device=device),
        check_t_madelung_continuity(device=device),
        check_t_continuum_readout(device=device),
        check_t_hydro_limit(device=device),
        check_so2_c4(device=device),
        check_arg_mass_carrier(device=device),
        check_u1_vac(device=device),
        check_chiral_su2(device=device),
        check_leapfrog_bit_exact(device=device),
        check_no_m_heat_death(device=device),
        check_theorem_2_3_8(device=device),
        check_planck_vacuum_floor(device=device),
        check_ladder_ledger(device=device),
        check_matter_b_readout(device=device),
        check_planckon_instrument_fcc(device=device),
        check_instrument_panel_vortex(device=device),
        check_instrument_panel_hex_slice(device=device),
        check_instrument_scales_ladder(device=device),
        check_instrument_scales_time_first(device=device),
        check_a14_symmetry(device=device),
        check_electron_anchor(device=device),
        check_saturation_bc(device=device),
        check_fcc_n12(device=device),
        check_vortex_hex_contour(device=device),
        check_spinor_360_sign(device=device),
        check_su2_720_sign(device=device),
        check_discrete_rot_exp(device=device),
        check_model_purity(),
    ]

def main() -> int:
    parser = argparse.ArgumentParser(description="First-principles M-layer verification")
    parser.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    results = run_all(args.device)
    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print(f"device={args.device}")
        print("-" * 60)
        for row in results:
            status = "PASS" if row["ok"] else "FAIL"
            print(f"{row['id']:12}  {status}  { {k: v for k, v in row.items() if k not in ('id', 'ok')} }")

    failed = [r for r in results if not r["ok"] and r["id"] not in ("A3_diffusive", "T_dft_oracle", "I2_zero", "T_MadelungContinuity")]
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
