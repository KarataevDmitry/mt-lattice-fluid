from pathlib import Path
import re

ROOT = Path(r"D:\Experiments\PersonalCursorFolder\open\mt-lattice-fluid")
MODEL = ROOT / "model"

META = re.compile(
    r"^\*\*(?:SSOT-часть MODEL|Не (?:SSOT|сюда)).*\n"
    r"(?:\*\*(?:SSOT|Не|В теле).*?\n)?"
    r"(?:\*\*В теле §3 запрещено:.*\n)?"
    r"---\n",
    re.M,
)

for path in sorted(MODEL.glob("*.md")):
    text = path.read_text(encoding="utf-8")
    new = META.sub("", text, count=1)
    if new != text:
        path.write_text(new, encoding="utf-8")
        print("header stripped:", path.name)

# §3-only fixes
p3 = MODEL / "03-evolution.md"
text = p3.read_text(encoding="utf-8")
text = text.replace(
    "**Legacy float gate** — DEVLOG §4. **Канон forward-tick:** §3.12.",
    "**Канон forward-tick:** §3.12.",
)
text = re.sub(
    r"\n### 3\.5 Legacy stubs[^\n]*\n→ \*\*DEVLOG\*\*[^\n]+\n",
    "\n",
    text,
)
p3.write_text(text, encoding="utf-8")
print("03-evolution patched")
