"""T bounded context loads (DDD)."""

from __future__ import annotations


def test_t_hydro_limit_row() -> None:
    from mt_ca.t.hydro_limit import hydro_limit_verify_row

    row = hydro_limit_verify_row()
    assert row["path_atom_is_121"] is True
    assert row["fcc_n_nn"] == 12


def test_t_coarse_reexport() -> None:
    from mt_ca.t.coarse import macro_amplitude

    assert callable(macro_amplitude)
