"""M/T instrument catalog, scales (nat→SI), and lab panels (§5.0–§5.2)."""
from mt_ca.instruments.catalog import REGISTRY, InstrumentId, InstrumentSpec, instrument_index
from mt_ca.instruments.panel import PANEL_SCHEMA, sample_field, sample_panel, sample_site
from mt_ca.instruments.scales import QuantityKind, ScaledReading, reading, scale_spec
from mt_ca.instruments.time_first_ladder import TimeFirstInstrumentLadder, instrument_ladder
from mt_ca.instruments.t_panel import T_PANEL_SCHEMA, sample_t_field

__all__ = [
    "PANEL_SCHEMA",
    "T_PANEL_SCHEMA",
    "REGISTRY",
    "InstrumentId",
    "InstrumentSpec",
    "QuantityKind",
    "ScaledReading",
    "instrument_index",
    "reading",
    "scale_spec",
    "sample_field",
    "sample_panel",
    "sample_site",
    "sample_t_field",
    "TimeFirstInstrumentLadder",
    "instrument_ladder",
]
