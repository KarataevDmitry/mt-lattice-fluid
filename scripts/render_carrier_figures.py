#!/usr/bin/env python3
"""Render carrier-geometry figures for book/sources/chapters/01-carrier.tex."""

from __future__ import annotations

import math
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Polygon
from mpl_toolkits.mplot3d.axes3d import Axes3D

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "book" / "sources" / "figures"

plt.rcParams.update(
    {
        "font.family": "serif",
        "font.serif": ["Times New Roman", "DejaVu Serif"],
        "mathtext.fontset": "cm",
        "axes.unicode_minus": False,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
    }
)


def _save(fig: plt.Figure, name: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / name
    fig.savefig(path, bbox_inches="tight", pad_inches=0.08)
    plt.close(fig)
    print(f"wrote {path}")


def fig_hex_kgeom() -> None:
    """Hexagonal Voronoi cell, six neighbors, R_in / R_out."""
    a = 1.0
    angles = np.linspace(0, 2 * np.pi, 7)[:-1] + np.pi / 6
    verts = np.column_stack([a * np.cos(angles), a * np.sin(angles)])

    fig, ax = plt.subplots(figsize=(5.6, 4.8))
    ax.set_aspect("equal")
    ax.axis("off")

    hex_patch = Polygon(verts, closed=True, fill=False, lw=1.6, ec="#1a4d8f")
    ax.add_patch(hex_patch)

    # neighbor centers on edges (distance a from center along edge midlines)
    for i in range(6):
        mid = 0.5 * (verts[i] + verts[(i + 1) % 6])
        ax.plot(*mid, "o", color="#555", ms=5)
        ax.plot([0, mid[0]], [0, mid[1]], color="#bbbbbb", lw=0.8, ls="--", zorder=0)

    ax.plot(0, 0, "o", color="#c0392b", ms=7, zorder=5)

    # R_out to vertex
    v = verts[0]
    ax.annotate(
        "",
        xy=v,
        xytext=(0, 0),
        arrowprops=dict(arrowstyle="-|>", color="#c0392b", lw=1.4),
    )
    ax.text(0.55 * v[0], 0.55 * v[1] + 0.06, r"$R_{\mathrm{out}}=a$", color="#c0392b", fontsize=12)

    # R_in apothem
    mid = 0.5 * (verts[0] + verts[1])
    ax.annotate(
        "",
        xy=mid,
        xytext=(0, 0),
        arrowprops=dict(arrowstyle="-|>", color="#27ae60", lw=1.4),
    )
    ax.text(0.35 * mid[0] - 0.05, 0.35 * mid[1] - 0.12, r"$R_{\mathrm{in}}$", color="#27ae60", fontsize=12)

    ax.text(
        0.02,
        -1.35,
        r"$\kappa_{\mathrm{hex}}=R_{\mathrm{in}}/R_{\mathrm{out}}=\sqrt{3}/2$",
        fontsize=12,
        ha="center",
    )
    ax.text(0, 1.28, r"гексагональная ячейка Вороного, $|N|=6$", ha="center", fontsize=11)

    lim = 1.45
    ax.set_xlim(-lim, lim)
    ax.set_ylim(-lim, lim)
    _save(fig, "carrier-hex-kgeom.pdf")


def _fcc_vertices(a: float = 1.0) -> np.ndarray:
    s = a / math.sqrt(2)
    uniq: list[tuple[float, float, float]] = []
    for i in range(3):
        for sx in (-1, 1):
            for sy in (-1, 1):
                v = [0.0, 0.0, 0.0]
                others = [(i + 1) % 3, (i + 2) % 3]
                v[others[0]] = sx * s
                v[others[1]] = sy * s
                tup = (v[0], v[1], v[2])
                if tup not in uniq:
                    uniq.append(tup)
    return np.array(uniq)


def _cubocta_edges(verts: np.ndarray, a: float) -> list[tuple[int, int]]:
    edges = []
    for i, vi in enumerate(verts):
        for j, vj in enumerate(verts):
            if i >= j:
                continue
            if abs(np.linalg.norm(vi - vj) - a) < 1e-6:
                edges.append((i, j))
    return edges


def fig_fcc_shell() -> None:
    """First coordination shell: cuboctahedron / 12 FCC neighbors."""
    a = 1.0
    verts = _fcc_vertices(a)
    edges = _cubocta_edges(verts, a)

    fig = plt.figure(figsize=(5.8, 5.2))
    ax: Axes3D = fig.add_subplot(111, projection="3d")

    for i, j in edges:
        xs = [verts[i, 0], verts[j, 0]]
        ys = [verts[i, 1], verts[j, 1]]
        zs = [verts[i, 2], verts[j, 2]]
        ax.plot(xs, ys, zs, color="#1a4d8f", lw=1.2, alpha=0.9)

    ax.scatter(verts[:, 0], verts[:, 1], verts[:, 2], c="#c0392b", s=36, depthshade=True)
    ax.scatter([0], [0], [0], c="#27ae60", s=50, depthshade=True)

    for i, j in edges:
        for k in (i, j):
            ax.plot([0, verts[k, 0]], [0, verts[k, 1]], [0, verts[k, 2]], color="#cccccc", lw=0.6, alpha=0.5)

    ax.set_box_aspect((1, 1, 1))
    lim = 0.85
    ax.set_xlim(-lim, lim)
    ax.set_ylim(-lim, lim)
    ax.set_zlim(-lim, lim)
    ax.set_xlabel(r"$x$", labelpad=-2)
    ax.set_ylabel(r"$y$", labelpad=-2)
    ax.set_zlabel(r"$z$", labelpad=-2)
    ax.view_init(elev=22, azim=-58)
    ax.set_title(r"FCC: $|N|=12$, ребро $a=h_L$", fontsize=11, pad=8)
    ax.grid(False)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_zticks([])
    _save(fig, "carrier-fcc-shell.pdf")


def fig_hull_voronoi() -> None:
    """Radial comparison: R_out, R_in^hull, R_in^Voronoi."""
    a = 1.0
    r_out = a
    r_hull = a / math.sqrt(2)
    r_vor = a / 2

    fig, ax = plt.subplots(figsize=(6.2, 3.6))
    ax.set_aspect("equal")
    ax.axis("off")

    for r, col, lw, ls in (
        (r_out, "#c0392b", 1.8, "-"),
        (r_hull, "#1a4d8f", 1.6, "-"),
        (r_vor, "#27ae60", 1.6, "--"),
    ):
        circ = plt.Circle((0, 0), r, fill=False, ec=col, lw=lw, ls=ls)
        ax.add_patch(circ)

    ax.plot(0, 0, "o", color="#333", ms=6)
    ax.plot([r_out], [0], "o", color="#c0392b", ms=6)
    ax.plot([r_vor], [0], "o", color="#27ae60", ms=5)

    ax.annotate(
        r"$R_{\mathrm{out}}=a$",
        xy=(0.72 * r_out, 0.05),
        fontsize=12,
        color="#c0392b",
    )
    ax.annotate(
        r"$R_{\mathrm{in}}^{\mathrm{hull}}=a/\sqrt{2}$",
        xy=(0.55 * r_hull, -0.22),
        fontsize=11,
        color="#1a4d8f",
    )
    ax.annotate(
        r"$R_{\mathrm{in}}^{\mathrm{Voronoi}}=a/2$",
        xy=(0.38 * r_vor, 0.18),
        fontsize=11,
        color="#27ae60",
    )
    ax.annotate(
        "сосед",
        xy=(r_out, 0),
        xytext=(r_out + 0.12, 0.25),
        fontsize=10,
        arrowprops=dict(arrowstyle="->", color="#555", lw=0.8),
    )

    ax.text(
        0,
        -1.15,
        r"$\kappa_{\mathrm{FCC}}=R_{\mathrm{in}}^{\mathrm{hull}}/R_{\mathrm{out}}=1/\sqrt{2}$"
        r";\quad R_{\mathrm{in}}^{\mathrm{Voronoi}}=\kappa\, R_{\mathrm{in}}^{\mathrm{hull}}$",
        ha="center",
        fontsize=11,
    )
    ax.set_xlim(-1.25, 1.55)
    ax.set_ylim(-1.35, 1.15)
    _save(fig, "carrier-hull-voronoi.pdf")


def main() -> None:
    fig_hex_kgeom()
    fig_fcc_shell()
    fig_hull_voronoi()


if __name__ == "__main__":
    main()
