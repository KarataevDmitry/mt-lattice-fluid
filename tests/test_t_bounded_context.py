"""T bounded context loads (DDD)."""

from __future__ import annotations


def test_t_hydro_limit_row() -> None:
    from mt_ca.t.hydro_limit import hydro_limit_verify_row

    row = hydro_limit_verify_row()
    assert row["path_atom_is_121"] is True
    assert row["fcc_n_nn"] == 12


def test_classical_limit_sweep() -> None:
    from mt_ca.t.hydro_limit import classical_limit_sweep_row, phi_bz_readout_row

    row = classical_limit_sweep_row(device="cpu")
    assert row["checks_ok"] is True
    assert row["coarse_to_gaussian"] is True
    assert row["phi_readout_ok"] is True

    phi = phi_bz_readout_row(device="cpu")
    assert phi["phi_readout_ok"] is True


def test_t_coarse_reexport() -> None:
    from mt_ca.t.coarse import macro_amplitude

    assert callable(macro_amplitude)
