# DEVLOG — журнал разработки

**Не SSOT физики.** Хронология сессий, статус реализации, открытые задачи, снимки верификации.

SSOT: [`MODEL.md`](MODEL.md) + [`model/`](model/) · META: [`META.md`](META.md) · протокол: [`BUILD.md`](BUILD.md)

---







## 2026-09-26 · DDD · убрать readout из API

`survey_probe`, `survey_at_site`, `SiteSurvey`, `nu_coarse_passes`, `m_rest_macro`, `check_t_hydro_limit_bundle`, `macro_slice_stats`, `cmb_forward` в yaml. Удалены `readout_probe`, `human_readout`, `run_gpu_readout`.

Removed: `grid.py`, `*_hex_slice` scenario aliases, `run_spec_cube`/`open_simulator`, draft `floor0_resonance*`. One API: scenario id + `embedding`.

## 2026-09-26 · mt_ca.app · scenario ⊥ embedding

**Fix:** сценарий = только условия (habitat/seed); **2+1 / 3+1** — поле ``RunSpec.embedding``, не отдельный «hex scenario». Алиасы ``*_hex_slice`` → тот же scenario + embedding 2+1.

## 2026-09-26 · mt_ca.app · lattice + lab (2+1 vs 3+1, instruments SSOT)

**Критерий готовности:** `dimension.py` (`LatticeDimension`), `lattice.py` (`build_run_spec`, `open_lattice`), `lab.py` (`LabSession`, `open_lab`, `planckon_lab_report`). CLI: `list` (dim column), `panel`. Verify: `Instrument_panel_*` canon vs hex_slice; `Planckon_instrument_fcc` → lab. Tools/probes via `open_lab`.

**Stack:** scenario → lattice → lab (instruments always `sim.cfg`; T-panel `plane_mconfig` on gate plane).


**Критерий готовности:** дефолт симов — **FCC 3+1** через `mt_ca/app` (`scenario.py`, `grid.run_spec_cube`, `open_simulator`); hex только `*_hex_slice`. Floor0 probes (`runner`, `si_floor0_rows`, `boil_ocean_periodicity`) на `floor0_planckon` / `habitat_boil`; anchor после settle; макроописание gate-plane `plane_mconfig`.

**Verify:** `Brick_internal_spectrum`, `Floor0_phase_space`, `Floor0_nE_excitation` PASS on FCC 32³ (CPU).

## 2026-09-26 · §5.0.4-A · n_E≥1 kick-harness (floor 0)

**Критерий готовности:** `run_floor0_nE_excitation_harness` — planckon on `VACUUM_BOIL`, settle 64, track 32; ledger `projected_phi_int` at core hits `n_E≥1` under free `g` (settled snapshot stays `n_E=0`).

**Verify:** `Floor0_nE_excitation` PASS · probe `tools/floor0_catalog_probe.py --excitation`.


## 2026-09-25 · mt_ca.app — SSOT simulation application

**Критерий готовности:** `mt_ca/app/` — habitat presets, `ScenarioSpec` registry, `RunSpec`/`RunResult`, `gate_b`/`peak_stats`, `runner.run()`, CLI `python -m mt_ca.app`.

**Scenarios:** `habitat_boil` (default live), `habitat_frozen` (control), `floor0_planckon`, `birth_*`.

**Wired:** `si_floor0_rows.floor0_phase_space_row` → `run_floor0_phase_space`; scripts `run_filled_bath_emergence`, `run_seed_family_scan`, `run_seed_brick_scan` use app gates/runner.

**Habitat rule:** no void — 2D excitations on `VACUUM_BOIL`; `simulator.reset` default = boil.


## 2026-09-24 · §8.2·units·T_P — independent of k_B (closed)

**Критерий готовности:** T_P:=E_P=ℏ/t_P; T_P_M:=E_0. No separate Θ on M. k_B/kelvin = T-export only.

**Code:** `SI.planck_temperature_independent_row()` · verify `Planck_temperature_independent`.


## 2026-09-24 · §8.2·units·time-first FIX — step 3 is [M]=m_P, not G

**Критерий готовности:** Cascade t_P → l_P=c·t_P → m_P=ℏ/(c²t_P). G=ℏc/m_P² is consequence only.

**Code:** `SI.units_time_first_cascade_row()` · verify `Units_time_first_cascade`.


## 2026-09-24 · §8.2·units·time-first — t_P → l_P → G (closed)

**Критерий готовности:** Ontology: time quantum first; metre = light-path in one quantum; G = c⁵ t_P²/ℏ exact.

**Code:** `SI.units_time_first_cascade_row()` · verify `Units_time_first_cascade`.


## 2026-09-24 · §8.2·[T]·t_P — time dim = t_P; M tick hT (closed)

**Критерий готовности:** [T]=[L]/[V] ⇒ t_P=l_P/c. M tick hT=κ·t_P. SI-2019 Cs second = T-export tautology twin of c-fixed metre.

**Code:** `SI.time_dim_from_tP_row()` · verify `Time_dim_from_tP`.


## 2026-09-24 · §8.2·[L]·l_P — length dim = l_P; hierarchy from α (closed)

**Критерий готовности:** Natural unit l_P. Exact α ⇒ Compton/Bohr/r_e = N_c, N_c/α, α·N_c hops. Not SI-metre fit.

**Code:** `SI.length_dim_from_lP_alpha_row()` · verify `Length_dim_from_lP_alpha`.


## 2026-09-24 · §8.2·meter·decouple — SI metre ∉ M (closed)

**Критерий готовности:** After α is closed, SI metre is fully off the M board. Lengths = hops of hL. α / masses / N_a0 never consult the metre. SI-2019 + optical a0 + √(ħG/c³) = T-export only.

**Code:** `SI.meter_decouple_from_M_row()` · verify `Meter_decouple_from_M` · MODEL §8.2·meter·decouple.


## 2026-09-24 · §8.2·α·meter fint — N_a0/a0 макроописание (closed α-path)

**Критерий готовности:** meter/optical a0 is **not** an input to α. Preferred α + upstairs cascade predict `N_a0=N_c/α`, `a0=N_a0·l_P`. Optical Bohr ≈ T-door ~0.45%. H→ℤN_a0 without α remains OPEN census (does not block α).

**Code:** `SI.alpha_meter_na0_bridge_row()` · verify `Alpha_meter_na0_bridge` · MODEL `08-alpha` / `08-units` §8.2·α·meter.

**Numbers (preferred):** N_a0≈3.259×10²⁴ vs optical ≈3.274×10²⁴ · rel≈0.448%.


## §0. Граница MODEL / DEVLOG / META / BUILD

| | **MODEL** | **DEVLOG** | **META** | **BUILD** |
|---|-----------|------------|----------|-----------|
| Роль | SSOT `g` — MODEL + `model/00`…`06` | реализация / верификация / открытое | космология | протокол сборки |
| Спор «что делает g?» | MODEL | — | — | — |
| «догнали ли код?» | — | **DEVLOG** | — | BUILD |
| «что видит мозг?» | — | — | META | — |

**Правило:** provenance, ✅/⚠️, open leaves, GPU DoD, даты сессий — **только DEVLOG**. MODEL не датирует разработку.


---

## §1. Реестр ограничений (единый указатель)

**Один экран.** Строка = известное ограничение → что требует от **`g`** → где в **MODEL** → **gap** → **verify** → **impl** → **следующий шаг**.

**Метод:** ansatz **`g`** → наложить известное. **`l_P = √(ℏG/c³)`** — естественная длина; **`L = f·l_P`**. Нет **`hL→0`** на M — макроописание T вверх (MODEL §0.4).

**Gap:** **—** закрыто · **sim** MODEL есть, код нет · **model** ещё не выведено в MODEL · **T** метрика T.

**Verify:** `python verify_principles.py --device cpu` · T: `validate_mt.py` · snapshot **2026-09-22**.

### A1–A16

| # | Условие (суть) | Что требует от **`g`** | MODEL | gap | verify | impl | следующий шаг |
|---|----------------|------------------------|-------|-----|--------|------|---------------|
| **A1** | **Каузальность** — за **`hT`** не дальше **`l_P`** | равные light-like NN; канон **FCC N₁₂**; Мур/2-я оболочка ✕ | §1.3 · §1.6 | — | **`FCC_N12`** PASS (16-tick, **HF ON**) | `laplacian` fcc · default | — |
| **A2** | **Локальность** | **`g(x)`** только из ε-окрестности | §2 · §0.3 | — | — (структура) | `projected_collision` | — |
| **A3** | **Унитарность** | **`Σ|z|²`** invariant; rotation, не damping | §2 · §5.2.1 | — | **`Leapfrog`** · **`A3`** · **`A3_global_norm`** PASS | `reversible` · `z_ring` | гладкая непрерывность → **T** |
| **A4** | **U(1)/SU(2) спинор** | **`z∈ℂ²`**, **`R(Φ)`** unitary | §2 · §3.10 | — | **`A4`** · **`SU2_360/720`** PASS | Rot_LUT · `su2_apply` | — |
| **A5** | **Абс. ноль недостижим** | boiling vac; **`z≡0`** excluded | §2 · §0.5 | sim | **`A5`** · **`PlanckVacuumFloor`** PASS | `heisenberg_floor` · seeds | ≠ D5 при floor — MODEL §2.3.8 |
| **A6** | **2-й закон локально** | mixing ↑ entropy | §2 | model | **`A3_diffusive`** anti · full **`g`** не доказано | legacy `linear_step` | вывести для full **`g`** или ослабить claim |
| **A7** | **`ρ ≤ ρ_P`** | **`K_P`** в Φ; clamp | §2 · §3.12.5 | sim | **`A7`** PASS | `bekenstein_scale_spinor` | — |
| **A8** | **Macro-линейность** | **`w(ρ)`** затухает | §2 · §3.4 | T | **`A8`** PASS | gate **`w(ρ)`** | макроописание T probes |
| **A9** | **CR / голоморфность** | **`g`** держит аналитичность | §2 · §3.9 | sim | **`A9`** stationarity PASS · plateau ceiling open | `cr_phi_int` in Φ | absolute ν_CA band |
| **A10** | **`n ∈ ℤ`** | winding **`∂(hV)`** | §2 · §5.0 | — | seeds OK · **`A10`** evolution PASS (HF off) | `topology` · seeds | — |
| **A11** | **Soliton / anti-smear** | **`K_P+Δφ`** держит ядро | §2 · §3.7–§3.9 | sim | **`A11`** PASS | saturating Φ | — |
| **A12** | **Lorentz / isotropy (T)** | macro круг **`κ=1/√2`** | §2 · §1.1 · §4.1 | T | T1 PASS (512²) | `macro` binomial | radial probe — open |
| **A13** | **Обратимость** | leapfrog на **`ℤ`** | §2 · §3.12 | — | **`Leapfrog`** PASS | `projected_step_fixed` | — |
| **A14** | **P/C/T/U1** | симметрии на **`g`** | §2 · §3.11 | — | **`A14`** · **`U1_vac`** · **`SO2_C4`** PASS · **`Chiral_SU2`** PASS | `symmetry` · `chiral` | g·e^{iθ} on Z_N Q-gap (invariants OK) |
| **A15** | **Геометрия / kappa_link** | kappa из многогранника; gamma = 1/N; канон N=12 | §1.6 · §5.2.2 | sim | **QuarterQuantum** PASS (MVP 1/4) | `si_constants` | FCC 1/12 row |
| **A16** | **Pauli / 720°** | **`2π→−1`**, repulsion | §2 · §3.10.4 | sim | **`A16`** · **`Pauli`** PASS | `pauli_phi` | — |

**§2.3 (блок):** ¬heat death · fixed points · Planck floor — MODEL §2.3 · **`NoMHeatDeath`** · **`Theorem_2_3_8`** · **`PlanckVacuumFloor`** PASS.

### Линейка · форма **`g`** · §5.2 (не отдельные A#)

| ограничение | MODEL | gap | verify | следующий шаг |
|-------------|-------|-----|--------|---------------|
| **`hL=l_P`**, **`B_hV`**, **`N_ring=512`** | §0 · §3.12.6 | — | **`HvBitBudget`** PASS | — |
| **тайл / ε:** **FCC N₁₂** default sim · гекс=срез (2+1) · n4 archive | §1.3 · §1.6.1 | — | **`FCC_N12`** PASS (пол ON) | true Bravais parity leaf open |
| **лестница ФТТ:** `G`, BZ, умклапп, `N_pack`, `b_atom` | §5.2.4 | model | — | quanta + probe |
| leapfrog **`2Z+⌊𝒩⌋`**, **`Φ(K_P,ζ,ρ)`**, **`R(Φ)=ω^Φ`** | §3.12.5 | sim | **`Leapfrog`** · **`DiscreteRotExp`** PASS | ledger-neutral kick distribution |
| **`s₀→p₀,L₀,E₀`**, **`κ_link`** (`¼` MVP / `⅙` hex / `1/12` FCC) | §5.2 · §1.4 · §1.6 | — | **`MechanicalQuantum`** · **`QuarterQuantum`** PASS | FCC/hex row |
| **`div j`**, **`ΣΔπ mod p₀`**, **`L_z`**, **`n_E` ledger** | §5.2.1–§5.2.3 | sim | **`LadderLedger`** PASS (proxy) | полный star closure на step |
| **`b` из n_partial, не amp²** | §5.0 · §5.2.3 | sim | **MatterOccupancyB** PASS | T occupancy — open |
| **4 силы** · v · α_s · Weinberg · α(MZ) · m_W,m_Z · **G_μν=8πℓ_P²T** · **CKM λ=3/13** | §8.4.1–§8.4.4 | census / IR / stencil / Aρη | EW+GR+CKM скелет ✅ | census · IR · stencil · Aρη |
| **Higgs = T-пена** | §5.0.1 · §8.3.1 | T | — | bare `v/2`; +`N_hier·α_fs/(4π)` → ~125.31 GeV; FCC-tail open; width open |

**Приоритет отставание симуляции:** A9 absolute ν_CA plateau · FCC bulk CR · Young/tunnel/census leaves.

**Цикл:** (1) строка реестра → (2) есть в MODEL? иначе **пробел в MODEL** → (3) режет **`g`**? impl отстаёт → **отставание симуляции** → (4) T-only → **`validate_mt`** → (5) несовместимость → правим MODEL/ansatz, не порог verify.

---

## §3. Open leaves (индекс)

- **§3.9 DA:** long-run exact `n` conservation on contour (макроописание T шум); D2Q9 ladder §3.8 step 2 only if hex fails vortex test
- **§3.10 SU(2):** full SM electron-from-`hV` sim (algebra `m_e=α²·m_H/N_φ` ✅ · `Electron_mass`; sim census still open)
- **§3.11 symmetries:** long-run **`g·P≠P·g`** on vortex (chirality dance §9.2)
- **§3.6 isotropy:** macro radial probe — open
- **§3.7 GPU:** T1-круг · Gaussian head-on · vortex axis ratio · hex §3.8 if square shows
- **§5.0.5:** `ρ_Θ` — Heisenberg matter/phase-density (аналог `ρ_e`); не путать с `|z|²` океана — sim leaf
- **§5.0.4-A:** внутренний спектр планкона — landmarks + vortex ground + SU(2) 2π/4π ✅ (`Brick_internal_spectrum`); **n_E≥1 excitation sim** + полный каталог состояний — open
- **Глоссарий:** `model/00-glossary.md` — планкон / **планковская дырка** ($b=0$, аналогия дырочной проводимости) / планковская ячейка / вакуум; sweep MODEL+book (`scripts/apply_planckon_glossary.py`)
- **§5.0.4-B:** внешние оболочки ε / отбор — open (этаж 1)
- **§1.6.5:** один КА-схема; `|N|` только от упаковки размерности — не «гекс↔FCC переключатель»
- **§1.6.4:** Minkowski `(3+1)FCC ↔ (2+1)hex` — погружение слоя `{111}`; якорь `c` на 4D — open bulk-coupling
- **§1.6 / §5.2.4:** 3D FCC кандидат; лестница BZ/умклапп/`N_pack`; asympt. κ_FCC — open
- **§3.8 / §1.4 hex:** 2D кандидат; мост `κ=√3/2`; impl MVP ещё `N₄`
- **§4.1.2 ν_CA:** fit **`ν_eff`** vs algebraic **`ν_CA`** — T6
- **§4.1.0 FCC/hex Green:** depth-2 path-Green algebra ✅ (`mt_ca/t_analysis.py`); R-fold accumulation / soft sim leaf open
- **§4.1.1-HL hydro:** Thm **T-HL** algebra ✅ (`T_hydro_limit`: `M=(4/3)I`, `Ŵ=1−(2/3)|k|²`, `κ=1/12` → NLSE+ν / NS-class); live FCC R-fold + `ω_macro` fit open
- **§4.9 Young:** GPU leaf barrier + detector screen + slit — open
- **§4.10 tunnel:** slab barrier $N$ · $|\mathcal{A}|\sim\tau^N$ · WKB continuum — open DoD
- **§4.9.2a birth:** $V\mapsto(n,Q,\chi,s,E,b,m)$ формулы ON · `SI.birth_row` live ($m_e$, $m_p$ check)
- **§5.0 binary ρ:** заполнение на T on T — open
- **§5.0.1 Arg mass:** **`m_H=m_P α_fs⁸ √(π/2)`** ✅ algebra · width/lineshape open
- **§5.0.3 antimatter:** sim VORTEX_P + VORTEX_M → n_net→0 + 2-front — open
- **§5.2.2 κ_link:** sim ballistic check on `c` — open
- **§5.3 gas:** sim EOS / `P(ρ)` макроописание — open
- **§5.3.2 v_s:** численный `v_s` on макроописание T — open
- **§5.3.3 VdW:** T compression / occupancy — open
- **§8.4.1–§8.4.4:** α_s runner ✅ · girth ✅ · GR+Эйнштейн ✅ · Weinberg+α+массы ✅ · **CKM $N_{gen}=d$, $\lambda=3/13$** ✅ · stencil/GW/Λ / census / IR / Aρη — open
- **§8 Higgs:** **`m_H` algebra** ✅ · width / lineshape leaf open
- **§8.2·vac:** A5 bath **`ρ_E(z_min)`**, **`T_M,bath`** order ✅ · Bose **`u(ω)`**, **`ω(k)`** DOS — open

---

## §4. Статус реализации по разделам


### §3.3–3.4 float prototype (historical · not M tick)

Ранний float U(1) scalar path — **не** §3.12. Оставлено здесь, не в MODEL.

**§3.3 split-step δS:**
```
S = Σ_{links} Re[ conj(z_x)(z_y - z_x) ] + Σ_x V(|z|²)
z* = local_ca(z; γ)
φ  = 2π · ( (1+r) / (|z*|² + ε) - 1 ) · w(ρ)
z' = z* · exp(i φ)
```

**§3.4 isotropic scalar gate:**
```
ζ = (Σ_N z) · z*
φ = 2π · ( (1+r)/(|z|²+ε) · Δφ − 1 ) · w(ρ)
z' = z · exp(iφ)
```

Физика phase wrap **`ζ=(Σz)·z*`** перенесена в MODEL **§3.4** (holonomy carrier only).

### §3.6 Isotropic streaming

- ✅ derived · T1 **micro≈1.0**
- macro radial probe — open
- legacy `local_ca`: micro ~1.25

### §3.7 Heisenberg · anti-smear

**Хронология (2026-09-22):** дилемма «чернила в воде» закрыта на M (§3.7.2); impl/sim — backlog ниже.

**§3.7.4 Impl/sim v3 backlog (не SSOT):**

| probe | метрика | isotropic | local_ca |
|-------|---------|-----------|----------|
| один Gaussian σ=5, 192 steps | `max(coarse)_late/0` | **0.15** | 0.32 |
| два Gaussian σ=6, 256 steps | `max(coarse)_ratio` | **0.12** | 0.28 |
| T2_collision (δ) | `peaks_late` | 2 | 2 |

**Не вердикт M:** `mt_ca` v3 + coarse — **догоняют** §3.7.2–§3.9.

### §3.9 DA / CR

| пункт | статус |
|-------|--------|
| **Φ = saturating ζ only** (§3.12.5) | ✅ 2026-09-23: CR residual / sync **не** второй канал Φ — дефект Arg(⟨z⟩/z) = Δφ_N **внутри** gate |
| **`Δφ` Heisenberg** | ✅ snap-*down* subthreshold → 0 (snap-up качал amp; Φ=0 локально OK §2.3.8) |
| winding **`n`** | ✅ **`A10` PASS** HF ON · `winding_robust` |
| holomorphy sync float | float `holomorphy_sync_step` — T/legacy; **не** в projected `g` |

**Verify A9:** `PLANE_WAVE` · HF ON · burn-in 32 + settle 32 · stationarity на gate-only. Absolute ν_CA ceiling — open.

**Dogfood:** CR+sync как extra Φ → fill; без них + Heisenberg-класс вакуум → vacuum/vortex устойчивы, `n` живёт.

### §3.12.6 / IC

| пункт | статус |
|-------|--------|
| Vacuum ocean | ✅ полный Z_N кирпич · **N_φ=13** класс (не RNG) · `phase_class=0` U(1)_vac gauge |
| SeedClass | VACUUM / IMPULSE / PLANE_WAVE / VORTEX_* поверх океана |

### §3.10 SU(2) · Pauli

**Хронология (2026-09-22):** «без спина Вселенная плоская и мёртвая».

| слой M | impl (`mt_ca`) |
|--------|----------------|
| **`z ∈ ℂ²`** | ✅ единственное поле |
| **SU(2) gate** | ✅ **`su2_apply`** |
| **360° → −1** | ✅ **`SU2_360`** |
| **720° → +1** | ✅ **`SU2_720`** |
| **Pauli на `v_p`** | ✅ **`pauli_phi`** · **`Pauli`** |

### §3.11 Symmetries

**Хронология (2026-09-22):** «доводи impl» — global phase не ломает `g`.

**Impl-gap (closed 2026-09-22):** `defect_axis → [0,0,1]` ломал U1 на PLANE_WAVE → fix `axis ← n_z`.

| слой M | impl |
|--------|------|
| **`U(1)_vac`** | ⚠️ verify **`U1_vac` FAIL** — §1 |
| **`P_L/P_R`** | ✅ **`chiral.py`** · **`Chiral_SU2`** |
| **projected 𝒩 on Z_N[i]** | ✅ **`projected_collision.py`** |
| **CPT product** | optional · `run_symmetry_probe.py` |
| **A14 bundle** | ✅ P/C/U1/chiral · long **`g_P_steps`** logged |

### §3.12.4 Module map (was MODEL §3.12.4)

| слой | модуль |
|------|--------|
| **`Z_N[i]`** ring ops | **`z_ring.py`** · **`N_ring = 512 = 2^9`**, mod from §3.12.6 |
| Planck **`⌊·⌋`** encode | **`fixed_point.py`** · **`frac_bits=6`**, **`mod_bits=9`** |
| **projected 𝒩** | **`projected_collision.py`** · default **`use_projected_collision=True`** |
| **`g` 2-го порядка** | **`reversible.evolve_canonical`** · **`projected_collision.py`** |
| `(Z, Z_past)` + ledger | **`simulator.py`** |
| декодирование для T | **`fixed_point.decode_spinor`** — T/UI, not tick |

### §3.12 Leapfrog Z_N[i]

**Хронология (2026-09-22):** float32 1-го порядка на 4070 → киральная «пляска» `n`; leapfrog на ℤ — единственный закон счёта.

| слой | impl |
|------|------|
| forward | **`projected_step_fixed`** |
| reverse | momentum ledger · **`Leapfrog`** bit-exact |
| gauge-fix encode | ✅ U1 equivariance |

### §4 T-layer

| раздел | статус |
|--------|--------|
| §4.1.2 **`ν_CA`** | ✅ algebraic · verify **`Nu_CA`** · **`T3_macro_viscosity`** · fit **`ν_eff`** open |
| §4.1.0 **(1-2-1) derive** | ✅ из A1: глубина 2 = return-paths; `⊗` только product-срез; FCC Green — open |
| §4.3 Madelung continuity | ✅ **T** · **`T_MadelungContinuity`** (диагностика; не M hard) |
| §4.9 Young | ✅ онтология · GPU slit leaf open · partial T2, A11 |
| §4.2 validate | **`validate_mt.py`** T1/T2/T3/T_dispersion · T2 aligned §4.9 (vortex soliton · dual Gaussian · 1-2-1 fringes OK) |

### §5 Matter · quantization · gas

| раздел | статус |
|--------|--------|
| §5.0 binary ρ | ✅ **`Rho_P_binary`** · occupancy T — open |
| §5.0.1 Arg mass | ✅ **`Arg_mass_carrier`** · **`T_zigzag_mass`** · sim open |
| §5.0.3 antimatter | ✅ A10 seeds · annihilation sim open |
| §5.2.1 mechanical | ✅ **`MechanicalQuantum`**, **`A3_global_norm`**, **`LadderLedger`** · smooth continuity → **T** |
| §5.2.3 elementary | ✅ **`ElementaryQuanta`** · **`LadderLedger`** · **`MatterOccupancyB`** |
| §5.3 gas / VdW | ✅ algebra · sim EOS open |

### §8 SM / Higgs

- ✅ онтология M→T · **v / α_s / Weinberg / α(MZ) / m_W,m_Z / G_μν / CKM λ=3/13** ✅ · **`m_H=v/2`** ✅ (~123 GeV; stack ~125.31) · **`m_p`** α·v/2·(1+κ²/N₁₂) ✅ · **`m_e`** α²·m_H/N_φ ✅ · **`m_n=m_p+2m_e`** ✅ · **`m_ν^(atm)`** α⁵·2m_H/(N_hier N_φ) ✅ · width / μ,τ / Γ_n / PMNS open · не refute LHC — переинтерпретация слоя

---

## §5. Хронология (цитаты сессий)

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
| 2026-09-22 | §8.4.2-D · §8.4.4 | $G_{\mu\nu}$ из strain+$8\pi\ell_P^{2}$ · CKM $N_{gen}=d$, $\lambda=3/13$ |
| 2026-09-22 | §8.4.3-D/E | бегунок α: $1/\alpha(M_Z)=1/\alpha_{fs}-B_{hV}$ · дерево $m_W,m_Z$ |
| 2026-09-22 | §8.2 Кулон | $F=\alpha_{fs} F_P n_1 n_2/N^{2}$ из носителя · `SI.coulomb_row` |
| 2026-09-22 | §8.2 Максвелл | Arg/j/Madelung/$K_P$ → E,B,J,c · `SI.maxwell_row` · sim ≠ пробел в MODEL |
| 2026-09-22 | §8.2 планк. ЭМ | M: $s_0/F_0/j$/Гаусс/Кулон $N=1$ · не ∇ на $\ell_P$ · `SI.planck_em_row` |
| 2026-09-22 | §8.2 Stokes+$\Phi_\square$ | дискретный контур = сумма рёбер · $B_\square=\Phi_\square/\ell_P^{2}$ |
| 2026-09-22 | §8.2 Lorentz из $K_P$ | $c^2=K_P/\mu_P$ + binomial(1-2-1) → макро-круг; ЭМ-блок закрыт контуром |
| 2026-09-22 | §8.2 излучение | $h\nu_0=4\pi E_0$ · $n=0$ · Debye $\omega_D$ · Bose $u(\omega)$ open · `SI.radiation_row` |
| 2026-09-22 | §8.2·5 | занятость $\langle n\rangle$/дискр.RJ = T-стат (§2.1), не закон M · M✅ квант+$n=0$ Bose-capable+BZ · Planck open |
| 2026-09-22 | §8.2 radiation hinges | $\mu=0$✅ схема · open: $T_\gamma$, $\omega(k)$, $g_{\mathrm{pol}}=2$, A6→мера, осциллятор |
| 2026-09-22 | §8.2 распад | аннигиляция≠распад · free $\gamma$ / одиночный $n\pm1$ стабильны · $\Gamma,\tau$ open · `SI.decay_row` |
| 2026-09-22 | §8.2 lemma | $m\ll m_P\not\Rightarrow$ must decay · масса≠стабильность · кирпич≠свободная $m_P$ |
| 2026-09-22 | §8.4.2-G | Diff hinge: фиксированная решётка ≠ Diff · DoD = 2 моды + PPN γ→1 · anti-BD |
| 2026-09-22 | §8.4.2-G lemma | ответ: $g$=описание деформации T, не free $h$ · Diff не axiom на FCC · verify = спектр IR |
| 2026-09-22 | §8.4.2-C′ | strain: $\varepsilon_e[\delta\rho]\to\ell_e\to\theta_f$; $h_{0i}[\Delta\varphi_e]$; не $\varepsilon\propto\Delta\varphi$ |
| 2026-09-22 | §8.4.2-C′′ | физсмысл: $h_{00,ij}\leftarrow\varepsilon$ (strain≠Коши); $h_{0i}\leftarrow$ Madelung; Regge пассивен |
| 2026-09-22 | §8.4.2-C′ | $\ell_P=\mathrm{const}$; $\ell_e$ = эффективная Regge-длина, не деформация шага |
| 2026-09-22 | §4.10 | tunnel M→T: leak$\to\tau^N=e^{-\kappa L/\ell_P}$ · sim slab DoD open |
| 2026-09-22 | §4.9.2a | birth = lock-in germ $V$; M-ID = invariants ($n$, Pauli, $E$); SM-словарь open |
| 2026-09-22 | §3.12.5a | $\varepsilon$ in $\Phi$-kick · $Z^{+}=2Z+\lfloor\mathcal{N}[\varepsilon]\rfloor-Z^{-}$ · $m_{\mathrm{loc}}\le m_P$ |
| 2026-09-22 | §8.4.2-C′′′ | $D_\star$ BC · **не сшивка**: $|h_{\mathrm{near}}/h_{\mathrm{Newton}}|\sim 2\times 10^{3}$ · dual $\rho_{\mathrm{vac}}$ hinge |
| 2026-09-22 | SatBC sim | `strain_metric` · verify `SatBC_Cppp` PASS · near/N=2047.5 · far $h=0$ · vortex 32t: $h(R)$ flat ≠$1/R$ |
| 2026-09-23 | FCC+HF | объёмная FCC (12 соседей) с полом: vacuum/impulse/wave/vortex multi-tick ✅ · verify HF ON |
| 2026-09-22 | FCC N₁₂ | default stencil cuboctahedral · κ=1/12 · `FCC_N12` multi-tick **HF ON** PASS |
| 2026-09-23 | IC+HF | вакуум = N_φ класс, не RNG; HF snap-down; CR≠второй Φ |
| 2026-09-23 | §3.9/§3.12.5 | sim: extra CR/sync в Φ качал amp; gate=ζ only → A9/A10 HF ON |
| 2026-09-23 | §4.3 · §5.2 | гладкая непрерывность → **T**; M = A3 + discrete ledgers; **`T_MadelungContinuity`** |
| 2026-09-23 | §4.9 T2 | probes: soliton=vortex; wave=dual Gaussian; 1-2-1 = макро T (не M); fringes≠fail |
| 2026-09-23 | §4.1.0 | вывод `(1-2-1)`: атом `[1,1]/2` → `w∗w`; 2D `⊗`; FCC 3D multinomial — hinge |
| 2026-09-23 | §4.1.0 physics | A1: depth-2 return-paths → `[1,2,1]`; `⊗`≠hex/FCC; κ независимо от бинома |
| 2026-09-23 | §8.3.1 Δλ | empty-cell quantum `δλ=α_fs/(4π)`; stack `N_hier·δλ` → m_H≈125.31 (0.045%) |
| 2026-09-23 | §8.3.1 | `m_H=v/2=m_P α⁸√(π/2)` · топология: peak·√(π/2); `λ=1/8` описание SM |
| 2026-09-23 | §8.3.1 fix | снята фальш soft-wall «поля занятости»; `b`=бит, объём=`z` |
| 2026-09-23 | §8.2 m_p | bare `m_p=α_fs·v/2≈0.8979 GeV` (−4.3% PDG) · тот же контур что `m_H=v/2` · edge `1+1/24` кандидат |
| 2026-09-23 | §8.2 m_p pack | stack `1+κ²/N₁₂` (`κ=1/√2`, `N₁₂=12`) → m_p≈0.9353 GeV (0.32%); inscribed sphere, not soft |E| |
| 2026-09-23 | §8.2 m_e | bare `α²·(v/2)/N_φ`≈0.504 MeV (1.37%); stack `α²·m_H/N_φ`≈0.513 MeV (0.45%); `N_φ=⌈4π⌉=13`; `f_геом` = следствие |
| 2026-09-23 | §8.2 m_ν | atm `α⁵·2m_H/(N_hier N_φ)`≈0.04986 eV (0.21% vs √Δm²≈0.05); =`α³·m_e/(N_hier/2)`; sol/lightest lemmas |
| 2026-09-23 | §8.2·5 β | слабый $\Delta B=0$ класс $n\to pe\bar\nu$ **разрешён** (SU(2)/$P_L$+оболочка); $\Gamma$ open ($m_n$ closed §8.2·7) |
| 2026-09-23 | §8.2·7 $m_n$ | ledger поверх $m_{\mathrm{arg}}$/$\rho_Q$: $m_n=m_p+2m_e$ (квант $m_e$, $k=2$ min β); порог ✅; Δ~−20% vs PDG; `Neutron_mass` |
| 2026-09-23 | §8.2 SM→Planck | формулы-карточка: α,v,m_H,m_p,m_e,m_ν,m_n,m_W/Z из E_P+геометрии |
| 2026-09-23 | §8.2 α honesty | table model α digits fixed (was CODATA clone); Δ(α⁻¹)≈3e-4 ~2ppm |
| 2026-09-24 | §8.2·α·carrier-soft | носитель: homogenize = product local($N_4$+SU2)×global($M$); subtract soft unit restores layers · candidate, not sealed |
| 2026-09-24 | §8.2·α·7=N4+SU2 | семёрка soft unit: кандидат **фундаментальный** $7=N_4+3$ (крест+Паули); κ/n_□ — число/эхо; descent OPEN · `seven_N4_plus_SU2` |
| 2026-09-24 | §6·seed·brick·scan | VACUUM_BOIL = N_φ Heisenberg bricks (full fill); reject N_ring ramp ring-scan; seeker → run_seed_brick_scan |
| 2026-09-24 | §0.10·gpu·eng·tail·close | floor+seed / R(Φ)≠Euler / SI literals closed as MODEL макроописание; §10→eng pointer · Gpu_eng_tail_close PASS |
| 2026-09-24 | §1.7·torus·close | finite wall-free Λ=T³/T²; Λ×S¹=phase fiber; reject walls/sphere; N soft; eng wrap=макроописание · Carrier_torus_close PASS |
| 2026-09-24 | §6·floor1·C3·bath·контрольный расчёт | VACUUM_BOIL contrast grows; **b=1 after densitometer dual-channel** (stale emerged_b=False was blind A10); gauge VACUUM frozen · Floor1_C3_bath_контрольный расчёт PASS |
| 2026-09-24 | §6·floor1·C3·gamma·reopen | alone n_ticks=1 coarse soft (void artifact?); continuum≠M kept · Floor1_C3_gamma_close PASS |
| 2026-09-24 | §6·floor1·C3·gamma·close | reject continuum Γ on M; local C3 τ_M=1·hT · Floor1_C3_gamma_close PASS |
| 2026-09-24 | §6·floor1·leftovers·close | C3→C2+γ existence closed (Γ soft); ν off-band ≠N₁₂^{3…4} · Floor1_leftovers_close PASS |
| 2026-09-24 | §6·floor1·dressing·f·close | ρ_Θ=𝟙[|Δφ|≥Δφ_min]; reject continuum/α f; T-smooth=binomial · Floor1_dressing_f_close PASS |
| 2026-09-24 | §6·floor1·dressing·close | R_dress=1·dl: N₁₂<N_φ ⇒ 2π/N₁₂>Δφ_min; local star; multi-shell=excitation · Floor1_dressing_close PASS |
| 2026-09-24 | §6·floor1·dressing | ρ_Θ halo: R_min=1·dl (ε-star) closed; outer R_dress OPEN; reject Compton/α/forced N₁₂^{3…4} · Floor1_dressing PASS |
| 2026-09-24 | §6·floor1·B0·census | only stable B=0 matter @N₁₂³…⁴ = dressed lightest Q=±1; Q=0 blobs=pre-resonance · Floor1_B0_census PASS |
| 2026-09-24 | §6·floor1 | band ~N₁₂³…N₁₂⁴·dl; reject Compton/a₀/confining/N_gen as floor1 · Floor1_leptonic PASS |
| 2026-09-24 | §8.2·α·upstairs | cascade closed on α_preferred; PDG=T-door; soft floors open · Alpha_upstairs_mass_probe PASS |
| 2026-09-24 | §8.2·α·SI-bridge | α exact (κ,M,d,U; no u(α)); U0↔ħc=2κU0; CODATA=T-door only · Alpha_si_bridge PASS |
| 2026-09-24 | §8.2·α·nF·Thm | M=1+N₁₂·N_hier=97 — theorem from momentum registry lemmas (core+star); not free count · Alpha_nF_momentum_registry PASS |
| 2026-09-24 | §8.2·α·nF·census | seat table: 1 core + 12×8 hier = 97; F=F₀/97 ⇒ α=κ/97; combinatorial closed · Alpha_nF_momentum_registry PASS |
| 2026-09-24 | §8.2·α·M·g·try | M=1+N₁₂·N_hier=97 (core b + link×hier); α=κ/97 ~−1040ppm; → census · Alpha_M_from_g_try PASS |
| 2026-09-24 | §8.2·α·√2·descent | lemma: α=κ/M ⇒ α∉ℚ; reject exact p/q under force dual; fraction=κ/M not ℚ · Alpha_sqrt2_descent PASS |
| 2026-09-24 | §8.2·α·dual | method α=m/n two paths; alive: κ/M (M open), ae/(2r); reject M/512 single-path · Alpha_dual_fraction PASS |
| 2026-09-24 | §8.2·α·EM·faces | w_□/w_△/dihedral/V/S body ok but ≠α (wrong scale); α_geom=counts≠areas; OPEN Φ_□ · Alpha_em_face_weight PASS |
| 2026-09-24 | §8.2·α·Rydberg·Hall | R_∞=α²·r/λ̄_C (same phase residue r); R_K exact SI-2019 ≠ α source; same coupling OPEN · Alpha_rydberg_hall PASS |
| 2026-09-24 | §8.2·α·ae | ae=α·2r factors (2r closed, α open); pure-geo ae reject; door ≠ bypass coupling OPEN · Alpha_ae_cloud PASS |
| 2026-09-24 | §8.2·α·g2 | bare g=2 from A16×g_orb; ae_bare=0; reject r/2r/z_vac/α-input; OPEN A5 holonomy→ae · Alpha_dirac_g2 PASS |
| 2026-09-23 | §8.2·α·Schwinger | lab door ae; identity ae^(1)=2αr with r=1/(4π); 1/(2π)=2r geometry; open Dirac g=2 + A5→ae · Alpha_schwinger PASS |
| 2026-09-23 | §8.2·α·Arg-try | Arg identity Δm=m_arg/(2MN_a0) closed; best int M=97 ~−2080ppm; reject 137² / 1/(4π·11) / mass-cascade; derivation OPEN · Alpha_arg_binding_try PASS |
| 2026-09-23 | §8.2·α·mass-defect | QM floor: α=√(2Δm/m_e); U/BE=2; E_coul_NN/E₀=α/κ; BE/E₀~1.58e-27 soft Arg; DoD Arg→Δm OPEN · Alpha_mass_defect_optics PASS |
| 2026-09-23 | §8.2·α·descent | амнезия: vacuum→r→Ω→N_φ→charge; phase residue≠α; AFTER π-tower~2ppm / α_geom~263ppm; coupling fraction OPEN · `Alpha_descent` PASS |
| 2026-09-23 | §8.2·α·meaning | опора: α=phase↔vacuum coupling; фазовый остаток r=1/(4π); число=π-tower (removed); F/hops/κ/M = макроописание; discrete FCC fraction OPEN · `Alpha_meaning` PASS |
| 2026-09-23 | §8.2·F | сила на F₀: **α=κ/M**; M_target≈96.90; **M=97** −1040 ppm; **M=96=N₁₂N_hier** +9366 ppm; reject 137κ; π not replaced · `Alpha_force_lattice` PASS |
| 2026-09-23 | §8.2·H | `N_a0` (размер H): Thm5.2⇒ℤ; mass≡hop α² (не независимый размер); отвергнуто `N_c·137` и optical a₀ как M; OPEN = H structure/`N_pack` · `Na0_H_carrier` PASS |
| 2026-09-23 | N_a0 carrier | `na0_from_carrier_row` · **`Na0_from_carrier` PASS** — N_a0=(m_P/m_e)·137 (α_geom); stack FP inv≈137.089 (−384 ppm); pure 13/12/8/512 monomials OPEN; **N_c·137 path later rejected as α-input** |
| 2026-09-23 | α FP analytic | bare **closed form** `α_fp=[N_φ/(N_a0√(π/2))]^{1/11}`; stack poly `(2/π)α²³+(1/8)α²²=RHS²`; exponent **11=8+2+1** · **`Alpha_fixed_point` PASS** |
| 2026-09-23 | α fixed-point | **first FP in model**: `alpha_fixed_point_row` · **`Alpha_fixed_point` PASS** — α_fp=N_c(m_e(α_fp))/N_a0 (optical a₀); inv≈137.092 (~−408 ppm CODATA); seed-invariant; π-poly not α-input |
| 2026-09-23 | α hop + H | `Alpha_hop_ladder` + шаг шкалы (Бор): α=N_c/N_a0; α²=N_re/N_a0 (= power in m_e); v_Bohr/c₀=ακ; still identity, N_★/N_a0 from g OPEN |
| 2026-09-23 | α hop ladder | `alpha_hop_ladder_row` · **`Alpha_hop_ladder` PASS** — α=κ·N_re/N_c0=N_★/N_c0 after ℓ_P⊄c; **identity rewrite**, N_★ from g OPEN; π-ansatz not replaced |
| 2026-09-23 | §8.2 α bridges | verify **`Alpha_bridges`**: δλ=α·r, B_hV runner, N_φ=|N₁₂|+1, Coulomb carrier PASS; r³ cascade OPEN (~4%); e₀/sim OPEN |
| 2026-09-23 | META §3.0 | карточка «два времени»: A5-пена M (нет начала/конца) vs наблюдаемая UI (генезис есть); §0.6 · §2.3 · MODEL hub |
| 2026-09-23 | META §3.0.1 | наш пузырь: CMB→`N_tick` ✅; full `Ψ` via `g⁻¹` ✕ (ℬ); realistic = seed §3.6 + constraints |
| 2026-09-23 | META §3.0.1 fix | `t_SI=N·hT` exact on M (no макроописание); open = infer N + anchor N=0; N_today~10⁶¹ |
| 2026-09-23 | bubble_tick | `SI.bubble_tick_row()` + verify **`Bubble_tick`**: N_today≈1.141×10⁶¹, N_CMB≈3.146×10⁵⁶, t_start=0 |
| 2026-09-23 | §8.2·vac | A5 bath: `vacuum_bath_row` · `T_M,bath~10³¹ K` · `λ₀~l_P` · **`Vacuum_bath` PASS** · ≠ CMB · Bose open |
| 2026-09-23 | §7.4 a≡l_P | `anchor_a_is_l_P_row` · **`Anchor_a_lP` PASS** — one ruler hL; √(ℏG/c³) check only; m_arg via c₀ |
| 2026-09-23 | §0 Thm 0.1 | `discreteness_from_axioms_row` · **`Discreteness_from_axioms` PASS** — Postulate 0.1 → theorem from A1–A16+bit budget |
| 2026-09-23 | §0.7–0.8 · Thm 5.1 | `mechanics_from_axioms_row` · **`Mechanics_from_axioms` PASS** — g from A1–A16 (Cor 0.7); Landau ladder s₀→F₀ (Cor 0.8) |
| 2026-09-23 | §0.9 · Thm 5.2 | `excitations_full_quantization_row` · **`Excitations_full_quantization` PASS** — no wave on M; sound/light=quanta |
| 2026-09-23 | §5.2.6 phonon | `phonon_from_carrier_row` · **`Phonon_from_carrier` PASS** — v_a=2c0, k_max=pi/l_P, omega_D=2pi/hT from FCC WS |
| 2026-09-23 | §7.3 Planck←cell | `planck_from_cell_conditions_row` · **`Planck_from_cell` PASS** — ρ_cell=μ_P, u_P=μ_Pc², t_P/E_P derived via κ |
| 2026-09-23 | §7.2·κ bottom-up | Planck ladder embeds **c**; **κ_geom** from hull not **c/c₀**; **`Kappa_bottom_up` PASS** — **`hT=κt_P`**, **`c=κc₀`** check |
| 2026-09-23 | §8.2·geo·voronoi | rhombic dodecahedron WS: **`V=v_hV`**, **`R_in=a/2`**, **`V_hull/V=16/3`**, dual cuboctahedron · **`Rhombic_dodecahedron_geo`**, **`Rhombic_dodecahedron` PASS** |
| 2026-09-23 | §8.2·geo | cuboctahedron 1-tick: **`V_cubo=(16/3)v_hV`** at `a=l_P` · `cuboctahedron_geometry_row` · **`Cuboctahedron_geo` PASS** · α_geom=137 (~260 ppm) exploratory; derived π ~2 ppm |
| 2026-09-23 | §8.2·geo | `cuboctahedron_carrier_row` · **`Cuboctahedron` PASS** — ratio inventory (κ derived; V/S, 6/8, 135°, Φ_□ open) |
| 2026-09-23 | §8.2·geo anchor | dimensional chain **`a=l_P` first** — `edge_a_m`, `V/S`, `A_□=a²`; ratios derived (κ=R_in/R_out after lengths) |
| 2026-09-23 | §8.2·Φ_□ probe | `em_plaquette.py` · **`Phi_square_probe` PASS** — hull lattice path; vortex Δφ_NN~1.48; α link макроописание ok; **alpha_match_open** (1/r≠α yet) |
| 2026-09-23 | §8.2·5 ΔB | derived $g$ **без** хода $\Delta B\neq 0$; $p\not\to e^+\pi^0$; confining girth-$d$ = $B$-класс; census sim всё ещё open |
| 2026-09-23 | §4.1.1-HL | Thm **T-HL**: FCC depth-2 `M=(4/3)I` · `Ŵ=1−(2/3)|k|²` · Madelung → NLSE+ν / NS-class; `T_hydro_limit` |
| 2026-09-23 | §4.1.0-T | Thm **T-CR** full proof: `2log cos(k/2)` series → `Ŵ/G=exp(−R k⁴/96+…)`; FCC/hex depth-2 census |
| 2026-09-22 | §0 | genesis narrative → DEVLOG §7; MODEL = postulates only |

---

## §7. Genesis (диалог → M)

**Не SSOT физики.** Как пришли к каркасу — история разработки; физика — **MODEL §0–§8**.

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
---
## §8. Вынесено из MODEL (split hub)

**Не SSOT физики.** При разбиении монолита MODEL → `MODEL.md` + `model/` сюда ушли сессионные/инженерные куски.

### Ночной канон (снимок, был в MODEL)

### Ночной канон M (2026-09-22) — принято

| # | Тезис | § |
|---|--------|---|
| 1 | Изотропное **`g`**, **`ζ=(Σz)·z*`**, phase wrap | §3.4 |
| 2 | Лучи/sweeps → micro-aniso; default isotropic | §3.6 |
| 3 | Smear → Гейзенберг Δφ≥½ + K_P триггер → anti-smear | §3.7 |
| 4 | Слабые волны на каноне носителя; тяжёлый vortex → контрольный расчёт на гекс-срезе **если** тест | §3.8 · §1.6 |
| 5 | **ДА:** голоморфная среда, **`g`** = удержание аналитичности | §3.9 |
| 6 | Полюс **`hV`**, вычет **`2πn`**, заряд | §3.9 |
| 7 | CR-единственность → **единое поле Λ**, запутанность **на том же Δt** | §3.9 |
| 8 | GPU: **`DX, DT, K_P, ALPHA*`** | §10.4 |
| 9 | 4 топокласса seeds | §9.7 |
| 10 | **SU(2) спинор** `z∈ℂ²`, **720°** → identity; **Паули** + **`K_P` отталкивание** | §3.10 |
| 11 | **system_quanta:** **`Δx, Δt`, `N_frame`, `I_max`**; мозг/UI → META §2 | §4.8 · META §2 |
| 12 | **Любая система:** из **`M, τ, R`** → **`N_frame`**, fractal **`m_P/M`** | §4.8 |
| 13 | **Газ:** macro-облако **`hV`**; **`PV=nRT`**; **`v_s ≪ c`**; **VdW `a,b` из `K_P,l_P`** | §5.3 |
| 14 | **Плотность M бинарна:** **`ρ ∈ {0, ρ_P}`**; macro **`1000 kg/m³`** = T-иллюзия binomialное усреднение | §5.0 |
| 15 | **Масса M:** **`Arg(⟨z⟩/z)`**-зигзаг + **`K_P`**; **Higgs = T-пена**, не первопричина | §5.0.1 · §8.3 |
| 16 | **Arg-квант:** **`s₀=ℏ/2`**, **`E₀=E_P/√2`**, **`m_arg=m_P/√2`**, **`v_arg=c₀`** | §5.0.2 |
| 17 | **Дуализм = T-иллюзия:** M — чистая жидкость; «частица» = солитон; Young = CR-схлоп | §4.9 |
| 18 | **Антиматерия = `n→−n`:** зеркало фазового вихря; annihilation = `n++n−→0` → 2γ | §5.0.3 · §9.2 |
| 19 | **`U(1)_vac` + хиральная упаковка:** global phase на `z`; **`defect_axis` fallback = local Bloch**, не `(0,0,1)`; **`P_L/P_R`** + независимый STREAM | §3.11 |
| 20 | **P / C / T legs (T-layer probes):** mirror, `z*`, chirality boost — **не** M `g⁻¹` | §3.11.3 · A14 |
| 21 | **M = leapfrog на ℤ:** **`l_P=t_P=1`** → нет float; **`z⁺=−z⁻+2z+⌊𝒩⌋`**, `(z,z_past)`; **T⁻¹** = algebra, не CPT-approx | §3.12 · A13 |
| 22 | **Projected collision = Z_N[i]:** **`N_ring=512`**, **`N_φ=⌈4π⌉=13`**, **`frac_bits=⌈log₂(512/13)⌉=6`**, **`Δφ_min=½` rad** | §3.12.5–§3.12.6 |
| 23 | **Локальные законы + SO(2):** **`p₀,L₀,F₀`** из **`s₀`**; A3 + discrete ledgers на M; гладкий **`div j`** = **T** | §5.2.1 · §4.3 · §1.6 |
| 24 | **`κ_link = 1/|N|`:** FCC **`1/12`** (канон 3+1); гекс-срез **`1/6`**; **`γ = cr_strength = ν_CA_natural`**; **`E₀ = p₀·c₀ = F₀·l_P`**; **`b ∈ {0,1}`**; **§5.2.3** — Pauli/sync/**`n_E`** без float | §5.2.2–§5.2.3 · §1.6 |
| 25 | **Gate M = `ω^Φ`:** **`exp(i·Θ·σ/2)`** — T-нотация; tick = **`R(Φ)`** / Rot_LUT на **`Z_N[i]`**, не matrix exp | §3.10.3 · §3.12.5 |
| 26 | **Theorem 2.3:** ¬M heat death, ¬shutdown — Lemmas 2.3.1–2.3.8 | §2.3 |

### Seeds · GPU · code slice (бывшие §9.7 · §10 · §11)

### 9.7 Поиск зародышей: **не brute force**, ~**10–20** прогонов

**Raw brute force** отсечён **до старта:** A9 (CR) + A4 (U(1)) → случайные поля = мусор на 1-м тике.

**Три сжатия:** (1) моды Δ₄ / **(k, φ)** · 	_analysis.py · (2) только winding **n ∈ ℤ** · (3) inverse coarse-grain из T (опция).

**4 топокласса на N₄:**

| n | физика | SeedClass | test |
|---|--------|-------------|------|
| 0 | безмассовая garmonika | PLANE_WAVE | T1 |
| +1 | pra-vortex 
_p | VORTEX_P | T2, A11 |
| −1 | antivortex | VORTEX_M | T2 collision · §5.0.3 |
| +2 | двойной узел | VORTEX_N2 | persistence |

**2 параметра на класс:** r = 1…5 ячеек; импульс/φ₀ → **~10–20 runs**. seeds.py · 
alidate_mt.py.

**ε = N₄** (Moore снят). Не наш BB; да — stable macro + **
_геометрия(n,N₄)**.

---

## §10. GPU / численная реализация (симуляционное макроописание · физика closed)

**Физика предохранителей закрыта в MODEL:** §1.7 (тор) · **§0.10** (пол/seed · `R(Φ)` · SI literals) · verify `Carrier_torus_close` · `Gpu_eng_tail_close`.  
Ниже — **только** пути в коде. Не новая физика, не knobs.

### 10.1 Границы: periodic wrap → §1.7

```
x+N ≡ x ,   y+N ≡ y
```

**Код:** `laplacian` — `torch.roll`; bond wrap в linear/local_ca.

### 10.2 Пол + seed → §0.10 / §0.5

`|z|≥z_min=1/64`; IC ~ пол; `gauge_fix=False` на tick encode.

**Код:** `fixed_point.vacuum_amplitude_quantum` · `seeds.make_seed` · `encode_spinor(gauge_fix=False)`.

### 10.3 Шаг → §0.10 / §3.12.5

`R(Φ)=ω^Φ` / float `exp(iφ)` decode; **не** Euler `z+=iφz`.

**Код:** `update.micro_step` · `linear_step_local_ca`. Hygiene: `norm_drift` в verify.

### 10.4 Literals → §0.10 / SI

`DX, DT, K_P, PHASE_SATURATION, …` = `as_code_dict()` paste. Округление ≠ другая физика.

**Код:** `python -c "from mt_ca.si_constants import as_code_dict; print(as_code_dict())"`.

**4 топокласса seeds:** `VACUUM`, `PLANE_WAVE`, `VORTEX_P/M/N2` · `seeds.py`.

---

## §10.5 Thermometer dual-channel (2026-09-24)

**Gap:** A10 макроописание was only `∮ d arg(z₂/z₁)`. Locked equal-lane boil (`z₁≡z₂`, VACUUM_BOIL bricks) → rel≡0 → seeker reported dead universe while contrast grew.

**Fix:** `mt_ca/topology.py` — channels **rel** / **u1**=`Arg(z₁+z₂)` / **auto**=max`|n|`. MODEL §5.0 derived. `MatterOccupancyB` gate includes locked U(1) synth. Brick-scan gate reports `winding_rel_max` / `winding_u1_max`.

**Probe:** SYNTH_U1 locked → rel=0, u1≈1, **b=1** · VORTEX_P → rel≈1, u1≈0, **b=1** · class-gradient boil IC still ~curl-free (no magic b from stripes). Stale bath `emerged_b=False` was this gap — not absence of matter.

**Family scan** (`scripts/run_seed_family_scan.py`, 128²×1024): VACUUM/BOIL/IMPULSE → born=0 · **PLANE_WAVE → born=1** (|n|_auto≈2) · VORTEX_* planted persist. Brick-offset BOIL subfamily still 0/52.

**α·full-quant:** тонкая структура = `α=κ/M` из полного квантования (Thm 5.1 seats); `M=97` **теорема** closed; π-tower coarse as descent; soft −1040 ppm OPEN. `Alpha_full_quantization_bridge`.

**Coulomb M-native:** закон силы на M — `F=n₁n₂ F₀/(M N²)` без continuum-α/π-tower; α=κ/M только макроописание T. `Coulomb_M_native`.

**α·U0·soft face:** preferred ~−0.000068 ppm (~0.45σ). Soft unit from symmetry: $U=(d+1)/d=1/(1−κ^{n_□})=8/7$. **Unit descent closed** — G-grade completeness: grade-0 soft singlet once in M-scale den (soft-minus; not ×M; not in num). `derivation_closed=True`. Global-M book false trail. Upstairs on `alpha_preferred`.

**α·SI-bridge:** carrier α from κ,M,d,U only — **exact** (no u(α), no ppm of α). Unit packet: U0=F0·l_P², ħc=2κ U0. CODATA contrast = optional T-door only. `Alpha_si_bridge` PASS.

**α·upstairs:** cascade closed on preferred α — v→m_H→m_p/m_e→m_n exact laws; PDG=T-door; soft ~10⁻³ floors open higher structure. `Alpha_upstairs_mass_probe` PASS.

---

## §11. Код (M-only slice)

`mt_ca/`: M = `local_ca` + gate. T = `t_analysis.py` + `validate_mt.py`. Протокол: `BUILD.md` · константы: `si_constants.py` · §10 — симуляционное макроописание §0.10/§1.7.


### Layout MODEL после split

`MODEL.md` = оглавление. Физика: `model/00`…`06`. Правило: не возвращать пометки реализации/MVP/даты в MODEL или `model/`.

### Wave: N₄/MVP purge из `model/` (после split)

Квадрат N₄ / Genese Moore / Impl-строки / Sim notes вычищены из `model/*`. Окрестность пишется как **`N` / `|N|`** (FCC 12 · гекс 6). Исторический ромб κ на N₄ — только здесь как архив: κ=1/√2 совпал с FCC 1-tick, но носитель канон — кубооктаэдр, не квадрат.
