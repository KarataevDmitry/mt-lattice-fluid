"""Verify suites — SSOT grouping (mirror mt_ca.app.scenario)."""

from __future__ import annotations

import inspect
from collections.abc import Callable, Iterator, Sequence
from dataclasses import dataclass
from typing import Any

from verify_checks.alpha import *  # noqa: F403
from verify_checks.axioms import *  # noqa: F403
from verify_checks.carrier import *  # noqa: F403
from verify_checks.cosmology import *  # noqa: F403
from verify_checks.floor0 import *  # noqa: F403
from verify_checks.floor1 import *  # noqa: F403
from verify_checks.geometry import *  # noqa: F403
from verify_checks.instruments import *  # noqa: F403
from verify_checks.sm import *  # noqa: F403
from verify_checks.units import *  # noqa: F403

# Row ids that may FAIL without failing the runner (documented probes / negative tests).
WAIVE_EXIT_IDS: frozenset[str] = frozenset(
    {
        "A3_diffusive",
        "T_dft_oracle",
        "I2_zero",
        "T_MadelungContinuity",
    }
)


@dataclass(frozen=True, slots=True)
class VerifySuiteSpec:
    """Named bundle of checks — like ScenarioSpec for sim."""

    id: str
    description: str
    check_names: tuple[str, ...]
    ship: bool = True  # included in `verify_principles.py --ship`


def _names(*fns: Callable[..., dict]) -> tuple[str, ...]:
    return tuple(fn.__name__ for fn in fns)


VERIFY_SUITES: dict[str, VerifySuiteSpec] = {
    "gate": VerifySuiteSpec(
        id="gate",
        description="MODEL purity + LF text EOL (.gitattributes).",
        check_names=_names(check_model_purity, check_repo_text_eol),
        ship=True,
    ),
    "m_axioms": VerifySuiteSpec(
        id="m_axioms",
        description="M law g — A3–A16, symmetries, leapfrog, balance equations (core).",
        check_names=_names(
            check_a3_unitarity,
            check_a3_local_ca,
            check_a3_spectral_reference,
            check_a3_diffusive_fails,
            check_a4_phase_preserves_modulus,
            check_impl_zero_frozen,
            check_a5_vacuum_floor,
            check_a8_macro_suppression,
            check_a11_vortex_persistence,
            check_a16_heisenberg_floor,
            check_a7_density_clamp,
            check_pauli_repel,
            check_a3_global_norm,
            check_so2_c4,
            check_arg_mass_carrier,
            check_u1_vac,
            check_chiral_su2,
            check_leapfrog_bit_exact,
            check_no_m_heat_death,
            check_theorem_2_3_8,
            check_planck_vacuum_floor,
            check_ladder_conservation,
            check_a14_symmetry,
            check_spinor_360_sign,
            check_su2_720_sign,
            check_discrete_rot_exp,
        ),
        ship=True,
    ),
    "m_evolution_open": VerifySuiteSpec(
        id="m_evolution_open",
        description="§3.9 CR on boil · A10 planted contour · FCC N₁₂ 3D boil · hex vortex.",
        check_names=_names(
            check_a9_cr_smooth_modes,
            check_a10_winding,
            check_fcc_boil_ramp_habitat,
            check_fcc_n12,
            check_vortex_hex_contour,
        ),
        ship=True,
    ),
    "t_macro": VerifySuiteSpec(
        id="t_macro",
        description="M→T: ℬz / hydro / T-CL / macro b-field.",
        check_names=_names(
            check_t_madelung_continuity,
            check_t_hydro_limit_bundle,
            check_t_hydro_limit,
            check_classical_limit,
            check_matter_b_macro,
            check_nu_CA_exact,
        ),
        ship=True,
    ),
    "floor0": VerifySuiteSpec(
        id="floor0",
        description="Floor-0 spectrum, brick, n_E catalog.",
        check_names=_names(
            check_brick_internal_spectrum,
            check_floor0_internal_catalog,
            check_floor0_gamma_V,
            check_floor0_phase_space,
            check_floor0_nE_excitation,
            check_floor0_nE_selection,
        ),
        ship=True,
    ),
    "floor1": VerifySuiteSpec(
        id="floor1",
        description="Floor-1 dressing / census / C3 dogfood.",
        check_names=_names(
            check_floor1_leptonic,
            check_floor1_B0_census,
            check_floor1_dressing,
            check_floor1_dressing_close,
            check_floor1_dressing_f_close,
            check_floor1_outer_shell_catalog,
            check_floor1_shell_transitions_boil,
            check_floor1_shell_excitation_relax,
            check_floor1_pm_coarse_dipole,
            check_floor1_leftovers_close,
            check_floor1_C3_gamma_close,
            check_floor1_C3_bath_dogfood,
            check_floor1_two_body_nn,
            check_floor1_n_body_chain,
        ),
        ship=True,
    ),
    "alpha": VerifySuiteSpec(
        id="alpha",
        description="α registry, bridges, Coulomb M-native.",
        check_names=_names(
            check_alpha_hop_ladder,
            check_alpha_fixed_point,
            check_alpha_force_lattice,
            check_alpha_meaning,
            check_alpha_descent,
            check_alpha_mass_defect_optics,
            check_alpha_arg_binding_try,
            check_alpha_schwinger,
            check_alpha_dirac_g2,
            check_alpha_ae_cloud,
            check_alpha_rydberg_hall,
            check_alpha_em_face_weight,
            check_alpha_dual_fraction,
            check_alpha_sqrt2_descent,
            check_alpha_M_from_g_try,
            check_alpha_nF_momentum_registry,
            check_alpha_full_quantization_bridge,
            check_coulomb_M_native,
            check_alpha_U0_soft_face,
            check_alpha_upstairs_mass_probe,
            check_alpha_si_bridge,
            check_alpha_meter_na0_bridge,
            check_alpha_bridges,
        ),
        ship=True,
    ),
    "units": VerifySuiteSpec(
        id="units",
        description="SI ladder, N_a0 carriers, meter decoupling.",
        check_names=_names(
            check_na0_from_carrier,
            check_na0_h_carrier,
            check_meter_decouple_from_M,
            check_length_dim_from_lP_alpha,
            check_time_dim_from_tP,
            check_units_time_first_cascade,
            check_planck_temperature_independent,
        ),
        ship=True,
    ),
    "carrier": VerifySuiteSpec(
        id="carrier",
        description="Geometry, carrier torus, planck-cell bit budget, vacuum bath.",
        check_names=_names(
            check_carrier_torus_close,
            check_gpu_eng_tail_close,
            check_bubble_tick,
            check_planck_cell_bit_budget,
            check_congruence_ladder,
            check_internal_phase_coords,
            check_rho_P_binary,
            check_vdw_algebra,
            check_arg_quantum,
            check_vacuum_bath,
            check_cuboctahedron_geometry,
            check_cuboctahedron_carrier,
            check_rhombic_dodecahedron_geometry,
            check_rhombic_dodecahedron_carrier,
            check_kappa_bottom_up,
            check_planck_from_cell_conditions,
            check_anchor_a_is_l_P,
            check_discreteness_from_axioms,
            check_mechanics_from_axioms,
            check_excitations_full_quantization,
            check_phonon_from_carrier,
            check_square_face_holonomy_probe,
        ),
        ship=True,
    ),
    "sm": VerifySuiteSpec(
        id="sm",
        description="Mass rows, Compton, mechanical quanta.",
        check_names=_names(
            check_compton_electron,
            check_higgs_mass,
            check_proton_mass,
            check_electron_mass,
            check_neutron_mass,
            check_annihilation_t_stats,
            check_annihilation_m_t_bundle,
            check_annihilation_pdg_tau_bridge,
            check_annihilation_pdg_tau_strict,
            check_neutrino_mass,
            check_mechanical_quantum,
            check_quarter_quantum,
            check_energy_quantum,
            check_elementary_quanta,
            check_electron_anchor,
            check_saturation_bc,
        ),
        ship=True,
    ),
    "instruments": VerifySuiteSpec(
        id="instruments",
        description="lab.open / panel scenarios (§5 instruments).",
        check_names=_names(
            check_planckon_instrument_fcc,
            check_instrument_panel_vortex,
            check_instrument_panel_2p1,
            check_instrument_scales_ladder,
            check_instrument_scales_time_first,
        ),
        ship=True,
    ),
    "cosmology": VerifySuiteSpec(
        id="cosmology",
        description="ISM screen v0 (blanket T-layer).",
        check_names=_names(check_ism_screen_v0),
        ship=False,
    ),
}

SUITE_ORDER: tuple[str, ...] = tuple(VERIFY_SUITES.keys())

SHIP_SUITE_IDS: tuple[str, ...] = tuple(sid for sid in SUITE_ORDER if VERIFY_SUITES[sid].ship)


def get_suite(suite_id: str) -> VerifySuiteSpec:
    if suite_id not in VERIFY_SUITES:
        raise KeyError(f"Unknown verify suite '{suite_id}'. Known: {sorted(VERIFY_SUITES)}")
    return VERIFY_SUITES[suite_id]


def order_suite_ids(suite_ids: Sequence[str]) -> tuple[str, ...]:
    """Dedupe and sort by SUITE_ORDER (for --scenario unions)."""
    rank = {s: i for i, s in enumerate(SUITE_ORDER)}
    seen: set[str] = set()
    ordered: list[str] = []
    for sid in suite_ids:
        get_suite(sid)
        if sid not in seen:
            seen.add(sid)
            ordered.append(sid)
    ordered.sort(key=lambda s: rank[s])
    return tuple(ordered)


def _check_registry() -> dict[str, Callable[..., dict]]:
    import sys

    mod = sys.modules[__name__]
    out: dict[str, Callable[..., dict]] = {}
    for name in dir(mod):
        if not name.startswith("check_"):
            continue
        fn = getattr(mod, name)
        if callable(fn):
            out[name] = fn
    return out


_CHECK_REGISTRY: dict[str, Callable[..., dict]] | None = None


def check_registry() -> dict[str, Callable[..., dict]]:
    global _CHECK_REGISTRY
    if _CHECK_REGISTRY is None:
        _CHECK_REGISTRY = _check_registry()
    return _CHECK_REGISTRY


def iter_suite_checks(suite_ids: Sequence[str]) -> Iterator[tuple[str, Callable[..., dict]]]:
    reg = check_registry()
    for sid in suite_ids:
        spec = get_suite(sid)
        for name in spec.check_names:
            if name not in reg:
                raise KeyError(f"Suite {sid}: missing check {name}")
            yield sid, reg[name]


def _invoke_check(fn: Callable[..., dict], device: str) -> dict:
    params = inspect.signature(fn).parameters
    if "device" in params:
        return fn(device=device)
    return fn()


def run_suites(device: str, suite_ids: Sequence[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for sid, fn in iter_suite_checks(suite_ids):
        row = _invoke_check(fn, device)
        row = dict(row)
        row["suite"] = sid
        rows.append(row)
    return rows


def run_all(device: str) -> list[dict[str, Any]]:
    return run_suites(device, SUITE_ORDER)


def run_ship(device: str) -> list[dict[str, Any]]:
    return run_suites(device, SHIP_SUITE_IDS)


def failed_rows(rows: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        r
        for r in rows
        if not r.get("ok")
        and r.get("id") not in WAIVE_EXIT_IDS
    ]
