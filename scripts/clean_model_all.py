"""Strip DEVLOG/impl pollution from all model/*.md files."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(r"D:\Experiments\PersonalCursorFolder\open\mt-lattice-fluid")
MODEL = ROOT / "model"

FORBID_LINE = re.compile(
    r"^(?:\*\*Код:\*\*|Код:|\*\*Impl:\*\*|#### \d+\.\d+\.\d+ Impl\b|→ \[`DEVLOG\.md`)"
)
VERIFY_TAIL = re.compile(r"\s*·\s*verify\s+(?:`[^`]+`|\*\*`[^`]+`\*\*)(?:\s*·\s*(?:`[^`]+`|\*\*`[^`]+`\*\*))*\.?\s*$")
MT_CA = re.compile(r"`?mt_ca/[^`\s]+`?")
PY_REF = re.compile(r"`[^`]+\.py`")
CHECK = re.compile(r"✅")
IMPL_COL = re.compile(r"\|\s*impl[^|]*\|", re.I)


def clean_line(line: str) -> str | None:
    if FORBID_LINE.match(line.strip()):
        return None
    s = VERIFY_TAIL.sub("", line)
    s = MT_CA.sub("DEVLOG", s)
    s = PY_REF.sub("DEVLOG", s)
    s = CHECK.sub("closed", s)
    s = re.sub(r"\s*·\s*`[^`]*\.py`[^.\n]*", "", s)
    if s.strip() in ("", "**Код:**"):
        return None
    return s.rstrip()


def clean_file(path: Path) -> int:
    lines = path.read_text(encoding="utf-8").splitlines()
    out: list[str] = []
    removed = 0
    for i, line in enumerate(lines):
        if i < 7:
            out.append(line)
            continue
        new = clean_line(line)
        if new is None:
            removed += 1
            continue
        if new != line:
            removed += 1
        out.append(new)
    # drop duplicate blank runs >2
    text = "\n".join(out) + "\n"
    text = re.sub(r"\n{4,}", "\n\n\n", text)
    path.write_text(text, encoding="utf-8")
    return removed


total = 0
for p in sorted(MODEL.glob("*.md")):
    n = clean_file(p)
    print(f"{p.name}: {n} edits")
    total += n
print("total edits", total)
