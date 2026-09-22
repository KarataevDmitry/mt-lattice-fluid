#!/usr/bin/env python3
"""Purge N₄/MVP/Impl/history language from model/*.md → physics SSOT only."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODEL_DIR = ROOT / "model"
DEVLOG = ROOT / "DEVLOG.md"


def strip_impl_sim_lines(text: str) -> str:
    out = []
    for line in text.splitlines(True):
        s = line.lstrip()
        if s.startswith("**Impl:**") or s.startswith("**Sim note:**"):
            continue
        if s.startswith("Impl:"):
            continue
        out.append(line)
    return "".join(out)


def bulk_neigh(text: str) -> str:
    """Neighborhood notation: N₄ → N (canon ε)."""
    reps = [
        (r"Δφ_N₄", "Δφ_N"),
        (r"Δφ_N4", "Δφ_N"),
        (r"⟨z⟩_\{N₄\}", "⟨z⟩_N"),
        (r"⟨z⟩_\{N4\}", "⟨z⟩_N"),
        (r"⟨z⟩_N₄", "⟨z⟩_N"),
        (r"⟨z⟩_N4", "⟨z⟩_N"),
        (r"⟨z⟩_\{N₄\}", "⟨z⟩_N"),
        (r"N₄\(x\)", "N(x)"),
        (r"N4\(x\)", "N(x)"),
        (r"\|N₄\|", "|N|"),
        (r"\|N4\|", "|N|"),
        (r"Σ_\{N₄\}", "Σ_N"),
        (r"Σ_\{y∈N₄\(x\)\}", "Σ_{y∈N(x)}"),
        (r"Σ_\{y∈N4\(x\)\}", "Σ_{y∈N(x)}"),
        (r"на \*\*N₄\*\*", "на **ε**"),
        (r"на N₄", "на ε"),
        (r"на \*\*`N₄`\*\*", "на **`N`**"),
        (r"`N₄`", "`N`"),
        (r"N₄", "N"),
        # leave ASCII N4 only in path-like? replace remaining N4 as neigh
        (r"(?<!\w)N4(?!\w)", "N"),
    ]
    for a, b in reps:
        text = re.sub(a, b, text)
    return text


def purge_mvp_phrases(text: str) -> str:
    text = re.sub(r"\s*\(`/\|N\|=4` MVP; гекс `6`; FCC `12`[^.]*\.\)",
                  " (`|N|=12` FCC · `6` гекс-срез — §1.4 · §1.6.)",
                  text)
    text = re.sub(r"\(`/¼` MVP · `⅙` hex · `1/12` FCC\)",
                  "(`1/12` FCC · `1/6` гекс)",
                  text)
    text = re.sub(r"\|N\|=4` MVP; гекс `6`; FCC `12`",
                  "|N|=12` FCC; гекс `6`",
                  text)
    text = text.replace("|N|=4` MVP; гекс `6`; FCC `12` — §1.4 · §1.6.",
                        "|N|=12` FCC · `6` гекс — §1.4 · §1.6.")
    text = re.sub(r"\(`\|N\|=4` MVP; гекс `6`; FCC `12` — §1\.4 · §1\.6\.\)",
                  "(`|N|=12` FCC · `6` гекс — §1.4 · §1.6.)",
                  text)
    # generic MVP tags
    text = re.sub(r"\s*/\s*MVP код[аы]?", "", text)
    text = re.sub(r"\(MVP\)", "", text)
    text = re.sub(r"MVP\s*/\s*история", "не канон",
                  text)
    text = re.sub(r"история\s*/\s*MVP код[аы]?", "не канон M",
                  text)
    text = re.sub(r"код MVP", "код (sim-gap)", text)
    text = re.sub(r"\bMVP\b", "sim-gap", text)
    text = re.sub(r"кандидат канона", "канон среза",
                  text)
    text = re.sub(r"\(кандидат\)", "(срез 2+1)", text)
    return text


def rewrite_carrier(text: str) -> str:
    """Structural surgery for 01-carrier.md."""
    # Fix continuum N block
    text = text.replace(
        """```
N(x) = N₄(x) = { x ± ê_i }     (2D: 4 соседа)
```

**Moore запрещён:** диагональ за один `hT` потребовала бы `$\\|\\Delta x\\|=\\sqrt{2}\\,l_P$` ⇒ `$\\sqrt{2}\\,c₀$` — см. §1.3.""",
        """```
N(x) = { y : |y−x| = l_P  и  light-like за hT }   — канон: |N|=12 FCC (§1.6)
```

**Муур / 2-я оболочка запрещены:** за один `hT` только равные light-like рёбра `l_P` — см. §1.3.""",
    )
    # More portable without over-escaped
    text = re.sub(
        r"```\nN\(x\) = N₄\(x\) = \{ x ± ê_i \}[^`]*```\n\n\*\*Moore запрещён:\*\*[^*]+\*\*§1\.3\.\*\*",
        "```\nN(x) = { y : |y−x| = l_P  и  light-like за hT }   — канон: |N|=12 FCC (§1.6)\n```\n\n"
        "**Муур / 2-я оболочка запрещены:** за один `hT` только равные light-like рёбра `l_P` — см. §1.3.",
        text,
        count=1,
        flags=re.S,
    )

    # §1.1 κ block — replace N4 romb narrative with FCC
    old_11 = re.search(
        r"Один тик `hT` — не дальше \*\*одной осевой\*\* клетки `l_P`\..*?\*\*Sim note:\*\*.*?\n\n(?=### 1\.2)",
        text,
        flags=re.S,
    )
    if old_11:
        repl = (
            "Один тик `hT` — не дальше **одного** light-like ребра `l_P` на каноне ε (FCC N₁₂ / гекс-срез).\n\n"
            "#### `c` — macro T (измеряемая «скорость света в вакууме»)\n\n"
            "**CODATA `c`** = **`κ·c₀`** при **`hT = t_P/√2`**. Не «медленнее на 30%» — "
            "**учебниковый `t_P` не равен M-тику**.\n\n"
            "```\n"
            "c_T = κ · c₀        (natural; κ — readout, не новая константа SI)\n"
            "```\n\n"
            "**Механизм (канон FCC, §1.6.2):** фотон = macro-пакет; 1-tick = кубооктаэдр; "
            "**`κ = 1/√2`** — вписанная сфера / изотропный T-фронт. На гекс-срезе — "
            "**`κ_hex = √3/2`** (§1.4.2).\n\n"
            "```\n"
            "κ_FCC = 1/√2 ≈ 0.7071     (канон 3+1)\n"
            "κ_hex = √3/2 ≈ 0.8660     (срез 2+1)\n"
            "```\n\n"
            "| Слой | Скорость (natural) | Геометрия |\n"
            "|------|---------------------|-----------|\n"
            "| M, link | `c₀` | ε канона (FCC / гекс) |\n"
            "| T (isotropic readout) | **`κ·c₀`** | вписанная сфера / окружность |\n"
            "| SI macro | `c = κ·c₀` = CODATA | §7 |\n\n"
            "κ **не fitted** — геометрия конуса.\n\n"
        )
        text = text[: old_11.start()] + repl + text[old_11.end() :]

    # §1.3 — drop square Genese + SC educational; keep general + FCC pointer
    old_13 = re.search(
        r"### 1\.3 .*?(?=### 1\.4 Форма)",
        text,
        flags=re.S,
    )
    if old_13:
        repl = (
            "### 1.3 Окрестность ε — световой конус\n\n"
            "**Общее правило A1 (любая решётка):**\n\n"
            "```\n"
            "N(x) = { y : |y−x| = l_P  и  Δs² = c₀² hT² − |y−x|² ≥ 0 }\n"
            "```\n\n"
            "За один `hT` в ε входят **только равные light-like** рёбра длины **`l_P`**. "
            "Любая более длинная связь за тот же тик — **space-like**, запрещена.\n\n"
            "Схема `g` одна (§1.6.5): меняется только `|N|` от упаковки.\n\n"
            "**Канон (3+1):** FCC **N₁₂** (§1.6). **Срез (2+1):** гекс **N₆** (§1.4). "
            "Квадрат / SC / D2Q9 — **не M** (история кода → DEVLOG).\n\n"
            "Тип ε → **`f_геометрия(n, ε)`** (§8.2).\n\n"
        )
        text = text[: old_13.start()] + repl + text[old_13.end() :]

    # Fix broken fence in 1.4.2 if present
    text = text.replace(
        "плоская грань (in): R_eucl = R · l_P · √3/2   →  κ = √3/2\n"
        "**Macro-изотропный свет**",
        "плоская грань (in): R_eucl = R · l_P · √3/2   →  κ = √3/2\n"
        "```\n\n"
        "**Macro-изотропный свет**",
    )

    # Drop Impl line leftovers / hard-code N4 coda
    text = re.sub(
        r"\*\*Код:\*\* `stencil` / `\|N\|`[^.]*онтология\.\n",
        "**Код:** `stencil` / `|N|` — параметр геометрии носителя; тело `projected_collision` / gate — одно.\n",
        text,
    )
    text = re.sub(
        r"Квадрат/`N` и SC/`N₆` — условные учебные носители \(§1\.3\), не канон размерности 3\.\n",
        "Канон размерности 3 — только FCC N₁₂; гекс — срез (§1.4 · §1.6).\n",
        text,
    )
    text = re.sub(
        r"\| квадрат N / SC \| sim-gap кода · условный §1\.3 \|\n",
        "",
        text,
    )
    text = re.sub(
        r"\| код `dV=l_P³`, stencil N \| \*\*sim-gap\*\* к `v_hV=l_P³/√2`, N₁₂ \|\n",
        "| код `dV` / stencil | **sim-gap** к `v_hV=l_P³/√2`, N₁₂ |\n",
        text,
    )
    text = re.sub(
        r"- Что код \(sim-gap\) уже считает зоны Бриллюэна M — \*\*model → sim\*\* open\.\n",
        "",
        text,
    )
    return text


def purge_file(path: Path) -> tuple[str, int]:
    raw = path.read_text(encoding="utf-8")
    before = raw
    text = strip_impl_sim_lines(raw)
    if path.name == "01-carrier.md":
        text = rewrite_carrier(text)
    text = bulk_neigh(text)
    text = purge_mvp_phrases(text)
    # second pass Impl after bulk
    text = strip_impl_sim_lines(text)
    # clean double blanks
    text = re.sub(r"\n{3,}", "\n\n", text)
    changed = 0 if text == before else 1
    if changed:
        path.write_text(text, encoding="utf-8", newline="\n")
    return path.name, changed


def append_devlog_note() -> None:
    note = (
        "\n\n### Wave: N₄/MVP purge из `model/` (после split)\n\n"
        "Квадрат N₄ / Genese Moore / Impl-строки / Sim notes вычищены из `model/*`. "
        "Окрестность пишется как **`N` / `|N|`** (FCC 12 · гекс 6). "
        "Исторический ромб κ на N₄ — только здесь как архив: κ=1/√2 совпал с FCC 1-tick, "
        "но носитель канона — кубооктаэдр, не квадрат.\n"
    )
    d = DEVLOG.read_text(encoding="utf-8")
    if "N₄/MVP purge" in d:
        return
    DEVLOG.write_text(d.rstrip() + note, encoding="utf-8", newline="\n")


def main() -> None:
    for p in sorted(MODEL_DIR.glob("*.md")):
        name, ch = purge_file(p)
        print(f"{name}: {'updated' if ch else 'clean'}")
    append_devlog_note()
    # recount
    for p in sorted(MODEL_DIR.glob("*.md")):
        t = p.read_text(encoding="utf-8")
        n4 = t.count("N₄") + len(re.findall(r"(?<!\w)N4(?!\w)", t))
        mvp = t.count("MVP")
        impl = t.count("**Impl:**") + t.count("Impl:")
        print(f"  check {p.name}: N4={n4} MVP={mvp} Impl={impl}")


if __name__ == "__main__":
    main()
