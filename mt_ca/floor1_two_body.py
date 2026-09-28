"""§5.0.3 / floor1 — two planckons on filled 3D FCC VACUUM_BOIL (A5).

Local planting at graph-separated cores; probes Q per core, Q_net, annihilation tick.
Not global torus winding (see annihilation_t_stats.py).
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Literal

import torch

from mt_ca.app.dimension import LatticeDimension
from mt_ca.app.lattice import build_run_spec, open_lattice
from mt_ca.config import MConfig
from mt_ca.fixed_point import decode_spinor, encode_spinor
from mt_ca.laplacian import _FCC_OFFSETS
from mt_ca.matter_survey import MatterSite, survey_at_site
from mt_ca.metrics import total_norm_squared
from mt_ca.seeds import SeedClass, make_seed
from mt_ca.spinor import spinor_density
from mt_ca.topology import winding_nearest_int

ScenarioId = Literal["pp_nn", "mm_nn", "pm_nn", "pm_d2"]

_WINDING_MIN = 0.75
_EXCITATION_CACHE: dict[tuple, torch.Tensor] = {}


def default_sim_device() -> str:
    """Match verify_principles.py: cuda when available."""
    return "cuda" if torch.cuda.is_available() else "cpu"


def fcc_offset_at_graph_distance(k: int) -> tuple[int, int, int]:
    """First BFS offset from origin on undirected FCC N₁₂ (torus-agnostic coords)."""
    if k < 1:
        raise ValueError("graph distance must be ≥ 1")
    origin = (0, 0, 0)
    seen: dict[tuple[int, int, int], int] = {origin: 0}
    frontier: list[tuple[int, int, int]] = [origin]
    while frontier:
        cur = frontier.pop(0)
        d = seen[cur]
        if d == k:
            return cur
        if d >= k:
            continue
        cz, cy, cx = cur
        for oz, oy, ox in _FCC_OFFSETS:
            nb = (cz + oz, cy + oy, cx + ox)
            if nb in seen:
                continue
            nd = d + 1
            seen[nb] = nd
            if nd == k:
                return nb
            frontier.append(nb)
    raise ValueError(f"no FCC offset at graph distance {k}")


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
    key = (seed_class.value, nz, ny, nx, str(device), dtype, mod_bits, frac_bits)
    cached = _EXCITATION_CACHE.get(key)
    if cached is not None:
        return cached
    kw = {
        "device": device,
        "dtype": dtype,
        "mod_bits": mod_bits,
        "frac_bits": frac_bits,
        "nz": nz,
    }
    z_full = make_seed(seed_class, ny, nx, **kw)
    z_boil = make_seed(SeedClass.VACUUM_BOIL, ny, nx, **kw)
    out = z_full - z_boil
    _EXCITATION_CACHE[key] = out
    return out


def make_two_planckon_field(
    nz: int,
    ny: int,
    nx: int,
    *,
    q_a: int,
    q_b: int,
    graph_sep: int,
    device: torch.device,
    dtype: torch.dtype = torch.complex64,
    mod_bits: int,
    frac_bits: int,
) -> tuple[torch.Tensor, tuple[int, int, int], tuple[int, int, int]]:
    """Boiling ocean + two localized vortex cores at FCC graph separation."""
    cz, cy, cx = nz // 2, ny // 2, nx // 2
    off = fcc_offset_at_graph_distance(graph_sep)
    site_a = (cz, cy, cx)
    site_b = (cz + off[0], cy + off[1], cx + off[2])

    seed_center = SeedClass.VORTEX_P if q_a > 0 else SeedClass.VORTEX_M
    seed_second = SeedClass.VORTEX_P if q_b > 0 else SeedClass.VORTEX_M
    kw = {
        "device": device,
        "dtype": dtype,
        "mod_bits": mod_bits,
        "frac_bits": frac_bits,
        "nz": nz,
    }
    z = make_seed(seed_center, ny, nx, **kw)
    if seed_second is not seed_center or off != (0, 0, 0):
        exc_b = _excitation_only_3d(
            seed_second, nz, ny, nx, device=device, dtype=dtype, mod_bits=mod_bits, frac_bits=frac_bits
        )
        z = z + _roll_site(exc_b, off[0], off[1], off[2])
    f = encode_spinor(z, frac_bits=frac_bits, mod_bits=mod_bits, gauge_fix=False)
    z_out = decode_spinor(f, frac_bits=frac_bits, mod_bits=mod_bits).to(dtype)
    return z_out, site_a, site_b


@dataclass(frozen=True, slots=True)
class CoreProbe:
    iz: int
    y: int
    x: int
    Q: int
    b: int
    winding_auto: float

    @property
    def stable_signed_Q(self) -> int | None:
        if self.b != 1 or self.winding_auto != self.winding_auto:
            return None
        if abs(self.winding_auto) < _WINDING_MIN:
            return None
        n = winding_nearest_int(self.winding_auto)
        if abs(n) != 1:
            return None
        return n


def _torus_wrap(val: int, n: int) -> int:
    return int(val) % n


def _row_to_core(site: tuple[int, int, int], row: Any) -> CoreProbe:
    w = float(row.winding_auto)
    if w != w or abs(w) < _WINDING_MIN:
        q = 0
    else:
        q = winding_nearest_int(w)
        if abs(q) != 1:
            q = 0
    iz, iy, ix = site
    return CoreProbe(iz=iz, y=iy, x=ix, Q=q, b=row.b, winding_auto=w)


def probe_core_near_anchor(
    z: torch.Tensor,
    anchor: tuple[int, int, int],
    *,
    contour_radius: int = 2,
    search_radius: int = 5,
    exclude: tuple[int, int, int] | None = None,
    rho: torch.Tensor | None = None,
    cfg: MConfig | None = None,
) -> CoreProbe:
    """Track |Q|≈1 core in a cube around anchor; pass ``rho`` to avoid recomputing density."""
    iz0, iy0, ix0 = anchor
    nz, ny, nx = z.shape[0], z.shape[1], z.shape[2]
    cfg = cfg or MConfig.for_stencil("fcc")
    if rho is None:
        rho = spinor_density(z)
    best_score = -1.0
    best_site = anchor
    best_row = None
    for dz in range(-search_radius, search_radius + 1):
        for dy in range(-search_radius, search_radius + 1):
            for dx in range(-search_radius, search_radius + 1):
                iz = _torus_wrap(iz0 + dz, nz)
                iy = _torus_wrap(iy0 + dy, ny)
                ix = _torus_wrap(ix0 + dx, nx)
                if exclude is not None and (iz, iy, ix) == exclude:
                    continue
                row = survey_at_site(
                    z, MatterSite(iz, iy, ix), contour_radius=contour_radius, cfg=cfg, rho=rho
                )
                w_abs = abs(float(row.winding_auto)) if row.winding_auto == row.winding_auto else -1.0
                score = w_abs + (0.25 if row.b == 1 else 0.0)
                if score > best_score:
                    best_score = score
                    best_site = (iz, iy, ix)
                    best_row = row
    if best_row is None:
        return CoreProbe(iz=iz0, y=iy0, x=ix0, Q=0, b=0, winding_auto=float("nan"))
    return _row_to_core(best_site, best_row)


def _probe_tracked_pair(
    z: torch.Tensor,
    track_a: tuple[int, int, int],
    track_b: tuple[int, int, int],
    anchor_a: tuple[int, int, int],
    anchor_b: tuple[int, int, int],
    *,
    contour_radius: int,
    cfg: MConfig,
    rho: torch.Tensor | None = None,
) -> tuple[CoreProbe, CoreProbe, tuple[int, int, int], tuple[int, int, int]]:
    if rho is None:
        rho = spinor_density(z)

    def _one(
        track: tuple[int, int, int],
        anchor: tuple[int, int, int],
        exclude: tuple[int, int, int] | None,
    ) -> CoreProbe:
        p = probe_core_near_anchor(
            z, track, contour_radius=contour_radius, search_radius=0, exclude=None, rho=rho, cfg=cfg
        )
        if p.stable_signed_Q is None:
            p = probe_core_near_anchor(
                z,
                anchor,
                contour_radius=contour_radius,
                search_radius=3,
                exclude=exclude,
                rho=rho,
                cfg=cfg,
            )
        return p

    pa = _one(track_a, anchor_a, None)
    pb = _one(track_b, anchor_b, (pa.iz, pa.y, pa.x))
    return pa, pb, (pa.iz, pa.y, pa.x), (pb.iz, pb.y, pb.x)


def pair_annihilated(c0: CoreProbe, c1: CoreProbe) -> bool:
    return c0.stable_signed_Q is None and c1.stable_signed_Q is None


def pair_like_persisted(c0: CoreProbe, c1: CoreProbe, sign: int) -> bool:
    s0, s1 = c0.stable_signed_Q, c1.stable_signed_Q
    return s0 == sign and s1 == sign


def scenario_charges(scenario: ScenarioId) -> tuple[int, int, int]:
    if scenario == "pp_nn":
        return 1, 1, 1
    if scenario == "mm_nn":
        return -1, -1, 1
    if scenario == "pm_nn":
        return 1, -1, 1
    if scenario == "pm_d2":
        return 1, -1, 2
    raise ValueError(f"unknown scenario {scenario!r}")


def run_two_body_scenario(
    scenario: ScenarioId,
    *,
    size: int = 24,
    relaxation: int = 12,
    n_max: int = 72,
    device: str | None = None,
    contour_radius: int = 2,
    tick_resolve: bool = True,
) -> dict[str, Any]:
    q_a, q_b, graph_sep = scenario_charges(scenario)
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
    z0, site_a, site_b = make_two_planckon_field(
        nz,
        sim.ny,
        sim.nx,
        q_a=q_a,
        q_b=q_b,
        graph_sep=graph_sep,
        device=dev,
        dtype=sim.dtype,
        mod_bits=cfg.mod_bits,
        frac_bits=cfg.frac_bits,
    )
    is_pm = scenario in ("pm_nn", "pm_d2")
    is_like = scenario in ("pp_nn", "mm_nn")
    like_sign = 1 if scenario == "pp_nn" else -1

    sim.set_field(z0)
    n0 = sim.norm()
    rho0 = spinor_density(sim.z)
    pa0, pb0, _, _ = _probe_tracked_pair(
        sim.z, site_a, site_b, site_a, site_b, contour_radius=contour_radius, cfg=cfg, rho=rho0
    )
    initial_like_ok = pair_like_persisted(pa0, pb0, like_sign) if is_like else None

    t_wall0 = time.perf_counter()
    if relaxation > 0:
        sim.step(relaxation)

    ticks_sample: list[dict[str, Any]] = []
    track_a, track_b = site_a, site_b
    event_tick: int | None = None
    pa_f: CoreProbe | None = None
    pb_f: CoreProbe | None = None
    ticks_probed = 0

    def _record_tick(t: int, pa: CoreProbe, pb: CoreProbe, ann: bool) -> None:
        ticks_sample.append(
            {
                "t": t,
                "Q_a": pa.Q,
                "Q_b": pb.Q,
                "Q_net": pa.Q + pb.Q,
                "pair_annihilated": ann,
                "like_persisted": pair_like_persisted(pa, pb, like_sign) if is_like else None,
            }
        )

    if tick_resolve:
        consecutive_ann = 0
        for t in range(1, n_max + 1):
            sim.step(1)
            rho = spinor_density(sim.z)
            ticks_probed += 1
            pa, pb, track_a, track_b = _probe_tracked_pair(
                sim.z,
                track_a,
                track_b,
                site_a,
                site_b,
                contour_radius=contour_radius,
                cfg=cfg,
                rho=rho,
            )
            ann = pair_annihilated(pa, pb)
            if ann:
                consecutive_ann += 1
            else:
                consecutive_ann = 0
            if event_tick is None:
                if consecutive_ann >= 2:
                    event_tick = t - 1
                elif t == n_max and ann:
                    event_tick = t
            if is_pm and consecutive_ann >= 2:
                pa_f, pb_f = pa, pb
                _record_tick(t, pa, pb, ann)
                break
            elif t == n_max:
                pa_f, pb_f = pa, pb
                _record_tick(t, pa, pb, ann)
        if pa_f is None or pb_f is None:
            rho = spinor_density(sim.z)
            pa_f, pb_f, _, _ = _probe_tracked_pair(
                sim.z,
                track_a,
                track_b,
                site_a,
                site_b,
                contour_radius=contour_radius,
                cfg=cfg,
                rho=rho,
            )
    else:
        sim.step(n_max)
        rho = spinor_density(sim.z)
        ticks_probed = 1
        pa_f, pb_f, _, _ = _probe_tracked_pair(
            sim.z, track_a, track_b, site_a, site_b, contour_radius=contour_radius, cfg=cfg, rho=rho
        )
        ann = pair_annihilated(pa_f, pb_f)
        if is_pm and ann:
            event_tick = n_max
        _record_tick(n_max, pa_f, pb_f, ann)

    ann_final = pair_annihilated(pa_f, pb_f)
    wall_s = time.perf_counter() - t_wall0

    n_late = sim.norm()
    norm_drift_rel = abs(n_late - n0) / max(n0, 1e-12)
    norm_ok = n_late < 12.0 * max(n0, 1e-12) and not (n_late != n_late)

    if is_pm:
        scenario_ok = pair_annihilated(pa_f, pb_f)
    else:
        scenario_ok = bool(initial_like_ok) and not pair_annihilated(pa_f, pb_f)

    return {
        "scenario": scenario,
        "size": size,
        "graph_sep": graph_sep,
        "q_a": q_a,
        "q_b": q_b,
        "site_a": site_a,
        "site_b": site_b,
        "relaxation": relaxation,
        "n_max": n_max,
        "norm0": n0,
        "norm_late": n_late,
        "norm_drift_rel": norm_drift_rel,
        "norm_ok": norm_ok,
        "event_tick": event_tick,
        "tick_resolve": tick_resolve,
        "ticks_probed": ticks_probed,
        "wall_s": wall_s,
        "pair_annihilated_final": pair_annihilated(pa_f, pb_f),
        "initial_like_ok": initial_like_ok,
        "like_persisted_final": pair_like_persisted(pa_f, pb_f, like_sign) if is_like else None,
        "scenario_ok": scenario_ok and norm_ok,
        "ticks_sample": ticks_sample,
        "Q_a_final": pa_f.Q,
        "Q_b_final": pb_f.Q,
    }


def run_two_body_harness(
    *,
    size: int = 24,
    relaxation: int = 12,
    n_max: int = 72,
    device: str | None = None,
    tick_resolve: bool = True,
) -> dict[str, Any]:
    """Run pp_nn, mm_nn, pm_nn and aggregate verify criteria."""
    device = device or default_sim_device()
    t0 = time.perf_counter()
    rows = {
        sid: run_two_body_scenario(
            sid,
            size=size,
            relaxation=relaxation,
            n_max=n_max,
            device=device,
            tick_resolve=tick_resolve,
        )
        for sid in ("pp_nn", "mm_nn", "pm_nn")
    }
    harness_wall_s = time.perf_counter() - t0
    pm_tick = rows["pm_nn"]["event_tick"]
    pp_ann = rows["pp_nn"]["pair_annihilated_final"]
    pm_final = rows["pm_nn"]["pair_annihilated_final"]
    annihilation_faster_than_like_like = pm_final and not pp_ann and not rows["mm_nn"]["pair_annihilated_final"]
    checks_ok = (
        rows["pp_nn"]["scenario_ok"]
        and rows["mm_nn"]["scenario_ok"]
        and rows["pm_nn"]["scenario_ok"]
        and annihilation_faster_than_like_like
        and all(rows[s]["norm_ok"] for s in rows)
    )
    return {
        "scenarios": rows,
        "pm_event_tick": pm_tick,
        "pp_event_tick": rows["pp_nn"]["event_tick"],
        "mm_event_tick": rows["mm_nn"]["event_tick"],
        "annihilation_faster_than_like_like": annihilation_faster_than_like_like,
        "checks_ok": checks_ok,
        "size": size,
        "relaxation": relaxation,
        "n_max": n_max,
        "device": device,
        "tick_resolve": tick_resolve,
        "harness_wall_s": harness_wall_s,
        "note": (
            "Two planckons on 3D VACUUM_BOIL (single-axis ramp); "
            "pm_nn: both cores lose stable |Q|=1; pp/mm: planted like-sign, no annihilation channel; "
            "Σ|z|² bounded vs t=0 (×12)."
        ),
    }
