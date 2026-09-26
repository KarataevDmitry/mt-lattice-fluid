#!/usr/bin/env python3
"""Export PS20 fiducial z=0 cooling/heating slice to repo JSON (Hybrid-CHIMES 2025 same HDF5 layout).

Place the Harvard Dataverse file at:
  data/_cache/UVB_dust1_CR1_G1_shield1.hdf5
Download: https://dataverse.harvard.edu/api/access/datafile/3985215
(or radcool.strw.leidenuniv.nl — model UVB_dust1_CR1_G1_shield1)

Hybrid-CHIMES (Ploeckinger et al. 2025) tables use the same format; swap HDF5 and re-run.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import h5py
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_HDF5 = ROOT / "data" / "_cache" / "UVB_dust1_CR1_G1_shield1.hdf5"
DEFAULT_OUT = ROOT / "data" / "wnm_cooling_ps20_fiducial_z0_v1.json"


def _total_log_per_nh2(cool_row: np.ndarray, heat_row: np.ndarray) -> tuple[float, float]:
    lc = np.power(10.0, cool_row[..., -2]) + np.power(10.0, cool_row[..., -1])
    lh = np.power(10.0, heat_row[..., -2]) + np.power(10.0, heat_row[..., -1])
    return np.log10(lh), np.log10(lc)


def build(hdf5_path: Path, out_path: Path) -> dict:
    with h5py.File(hdf5_path, "r") as f:
        z_bins = f["TableBins/RedshiftBins"][()]
        met_bins = f["TableBins/MetallicityBins"][()]
        t_bins = f["TableBins/TemperatureBins"][()]
        n_bins = f["TableBins/DensityBins"][()]
        iz = int(np.argmin(np.abs(z_bins - 0.0)))
        im = int(np.argmin(np.abs(met_bins - 0.0)))
        cool = f["Tdep/Cooling"][iz, :, im, :, :]
        heat = f["Tdep/Heating"][iz, :, im, :, :]
        ne = f["Tdep/ElectronFractions"][iz, :, im, :, -1]

        n_n = len(n_bins)
        n_t = len(t_bins)
        log_heat = [[0.0] * n_t for _ in range(n_n)]
        log_cool = [[0.0] * n_t for _ in range(n_n)]
        log_ne = [[0.0] * n_t for _ in range(n_n)]
        for i in range(n_n):
            for j in range(n_t):
                lh, lc = _total_log_per_nh2(cool[j, i, :], heat[j, i, :])
                log_heat[i][j] = float(lh)
                log_cool[i][j] = float(lc)
                log_ne[i][j] = float(ne[j, i])

    payload = {
        "schema": "wnm_cooling/ps20_fiducial_z0_v1",
        "lineage": "hybrid_chimes_2025_compatible",
        "source_hdf5": "UVB_dust1_CR1_G1_shield1.hdf5",
        "references": [
            "Ploeckinger & Schaye 2020 (Cloudy v17.01, mod. FG20 UVB)",
            "Ploeckinger et al. 2025 Hybrid-CHIMES (same table format)",
        ],
        "model": "UVB_dust1_CR1_G1_shield1",
        "redshift": float(z_bins[iz]),
        "log10_metallicity_Z_over_Zsun": float(met_bins[im]),
        "units": {
            "log10_n_H": "log10 cm^-3",
            "log10_T": "log10 K",
            "log10_heating_per_nH2": "log10 erg cm^3 s^-1 per n_H^2",
            "log10_cooling_per_nH2": "log10 erg cm^3 s^-1 per n_H^2",
            "log10_ne_over_nH": "log10 n_e/n_H",
        },
        "log10_n_H": [float(x) for x in n_bins],
        "log10_T": [float(x) for x in t_bins],
        "log10_heating_per_nH2": log_heat,
        "log10_cooling_per_nH2": log_cool,
        "log10_ne_over_nH": log_ne,
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as fp:
        json.dump(payload, fp, indent=2)
    return payload


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--hdf5", type=Path, default=DEFAULT_HDF5)
    p.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = p.parse_args()
    if not args.hdf5.is_file():
        print(f"Missing HDF5: {args.hdf5}", file=sys.stderr)
        print("Download UVB_dust1_CR1_G1_shield1.hdf5 into data/_cache/ then re-run.", file=sys.stderr)
        return 1
    build(args.hdf5, args.out)
    print(f"Wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
