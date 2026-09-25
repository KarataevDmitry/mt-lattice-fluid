#!/usr/bin/env python3
"""Render carrier-geometry figures for book/sources/chapters/01-carrier.tex.

Drafting primitives: figure_draft (dimension lines, leaders — labels off geometry)."""

from __future__ import annotations

import math
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Polygon, Wedge
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from mpl_toolkits.mplot3d.axes3d import Axes3D
from scipy.spatial import ConvexHull, Voronoi

from figure_draft import dim_axis_h, dim_axis_v, dim_linear, dim_radius, leader

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "book" / "sources" / "figures"

INK = "#222222"
MUTED = "#666666"
LIGHT = "#aaaaaa"
FILL = "#f0f0f0"
FILL_ALT = "#e4e4e4"
HI = "#d8d8d8"

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
    fig.savefig(path, bbox_inches="tight", pad_inches=0.10)
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


def _style_3d(ax: Axes3D, lim: float, elev: float = 22, azim: float = -58, pad: float = 0.0) -> None:
    lim = lim + pad
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


def _first_shell(centers: np.ndarray) -> tuple[np.ndarray, int, set[int]]:
    center_idx = int(np.argmin(np.linalg.norm(centers, axis=1)))
    c = centers[center_idx]
    dists = np.linalg.norm(centers - c, axis=1)
    nn = float(np.min(dists[dists > 1e-9]))
    keep = np.where(dists <= nn * 1.02)[0]
    idx_map = {int(old): new for new, old in enumerate(keep)}
    neighbors = {idx_map[int(i)] for i in keep if int(i) != center_idx}
    return centers[keep], idx_map[center_idx], neighbors


def _draw_sphere_packing(
    ax: Axes3D,
    centers: np.ndarray,
    radius: float,
    *,
    center_idx: int | None = None,
    neighbor_idx: set[int] | None = None,
    first_shell_only: bool = True,
) -> None:
    if first_shell_only:
        centers, center_idx, neighbor_idx = _first_shell(centers)
    for i, c in enumerate(centers):
        if center_idx is not None and i == center_idx:
            col, alpha = INK, 0.95
        elif neighbor_idx and i in neighbor_idx:
            col, alpha = MUTED, 0.88
        else:
            col, alpha = LIGHT, 0.55
        _add_sphere(ax, c, radius, col, alpha=alpha, n=14)


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
    return squares, [np.array(t) for t in tri_list]


def _add_poly_faces(ax: Axes3D, faces: list[np.ndarray], color: str, alpha: float, edge: str = INK, ls: str = "-") -> None:
    polys = Poly3DCollection(faces, facecolors=color, edgecolors=edge, linewidths=0.7, alpha=alpha, linestyles=ls)
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
            col, alpha, lw = HI, 0.65, 0.9
        else:
            col, alpha, lw = FILL, 0.22, 0.45
        polys = Poly3DCollection(tris, facecolors=col, edgecolors=MUTED, linewidths=lw, alpha=alpha)
        ax.add_collection3d(polys)


def _draw_triangle_tiling(ax, a: float, rows: int, cols: int, highlight_idx: tuple[int, int, int] | None = None) -> None:
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
                        facecolor=HI if hi else (FILL if t_idx == 0 else FILL_ALT),
                        edgecolor=INK if hi else MUTED,
                        lw=1.5 if hi else 0.7,
                        zorder=2 if hi else 1,
                    )
                )


def _draw_square_tiling(ax, a: float, n: int, highlight: tuple[int, int] | None = None) -> None:
    for i in range(-n, n):
        for j in range(-n, n):
            x, y = i * a, j * a
            hi = highlight == (i, j)
            ax.add_patch(
                Polygon(
                    [(x, y), (x + a, y), (x + a, y + a), (x, y + a)],
                    closed=True,
                    facecolor=HI if hi else FILL,
                    edgecolor=INK if hi else MUTED,
                    lw=1.5 if hi else 0.7,
                    zorder=2 if hi else 1,
                )
            )


def _draw_hex_tiling(ax, s: float, rings: int, highlight: tuple[int, int] | None = None) -> None:
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
                    facecolor=HI if hi else FILL,
                    edgecolor=INK if hi else MUTED,
                    lw=1.5 if hi else 0.7,
                    zorder=2 if hi else 1,
                )
            )


def fig_lattice_field() -> None:
    a = 1.0
    rows, cols = 4, 5
    pts = [(c * a * 1.05, r * a * 0.92) for r in range(rows) for c in range(cols)]

    fig, ax = plt.subplots(figsize=(6.0, 3.8))
    ax.set_aspect("equal")
    ax.axis("off")

    cx, cy = 2 * a * 1.05, 1 * a * 0.92
    for x, y in pts:
        focus = abs(x - cx) < 0.01 and abs(y - cy) < 0.01
        ax.plot(x, y, "o", color=INK, ms=9 if focus else 5, zorder=3)
        for dx, dy in ((a * 1.05, 0), (-a * 1.05, 0), (0, a * 0.92)):
            nx, ny = x + dx, y + dy
            if any(abs(nx - px) < 0.01 and abs(ny - py) < 0.01 for px, py in pts):
                ax.plot([x, nx], [y, ny], color=LIGHT, lw=0.9, zorder=1)

    leader(ax, (cx, cy), r"$z(x)\in\mathbb{C}^2$", (cx + 0.55, cy + 0.55), fontsize=12)
    ax.text(0.02, -0.35, r"$\Lambda$ — счётное множество узлов; шаг $h_L$, такт $h_T$, $c_0=h_L/h_T$", fontsize=10)
    ax.set_xlim(-0.4, 4.8)
    ax.set_ylim(-0.6, 3.2)
    _save(fig, "carrier-lattice-field.pdf")


def fig_epsilon_neighborhood() -> None:
    a = 1.0
    angles = np.linspace(0, 2 * np.pi, 7)[:-1] + np.pi / 6

    fig, ax = plt.subplots(figsize=(5.4, 4.6))
    ax.set_aspect("equal")
    ax.axis("off")

    ax.plot(0, 0, "o", color=INK, ms=9, zorder=5)
    for th in angles:
        p = a * np.array([np.cos(th), np.sin(th)])
        ax.plot([0, p[0]], [0, p[1]], color=LIGHT, lw=1.0, ls=":", zorder=2)
        ax.plot(p[0], p[1], "o", color=MUTED, ms=7, zorder=4)

    p0 = a * np.array([np.cos(angles[0]), np.sin(angles[0])])
    ax.plot([0, p0[0]], [0, p0[1]], color=INK, lw=1.5, zorder=3)
    dim_radius(ax, a, math.degrees(angles[0]), r"$h_L$", label_gap=0.16)

    wedge = Wedge((0, 0), a * 1.05, 0, 360, width=0.08, facecolor=FILL, edgecolor=LIGHT, lw=0.8, zorder=1)
    ax.add_patch(wedge)
    ax.text(0, -1.35, r"$N(x)$: узлы на расстоянии $h_L$ за один такт $h_T$", ha="center", fontsize=11)
    leader(ax, (0.0, a * 1.08), r"$c_0h_T=h_L$", (0.55, a * 1.22), color=MUTED)
    ax.set_xlim(-1.4, 1.4)
    ax.set_ylim(-1.55, 1.45)
    _save(fig, "carrier-epsilon.pdf")


def fig_plane_tilings() -> None:
    fig, axes = plt.subplots(1, 3, figsize=(9.6, 3.2))

    ax = axes[0]
    ax.set_aspect("equal")
    ax.axis("off")
    a = 0.55
    _draw_triangle_tiling(ax, a=a, rows=5, cols=5, highlight_idx=(0, 0, 0))
    ax.set_xlim(-2.6, 2.6)
    ax.set_ylim(-2.0, 2.0)
    ax.set_title(r"треугольники", fontsize=10)

    ax = axes[1]
    ax.set_aspect("equal")
    ax.axis("off")
    a = 0.65
    _draw_square_tiling(ax, a=a, n=4, highlight=(0, 0))
    dim_linear(ax, (0.0, 0.0), (a, 0.0), r"$a$", offset=-0.18, side=-1)
    ax.set_xlim(-2.2, 2.2)
    ax.set_ylim(-2.35, 2.2)
    ax.set_title(r"квадраты", fontsize=10)

    ax = axes[2]
    ax.set_aspect("equal")
    ax.axis("off")
    s = 0.42
    _draw_hex_tiling(ax, s=s, rings=4, highlight=(0, 0))
    ax.set_xlim(-2.5, 2.5)
    ax.set_ylim(-2.5, 2.5)
    ax.set_title(r"шестиугольники", fontsize=10)

    fig.suptitle("Три регулярных замощения плоскости", fontsize=11, y=1.02)
    _save(fig, "carrier-tilings.pdf")


def fig_neighbors_2d() -> None:
    fig, axes = plt.subplots(1, 3, figsize=(9.8, 3.4))

    ax = axes[0]
    ax.set_aspect("equal")
    ax.axis("off")
    a = 0.55
    _draw_triangle_tiling(ax, a=a, rows=4, cols=4, highlight_idx=None)
    h = a * math.sqrt(3) / 2
    v1 = np.array([a, 0.0])
    v2 = np.array([a / 2, h])
    cx, cy = (v1 + v2) / 3
    ax.plot(cx, cy, "o", color=INK, ms=7, zorder=6)
    for ang in np.deg2rad([0, 120, 240]):
        p = cx + a * np.array([np.cos(ang), np.sin(ang)])
        ax.plot([cx, p[0]], [cy, p[1]], color=INK, lw=1.2, zorder=4)
        ax.plot(p[0], p[1], "o", color=MUTED, ms=5, zorder=5)
    ax.set_xlim(-1.8, 2.4)
    ax.set_ylim(-1.4, 1.8)
    ax.set_title(r"$|N|=3$", fontsize=10)

    ax = axes[1]
    ax.set_aspect("equal")
    ax.axis("off")
    a = 0.65
    _draw_square_tiling(ax, a=a, n=3, highlight=None)
    cx, cy = 0.0, 0.0
    ax.plot(cx, cy, "o", color=INK, ms=7, zorder=6)
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        p = np.array([cx, cy]) + a * np.array([dx, dy])
        ax.plot([cx, p[0]], [cy, p[1]], color=INK, lw=1.2, zorder=4)
        ax.plot(p[0], p[1], "o", color=MUTED, ms=5, zorder=5)
    diag = a / math.sqrt(2)
    ax.plot([0, diag], [0, diag], color=MUTED, lw=1.0, ls="--", zorder=3)
    dim_linear(ax, (0.0, 0.0), (diag, diag), r"$h_L\sqrt{2}$", offset=0.22, color=MUTED, ls="--", side=-1)
    ax.set_xlim(-1.6, 1.6)
    ax.set_ylim(-1.6, 1.6)
    ax.set_title(r"$|N|=4$", fontsize=10)

    ax = axes[2]
    ax.set_aspect("equal")
    ax.axis("off")
    s = 0.42
    _draw_hex_tiling(ax, s=s, rings=3, highlight=None)
    ax.plot(0, 0, "o", color=INK, ms=7, zorder=6)
    for ang in np.linspace(0, 2 * np.pi, 7)[:-1]:
        p = s * np.array([np.cos(ang), np.sin(ang)])
        ax.plot([0, p[0]], [0, p[1]], color=INK, lw=1.2, zorder=4)
        ax.plot(p[0], p[1], "o", color=MUTED, ms=5, zorder=5)
    ax.set_xlim(-2.0, 2.0)
    ax.set_ylim(-2.0, 2.0)
    ax.set_title(r"$|N|=6$", fontsize=10)

    fig.suptitle(r"Соседство $N(x)$ на регулярных решётках", fontsize=11, y=1.03)
    _save(fig, "carrier-neighbors-2d.pdf")


def _draw_spacetime_2d(ax, c0: float, *, t_lim: float = 1.25, x_lim: float = 1.65, show_past: bool = True) -> None:
    ax.set_aspect("equal")
    ax.axhline(0, color=LIGHT, lw=0.8, zorder=0)
    ax.axvline(0, color=LIGHT, lw=0.8, zorder=0)

    t_f = np.linspace(0, t_lim, 80)
    ax.fill_between(c0 * t_f, 0, t_f, color=FILL, alpha=0.55, zorder=0)
    ax.fill_between(-c0 * t_f, 0, t_f, color=FILL, alpha=0.55, zorder=0)
    ax.plot(c0 * t_f, t_f, color=MUTED, lw=1.5, zorder=1)
    ax.plot(-c0 * t_f, t_f, color=MUTED, lw=1.5, zorder=1)

    if show_past:
        t_p = np.linspace(-t_lim, 0, 80)
        ax.fill_between(c0 * t_p, t_p, 0, color=FILL, alpha=0.35, zorder=0)
        ax.fill_between(-c0 * t_p, t_p, 0, color=FILL, alpha=0.35, zorder=0)
        ax.plot(c0 * t_p, t_p, color=MUTED, lw=1.5, zorder=1)
        ax.plot(-c0 * t_p, t_p, color=MUTED, lw=1.5, zorder=1)
        ax.text(-0.08, -t_lim * 0.72, "прошлое", fontsize=9, ha="center", color=MUTED)

    ax.scatter([0], [0], color=INK, s=55, zorder=5)
    leader(ax, (0.0, 0.0), "наблюдатель", (0.22, -0.12), fontsize=9)
    leader(ax, (0.0, t_lim * 0.72), "будущее", (-0.42, t_lim * 0.88), color=MUTED, fontsize=9)
    leader(ax, (x_lim * 0.78, 0.0), r"$t=0$", (x_lim * 0.55, -0.14), color=MUTED, fontsize=9)
    ax.set_xlabel(r"пространство $x$")
    ax.set_ylabel(r"время $t$")
    ax.set_xlim(-x_lim, x_lim)
    ax.set_ylim(-t_lim if show_past else -0.08, t_lim)


def _light_cone_surface(c0: float, t_max: float, n: int = 40) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    theta = np.linspace(0, 2 * np.pi, n)
    t = np.linspace(0, t_max, n // 2)
    th, tt = np.meshgrid(theta, t)
    r = c0 * tt
    return r * np.cos(th), r * np.sin(th), tt, th


def fig_light_cone() -> None:
    a = 1.0
    ht = 1.0
    c0 = a / ht
    r2 = a * math.sqrt(2)

    fig = plt.figure(figsize=(10.8, 4.9))

    ax2d = fig.add_subplot(1, 2, 1)
    _draw_spacetime_2d(ax2d, c0, t_lim=1.2, x_lim=1.75)
    ax2d.scatter([a], [ht], color=INK, s=48, zorder=6)
    ax2d.plot([0, a], [0, ht], color=INK, lw=1.2, zorder=4)
    ax2d.scatter([r2], [ht], color=MUTED, marker="x", s=70, linewidths=2, zorder=6)
    ax2d.plot([0, r2], [0, ht], color=MUTED, lw=1.0, ls="--", zorder=4)
    dim_axis_h(ax2d, 0, a, ht, r"$h_L$", offset=0.14)
    dim_axis_v(ax2d, 0, ht, 0, r"$h_T$", offset=0.14)
    dim_linear(ax2d, (0.0, 0.0), (r2, ht), r"$h_L\sqrt{2}$", offset=0.18, color=MUTED, ls="--", side=1)
    ax2d.set_title(r"срез $(x,t)$: $c_0 h_T=h_L$", fontsize=10)

    ax3d: Axes3D = fig.add_subplot(1, 2, 2, projection="3d")
    xf, yf, tf, _ = _light_cone_surface(c0, 1.15)
    ax3d.plot_surface(xf, yf, tf, color=FILL, alpha=0.55, linewidth=0, shade=True)
    ax3d.plot_surface(xf, yf, -tf, color=FILL, alpha=0.55, linewidth=0, shade=True)
    lim = 1.15
    xx, yy = np.meshgrid(np.linspace(-lim, lim, 10), np.linspace(-lim, lim, 10))
    ax3d.plot_surface(xx, yy, np.zeros_like(xx), color=FILL_ALT, alpha=0.35, linewidth=0, shade=False)
    ax3d.scatter([0], [0], [0], color=INK, s=45, depthshade=True)
    ax3d.scatter([a], [0], [ht], color=INK, s=40, depthshade=True)
    ax3d.scatter([r2], [0], [ht], color=MUTED, marker="x", s=60, linewidths=2)
    _style_3d(ax3d, 1.35, elev=22, azim=-52, pad=0.12)
    ax3d.set_title(r"объём $(x,y,t)$", fontsize=10, pad=8)

    fig.suptitle("Световой конус: наблюдатель в $(0,0)$, будущее вверх", fontsize=11, y=1.02)
    _save(fig, "carrier-light-cone.pdf")


def fig_hex_neighbors() -> None:
    a = 1.0
    fig, ax = plt.subplots(figsize=(6.4, 5.2))
    ax.set_aspect("equal")
    ax.axis("off")

    _draw_hex_tiling(ax, s=a, rings=3, highlight=(0, 0))
    angles = np.linspace(0, 2 * np.pi, 7)[:-1] + np.pi / 6
    verts = np.column_stack([a * np.cos(angles), a * np.sin(angles)])

    ax.plot(0, 0, "o", color=INK, ms=9, zorder=6)
    for v in verts:
        ax.plot([0, v[0]], [0, v[1]], color=INK, lw=1.4, ls=":", zorder=4)
        ax.plot(v[0], v[1], "o", color=MUTED, ms=6, zorder=5)

    e0, e1 = verts[0], verts[1]
    dim_linear(ax, (e0[0], e0[1]), (e1[0], e1[1]), r"$a=h_L$", offset=0.22, side=-1)
    dim_radius(ax, a, 30, r"$h_L$", label_gap=0.14)

    ax.text(0, 2.55, r"гексагональная ячейка Вороного, $|N(x)|=6$", ha="center", fontsize=11)
    ax.text(0, -2.35, r"соседи на расстоянии $h_L$ за один такт $h_T$", ha="center", fontsize=10)
    lim = 3.1
    ax.set_xlim(-lim, lim)
    ax.set_ylim(-lim * 0.92, lim * 0.92)
    _save(fig, "carrier-hex-neighbors.pdf")


def fig_hex_radii() -> None:
    a = 1.0
    r_in = a * math.sqrt(3) / 2
    angles = np.linspace(0, 2 * np.pi, 7)[:-1] + np.pi / 6
    verts = np.column_stack([a * np.cos(angles), a * np.sin(angles)])

    fig, ax = plt.subplots(figsize=(6.8, 5.0))
    ax.set_aspect("equal")
    ax.axis("off")

    ax.add_patch(plt.Circle((0, 0), a, fill=False, ec=INK, lw=2.0, zorder=1))
    ax.add_patch(plt.Circle((0, 0), r_in, fill=False, ec=MUTED, lw=2.0, ls="--", zorder=1))
    ax.add_patch(Polygon(verts, closed=True, facecolor=FILL, edgecolor=INK, lw=2.0, zorder=2))

    ax.plot(0, 0, "o", color=INK, ms=8, zorder=6)

    dim_radius(ax, a, 90, r"$R_{\mathrm{out}}=a$", color=INK, label_gap=0.12)
    dim_radius(ax, r_in, 0, r"$R_{\mathrm{in}}=\frac{\sqrt{3}}{2}a$", color=MUTED, ls="--", label_gap=0.12)

    ax.text(-0.05, -1.42, r"$\kappa_{\mathrm{hex}}=R_{\mathrm{in}}/R_{\mathrm{out}}=\sqrt{3}/2$", fontsize=12, ha="center")
    ax.text(0, 1.32, r"однотактовое тело: вписанная и описанная сферы", ha="center", fontsize=11)
    ax.set_xlim(-1.35, 1.45)
    ax.set_ylim(-1.55, 1.55)
    _save(fig, "carrier-hex-radii.pdf")


def _draw_single_packing(name: str, n_neighbors: int, centers: np.ndarray, radius: float, outfile: str) -> None:
    fig = plt.figure(figsize=(5.6, 5.2))
    ax: Axes3D = fig.add_subplot(111, projection="3d")
    shell, center_idx, neighbors = _first_shell(centers)
    _draw_sphere_packing(ax, shell, radius, center_idx=center_idx, neighbor_idx=neighbors, first_shell_only=False)
    extent = float(np.max(np.linalg.norm(shell, axis=1)) + radius)
    _style_3d(ax, extent, elev=26, azim=-56, pad=0.35)
    ax.set_title(f"{name}, $|N|={n_neighbors}$", fontsize=11, pad=10)
    _save(fig, outfile)


def fig_packing_sc() -> None:
    _draw_single_packing("SC", 6, _simple_cubic_centers(1, 1.0), 0.5, "carrier-packing-sc.pdf")


def fig_packing_bcc() -> None:
    _draw_single_packing("BCC", 8, _bcc_centers(1, 1.0), math.sqrt(3) / 4, "carrier-packing-bcc.pdf")


def fig_packing_fcc() -> None:
    _draw_single_packing("FCC", 12, _fcc_lattice_points(1, 1.0), 0.5, "carrier-packing-fcc.pdf")


def fig_fcc_shell() -> None:
    a = 1.0
    centers = _fcc_lattice_points(1, a)
    radius = a / 2
    shell, center_idx, neighbors = _first_shell(centers)

    fig = plt.figure(figsize=(6.4, 5.8))
    ax: Axes3D = fig.add_subplot(111, projection="3d")
    _draw_sphere_packing(ax, shell, radius, center_idx=center_idx, neighbor_idx=neighbors, first_shell_only=False)
    extent = float(np.max(np.linalg.norm(shell, axis=1)) + radius)
    _style_3d(ax, extent, elev=24, azim=-52, pad=0.32)
    ax.set_title(r"FCC: плотнейшая упаковка, $|N|=12$, $a=h_L$", fontsize=10, pad=8)
    _save(fig, "carrier-fcc-shell.pdf")


def _draw_cubocta_section(ax, a: float) -> None:
    """2D meridian section: distances to square vs triangular faces."""
    r_hull = a / math.sqrt(2)
    r_tri = a * math.sqrt(2 / 3)
    r_out = a
    ax.set_aspect("equal")
    ax.axis("off")

    ax.plot(0, 0, "o", color=INK, ms=6, zorder=6)
    ax.plot([r_hull, r_hull], [-0.38, 0.38], color=INK, lw=2.0, zorder=2)

    ang_v = math.radians(36)
    vx, vy = r_out * math.cos(ang_v), r_out * math.sin(ang_v)
    ax.plot([0, vx], [0, vy], color=INK, lw=1.3, zorder=3)
    ax.plot(vx, vy, "o", color=INK, ms=5, zorder=5)

    ang_t = math.radians(64)
    tx, ty = r_tri * math.cos(ang_t), r_tri * math.sin(ang_t)
    nx, ny = -math.sin(ang_t), math.cos(ang_t)
    ax.plot([tx - 0.22 * nx, tx + 0.22 * nx], [ty - 0.22 * ny, ty + 0.22 * ny], color=MUTED, lw=1.6, ls="--", zorder=2)

    dim_linear(ax, (0.0, 0.0), (r_hull, 0.0), r"$R_{\mathrm{in}}^{\mathrm{hull}}=a/\sqrt{2}$", offset=-0.2, side=-1)
    dim_radius(ax, r_out, math.degrees(ang_v), r"$R_{\mathrm{out}}=a$", label_gap=0.1)
    dim_linear(
        ax,
        (0.0, 0.0),
        (tx, ty),
        r"$a\sqrt{2/3}$",
        offset=0.2,
        color=MUTED,
        ls="--",
        side=1,
    )
    ax.set_xlim(-0.15, 1.35)
    ax.set_ylim(-0.55, 1.05)


def fig_cubocta_faces() -> None:
    a = 1.0
    verts = _fcc_vertices(a)
    squares, triangles = _cuboctahedron_face_groups(verts, a)

    fig = plt.figure(figsize=(10.4, 4.8))
    ax3: Axes3D = fig.add_subplot(1, 2, 1, projection="3d")
    _add_poly_faces(ax3, squares, FILL, alpha=0.85, edge=INK, ls="-")
    _add_poly_faces(ax3, triangles, FILL_ALT, alpha=0.65, edge=MUTED, ls="--")
    _wire_3d(ax3, verts, _cubocta_edges(verts, a), color=LIGHT, lw=0.7, alpha=0.6)
    _style_3d(ax3, 0.95, elev=18, azim=-42, pad=0.15)
    ax3.set_title("кубооктаэдр", fontsize=10, pad=8)

    ax2d = fig.add_subplot(1, 2, 2)
    _draw_cubocta_section(ax2d, a)
    ax2d.set_title(r"меридиан: разные $R_{\mathrm{in}}$", fontsize=10)

    fig.suptitle("Выпуклая оболочка 12 соседей FCC", fontsize=11, y=1.02)
    _save(fig, "carrier-cubocta-faces.pdf")


def fig_hull_voronoi() -> None:
    a = 1.0
    r_out, r_hull, r_vor = a, a / math.sqrt(2), a / 2

    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    ax.set_aspect("equal")
    ax.axis("off")
    for r, col, lw, ls in ((r_out, INK, 1.8, "-"), (r_hull, MUTED, 1.6, "-"), (r_vor, MUTED, 1.6, "--")):
        ax.add_patch(plt.Circle((0, 0), r, fill=False, ec=col, lw=lw, ls=ls, zorder=1))
    ax.plot(0, 0, "o", color=INK, ms=6, zorder=6)

    dim_radius(ax, r_vor, 118, r"$R_{\mathrm{in}}^{\mathrm{Voronoi}}=a/2$", color=MUTED, ls="--")
    dim_radius(ax, r_hull, -28, r"$R_{\mathrm{in}}^{\mathrm{hull}}=a/\sqrt{2}$", color=MUTED)
    dim_radius(ax, r_out, 22, r"$R_{\mathrm{out}}=a$", color=INK)

    ax.text(0, -1.22, r"$\kappa_{\mathrm{FCC}}=1/\sqrt{2}$;\quad $R_{\mathrm{in}}^{\mathrm{Voronoi}}=\kappa\, R_{\mathrm{in}}^{\mathrm{hull}}$", ha="center", fontsize=11)
    ax.set_xlim(-1.15, 1.65)
    ax.set_ylim(-1.42, 1.35)
    _save(fig, "carrier-hull-voronoi.pdf")


def fig_voronoi_cell() -> None:
    a = 1.0
    fig = plt.figure(figsize=(6.8, 5.8))
    ax: Axes3D = fig.add_subplot(111, projection="3d")
    _draw_voronoi_tessellation(ax, lattice_radius=2, a=a, origin_only_neighbors=True)
    _style_3d(ax, 1.15, elev=24, azim=-50, pad=0.18)
    ax.set_title(r"Замощение $\mathbb{R}^3$ ячейками Вороного FCC", fontsize=10, pad=8)
    _save(fig, "carrier-voronoi-cell.pdf")


def fig_fcc_111_slice() -> None:
    a = 1.0
    radius = a / 2
    centers = _fcc_lattice_points(1, a)
    fig = plt.figure(figsize=(6.8, 5.8))
    ax: Axes3D = fig.add_subplot(111, projection="3d")

    on_slice = np.abs(centers.sum(axis=1)) < 0.12
    for i, c in enumerate(centers):
        if on_slice[i]:
            _add_sphere(ax, c, radius, MUTED, alpha=0.95, n=12)
        else:
            _add_sphere(ax, c, radius, LIGHT, alpha=0.45, n=10)

    lim = 1.05
    xx, yy = np.meshgrid(np.linspace(-lim, lim, 12), np.linspace(-lim, lim, 12))
    ax.plot_surface(xx, yy, -xx - yy, alpha=0.18, color=FILL, linewidth=0, shade=False)

    _style_3d(ax, 1.05, elev=20, azim=-58, pad=0.22)
    ax.set_title(r"Срез $\{111\}$ через FCC-упаковку", fontsize=10, pad=8)
    _save(fig, "carrier-fcc-111-slice.pdf")


def fig_two_speeds() -> None:
    a = 1.0
    ht = 1.0
    c0 = a / ht
    kappa = 1 / math.sqrt(2)
    c_macro = kappa * c0

    fig, axes = plt.subplots(1, 2, figsize=(9.2, 4.2))

    ax = axes[0]
    _draw_spacetime_2d(ax, c0, t_lim=1.35, x_lim=1.55, show_past=False)
    xs, ts = zip(*[(i * a, i * ht) for i in range(4)])
    ax.plot(xs, ts, "o-", color=INK, lw=1.5, ms=5, zorder=6)
    dim_axis_h(ax, 0, a, ht, r"$h_L$", offset=0.11)
    dim_axis_v(ax, 0, ht, 0, r"$h_T$", offset=0.11)
    ax.set_title("микро: дискретный шаг по решётке", fontsize=10)

    ax = axes[1]
    _draw_spacetime_2d(ax, c0, t_lim=1.35, x_lim=1.55, show_past=False)
    x_end = 1.4
    ax.plot([0, x_end], [0, x_end / c0], color=MUTED, lw=1.6, ls="--", zorder=4)
    ax.plot([0, x_end], [0, x_end / c_macro], color=INK, lw=2.0, zorder=5)
    leader(ax, (x_end * 0.7, x_end / c0), r"$c_0$", (x_end * 0.35, x_end / c0 + 0.12), color=MUTED, fontsize=10)
    leader(ax, (x_end * 0.7, x_end / c_macro), r"$c=\kappa c_0$", (x_end * 0.35, x_end / c_macro - 0.14), fontsize=10)
    leader(ax, (0.85, 0.55), r"$\kappa=1/\sqrt{2}$", (0.55, 0.75), color=MUTED, fontsize=9)
    ax.set_title("макро: осреднённый фронт", fontsize=10)

    fig.suptitle(r"Две скорости в плоскости $(x,t)$, наблюдатель в $(0,0)$", fontsize=11, y=1.02)
    _save(fig, "carrier-two-speeds.pdf")


def fig_slice_bridge() -> None:
    fig = plt.figure(figsize=(9.4, 4.0))

    ax2d = fig.add_subplot(1, 2, 1)
    ax2d.set_aspect("equal")
    ax2d.axis("off")
    s = 0.42
    _draw_hex_tiling(ax2d, s=s, rings=3, highlight=(0, 0))
    ax2d.plot(0, 0, "o", color=INK, ms=5, zorder=6)
    ax2d.set_xlim(-2.2, 2.2)
    ax2d.set_ylim(-2.2, 2.2)
    ax2d.set_title(r"$(2{+}1)$: $\kappa_{\mathrm{hex}}=\sqrt{3}/2$", fontsize=10)

    ax3d: Axes3D = fig.add_subplot(1, 2, 2, projection="3d")
    a = 1.0
    centers = _fcc_lattice_points(1, a)
    shell, center_idx, neighbors = _first_shell(centers)
    _draw_sphere_packing(ax3d, shell, a / 2, center_idx=center_idx, neighbor_idx=neighbors, first_shell_only=False)
    lim = 1.05
    xx, yy = np.meshgrid(np.linspace(-lim, lim, 8), np.linspace(-lim, lim, 8))
    ax3d.plot_surface(xx, yy, -xx - yy, alpha=0.15, color=FILL, linewidth=0, shade=False)
    extent = float(np.max(np.linalg.norm(shell, axis=1)) + a / 2)
    _style_3d(ax3d, extent, elev=22, azim=-52, pad=0.25)
    ax3d.set_title(r"$(3{+}1)$ FCC, срез $\{111\}$", fontsize=10, pad=6)

    fig.suptitle(r"Связь среза $(2{+}1)$ и носителя $(3{+}1)$", fontsize=11, y=1.02)
    _save(fig, "carrier-slice-bridge.pdf")


def fig_field_neighbors() -> None:
    a = 1.0
    angles = np.linspace(0, 2 * np.pi, 7)[:-1]

    fig, ax = plt.subplots(figsize=(5.6, 4.8))
    ax.set_aspect("equal")
    ax.axis("off")

    ax.plot(0, 0, "o", color=INK, ms=10, zorder=5)
    for t in angles:
        p = a * np.array([np.cos(t), np.sin(t)])
        ax.plot([0, p[0]], [0, p[1]], color=LIGHT, lw=1.0, zorder=1)
        ax.plot(p[0], p[1], "o", color=MUTED, ms=5, zorder=3)

    circ = plt.Circle((0, 0), 0.35, fill=False, ec=INK, lw=1.0)
    ax.add_patch(circ)
    leader(ax, (0.28, 0.18), r"$z_1$", (0.05, 0.52), fontsize=10)
    leader(ax, (-0.22, -0.28), r"$z_2$", (-0.48, -0.44), color=MUTED, fontsize=10)
    ax.text(0.02, -1.35, r"состояние узла $z(x)\in\mathbb{C}^2$; локальный закон на $N(x)$", ha="center", fontsize=10)
    ax.set_xlim(-1.45, 1.45)
    ax.set_ylim(-1.55, 1.35)
    _save(fig, "carrier-field-z.pdf")


def _draw_worldlines_row(axes, *, kappa: float, row_title: str, t_lim: float = 1.45, x_lim: float = 1.8) -> None:
    a = 1.0
    ht = 1.0
    c0 = a / ht
    c_macro = kappa * c0

    ax = axes[0]
    _draw_spacetime_2d(ax, c0, t_lim=t_lim, x_lim=x_lim, show_past=False)
    n = 4
    xs = [i * a for i in range(n + 1)]
    ts = [i * ht for i in range(n + 1)]
    ax.plot(xs, ts, "o-", color=INK, lw=2.1, ms=6, zorder=6)
    ax.text(-x_lim * 0.92, t_lim * 0.55, row_title, fontsize=9, color=MUTED, rotation=90, va="center")
    dim_axis_h(ax, 0, a, ht, r"$h_L$", offset=0.11)
    dim_axis_v(ax, 0, ht, 0, r"$h_T$", offset=0.11)
    ax.set_title(r"null на $M$", fontsize=9)

    ax = axes[1]
    _draw_spacetime_2d(ax, c0, t_lim=t_lim, x_lim=x_lim, show_past=False)
    xs_mass = [0, 1, 2, 1, 2, 3, 2, 3, 4]
    ts_mass = [i * ht for i in range(len(xs_mass))]
    ax.plot(xs_mass, ts_mass, "o-", color=MUTED, lw=2.1, ms=5, zorder=6)
    leader(ax, (1.5, 1.5), r"$K_P$", (1.85, 1.15), color=MUTED, fontsize=8)
    ax.set_title(r"массивная", fontsize=9)

    ax = axes[2]
    _draw_spacetime_2d(ax, c0, t_lim=t_lim, x_lim=x_lim, show_past=False)
    x_end = 1.35
    ax.plot([0, x_end], [0, x_end / c_macro], color=INK, lw=2.3, zorder=6)
    ax.plot(xs, ts, color=MUTED, lw=1.3, ls=":", marker="o", ms=4, zorder=5)
    leader(ax, (x_end * 0.72, x_end / c_macro), r"$c=\kappa c_0$", (x_end * 0.45, x_end / c_macro + 0.18), fontsize=9)
    leader(ax, (x_end * 0.72, x_end / c0), r"$c_0$", (x_end * 0.45, x_end / c0 - 0.18), color=MUTED, fontsize=8)
    ax.set_title(r"макро-фотон", fontsize=9)


def fig_worldlines() -> None:
    fig, axes = plt.subplots(2, 3, figsize=(11.4, 7.0))
    _draw_worldlines_row(axes[0], kappa=1 / math.sqrt(2), row_title=r"FCC $(3{+}1)$\n$\kappa=1/\sqrt{2}$")
    _draw_worldlines_row(axes[1], kappa=math.sqrt(3) / 2, row_title=r"гекс $(2{+}1)$\n$\kappa=\sqrt{3}/2$")
    fig.suptitle(r"Мировые линии в плоскости $(x,t)$: FCC и гекс-срез", fontsize=11, y=0.98)
    fig.subplots_adjust(top=0.9, hspace=0.38)
    _save(fig, "carrier-worldlines.pdf")


def main() -> None:
    fig_lattice_field()
    fig_epsilon_neighborhood()
    fig_plane_tilings()
    fig_neighbors_2d()
    fig_light_cone()
    fig_hex_neighbors()
    fig_hex_radii()
    fig_packing_sc()
    fig_packing_bcc()
    fig_packing_fcc()
    fig_fcc_shell()
    fig_cubocta_faces()
    fig_hull_voronoi()
    fig_voronoi_cell()
    fig_fcc_111_slice()
    fig_two_speeds()
    fig_worldlines()
    fig_slice_bridge()
    fig_field_neighbors()


if __name__ == "__main__":
    main()
