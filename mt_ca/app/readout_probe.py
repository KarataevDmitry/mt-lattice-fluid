"""Script-facing readout probe — survey vs anchor in one call (§5.0 instrument)."""
from __future__ import annotations

from typing import Any, Literal

import torch

from mt_ca.app.gates import gate_b
from mt_ca.matter_readout import MatterSite, default_anchor

READOUT_SCHEMA = 1


def gates_at_z(
    z: torch.Tensor,
    *,
    with_anchor: bool = True,
    anchor: MatterSite | tuple[int | None, int, int] | Literal["center"] | None = None,
    top_k: int = 8,
    contour_radius: int = 2,
) -> dict[str, float | int | bool]:
    """Single ``gate_b`` call; always fills ``passed_survey`` + optional anchor lane."""
    anchor_site: MatterSite | None
    if not with_anchor:
        anchor_site = None
    elif anchor is None or anchor == "center":
        anchor_site = default_anchor(z)
    elif isinstance(anchor, MatterSite):
        anchor_site = anchor
    else:
        iz, y, x = anchor
        anchor_site = MatterSite(iz, y, x)
    return gate_b(
        z,
        anchor=anchor_site,
        top_k=top_k,
        contour_radius=contour_radius,
    )


def lane_survey(g: dict[str, float | int | bool]) -> dict[str, float | int | bool]:
    return {
        "passed": bool(g["passed_survey"]),
        "b": int(g["b_argmax"]),
        "b_hits": int(g["b_hits_topk"]),
        "w_max": float(g["winding_abs_max"]),
        "w_rel": float(g["winding_rel_max"]),
        "w_u1": float(g["winding_u1_max"]),
        "contrast": float(g["contrast"]),
    }


def lane_anchor(g: dict[str, float | int | bool]) -> dict[str, float | int | bool]:
    return {
        "passed": bool(g["passed_anchor"]),
        "b": int(g["b_anchor"]),
        "w_max": float(g["winding_abs_max"]),
        "contrast": float(g["contrast"]),
    }


def dual_lanes(g: dict[str, float | int | bool]) -> dict[str, Any]:
    return {
        "schema": READOUT_SCHEMA,
        "survey": lane_survey(g),
        "anchor": lane_anchor(g),
    }


def born_survey(g0: dict[str, float | int | bool], g1: dict[str, float | int | bool]) -> bool:
    """Spontaneous birth: survey mode (local ρ maxima + contour)."""
    return bool(g1["passed_survey"] and not g0["passed_survey"])


def born_anchor(g0: dict[str, float | int | bool], g1: dict[str, float | int | bool]) -> bool:
    """Birth at fixed core (planted / tracked site)."""
    return bool(g1["passed_anchor"] and not g0["passed_anchor"])


def planted_persisted(g0: dict[str, float | int | bool], g1: dict[str, float | int | bool]) -> bool:
    return bool(g0["passed_anchor"] and g1["passed_anchor"])


def planted_lost(g0: dict[str, float | int | bool], g1: dict[str, float | int | bool]) -> bool:
    return bool(g0["passed_anchor"] and not g1["passed_anchor"])


def sample_row(g: dict[str, float | int | bool], *, t: int) -> dict[str, Any]:
    return {"t": t, **dual_lanes(g)}
