# §3 · WNM thermal balance (table SSOT)

### §3.0 · Default (2026)

**Lineage:** [Ploeckinger & Schaye 2020](https://radcool.strw.leidenuniv.nl/) fiducial `UVB_dust1_CR1_G1_shield1` (Cloudy v17.01, mod. FG20 UVB). **Hybrid-CHIMES** (Ploeckinger et al. 2025, MNRAS) uses the **same HDF5 layout** — swap source file and re-run build when their tables ship.

**Repo JSON:** `data/wnm_cooling_ps20_fiducial_z0_v1.json` (generated, ~0.5 MB).

**No `cooling_scale`.** No `T_LIC` in the solver.

### §3.1 · Build from HDF5 (operator)

1. Download `UVB_dust1_CR1_G1_shield1.hdf5` (Harvard Dataverse file id **3985215** or [radcool](https://radcool.strw.leidenuniv.nl/)).
2. Place at `data/_cache/UVB_dust1_CR1_G1_shield1.hdf5` (gitignored).
3. Run:

```bash
python scripts/build_wnm_cooling_table.py
```

### §3.2 · Solver

- Interpolate **log10(Λ_heat/n_H²)**, **log10(Λ_cool/n_H²)** on (log n_H, log T).
- **`equilibrium_mode: wnm_ridge`:** max WNM root (T ≥ 4000 K) at LIC `n_H`; if PS20 has no hot root at that density (cold stable branch), use **`wnm_reference_log_nH: -2.85`** where the table’s upper WNM branch crosses ~7×10³ K.
- Readout **`n_e`**, **`T_eq` map** still use **LIC `n_H`** for amplitude; balance diagnostics at the density where the root was found.

### §3.3 · Impl

- `mt_ca.blanket.cooling_table` — load + interpolate JSON
- `mt_ca.blanket.wnm.wnm_equilibrium_T_K` — bisection on table net rate

### §3.4 · OPEN

Replace HDF5 with **Hybrid-CHIMES 2025** tables when published on [hybridchimes](https://www.sylviaploeckinger.com/hybridchimes); keep JSON schema, bump `schema` tag.
