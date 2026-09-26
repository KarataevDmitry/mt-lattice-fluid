# Одеяло МЗВ · вторая поверхность над океаном

**Океан (первая поверхность):** ST-ткань M-слоя (~$10^{31}$ K в log-масштабе T) — см. **`MODEL.md`**, [`model/`](model/), код **`mt_ca.app`** (`HabitatPreset.VACUUM_BOIL`, `habitat_boil`).

**Одеяло МЗВ (вторая поверхность):** однородная тёплая нейтральная среда поверх установившегося океана; **$T_{\mathrm{МЗВ}}\sim 10^3\,\mathrm{K}$** (LIC ~7000 K), **не** CMB (2.7 K), **не** подгонка «заполнить до T_LIC».

**Журнал разработки** → [`DEVLOG.md`](DEVLOG.md) — не меняет утверждения ниже.

### Структура документации

```
гипотеза, баланс Γ=Λ  →  BLANKET.md + blanket/*.md
                              ↓
                         data/ism_constraints_v0.yaml
                              ↓
                         mt_ca/blanket/
                              ↓
                         скрипты, верификация (может отставать)
```

### MODEL · одеяло · META

| | **MODEL** | **BLANKET** | **META** |
|---|-----------|-------------|----------|
| Роль | SSOT **`g`**, M→T | SSOT **МЗВ на океане** | космология над макро-T |
| Температура | $T_M$, усреднение | $T_{\mathrm{МЗВ}}$, баланс WNM | описание наблюдателя |
| Код | `mt_ca.app` | `mt_ca.blanket` | — |

Одеяло **над** кипящим оcean; новых аксиом в `g` нет.

### Карта

| файл | содержание |
|------|------------|
| [`blanket/00-glossary.md`](blanket/00-glossary.md) | термины МЗВ, LIC, τ, $T_{\mathrm{eq}}$ |
| [`blanket/01-two-surfaces.md`](blanket/01-two-surfaces.md) | океан → одеяло |
| [`blanket/02-homogeneous-fill.md`](blanket/02-homogeneous-fill.md) | однородное τ, слои ℬ, карта T |
| [`blanket/03-wnm-thermal.md`](blanket/03-wnm-thermal.md) | Γ=Λ, таблица PS20 |
| [`blanket/04-constraints-data.md`](blanket/04-constraints-data.md) | yaml/json, критерии |
| [`blanket/05-screen-forward.md`](blanket/05-screen-forward.md) | колонка τ (смежная задача) |

### Реализация

| модуль | роль |
|--------|------|
| `mt_ca.blanket.constraints` | `load_ism_constraints()` |
| `mt_ca.blanket.preset` | `BlanketPreset` |
| `mt_ca.blanket.surface` | τ, `apply_ism_blanket`, `ism_T_map_K` |
| `mt_ca.blanket.wnm` | равновесие WNM |
| `mt_ca.blanket.column` | τ(N_H, r) по колонке |
| `mt_ca.blanket.stack` | наложение на симулятор |

Старые импорты (`ism_blanket`, `ism_screen`, `wnm_thermal`) — совместимость; новый код: **`mt_ca.blanket`**.

**Контрольный расчёт:** `python scripts/run_ism_blanket_over_ocean.py`.
