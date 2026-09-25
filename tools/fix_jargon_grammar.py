#!/usr/bin/env python3
"""Fix grammar artifacts and remaining jargon after clean_jargon.py."""
from __future__ import annotations

from pathlib import Path

MODEL = Path(__file__).resolve().parents[1] / "model"
BOOK = Path(__file__).resolve().parents[1] / "book" / "sources" / "chapters"

FIXES: list[tuple[str, str]] = [
    # Grammar from stamped → выведено
    ("Аннигиляция (§5.0.3) **уже** выведено", "Аннигиляция (§5.0.3) **уже выведена**"),
    ("слабый класс выведено", "слабый класс **выведен**"),
    ("выведено класс", "**выведен** класс"),
    ("выведено **стабилен**", "**стабилен** (выведено)"),
    ("выведено **топо-защита**", "**топо-защита** (выведено)"),
    ("| выведено схема", "| **выведена** схема"),
    ("| выведено рамка", "| **выведена** рамка"),
    ("| выведено модель", "| **выведена** модель"),
    ("нет выведено хода", "нет **выведенного** хода"),
    ("$Q$, и выведено $B", "$Q$, и **выведенные** $B"),
    ("(+ $L$, если выведено)", "(+ $L$, если $L$ в схеме)"),
    ("Класс хода — да, выведено.", "Класс хода **выведен**."),
    ("**Вывод:** выведенного $g$ **не содержит**", "**Вывод:** в выведенном $g$ **нет**"),
    ("без выведено $\\zeta", "без **выведенного** $\\zeta"),
    ("****Задача**", "**Задача**"),
    # Status caps
    ("**CLOSED", "**Закрыто"),
    ("CLOSED:", "Закрыто:"),
    ("| **CLOSED** |", "| **закрыто** |"),
    ("**SOFT (reopen):**", "**Мягко (переоткрыто):**"),
    ("**REJECT:**", "**Отвергнуто:**"),
    ("→ **reject**", "→ **отвергнуто**"),
    # Dev jargon
    ("eng readout", "симуляционное чтение"),
    ("float-knobs", "непрерывные параметры"),
    ("float-knob", "непрерывный параметр"),
    ("mechanical непрерывные параметры", "механических непрерывных параметров"),
    ("mechanical float-knobs", "механических непрерывных параметров"),
    ("не knobs", "не свободные параметры"),
    ("(уже ):", "(уже выведено):"),
    ("**shipped**", "**выведено**"),
    ("soft preferred лабораторное согласование", "предпочтительная мягкая грань; лабораторное согласование"),
    ("Структурная α закрыта (soft-face)", "Структурная α закрыта (мягкая грань)"),
    ("α закрыто (soft-face,", "α закрыто (мягкая грань,"),
    ("#### §8.2·α·U0·мягкая грань", "#### §8.2·α·U0·soft-face"),
    ("·  bare", " · bare"),
    ("·  A5", " · A5"),
    ("·  **`", " · **`"),
    (
        "#### §8.2·α·EM·faces · Вес граней / dihedral → α?\n вес граней / dihedral → α?",
        "#### §8.2·α·EM·faces · Вес граней / dihedral → α?",
    ),
    ("Спросить у **светового конуса**", "Вывести из **светового конуса**"),
    ("### 0.10 Eng-хвост", "### 0.10 Инженерный хвост"),
    ("(eng paste)", "(инженерная вставка)"),
    ("**Код (ask):**", "**Код:**"),
]

BOOK_FIXES: list[tuple[str, str]] = [
    ("kick-ledger", "реестр импульса"),
    ("Места kick-ledger", "Места реестра импульса"),
    ("sealed soft-face", "закрытой формулы мягкой грани"),
    ("Soft-face:", "Мягкая грань:"),
    ("soft-face", "мягкая грань"),
    ("\\textbf{sealed}", "\\textbf{закрыто}"),
    ("после seal $\\alpha", "после закрытия $\\alpha"),
    ("уже sealed", "уже закрыто"),
    ("число уже sealed", "число уже закрыто"),
]


def apply(path: Path, pairs: list[tuple[str, str]]) -> bool:
    text = path.read_text(encoding="utf-8")
    updated = text
    for old, new in pairs:
        updated = updated.replace(old, new)
    if updated != text:
        path.write_text(updated, encoding="utf-8")
        return True
    return False


def main() -> None:
    for path in sorted(MODEL.glob("*.md")):
        if apply(path, FIXES):
            print(f"fixed model/{path.name}")
    if BOOK.exists():
        for path in sorted(BOOK.glob("*.tex")):
            if apply(path, BOOK_FIXES):
                print(f"fixed book/{path.name}")


if __name__ == "__main__":
    main()
