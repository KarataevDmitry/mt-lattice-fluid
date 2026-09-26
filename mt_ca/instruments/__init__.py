"""M/T instrument catalog and lab panel (§5.0–§5.2)."""
from mt_ca.instruments.catalog import REGISTRY, InstrumentId, InstrumentSpec, instrument_index
from mt_ca.instruments.panel import PANEL_SCHEMA, sample_field, sample_panel, sample_site

__all__ = [
    "PANEL_SCHEMA",
    "REGISTRY",
    "InstrumentId",
    "InstrumentSpec",
    "instrument_index",
    "sample_field",
    "sample_panel",
    "sample_site",
]
