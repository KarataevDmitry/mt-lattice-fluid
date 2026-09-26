# Одеяло МЗВ · вторая поверхность над океаном

**Океан (первая поверхность):** ST-ткань M-слоя (~$10^{31}$ K в log-масштабе T) — канон **`MODEL.md`** + hub [`model/`](model/) + код **`mt_ca.app`** (`HabitatPreset.VACUUM_BOIL`, `habitat_boil`).

**Одеяло МЗВ (вторая поверхность):** однородное заполнение тёплой нейтральной среды поверх устоявшегося океана; мacro **$T_{\mathrm{МЗВ}}\sim 10^3\,\mathrm{K}$** (LIC ~7000 K), **не** CMB (2.7 K) и **не** подмена «заполнить до T_LIC».

**Devlog** (impl, dogfood, open) → [`DEVLOG.md`](DEVLOG.md) — **не SSOT** одеяла; не меняет утверждения ниже.

### Иерархия (SSOT одеяла)

```
гипотеза + T-физика МЗВ  →  BLANKET.md + blanket/*.md   — что такое вторая поверхность, Γ=Λ, pass
                              ↓
                         data/ism_constraints_v0.yaml    — числа, якоря LIC/VLISM, pass_blanket
                              ↓
                         impl mt_ca/blanket/             — preset · surface · wnm · constraints
                              ↓
                         sim scripts / verify            — dogfood; может отставать
```

**Истина одеяла** идёт из **этого hub + `blanket/` + `data/ism_constraints_v0.*`**. Код **догоняет**.

### M vs blanket vs Meta

| | **MODEL** | **BLANKET** | **META** |
|---|-----------|-------------|----------|
| Роль | канон **`g`**, M→T мост | канон **второй поверхности** (МЗВ на океане) | космология / наблюдатель **над** macro-T |
| Температура | $T_M$ fabric, coarse | $T_{\mathrm{МЗВ}}$, WNM balance | observer narrative |
| Код | `mt_ca.app` habitat | `mt_ca.blanket` | — |

**MODEL не дублируется:** одеяло — **над** уже кипящим океаном; не новая аксиoma в `g`.

### Карта

| файл | содержание |
|------|------------|
| [`blanket/00-glossary.md`](blanket/00-glossary.md) | МЗВ, LIC, τ, $T_{\mathrm{eq}}$, что **не** входит в солвер |
| [`blanket/01-two-surfaces.md`](blanket/01-two-surfaces.md) | стек: ocean → blanket; аналогия `app` / `blanket` |
| [`blanket/02-homogeneous-fill.md`](blanket/02-homogeneous-fill.md) | однородное τ, слои ℬ, readout $T_{\mathrm{ISM}}(\|\Phi\|)$ |
| [`blanket/03-wnm-thermal.md`](blanket/03-wnm-thermal.md) | Γ=Λ, H+He, `cooling_scale` как норма линий |
| [`blanket/04-constraints-data.md`](blanket/04-constraints-data.md) | schema yaml/json, pass criteria |
| [`blanket/05-screen-forward.md`](blanket/05-screen-forward.md) | column τ forward (смежный harness, не геометрия одеяла) |

### Код (SSOT impl)

| модуль | роль |
|--------|------|
| `mt_ca.blanket.constraints` | `load_ism_constraints()` → `data/ism_constraints_v0.yaml` |
| `mt_ca.blanket.preset` | `BlanketPreset` — none / homogeneous_mzw |
| `mt_ca.blanket.surface` | τ uniform, `apply_ism_blanket`, `ism_T_map_K`, reports |
| `mt_ca.blanket.wnm` | `wnm_equilibrium_T_K`, `equilibrium_T_wnm_K` |
| `mt_ca.blanket.column` | column τ(N_H, r) для uniform fill и forward |
| `mt_ca.blanket.stack` | наложение preset на `LatticeFluidSimulator` |

Legacy import paths (`mt_ca.ism_blanket`, `mt_ca.ism_screen`, `mt_ca.wnm_thermal`) — shims; новый код импортирует **`mt_ca.blanket`**.

Dogfood: `python scripts/run_ism_blanket_over_ocean.py`.
