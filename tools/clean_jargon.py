#!/usr/bin/env python3
"""Remove agent-interview jargon from mt-lattice-fluid model/*.md."""
from __future__ import annotations

import re
from pathlib import Path

MODEL = Path(__file__).resolve().parents[1] / "model"


def clean(text: str) -> str:
    # Multi-word / ordered replacements first.
    pairs: list[tuple[str, str]] = [
        # Interview ritual
        ("**Опрос — ответы носителя:**", "**Вывод:**"),
        ("**Ответ носителя (два слоя):**", "**Вывод (два слоя):**"),
        ("**Ответ носителя:**", "**Вывод:**"),
        ("**Итог опроса**", "**Итог**"),
        ("3 · Итог опроса", "3 · Итог"),
        ("1 · Спросили носитель: когда стабилен?", "1 · Стабильность"),
        ("Спросили носитель (§", "Из (§"),
        ("#### 5.2.6 Спросили носитель про **фонон**", "#### 5.2.6 Фонон"),
        ("Спросили носитель про **фонон**", "Фонон"),
        ("Спросили носитель:", ""),
        ("Спросили носитель про", ""),
        ("Вопрос носителю", "**Задача**"),
        ("**Опрос:**", "**Разбор:**"),
        # Ask-model section headers
        ("**5 · Ask-model:", "**5 ·"),
        ("**6 · Ask-model:", "**6 ·"),
        ("**7 · Ask-model:", "**7 ·"),
        ("Ask-model:", ""),
        ("ask-model", "модель"),
        # Section titles with ·ask
        ("#### §8.2·α·g2·ask · bare", "#### §8.2·α·g2 · Bare"),
        ("#### §8.2·α·g2·ask · Спросили носитель: bare", "#### §8.2·α·g2 · Bare"),
        ("#### §8.2·α·ae·ask · Спросили носитель: A5", "#### §8.2·α·ae · A5"),
        ("#### §8.2·H·ask · Спросили носитель:", "#### §8.2·H ·"),
        ("#### §8.2·geo·ask · Спросили носитель:", "#### §8.2·geo ·"),
        ("#### §8.2·α·EM·faces · Спросили носитель:", "#### §8.2·α·EM·faces ·"),
        ("#### §6·floor1·ask ·", "#### §6·floor1 ·"),
        ("#### §6·dressing·ask ·", "#### §6·dressing ·"),
        ("#### §8.2·α·dual · Метод:", "#### §8.2·α·dual ·"),
        # Method → Подход (interview steps)
        ("**Метод:** как §8.2·H·ask —", "**Подход:**"),
        ("**Метод:** как §8.2·geo·ask", "**Подход:** как §8.2·geo"),
        ("**Метод:** как §8.2·H·ask", "**Подход:** как §8.2·H"),
        ("**Метод:** geo·ask", "**Подход:**"),
        ("**Метод:** (1) зафиксировать", "**Подход:** (1) зафиксировать"),
        ("**Метод:** (1) назвать", "**Подход:** (1) назвать"),
        ("**Метод:** (1) **`a=l_P`**", "**Подход:** (1) **`a=l_P`**"),
        ("**Метод:** тот же, что", "**Подход:** тот же, что"),
        ("**Метод:** не «M", "**Подход:** не «M"),
        ("**Метод:**", "**Подход:**"),
        # English agent jargon
        ("not knobs", "не свободные параметры"),
        ("kick-ledger", "реестр импульса"),
        ("kick ledger", "реестр импульса"),
        ("lab-inside", "лабораторное согласование"),
        ("readout **forced**", "readout **вынужден**"),
        ("sim soft", "sim открыто"),
        # stamped (longest phrases first)
        ("Уже stamped (не свободные параметры)", "Уже выведено (не свободные параметры)"),
        ("**Уже stamped (не свободные параметры):**", "**Уже выведено (не свободные параметры):**"),
        ("**Уже stamped (не knobs):**", "**Уже выведено (не свободные параметры):**"),
        ("**Что уже stamped (не угадайка):**", "**Что уже выведено:**"),
        ("**Что уже stamped:**", "**Что уже выведено:**"),
        ("уже stamped", "уже выведено"),
        ("Уже stamped", "Уже выведено"),
        ("не stamped", "не выведено"),
        ("not stamped", "не выведено"),
        ("stamped downhill", "выведенный downhill"),
        ("stamped downhill-*класс*", "выведенный downhill-класс"),
        ("у stamped $g$", "у выведенного $g$"),
        ("stamped $g$", "выведенного $g$"),
        ("stamped инвариантов", "выведенных инвариантов"),
        ("stamped как", "выведено как"),
        ("stamped (§", "выведено (§"),
        ("stamped **", "выведено **"),
        (" — stamped", " — выведено"),
        ("| stamped |", "| выведено |"),
        ("$m_e$ stamped", "$m_e$ выведено"),
        ("where stamped", "где выведено"),
        ("что stamped", "что выведено"),
        ("stamped ", "выведено "),
        ("stamped.", "выведено."),
        ("stamped,", "выведено,"),
        ("stamped;", "выведено;"),
        ("stamped)", "выведено)"),
        ("stamped**", "выведено**"),
        # demoted
        ("demoted coarse", "грубое приближение"),
        ("Demoted:", "Грубое:"),
        ("demoted $\\alpha_0", "грубого $\\alpha_0"),
        ("при demoted", "при грубом"),
        ("При demoted", "При грубом"),
        ("Лемма (force dual, demoted coarse)", "Лемма (force dual, грубое приближение)"),
        ("demoted", "грубое"),
        # SEALED / CLOSED / sealed
        ("κ CLOSED", "κ закрыто"),
        ("M=97** CLOSED", "M=97** закрыто"),
        ("unit descent **SEALED**", "unit descent **закрыто**"),
        ("**SEALED:**", "**Закрыто:**"),
        ("**SEALED", "**Закрыто"),
        (" (SEALED)", " (закрыто)"),
        ("· SEALED", "· закрыто"),
        (" SEALED", " закрыто"),
        ("α sealed", "α закрыто"),
        ("| sealed |", "| закрыто |"),
        (" sealed", " закрыто"),
        ("**CLOSED**", "**закрыто**"),
        (" CLOSED", " закрыто"),
        ("census **CLOSED**", "census **закрыто**"),
        ("hop **CLOSED**", "hop **закрыто**"),
        ("масса **CLOSED**", "масса **закрыто**"),
        ("**IN PROGRESS**", "**в работе**"),
        # soft-face prose (keep anchor ids with soft-face)
        ("soft-face fundamentals", "фундаменталы мягкой грани"),
        ("soft-face preferred", "предпочтительная мягкая грань"),
        ("soft-face поправки", "поправки мягкой грани"),
        ("**α** = soft-face", "**α** = мягкая грань"),
        ("= soft-face", "= мягкая грань"),
        ("| soft-face |", "| мягкая грань |"),
        ("soft-face ", "мягкая грань "),
        # Section cross-refs ·ask in prose
        ("§8.2·H·ask", "§8.2·H"),
        ("§8.2·geo·ask", "§8.2·geo"),
        ("§8.2·α·g2·ask", "§8.2·α·g2"),
        ("§8.2·α·ae·ask", "§8.2·α·ae"),
        ("ae·ask", "§8.2·α·ae"),
        ("geo·ask", "§8.2·geo"),
        ("H·ask", "§8.2·H"),
        ("F-ask", "§8.2·F"),
        ("dressing·ask", "dressing"),
        ("§6·floor1·ask", "§6·floor1"),
        ("§6·dressing·ask", "§6·dressing"),
        ("floor1·ask", "§6·floor1"),
        # Interview tail
        ("(4) reject / report.", "(4) отвергнуть / зафиксировать."),
        ("; (4) reject / report", "; (4) отвергнуть / зафиксировать"),
        ("reject / report", "отвергнуть / зафиксировать"),
        # «Кулон из носителя» → neutral
        ("«Кулон из носителя»", "§8.2·coulomb"),
        ("Кулон из носителя", "кулон на M (§8.2·coulomb)"),
        # Reading carrier as jargon in Schwinger section
        ("дверь Швингера = чтение носителя", "дверь Швингера = чтение с M"),
    ]

    for old, new in pairs:
        text = text.replace(old, new)

    # Remove leftover empty «Спросили носитель» fragments in headers
    text = re.sub(
        r"(#### [^\n]+ · )\s*`\*\*N_a0\*\*`",
        r"#### §8.2·H · **`N_a0`**",
        text,
    )
    text = re.sub(
        r"(#### §8\.2·H · )\s*`\*\*N_a0\*\*`",
        r"#### §8.2·H · **`N_a0`**",
        text,
    )
    text = re.sub(
        r"(#### §8\.2·geo · )\s*`\*\*a\*\*`",
        r"#### §8.2·geo · **`a` → coupling**",
        text,
    )
    text = re.sub(
        r"(#### §8\.2·α·EM·faces · )",
        r"#### §8.2·α·EM·faces · Вес граней / dihedral → α?\n",
        text,
        count=1,
    )

    return text


def main() -> None:
    for path in sorted(MODEL.glob("*.md")):
        original = path.read_text(encoding="utf-8")
        updated = clean(original)
        if updated != original:
            path.write_text(updated, encoding="utf-8")
            print(f"updated {path.name}")


if __name__ == "__main__":
    main()
