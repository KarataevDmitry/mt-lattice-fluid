"""Bounded context **T** — макроописание поверх M (§4 MODEL).

Submodules: coarse, spectral, hydro_limit, validation, anchors.
Плоские `macro.py` / `t_analysis.py` / `t_validation.py` — ещё физические файлы; импорт наружу через `mt_ca.t.*`.
"""

from mt_ca.t import anchors, coarse, hydro_limit, spectral, validation

__all__ = [
    "anchors",
    "coarse",
    "hydro_limit",
    "spectral",
    "validation",
]
