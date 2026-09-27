"""Verify suite SSOT — same pattern as mt_ca.app.scenario."""

from __future__ import annotations

from verify_checks.suites import SUITE_ORDER, VERIFY_SUITES, check_registry, iter_suite_checks


def test_every_suite_check_resolves() -> None:
    reg = check_registry()
    for sid in SUITE_ORDER:
        spec = VERIFY_SUITES[sid]
        assert spec.id == sid
        for name in spec.check_names:
            assert name in reg


def test_no_duplicate_checks_across_suites() -> None:
    seen: set[str] = set()
    for _, fn in iter_suite_checks(SUITE_ORDER):
        name = fn.__name__
        assert name not in seen
        seen.add(name)


def test_ship_excludes_evolution_open() -> None:
    from verify_checks.suites import SHIP_SUITE_IDS

    assert "m_evolution_open" not in SHIP_SUITE_IDS
    assert "gate" in SHIP_SUITE_IDS
    assert "t_macro" in SHIP_SUITE_IDS


def test_scenario_verify_suites_resolve() -> None:
    from mt_ca.app.scenario import SCENARIOS
    from verify_checks.suites import get_suite

    for spec in SCENARIOS.values():
        assert spec.verify_suites
        for suite_id in spec.verify_suites:
            get_suite(suite_id)


def test_floor0_planckon_verify_profile() -> None:
    from mt_ca.app.scenario_verify import verify_suite_ids_for_scenario

    assert verify_suite_ids_for_scenario("floor0_planckon") == (
        "gate",
        "floor0",
        "instruments",
    )
