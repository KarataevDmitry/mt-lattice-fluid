#!/usr/bin/env python3
"""Render carrier-geometry figures for book/sources/chapters/01-carrier.tex."""

from __future__ import annotations

import math
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Polygon, Wedge
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from mpl_toolkits.mplot3d.axes3d import Axes3D
from scipy.spatial import ConvexHull, Voronoi

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


def _sphere_mesh(center: np.ndarray, radius: float, n: int = 14) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    u = np.linspace(0, 2 * np.pi, n)
    v = np.linspace(0, np.pi, max(6, n // 2))
    u, v = np.meshgrid(u, v)
    x = center[0] + radius * np.cos(u) * np.sin(v)
    y = center[1] + radius * np.sin(u) * np.sin(v)
    z = center[2] + radius * np.cos(v)
    return x, y, z


def _add_sphere(ax: Axes3D, center: np.ndarray, radius: float, color: str, alpha: float = 0.9, n: int = 14) -> None:
    x, y, z = _sphere_mesh(center, radius, n=n)
    ax.plot_surface(x, y, z, color=color, alpha=alpha, linewidth=0, antialiased=True, shade=True)


def _simple_cubic_centers(n: int, a: float = 1.0) -> np.ndarray:
    return np.array([(i * a, j * a, k * a) for i in range(-n, n + 1) for j in range(-n, n + 1) for k in range(-n, n + 1)])


def _bcc_centers(n: int, a: float = 1.0) -> np.ndarray:
    pts: set[tuple[float, float, float]] = set()
    for i in range(-n, n + 1):
        for j in range(-n, n + 1):
            for k in range(-n, n + 1):
                pts.add((i * a, j * a, k * a))
                pts.add((i * a + a / 2, j * a + a / 2, k * a + a / 2))
    return np.array(sorted(pts))


def _draw_sphere_packing(
    ax: Axes3D,
    centers: np.ndarray,
    radius: float,
    *,
    base_color: str = "#9bb8d3",
    center_idx: int | None = None,
    neighbor_idx: set[int] | None = None,
) -> None:
    mesh_n = 8 if len(centers) > 24 else 12
    for i, c in enumerate(centers):
        if center_idx is not None and i == center_idx:
            col, alpha = COL["red"], 0.95
        elif neighbor_idx and i in neighbor_idx:
            col, alpha = "#e8a598", 0.88
        else:
            col, alpha = base_color, 0.82
        _add_sphere(ax, c, radius, col, alpha=alpha, n=mesh_n)


def _cuboctahedron_face_groups(verts: np.ndarray, a: float) -> tuple[list[np.ndarray], list[np.ndarray]]:
    s = a / math.sqrt(2)
    squares: list[np.ndarray] = []
    for axis in range(3):
        for sign in (-1, 1):
            level = sign * s
            on = [v for v in verts if abs(v[axis] - level) < 1e-6]
            if len(on) == 4:
                squares.append(np.array(on))
    tri_list = [
        [(s, s, 0), (s, 0, s), (0, s, s)],
        [(s, s, 0), (s, 0, -s), (0, s, -s)],
        [(s, -s, 0), (s, 0, s), (0, -s, s)],
        [(s, -s, 0), (s, 0, -s), (0, -s, -s)],
        [(-s, s, 0), (-s, 0, s), (0, s, s)],
        [(-s, s, 0), (-s, 0, -s), (0, s, -s)],
        [(-s, -s, 0), (-s, 0, s), (0, -s, s)],
        [(-s, -s, 0), (-s, 0, -s), (0, -s, -s)],
    ]
    triangles = [np.array(t) for t in tri_list]
    return squares, triangles


def _add_poly_faces(ax: Axes3D, faces: list[np.ndarray], color: str, alpha: float, edge: str = COL["blue"]) -> None:
    polys = Poly3DCollection(faces, facecolors=color, edgecolors=edge, linewidths=0.6, alpha=alpha)
    ax.add_collection3d(polys)


def _voronoi_cell_mesh(vor: Voronoi, point_idx: int) -> tuple[np.ndarray, np.ndarray] | tuple[None, None]:
    region = [v for v in vor.regions[vor.point_region[point_idx]] if v >= 0]
    if len(region) < 4:
        return None, None
    verts = vor.vertices[region]
    try:
        hull = ConvexHull(verts)
    except Exception:
        return None, None
    return verts, hull.simplices


def _draw_voronoi_tessellation(ax: Axes3D, lattice_radius: int, a: float, origin_only_neighbors: bool = True) -> None:
    pts = _fcc_lattice_points(lattice_radius, a)
    vor = Voronoi(pts)
    origin_idx = int(np.argmin(np.linalg.norm(pts, axis=1)))
    for i, p in enumerate(pts):
        if origin_only_neighbors and np.linalg.norm(p) > 1.8 * a:
            continue
        mesh = _voronoi_cell_mesh(vor, i)
        if mesh[0] is None:
            continue
        verts, simplices = mesh
        tris = verts[simplices]
        if i == origin_idx:
            col, alpha, lw = "#fff4e8", 0.55, 0.9
        else:
            col, alpha, lw = "#eef4fb", 0.18, 0.4
        polys = Poly3DCollection(tris, facecolors=col, edgecolors=COL["blue"], linewidths=lw, alpha=alpha)
        ax.add_collection3d(polys)


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


def _draw_spacetime_2d(
    ax,
    c0: float,
    *,
    t_lim: float = 1.25,
    x_lim: float = 1.65,
    show_past: bool = True,
    cone_col: str = "#4fa9b8",
) -> None:
    """Classical $(x,t)$ diagram: observer at $(0,0)$, future up, past down."""
    ax.set_aspect("equal")
    ax.axhline(0, color="#bbbbbb", lw=0.8, zorder=0)
    ax.axvline(0, color="#bbbbbb", lw=0.8, zorder=0)

    t_f = np.linspace(0, t_lim, 80)
    ax.fill_between(c0 * t_f, 0, t_f, color=cone_col, alpha=0.12, zorder=0)
    ax.fill_between(-c0 * t_f, 0, t_f, color=cone_col, alpha=0.12, zorder=0)
    ax.plot(c0 * t_f, t_f, color=cone_col, lw=1.5, zorder=1)
    ax.plot(-c0 * t_f, t_f, color=cone_col, lw=1.5, zorder=1)

    if show_past:
        t_p = np.linspace(-t_lim, 0, 80)
        ax.fill_between(c0 * t_p, t_p, 0, color=cone_col, alpha=0.08, zorder=0)
        ax.fill_between(-c0 * t_p, t_p, 0, color=cone_col, alpha=0.08, zorder=0)
        ax.plot(c0 * t_p, t_p, color=cone_col, lw=1.5, zorder=1)
        ax.plot(-c0 * t_p, t_p, color=cone_col, lw=1.5, zorder=1)
        ax.text(-0.08, -t_lim * 0.72, "прошлое", fontsize=9, ha="center", color="#2c6e7a")

    ax.scatter([0], [0], color=COL["red"], s=55, zorder=5)
    ax.text(0.06, -0.06, "наблюдатель", fontsize=9, color=COL["red"])
    ax.text(-0.1, t_lim * 0.78, "будущее", fontsize=9, ha="center", color="#2c6e7a")
    ax.text(x_lim * 0.82, 0.03, r"$t=0$", fontsize=9, color="#2d6a3e")
    ax.set_xlabel(r"пространство $x$")
    ax.set_ylabel(r"время $t$")
    ax.set_xlim(-x_lim, x_lim)
    ax.set_ylim(-t_lim if show_past else -0.08, t_lim)


def _light_cone_surface(c0: float, t_max: float, n: int = 40) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    theta = np.linspace(0, 2 * np.pi, n)
    t = np.linspace(0, t_max, n // 2)
    th, tt = np.meshgrid(theta, t)
    r = c0 * tt
    x = r * np.cos(th)
    y = r * np.sin(th)
    return x, y, tt, th


def fig_light_cone() -> None:
    """2D classical $(x,t)$ slice + 3D light cones."""
    a = 1.0
    ht = 1.0
    c0 = a / ht
    cone_col = "#4fa9b8"
    r2 = a * math.sqrt(2)

    fig = plt.figure(figsize=(10.8, 4.9))

    ax2d = fig.add_subplot(1, 2, 1)
    _draw_spacetime_2d(ax2d, c0, t_lim=1.2, x_lim=1.75)
    ax2d.scatter([a], [ht], color=COL["blue"], s=48, zorder=6)
    ax2d.plot([0, a], [0, ht], color=COL["blue"], lw=1.2, zorder=4)
    ax2d.text(a + 0.05, ht * 0.45, r"$h_L$", fontsize=9, color=COL["blue"])
    ax2d.scatter([r2], [ht], color=COL["red"], marker="x", s=70, linewidths=2, zorder=6)
    ax2d.plot([0, r2], [0, ht], color=COL["red"], lw=1.0, ls="--", zorder=4)
    ax2d.text(r2 + 0.04, ht + 0.04, r"$h_L\sqrt{2}$", fontsize=9, color=COL["red"])
    ax2d.set_title(r"срез $(x,t)$: $c_0 h_T=h_L$", fontsize=10)

    ax3d: Axes3D = fig.add_subplot(1, 2, 2, projection="3d")
    xf, yf, tf, _ = _light_cone_surface(c0, 1.15)
    ax3d.plot_surface(xf, yf, tf, color=cone_col, alpha=0.38, linewidth=0, shade=True)
    ax3d.plot_surface(xf, yf, -tf, color=cone_col, alpha=0.38, linewidth=0, shade=True)
    lim = 1.15
    xx, yy = np.meshgrid(np.linspace(-lim, lim, 10), np.linspace(-lim, lim, 10))
    ax3d.plot_surface(xx, yy, np.zeros_like(xx), color="#8fd4a6", alpha=0.22, linewidth=0, shade=False)
    ax3d.scatter([0], [0], [0], color=COL["red"], s=45, depthshade=True)
    ax3d.scatter([a], [0], [ht], color=COL["blue"], s=40, depthshade=True)
    ax3d.scatter([r2], [0], [ht], color=COL["red"], marker="x", s=60, linewidths=2)
    _style_3d(ax3d, 1.35, elev=22, azim=-52)
    ax3d.set_title(r"объём $(x,y,t)$", fontsize=10, pad=8)

    fig.suptitle("Световой конус: наблюдатель в $(0,0)$, будущее вверх", fontsize=11, y=1.02)
    _save(fig, "carrier-light-cone.pdf")


def fig_hex_kgeom() -> None:
    a = 1.0
    r_in = a * math.sqrt(3) / 2
    angles = np.linspace(0, 2 * np.pi, 7)[:-1] + np.pi / 6
    verts = np.column_stack([a * np.cos(angles), a * np.sin(angles)])

    fig, ax = plt.subplots(figsize=(7.2, 5.0))
    ax.set_aspect("equal")
    ax.axis("off")

    # описанная и вписанная окружности — разница радиусов видна сразу
    ax.add_patch(plt.Circle((0, 0), a, fill=False, ec=COL["red"], lw=2.2, zorder=1))
    ax.add_patch(plt.Circle((0, 0), r_in, fill=False, ec=COL["green"], lw=2.2, ls="--", zorder=1))

    hex_patch = Polygon(verts, closed=True, facecolor="#eef4fb", edgecolor=COL["blue"], lw=2.0, zorder=2)
    ax.add_patch(hex_patch)

    ax.plot(0, 0, "o", color=COL["red"], ms=8, zorder=6)
    ax.plot([0, 0], [0, a], color=COL["red"], lw=2.0, zorder=5)
    ax.plot([0, r_in], [0, 0], color=COL["green"], lw=2.0, zorder=5)
    ax.plot([r_in, r_in], [-0.04, 0.04], color=COL["green"], lw=1.2, zorder=5)

    ax.text(0.07, a * 0.52, r"$R_{\mathrm{out}}=a$", color=COL["red"], fontsize=13)
    ax.text(r_in * 0.45, -0.14, r"$R_{\mathrm{in}}=\frac{\sqrt{3}}{2}a$", color=COL["green"], fontsize=12)

    e0, e1 = verts[0], verts[1]
    emid = 0.5 * (e0 + e1)
    ax.annotate(
        "",
        xy=emid + np.array([0.12, 0.08]),
        xytext=emid - np.array([0.12, 0.08]),
        arrowprops=dict(arrowstyle="<->", color=COL["node"], lw=1.2),
    )
    ax.text(emid[0] + 0.18, emid[1] + 0.12, r"$a$", fontsize=12, color=COL["node"])

    # шкала сравнения длин (тот же масштаб, крупнее)
    bx, by = 1.55, -0.55
    ax.plot([bx, bx + a], [by, by], color=COL["red"], lw=3.0, solid_capstyle="round")
    ax.plot([bx, bx + r_in], [by - 0.22, by - 0.22], color=COL["green"], lw=3.0, solid_capstyle="round")
    ax.plot([bx, bx], [by - 0.06, by + 0.06], color=COL["node"], lw=0.8)
    ax.plot([bx + a, bx + a], [by - 0.06, by + 0.06], color=COL["red"], lw=0.8)
    ax.plot([bx + r_in, bx + r_in], [by - 0.28, by - 0.16], color=COL["green"], lw=0.8)
    ax.text(bx + a * 0.5, by + 0.1, r"$R_{\mathrm{out}}$", color=COL["red"], fontsize=10, ha="center")
    ax.text(bx + r_in * 0.5, by - 0.34, r"$R_{\mathrm{in}}$", color=COL["green"], fontsize=10, ha="center")

    ax.text(-0.05, -1.42, r"$\kappa_{\mathrm{hex}}=R_{\mathrm{in}}/R_{\mathrm{out}}=\sqrt{3}/2$", fontsize=12, ha="center")
    ax.text(0, 1.38, r"гексагональная ячейка Вороного, $|N|=6$", ha="center", fontsize=11)
    ax.set_xlim(-1.35, 2.65)
    ax.set_ylim(-1.55, 1.55)
    _save(fig, "carrier-hex-kgeom.pdf")


def fig_packing_compare() -> None:
    """SC / BCC / FCC — real 3D sphere packings."""
    fig = plt.figure(figsize=(9.6, 3.4))
    specs = [
        ("SC", 6, _simple_cubic_centers(1, 1.0), 0.5),
        ("BCC", 8, _bcc_centers(1, 1.0), math.sqrt(3) / 4),
        ("FCC", 12, _fcc_lattice_points(1, 1.0), 0.5),
    ]
    for k, (name, n, centers, radius) in enumerate(specs):
        ax: Axes3D = fig.add_subplot(1, 3, k + 1, projection="3d")
        center_idx = int(np.argmin(np.linalg.norm(centers, axis=1)))
        _draw_sphere_packing(ax, centers, radius, center_idx=center_idx)
        lim = max(1.2, float(np.max(np.abs(centers)) + radius + 0.15))
        _style_3d(ax, lim, elev=24, azim=-58)
        ax.set_title(f"{name}, $|N|={n}$", fontsize=10, pad=6)
    fig.suptitle("Три кубические упаковки равных сфер", fontsize=11, y=1.02)
    _save(fig, "carrier-packing.pdf")


def fig_fcc_shell() -> None:
    """FCC closest packing — touching spheres."""
    a = 1.0
    centers = _fcc_lattice_points(1, a)
    radius = a / 2
    center_idx = int(np.argmin(np.linalg.norm(centers, axis=1)))
    center = centers[center_idx]
    dists = np.linalg.norm(centers - center, axis=1)
    neighbors = set(int(i) for i in np.where(np.isclose(dists, a, atol=1e-5))[0])

    fig = plt.figure(figsize=(6.0, 5.4))
    ax: Axes3D = fig.add_subplot(111, projection="3d")
    _draw_sphere_packing(ax, centers, radius, center_idx=center_idx, neighbor_idx=neighbors)
    _style_3d(ax, 1.05, elev=22, azim=-52)
    ax.set_title(r"FCC: плотнейшая упаковка, $|N|=12$, $a=h_L$", fontsize=10, pad=8)
    _save(fig, "carrier-fcc-shell.pdf")


def fig_cubocta_faces() -> None:
    """Solid cuboctahedron with square and triangular faces."""
    a = 1.0
    verts = _fcc_vertices(a)
    squares, triangles = _cuboctahedron_face_groups(verts, a)

    fig = plt.figure(figsize=(6.2, 5.2))
    ax: Axes3D = fig.add_subplot(111, projection="3d")
    _add_poly_faces(ax, squares, "#f5b7b1", alpha=0.75, edge=COL["red"])
    _add_poly_faces(ax, triangles, "#b8e0c2", alpha=0.55, edge=COL["green"])
    _wire_3d(ax, verts, _cubocta_edges(verts, a), color=COL["blue"], lw=0.8, alpha=0.5)
    _style_3d(ax, 0.95, elev=18, azim=-42)
    ax.text2D(0.04, 0.93, r"квадрат: $R_{\mathrm{in}}^{\mathrm{hull}}=a/\sqrt{2}$", transform=ax.transAxes, color=COL["red"], fontsize=10)
    ax.text2D(0.04, 0.87, r"треугольник: $a\sqrt{2/3}$", transform=ax.transAxes, color=COL["green"], fontsize=10)
    ax.set_title("Кубооктаэдр — выпуклая оболочка 12 соседей", fontsize=10, pad=8)
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
    """3D Voronoi tessellation of FCC — space partitioned into rhombic dodecahedra."""
    a = 1.0
    fig = plt.figure(figsize=(6.4, 5.4))
    ax: Axes3D = fig.add_subplot(111, projection="3d")
    _draw_voronoi_tessellation(ax, lattice_radius=2, a=a, origin_only_neighbors=True)
    _style_3d(ax, 1.15, elev=24, azim=-50)
    ax.set_title(r"Замощение $\mathbb{R}^3$ ячейками Вороного FCC", fontsize=10, pad=8)
    _save(fig, "carrier-voronoi-cell.pdf")


def fig_fcc_111_slice() -> None:
    """FCC sphere packing cut by {111} plane — real 3D slice."""
    a = 1.0
    radius = a / 2
    centers = _fcc_lattice_points(1, a)
    fig = plt.figure(figsize=(6.4, 5.4))
    ax: Axes3D = fig.add_subplot(111, projection="3d")

    on_slice = np.abs(centers.sum(axis=1)) < 0.12
    for i, c in enumerate(centers):
        if on_slice[i]:
            _add_sphere(ax, c, radius, "#e8a598", alpha=0.95, n=12)
        else:
            _add_sphere(ax, c, radius, "#9bb8d3", alpha=0.55, n=10)

    lim = 1.05
    xx, yy = np.meshgrid(np.linspace(-lim, lim, 12), np.linspace(-lim, lim, 12))
    zz = -xx - yy
    ax.plot_surface(xx, yy, zz, alpha=0.22, color=COL["green"], linewidth=0, shade=False)

    _style_3d(ax, 1.05, elev=20, azim=-58)
    ax.set_title(r"Срез $\{111\}$ через FCC-упаковку", fontsize=10, pad=8)
    _save(fig, "carrier-fcc-111-slice.pdf")


def fig_two_speeds() -> None:
    """Two speeds in classical $(x,t)$ diagrams, observer at origin."""
    a = 1.0
    ht = 1.0
    c0 = a / ht
    kappa = 1 / math.sqrt(2)
    c_macro = kappa * c0

    fig, axes = plt.subplots(1, 2, figsize=(9.2, 4.2))

    ax = axes[0]
    _draw_spacetime_2d(ax, c0, t_lim=1.35, x_lim=1.55, show_past=False)
    ticks = [(i * a, i * ht) for i in range(4)]
    xs, ts = zip(*ticks)
    ax.plot(xs, ts, "o-", color=COL["blue"], lw=1.5, ms=5, zorder=6)
    ax.text(1.15, -0.12, r"тактовая $c_0$: один такт $h_T$, шаг $h_L$", ha="center", fontsize=9)
    ax.set_title("микро: дискретный шаг по решётке", fontsize=10)

    ax = axes[1]
    _draw_spacetime_2d(ax, c0, t_lim=1.35, x_lim=1.55, show_past=False)
    x_end = 1.4
    ax.plot([0, x_end], [0, x_end / c0], color=COL["blue"], lw=1.6, ls="--", zorder=4)
    ax.plot([0, x_end], [0, x_end / c_macro], color=COL["red"], lw=2.0, zorder=5)
    ax.text(x_end * 0.55, x_end / c0 + 0.06, r"$c_0$", color=COL["blue"], fontsize=10)
    ax.text(x_end * 0.62, x_end / c_macro - 0.1, r"$c=\kappa c_0$", color=COL["red"], fontsize=10)
    ax.text(0.75, -0.1, r"$\kappa=1/\sqrt{2}$", ha="center", fontsize=9)
    ax.set_title("макро: осреднённый фронт", fontsize=10)

    fig.suptitle(r"Две скорости в плоскости $(x,t)$, наблюдатель в $(0,0)$", fontsize=11, y=1.02)
    _save(fig, "carrier-two-speeds.pdf")


def fig_slice_bridge() -> None:
    """(3+1) FCC packing vs (2+1) hex slice."""
    fig = plt.figure(figsize=(9.0, 3.8))

    ax2d = fig.add_subplot(1, 2, 1)
    ax2d.set_aspect("equal")
    ax2d.axis("off")
    s = 0.42
    _draw_hex_tiling(ax2d, s=s, rings=3, highlight=(0, 0))
    ax2d.plot(0, 0, "o", color=COL["red"], ms=5, zorder=6)
    ax2d.set_xlim(-2.2, 2.2)
    ax2d.set_ylim(-2.2, 2.2)
    ax2d.set_title(r"$(2{+}1)$: $\kappa_{\mathrm{hex}}=\sqrt{3}/2$", fontsize=10)

    ax3d: Axes3D = fig.add_subplot(1, 2, 2, projection="3d")
    a = 1.0
    centers = _fcc_lattice_points(1, a)
    _draw_sphere_packing(ax3d, centers, a / 2)
    lim = 1.05
    xx, yy = np.meshgrid(np.linspace(-lim, lim, 8), np.linspace(-lim, lim, 8))
    ax3d.plot_surface(xx, yy, -xx - yy, alpha=0.2, color=COL["green"], linewidth=0, shade=False)
    _style_3d(ax3d, 1.05, elev=22, azim=-52)
    ax3d.set_title(r"$(3{+}1)$ FCC, срез $\{111\}$", fontsize=10, pad=6)

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
