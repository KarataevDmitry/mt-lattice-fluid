# DEVLOG — дневник разработки (impl · verify · open)

**Не SSOT физики.** Provenance сессий, impl status, open leaves, verify snapshots, backlog.

Канон формул: [`MODEL.md`](MODEL.md) · meta: [`META.md`](META.md) · протокол: [`BUILD.md`](BUILD.md)

---

## §0. Граница MODEL / DEVLOG / META / BUILD

| | **MODEL** | **DEVLOG** | **META** | **BUILD** |
|---|-----------|------------|----------|-----------|
| Роль | SSOT физики `g` | impl/verify/open | UI/космология | протокол сборки |
| Спор «что делает g?» | MODEL | — | — | — |
| «догнали ли код?» | — | **DEVLOG** | — | BUILD |
| «что видит мозг?» | — | — | META | — |

**Правило:** provenance, ✅/⚠️, open leaves, GPU DoD, даты сессий — **только DEVLOG**. MODEL не датирует разработку.

---

## §1. Реестр ограничений (единый указатель)

**Один экран.** Строка = известное ограничение → что требует от **`g`** → где в **MODEL** → **gap** → **verify** → **impl** → **следующий шаг**.

**Метод:** ansatz **`g`** → наложить известное. **`l_P = √(ℏG/c³)`** — естественная длина; **`L = f·l_P`**. Нет **`hL→0`** на M — T-readout вверх (MODEL §0.4).

**Gap:** **—** закрыто · **sim** MODEL есть, код нет · **model** ещё не выведено в MODEL · **T** readout/metric.

**Verify:** `python verify_principles.py --device cpu` · T: `validate_mt.py` · snapshot **2026-09-22**.

### A1–A16

| # | Условие (суть) | Что требует от **`g`** | MODEL | gap | verify | impl | следующий шаг |
|---|----------------|------------------------|-------|-----|--------|------|---------------|
| **A1** | **Каузальность** — за **`hT`** не дальше **`l_P`** | равные light-like NN; канон **FCC N₁₂**; Мур/2-я оболочка ✕ | §1.3 · §1.6 | — / sim | — (структура) · MVP=`N₄` | `laplacian` N₄ | stencil → N₁₂ |
| **A2** | **Локальность** | **`g(x)`** только из ε-окрестности | §2 · §0.3 | — | — (структура) | `projected_collision` | — |
| **A3** | **Унитарность** | **`Σ|z|²`** invariant; rotation, не damping | §2 · §5.2.1 | sim | **`Leapfrog`** PASS · **`A3`** · **`LocalContinuity`** (bond) | `reversible` · `z_ring` | **`div j=0`** на full **`projected_step`** |
| **A4** | **U(1)/SU(2) спинор** | **`z∈ℂ²`**, **`R(Φ)`** unitary | §2 · §3.10 | — | **`A4`** · **`SU2_360/720`** PASS | Rot_LUT · `su2_apply` | — |
| **A5** | **Абс. ноль недостижим** | boiling vac; **`z≡0`** excluded | §2 · §0.5 | sim | **`A5`** · **`PlanckVacuumFloor`** PASS | `heisenberg_floor` · seeds | ≠ D5 при floor — MODEL §2.3.8 |
| **A6** | **2-й закон локально** | mixing ↑ entropy | §2 | model | **`A3_diffusive`** anti · full **`g`** не доказано | legacy `linear_step` | вывести для full **`g`** или ослабить claim |
| **A7** | **`ρ ≤ ρ_P`** | **`K_P`** в Φ; clamp | §2 · §3.12.5 | sim | **`A7`** PASS | `bekenstein_scale_spinor` | — |
| **A8** | **Macro-линейность** | **`w(ρ)`** затухает | §2 · §3.4 | T | **`A8`** PASS | gate **`w(ρ)`** | T-readout probes |
| **A9** | **CR / голоморфность** | **`g`** держит аналитичность | §2 · §3.9 | **sim** | **`A9` FAIL** | `cr_strength` · holomorphy sync | CR на **`Φ(ζ)`**, не stationarity seed |
| **A10** | **`n ∈ ℤ`** | winding **`∂(hV)`** | §2 · §5.0 | **sim** | seeds OK · **`A10`** evolution **FAIL** | `topology` · seeds | long-run **`n`** — §3 open |
| **A11** | **Soliton / anti-smear** | **`K_P+Δφ`** держит ядро | §2 · §3.7–§3.9 | sim | **`A11`** PASS | saturating Φ | — |
| **A12** | **Lorentz / isotropy (T)** | macro круг **`κ=1/√2`** | §2 · §1.1 · §4.1 | T | T1 PASS (512²) | `macro` binomial | radial probe — open |
| **A13** | **Обратимость** | leapfrog на **`ℤ`** | §2 · §3.12 | — | **`Leapfrog`** PASS | `projected_step_fixed` | — |
| **A14** | **P/C/T/U1** | симметрии на **`g`** | §2 · §3.11 | **sim** | **`A14`** · **`U1_vac`** · **`SO2_C4` FAIL** · **`Chiral_SU2` PASS** | `symmetry` · `chiral` | **equivariant encode + step** (одна ось с A9) |
| **A15** | **Геометрия / kappa_link** | kappa из многогранника; gamma = 1/N; канон N=12 | §1.6 · §5.2.2 | sim | **QuarterQuantum** PASS (MVP 1/4) | `si_constants` | FCC 1/12 row |
| **A16** | **Pauli / 720°** | **`2π→−1`**, repulsion | §2 · §3.10.4 | sim | **`A16`** · **`Pauli`** PASS | `pauli_phi` | — |

**§2.3 (блок):** ¬heat death · fixed points · Planck floor — MODEL §2.3 · **`NoMHeatDeath`** · **`Theorem_2_3_8`** · **`PlanckVacuumFloor`** PASS.

### Линейка · форма **`g`** · §5.2 (не отдельные A#)

| ограничение | MODEL | gap | verify | следующий шаг |
|-------------|-------|-----|--------|---------------|
| **`hL=l_P`**, **`B_hV`**, **`N_ring=512`** | §0 · §3.12.6 | — | **`HvBitBudget`** PASS | — |
| **тайл / ε:** **FCC N₁₂ обоснован** (упаковка ∧ конус); гекс=(2+1) срез; квадрат=MVP | §1.3 · §1.6.1 | sim | MVP=`N₄` | FCC stencil + `v_hV` |
| **лестница ФТТ:** `G`, BZ, умклапп, `N_pack`, `b_atom` | §5.2.4 | model | — | quanta + probe |
| leapfrog **`2Z+⌊𝒩⌋`**, **`Φ(K_P,ζ,ρ)`**, **`R(Φ)=ω^Φ`** | §3.12.5 | sim | **`Leapfrog`** · **`DiscreteRotExp`** PASS | ledger-neutral kick distribution |
| **`s₀→p₀,L₀,E₀`**, **`κ_link`** (`¼` MVP / `⅙` hex / `1/12` FCC) | §5.2 · §1.4 · §1.6 | — | **`MechanicalQuantum`** · **`QuarterQuantum`** PASS | FCC/hex row |
| **`div j`**, **`ΣΔπ mod p₀`**, **`L_z`**, **`n_E` ledger** | §5.2.1–§5.2.3 | sim | **`LadderLedger`** PASS (proxy) | полный star closure на step |
| **`b` из n_partial, не amp²** | §5.0 · §5.2.3 | sim | **MatterOccupancyB** PASS | T occupancy — open |
| **4 силы** · v=α_fs^8 E_P √(2π) · 8=⌊B_hV⌋−1_occupancy · α_s seed 3/(8π) | §8.4.1 | model / T(α_s) | v/G_F hit · occupancy lemma ✅ | α_s runner · GR strain |
| **Higgs = T-пена** | §5.0.1 · §8 | T | — | sim **`m_H`** leaf |

**Приоритет sim-gap:** **A14 + A9** (equivariant canonical step) → затем A10 evolution, A3 full continuity.

**Цикл:** (1) строка реестра → (2) есть в MODEL? иначе **model-gap** → (3) режет **`g`**? impl отстаёт → **sim-gap** → (4) T-only → **`validate_mt`** → (5) несовместимость → правим MODEL/ansatz, не порог verify.

---

## §3. Open leaves (индекс)

- **§3.9 DA:** long-run exact `n` conservation on contour (T-readout шум); D2Q9 ladder §3.8 step 2 only if hex fails vortex test
- **§3.10 SU(2):** full SM electron-from-`hV` sim (anchor `m_e` via `electron_v_p_anchor` ✅ algebra only)
- **§3.11 symmetries:** long-run **`g·P≠P·g`** on vortex (chirality dance §9.2)
- **§3.6 isotropy:** macro radial probe — open
- **§3.7 GPU:** T1-круг · Gaussian head-on · vortex axis ratio · hex §3.8 if square shows
- **§5.0.5:** `ρ_Θ` — Heisenberg matter/phase-density (аналог `ρ_e`); не путать с `|z|²` океана — sim leaf
- **§5.0.4:** запрещёнка пра-частицы (уровни/`E₀`/Паули/оболочки ε; не орбиталь внутри `l_P`) — sim spectrum open
- **§1.6.5:** один КА-схема; `|N|` только от упаковки размерности — не «гекс↔FCC переключатель»
- **§1.6.4:** Minkowski `(3+1)FCC ↔ (2+1)hex` — погружение слоя `{111}`; якорь `c` на 4D — open bulk-coupling
- **§1.6 / §5.2.4:** 3D FCC кандидат; лестница BZ/умклапп/`N_pack`; asympt. κ_FCC — open
- **§3.8 / §1.4 hex:** 2D кандидат; мост `κ=√3/2`; impl MVP ещё `N₄`
- **§4.1.2 ν_CA:** fit **`ν_eff`** vs algebraic **`ν_CA`** — T6
- **§4.9 Young:** GPU leaf barrier + detector screen + slit — open
- **§5.0 binary ρ:** occupancy readout on T — open
- **§5.0.1 Arg mass:** sim `m_H` vs N_вихрей — open
- **§5.0.3 antimatter:** sim VORTEX_P + VORTEX_M → n_net→0 + 2-front — open
- **§5.2.2 κ_link:** sim ballistic check on `c` — open
- **§5.3 gas:** sim EOS / `P(ρ)` readout — open
- **§5.3.2 v_s:** численный `v_s` on T-readout — open
- **§5.3.3 VdW:** T compression / occupancy — open
- **§8.4:** четыре взаимодействия = симметричные каналы одного квантованного `g`; `α_s`/`G_F`/metric — model-gap (не «вне M»)
- **§8 Higgs:** численный `m_H` / Higgs width leaf — open

---

## §4. Impl status по разделам

### §3.6 Isotropic streaming

- ✅ shipped · T1 **micro≈1.0**
- macro radial probe — open
- legacy `local_ca`: micro ~1.25

### §3.7 Heisenberg · anti-smear

**Provenance (2026-09-22):** дилемма «чернила в воде» закрыта на M (§3.7.2); impl/sim — backlog ниже.

**§3.7.4 Impl/sim v3 backlog (не канон):**

| probe | метрика | isotropic | local_ca |
|-------|---------|-----------|----------|
| один Gaussian σ=5, 192 steps | `max(coarse)_late/0` | **0.15** | 0.32 |
| два Gaussian σ=6, 256 steps | `max(coarse)_ratio` | **0.12** | 0.28 |
| T2_collision (δ) | `peaks_late` | 2 | 2 |

**Не вердикт M:** `mt_ca` v3 + coarse — **догоняют** §3.7.2–§3.9.

### §3.9 DA / CR

| пункт | статус |
|-------|--------|
| CR + **`cr_strength`** | ✅ shipped · verify **`A9` FAIL** — §1 |
| **`Δφ ≥ 1/2`** Heisenberg floor | ✅ **`heisenberg_floor`** · A16 |
| winding **`n`** seeds + T readout | ✅ A10 · `topology.winding_robust` |
| holomorphy sync on tick | ✅ **`holomorphy_sync_step`** |

**Verify A9:** `PLANE_WAVE` · burn-in 32 + settle 32 · пороги `cr_seed_ceiling` / `cr_dispersion_ceiling`. Старый **`e₁ < 0.05`** — отвергнут.

**Implementation debt:** где impl проще (локальный `N₄` на tick без явного CR) — backlog, не отмена ДА-формулировки.

### §3.10 SU(2) · Pauli

**Provenance (2026-09-22):** «без спина Вселенная плоская и мёртвая».

| слой M | impl (`mt_ca`) |
|--------|----------------|
| **`z ∈ ℂ²`** | ✅ единственное поле |
| **SU(2) gate** | ✅ **`su2_apply`** |
| **360° → −1** | ✅ **`SU2_360`** |
| **720° → +1** | ✅ **`SU2_720`** |
| **Pauli на `v_p`** | ✅ **`pauli_phi`** · **`Pauli`** |

### §3.11 Symmetries

**Provenance (2026-09-22):** «доводи impl» — global phase не ломает `g`.

**Impl-gap (closed 2026-09-22):** `defect_axis → [0,0,1]` ломал U1 на PLANE_WAVE → fix `axis ← n_z`.

| слой M | impl |
|--------|------|
| **`U(1)_vac`** | ⚠️ verify **`U1_vac` FAIL** — §1 |
| **`P_L/P_R`** | ✅ **`chiral.py`** · **`Chiral_SU2`** |
| **projected 𝒩 on Z_N[i]** | ✅ **`projected_collision.py`** |
| **CPT product** | optional · `run_symmetry_probe.py` |
| **A14 bundle** | ✅ P/C/U1/chiral · long **`g_P_steps`** logged |

### §3.12 Leapfrog Z_N[i]

**Provenance (2026-09-22):** float32 1-го порядка на 4070 → киральная «пляска» `n`; leapfrog на ℤ — единственный закон счёта.

| слой | impl |
|------|------|
| forward | **`projected_step_fixed`** |
| reverse | kick ledger · **`Leapfrog`** bit-exact |
| gauge-fix encode | ✅ U1 equivariance |

### §4 T-layer

| раздел | статус |
|--------|--------|
| §4.1.2 **`ν_CA`** | ✅ algebraic · verify **`Nu_CA`** · **`T3_macro_viscosity`** · fit **`ν_eff`** open |
| §4.9 Young | ✅ онтология · GPU slit leaf open · partial T2, A11 |
| §4.2 validate | **`validate_mt.py`** T1/T2/T3/T_dispersion PASS 512² CUDA (2026-09-22) |

### §5 Matter · quantization · gas

| раздел | статус |
|--------|--------|
| §5.0 binary ρ | ✅ **`Rho_P_binary`** · occupancy T — open |
| §5.0.1 Arg mass | ✅ **`Arg_mass_carrier`** · **`T_zigzag_mass`** · sim open |
| §5.0.3 antimatter | ✅ A10 seeds · annihilation sim open |
| §5.2.1 mechanical | ✅ **`MechanicalQuantum`**, **`LocalContinuity`**, **`LadderLedger`** |
| §5.2.3 elementary | ✅ **`ElementaryQuanta`** · **`LadderLedger`** · **`MatterOccupancyB`** |
| §5.3 gas / VdW | ✅ algebra · sim EOS open |

### §8 SM / Higgs

- ✅ онтология M→T · **`m_H` leaf** open · не refute LHC — переинтерпретация слоя

---

## §5. Provenance (цитаты сессий)

| дата | контекст | цитата / триггер |
|------|----------|------------------|
| 2026-09-22 | §3.7 | дилемма isotropic vs rays — закрыта Heisenberg + K_P |
| 2026-09-22 | §3.8 | «тяжёлый vortex на квадрате» + дискретный анализ |
| 2026-09-22 | §3.9 | «строгий ДА убирает физические натяжки» |
| 2026-09-22 | §3.10 | «без спина Вселенная плоская и мёртвая» |
| 2026-09-22 | §3.11 | «доводи impl» — U1_vac + chirality |
| 2026-09-22 | §3.12 | float32 1st order на 4070 → chirality dance `n` |
| 2026-09-22 | night canon | split MODEL/META; canonical Z_N[i]; quantization ladder |
| 2026-09-22 | §3.10.3 | `exp(i·Θ·σ/2)` → discrete `R(Φ)=ω^Φ` on Z_N[i] |
| 2026-09-22 | §1.6.1 | теорема выбора: упаковка∧конус ⇒ FCC N₁₂ (обоснованный канон ε) |
| 2026-09-22 | §0 | genesis narrative → DEVLOG §7; MODEL = postulates only |

---

## §7. Genesis (диалог → M)

**Не SSOT.** Как пришли к каркасу — история разработки; физика — **MODEL §0–§8**.

**Вход:** **красное смещение (redshift)** — частота/длина волны не инвариантны → мотивация дискретного времени и «ходов».

**Сдвиг:** картина **дискретного автомата** — время и «ходы», не плавный контinuум «из коробки».

**Гипотеза:** квантованное время ⇒ дискретный элементарный уровень.

**Порядок сборки** (протокол — [`BUILD.md`](BUILD.md)):

1. дискретность + **`(hL, hT)`** → КА, **`Ψ^{t+1}=g(Ψ^t)`**
2. абсолютные условия A1–A16 → ограничивают **`g`** (MODEL §2)
3. конкретизация **`g`**, SI, SM (§3–§8)

**Не путать с MODEL §0:** там только **постулаты/определения/следствия**, без narrative.

---

## §6. Команды verify

```bash
python verify_principles.py --device cpu
python validate_mt.py          # T1/T2/T3 — CUDA
python scripts/run_symmetry_probe.py
```

**Последний полный M-verify (2026-09-22):** см. колонку **verify** в **§1**.
