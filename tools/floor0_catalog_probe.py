"""Recompute floor-0 internal catalog numbers (§5.0.4-A).

Usage:
  python tools/floor0_catalog_probe.py
  python tools/floor0_catalog_probe.py --bloch-only
"""
from __future__ import annotations

import argparse

import numpy as np
import torch

from mt_ca.fixed_point import decode_spinor
from mt_ca.si_constants import SI
from mt_ca.spinor import bloch_vector


def count_bloch_q_grid(frac_bits: int = 6) -> int:
    """Distinct Bloch directions from non-zero Q(frac_bits) spinor lanes."""
    levels = np.arange(-(1 << frac_bits) // 2, (1 << frac_bits) // 2, dtype=np.int32)
    blochs: set[tuple[int, int, int]] = set()
    chunk = 4096
    vals = list(levels)
    length = len(vals)
    for ia in range(0, length, chunk):
        a = np.array(vals[ia : ia + chunk], dtype=np.int32)
        for ib in range(0, length, chunk):
            b = np.array(vals[ib : ib + chunk], dtype=np.int32)
            for ic in range(0, length, chunk):
                c = np.array(vals[ic : ic + chunk], dtype=np.int32)
                for id_ in range(0, length, chunk):
                    d = np.array(vals[id_ : id_ + chunk], dtype=np.int32)
                    aa, bb, cc, dd = np.meshgrid(a, b, c, d, indexing="ij")
                    f = torch.stack(
                        [
                            torch.from_numpy(aa.reshape(-1)),
                            torch.from_numpy(bb.reshape(-1)),
                            torch.from_numpy(cc.reshape(-1)),
                            torch.from_numpy(dd.reshape(-1)),
                        ],
                        dim=-1,
                    )
                    z = decode_spinor(f, frac_bits=frac_bits)
                    mag = z.abs().square().sum(dim=-1)
                    mask = mag > 1e-20
                    if not bool(mask.any().item()):
                        continue
                    bv = bloch_vector(z[mask])
                    keys = tuple(map(tuple, torch.round(bv * 1e5).int().tolist()))
                    blochs.update(keys)
    return len(blochs)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bloch-only", action="store_true")
    parser.add_argument("--phase-space", action="store_true")
    parser.add_argument("--excitation", action="store_true")
    parser.add_argument("--selection", action="store_true")
    parser.add_argument("--gamma-table", action="store_true")
    parser.add_argument("--frac-bits", type=int, default=6)
    args = parser.parse_args()

    if args.gamma_table:
        row = SI.floor0_gamma_V_row()
        for key in (
            "habitat",
            "orbit_unique",
            "ground_branch_rows",
            "excited_branch_rows",
            "excited_n_E_values",
            "orbit_within_cap",
            "table_rows_total",
            "full_table_closed",
            "checks_ok",
        ):
            print(f"{key}: {row[key]}")
        return

    if args.bloch_only:
        n = count_bloch_q_grid(frac_bits=args.frac_bits)
        print(f"bloch_distinct_q{args.frac_bits} = {n}")
        return

    if args.phase_space:
        row = SI.floor0_phase_space_row()
        print(f"habitat: {row['habitat']}")
        for key in (
            "ocean_contrast_grows",
            "planckon_iteration_unique",
            "planckon_nonzero_impulses",
            "bekenstein_cap_states",
            "naive_q_times_p",
        ):
            print(f"{key}: {row[key]}")
        print("planckon_core:", row["planckon_core"])
        print("bath_brick:", row["bath_brick"])
        return

    if args.selection:
        row = SI.floor0_selection_row()
        for key in (
            "habitat",
            "planckon_samples",
            "violation_total",
            "n_E_peak_core",
            "checks_ok",
        ):
            print(f"{key}: {row[key]}")
        print("violations:", row["violations"])
        print("transition_stats:", row["transition_stats"])
        return

    if args.excitation:
        row = SI.floor0_nE_excitation_row()
        for key in (
            "habitat",
            "n_E_peak_core",
            "phi_ticks_peak_core",
            "peak_tick",
            "hits_planckon",
            "checks_ok",
        ):
            print(f"{key}: {row[key]}")
        print("first_hit:", row["first_hit"])
        return

    row = SI.internal_state_catalog_row()
    for key in (
        "phase_states",
        "n_E_classes",
        "amplitude_levels",
        "q_grid_spinor_configs",
        "bloch_distinct_q6",
        "bekenstein_cap_states",
        "naive_phase_times_n_E",
        "cap_binds_registers",
    ):
        print(f"{key}: {row[key]}")
    print("tiers:", [t["id"] for t in row["tiers"]])


if __name__ == "__main__":
    main()
