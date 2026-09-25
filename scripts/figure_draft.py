"""GOST-style dimensioning for book figures (cf. extension / dimension / leader lines).

Contour (object): thick solid.
Dimensioning: thin solid; extension lines with gap from contour and slight overhang past
the dimension line; arrowheads on dimension lines; labels on or above the dimension line.
"""

from __future__ import annotations

import math

INK = "#000000"
MUTED = "#444444"
LIGHT = "#888888"

# Line weights (pt): object vs dimensioning per drafting convention.
LW_OBJECT = 1.75
LW_DIM = 0.55

# Gaps in data coordinates (tune per figure scale ~ O(1)).
GAP_FROM_OBJECT = 0.025
EXT_OVERHANG = 0.035

_ARROW = dict(arrowstyle="-|>", mutation_scale=7, lw=LW_DIM, shrinkA=0, shrinkB=0)
_ARROW_DASH = {**_ARROW, "linestyle": "--"}


def _label_bbox() -> dict:
    return dict(boxstyle="square,pad=0.15", facecolor="white", edgecolor="none", alpha=0.92)


def centerline(ax, p0: tuple[float, float], p1: tuple[float, float], *, color: str = LIGHT) -> None:
    """Axis / center line (dash-dot)."""
    ax.plot(
        [p0[0], p1[0]],
        [p0[1], p1[1]],
        color=color,
        lw=LW_DIM,
        ls=(0, (3.5, 1.2, 0.8, 1.2)),
        zorder=1,
    )


def dim_radius(
    ax,
    r: float,
    angle_deg: float,
    label: str,
    *,
    color: str = INK,
    ls: str = "-",
    tick: float = 0.035,
    label_gap: float = 0.12,
    ox: float = 0.0,
    oy: float = 0.0,
) -> None:
    """Radial dimension: thin leader from center to arc + witness tick + label outside."""
    th = math.radians(angle_deg)
    ux, uy = math.cos(th), math.sin(th)
    px, py = ox + r * ux, oy + r * uy
    gap = GAP_FROM_OBJECT
    ax.plot(
        [ox + gap * ux, px],
        [oy + gap * uy, py],
        color=color,
        lw=LW_DIM,
        ls=ls,
        zorder=5,
        solid_capstyle="butt",
    )
    nx, ny = -uy, ux
    ax.plot(
        [px - tick * nx, px + tick * nx],
        [py - tick * ny, py + tick * ny],
        color=color,
        lw=LW_DIM,
        zorder=6,
        solid_capstyle="round",
    )
    ap = _ARROW_DASH if ls == "--" else _ARROW
    ax.annotate("", xy=(px, py), xytext=(ox + gap * ux, oy + gap * uy), arrowprops=dict(**ap, color=color))
    lx, ly = ox + (r + label_gap) * ux, oy + (r + label_gap) * uy
    ha = "left" if ux > 0.15 else ("right" if ux < -0.15 else "center")
    va = "bottom" if uy > 0.15 else ("top" if uy < -0.15 else "center")
    ax.text(lx, ly, label, fontsize=9, color=color, ha=ha, va=va, zorder=7, bbox=_label_bbox())


def dim_linear(
    ax,
    p0: tuple[float, float],
    p1: tuple[float, float],
    label: str,
    *,
    offset: float = 0.16,
    color: str = INK,
    ls: str = "-",
    side: float = 1.0,
    text_side: float | None = None,
) -> None:
    """Linear dimension: offset extension lines + dimension line with inward arrows."""
    x0, y0 = p0
    x1, y1 = p1
    dx, dy = x1 - x0, y1 - y0
    length = math.hypot(dx, dy)
    if length < 1e-9:
        return
    ux, uy = dx / length, dy / length
    nx, ny = side * (-uy), side * ux
    ts = text_side if text_side is not None else side

    # Extension lines: gap from object → past dimension line.
    ext_len = offset + EXT_OVERHANG
    ax.plot(
        [x0 + nx * GAP_FROM_OBJECT, x0 + nx * ext_len],
        [y0 + ny * GAP_FROM_OBJECT, y0 + ny * ext_len],
        color=color,
        lw=LW_DIM,
        ls=ls,
        zorder=4,
    )
    ax.plot(
        [x1 + nx * GAP_FROM_OBJECT, x1 + nx * ext_len],
        [y1 + ny * GAP_FROM_OBJECT, y1 + ny * ext_len],
        color=color,
        lw=LW_DIM,
        ls=ls,
        zorder=4,
    )

    ox0, oy0 = x0 + nx * offset, y0 + ny * offset
    ox1, oy1 = x1 + nx * offset, y1 + ny * offset
    ap = _ARROW_DASH if ls == "--" else _ARROW
    ax.annotate(
        "",
        xy=(ox1, oy1),
        xytext=(ox0, oy0),
        arrowprops=dict(**ap, color=color),
    )
    mx, my = 0.5 * (ox0 + ox1), 0.5 * (oy0 + oy1)
    tx, ty = mx + ts * nx * 0.07, my + ts * ny * 0.07
    ax.text(mx, my, label, fontsize=9, color=color, ha="center", va="center", zorder=7, bbox=_label_bbox())


def dim_axis_h(
    ax,
    x0: float,
    x1: float,
    y: float,
    label: str,
    *,
    offset: float = 0.12,
    color: str = INK,
    ls: str = "-",
    below: bool = True,
) -> None:
    """Horizontal dimension (GOST: text above the dimension line when placed below part)."""
    sign = -1.0 if below else 1.0
    y_dim = y + sign * offset
    y_ext_end = y_dim + sign * EXT_OVERHANG
    y_obj_start = y + sign * GAP_FROM_OBJECT

    ax.plot([x0, x0], [y_obj_start, y_ext_end], color=color, lw=LW_DIM, ls=ls, zorder=4)
    ax.plot([x1, x1], [y_obj_start, y_ext_end], color=color, lw=LW_DIM, ls=ls, zorder=4)
    ap = _ARROW_DASH if ls == "--" else _ARROW
    ax.annotate(
        "",
        xy=(x1, y_dim),
        xytext=(x0, y_dim),
        arrowprops=dict(**ap, color=color),
    )
    ty = y_dim + sign * 0.055
    ax.text(0.5 * (x0 + x1), ty, label, fontsize=9, color=color, ha="center", va="center", zorder=7, bbox=_label_bbox())


def dim_axis_v(
    ax,
    y0: float,
    y1: float,
    x: float,
    label: str,
    *,
    offset: float = 0.12,
    color: str = INK,
    ls: str = "-",
    left: bool = True,
) -> None:
    """Vertical dimension (GOST: text to the left of the dimension line)."""
    sign = -1.0 if left else 1.0
    x_dim = x + sign * offset
    x_ext_end = x_dim + sign * EXT_OVERHANG
    x_obj_start = x + sign * GAP_FROM_OBJECT

    ax.plot([x_obj_start, x_ext_end], [y0, y0], color=color, lw=LW_DIM, ls=ls, zorder=4)
    ax.plot([x_obj_start, x_ext_end], [y1, y1], color=color, lw=LW_DIM, ls=ls, zorder=4)
    ap = _ARROW_DASH if ls == "--" else _ARROW
    ax.annotate(
        "",
        xy=(x_dim, y1),
        xytext=(x_dim, y0),
        arrowprops=dict(**ap, color=color),
    )
    tx = x_dim + sign * 0.055
    ax.text(tx, 0.5 * (y0 + y1), label, fontsize=9, color=color, ha="center", va="center", zorder=7, bbox=_label_bbox())


def leader(
    ax,
    tip: tuple[float, float],
    label: str,
    text_pos: tuple[float, float],
    *,
    color: str = INK,
    fontsize: float = 9,
    elbow: str = "horizontal",
) -> None:
    """GOST leader: thin polyline with horizontal text shelf at free end."""
    px, py = tip
    tx, ty = text_pos
    if elbow == "horizontal":
        ax.plot([tx, px], [ty, ty], color=color, lw=LW_DIM, zorder=5, solid_capstyle="butt")
        ax.plot([px, px], [ty, py], color=color, lw=LW_DIM, zorder=5, solid_capstyle="butt")
        ax.annotate("", xy=(px, py), xytext=(px, ty), arrowprops=dict(**_ARROW, color=color))
        ax.text(tx, ty, label, fontsize=fontsize, color=color, ha="left", va="bottom", zorder=7)
    else:
        ax.plot([tx, px], [ty, py], color=color, lw=LW_DIM, zorder=5)
        ax.annotate("", xy=(px, py), xytext=(tx, ty), arrowprops=dict(**_ARROW, color=color))
        ax.text(tx, ty, label, fontsize=fontsize, color=color, ha="right", va="bottom", zorder=7)
