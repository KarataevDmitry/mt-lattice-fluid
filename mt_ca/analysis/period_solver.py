"""Solve O∘g^T ≈ O and detect exact CA cycles on trajectories (exact g from sim)."""
from __future__ import annotations

import hashlib
from collections.abc import Callable

import torch

from mt_ca.analysis.functional_period import shift_residual


def solve_observable_period(
    series: list[float],
    *,
    t_max: int,
    mse_threshold: float = 1e-4,
) -> dict:
    """Minimal T in 1..t_max with shift_mse_norm(T) <= threshold, else none."""
    n = len(series)
    cap = min(t_max, max(1, n // 3))
    best: tuple[int, float] | None = None
    hits: list[dict] = []
    for t in range(1, cap + 1):
        mse = shift_residual(series, t)
        if mse != mse:  # nan
            continue
        if mse <= mse_threshold:
            hits.append({"T": t, "shift_mse_norm": round(mse, 8)})
            if best is None or t < best[0]:
                best = (t, mse)
    return {
        "mse_threshold": mse_threshold,
        "t_max": cap,
        "period_T": best[0] if best else None,
        "period_mse": round(best[1], 8) if best else None,
        "all_T_below_threshold": hits[:32],
        "solved": best is not None,
    }


def ca_pair_fingerprint(f_curr: torch.Tensor, f_past: torch.Tensor) -> bytes:
    """Exact bytes for cycle detection on Z_N[i] pair."""
    return (
        f_curr.detach().cpu().numpy().tobytes()
        + b"|"
        + f_past.detach().cpu().numpy().tobytes()
    )


def ca_pair_digest(f_curr: torch.Tensor, f_past: torch.Tensor) -> bytes:
    """SHA-256 digest of leapfrog pair (streaming CA cycle search)."""
    h = hashlib.sha256()
    h.update(f_curr.detach().cpu().numpy().tobytes())
    h.update(b"|")
    h.update(f_past.detach().cpu().numpy().tobytes())
    return h.digest()


def solve_ca_trajectory_period(
    f_currs: list[torch.Tensor],
    f_pasts: list[torch.Tensor],
) -> dict:
    """First repeat of (f_curr,f_past) along stored trajectory → exact cycle length."""
    seen: dict[bytes, int] = {}
    for t, (fc, fp) in enumerate(zip(f_currs, f_pasts, strict=True)):
        key = ca_pair_fingerprint(fc, fp)
        if key in seen:
            period = t - seen[key]
            return {
                "solved": True,
                "cycle_period_T": period,
                "cycle_start_tick": seen[key],
                "cycle_end_tick": t,
                "trajectory_ticks": len(f_currs),
            }
        seen[key] = t
    return {
        "solved": False,
        "cycle_period_T": None,
        "trajectory_ticks": len(f_currs),
        "note": "no repeat within stored trajectory — extend ticks or state space too large",
    }


def stream_ca_cycle_search(
    sim,
    *,
    max_ticks: int,
    sample_each_tick: Callable[[int], None] | None = None,
) -> dict:
    """Step ``sim`` up to ``max_ticks``; return on first exact repeat of (f_curr, f_past)."""
    f_curr = sim._f_curr
    f_past = sim._f_past
    if f_curr is None or f_past is None:
        raise RuntimeError("simulator has no leapfrog registers (_f_curr/_f_past)")
    seen: dict[bytes, int] = {}
    for t in range(max_ticks + 1):
        key = ca_pair_digest(f_curr, f_past)
        if key in seen:
            period = t - seen[key]
            return {
                "solved": True,
                "cycle_period_T": period,
                "cycle_start_tick": seen[key],
                "cycle_end_tick": t,
                "trajectory_ticks": t,
                "max_ticks": max_ticks,
                "search_mode": "stream_digest",
            }
        seen[key] = t
        if t >= max_ticks:
            break
        sim.step(1)
        if sample_each_tick is not None:
            sample_each_tick(t + 1)
        f_curr = sim._f_curr
        f_past = sim._f_past
        assert f_curr is not None and f_past is not None
    return {
        "solved": False,
        "cycle_period_T": None,
        "trajectory_ticks": max_ticks,
        "max_ticks": max_ticks,
        "distinct_pairs_seen": len(seen),
        "search_mode": "stream_digest",
        "note": f"no CA pair repeat within T_max={max_ticks} (certifies T_B>{max_ticks} if attractor entered)",
    }
