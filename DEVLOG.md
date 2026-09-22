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

Живой статус `verify_principles.py` / `validate_mt.py`. Физика условий — MODEL §2.

| # | Verify / impl |
|---|---------------|
| A1 | ✅ структура M |
| A2 | ✅ структура M |
| A3 | ✅ `local_ca` (M) · **`Leapfrog`** bit-exact on Z_N[i] |
| A4 | ✅ **§3.10** · impl SU(2) |
| A5 | ✅ gate в §3.4 |
| A6 | ⚠️ мотив linear step; **не доказано для полного `g`** |
| A7 | ✅ **`rho_max` clamp** · `clamp_density` |
| A8 | ✅ gate asymptotics + `w(ρ)` |
| A9 | ✅ **§3.9** · impl **`cr_strength` + holomorphy sync** |
| A10 | ✅ **§3.9** · seeds **`n∈{±1,±2}`** · T contour readout |
| A11 | ✅ **§3.7–§3.9** · A11 PASS · T-readout binomial |
| A12 | ✅ T1 PASS (512² CUDA) |
| A13 | ✅ **§3.12** · **`Leapfrog`** bit-exact |
| A14 | ✅ **`U1_vac`** · **`Chiral_SU2`** · P/C seeds · ⚠️ long **`g·P`** |
| A15 | ✅ **`κ_link`** · **`α*`** · **`sync=κ_link·Δφ_min`** (§5.2.3) |
| A16 | ✅ **§3.10** · SU(2) + **`pauli_phi`** + verify |

**Легенда:** ✅ слой M · ⚠️ impl/sim · ❌ не разбирали.

---

## §2. Audit · gap tracker

| величина | статус | gap |
|----------|--------|-----|
| **`κ_link`, `γ`, `cr_strength`, `ν_CA`** | ✅ **`¼`** | — |
| **`s₀`, `p₀`, `L₀`, `E₀`, `F₀`, `g_M`** | ✅ §5.2.1 | — |
| **`sync`, Pauli, `ρ_Q`, `n_E` map** | ✅ §5.2.3 | sim verify **EnergyLedger** open |
| **`R(Φ)=ω^Φ` vs `exp(i·Θ·σ/2)`** | ✅ §3.10.3 · §3.12.5 | verify **`DiscreteRotExp`** |
| **`b ∈ {0,1}`** | ✅ §5.0 / §5.2.3 | sim primary readout — open |
| **`α_s`, G_F, динамическая метрика** | ❌ | **model-gap** SM/GR |

Verify: **`QuarterQuantum`**, **`EnergyQuantum`**, **`ElementaryQuanta`**, **`Rho_P_binary`**.

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
| CR + **`cr_strength`** | ✅ shipped · A9 PASS |
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
| **`U(1)_vac`** | ✅ verify **`U1_vac`** |
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
| §5.2.1 mechanical | ✅ **`MechanicalQuantum`**, **`LocalContinuity`**, **`SO2_C4`** |
| §5.2.3 elementary | ✅ **`ElementaryQuanta`** · **EnergyLedger** verify open |
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
| 2026-09-22 | §0 | genesis narrative → DEVLOG §7; MODEL = postulates only |

---

## §7. Genesis (диалог → M)

**Не SSOT.** Как пришли к каркасу — история разработки; физика — **MODEL §0–§8**.

**Вход:** GR — гравитационное замедление времени (метрика, geodesics, redshift) → мотивация дискретного времени.

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

**Последний полный M-verify:** все checks PASS (кроме намеренных `A3_diffusive`, `T_dft_oracle`).
