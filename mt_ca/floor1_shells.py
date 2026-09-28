"""§5.0.4-B — coordination shells and ρ_Θ mode catalog (FCC N₁₂ graph)."""
from __future__ import annotations

from collections import deque
from typing import Any

from mt_ca.laplacian import _FCC_OFFSETS


def fcc_graph_distance(
    origin: tuple[int, int, int] = (0, 0, 0),
    *,
    max_k: int,
) -> dict[tuple[int, int, int], int]:
    """Shortest-path distance from ``origin`` up to shell ``max_k`` (bounded BFS).

    On the infinite ℤ³ FCC graph an unbounded BFS never terminates — always pass ``max_k``.
    """
    if max_k < 0:
        raise ValueError("max_k must be >= 0")
    dist: dict[tuple[int, int, int], int] = {origin: 0}
    q: deque[tuple[int, int, int]] = deque([origin])
    offsets = _FCC_OFFSETS
    while q:
        p = q.popleft()
        d = dist[p]
        if d >= max_k:
            continue
        for o in offsets:
            n = (p[0] + o[0], p[1] + o[1], p[2] + o[2])
            if n not in dist:
                dist[n] = d + 1
                q.append(n)
    return dist


def coordination_shell_sizes(max_k: int = 3) -> dict[int, int]:
    """Site counts on coordination spheres k=0…max_k (k=0 is the core)."""
    dist = fcc_graph_distance(max_k=max_k)
    return {k: sum(1 for d in dist.values() if d == k) for k in range(max_k + 1)}


def sites_on_shell(k: int, *, ball_max_k: int | None = None) -> list[tuple[int, int, int]]:
    if k < 0:
        raise ValueError("k must be >= 0")
    cap = ball_max_k if ball_max_k is not None else k
    if cap < k:
        raise ValueError("ball_max_k must be >= k")
    dist = fcc_graph_distance(max_k=cap)
    return sorted(p for p, d in dist.items() if d == k)


def _neighbors_on_shell(
    site: tuple[int, int, int],
    target_k: int,
    *,
    ball_max_k: int,
    dist: dict[tuple[int, int, int], int],
) -> list[tuple[int, int, int]]:
    x, y, z = site
    out: list[tuple[int, int, int]] = []
    for o in _FCC_OFFSETS:
        n = (x + o[0], y + o[1], z + o[2])
        if dist.get(n) == target_k:
            out.append(n)
    return out


def shell_neighbor_stats(max_k: int = 3) -> dict[int, dict[str, int | float]]:
    """How shell-k sites attach to inner shells (for selection / A1 reachability)."""
    dist = fcc_graph_distance(max_k=max_k)
    stats: dict[int, dict[str, int | float]] = {}
    for k in range(2, max_k + 1):
        counts: list[int] = []
        for site in sites_on_shell(k, ball_max_k=max_k):
            counts.append(len(_neighbors_on_shell(site, k - 1, ball_max_k=max_k, dist=dist)))
        stats[k] = {
            "sites": len(counts),
            "min_inner_neighbors": min(counts) if counts else 0,
            "max_inner_neighbors": max(counts) if counts else 0,
        }
    return stats


def build_rho_theta_shell_catalog(*, max_k: int = 3) -> dict[str, Any]:
    """Finite catalog tiers for ρ_Θ modes on coordination spheres (not 2^N enumeration)."""
    sizes = coordination_shell_sizes(max_k=max_k)
    n12 = sizes[1]
    n2 = sizes[2]
    n3 = sizes[3] if max_k >= 3 else 0
    cumulative = sum(sizes[k] for k in range(max_k + 1))
    elementary_excitations = n2 + n3  # one-site bumps on shells 2–3 with full ε-star

    neighbor_stats = shell_neighbor_stats(max_k=max_k)
    shell2_reachable_one_tick = (
        neighbor_stats.get(2, {}).get("min_inner_neighbors", 0) >= 1
    )
    shell3_reachable_two_ticks = (
        neighbor_stats.get(3, {}).get("min_inner_neighbors", 0) >= 1
    )

    tiers: list[dict[str, str | int]] = [
        {
            "id": "shell_geometry",
            "status": "closed",
            "count": cumulative,
            "note": f"FCC graph ball k≤{max_k}: 1+{n12}+{n2}+{n3} sites",
        },
        {
            "id": "shell1_star",
            "status": "closed",
            "count": n12,
            "note": "ε-star; ground C2 support (R_dress=1·dl)",
        },
        {
            "id": "shell2_sphere",
            "status": "closed",
            "count": n2,
            "note": "2nd coordination sphere; excitation locus (C3)",
        },
        {
            "id": "shell3_sphere",
            "status": "closed",
            "count": n3,
            "note": "3rd coordination sphere; higher C3 locus",
        },
        {
            "id": "elementary_single_site_modes",
            "status": "closed_algebra",
            "count": elementary_excitations,
            "note": "one ρ_Θ bump on shell 2 or 3 with full shell-1 halo",
        },
        {
            "id": "full_binary_patterns",
            "status": "not_enumerated",
            "count": 0,
            "note": f"2^{n2}+2^{n3} composite patterns — C3 class; not SSOT table",
        },
        {
            "id": "inter_shell_g_paths",
            "status": "soft_open",
            "count": 0,
            "note": "full allowed transitions under g between shell occupancies",
        },
    ]

    checks_ok = (
        n12 == 12
        and n2 == 42
        and n3 == 92
        and elementary_excitations == 134
        and shell2_reachable_one_tick
        and shell3_reachable_two_ticks
    )

    return {
        "max_k": max_k,
        "shell_sizes": sizes,
        "cumulative_sites": cumulative,
        "elementary_excitations_shell23": elementary_excitations,
        "neighbor_stats": neighbor_stats,
        "shell2_one_tick_from_star": shell2_reachable_one_tick,
        "shell3_two_tick_bridge": shell3_reachable_two_ticks,
        "tiers": tiers,
        "catalog_algebra_closed": checks_ok,
        "full_selection_closed": False,
        "checks_ok": checks_ok,
    }
