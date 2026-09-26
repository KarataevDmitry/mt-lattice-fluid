"""Numeric anchors for ISM blanket — SSOT: data/ism_constraints_v0.yaml."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

_REPO_DATA = Path(__file__).resolve().parents[2] / "data"
DEFAULT_YAML = _REPO_DATA / "ism_constraints_v0.yaml"
DEFAULT_JSON = _REPO_DATA / "ism_constraints_v0.json"


def load_ism_constraints(path: Path | str | None = None) -> dict[str, Any]:
    if path is not None:
        p = Path(path)
        if p.suffix.lower() in {".yaml", ".yml"}:
            with p.open(encoding="utf-8") as f:
                data = yaml.safe_load(f)
        else:
            with p.open(encoding="utf-8") as f:
                data = json.load(f)
    elif DEFAULT_YAML.is_file():
        with DEFAULT_YAML.open(encoding="utf-8") as f:
            data = yaml.safe_load(f)
    elif DEFAULT_JSON.is_file():
        with DEFAULT_JSON.open(encoding="utf-8") as f:
            data = json.load(f)
    else:
        raise FileNotFoundError("missing data/ism_constraints_v0.yaml or .json")
    if not isinstance(data, dict):
        raise ValueError("invalid ISM constraints file")
    return data
