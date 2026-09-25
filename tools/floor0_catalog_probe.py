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
    parser.add_argument("--frac-bits", type=int, default=6)
    args = parser.parse_args()

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
            "planckon_nonzero_kicks",
            "bekenstein_cap_states",
            "naive_q_times_p",
        ):
            print(f"{key}: {row[key]}")
        print("planckon_core:", row["planckon_core"])
        print("bath_brick:", row["bath_brick"])
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
