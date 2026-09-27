"""Lattice embedding — coordinate dimension of the run (independent of scenario IC).

Scenario = *conditions* (habitat, seed, …). The same excitation (e.g. planckon)
can be simulated on a 2+1 slice or a 3+1 volume; only the embedding of the
coordinate vector changes what we *see*, not the object identity.
"""
from __future__ import annotations

from enum import Enum

from mt_ca.app.neighbor_template import (
    CANON_NEIGHBOR_TEMPLATE,
    SLICE_NEIGHBOR_TEMPLATE,
)


class LatticeDimension(str, Enum):
    """Simulator embedding — size of the spatial grid, not the physical scenario."""

    VOLUME_3P1 = "3+1"
    """FCC cuboid (nz, ny, nx)."""

    SLICE_2P1 = "2+1"
    """Hex torus (ny, nx) — lower-dimensional embedding of the same local g."""


def neighbor_template_for_dimension(dim: LatticeDimension) -> str:
    return (
        CANON_NEIGHBOR_TEMPLATE
        if dim is LatticeDimension.VOLUME_3P1
        else SLICE_NEIGHBOR_TEMPLATE
    )


def dimension_for_neighbor_template(neighbor_template: str) -> LatticeDimension:
    if neighbor_template == CANON_NEIGHBOR_TEMPLATE:
        return LatticeDimension.VOLUME_3P1
    if neighbor_template == SLICE_NEIGHBOR_TEMPLATE:
        return LatticeDimension.SLICE_2P1
    raise ValueError(f"Неизвестный шаблон соседства: {neighbor_template!r}")


# Совместимость
neighbor_scheme_for_dimension = neighbor_template_for_dimension
dimension_for_neighbor_scheme = dimension_for_neighbor_template
stencil_for_dimension = neighbor_template_for_dimension
dimension_for_stencil = dimension_for_neighbor_template


def nz_for_dimension(dim: LatticeDimension, edge: int) -> int | None:
    return edge if dim is LatticeDimension.VOLUME_3P1 else None


def grid_shape_label(dim: LatticeDimension, edge: int) -> str:
    return f"{edge}³" if dim is LatticeDimension.VOLUME_3P1 else f"{edge}²"
