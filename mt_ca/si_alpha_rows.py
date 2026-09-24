"""α ask/row mixins — facade over probe/thm/soft splits."""
from __future__ import annotations

from mt_ca.si_alpha_probe_rows import SIAlphaProbeRows
from mt_ca.si_alpha_soft_rows import SIAlphaSoftRows
from mt_ca.si_alpha_thm_rows import SIAlphaThmRows


class SIAlphaRows(SIAlphaProbeRows, SIAlphaThmRows, SIAlphaSoftRows):
    """Combined α rows for SIConstants MRO."""

