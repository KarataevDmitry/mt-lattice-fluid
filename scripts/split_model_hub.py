#!/usr/bin/env python3
"""Split MODEL.md into hub + model/*.md; move impl/GPU/seeds to DEVLOG."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / "MODEL.md"
DEVLOG = ROOT / "DEVLOG.md"
OUT = ROOT / "model"


def slice_lines(lines: list[str], start: int, end: int | None = None) -> str:
    """1-based inclusive start; end exclusive (1-based) or None = EOF."""
    a = start - 1
    b = None if end is None else end - 1
    return "".join(lines[a:b])


def topic_header(title: str, rel: str) -> str:
    return (
        f"# {title}\n\n"
        f"**SSOT-часть MODEL.** Hub: [`MODEL.md`](../MODEL.md) · соседи: [`model/`](.)\n\n"
        f"**Не сюда:** impl / verify / даты / MVP / provenance → [`DEVLOG.md`](../DEVLOG.md).\n\n"
        f"---\n\n"
    )


def main() -> None:
    lines = MODEL.read_text(encoding="utf-8").splitlines(True)
    n = len(lines)
    print(f"read MODEL.md lines={n}")

    # Boundaries from scan (1-based headers)
    # preamble 1..80; night-canon inside preamble; §0@81 §1@121 §2@517 §3@719
    # §4@1305 §5@1588 §6@2332 §7@2347 §8@2412 ###9.7@2946 §10@2970 §11@3042
    s0, s1, s2, s3 = 81, 121, 517, 719
    s4, s5, s6, s7, s8 = 1305, 1588, 2332, 2347, 2412
    s97, s10, s11 = 2946, 2970, 3042

    preamble = slice_lines(lines, 1, s0)
    night_marker = "### Ночной канон M"
    night_body = ""
    if night_marker in preamble:
        pre_head, _, rest = preamble.partition(night_marker)
        # drop night table until next --- after it, keep rest of preamble after table
        if "\n---\n" in rest:
            night_raw, _, after = rest.partition("\n---\n")
            night_body = night_marker + night_raw
            preamble = pre_head.rstrip() + "\n\n---\n\n" + after.lstrip()
        else:
            night_body = night_marker + rest
            preamble = pre_head.rstrip() + "\n\n"

    parts = {
        "00-foundations.md": (
            "§0 · Основания M",
            slice_lines(lines, s0, s1),
        ),
        "01-carrier.md": (
            "§1 · Носитель (Planck lattice · FCC)",
            slice_lines(lines, s1, s2),
        ),
        "02-axioms.md": (
            "§2 · Абсолютные условия",
            slice_lines(lines, s2, s3),
        ),
        "03-evolution.md": (
            "§3 · Функция перехода g",
            slice_lines(lines, s3, s4),
        ),
        "04-macro.md": (
            "§4 · M → T (macro)",
            slice_lines(lines, s4, s5),
        ),
        "05-matter.md": (
            "§5 · Элементарный объём dV и matter",
            slice_lines(lines, s5, s6),
        ),
        "06-si-sm.md": (
            "§6–§8 · Лестница · SI · SM",
            slice_lines(lines, s6, s97),
        ),
    }

    impl_tail = slice_lines(lines, s97, None)  # 9.7 + §10 + §11

    OUT.mkdir(exist_ok=True)
    for name, (title, body) in parts.items():
        path = OUT / name
        # strip leading H2 duplicate if topic_header already titles
        text = topic_header(title, name) + body.lstrip("\n")
        path.write_text(text, encoding="utf-8", newline="\n")
        print(f"wrote {path.relative_to(ROOT)} chars={len(text)}")

    hub = """# M → T → SM lattice fluid

**Манифест:** [`MANIFEST.md`](MANIFEST.md) — исходная формулировка «Дискретная информационная термодинамика».  
**Meta** (космология, observer UI, access) → **[`META.md`](META.md)** — **не SSOT**; не добавляет knobs в `g`.  
**Devlog** (impl, verify, open leaves) → **[`DEVLOG.md`](DEVLOG.md)** — **не SSOT**; не меняет `g`.  
**SM constants** — [`model/06-si-sm.md`](model/06-si-sm.md), часть **MODEL**, не meta.

### Иерархия слоёв (SSOT)

```
физика (известное)  →  M   model/*.md + этот hub   — канон: g, аксиомы, ДА, M→T→SM
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

Даты сессий · «ночной канон»-таблицы · **`Impl:`** · MVP/Genese-повествование · «была здесь» · provenance · sim notes — **только [`DEVLOG.md`](DEVLOG.md)**.  
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
| [`model/00-foundations.md`](model/00-foundations.md) | §0 основания |
| [`model/01-carrier.md`](model/01-carrier.md) | §1 носитель: FCC N₁₂ · гекс-срез · κ |
| [`model/02-axioms.md`](model/02-axioms.md) | §2 абсолютные условия A1–A16 |
| [`model/03-evolution.md`](model/03-evolution.md) | §3 `g`, ДА, спинор, leapfrog |
| [`model/04-macro.md`](model/04-macro.md) | §4 M→T |
| [`model/05-matter.md`](model/05-matter.md) | §5 dV, occupancy, гидро |
| [`model/06-si-sm.md`](model/06-si-sm.md) | §6–§8 лестница · SI · SM |

**Канон носителя (3+1):** FCC **N₁₂**. **Срез (2+1):** гекс **N₆** = {111} FCC. Квадрат N₄ — не физика M (см. DEVLOG).

### Инженерный хвост (не SSOT физики)

Seeds / GPU-контракт / code slice — [`DEVLOG.md`](DEVLOG.md) (§ eng / night canon).
"""
    MODEL.write_text(hub, encoding="utf-8", newline="\n")
    print(f"wrote MODEL.md hub chars={len(hub)}")

    # Append to DEVLOG
    dev = DEVLOG.read_text(encoding="utf-8")
    marker = "\n## §8. Вынесено из MODEL (split hub)\n"
    if marker.strip() in dev:
        print("DEVLOG already has §8 split marker — skip append")
    else:
        block = []
        block.append("\n---\n")
        block.append("## §8. Вынесено из MODEL (split hub)\n\n")
        block.append(
            "**Не SSOT.** При разбиении монолита MODEL → hub + `model/` сюда ушли "
            "сессионные/инженерные куски.\n\n"
        )
        if night_body.strip():
            block.append("### Ночной канон (снимок, был в MODEL)\n\n")
            block.append(night_body.strip() + "\n\n")
        block.append("### Seeds · GPU · code slice (бывшие §9.7 · §10 · §11)\n\n")
        block.append(impl_tail.lstrip("\n"))
        block.append(
            "\n\n### Layout MODEL после split\n\n"
            "`MODEL.md` = hub. Физика: `model/00`…`06`. "
            "Правило: не возвращать Impl/MVP/даты в hub или `model/`.\n"
        )
        DEVLOG.write_text(dev.rstrip() + "".join(block), encoding="utf-8", newline="\n")
        print(f"appended DEVLOG §8 (+{sum(len(x) for x in block)} chars)")

    print("OK")


if __name__ == "__main__":
    main()
