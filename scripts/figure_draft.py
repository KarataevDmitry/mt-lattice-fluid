"""Shared drafting-style annotations for book figures (GOST-like dimension lines)."""

from __future__ import annotations

import math

INK = "#222222"
MUTED = "#666666"
LIGHT = "#aaaaaa"


def dim_radius(
    ax,
    r: float,
    angle_deg: float,
    label: str,
    *,
    color: str = INK,
    ls: str = "-",
    lw: float = 1.25,
    tick: float = 0.04,
    label_gap: float = 0.14,
    ox: float = 0.0,
    oy: float = 0.0,
) -> None:
    """Radial dimension from (ox, oy): extension + arrow + label outside."""
    th = math.radians(angle_deg)
    ux, uy = math.cos(th), math.sin(th)
    px, py = ox + r * ux, oy + r * uy
    ax.plot([ox, px], [oy, py], color=color, lw=lw, ls=ls, zorder=4, solid_capstyle="butt")
    nx, ny = -uy, ux
    ax.plot(
        [px - tick * nx, px + tick * nx],
        [py - tick * ny, py + tick * ny],
        color=color,
        lw=lw,
        zorder=5,
        solid_capstyle="round",
    )
    ax.annotate(
        "",
        xy=(px, py),
        xytext=(ox, oy),
        arrowprops=dict(arrowstyle="-|>", color=color, lw=lw, linestyle=ls),
    )
    lx, ly = ox + (r + label_gap) * ux, oy + (r + label_gap) * uy
    ha = "left" if ux > 0.2 else ("right" if ux < -0.2 else "center")
    va = "bottom" if uy > 0.2 else ("top" if uy < -0.2 else "center")
    ax.text(lx, ly, label, fontsize=10, color=color, ha=ha, va=va, zorder=6)


def dim_linear(
    ax,
    p0: tuple[float, float],
    p1: tuple[float, float],
    label: str,
    *,
    offset: float = 0.16,
    color: str = INK,
    ls: str = "-",
    lw: float = 1.2,
    label_pad: float = 0.06,
    side: float = 1.0,
) -> None:
    """Linear dimension between p0 and p1 with offset extension lines."""
    x0, y0 = p0
    x1, y1 = p1
    dx, dy = x1 - x0, y1 - y0
    length = math.hypot(dx, dy)
    if length < 1e-9:
        return
    ux, uy = dx / length, dy / length
    nx, ny = side * (-uy), side * ux

    ext = offset * 1.12
    ax.plot([x0, x0 + nx * ext], [y0, y0 + ny * ext], color=color, lw=lw * 0.9, ls=ls, zorder=3)
    ax.plot([x1, x1 + nx * ext], [y1, y1 + ny * ext], color=color, lw=lw * 0.9, ls=ls, zorder=3)

    ox0, oy0 = x0 + nx * offset, y0 + ny * offset
    ox1, oy1 = x1 + nx * offset, y1 + ny * offset
    ax.annotate(
        "",
        xy=(ox1, oy1),
        xytext=(ox0, oy0),
        arrowprops=dict(arrowstyle="<->", color=color, lw=lw, linestyle=ls),
    )
    mx, my = 0.5 * (ox0 + ox1), 0.5 * (oy0 + oy1)
    ax.text(mx + nx * label_pad, my + ny * label_pad, label, fontsize=9, color=color, ha="center", va="center", zorder=6)


def leader(
    ax,
    tip: tuple[float, float],
    label: str,
    text_pos: tuple[float, float],
    *,
    color: str = INK,
    lw: float = 1.1,
    fontsize: float = 10,
) -> None:
    """Callout: arrow from label to feature."""
    ax.annotate(
        label,
        xy=tip,
        xytext=text_pos,
        fontsize=fontsize,
        color=color,
        arrowprops=dict(arrowstyle="-|>", color=color, lw=lw, connectionstyle="arc3,rad=0.08"),
    )


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
) -> None:
    """Horizontal dimension line below/above a feature."""
    y_dim = y - offset
    ax.plot([x0, x0], [y, y_dim - 0.04], color=color, lw=0.9, ls=ls, zorder=3)
    ax.plot([x1, x1], [y, y_dim - 0.04], color=color, lw=0.9, ls=ls, zorder=3)
    ax.annotate(
        "",
        xy=(x1, y_dim),
        xytext=(x0, y_dim),
        arrowprops=dict(arrowstyle="<->", color=color, lw=1.1, linestyle=ls),
    )
    ax.text(0.5 * (x0 + x1), y_dim - 0.08, label, fontsize=9, color=color, ha="center", va="top", zorder=6)


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
) -> None:
    """Vertical dimension line left/right of a feature."""
    x_dim = x - offset
    ax.plot([x, x_dim - 0.04], [y0, y0], color=color, lw=0.9, ls=ls, zorder=3)
    ax.plot([x, x_dim - 0.04], [y1, y1], color=color, lw=0.9, ls=ls, zorder=3)
    ax.annotate(
        "",
        xy=(x_dim, y1),
        xytext=(x_dim, y0),
        arrowprops=dict(arrowstyle="<->", color=color, lw=1.1, linestyle=ls),
    )
    ax.text(x_dim - 0.08, 0.5 * (y0 + y1), label, fontsize=9, color=color, ha="right", va="center", zorder=6)
