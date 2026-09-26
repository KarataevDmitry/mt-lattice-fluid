"""Solve O∘g^T ≈ O and detect exact CA cycles on trajectories (exact g from sim)."""
from __future__ import annotations

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
