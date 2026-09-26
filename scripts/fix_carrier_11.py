#!/usr/bin/env python3
from pathlib import Path
import re

p = Path(__file__).resolve().parents[1] / "model" / "01-carrier.md"
t = p.read_text(encoding="utf-8")

t, n0 = re.subn(
    r"```\nN\(x\) = N\(x\) = \{ x ± ê_i \}.*?```\n\n\*\*Moore запрещён:\*\*.*?§1\.3\.\n",
    "```\nN(x) = { y : |y−x| = l_P  и  light-like за hT }   — канон: |N|=12 FCC (§1.6)\n```\n\n"
    "**Муур / 2-я оболочка запрещены:** за один `hT` только равные light-like рёбра `l_P` — см. §1.3.\n",
    t,
    count=1,
    flags=re.S,
)
print("continuum", n0)

start = t.find("c  = κ · c₀ = c_CODATA")
end = t.find("\n### 1.2 ")
if start < 0 or end < 0:
    raise SystemExit(f"markers missing start={start} end={end}")

close = t.find("```", start)
if close < 0:
    raise SystemExit("fence missing")
head = t[: close + 3]
tail = t[end:]

mid = """

Один тик `hT` — не дальше **одного** light-like ребра `l_P` на каноне ε (FCC N₁₂ / гекс-срез).

#### `c` — macro T (измеряемая «скорость света в вакууме»)

**CODATA `c`** = **`κ·c₀`** при **`hT = t_P/√2`**. Не «медленнее на 30%» — **учебниковый `t_P` не равен M-тику**.

```
c_T = κ · c₀        (natural; κ — macro κ, не новая константа SI)
```

**Механизм (канон FCC, §1.6.2):** фотон = macro-пакет; 1-tick = кубооктаэдр; **`κ = 1/√2`** — вписанная сфера / изотропный T-фронт. На гекс-срезе — **`κ_hex = √3/2`** (§1.4.2).

```
κ_FCC = 1/√2 ≈ 0.7071     (канон 3+1)
κ_hex = √3/2 ≈ 0.8660     (срез 2+1)
```

| Слой | Скорость (natural) | Геометрия |
|------|---------------------|-----------|
| M, link | `c₀` | ε канона (FCC / гекс) |
| T (isotropic macro κ) | **`κ·c₀`** | вписанная сфера / окружность |
| SI macro | `c = κ·c₀` = CODATA | §7 |

κ **не fitted** — геометрия конуса.
"""

t = head + mid + tail

reps = [
    (
        "Квадрат/`N` и SC/`N₆` — условные учебные носители (§1.3), не канон размерности 3.",
        "Канон размерности 3 — только FCC N₁₂; гекс — срез (§1.4 · §1.6).",
    ),
    ("| квадрат N / SC | sim-gap кода · условный §1.3 |\n", ""),
]
for a, b in reps:
    if a in t:
        t = t.replace(a, b)
        print("fixed", a[:50])
    else:
        print("miss", a[:60])

# leftover romb narrative lines in 1.1 were removed with mid; scrub table row if residual
t = t.replace("| квадрат N / SC | sim-gap кода · условный §1.3 |", "")

p.write_text(t, encoding="utf-8", newline="\n")
print("romb", t.count("ромб"), "κ_FCC", "κ_FCC = 1/√2" in t)
