# §1 · Две поверхности

### §1.0 · Стек

```
z ↑
│  blanket layers   ← вторая поверхность (МЗВ, mt_ca.blanket)
│  ── interface ──
│  boil ocean       ← первая поверхность (ST, mt_ca.app / habitat_boil)
└──────────────────
```

**Первая поверхность** задаёт **substrate** после settle: spinor ocean с контрастом порядка единицы на macro.

**Вторая поверхность** — не смена habitat и не новый seed class; это **наложение** поверх уже инициализированного океана:

1. сохранить `z_ocean` (reference);
2. построить однородный `tau_2d`;
3. `apply_ism_blanket` — копии интерфейса с послойным exp(−τ/N);
4. readout $T_{\mathrm{МЗВ}}$ на верхнем слое + ripple от |Φ|.

### §1.1 · SSOT-пары

| слой | физика / гипотеза | код |
|------|-------------------|-----|
| ocean | A5 boil, floor0… | `ScenarioSpec` + `HabitatPreset.VACUUM_BOIL` |
| blanket | homogeneous МЗВ, WNM Γ=Λ | `BlanketPreset.HOMOGENEOUS_MZW` + `mt_ca.blanket.stack` |

Сценарий **`ocean_ism_blanket`** (app) = `habitat_boil` + preset одеяла — один объект условий, как `floor0_planckon` для приборов.

### §1.2 · Что отвергнуто

- Градиент τ по «ветру» как прокси ISM.
- Подгонка readout к `T_K_warm_nominal` внутри формулы карты T.
- Трактовать успех одеяла как совпадение с **CMB** ΔT/T.
