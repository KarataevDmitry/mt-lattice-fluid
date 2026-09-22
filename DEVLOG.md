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

## §1. Реестр аксиом A1–A16 (verify)

**Зачем эта таблица:** открыла **A1** — видишь **что это**, **где в MODEL**, **чем проверяем**, **PASS/FAIL**. Не дублирует §2.1 (там — полный реестр наложений + «как уложить»).

**Команда:** `python verify_principles.py --device cpu` · T: `validate_mt.py`

| # | Условие (суть) | Что требует от **`g`** | MODEL | verify · статус | impl (`mt_ca`) |
|---|----------------|------------------------|-------|-----------------|----------------|
| **A1** | **Каузальность** — за **`hT`** сигнал не дальше **`l_P`** по оси | только **`N₄`**, Moore за один tick **запрещён** | §2 · §1.3–§1.4 | — · **структура** (отдельного probe нет) | `laplacian.py` stencil **`N₄`** |
| **A2** | **Локальность** | **`g(x)`** только из ε-окрестности **`x`** | §2 · §0.3 | — · **структура** | `projected_collision.py` · local ζ, Φ |
| **A3** | **Унитарность / сохранение информации** | **`Σ|z|²`** invariant; gate = rotation, не damping | §2 · §5.2.1 | **`Leapfrog`** PASS · **`A3`** (bit-exact) · **`LocalContinuity`** (bond layer) | `reversible.py` · `z_ring.py` |
| **A4** | **U(1) / SU(2) спинор** | **`z∈ℂ²`**, gate **`R(Φ)`** unitary на спиноре | §2 · §3.10 | **`A4`** PASS · **`SU2_360`** · **`SU2_720`** | `spinor` · `su2_apply` · Rot_LUT |
| **A5** | **3-й закон: абс. ноль недостижим** | вакуум **кипит**; **`z≡0`** excluded; floor амплитуды | §2 · §0.5 | **`A5`** PASS · **`PlanckVacuumFloor`** PASS · **`I2_zero`** (anti) | `seeds.VACUUM` · `heisenberg_floor` |
| **A6** | **2-й закон (локально)** | mixing ↑ entropy при фикс. norm | §2 | **`A3_diffusive`** FAIL by design (anti-check) · full **`g`** — **не доказано** | legacy `linear_step` only |
| **A7** | **Планковский потолок **`ρ≤ρ_P`** | **`K_P`** в знаменателе Φ; clamp после step | §2 · §3.12.5 | **`A7`** PASS | `bekenstein_scale_spinor` · `clamp_density` |
| **A8** | **Macro-линейность** | нелинейность **`w(ρ)`** затухает при больших **`ρ`** | §2 · §3.4 | **`A8`** PASS | gate **`w(ρ)`** |
| **A9** | **Дискретная аналитичность (CR)** | **`g`** удерживает голоморфность; CR → поле Λ | §2 · §3.9 | **`A9`** **FAIL** | `cr_strength` · `holomorphy_sync_step` |
| **A10** | **Топологический заряд **`n∈ℤ`** | winding на **`∂(hV)`**; полюс **`v_p`** | §2 · §5.0 | seeds PASS · evolution **`A10`** **FAIL** | `topology.py` · seeds §9.7 |
| **A11** | **Soliton / anti-smear** | размазанное не голоморфно; **`K_P+Δφ`** держит ядро | §2 · §3.7–§3.9 | **`A11`** PASS | saturating Φ · vortex seeds |
| **A12** | **Изотропия / Lorentz (T)** | micro isotropic; macro круг **`κ=1/√2`** | §2 · §1.1 · §4.1 | **`validate_mt` T1** PASS (512² CUDA) | `macro.py` binomial · §3.6 |
| **A13** | **Обратимость шага** | **`Z⁺+Z⁻=2Z+⌊𝒩⌋`** на **`ℤ`**; **`g⁻¹`** algebra | §2 · §3.12 | **`Leapfrog`** PASS | `projected_step_fixed` |
| **A14** | **P / C / T / U(1)_vac** | симметрии discrete на **`g`** | §2 · §3.11 | **`A14`** **FAIL** · **`U1_vac`** **FAIL** · **`SO2_C4`** **FAIL** · **`Chiral_SU2`** PASS | `symmetry.py` · `chiral.py` |
| **A15** | **Наименьшее действие / геометрия N₄** | **`κ=1/√2`**, **`γ=κ_link=¼`**, **`α*`** | §2 · §5.2.2 · §7.1 | **`QuarterQuantum`** PASS · `check_kappa.py` | `MConfig.gamma` · `si_constants` |
| **A16** | **Fermi / Pauli** | **`2π→−1`**, **`4π→+1`**; параллельные spinors repel | §2 · §3.10.4 | **`A16`** PASS · **`Pauli`** PASS | `pauli_phi` · SU(2) double cover |

**Связанное (не отдельная аксиома):**

| блок | суть | MODEL | verify · статус |
|------|------|-------|-----------------|
| **§2.3** | ¬M heat death; fixed points; Planck floor | §2.3 · §0.5 | **`NoMHeatDeath`** · **`Theorem_2_3_8`** · **`PlanckVacuumFloor`** PASS |

**Легенда verify:** **PASS** / **FAIL** = последний `verify_principles.py` (2026-09-22). **—** = нет отдельного probe, только структура кода/MODEL. Детали gap и «как уложить» → **§2.1**.

---

## §2. Audit · gap tracker

Полный реестр «известное → MODEL → как уложить в `g`» — **§2.1**. Ниже — краткий индекс quanta.

| величина | статус | gap |
|----------|--------|-----|
| **`κ_link`, `γ`, `cr_strength`, `ν_CA`** | ✅ **`¼`** | — |
| **`s₀`, `p₀`, `L₀`, `E₀`, `F₀`, `g_M`** | ✅ §5.2.1 | — |
| **`sync`, Pauli, `ρ_Q`, `n_E` map** | ✅ §5.2.3 | **`LadderLedger`** (E/p/L + Heisenberg every tick) |
| **`R(Φ)=ω^Φ` vs `exp(i·Θ·σ/2)`** | ✅ §3.10.3 · §3.12.5 | verify **`DiscreteRotExp`** |
| **`b ∈ {0,1}`** | ✅ §5.0 / §5.2.3 | **`MatterOccupancyB`** (n_∂ + ρ gate, not \|z\|²) |
| **`α_s`, G_F, динамическая метрика** | ❌ | **model-gap** SM/GR |

Verify: **`QuarterQuantum`**, **`EnergyQuantum`**, **`ElementaryQuanta`**, **`Rho_P_binary`**, **`LadderLedger`**, **`MatterOccupancyB`**. Живой PASS/FAIL по строкам — **§2.1** (не дублировать здесь).

---

## §2.1 Реестр фундаментальных ограничений

**Метод (как теормех):** предположение → **общий вид** локального перехода **`g`** → **наложение** уже известных ограничений. Не «предел **`hL→0`**» (как **`c→∞`**, **`ℏ→0`** в другую сторону), а **T-readout вверх** с **фиксированного** шага; **`l_P = √(ℏG/c³)`** — **естественная единица длины**, любая **`L = f·l_P`**. Ниже **`dl = hL = l_P`** на M **нет координаты** (MODEL §0.4, §1.4).

**Три gap’а (MODEL шапка):**

| gap | смысл | долг |
|-----|--------|------|
| **model-gap** | ограничение **известно**, в MODEL **ещё не выведено / не режет форму `g`** | дописать § MODEL |
| **sim-gap** | в MODEL **уже сказано**, **`mt_ca`** не догнал | код · verify |
| **T-metric** | грубый readout / fit на T | `validate_mt`, macro — **не refute M** |

**Колонки реестра:**

| колонка | смысл |
|---------|--------|
| **MODEL** | где уже записано |
| **режет `g`?** | **да** — сужает **`Φ` / ⌊𝒩⌋ / encode / leapfrog** · **частично** · **следствие** · **T-only** |
| **gap** | — · model · sim · T |
| **verify** | probe · PASS/FAIL · — (ещё нет) |
| **уложить** | следующий шаг наложения (не «ещё один knob») |

*Verify snapshot: `python verify_principles.py --device cpu` (2026-09-22 после **`LadderLedger`** ship).*

### I · Линейка и кирпич (из CODATA, не knobs)

| ограничение | источник | MODEL | режет `g`? | gap | verify | уложить |
|-------------|----------|-------|------------|-----|--------|---------|
| **`l_P`**, **`hL = l_P`** | **`√(ℏG/c³)`** | §0.2 · §1 · §7 | **да** — шаг решётки, **`dV=l_P³`** | — | **`HvBitBudget`** algebra | — |
| **`hT = t_P/√2`**, **`c₀ = √2·c`** | N₄ + CODATA **`c`** | §0.2 · §1.1 | **да** — один M-тик, конус | — | **`MechanicalQuantum`** | — |
| **`κ = 1/√2`** | геометрия ромба N₄ | §1.1 · A15 | **да** — macro readout, не fitted | — | `scripts/check_kappa.py` | T1 radial — **T-metric** open |
| **`B_hV = 2π/ln2`**, **`N_ring=512`**, **`frac_bits=6`** | Planck **`E_P l_P = ℏc`** | §3.12.6 | **да** — **`Z_N[i]`**, Rot_LUT | — | **`HvBitBudget`** PASS | — |
| **`Δφ_min = ½`**, **`N_φ=13`** | Heisenberg · **`s₀=ℏ/2`** | §5.0.2 · §3.12.6 | **да** — floor на **`Φ`** | sim | **`A16`** · **`LadderLedger`** PASS | полный star ledger на **реальном** kick — **model→sim** |
| **нет `hL→0` на M** | дискретность | §0.4 · §1.4 | **структура** | — | — | не путать с T continuum |
| **`z_min`**, **`vacuum_amplitude`** | **`2^{−B_amp}`** · A5 | §0.5 · §10.2 | **да** — пол амплитуды | sim | **`PlanckVacuumFloor`** PASS | — |

### II · Форма перехода (ansatz `g`)

| ограничение | MODEL | режет `g`? | gap | verify | уложить |
|-------------|-------|------------|-----|--------|---------|
| **локальность **`N₄`**** | §0.3 · A2 | **да** | — | структура | Moore запрещён §1.3 |
| **leapfrog **`Z⁺+Z⁻=2Z+⌊𝒩⌋`**** | §3.12 | **да** — 2,−1 из конуса | — | **`Leapfrog`** PASS | — |
| **holonomy **`ζ`**** | §3.12.5 | **да** — вход **`Φ`** | — | **`Arg_mass_carrier`** PASS | — |
| **`Φ = ⌊K_P ζ_imag / (ζ_real+|Z|²+K_P)⌋`** | §3.12.5 · A7 | **да** — saturating + Bekenstein | sim | **`A7`** · **`DiscreteRotExp`** | ledger-neutral распределение kick — **model** |
| **`R(Φ)=ω^Φ`**, не matrix exp | §3.10.3 · §3.12.5 | **да** | — | **`DiscreteRotExp`** PASS | — |
| **decode float ≠ tick** | §0.3 · §3.12.4 | **да** | sim | **`Leapfrog`** | — |

### III · A1–A16 (абсолютные условия → класс допустимых `g`)

| # | суть | MODEL | режет `g`? | gap | verify (2026-09-22) | уложить |
|---|------|-------|------------|-----|---------------------|---------|
| A1 | каузальность, **`c₀`**, N₄ | §2 | **да** | — | структура | — |
| A2 | локальность | §2 | **да** | — | структура | — |
| A3 | **`Σ|z|²`**, unitary gate | §2 · §5.2.1 | **да** | sim | **`Leapfrog`** · **`LocalContinuity`** (bond) | **`div j=0`** на full **`projected_step`** — **sim** |
| A4 | **`ℂ²`**, SU(2)/U(1) gate | §2 · §3.10 | **да** | — | **`SU2_360/720`** | — |
| A5 | нет абс. нуля · boiling vac | §2 · §0.5 | **да** | sim | **`A5`** · **`PlanckVacuumFloor`** | ≠ D5 динамика при floor — **§2.3.8** |
| A6 | локальная энтропия | §2 | **частично** | model | **`A3_diffusive`** (anti) | для full **`g`** — **model-gap** |
| A7 | **`ρ ≤ ρ_P`**, **`u_P`** | §2 · §3.12.5 | **да** | sim | **`A7`** PASS | — |
| A8 | macro-линейность | §2 | **T + gate** | T | **`A8`** | T-readout |
| A9 | CR / голоморфность | §2 · §3.9 | **да** — класс **`g`** | **sim** | **`A9` FAIL** | CR как **ограничение на `Φ(ζ)`**, не stationarity seed — **model→sim** |
| A10 | **`n ∈ ℤ`**, winding | §2 · §5.0 | **да** | **sim** | seeds PASS · **evolution FAIL** | long-run **`n`** — §3 open |
| A11 | anti-smear, soliton | §2 · §3.7 | **да** | sim | **`A11`** PASS | — |
| A12 | Lorentz / isotropy T | §2 | **T** | T | **`validate_mt` T1** | macro radial — open |
| A13 | обратимость шага | §2 · §3.12 | **да** | — | **`Leapfrog`** PASS | — |
| A14 | P/C/T/U1 on **`g`** | §2 · §3.11 | **да** | **sim** | **`U1_vac` FAIL** · **`SO2_C4` FAIL** · **`A14` FAIL** | equivariant **encode + step** — **sim-gap**, не ослаблять MODEL |
| A15 | **`κ_link=¼`**, **`α*`** | §2 · §5.2.2 | **да** | — | **`QuarterQuantum`** PASS | — |
| A16 | Pauli · **`2π→−1`** | §2 · §3.10.4 | **да** | sim | **`Pauli`** · **`A16`** PASS | — |

### IV · Лестница §5.2 (механика без float-knobs)

| ограничение | MODEL | режет `g`? | gap | verify | уложить |
|-------------|-------|------------|-----|--------|---------|
| **`s₀ → p₀, L₀, E₀, F₀, g_M`** | §5.0.2 · §5.2.1 | **да** — integer ledger | — | **`MechanicalQuantum`** · **`EnergyQuantum`** · **`Arg_quantum`** | — |
| **`κ_link = γ = cr = ν_CA_nat = ¼`** | §5.2.2 | **да** | — | **`QuarterQuantum`** · **`Nu_CA`** | ballistic **`c`** sim — T |
| **`div j=0`**, **`Σ_{N₄}Δπ≡0 (mod p₀)`**, **`L_z∈L₀·ℤ`** | §5.2.1 | **да** | **sim** | **`LadderLedger`** PASS (proxy floor + mod **p₀**) | **полное** star closure на step — **model→sim** |
| **`n_E = ⌊|Φ|/Δφ_disc⌋`**, energy ledger | §5.2.3 | **да** | **sim** | **`ElementaryQuanta`** · **`LadderLedger`** | boiling vac star — **model derive** |
| **`b = min(1,|n_∂|)`**, **`ρ_matter=ρ_P·b`** | §5.0 · §5.2.3 | readout | sim | **`MatterOccupancyB`** PASS | T occupancy §5.0 — open |
| **`Q = n·e₀`**, **`α_fs`** geometry | §5.2.3 · §8.2 | **T anchor** | model | **`Compton_e`** algebra | dynamical EM — model-gap |

### V · Известно · сознательно не в M (model-gap SM/GR)

| ограничение | статус | уложить |
|-------------|--------|---------|
| **`α_s`, G_F, running couplings** | ❌ model-gap | не подменять §8 якорями |
| **динамическая метрика GR** | ❌ model-gap | §8 / META |
| **Higgs как M-первопричина** | ❌ — **T-пена** §5.0.1 | sim **`m_H`** leaf |

### §2.1.1 Цикл работы (SSOT процесс)

1. **Строка реестра** — ограничение из «уже знаем» (CODATA · симметрия · термо · топология).
2. **MODEL** — есть § / нет → **model-gap**: вывести, как сужается **`Φ`**, **`⌊𝒩⌋`**, encode, **`hT`**.
3. **Режет форму?** — если да в MODEL, impl отстаёт → **sim-gap** (`mt_ca`, probe).
4. **T-only** — **`validate_mt`**, GPU; **не** ослаблять M под sim (MODEL шапка).
5. **Несовместимость** — правим **ansatz** или **одно ограничение** в MODEL; не «зелёный порог» verify.

**Приоритет sim-gap (блокирует Noether-таблицу §5.2.1):** **`U1_vac`** · **`SO2_C4`** · **`A9`** · **`A14`** — одна ось: **equivariant canonical step**.

**Provenance (2026-09-22):** «список ограничений → что в MODEL → как уложить»; **`l_P`** = natural unit, не postulate.

---

## §3. Open leaves (индекс)

- **§3.9 DA:** long-run exact `n` conservation on contour (T-readout шум); D2Q9 ladder §3.8 step 2 only if hex fails vortex test
- **§3.10 SU(2):** full SM electron-from-`hV` sim (anchor `m_e` via `electron_v_p_anchor` ✅ algebra only)
- **§3.11 symmetries:** long-run **`g·P≠P·g`** on vortex (chirality dance §9.2)
- **§3.6 isotropy:** macro radial probe — open
- **§3.7 GPU:** T1-круг · Gaussian head-on · vortex axis ratio · hex §3.8 if square shows
- **§3.8 hex:** гипотеза до GPU-leaf; метрика anisotropy контура vortex
- **§4.1.2 ν_CA:** fit **`ν_eff`** vs algebraic **`ν_CA`** — T6
- **§4.9 Young:** GPU leaf barrier + detector screen + slit — open
- **§5.0 binary ρ:** occupancy readout on T — open
- **§5.0.1 Arg mass:** sim `m_H` vs N_вихрей — open
- **§5.0.3 antimatter:** sim VORTEX_P + VORTEX_M → n_net→0 + 2-front — open
- **§5.2.2 κ_link:** sim ballistic check on `c` — open
- **§5.3 gas:** sim EOS / `P(ρ)` readout — open
- **§5.3.2 v_s:** численный `v_s` on T-readout — open
- **§5.3.3 VdW:** T compression / occupancy — open
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
| CR + **`cr_strength`** | ✅ shipped · verify **`A9` FAIL** — §2.1 |
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
| **`U(1)_vac`** | ⚠️ verify **`U1_vac` FAIL** — §2.1 |
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
| 2026-09-22 | §2.1 | реестр фундаментальных ограничений · цикл наложения · honest verify |
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

**Последний полный M-verify (2026-09-22):** **`LadderLedger`**, **`MatterOccupancyB`**, **`PlanckVacuumFloor`**, **`Theorem_2_3_8`** PASS · **`A9`**, **`SO2_C4`**, **`U1_vac`**, **`A14`**, **`A10`** (evolution) FAIL — детали **§2.1**.
