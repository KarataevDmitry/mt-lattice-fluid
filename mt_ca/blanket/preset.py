"""Blanket presets — SSOT for second surface over boil ocean."""

from __future__ import annotations

from enum import Enum


class BlanketPreset(str, Enum):
    """What sits above the settled ocean interface (not a habitat swap)."""

    NONE = "none"
    """Ocean only — no МЗВ overlay."""

    HOMOGENEOUS_MZW = "homogeneous_mzw"
    """Uniform τ, layered exp attenuation; T readout via WNM Γ=Λ + ℬ ripple."""
