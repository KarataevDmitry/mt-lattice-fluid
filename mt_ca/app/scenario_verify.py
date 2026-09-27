"""Scenario → verify suite ids (shared vocabulary with verify_principles.py)."""

from __future__ import annotations

from mt_ca.app.scenario import SCENARIOS, ScenarioSpec, get_scenario


def verify_suite_ids_for_scenario(scenario_id: str) -> tuple[str, ...]:
    return get_scenario(scenario_id).verify_suites


def verify_suite_ids_for_scenarios(scenario_ids: list[str]) -> tuple[str, ...]:
    """Union of per-scenario suites (order = first seen while scanning scenarios)."""
    seen: set[str] = set()
    ordered: list[str] = []
    for sid in scenario_ids:
        for suite in verify_suite_ids_for_scenario(sid):
            if suite not in seen:
                seen.add(suite)
                ordered.append(suite)
    return tuple(ordered)


def list_scenarios_with_verify() -> list[ScenarioSpec]:
    return [SCENARIOS[k] for k in sorted(SCENARIOS)]
