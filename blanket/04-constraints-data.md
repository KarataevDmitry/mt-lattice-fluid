# §4 · Ограничения и данные

### §4.0 · Файлы

`data/ism_constraints_v0.yaml` и зеркало `.json`, схема `ism_constraints/v2`.

Загрузчик: `load_ism_constraints()`.

### §4.1 · Блоки

| ключ | назначение |
|------|------------|
| `geometry` | AU, pc |
| `lic` | `n_H`, `T_K_warm_nominal` — сравнение с наблюдением |
| `vlism_voyager_v1` | якорь τ, VLISM |
| `column_screen` | $N_H$, $\sigma_{\mathrm{eff}}$ |
| `model_v1` | связь с полем, ионизация, Y_He |
| `wnm_thermal` | путь к JSON, режим равновесия |
| `pass_blanket` | диапазон T, допуск к LIC |

### §4.2 · yaml и json

При изменении yaml обновлять json.

### §4.3 · Критерии

- `ok_T_ISM_scale` — медиана в `T_lic_K_range`.
- `ok_match_LIC_observation` — относительное отклонение от `T_K_warm_nominal`.
