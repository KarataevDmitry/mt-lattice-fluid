"""Rewrite tracked text files to LF (matches .gitattributes). Idempotent."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_SUFFIXES = frozenset({".md", ".py", ".tex", ".json", ".yml", ".yaml", ".toml", ".sh"})


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def tracked_text_paths(root: Path) -> list[str]:
    proc = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=root,
        capture_output=True,
        check=True,
    )
    out: list[str] = []
    for rel in proc.stdout.decode("utf-8", errors="replace").split("\0"):
        if not rel or Path(rel).suffix.lower() not in _SUFFIXES:
            continue
        out.append(rel)
    return out


def to_lf(data: bytes) -> bytes:
    text = data.decode("utf-8")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    return text.encode("utf-8")


def main() -> int:
    root = repo_root()
    changed = 0
    for rel in tracked_text_paths(root):
        path = root / rel
        if not path.is_file():
            continue
        raw = path.read_bytes()
        if b"\r" not in raw:
            continue
        new = to_lf(raw)
        if new != raw:
            path.write_bytes(new)
            changed += 1
            print(rel)
    print(f"normalize_text_eol: {changed} file(s) updated", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
