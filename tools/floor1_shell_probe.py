"""Recompute §5.0.4-B outer-shell catalog numbers."""
from __future__ import annotations

from mt_ca.si_constants import SI


def main() -> None:
    row = SI.floor1_outer_shell_catalog_row()
    for key in (
        "shell2_sites",
        "shell3_sites",
        "cumulative_ball_k3",
        "elementary_excitations_shell23",
        "catalog_algebra_closed",
        "derivation_closed",
        "checks_ok",
    ):
        print(f"{key}: {row[key]}")


if __name__ == "__main__":
    main()
