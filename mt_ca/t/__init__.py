"""Bounded context **T** — макроописание поверх M (§4 MODEL).

Packages:
  coarse      — binomial |Φ|, §4.1.1
  spectral    — DFT / dispersion calibration
  hydro_limit — T-CR, path-Green, §4.1.0–§4.1.1-HL
  validation  — T1/T2/T3 self-checks
  anchors     — SI anchor rows (§5)

Legacy flat modules (`macro.py`, `t_analysis.py`, …) remain as shims during migration.
"""

from mt_ca.t import anchors, coarse, hydro_limit, spectral, validation

__all__ = [
    "anchors",
    "coarse",
    "hydro_limit",
    "spectral",
    "validation",
]
