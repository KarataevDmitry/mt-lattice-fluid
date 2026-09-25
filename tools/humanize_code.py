#!/usr/bin/env python3
"""Rename agent jargon to human-readable identifiers in mt-lattice-fluid code."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

TARGET_GLOBS = [
    ROOT / "mt_ca",
    ROOT / "verify_checks",
    ROOT / "model",
]
TARGET_FILES = [ROOT / "verify_principles.py"]

# Order matters: longest / most specific first.
TEXT_REPLACEMENTS: list[tuple[str, str]] = [
    # Section refs in strings
    ("§8.2·F·ask", "§8.2·F"),
    ("§8.2·H·ask", "§8.2·H"),
    ("§8.2·geo·ask", "§8.2·geo"),
    ("§8.2·geo·voronoi·ask", "§8.2·geo·voronoi"),
    ("§8.2·α·g2·ask", "§8.2·α·g2"),
    ("§8.2·α·ae·ask", "§8.2·α·ae"),
    ("§6·floor1·ask", "§6·floor1"),
    ("·ask", ""),
    # kick-ledger (census / docs only — not pauli_kick / collision kick)
    ("kick-ledger", "momentum registry"),
    ("kick ledger", "momentum ledger"),
    ("kick_ledger", "momentum_ledger"),
    ("alpha_nF_kick_census", "alpha_nF_momentum_registry"),
    ("Alpha_nF_kick_census", "Alpha_nF_momentum_registry"),
    ("closed_by_nF_kick_census", "closed_by_nF_momentum_registry"),
    # Field / key names
    ("ratio_shipped_count", "ratio_derived_count"),
    ("ladder_shipped_count", "ladder_derived_count"),
    ("alpha_inv_stamped_rel_err", "alpha_inv_derived_rel_err"),
    ("discrete_path_shipped", "discrete_path_derived"),
    ("soft_candidate_shipped", "soft_candidate_derived"),
    ("mechanism_descent_shipped", "mechanism_descent_derived"),
    ("axiom_inv_cut_shipped", "axiom_inv_cut_derived"),
    ("axiom_seat_unit_shipped", "axiom_seat_unit_derived"),
    ("axiom_seat_plus_face_shipped", "axiom_seat_plus_face_derived"),
    ("alpha_fs_stamped", "alpha_fs_derived"),
    ("lab_inside_codata_band", "within_codata_band"),
    ("ask_ok", "checks_ok"),
    # Status tokens
    ("stamped_T", "derived_T"),
    ("demoted_T", "coarse_T"),
    ("demoted_coarse", "coarse_approx"),
    ("rejected_as_M_input", "rejected_as_m_input"),
    ('"shipped"', '"derived"'),
    ('"stamped"', '"derived"'),
    ('"demoted"', '"coarse"'),
    ('"sealed"', '"closed"'),
    ('"SEALED"', '"closed"'),
    ('"CLOSED"', '"closed"'),
    # Prose in docstrings / notes
    ("already stamped", "already derived"),
    ("not stamped", "not derived"),
    ("not knobs", "not free parameters"),
    ("float-knobs", "continuous parameters"),
    ("float-knob", "continuous parameter"),
    ("soft-face", "soft face"),
    ("ask-model", "model"),
    ("Demoted", "Coarse"),
    ("demoted", "coarse"),
    ("stamped", "derived"),
    ("shipped", "derived"),
    ("SEALED", "closed"),
    (" CLOSED", " closed"),
]

IDENT_REPLACEMENTS: list[tuple[str, str]] = [
    ("_ask_row", "_row"),
    ("_ask", ""),
]


def iter_files() -> list[Path]:
    files: list[Path] = list(TARGET_FILES)
    for base in TARGET_GLOBS:
        if base.is_dir():
            files.extend(sorted(base.rglob("*.md")))
            files.extend(sorted(base.rglob("*.py")))
        elif base.suffix == ".md":
            files.append(base)
    return [p for p in files if p.name not in {"humanize_code.py", "clean_jargon.py", "fix_jargon_grammar.py"}]


def humanize(text: str) -> str:
    for old, new in TEXT_REPLACEMENTS:
        text = text.replace(old, new)
    for old, new in IDENT_REPLACEMENTS:
        text = text.replace(old, new)
    # ask g for → derive g for (leftover prose)
    text = text.replace("ask g for", "derive g for")
    text = text.replace("ask_ok", "checks_ok")
    return text


def main() -> None:
    changed: list[str] = []
    for path in iter_files():
        original = path.read_text(encoding="utf-8")
        updated = humanize(original)
        if updated != original:
            path.write_text(updated, encoding="utf-8")
            changed.append(str(path.relative_to(ROOT)))
    print(f"updated {len(changed)} files")
    for name in changed:
        print(f"  {name}")


if __name__ == "__main__":
    main()
