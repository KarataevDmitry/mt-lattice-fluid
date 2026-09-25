# M → T → SM lattice fluid

**Манифест:** [`MANIFEST.md`](MANIFEST.md) — исходная формулировка «Дискретная информационная термодинамика».
**Meta** (космология, observer UI, access) → **[`META.md`](META.md)** — **не SSOT**; не добавляет knobs в `g`. **Два «времени»:** A5-пена без начала/конца (M) vs генезис **наблюдаемой** — **META §3.0**.
**Devlog** (impl, verify, open leaves) → **[`DEVLOG.md`](DEVLOG.md)** — **не SSOT**; не меняет `g`.
**SM constants** — [`model/06-si-sm.md`](model/06-si-sm.md) (hub §6–§8), часть **MODEL**, не meta.

### Иерархия слоёв (SSOT)

```
физика (известное)  →  M   model/*.md + этот hub   — утверждения: g, аксиомы, ДА, M→T→SM
                           ↓  следует
                      impl mt_ca/            — реализация; **может отставать** от M
                           ↓  проверяет (impl ↔ M)
                      sim  validate_mt, GPU  — не «истина»; ловит sim-gap и T-метрики
                           ↓
                      T    coarse, readout     — наблюдаемый слой
                           ↓  (интерпретация)
                      Meta META.md           — космология, UI, access; **не refute M**
                      Devlog DEVLOG.md       — impl status, verify, open; **не refute M**
```

**Истина идёт из MODEL (hub + `model/`).** Impl и sim **догоняют**.

### Запрещено в MODEL

Даты сессий · snapshot-таблицы · **`Impl:`** · MVP/Genese-повествование · «была здесь» · provenance · sim notes — **только [`DEVLOG.md`](DEVLOG.md)**.
MODEL = физика `g` **сейчас**, не дневник разработки.

### M vs Meta / Devlog

| | **MODEL** | **META** | **DEVLOG** |
|---|-----------|----------|------------|
| Роль | **SSOT физики** | UI / космология **над** M | impl / verify / open |
| Где | этот hub + [`model/`](model/) | `META.md` | `DEVLOG.md` |
| Спор | «что делает `g`?» → только MODEL | «что видит мозг?» → META | «догнали код?» → DEVLOG |

### Три вида gap

| gap | смысл | чей долг | лечение |
|-----|--------|----------|---------|
| **model-gap** | в M **не применили** уже известную физику | **MODEL** | дописать/вывести § |
| **sim-gap** | в MODEL **уже сказано**, impl/sim **не догнали** | **mt_ca** / verify | код, harness |
| **T-metric** | грубый readout / слабая метрика T | **validate_mt**, macro | не «M refuted» |

**Правило:** sim ≠ M → сначала классифицировать gap; **не** ослаблять MODEL под sim.

### Карта физики

| файл | содержание |
|------|------------|
| [`model/00-glossary.md`](model/00-glossary.md) | **глоссарий:** планкон · планковская дырка · планковская ячейка · вакуум |
| [`model/00-foundations.md`](model/00-foundations.md) | §0 основания · **eng-хвост §0.10** |
| [`model/01-carrier.md`](model/01-carrier.md) | §1 носитель: FCC N₁₂ · гекс-срез · κ · **тор §1.7** |
| [`model/02-axioms.md`](model/02-axioms.md) | §2 абсолютные условия A1–A16 |
| [`model/03-evolution.md`](model/03-evolution.md) | §3 `g`, ДА, спинор, leapfrog |
| [`model/04-macro.md`](model/04-macro.md) | §4 M→T |
| [`model/05-matter.md`](model/05-matter.md) | §5 dV, occupancy, гидро |
| [`model/05-floor0-spectrum.md`](model/05-floor0-spectrum.md) | §5.0.4-A внутренний спектр планкона (этаж 0) |
| [`model/06-si-sm.md`](model/06-si-sm.md) | hub §6–§8 (оглавление) |
| [`model/06-ladder.md`](model/06-ladder.md) | §6 иерархия M→SM · **§6.0 лестница до T** |
| [`model/07-si-bridge.md`](model/07-si-bridge.md) | §7 SI-мост |
| [`model/08-alpha.md`](model/08-alpha.md) | §8.1–8.2 α |
| [`model/08-units.md`](model/08-units.md) | §8.2 meter / units |
| [`model/08-masses.md`](model/08-masses.md) | §8.2 массы |
| [`model/08-higgs.md`](model/08-higgs.md) | §8.3 Higgs |
| [`model/08-forces.md`](model/08-forces.md) | §8.4 силы · GR · Weinberg · CKM |

**Носитель (3+1):** FCC **N₁₂**. **Срез (2+1):** гекс **N₆** = {111} FCC. Квадрат N₄ — не физика M (см. DEVLOG).

### Инженерный хвост (не SSOT физики)

Seeds / GPU-контракт / code slice — [`DEVLOG.md`](DEVLOG.md) (§ eng).
