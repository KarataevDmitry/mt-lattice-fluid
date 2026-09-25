"""Habitat presets — live simulation substrate (§0.5 · A5)."""
from __future__ import annotations

from enum import Enum


class HabitatPreset(str, Enum):
    """SSOT for what fills the lattice before excitations."""

    VACUUM_BOIL = "vacuum_boil"
    """Every hV filled; NN Δclass = Δφ_min — default live habitat."""

    VACUUM_FROZEN = "vacuum_frozen"
    """Gauge-fixed class 0 (Φ=0) — control only, not live physics."""

    @property
    def is_live(self) -> bool:
        return self is HabitatPreset.VACUUM_BOIL
