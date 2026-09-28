"""FCC N₁₂ — совместимость класса фазы A5-boil с рёбрами каузальной звезды."""
from __future__ import annotations

from mt_ca.laplacian import _FCC_OFFSETS


def fcc_phase_step_mod_n_phi(
    dz: int,
    dy: int,
    dx: int,
    *,
    n_phi: int,
) -> set[int]:
    """Множество $|Δk \bmod N_\varphi|$ по всем 12 смещениям N₁₂."""
    steps: set[int] = set()
    for oz, oy, ox in _FCC_OFFSETS:
        dk = (dz * oz + dy * oy + dx * ox) % n_phi
        if dk > n_phi // 2:
            dk = n_phi - dk
        steps.add(dk)
    return steps


def fcc_boiling_ramp_ok(
    dz: int,
    dy: int,
    dx: int,
    *,
    n_phi: int = 13,
) -> bool:
    """True, если вдоль каждого ребра N₁₂ скачок класса — 0 или 1 тик (Гейзенберг)."""
    if (dz, dy, dx) == (0, 0, 0):
        return False
    return fcc_phase_step_mod_n_phi(dz, dy, dx, n_phi=n_phi) <= {0, 1}


def default_fcc_boiling_ramp() -> tuple[int, int, int]:
    """Канон 3+1: одноосный ramp (+x)."""
    return (0, 0, 1)
