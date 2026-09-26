# §3 · Тепловой баланс WNM

### §3.0 · Таблица (2026)

**Источник:** Ploeckinger & Schaye 2020, `UVB_dust1_CR1_G1_shield1`. Hybrid-CHIMES (2025) — тот же формат HDF5; при смене источника пересобрать JSON.

**Файл:** `data/wnm_cooling_ps20_fiducial_z0_v1.json`.

Без `cooling_scale`. $T_{\mathrm{LIC}}$ в решатель не подставляется.

### §3.1 · Сборка из HDF5

1. Скачать HDF5 (Dataverse **3985215**).
2. `data/_cache/UVB_dust1_CR1_G1_shield1.hdf5`.
3. `python scripts/build_wnm_cooling_table.py`

### §3.2 · Решение

- Интерполяция log Λ_heat, Λ_cool по (log n_H, log T).
- `equilibrium_mode: wnm_ridge` — верхний корень WNM; при отсутствии горячей ветви при LIC — `wnm_reference_log_nH: -2.85`.
- $n_e$, карта $T_{\mathrm{eq}}$: амплитуда при LIC `n_H`; баланс — при плотности корня.

### §3.3 · Код

`mt_ca.blanket.cooling_table`, `mt_ca.blanket.wnm.wnm_equilibrium_T_K`.

### §3.4 · Открыто

Таблицы Hybrid-CHIMES 2025 при публикации — та же схема JSON.
