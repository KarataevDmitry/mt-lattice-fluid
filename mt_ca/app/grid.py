"""Backward-compatible re-exports — prefer ``mt_ca.app.lattice``."""
from mt_ca.app.lattice import (  # noqa: F401
    CANON_STENCIL,
    SLICE_STENCIL,
    LatticeDimension,
    build_run_spec,
    describe_lattice,
    nz_for_scenario,
    open_lattice,
    open_simulator,
    run_spec_cube,
)

__all__ = [
    "CANON_STENCIL",
    "SLICE_STENCIL",
    "LatticeDimension",
    "build_run_spec",
    "describe_lattice",
    "nz_for_scenario",
    "open_lattice",
    "open_simulator",
    "run_spec_cube",
]
