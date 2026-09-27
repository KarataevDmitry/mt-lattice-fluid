#!/usr/bin/env python3
"""One-shot: B_V/dV JSON and API → B_V/dV (volume notation)."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

GLOBS = [
    ROOT / "mt_ca",
    ROOT / "verify_checks",
    ROOT / "tools",
    ROOT / "model",
    ROOT / "GLOSSARY.ru.md",
    ROOT / "BUILD.md",
]

# Longest keys first
PAIRS: list[tuple[str, str]] = [
    ("geometry_dV_over_V_P", "geometry_dV_over_V_P"),
    ("dV_equals_V_P_over_sqrt2", "dV_equals_V_P_over_sqrt2"),
    ("geometry_dV_m3", "geometry_dV_m3"),
    ("V_over_dV_exact", "V_over_dV_exact"),
    ("V_over_dV", "V_over_dV"),
    ("dV_over_V_P", "dV_over_V_P"),
    ("dV_m3", "dV_m3"),
    ("bekenstein_B_V", "bekenstein_B_V"),
    ("B_V_pure", "B_V_pure"),
    ("B_V_fraction", "B_V_fraction"),
    ("B_V_bits", "B_V_bits"),
    ("B_V_bits", "B_V_bits"),
    ("floor_B_V", "floor_B_V"),
    ('"B_V"', '"B_V"'),
    ("'B_V'", "'B_V'"),
    (".B_V", ".B_V"),
    ("B_V:", "B_V:"),
    ("B_V=", "B_V="),
    ("⌊B_V⌋", "⌊B_V⌋"),
    ("B_V ", "B_V "),
    ("B_V,", "B_V,"),
    ("B_V)", "B_V)"),
    ("B_V·", "B_V·"),
    ("B_V/", "B_V/"),
    ("B_V−", "B_V−"),
    ("−B_V", "−B_V"),
    ("{B_V}", "{B_V}"),
    ("dV", "dV"),
    ("PlanckCellBitBudget", "PlanckCellBitBudget"),
    ("planck_cell_bit_budget_row", "planck_cell_bit_budget_row"),
    ("planck_cell_bit_budget", "planck_cell_bit_budget"),
    ("check_planck_cell_bit_budget", "check_planck_cell_bit_budget"),
    ("run_floor0_gamma_V", "run_floor0_gamma_V"),
    ("floor0_gamma_V_row", "floor0_gamma_V_row"),
    ("check_floor0_gamma_V", "check_floor0_gamma_V"),
    ("Floor0_gamma_V", "Floor0_gamma_V"),
    ("Γ_V", "Γ_V"),
]

SKIP = {".cdp", "__pycache__", ".git"}


def iter_files() -> list[Path]:
    out: list[Path] = []
    for base in GLOBS:
        if base.is_file():
            out.append(base)
            continue
        for p in base.rglob("*"):
            if not p.is_file():
                continue
            if p.suffix not in {".py", ".md"}:
                continue
            if any(s in p.parts for s in SKIP):
                continue
            out.append(p)
    return out


def main() -> None:
    for path in iter_files():
        text = path.read_text(encoding="utf-8")
        orig = text
        for a, b in PAIRS:
            text = text.replace(a, b)
        if text != orig:
            path.write_text(text, encoding="utf-8", newline="\n")
            print(path.relative_to(ROOT))


if __name__ == "__main__":
    main()
