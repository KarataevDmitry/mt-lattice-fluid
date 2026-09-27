#!/usr/bin/env python3
"""Normalize MODEL notation: capital V = volume, lowercase v = velocity."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Order: longer / more specific first
SUBS: list[tuple[str, str]] = [
    ("$\\Gamma_{hV}$", "$\\Gamma_V$"),
    ("\\Gamma_{hV}", "\\Gamma_V"),
    ("Γ_{hV}", "Γ_V"),
    ("$B_{hV}$", "$B_V$"),
    ("B_{hV}", "B_V"),
    ("`B_hV`", "`B_V`"),
    ("B_hV", "B_V"),
    ("$v_{hV}$", "$dV$"),
    ("v_{hV}", "dV"),
    ("`v_hV`", "`dV`"),
    ("v_hV", "dV"),
    ("`v_p`", "`V_P`"),
    ("$v_p$", "$V_P$"),
    ("∂(hV)", "∂(V_P)"),
    ("$hV$", "$V_P$"),
    ("`hV`", "`V_P`"),
    ("**(hV ", "**($V_P$ "),
    ("#(hV ", "#($V_P$ "),
    ("В чате ту же ячейку писали **hV**; в коде — **planck cell**. ", ""),
    ("В чате «hV». ", ""),
]

HV_RE = re.compile(
    r"(?<![A-Za-z0-9_])hV(?![A-Za-z0-9_])"
)  # bare hV token → V_P in prose fragments
V_P_RE = re.compile(r"\bv_p\b")


def patch_text(text: str) -> str:
    for old, new in SUBS:
        text = text.replace(old, new)
    text = V_P_RE.sub("V_P", text)
    # last: standalone hV (not inside identifiers like Floor0_gamma_hV — already Gamma fixed)
    text = HV_RE.sub("V_P", text)
    return text


def main() -> None:
    paths = list((ROOT / "model").glob("*.md"))
    # GLOSSARY.ru.md — править вручную (ключи JSON вроде v_hV_m3 не трогать автозаменой).
    for path in paths:
        raw = path.read_text(encoding="utf-8")
        new = patch_text(raw)
        if new != raw:
            path.write_text(new, encoding="utf-8", newline="\n")
            print(f"updated {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
