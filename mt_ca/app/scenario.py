"""Named scenarios — SSOT for conditions (habitat + seed), not grid embedding."""
from __future__ import annotations

from dataclasses import dataclass

from mt_ca.app.brick import BrickSpec
from mt_ca.app.habitat import HabitatPreset
from mt_ca.blanket.preset import BlanketPreset
from mt_ca.seeds import SeedClass


@dataclass(frozen=True, slots=True)
class ScenarioSpec:
    """Initial conditions + habitat — same object in any embedding dimension."""

    id: str
    seed: SeedClass
    habitat: HabitatPreset
    brick: BrickSpec | None = None
    impulse_amplitude: float = 0.35
    description: str = ""
    blanket: BlanketPreset = BlanketPreset.NONE
    blanket_thickness: int = 6

    @property
    def habitat_label(self) -> str:
        return self.habitat.value


SCENARIOS: dict[str, ScenarioSpec] = {
    "habitat_boil": ScenarioSpec(
        id="habitat_boil",
        seed=SeedClass.VACUUM_BOIL,
        habitat=HabitatPreset.VACUUM_BOIL,
        description="Filled boiling ocean (A5).",
    ),
    "habitat_frozen": ScenarioSpec(
        id="habitat_frozen",
        seed=SeedClass.VACUUM,
        habitat=HabitatPreset.VACUUM_FROZEN,
        description="Gauge-fixed frozen vacuum — control.",
    ),
    "floor0_planckon": ScenarioSpec(
        id="floor0_planckon",
        seed=SeedClass.VORTEX_P,
        habitat=HabitatPreset.VACUUM_BOIL,
        description="Planckon vortex on boiling ocean (§5.0.4-A).",
    ),
    "birth_impulse": ScenarioSpec(
        id="birth_impulse",
        seed=SeedClass.IMPULSE,
        habitat=HabitatPreset.VACUUM_BOIL,
        description="Impulse on boil — birth candidate.",
    ),
    "birth_plane_wave": ScenarioSpec(
        id="birth_plane_wave",
        seed=SeedClass.PLANE_WAVE,
        habitat=HabitatPreset.VACUUM_BOIL,
        description="Plane-wave packet on boil.",
    ),
    "filled_bath_emergence": ScenarioSpec(
        id="filled_bath_emergence",
        seed=SeedClass.VACUUM_BOIL,
        habitat=HabitatPreset.VACUUM_BOIL,
        description="Multi-arm bath emergence dogfood (§6 C3).",
    ),
    "ocean_ism_blanket": ScenarioSpec(
        id="ocean_ism_blanket",
        seed=SeedClass.VACUUM_BOIL,
        habitat=HabitatPreset.VACUUM_BOIL,
        blanket=BlanketPreset.HOMOGENEOUS_MZW,
        blanket_thickness=6,
        description="Boil ocean + homogeneous МЗВ blanket (BLANKET.md).",
    ),
}


def get_scenario(scenario_id: str) -> ScenarioSpec:
    if scenario_id not in SCENARIOS:
        raise KeyError(f"Unknown scenario '{scenario_id}'. Known: {sorted(SCENARIOS)}")
    return SCENARIOS[scenario_id]


_SEED_TO_SCENARIO: dict[SeedClass, str] = {
    SeedClass.VACUUM_BOIL: "habitat_boil",
    SeedClass.VACUUM: "habitat_frozen",
    SeedClass.VORTEX_P: "floor0_planckon",
    SeedClass.VORTEX_M: "floor0_planckon",
    SeedClass.VORTEX_N2: "floor0_planckon",
    SeedClass.IMPULSE: "birth_impulse",
    SeedClass.PLANE_WAVE: "birth_plane_wave",
}


def scenario_for_seed(seed: SeedClass) -> ScenarioSpec:
    if seed in _SEED_TO_SCENARIO:
        registered = get_scenario(_SEED_TO_SCENARIO[seed])
        if registered.seed is seed:
            return registered
        return ScenarioSpec(
            id=seed.value,
            seed=seed,
            habitat=HabitatPreset.VACUUM_BOIL,
            description=f"{seed.value} on boiling ocean",
        )
    return ScenarioSpec(
        id=seed.value,
        seed=seed,
        habitat=HabitatPreset.VACUUM_BOIL,
        description=f"{seed.value} on boiling ocean",
    )
