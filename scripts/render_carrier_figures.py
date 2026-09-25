#!/usr/bin/env python3
"""Render carrier-geometry figures for book/sources/chapters/01-carrier.tex."""

from __future__ import annotations

import math
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Polygon, Wedge
from mpl_toolkits.mplot3d.axes3d import Axes3D
from scipy.spatial import Voronoi

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

COL = {
    "blue": "#1a4d8f",
    "red": "#c0392b",
    "green": "#27ae60",
    "gray": "#888888",
    "light": "#cccccc",
    "node": "#333333",
}


def _save(fig: plt.Figure, name: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / name
    fig.savefig(path, bbox_inches="tight", pad_inches=0.08)
    plt.close(fig)
    print(f"wrote {path}")


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


def _fcc_lattice_points(radius: int = 2, a: float = 1.0) -> np.ndarray:
    s = a / math.sqrt(2)
    prim = np.array([[s, s, 0.0], [s, 0.0, s], [0.0, s, s]])
    pts: set[tuple[float, float, float]] = set()
    for n1 in range(-radius, radius + 1):
        for n2 in range(-radius, radius + 1):
            for n3 in range(-radius, radius + 1):
                p = n1 * prim[0] + n2 * prim[1] + n3 * prim[2]
                pts.add(tuple(np.round(p, 10)))
    return np.array(sorted(pts))


def _wire_3d(ax: Axes3D, verts: np.ndarray, edges: list[tuple[int, int]], **kw) -> None:
    for i, j in edges:
        ax.plot(
            [verts[i, 0], verts[j, 0]],
            [verts[i, 1], verts[j, 1]],
            [verts[i, 2], verts[j, 2]],
            **kw,
        )


def _style_3d(ax: Axes3D, lim: float, elev: float = 22, azim: float = -58) -> None:
    ax.set_box_aspect((1, 1, 1))
    ax.set_xlim(-lim, lim)
    ax.set_ylim(-lim, lim)
    ax.set_zlim(-lim, lim)
    ax.view_init(elev=elev, azim=azim)
    ax.grid(False)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_zticks([])


def fig_lattice_field() -> None:
    """Lattice snippet + spinor field z on a node."""
    a = 1.0
    rows, cols = 4, 5
    pts = []
    for r in range(rows):
        for c in range(cols):
            pts.append((c * a * 1.05, r * a * 0.92))

    fig, ax = plt.subplots(figsize=(6.0, 3.8))
    ax.set_aspect("equal")
    ax.axis("off")

    cx, cy = 2 * a * 1.05, 1 * a * 0.92
    for x, y in pts:
        col = COL["red"] if abs(x - cx) < 0.01 and abs(y - cy) < 0.01 else COL["node"]
        ms = 9 if col == COL["red"] else 5
        ax.plot(x, y, "o", color=col, ms=ms, zorder=3)
        for dx, dy in ((a * 1.05, 0), (-a * 1.05, 0), (0, a * 0.92)):
            nx, ny = x + dx, y + dy
            if any(abs(nx - px) < 0.01 and abs(ny - py) < 0.01 for px, py in pts):
                ax.plot([x, nx], [y, ny], color=COL["light"], lw=0.9, zorder=1)

    ax.annotate(
        r"$z(x)\in\mathbb{C}^2$",
        xy=(cx, cy),
        xytext=(cx + 0.55, cy + 0.55),
        fontsize=12,
        arrowprops=dict(arrowstyle="->", color=COL["blue"], lw=1.2),
    )
    ax.text(0.02, -0.35, r"$\Lambda$ — счётное множество узлов; шаг $h_L$, такт $h_T$, $c_0=h_L/h_T$", fontsize=10)
    ax.set_xlim(-0.4, 4.8)
    ax.set_ylim(-0.6, 3.2)
    _save(fig, "carrier-lattice-field.pdf")


def fig_epsilon_neighborhood() -> None:
    """One-tick neighborhood N(x) on hex stencil."""
    a = 1.0
    angles = np.linspace(0, 2 * np.pi, 7)[:-1] + np.pi / 6
    dirs = [np.array([np.cos(t), np.sin(t)]) for t in angles]

    fig, ax = plt.subplots(figsize=(5.4, 4.6))
    ax.set_aspect("equal")
    ax.axis("off")

    ax.plot(0, 0, "o", color=COL["red"], ms=9, zorder=5)
    for d in dirs:
        p = a * d
        ax.plot([0, p[0]], [0, p[1]], color=COL["blue"], lw=1.5, zorder=2)
        ax.plot(p[0], p[1], "o", color=COL["blue"], ms=7, zorder=4)

    wedge = Wedge((0, 0), a * 1.05, 0, 360, width=0.08, facecolor=COL["green"], alpha=0.25, zorder=1)
    ax.add_patch(wedge)
    ax.text(0, -1.35, r"$N(x)$: узлы на расстоянии $h_L$ за один такт $h_T$", ha="center", fontsize=11)
    ax.text(0, 1.25, r"$c_0h_T=h_L$", ha="center", fontsize=11, color=COL["green"])
    ax.set_xlim(-1.4, 1.4)
    ax.set_ylim(-1.55, 1.45)
    _save(fig, "carrier-epsilon.pdf")


def _draw_triangle_tiling(ax, a: float, rows: int, cols: int, highlight_idx: tuple[int, int, int] | None = None) -> None:
    """Equilateral-triangle tessellation via parallelogram splits."""
    h = a * math.sqrt(3) / 2
    v1 = np.array([a, 0.0])
    v2 = np.array([a / 2, h])
    for i in range(-cols, cols):
        for j in range(-rows, rows):
            p = i * v1 + j * v2
            tris = (
                (0, np.vstack([p, p + v1, p + v2])),
                (1, np.vstack([p + v1, p + v2, p + v1 + v2])),
            )
            for t_idx, verts in tris:
                hi = highlight_idx == (i, j, t_idx)
                ax.add_patch(
                    Polygon(
                        verts,
                        closed=True,
                        facecolor="#fff4e8" if hi else ("#eef4fb" if t_idx == 0 else "#f7f9fc"),
                        edgecolor=COL["blue"],
                        lw=1.4 if hi else 0.75,
                        zorder=2 if hi else 1,
                    )
                )


def _draw_square_tiling(ax, a: float, n: int, highlight: tuple[int, int] | None = None) -> None:
    """Square-grid tessellation of the plane."""
    for i in range(-n, n):
        for j in range(-n, n):
            x, y = i * a, j * a
            hi = highlight == (i, j)
            ax.add_patch(
                Polygon(
                    [(x, y), (x + a, y), (x + a, y + a), (x, y + a)],
                    closed=True,
                    facecolor="#fff4e8" if hi else "#eef4fb",
                    edgecolor=COL["blue"],
                    lw=1.4 if hi else 0.75,
                    zorder=2 if hi else 1,
                )
            )


def _draw_hex_tiling(ax, s: float, rings: int, highlight: tuple[int, int] | None = None) -> None:
    """Hexagonal (honeycomb) tessellation of the plane."""
    dx = math.sqrt(3) * s
    dy = 1.5 * s
    for row in range(-rings, rings + 1):
        for col in range(-rings, rings + 1):
            cx = col * dx + (row % 2) * dx / 2
            cy = row * dy
            angles = np.linspace(0, 2 * np.pi, 7)[:-1] + np.pi / 6
            verts = np.column_stack([cx + s * np.cos(angles), cy + s * np.sin(angles)])
            hi = highlight == (row, col)
            ax.add_patch(
                Polygon(
                    verts,
                    closed=True,
                    facecolor="#fff4e8" if hi else "#eef4fb",
                    edgecolor=COL["blue"],
                    lw=1.4 if hi else 0.75,
                    zorder=2 if hi else 1,
                )
            )


def fig_plane_tilings() -> None:
    """Three regular plane tilings — the plane partitioned into tiles."""
    fig, axes = plt.subplots(1, 3, figsize=(9.2, 3.1))

    # triangular tiling (tile = △); nodes at tile centres → |N|=3
    ax = axes[0]
    ax.set_aspect("equal")
    ax.axis("off")
    a = 0.55
    _draw_triangle_tiling(ax, a=a, rows=5, cols=5, highlight_idx=(0, 0, 0))
    h = a * math.sqrt(3) / 2
    v1 = np.array([a, 0.0])
    v2 = np.array([a / 2, h])
    cx, cy = (v1 + v2) / 3  # centroid of highlighted triangle
    for ang in np.deg2rad([0, 120, 240]):
        p = cx + a * np.array([np.cos(ang), np.sin(ang)])
        ax.plot([cx, p[0]], [cy, p[1]], color=COL["red"], lw=0.9, ls=":", zorder=4)
        ax.plot(p[0], p[1], "o", color=COL["node"], ms=3.5, zorder=5)
    ax.plot(cx, cy, "o", color=COL["red"], ms=5, zorder=6)
    ax.set_xlim(-2.6, 2.6)
    ax.set_ylim(-2.0, 2.0)
    ax.set_title(r"треугольники, $|N|=3$", fontsize=10)

    # square tiling
    ax = axes[1]
    ax.set_aspect("equal")
    ax.axis("off")
    a = 0.65
    _draw_square_tiling(ax, a=a, n=4, highlight=(0, 0))
    cx, cy = a / 2, a / 2
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        p = np.array([cx, cy]) + a * np.array([dx, dy])
        ax.plot([cx, p[0]], [cy, p[1]], color=COL["red"], lw=0.9, ls=":", zorder=4)
        ax.plot(p[0], p[1], "o", color=COL["node"], ms=3.5, zorder=5)
    diag = a / math.sqrt(2)
    ax.plot([cx + diag, cx - diag], [cy + diag, cy - diag], color=COL["red"], lw=0.9, ls="--", zorder=3)
    ax.plot([cx + diag, cx - diag], [cy - diag, cy + diag], color=COL["red"], lw=0.9, ls="--", zorder=3)
    ax.plot(cx, cy, "o", color=COL["red"], ms=5, zorder=6)
    ax.text(cx + 0.42 * a, cy + 0.42 * a, r"$h_L\sqrt{2}$", fontsize=8, color=COL["red"])
    ax.set_xlim(-2.2, 2.2)
    ax.set_ylim(-2.2, 2.2)
    ax.set_title(r"квадраты, $|N|=4$", fontsize=10)

    # hexagonal tiling
    ax = axes[2]
    ax.set_aspect("equal")
    ax.axis("off")
    s = 0.42
    _draw_hex_tiling(ax, s=s, rings=4, highlight=(0, 0))
    ax.plot(0, 0, "o", color=COL["red"], ms=5, zorder=6)
    for ang in np.linspace(0, 2 * np.pi, 7)[:-1]:
        p = s * np.array([np.cos(ang), np.sin(ang)])
        ax.plot([0, p[0]], [0, p[1]], color=COL["red"], lw=0.9, ls=":", zorder=4)
        ax.plot(p[0], p[1], "o", color=COL["node"], ms=3.5, zorder=5)
    lim = 2.5
    ax.set_xlim(-lim, lim)
    ax.set_ylim(-lim, lim)
    ax.set_title(r"шестиугольники, $|N|=6$", fontsize=10)

    fig.suptitle("Три регулярных замощения плоскости", fontsize=11, y=1.02)
    _save(fig, "carrier-tilings.pdf")


def fig_light_cone() -> None:
    """Spacetime: first shell on cone, second shell spacelike."""
    a = 1.0
    ht = 1.0
    c0 = a / ht

    fig, axes = plt.subplots(1, 2, figsize=(8.6, 3.6))

    # spacetime diagram
    ax = axes[0]
    ax.set_aspect("equal")
    ax.axhline(0, color="#ddd", lw=0.8)
    ax.axvline(0, color="#ddd", lw=0.8)
    t = np.linspace(0, 1.2, 50)
    ax.plot(c0 * t, t, color=COL["green"], lw=1.4)
    ax.plot(-c0 * t, t, color=COL["green"], lw=1.4)
    ax.fill_between(c0 * t, 0, t, alpha=0.08, color=COL["green"])
    ax.plot([a, a], [0, ht], "o-", color=COL["blue"], lw=1.2, ms=6, label=r"1-я оболочка, $r=h_L$")
    ax.plot([a * math.sqrt(2), a * math.sqrt(2)], [0, ht], "x", color=COL["red"], ms=10, mew=2)
    ax.annotate(
        r"2-я оболочка, $r=h_L\sqrt{2}$",
        xy=(a * math.sqrt(2), ht),
        xytext=(a * 1.05, ht + 0.25),
        fontsize=9,
        color=COL["red"],
        arrowprops=dict(arrowstyle="->", color=COL["red"], lw=0.8),
    )
    ax.text(0.15, 0.95, "пространственноподобно", fontsize=8, color=COL["red"], rotation=0)
    ax.set_xlabel(r"пространство $x$")
    ax.set_ylabel(r"время $t$")
    ax.set_title(r"световой конус $c_0$", fontsize=10)
    ax.set_xlim(-0.2, 1.8)
    ax.set_ylim(-0.05, 1.35)

    # square lattice spatial view
    ax = axes[1]
    ax.set_aspect("equal")
    ax.axis("off")
    ax.plot(0, 0, "o", color=COL["red"], ms=8)
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        ax.plot([0, dx], [0, dy], color=COL["blue"], lw=1.4)
        ax.plot(dx, dy, "o", color=COL["blue"], ms=6)
    for dx, dy in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
        ax.plot([0, dx], [0, dy], color=COL["red"], lw=1.0, ls="--")
        ax.plot(dx, dy, "x", color=COL["red"], ms=8, mew=2)
    ax.text(0, -1.45, r"за $h_T$ достижимы только рёбра длины $h_L$", ha="center", fontsize=10)
    ax.set_xlim(-1.5, 1.5)
    ax.set_ylim(-1.65, 1.35)
    ax.set_title("квадратная решётка", fontsize=10)

    fig.suptitle("Световой конус отсекает вторую координационную оболочку", fontsize=11, y=1.02)
    _save(fig, "carrier-light-cone.pdf")


def fig_hex_kgeom() -> None:
    a = 1.0
    angles = np.linspace(0, 2 * np.pi, 7)[:-1] + np.pi / 6
    verts = np.column_stack([a * np.cos(angles), a * np.sin(angles)])

    fig, ax = plt.subplots(figsize=(5.6, 4.8))
    ax.set_aspect("equal")
    ax.axis("off")

    hex_patch = Polygon(verts, closed=True, fill=False, lw=1.6, ec=COL["blue"])
    ax.add_patch(hex_patch)

    for i in range(6):
        mid = 0.5 * (verts[i] + verts[(i + 1) % 6])
        ax.plot(*mid, "o", color=COL["gray"], ms=5)
        ax.plot([0, mid[0]], [0, mid[1]], color=COL["light"], lw=0.8, ls="--", zorder=0)

    ax.plot(0, 0, "o", color=COL["red"], ms=7, zorder=5)
    v = verts[0]
    ax.annotate("", xy=v, xytext=(0, 0), arrowprops=dict(arrowstyle="-|>", color=COL["red"], lw=1.4))
    ax.text(0.55 * v[0], 0.55 * v[1] + 0.06, r"$R_{\mathrm{out}}=a$", color=COL["red"], fontsize=12)
    mid = 0.5 * (verts[0] + verts[1])
    ax.annotate("", xy=mid, xytext=(0, 0), arrowprops=dict(arrowstyle="-|>", color=COL["green"], lw=1.4))
    ax.text(0.35 * mid[0] - 0.05, 0.35 * mid[1] - 0.12, r"$R_{\mathrm{in}}$", color=COL["green"], fontsize=12)
    ax.text(0.02, -1.35, r"$\kappa_{\mathrm{hex}}=R_{\mathrm{in}}/R_{\mathrm{out}}=\sqrt{3}/2$", fontsize=12, ha="center")
    ax.text(0, 1.28, r"гексагональная ячейка Вороного, $|N|=6$", ha="center", fontsize=11)
    ax.set_xlim(-1.45, 1.45)
    ax.set_ylim(-1.45, 1.45)
    _save(fig, "carrier-hex-kgeom.pdf")


def fig_packing_compare() -> None:
    """SC / BCC / FCC coordination numbers."""
    fig, axes = plt.subplots(1, 3, figsize=(8.8, 2.8))
    specs = [
        ("SC", 6, [(1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)]),
        ("BCC", 8, [(1, 1, 1), (1, 1, -1), (1, -1, 1), (1, -1, -1), (-1, 1, 1), (-1, 1, -1), (-1, -1, 1), (-1, -1, -1)]),
        ("FCC", 12, None),
    ]
    for ax, (name, n, dirs) in zip(axes, specs):
        ax.set_aspect("equal")
        ax.axis("off")
        ax.plot(0, 0, "o", color=COL["red"], ms=8)
        if name == "FCC":
            dirs = _fcc_vertices(1.0)
            dirs = [tuple(v) for v in dirs]
        else:
            dirs = [tuple(np.array(d) / np.linalg.norm(d)) for d in dirs]
        for d in dirs:
            ax.plot([0, d[0]], [0, d[1]], color=COL["blue"], lw=1.0)
            ax.plot(d[0], d[1], "o", color=COL["node"], ms=4)
        ax.set_xlim(-1.2, 1.2)
        ax.set_ylim(-1.2, 1.2)
        ax.set_title(f"{name}, $|N|={n}$", fontsize=10)
    fig.suptitle("Координационные числа кубических упаковок (проекция)", fontsize=11, y=1.02)
    _save(fig, "carrier-packing.pdf")


def fig_fcc_shell() -> None:
    a = 1.0
    verts = _fcc_vertices(a)
    edges = _cubocta_edges(verts, a)

    fig = plt.figure(figsize=(5.8, 5.2))
    ax: Axes3D = fig.add_subplot(111, projection="3d")
    _wire_3d(ax, verts, edges, color=COL["blue"], lw=1.2, alpha=0.9)
    ax.scatter(verts[:, 0], verts[:, 1], verts[:, 2], c=COL["red"], s=36, depthshade=True)
    ax.scatter([0], [0], [0], c=COL["green"], s=50, depthshade=True)
    for i, j in edges:
        for k in (i, j):
            ax.plot([0, verts[k, 0]], [0, verts[k, 1]], [0, verts[k, 2]], color=COL["light"], lw=0.6, alpha=0.5)
    _style_3d(ax, 0.85)
    ax.set_title(r"FCC: $|N|=12$, ребро $a=h_L$", fontsize=11, pad=8)
    _save(fig, "carrier-fcc-shell.pdf")


def fig_cubocta_faces() -> None:
    """Square vs triangular face distances on cuboctahedron."""
    a = 1.0
    s = a / math.sqrt(2)
    verts = _fcc_vertices(a)
    edges = _cubocta_edges(verts, a)

    fig = plt.figure(figsize=(6.0, 5.0))
    ax: Axes3D = fig.add_subplot(111, projection="3d")
    _wire_3d(ax, verts, edges, color=COL["blue"], lw=1.0, alpha=0.7)

    sq = np.array([[s, s, 0], [s, -s, 0], [s, 0, s], [s, 0, -s]])
    tri = np.array([[s, s, 0], [s, 0, s], [0, s, s]])
    sq_loop = np.vstack([sq, sq[0]])
    tri_loop = np.vstack([tri, tri[0]])
    ax.plot(sq_loop[:, 0], sq_loop[:, 1], sq_loop[:, 2], color=COL["red"], lw=2.2)
    ax.plot(tri_loop[:, 0], tri_loop[:, 1], tri_loop[:, 2], color=COL["green"], lw=2.2, ls="--")

    ax.scatter([0], [0], [0], c=COL["node"], s=40)
    _style_3d(ax, 0.9, elev=18, azim=-42)
    ax.text2D(0.05, 0.92, r"квадратная грань: $R_{\mathrm{in}}^{\mathrm{hull}}=a/\sqrt{2}$", transform=ax.transAxes, color=COL["red"], fontsize=10)
    ax.text2D(0.05, 0.86, r"треугольная грань: $a\sqrt{2/3}$", transform=ax.transAxes, color=COL["green"], fontsize=10)
    ax.set_title("Кубооктаэдр: разные грани — разные расстояния", fontsize=10, pad=8)
    _save(fig, "carrier-cubocta-faces.pdf")


def fig_hull_voronoi() -> None:
    a = 1.0
    r_out, r_hull, r_vor = a, a / math.sqrt(2), a / 2

    fig, ax = plt.subplots(figsize=(6.2, 3.6))
    ax.set_aspect("equal")
    ax.axis("off")
    for r, col, lw, ls in ((r_out, COL["red"], 1.8, "-"), (r_hull, COL["blue"], 1.6, "-"), (r_vor, COL["green"], 1.6, "--")):
        ax.add_patch(plt.Circle((0, 0), r, fill=False, ec=col, lw=lw, ls=ls))
    ax.plot(0, 0, "o", color=COL["node"], ms=6)
    ax.plot([r_out], [0], "o", color=COL["red"], ms=6)
    ax.annotate(r"$R_{\mathrm{out}}=a$", xy=(0.72 * r_out, 0.05), fontsize=12, color=COL["red"])
    ax.annotate(r"$R_{\mathrm{in}}^{\mathrm{hull}}=a/\sqrt{2}$", xy=(0.55 * r_hull, -0.22), fontsize=11, color=COL["blue"])
    ax.annotate(r"$R_{\mathrm{in}}^{\mathrm{Voronoi}}=a/2$", xy=(0.38 * r_vor, 0.18), fontsize=11, color=COL["green"])
    ax.text(0, -1.15, r"$\kappa_{\mathrm{FCC}}=1/\sqrt{2}$;\quad $R_{\mathrm{in}}^{\mathrm{Voronoi}}=\kappa\, R_{\mathrm{in}}^{\mathrm{hull}}$", ha="center", fontsize=11)
    ax.set_xlim(-1.25, 1.55)
    ax.set_ylim(-1.35, 1.15)
    _save(fig, "carrier-hull-voronoi.pdf")


def fig_voronoi_cell() -> None:
    """Rhombic dodecahedron = Voronoi cell of FCC."""
    pts = _fcc_lattice_points(radius=2, a=1.0)
    vor = Voronoi(pts)
    origin_idx = np.argmin(np.linalg.norm(pts, axis=1))
    region = vor.regions[vor.point_region[origin_idx]]
    region = [i for i in region if i >= 0]
    cell_verts = vor.vertices[region]

    edges = set()
    for ridge, verts_idx in zip(vor.ridge_vertices, vor.ridge_points):
        if origin_idx in verts_idx:
            rv = [v for v in ridge if v >= 0]
            if len(rv) == 2 and rv[0] in region and rv[1] in region:
                edges.add(tuple(sorted(rv)))

    fig = plt.figure(figsize=(5.6, 5.0))
    ax: Axes3D = fig.add_subplot(111, projection="3d")
    for i, j in edges:
        ax.plot(
            [cell_verts[i, 0], cell_verts[j, 0]],
            [cell_verts[i, 1], cell_verts[j, 1]],
            [cell_verts[i, 2], cell_verts[j, 2]],
            color=COL["blue"],
            lw=1.2,
        )
    ax.scatter(cell_verts[:, 0], cell_verts[:, 1], cell_verts[:, 2], c=COL["red"], s=20)
    ax.scatter([0], [0], [0], c=COL["green"], s=45)
    _style_3d(ax, 0.65, elev=25, azim=-50)
    ax.set_title(r"Ячейка Вороного FCC (ромбододекаэдр), $v_{\mathrm{hV}}=a^3/\sqrt{2}$", fontsize=10, pad=8)
    _save(fig, "carrier-voronoi-cell.pdf")


def fig_fcc_111_slice() -> None:
    """FCC lattice with {111} plane and hexagonal slice."""
    pts = _fcc_lattice_points(radius=2, a=1.0)
    fig = plt.figure(figsize=(6.2, 5.2))
    ax: Axes3D = fig.add_subplot(111, projection="3d")
    ax.scatter(pts[:, 0], pts[:, 1], pts[:, 2], c=COL["light"], s=18, depthshade=True, alpha=0.7)

    # plane x+y+z = const through origin neighbors
    d = 0.0
    xx, yy = np.meshgrid(np.linspace(-1, 1, 10), np.linspace(-1, 1, 10))
    zz = d - xx - yy
    ax.plot_surface(xx, yy, zz, alpha=0.18, color=COL["green"], linewidth=0)

    on_plane = pts[np.abs(pts.sum(axis=1) - d) < 0.08]
    ax.scatter(on_plane[:, 0], on_plane[:, 1], on_plane[:, 2], c=COL["red"], s=55, depthshade=True)

    _style_3d(ax, 1.1, elev=20, azim=-58)
    ax.set_title(r"Срез $\{111\}$: гексагональный слой $(2{+}1)$", fontsize=10, pad=8)
    _save(fig, "carrier-fcc-111-slice.pdf")


def fig_two_speeds() -> None:
    """Microscopic c0 vs macroscopic c = kappa c0."""
    fig, axes = plt.subplots(1, 2, figsize=(8.4, 3.2))

    ax = axes[0]
    ax.set_aspect("equal")
    ax.axis("off")
    path = [(0, 0), (1, 0), (1, 1), (2, 1), (3, 1)]
    xs, ys = zip(*path)
    ax.plot(xs, ys, "o-", color=COL["blue"], lw=1.4, ms=6)
    ax.annotate("", xy=(1, 0), xytext=(0, 0), arrowprops=dict(arrowstyle="<->", color=COL["gray"], lw=1.0))
    ax.text(0.5, -0.18, r"$h_L$", ha="center", fontsize=10)
    ax.annotate("", xy=(1, 1), xytext=(1, 0), arrowprops=dict(arrowstyle="<->", color=COL["gray"], lw=1.0))
    ax.text(1.18, 0.5, r"$h_L$", fontsize=10)
    ax.text(1.5, -0.55, r"тактовая $c_0=h_L/h_T$", ha="center", fontsize=10)
    ax.set_xlim(-0.3, 3.3)
    ax.set_ylim(-0.7, 1.5)
    ax.set_title("микро: зигзаг по рёбрам", fontsize=10)

    ax = axes[1]
    ax.set_aspect("equal")
    ax.axis("off")
    k = 1 / math.sqrt(2)
    ax.plot([0, 3], [0, 3 * k], color=COL["red"], lw=2.0)
    ax.plot([0, 3], [0, 3], color=COL["blue"], lw=1.0, ls="--", alpha=0.5)
    ax.text(2.2, 2.35, r"$c=\kappa c_0$", color=COL["red"], fontsize=11)
    ax.text(2.4, 2.75, r"$c_0$", color=COL["blue"], fontsize=10)
    ax.text(1.5, -0.35, r"$\kappa=1/\sqrt{2}$ на FCC", ha="center", fontsize=10)
    ax.set_xlim(-0.2, 3.3)
    ax.set_ylim(-0.5, 3.3)
    ax.set_title("макро: осреднённый фронт", fontsize=10)

    fig.suptitle(r"Две скорости: $c_0$ на решётке, $c=\kappa c_0$ на $T$", fontsize=11, y=1.02)
    _save(fig, "carrier-two-speeds.pdf")


def fig_slice_bridge() -> None:
    """(3+1) FCC vs (2+1) hex slice with different kappa."""
    fig, axes = plt.subplots(1, 2, figsize=(8.6, 3.6))

    ax = axes[0]
    ax.set_aspect("equal")
    ax.axis("off")
    for k in range(6):
        ang = k * np.pi / 3 + np.pi / 6
        p = np.array([np.cos(ang), np.sin(ang)])
        ax.plot([0, p[0]], [0, p[1]], color=COL["blue"], lw=1.2)
    ax.plot(0, 0, "o", color=COL["red"], ms=8)
    ax.text(0, -1.35, r"$(2{+}1)$: $\kappa_{\mathrm{hex}}=\sqrt{3}/2$, $|N|=6$", ha="center", fontsize=10)
    ax.set_xlim(-1.3, 1.3)
    ax.set_ylim(-1.55, 1.2)
    ax.set_title("гексагональный срез", fontsize=10)

    ax = axes[1]
    ax.axis("off")
    ax.text(0.5, 0.55, r"$(3{+}1)$ FCC", ha="center", fontsize=12, transform=ax.transAxes)
    ax.text(0.5, 0.38, r"$\kappa_{\mathrm{FCC}}=1/\sqrt{2}$, $|N|=12$", ha="center", fontsize=10, transform=ax.transAxes)
    ax.text(0.5, 0.22, r"$c=\kappa c_0$ — одно $c$, разное разбиение", ha="center", fontsize=10, transform=ax.transAxes, color=COL["blue"])
    ax.text(0.5, 0.06, r"срез $\{111\}$ вложен в объём", ha="center", fontsize=10, transform=ax.transAxes, color=COL["green"])

    fig.suptitle(r"Связь среза $(2{+}1)$ и носителя $(3{+}1)$", fontsize=11, y=1.02)
    _save(fig, "carrier-slice-bridge.pdf")


def fig_field_neighbors() -> None:
    """Spinor z on central node, coupling to neighbors."""
    a = 1.0
    angles = np.linspace(0, 2 * np.pi, 7)[:-1]

    fig, ax = plt.subplots(figsize=(5.6, 4.8))
    ax.set_aspect("equal")
    ax.axis("off")

    ax.plot(0, 0, "o", color=COL["red"], ms=10, zorder=5)
    for t in angles:
        p = a * np.array([np.cos(t), np.sin(t)])
        ax.plot([0, p[0]], [0, p[1]], color=COL["light"], lw=1.0, zorder=1)
        ax.plot(p[0], p[1], "o", color=COL["node"], ms=5, zorder=3)

    # Argand-style inset for z in C^2
    circ = plt.Circle((0, 0), 0.35, fill=False, ec=COL["blue"], lw=1.0)
    ax.add_patch(circ)
    ax.annotate("", xy=(0.28, 0.18), xytext=(0, 0), arrowprops=dict(arrowstyle="-|>", color=COL["blue"], lw=1.3))
    ax.text(0.0, 0.48, r"$z_1$", ha="center", fontsize=10, color=COL["blue"])
    ax.annotate("", xy=(-0.22, -0.28), xytext=(0, 0), arrowprops=dict(arrowstyle="-|>", color=COL["green"], lw=1.3))
    ax.text(-0.38, -0.42, r"$z_2$", fontsize=10, color=COL["green"])
    ax.text(0.02, -1.35, r"состояние узла $z(x)\in\mathbb{C}^2$; локальный закон на $N(x)$", ha="center", fontsize=10)
    ax.set_xlim(-1.45, 1.45)
    ax.set_ylim(-1.55, 1.35)
    _save(fig, "carrier-field-z.pdf")


def main() -> None:
    fig_lattice_field()
    fig_epsilon_neighborhood()
    fig_plane_tilings()
    fig_light_cone()
    fig_hex_kgeom()
    fig_packing_compare()
    fig_fcc_shell()
    fig_cubocta_faces()
    fig_hull_voronoi()
    fig_voronoi_cell()
    fig_fcc_111_slice()
    fig_two_speeds()
    fig_slice_bridge()
    fig_field_neighbors()


if __name__ == "__main__":
    main()
