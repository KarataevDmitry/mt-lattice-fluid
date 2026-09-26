"""Shim — SSOT: ``mt_ca.blanket.surface`` · see BLANKET.md."""

from mt_ca.blanket.surface import (
    apply_ism_blanket,
    blanket_distribution_report,
    ism_T_map_K,
    ism_temperature_report,
    macro_slice_stats,
    tau_map_ism_blanket,
    tau_uniform_ism_blanket,
)

__all__ = [
    "apply_ism_blanket",
    "blanket_distribution_report",
    "ism_T_map_K",
    "ism_temperature_report",
    "macro_slice_stats",
    "tau_map_ism_blanket",
    "tau_uniform_ism_blanket",
]
