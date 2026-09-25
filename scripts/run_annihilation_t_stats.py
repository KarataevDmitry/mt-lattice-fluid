#!/usr/bin/env python3
"""Print §5.0.3 T-statistics probe (dual-front readout)."""

from __future__ import annotations

import json

from mt_ca.annihilation_t_stats import annihilation_t_stats_probe


def main() -> None:
    row = annihilation_t_stats_probe()
    print(json.dumps(row, indent=2, default=str))


if __name__ == "__main__":
    main()
