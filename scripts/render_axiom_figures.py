#!/usr/bin/env python3
"""Render figures for axiom chapters (00-axiom-rationale, 02-axioms)."""

from __future__ import annotations

import math
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Arc, Circle, Rectangle, Wedge

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from render_carrier_figures import _draw_hex_neighborhood, _hex_cell_center, _save
from figure_draft import LW_OBJECT, dim_linear, dim_radius, leader

# Book palette: black/gray + line style, not rainbow.
INK = "#222222"
MUTED = "#666666"
LIGHT = "#aaaaaa"
FILL = "#f0f0f0"

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


def fig_axiom_ladder() -> None:
    """Physical descent ladder (ch. axiom-rationale)."""
    fig, ax = plt.subplots(figsize=(5.8, 5.6))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis("off")

    steps = [
        (9.0, r"$c=\infty$", "классическая механика"),
        (7.4, r"$c\neq\infty$", "СТО"),
        (5.8, r"$\hbar\neq 0$", "квантовая механика"),
        (4.2, r"рождение частиц", "теория поля"),
        (2.6, r"$\hbar,\,G,\,c$", "узлы на решётке"),
    ]
    x0, x1 = 2.0, 8.0
    for y, label, title in steps:
        ax.plot([x0, x1], [y, y], color=INK, lw=1.8)
        ax.text(1.2, y, label, ha="right", va="center", fontsize=10)
        ax.text(8.2, y, title, ha="left", va="center", fontsize=10)

    for y1, y2 in zip([s[0] for s in steps], [s[0] for s in steps[1:]]):
        ax.annotate(
            "",
            xy=(4.9, y2 + 0.18),
            xytext=(4.9, y1 - 0.18),
            arrowprops=dict(arrowstyle="-|>", color=MUTED, lw=1.2),
        )

    ax.text(5.0, 0.7, "спуск: снимается одна идеализация", ha="center", fontsize=10, color=MUTED)
    ax.set_title("Лестница физических идеализаций", fontsize=11, pad=10)
    _save(fig, "axiom-ladder.pdf")


def fig_axiom_locality() -> None:
    """A1–A2: causal neighborhood and local law g."""
    fig, axes = plt.subplots(1, 2, figsize=(9.0, 4.0))

    ax = axes[0]
    ax.set_aspect("equal")
    ax.axis("off")
    a = 1.0
    angles = np.linspace(0, 2 * np.pi, 7)[:-1] + np.pi / 6
    _draw_hex_neighborhood(ax, a, rings=2, center=(0, 0))
    e0, e1 = a * np.array([np.cos(angles[0]), np.sin(angles[0])]), a * np.array([np.cos(angles[1]), np.sin(angles[1])])
    dim_linear(ax, (e0[0], e0[1]), (e1[0], e1[1]), r"$h_L$", offset=0.20, side=-1)
    leader(ax, (0.0, 0.0), r"$x$", (-0.55, 0.42), fontsize=10)
    leader(ax, (0.0, a * 0.55), r"$N(x)$", (0.55, 1.05), fontsize=10)
    ax.text(0, -1.75, r"$A_1$: $c_0 h_T=h_L$, окрестность $N(x)$", ha="center", fontsize=10)
    ax.set_xlim(-2.0, 2.0)
    ax.set_ylim(-1.95, 1.55)

    ax = axes[1]
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6)
    ax.axis("off")
    for i, (x, y) in enumerate([(1.2, 3.0), (1.2, 1.0), (1.2, 5.0), (3.0, 2.0), (3.0, 4.0)]):
        ax.add_patch(Circle((x, y), 0.35, facecolor=FILL, edgecolor=MUTED, lw=1.0))
        ax.text(x, y, rf"$z_{i+1}$", ha="center", va="center", fontsize=9)
    ax.add_patch(Rectangle((5.0, 2.2), 1.6, 1.6, facecolor=FILL, edgecolor=INK, lw=1.2))
    ax.text(5.8, 3.0, r"$g$", ha="center", va="center", fontsize=14)
    ax.add_patch(Circle((8.2, 3.0), 0.45, facecolor="white", edgecolor=INK, lw=1.4))
    ax.text(8.2, 3.0, r"$z(x)$", ha="center", va="center", fontsize=10)
    for x, y in [(1.2, 3.0), (1.2, 1.0), (1.2, 5.0), (3.0, 2.0), (3.0, 4.0)]:
        ax.annotate("", xy=(5.0, 3.0), xytext=(x + 0.35, y), arrowprops=dict(arrowstyle="-|>", color=LIGHT, lw=0.9))
    ax.annotate("", xy=(7.75, 3.0), xytext=(6.6, 3.0), arrowprops=dict(arrowstyle="-|>", color=INK, lw=1.3))
    leader(ax, (8.2, 3.0), r"$z(x)$", (9.0, 3.55), fontsize=10)
    leader(ax, (5.8, 3.0), r"$g$", (5.8, 4.0), fontsize=11)
    ax.text(5.0, 0.55, r"$A_2$: $z(x,t{+}1)=g(\{z(y,t)\}_{y\in N(x)})$", ha="center", fontsize=10)

    fig.suptitle("Каузальность и локальность", fontsize=11, y=1.02)
    _save(fig, "axiom-locality.pdf")


def _draw_phasor(
    ax,
    cx: float,
    cy: float,
    phi: float,
    length: float,
    color: str,
    label: str,
    *,
    ls: str = "-",
    lw: float = 2.0,
) -> None:
    x, y = cx + length * np.cos(phi), cy + length * np.sin(phi)
    ax.annotate(
        "",
        xy=(x, y),
        xytext=(cx, cy),
        arrowprops=dict(arrowstyle="-|>", color=color, lw=lw, linestyle=ls),
    )
    leader(ax, (x, y), label, (1.22 * (x - cx) + cx, 1.22 * (y - cy) + cy), fontsize=10)


def fig_axiom_unitarity() -> None:
    """A3–A4: norm preservation and spinor on C^2, with explicit before→after."""
    fig, axes = plt.subplots(1, 2, figsize=(9.4, 4.1))

    ax = axes[0]
    ax.set_aspect("equal")
    ax.axis("off")
    r = 1.0
    ax.add_patch(Circle((0, 0), r, fill=False, ec=LIGHT, lw=1.0, ls="--"))
    phi0, phi1 = np.deg2rad(35), np.deg2rad(95)
    _draw_phasor(ax, 0, 0, phi0, r, INK, r"$z$")
    _draw_phasor(ax, 0, 0, phi1, r, MUTED, r"$z\,e^{i\Phi}$", ls="--", lw=1.6)
    arc_r = 0.38
    ax.add_patch(
        Arc(
            (0, 0),
            2 * arc_r,
            2 * arc_r,
            angle=0,
            theta1=np.rad2deg(phi0),
            theta2=np.rad2deg(phi1),
            color=INK,
            lw=1.8,
        )
    )
    phi_mid = 0.5 * (phi0 + phi1)
    leader(
        ax,
        (arc_r * np.cos(phi_mid), arc_r * np.sin(phi_mid)),
        r"$\Phi$",
        (1.7 * arc_r * np.cos(phi_mid), 1.7 * arc_r * np.sin(phi_mid)),
        fontsize=11,
    )
    ax.annotate(
        "",
        xy=(r * np.cos(phi1), r * np.sin(phi1)),
        xytext=(r * np.cos(phi0), r * np.sin(phi0)),
        arrowprops=dict(arrowstyle="-|>", color=INK, lw=2.0, connectionstyle="arc3,rad=0.28"),
    )
    ax.text(0, -1.45, r"$A_3$: $|z|\mapsto|z|$, меняется фаза", ha="center", fontsize=10)
    ax.set_xlim(-1.55, 1.55)
    ax.set_ylim(-1.65, 1.55)

    ax = axes[1]
    ax.set_aspect("equal")
    ax.axis("off")
    cx_before, cx_after = -1.15, 1.15
    rad = 0.5
    phi1, phi2 = np.deg2rad(30), np.deg2rad(112)
    dphi = np.deg2rad(24)
    ln1, ln2 = 0.42, 0.33

    for cx in (cx_before, cx_after):
        ax.add_patch(Circle((cx, 0), rad, fill=False, ec=LIGHT, lw=0.9, ls="--"))

    _draw_phasor(ax, cx_before, 0, phi1, ln1, INK, r"$z_1$")
    _draw_phasor(ax, cx_before, 0, phi2, ln2, INK, r"$z_2$")
    _draw_phasor(ax, cx_after, 0, phi1 + dphi, ln1, MUTED, r"$z'_1$", ls="--", lw=1.6)
    _draw_phasor(ax, cx_after, 0, phi2 + dphi, ln2, MUTED, r"$z'_2$", ls="--", lw=1.6)

    ax.annotate(
        "",
        xy=(cx_after - rad - 0.05, 0),
        xytext=(cx_before + rad + 0.05, 0),
        arrowprops=dict(arrowstyle="-|>", color=INK, lw=1.8),
    )
    leader(ax, (0.0, 0.12), r"$R(\Phi)$", (0.0, 0.55), fontsize=11)
    leader(ax, (cx_before, -0.55), r"$z=(z_1,z_2)^\top$", (cx_before, -0.95), fontsize=10)
    leader(ax, (cx_after, -0.55), r"$R(\Phi)z$", (cx_after, -0.95), fontsize=10)
    ax.text(0, -1.42, r"$A_4$: $SU(2)$ на $\mathbb{C}^2$", ha="center", fontsize=10)
    ax.set_xlim(-2.05, 2.05)
    ax.set_ylim(-1.65, 1.25)

    fig.suptitle("Унитарность и спинор", fontsize=11, y=1.02)
    _save(fig, "axiom-unitarity.pdf")


def fig_axiom_thermo() -> None:
    """A5–A6: vacuum floor and phase mixing at fixed N."""
    fig, axes = plt.subplots(1, 2, figsize=(9.0, 3.8))

    ax = axes[0]
    z = np.linspace(0, 1.2, 200)
    v = (z - 0.35) ** 2 + 0.05
    ax.plot(z, v, color=INK, lw=1.8)
    ax.axvline(0.35, color=MUTED, ls="--", lw=1.2)
    ax.plot(0, 2.5, marker="x", color=INK, ms=10, mew=1.8)
    leader(ax, (0.0, 2.5), r"$z=0$: deadlock", (0.12, 2.15), fontsize=9)
    ax.scatter([0.35], [0.05], color=INK, s=40, zorder=5)
    leader(ax, (0.35, 0.05), r"вакуум $z_{\min}>0$", (0.55, 0.28), fontsize=9)
    ax.set_xlabel(r"$|z|$")
    ax.set_ylabel(r"отклик $\Phi$")
    ax.set_title(r"$A_5$: третье начало", fontsize=10)
    ax.set_xlim(-0.05, 1.15)
    ax.set_ylim(-0.1, 2.8)

    ax = axes[1]
    n = 12
    phases = np.linspace(0, 2 * np.pi, n, endpoint=False)
    ax.bar(phases, np.ones(n), width=0.45, color=FILL, edgecolor=INK, lw=0.7)
    ax.axhline(1.0, color=INK, ls="--", lw=1.1)
    leader(ax, (1.0, 1.0), r"$N=\sum|z|^2$", (1.55, 1.12), fontsize=10)
    ax.set_xlabel(r"фазы в $\varepsilon$-окрестности")
    ax.set_ylabel("вес")
    ax.set_title(r"$A_6$: энтропия фаз $\uparrow$, $N$ фикс.", fontsize=10)
    ax.set_xlim(-0.2, 2 * np.pi + 0.2)
    ax.set_ylim(0, 1.25)

    fig.suptitle("Термодинамика микроуровня", fontsize=11, y=1.03)
    _save(fig, "axiom-thermo.pdf")


def fig_axiom_defects() -> None:
    """A9–A11: holonomy, winding, vortex focus."""
    fig, axes = plt.subplots(1, 3, figsize=(10.2, 3.5))

    ax = axes[0]
    ax.set_aspect("equal")
    ax.axis("off")
    sq = np.array([[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]])
    ax.plot(sq[:, 0], sq[:, 1], color=INK, lw=1.4)
    for k, (x, y) in enumerate([(0, 0), (1, 0), (1, 1), (0, 1)]):
        ang = np.deg2rad(45 + 90 * k)
        ax.annotate(
            "",
            xy=(x + 0.18 * np.cos(ang), y + 0.18 * np.sin(ang)),
            xytext=(x, y),
            arrowprops=dict(arrowstyle="-|>", color=MUTED, lw=1.1),
        )
    ax.text(0.5, -0.22, r"$A_9$: $\zeta=(\sum_N z)\cdot z^*$", ha="center", fontsize=9)
    ax.set_xlim(-0.2, 1.2)
    ax.set_ylim(-0.35, 1.15)

    ax = axes[1]
    ax.set_aspect("equal")
    ax.axis("off")
    ax.add_patch(Circle((0, 0), 1.0, fill=False, ec=LIGHT, lw=1.0))
    th = np.linspace(0, 2 * np.pi, 80)
    ax.plot(np.cos(th), np.sin(th), color=INK, lw=1.8)
    ax.annotate(
        "",
        xy=(1.0, 0),
        xytext=(0.85, 0.52),
        arrowprops=dict(arrowstyle="-|>", color=INK, lw=1.6, connectionstyle="arc3,rad=0.5"),
    )
    ax.plot(0, 0, "o", color=INK, ms=5)
    ax.text(0, -1.28, r"$A_{10}$: $\oint d\arg z=2\pi n$", ha="center", fontsize=9)
    ax.set_xlim(-1.35, 1.35)
    ax.set_ylim(-1.45, 1.25)

    ax = axes[2]
    r = np.linspace(0.05, 1.2, 120)
    wide = np.exp(-((r - 0.7) ** 2) / 0.25)
    tight = np.exp(-(r ** 2) / 0.03)
    ax.plot(r, wide, color=MUTED, lw=1.5, ls="--")
    ax.plot(r, tight, color=INK, lw=1.8)
    leader(ax, (0.55, 0.72), "размазано", (0.2, 0.88), color=MUTED, fontsize=9)
    leader(ax, (0.12, 0.88), "полюс", (0.05, 0.62), fontsize=9)
    ax.set_xlabel(r"$r$")
    ax.set_ylabel(r"$|\nabla\arg z|$")
    ax.set_title(r"$A_{11}$: anti-smear", fontsize=10)
    ax.set_xlim(0, 1.25)
    ax.set_ylim(0, 1.05)

    fig.suptitle("Аналитичность и топологические дефекты", fontsize=11, y=1.03)
    _save(fig, "axiom-defects.pdf")


def fig_axiom_m_t() -> None:
    """Determinism on M vs coarse macro on T."""
    fig, axes = plt.subplots(1, 2, figsize=(9.0, 3.8))
    n = 16
    rng = np.random.default_rng(0)
    phase = rng.uniform(0, 2 * np.pi, (n, n))

    ax = axes[0]
    ax.imshow(np.cos(phase), cmap="gray", vmin=-1, vmax=1, interpolation="nearest")
    ax.set_title(r"$\mathcal{M}$: детерминированный $z(x,t)$", fontsize=10)
    ax.set_xticks([])
    ax.set_yticks([])

    ax = axes[1]
    k = np.array([0.25, 0.5, 0.25])
    smooth = np.apply_along_axis(lambda v: np.convolve(v, k, mode="same"), 0, np.cos(phase))
    smooth = np.apply_along_axis(lambda v: np.convolve(v, k, mode="same"), 1, smooth)
    ax.imshow(smooth, cmap="gray", vmin=-1, vmax=1, interpolation="bilinear")
    ax.set_title(r"$\mathcal{T}$: $\Phi=\mathcal{B}z$, Born $|\Phi|^2$", fontsize=10)
    ax.set_xticks([])
    ax.set_yticks([])

    fig.suptitle("Детерминизм микроуровня и грубый прибор", fontsize=11, y=1.03)
    _save(fig, "axiom-m-t.pdf")


def fig_axiom_heat_death() -> None:
    """Theorem 2.3: N invariant on M, Var(Phi) may drop on T."""
    fig, ax = plt.subplots(figsize=(6.4, 3.8))
    t = np.linspace(0, 10, 200)
    n0 = 1.0
    var = 0.8 * np.exp(-0.25 * t) + 0.05 * np.sin(2.5 * t) + 0.08
    ax.plot(t, np.full_like(t, n0), color=INK, lw=2.0, label=r"$N(t)$ на $\mathcal{M}$")
    ax.plot(t, var, color=MUTED, lw=1.8, ls="--", label=r"$\mathrm{Var}(\Phi)$ на $\mathcal{T}$")
    ax.set_xlabel(r"время $t$")
    ax.set_ylabel("нормированная величина")
    ax.legend(loc="upper right", fontsize=9)
    ax.set_title(r"Нет тепловой смерти на $\mathcal{M}$", fontsize=10)
    leader(ax, (5.0, 0.12), r"$g^{-1}$ существует; $\mathcal{B}$ необратима", (5.0, -0.08), color=MUTED, fontsize=9)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 1.15)
    _save(fig, "axiom-heat-death.pdf")


def main() -> None:
    fig_axiom_ladder()
    fig_axiom_locality()
    fig_axiom_unitarity()
    fig_axiom_thermo()
    fig_axiom_defects()
    fig_axiom_m_t()
    fig_axiom_heat_death()


if __name__ == "__main__":
    main()
