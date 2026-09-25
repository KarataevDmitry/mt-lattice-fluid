"""Heisenberg-brick boil offsets on a filled lattice."""
from __future__ import annotations

from dataclasses import dataclass

from mt_ca.si_constants import HV


@dataclass(frozen=True, slots=True)
class BrickSpec:
    """phase_class(y,x) = (class_dy·y + class_dx·x + class_offset) mod N_φ."""

    class_dy: int = 1
    class_dx: int = 1
    class_offset: int = 0


def brick_axis_configs(n_phi: int | None = None) -> list[BrickSpec]:
    """Enumerate axis NN brick families (|dy|=|dx|=1) × offset mod N_φ."""
    n = HV.N_phi if n_phi is None else n_phi
    out: list[BrickSpec] = []
    for offset in range(n):
        for dy, dx in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
            out.append(BrickSpec(class_dy=dy, class_dx=dx, class_offset=offset))
    return out
