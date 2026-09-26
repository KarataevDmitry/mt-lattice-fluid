#!/usr/bin/env python3
"""Strip DEVLOG/editorial voice from model/*.md — physics paper vocabulary only."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MODEL = ROOT / "model"

DELETE_LINE = [
    re.compile(p, re.I)
    for p in (
        r"DEVLOG",
        r"\*\*Python \(SSOT\):\*\*",
        r"\*\*Рантайм gate:\*\*",
        r"DoD leaf",
        r"sim leaf",
        r"Census DoD",
        r"\*\*DoD ",
        r"Exploratory \(anti-pattern\)",
        r"\*\*Fix:\*\*",
    )
]

SUBS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\*\*Claim:\*\*"), "**Утверждение:**"),
    (re.compile(r"\*\*Итог опроса:\*\*"), "**Следствие:**"),
    (re.compile(r"\*\*Итог:\*\*"), "**Следствие:**"),
    (re.compile(r"\*\*Не путать:\*\*\s*"), ""),
    (re.compile(r"\(история кода → DEVLOG\)"), ""),
    (re.compile(r"\s*\(§3\.6 legacy stream\)"), ""),
    (re.compile(r"§9\.7 leaf:"), "§9.7:"),
    (re.compile(r"отдельный численный leaf"), "асимптотический предел"),
    (re.compile(r"open leaf vs"), "асимптотика vs"),
    (re.compile(r"open sim"), "открытый вывод"),
    (re.compile(r"open leaf"), "открытый вывод"),
    (re.compile(r" — open DoD на T"), " — требуют T-layer"),
    (re.compile(r"\bdogfood\b", re.I), "срез"),
    (re.compile(r"\| sim:"), "|"),
    (re.compile(r"⚠️\s*"), ""),
    (re.compile(r"\*\*open DoD\*\*"), "открыто"),
    (re.compile(r"· ⚠️ sim"), ""),
    (re.compile(r"\(§3\.6 legacy stream\)"), ""),
]


def clean_line(line: str) -> str | None:
    if any(rx.search(line) for rx in DELETE_LINE):
        return None
    for rx, repl in SUBS:
        line = rx.sub(repl, line)
    return line.rstrip()


def clean_text(text: str) -> str:
    out: list[str] = []
    for line in text.splitlines():
        cleaned = clean_line(line)
        if cleaned is not None:
            out.append(cleaned)
    body = "\n".join(out)
    while "\n\n\n" in body:
        body = body.replace("\n\n\n", "\n\n")
    return body + "\n"


def main() -> None:
    for path in sorted(MODEL.glob("*.md")):
        original = path.read_text(encoding="utf-8")
        updated = clean_text(original)
        if updated != original:
            path.write_text(updated, encoding="utf-8")
            print(f"updated {path.name}")


if __name__ == "__main__":
    main()
