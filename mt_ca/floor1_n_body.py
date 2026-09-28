"""§5.0.3 / floor1 — N planckons on 3D FCC VACUUM_BOIL (A5 dogfood).

Chain layouts on FCC NN path; graph distances between tracked cores; ± pair events.
Not in MODEL — DEVLOG / verify only.
"""
from __future__ import annotations

import time
from typing import Any, Literal

import torch

from mt_ca.app.dimension import LatticeDimension
from mt_ca.app.lattice import build_run_spec, open_lattice
from mt_ca.config import MConfig
from mt_ca.fixed_point import decode_spinor, encode_spinor
from mt_ca.laplacian import _FCC_OFFSETS
from mt_ca.seeds import SeedClass, make_seed
from mt_ca.spinor import spinor_density

from mt_ca.floor1_two_body import CoreProbe, default_sim_device, pair_annihilated

NBodyScenarioId = Literal["chain4_alt_pm", "chain4_cluster_ppmm", "chain4_pp"]


def fcc_nn_path_offsets(n_sites: int) -> list[tuple[int, int, int]]:
    """``n_sites`` sites along a simple FCC NN walk from origin (includes origin)."""
    if n_sites < 1:
        raise ValueError("n_sites must be ≥ 1")
    path: list[tuple[int, int, int]] = [(0, 0, 0)]
    used = {(0, 0, 0)}
    cur = (0, 0, 0)
    while len(path) < n_sites:
        nxt = None
        for dz, dy, dx in _FCC_OFFSETS:
            nb = (cur[0] + dz, cur[1] + dy, cur[2] + dx)
            if nb in used:
                continue
            nxt = nb
            break
        if nxt is None:
            raise ValueError(f"cannot extend FCC path to length {n_sites}")
        path.append(nxt)
        used.add(nxt)
        cur = nxt
    return path


def torus_fcc_graph_distance(
    a: tuple[int, int, int],
    b: tuple[int, int, int],
    nz: int,
    ny: int,
    nx: int,
) -> int:
    """Shortest-path length on FCC graph with periodic boundaries."""
    if a == b:
        return 0
    start = (int(a[0]) % nz, int(a[1]) % ny, int(a[2]) % nx)
    goal = (int(b[0]) % nz, int(b[1]) % ny, int(b[2]) % nx)
    seen: dict[tuple[int, int, int], int] = {start: 0}
    frontier = [start]
    while frontier:
        cur = frontier.pop(0)
        d = seen[cur]
        if cur == goal:
            return d
        cz, cy, cx = cur
        for dz, dy, dx in _FCC_OFFSETS:
            nb = ((cz + dz) % nz, (cy + dy) % ny, (cx + dx) % nx)
            if nb in seen:
                continue
            seen[nb] = d + 1
            if nb == goal:
                return d + 1
            frontier.append(nb)
    return 10**6


def _roll_site(z: torch.Tensor, dz: int, dy: int, dx: int) -> torch.Tensor:
    return torch.roll(torch.roll(torch.roll(z, shifts=dz, dims=0), shifts=dy, dims=1), shifts=dx, dims=2)


def _excitation_only_3d(
    seed_class: SeedClass,
    nz: int,
    ny: int,
    nx: int,
    *,
    device: torch.device,
    dtype: torch.dtype,
    mod_bits: int,
    frac_bits: int,
) -> torch.Tensor:
    from mt_ca.floor1_two_body import _excitation_only_3d as _exc

    return _exc(
        seed_class,
        nz,
        ny,
        nx,
        device=device,
        dtype=dtype,
        mod_bits=mod_bits,
        frac_bits=frac_bits,
    )


def make_n_planckon_field(
    nz: int,
    ny: int,
    nx: int,
    *,
    charges: tuple[int, ...],
    rel_offsets: list[tuple[int, int, int]],
    device: torch.device,
    dtype: torch.dtype,
    mod_bits: int,
    frac_bits: int,
) -> tuple[torch.Tensor, list[tuple[int, int, int]]]:
    if len(charges) != len(rel_offsets):
        raise ValueError("charges and rel_offsets length mismatch")
    cz, cy, cx = nz // 2, ny // 2, nx // 2
    kw = {
        "device": device,
        "dtype": dtype,
        "mod_bits": mod_bits,
        "frac_bits": frac_bits,
        "nz": nz,
    }
    z = make_seed(SeedClass.VACUUM_BOIL, ny, nx, **kw)
    for q, off in zip(charges, rel_offsets, strict=True):
        seed = SeedClass.VORTEX_P if q > 0 else SeedClass.VORTEX_M
        exc = _excitation_only_3d(
            seed, nz, ny, nx, device=device, dtype=dtype, mod_bits=mod_bits, frac_bits=frac_bits
        )
        z = z + _roll_site(exc, off[0], off[1], off[2])
    f = encode_spinor(z, frac_bits=frac_bits, mod_bits=mod_bits, gauge_fix=False)
    z_out = decode_spinor(f, frac_bits=frac_bits, mod_bits=mod_bits).to(dtype)
    sites = [(cz + off[0], cy + off[1], cx + off[2]) for off in rel_offsets]
    return z_out, sites


def scenario_layout(scenario: NBodyScenarioId) -> tuple[tuple[int, ...], list[tuple[int, int, int]]]:
    offsets = fcc_nn_path_offsets(4)
    if scenario == "chain4_alt_pm":
        return (+1, -1, +1, -1), offsets
    if scenario == "chain4_cluster_ppmm":
        return (+1, +1, -1, -1), offsets
    if scenario == "chain4_pp":
        return (+1, +1, +1, +1), offsets
    raise ValueError(f"unknown scenario {scenario!r}")


def count_stable_cores(probes: list[CoreProbe]) -> int:
    return sum(1 for p in probes if p.stable_signed_Q is not None)


def opposite_pair_indices(charges: tuple[int, ...]) -> list[tuple[int, int]]:
    out: list[tuple[int, int]] = []
    for i in range(len(charges)):
        for j in range(i + 1, len(charges)):
            if charges[i] * charges[j] < 0:
                out.append((i, j))
    return out


def min_pairwise_graph_distance(
    probes: list[CoreProbe],
    nz: int,
    ny: int,
    nx: int,
    *,
    only_stable: bool = True,
) -> int | None:
    sites: list[tuple[int, int, int]] = []
    for p in probes:
        if only_stable and p.stable_signed_Q is None:
            continue
        sites.append((p.iz, p.y, p.x))
    if len(sites) < 2:
        return None
    best = 10**6
    for i in range(len(sites)):
        for j in range(i + 1, len(sites)):
            best = min(best, torus_fcc_graph_distance(sites[i], sites[j], nz, ny, nx))
    return best if best < 10**6 else None


def _probe_all_tracked(
    z: torch.Tensor,
    tracks: list[tuple[int, int, int]],
    anchors: list[tuple[int, int, int]],
    *,
    contour_radius: int,
    cfg: MConfig,
    rho: torch.Tensor,
) -> tuple[list[CoreProbe], list[tuple[int, int, int]]]:
    from mt_ca.matter_survey import MatterSite, survey_at_site
    from mt_ca.floor1_two_body import _row_to_core, _torus_wrap

    probes: list[CoreProbe] = []
    new_tracks: list[tuple[int, int, int]] = []
    taken: set[tuple[int, int, int]] = set()
    nz, ny, nx = z.shape[0], z.shape[1], z.shape[2]

    def _best_near(
        iz0: int, iy0: int, ix0: int, search_radius: int
    ) -> CoreProbe:
        best_score = -1.0
        best_site = (iz0, iy0, ix0)
        best_row = None
        for dz in range(-search_radius, search_radius + 1):
            for dy in range(-search_radius, search_radius + 1):
                for dx in range(-search_radius, search_radius + 1):
                    iz = _torus_wrap(iz0 + dz, nz)
                    iy = _torus_wrap(iy0 + dy, ny)
                    ix = _torus_wrap(ix0 + dx, nx)
                    site = (iz, iy, ix)
                    if site in taken:
                        continue
                    row = survey_at_site(
                        z, MatterSite(iz, iy, ix), contour_radius=contour_radius, cfg=cfg, rho=rho
                    )
                    w_abs = abs(float(row.winding_auto)) if row.winding_auto == row.winding_auto else -1.0
                    score = w_abs + (0.25 if row.b == 1 else 0.0)
                    if score > best_score:
                        best_score = score
                        best_site = site
                        best_row = row
        if best_row is None:
            return CoreProbe(iz=iz0, y=iy0, x=ix0, Q=0, b=0, winding_auto=float("nan"))
        return _row_to_core(best_site, best_row)

    for track, anchor in zip(tracks, anchors, strict=True):
        tz, ty, tx = track
        p = _best_near(tz, ty, tx, 0)
        if p.stable_signed_Q is None:
            az, ay, ax = anchor
            p = _best_near(az, ay, ax, 3)
        site = (p.iz, p.y, p.x)
        taken.add(site)
        probes.append(p)
        new_tracks.append(site)
    return probes, new_tracks


def run_n_body_scenario(
    scenario: NBodyScenarioId,
    *,
    size: int = 24,
    relaxation: int = 12,
    n_max: int = 72,
    device: str | None = None,
    contour_radius: int = 2,
    tick_resolve: bool = False,
) -> dict[str, Any]:
    charges, rel_offsets = scenario_layout(scenario)
    device = device or default_sim_device()
    dev = torch.device(device)
    cfg = MConfig.for_stencil("fcc", heisenberg_floor=True)
    spec = build_run_spec(
        "habitat_boil",
        size,
        embedding=LatticeDimension.VOLUME_3P1,
        device=device,
        steps=0,
    )
    sim = open_lattice(spec)
    nz = sim.nz
    assert nz is not None
    z0, sites = make_n_planckon_field(
        nz,
        sim.ny,
        sim.nx,
        charges=charges,
        rel_offsets=rel_offsets,
        device=dev,
        dtype=sim.dtype,
        mod_bits=cfg.mod_bits,
        frac_bits=cfg.frac_bits,
    )
    sim.set_field(z0)
    n0 = sim.norm()
    tracks = list(sites)
    anchors = list(sites)
    opp_pairs = opposite_pair_indices(charges)

    t_wall0 = time.perf_counter()
    if relaxation > 0:
        sim.step(relaxation)

    first_pm_pair_tick: int | None = None
    ticks_sample: list[dict[str, Any]] = []
    ticks_probed = 0
    probes_f: list[CoreProbe] | None = None

    def _snapshot(t: int, probes: list[CoreProbe]) -> None:
        n_st = count_stable_cores(probes)
        min_d = min_pairwise_graph_distance(probes, nz, sim.ny, sim.nx)
        ticks_sample.append(
            {
                "t": t,
                "n_stable": n_st,
                "min_graph_dist_stable": min_d,
                "Q": [p.stable_signed_Q for p in probes],
            }
        )

    if tick_resolve:
        for t in range(1, n_max + 1):
            sim.step(1)
            rho = spinor_density(sim.z)
            ticks_probed += 1
            probes, tracks = _probe_all_tracked(
                sim.z, tracks, anchors, contour_radius=contour_radius, cfg=cfg, rho=rho
            )
            if first_pm_pair_tick is None:
                for i, j in opp_pairs:
                    if pair_annihilated(probes[i], probes[j]):
                        first_pm_pair_tick = t
                        break
            if t == n_max or (scenario != "chain4_pp" and count_stable_cores(probes) <= 1):
                probes_f = probes
                _snapshot(t, probes)
                if scenario != "chain4_pp" and count_stable_cores(probes) <= 1:
                    break
            elif t % 8 == 0:
                _snapshot(t, probes)
        if probes_f is None:
            rho = spinor_density(sim.z)
            probes_f, _ = _probe_all_tracked(
                sim.z, tracks, anchors, contour_radius=contour_radius, cfg=cfg, rho=rho
            )
            _snapshot(n_max, probes_f)
    else:
        sim.step(n_max)
        rho = spinor_density(sim.z)
        ticks_probed = 1
        probes_f, tracks = _probe_all_tracked(
            sim.z, tracks, anchors, contour_radius=contour_radius, cfg=cfg, rho=rho
        )
        for i, j in opp_pairs:
            if pair_annihilated(probes_f[i], probes_f[j]):
                first_pm_pair_tick = n_max
                break
        _snapshot(n_max, probes_f)

    assert probes_f is not None
    wall_s = time.perf_counter() - t_wall0
    n_late = sim.norm()
    norm_ok = n_late < 12.0 * max(n0, 1e-12) and not (n_late != n_late)
    n_stable_final = count_stable_cores(probes_f)
    min_dist_final = min_pairwise_graph_distance(probes_f, nz, sim.ny, sim.nx)
    min_dist_initial = min_pairwise_graph_distance(
        [
            CoreProbe(iz=s[0], y=s[1], x=s[2], Q=q, b=1, winding_auto=1.0)
            for s, q in zip(sites, charges, strict=True)
        ],
        nz,
        sim.ny,
        sim.nx,
        only_stable=False,
    )

    if scenario == "chain4_pp":
        scenario_ok = n_stable_final >= 3 and not any(
            pair_annihilated(probes_f[i], probes_f[j])
            for i in range(4)
            for j in range(i + 1, 4)
            if charges[i] * charges[j] < 0
        )
    elif scenario == "chain4_alt_pm":
        scenario_ok = n_stable_final <= 2 and (first_pm_pair_tick is not None or n_stable_final < 4)
    else:
        scenario_ok = n_stable_final < 4 and first_pm_pair_tick is not None

    scenario_ok = scenario_ok and norm_ok
    if scenario == "chain4_pp" and min_dist_final is not None:
        scenario_ok = scenario_ok and min_dist_final >= 1

    return {
        "scenario": scenario,
        "charges": charges,
        "size": size,
        "relaxation": relaxation,
        "n_max": n_max,
        "norm0": n0,
        "norm_late": n_late,
        "norm_ok": norm_ok,
        "n_stable_final": n_stable_final,
        "min_graph_dist_initial": min_dist_initial,
        "min_graph_dist_final": min_dist_final,
        "first_pm_pair_tick": first_pm_pair_tick,
        "tick_resolve": tick_resolve,
        "ticks_probed": ticks_probed,
        "wall_s": wall_s,
        "scenario_ok": scenario_ok,
        "ticks_sample": ticks_sample,
        "sites_initial": sites,
        "tracks_final": tracks,
    }


def run_n_body_harness(
    *,
    size: int = 24,
    relaxation: int = 12,
    n_max: int = 72,
    device: str | None = None,
    tick_resolve: bool = False,
) -> dict[str, Any]:
    device = device or default_sim_device()
    t0 = time.perf_counter()
    scenarios: tuple[NBodyScenarioId, ...] = (
        "chain4_alt_pm",
        "chain4_cluster_ppmm",
        "chain4_pp",
    )
    rows = {
        sid: run_n_body_scenario(
            sid,
            size=size,
            relaxation=relaxation,
            n_max=n_max,
            device=device,
            tick_resolve=tick_resolve,
        )
        for sid in scenarios
    }
    alt = rows["chain4_alt_pm"]
    clu = rows["chain4_cluster_ppmm"]
    pp = rows["chain4_pp"]
    pm_channel_opens = (
        alt["n_stable_final"] < pp["n_stable_final"]
        and clu["n_stable_final"] < pp["n_stable_final"]
    )
    checks_ok = all(rows[s]["scenario_ok"] for s in scenarios) and pm_channel_opens
    return {
        "scenarios": rows,
        "checks_ok": checks_ok,
        "pm_channel_opens": pm_channel_opens,
        "size": size,
        "relaxation": relaxation,
        "n_max": n_max,
        "device": device,
        "tick_resolve": tick_resolve,
        "harness_wall_s": time.perf_counter() - t0,
        "note": (
            "Four planckons on FCC NN chain on VACUUM_BOIL: ± alternation vs ++-- cluster vs ++++; "
            "track graph distance between cores; no global collapse to one site (like-sign)."
        ),
    }
