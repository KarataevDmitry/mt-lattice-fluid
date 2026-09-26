# §4 · Data constraints

### §4.0 · Файлы

**SSOT чисел:** `data/ism_constraints_v0.yaml` (primary) и зеркало `data/ism_constraints_v0.json`.

Schema tag: `ism_constraints/v2`.

Loader: `mt_ca.blanket.constraints.load_ism_constraints()`.

### §4.1 · Блоки

| ключ | назначение |
|------|------------|
| `geometry` | AU, pc — перевод r_au → pc |
| `lic` | `n_H_cm3_nominal`, ranges; `T_K_warm_nominal` — **obs compare only** |
| `vlism_voyager_v1` | якорь τ, magnetothermal VLISM (forward harness) |
| `column_screen` | segments $N_H$, $\sigma_{\mathrm{eff}}$ |
| `model_v1` | thermal_coupling, ionization caps, Y_He |
| `wnm_thermal` | table JSON path, `equilibrium_mode`, `wnm_reference_log_nH` |
| `pass_blanket` | T range, tolerance vs LIC obs |

### §4.2 · Sync yaml ↔ json

При изменении yaml обновлять json (или regenerate в CI) — один SSOT, два формата для tooling.

### §4.3 · Pass blanket

- `ok_T_ISM_scale`: median в `T_lic_K_range`.
- `ok_match_LIC_observation`: rel median vs `T_K_warm_nominal` ≤ tolerance.

Hypothesis flag в dogfood: scale pass; obs match — отдельная строка отчёта.
