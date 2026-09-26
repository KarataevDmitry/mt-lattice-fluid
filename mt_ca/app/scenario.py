"""Named simulation scenarios — SSOT for IC + habitat."""

from __future__ import annotations



from dataclasses import dataclass



from mt_ca.app.brick import BrickSpec

from mt_ca.app.stencil import CANON_STENCIL, SLICE_STENCIL

from mt_ca.app.habitat import HabitatPreset

from mt_ca.seeds import SeedClass





@dataclass(frozen=True, slots=True)

class ScenarioSpec:

    """One reproducible simulation setup."""



    id: str

    seed: SeedClass

    habitat: HabitatPreset

    stencil: str = CANON_STENCIL

    brick: BrickSpec | None = None

    impulse_amplitude: float = 0.35

    description: str = ""



    @property

    def habitat_label(self) -> str:

        return self.habitat.value





SCENARIOS: dict[str, ScenarioSpec] = {

    "habitat_boil": ScenarioSpec(

        id="habitat_boil",

        seed=SeedClass.VACUUM_BOIL,

        habitat=HabitatPreset.VACUUM_BOIL,

        stencil=CANON_STENCIL,

        description="Filled boiling ocean (3+1 FCC, A5).",

    ),

    "habitat_frozen": ScenarioSpec(

        id="habitat_frozen",

        seed=SeedClass.VACUUM,

        habitat=HabitatPreset.VACUUM_FROZEN,

        stencil=CANON_STENCIL,

        description="Gauge-fixed frozen vacuum — control (FCC).",

    ),

    "floor0_planckon": ScenarioSpec(

        id="floor0_planckon",

        seed=SeedClass.VORTEX_P,

        habitat=HabitatPreset.VACUUM_BOIL,

        stencil=CANON_STENCIL,

        description="Planckon vortex on boiling ocean (§5.0.4-A, 3+1 FCC).",

    ),

    "birth_impulse": ScenarioSpec(

        id="birth_impulse",

        seed=SeedClass.IMPULSE,

        habitat=HabitatPreset.VACUUM_BOIL,

        stencil=CANON_STENCIL,

        description="Impulse on boil — birth candidate (FCC).",

    ),

    "birth_plane_wave": ScenarioSpec(

        id="birth_plane_wave",

        seed=SeedClass.PLANE_WAVE,

        habitat=HabitatPreset.VACUUM_BOIL,

        stencil=CANON_STENCIL,

        description="Plane-wave packet on boil (FCC).",

    ),

    "filled_bath_emergence": ScenarioSpec(

        id="filled_bath_emergence",

        seed=SeedClass.VACUUM_BOIL,

        habitat=HabitatPreset.VACUUM_BOIL,

        stencil=CANON_STENCIL,

        description="Multi-arm bath emergence dogfood (§6 C3, FCC).",

    ),

    "floor0_planckon_hex_slice": ScenarioSpec(

        id="floor0_planckon_hex_slice",

        seed=SeedClass.VORTEX_P,

        habitat=HabitatPreset.VACUUM_BOIL,

        stencil=SLICE_STENCIL,

        description="2+1 hex slice only — legacy/dogfood, not cosmology SSOT.",

    ),

    "habitat_boil_hex_slice": ScenarioSpec(

        id="habitat_boil_hex_slice",

        seed=SeedClass.VACUUM_BOIL,

        habitat=HabitatPreset.VACUUM_BOIL,

        stencil=SLICE_STENCIL,

        description="2+1 hex boil slice — fixed-point control, not 3+1 dynamics.",

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

    """Map ``SeedClass`` to a scenario (registered id or inline on boil)."""

    if seed in _SEED_TO_SCENARIO:

        registered = get_scenario(_SEED_TO_SCENARIO[seed])

        if registered.seed is seed:

            return registered

        return ScenarioSpec(

            id=seed.value,

            seed=seed,

            habitat=HabitatPreset.VACUUM_BOIL,

            stencil=CANON_STENCIL,

            description=f"{seed.value} on boiling ocean (FCC)",

        )

    return ScenarioSpec(

        id=seed.value,

        seed=seed,

        habitat=HabitatPreset.VACUUM_BOIL,

        stencil=CANON_STENCIL,

        description=f"{seed.value} on boiling ocean (FCC)",

    )


