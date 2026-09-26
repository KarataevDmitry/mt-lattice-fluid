"""Lattice dimension SSOT — 3+1 volume vs 2+1 slice (not interchangeable dogfood)."""
from __future__ import annotations

from enum import Enum

from mt_ca.app.stencil import CANON_STENCIL, SLICE_STENCIL


class LatticeDimension(str, Enum):
    """How the simulator is embedded — drives nz and instrument readout."""

    VOLUME_3P1 = "3+1"
    """FCC cuboid (nz, ny, nx) — cosmology, boil ocean, planckon SSOT."""

    SLICE_2P1 = "2+1"
    """Hex torus (ny, nx) — explicit slice scenarios and component tests only."""


def dimension_for_stencil(stencil: str) -> LatticeDimension:
    if stencil == CANON_STENCIL:
        return LatticeDimension.VOLUME_3P1
    if stencil == SLICE_STENCIL:
        return LatticeDimension.SLICE_2P1
    raise ValueError(f"Unknown stencil {stencil!r}; expected {CANON_STENCIL!r} or {SLICE_STENCIL!r}")


def nz_for_dimension(dim: LatticeDimension, edge: int) -> int | None:
    return edge if dim is LatticeDimension.VOLUME_3P1 else None


def grid_shape_label(dim: LatticeDimension, edge: int) -> str:
    return f"{edge}³" if dim is LatticeDimension.VOLUME_3P1 else f"{edge}²"
