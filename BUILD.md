# Построение M из первых принципов

Повторяемый протокол: **генезис → каркас → условия → конкретизация → проверка**.

SSOT физики: `MODEL.md` · SSOT одеяла: `BLANKET.md` · манифест: `MANIFEST.md` · журнал: `DEVLOG.md`. Код: `mt_ca/`, верификация: `verify_principles.py`.

---

## Шаг 0. Генезис

**Narrative / диалог:** [`DEVLOG.md` §7](DEVLOG.md#§7-genesis-диалог--m). **Канон постулатов:** [`MODEL.md` §0](MODEL.md#§0-основания-m).

| # | Шаг | Вывод |
|---|-----|-------|
| 0.1 | Красное смещение (redshift) | частота не абсолютна → дискретные тики |
| 0.2 | Картина «ходов» / тиков | дискретное время как гипотеза |
| 0.3 | Квант времени | `hT = t_P/√2` (не учебниковый `t_P` alone) |
| 0.4 | Дискретный мир | `hL = l_P`, `c₀ = hL/hT`, `c = κ·c₀` |
| 0.5 | Элементарный уровень | **КА**, фиксированные шаги |

**Проверка:** логическая цепочка, не численная.

---

## Шаг 1. Решётка (§1)

```
Λ = (ℤ/Nℤ)^d ,  t ∈ ℤ
dl = hL = l_P ,  hT = t_P ,  dV = dl³
N₄(x) = { x ± ê_i }     Moore запрещён — §1.3 (световой конус, Δs²)
f_геометрия зависит от ε; выбор N₄ из симметрии, не LBM-костыль
```

**Проверка:** `laplacian.py` — только 4 `roll`, без диагоналей. **Не Moore** в micro (внешний совет «8 соседей» ломает A1).

---

## Шаг 2. Каркас `g` (§3.1)

Дискретность + локальность + каузальность ⇒

```
Ψ^{t+1} = g(Ψ^t)
g = g_phase ∘ g_cr? ∘ g_lin
g_lin:   z ↦ L(z)
g_phase: z ↦ z · exp(i·Φ(z))
```

Параметры `(γ, Φ, L)` **ещё свободны**.

---

## Шаг 3. Абсолютные условия → ограничения (§2, §3.2)

Навешиваются **на каркас**, по одному. Для каждого — что запрещено и что остаётся.

| ID | Условие | Решение в модели |
|----|---------|------------------|
| A3 | Унитарность | `g_lin` = local bond-unitary на `N₄`; `g_phase` = `exp(iφ)` |
| A4 | U(1) | φ ∈ ℝ, без \|z\|-dissipation |
| A5 | Абс. ноль | Φ → large при \|z\|→0 |
| A6 | Энтропия | mixing через локальные unitary; T-предел |
| A7 | ρ_E ≤ u_P | знаменатель `+ε`, `\|z\|² ↔ ρ_E/u_P` |
| A8 | Макро-линейность | φ→0 при \|z\|→∞ **встроено в gate**; доп. `w(ρ)=1/(1+ρ/ρ_macro)` |
| A9 | Коши–Риман | метрика `cauchy_riemann_energy`; гладкие моды низкий CR; vortex core — намеренное нарушение |

**Конфликт A3↔A6 (старый MVP):** `z+γΔ₄z` (real) ломает норму.  
**Разрешение M:** product локальных 2×2 unitaries на links `N₄` (`linear_step_local_ca`).

**DFT (T-слой):** `t_analysis.spectral_unitary_reference` = exp(i·γ·Δ₄) для **калибровки** dispersion и сравнения с local CA — **не** micro_step.

---

## Шаг 4. Конкретизация (§3.3)

**Действие (шаблон A15):**

```
S = Σ_{links∈N₄} Re[ conj(z_x)(z_y - z_x) ] + Σ_x V(|z_x|²)
```

**Split-step (§7.1 — числа зафиксированы):**

```
z* = local_ca(z; γ)     — legacy: 4 bond-color sub-sweeps on N₄
z' = z · exp(i·φ_eff)   — default isotropic: one exp(iφ), no sweeps (§3.6 MODEL.md)
φ_base = 2π · ( α*/(|z|² + ε) · Re(⟨z⟩_N₄/z) - 1 )   — isotropic; legacy gate omits Re term
φ_eff  = φ_base · w(ρ) ,   w = 1/(1 + (ρ/ρ_macro)²)
α* = 1 + 1/(4π) ≈ 1.079577 ,  ε = 1 ,  β_SI = u_P = K_P ≈ 4.633e113 J/m³
ω = 2π/hT ≈ 1.648e44 rad/s ,  DX = 1.616255e-35 m ,  DT = hT ≈ 3.812e-44 s
γ = 0.25                   (dispersion — калибровать vs T DFT oracle)
```

См. `mt_ca/si_constants.py` · `python -c "from mt_ca.si_constants import as_code_dict; print(as_code_dict())"`

**A8 без `w`:** при ρ→∞, `α*/(ρ+ε)-1 → -1` ⇒ φ→0 mod 2π — gate уже гасит нелинейность на macro.

---

## Шаг 5. Численная проверка

```bash
python verify_principles.py --ship
python verify_principles.py --list
python verify_principles.py --suite t_macro
python verify_principles.py --scenario floor0_planckon   # same ids as: python -m mt_ca.app.cli run …
python run_benchmark.py --json
```

### Agent status card (2026-09-27)

Один экран для агентов. **Полная таблица:** [`DEVLOG.md`](DEVLOG.md) §1.0 · **группировка:** `verify_checks/suites.py` · **сценарии:** `mt_ca/app/scenario.py` (`verify_suites`).

| Вопрос | Ответ |
|--------|--------|
| Ship зелёный? | **`--ship`** (~117 checks) · `gate`: **`Model_purity`** + **`Repo_text_eol`** (LF) · далее `m_axioms`, `t_macro`, floor0/1, α/units/carrier/sm/instruments |
| Что красное? | Suite **`m_evolution_open`** only: `A9`, `A10`, `FCC_N12`, `Vortex_hex` — **не** в ship; M-динамика/пороги, не опровержение §8.2 |
| α / массы / Higgs «выведены»? | **Да** в смысле MODEL: одна цепочка α_fs→v→m_H→…; verify ship PASS на registry rows. **Open:** ppm-хвосты packing/FCC, Γ/τ/width, альтернативные derivation-пробы в verify (археология) |
| M→T / классика | Suite **`t_macro`**: `T_hydro_limit*`, **`T_classical_limit`**, **`phi_bz`** (Φ=ℬz) |
| Сим = verify? | `--scenario <id>` → `ScenarioSpec.verify_suites`; `cli list` колонка `verify` |
| Перед правкой MODEL | `gate` PASS (`Model_purity`, `Repo_text_eol`); текст SSOT — **LF** (`.gitattributes`, `python tools/normalize_text_eol.py`) |

| Тест | Axiom | Критерий |
|------|-------|----------|
| A3 local_ca | A3 | norm_drift < 1e-4 |
| T_dft_oracle | T | local vs spectral (informative) |
| A3 diffusive | — | drift >> 0 (legacy gap) |
| A4 | A4 | \|z·e^{iφ}\| = \|z\| |
| A5 | A5 | vacuum не схлопывается |
| A8 | A8 | φ_high < φ_low при ρ_high |
| A9 | A9 | **`e₀≤ν_CA·{B_V}²`**, **`e₁≤ν_CA·(1+{B_V})`**, стационарность (§3.9.6) |
| A11 | validation | vortex amp не исчезает за 128 steps |

---

## Шаг 6. Открытые пробелы (честно)

**Актуальный снимок verify + α/массы/Higgs:** [`DEVLOG.md`](DEVLOG.md) §1.0 и §3 (open UoW). Таблица ниже — **исторический MVP** (до suites); не использовать для ship-статуса.

| ID | Статус после пересборки |
|----|-------------------------|
| A3 | ✅ `local_ca` в M |
| A6 | ⚠️ мотив сохранён; строгий entropy proof — нет |
| A8 | ⚠️ gate asymptotics + `w(ρ)` |
| A9 | ⚠️ **`m_evolution_open` FAIL** stationarity (2026-09-27); см. DEVLOG §1 |
| A10 | ⚠️ seeds OK · evolution **FAIL** в open suite; не «❌ post-process only» |
| A12 | ❌ T-гипотеза |
| A14 | ✅ P/C/T/U1 probes · long **`g·P`** open · CPT product = optional T-layer (not M **`g⁻¹**) |
| A15 | ⚠️ γ dispersion (T); **α*, α_fs, Planck — §7–§8 fixed** |

---

## Порядок работы при уточнении

1. Пройти шаги 0–2 — **не менять порядок** (условия после каркаса).
2. Для каждого нового условия: добавить строку в §2, ограничение в §3.2, тест в `verify_principles.py`.
3. Только после PASS A3/A4/A5 — калибровать γ по dispersion; α* по vacuum spectrum.
4. SM-слой (§8) — **после** стабильного M + T coarse-grain.

---

## Шаг 7. GPU-контракт (§10 — три предохранителя)

| # | Риск | Решение | Код |
|---|------|---------|-----|
| 1 | стенки гасят норму | **тор** (periodic BC) | `laplacian.py` `torch.roll`; bond wrap в `linear.py` |
| 2 | `z≡0` → поле не эволюционирует | **первичный бульон** `\|z\|~10^{-6}` | `MConfig.vacuum_amplitude=1e-6`, `seeds.VACUUM` |
| 3 | Euler `z+=iφz` ломает `\|z\|` | **`z *= exp(iφ)`** + bond-unitary linear | `update.micro_step` |

**Проверка:** `verify_principles.py` (A3 norm drift, A4 modulus, A5 vacuum не схлопывается).

---

## Шаг 8. Эпистемология и поиск зародышей (§2.2, §9.7)

| Вопрос | Ответ |
|--------|--------|
| Brute force всех IC? | **Нет** — CR + U(1) сжимают пространство |
| Сколько вариантов? | **4** топокласса × **(r, импульс)** ≈ **10–20** runs |
| ε | **N₄** · `seeds.py` |

**Таблица прогонов (MVP):**

| n | seed | smoke test |
|---|------|------------|
| 0 | `PLANE_WAVE` | T1 |
| +1 | `VORTEX_P` | T2 + A11 |
| −1 | `VORTEX_M` | T2 collision |
| +2 | `VORTEX_N2` | persistence |

```bash
python validate_mt.py
python verify_principles.py
# sweep: r∈{1..5}, seeds above — UoW script TBD
```

**Сжатия:** моды Δ₄/DFT · winding `n` only · optional inverse coarse-grain из T.
