"""Functional period O∘g^T ≈ O on CA trajectories (discrete f(t+T)=f(t) test).

Analytic target: find minimal T>0 with O(g^T z_t)=O(z_t) on attractor segment.
Numeric: normalized shift residual on instrument series; optional exact Z_N[i] leapfrog match.
"""
from __future__ import annotations

import torch


def shift_residual(series: list[float] | torch.Tensor, lag: int) -> float:
    """Mean squared error / var for comparing f(t) to f(t+lag) (functional equation residual)."""
    if lag <= 0:
        raise ValueError("lag must be positive")
    x = torch.as_tensor(series, dtype=torch.float64)
    n = int(x.numel())
    if lag >= n:
        return float("nan")
    a = x[:-lag]
    b = x[lag:]
    diff = a - b
    var = float(x.var(unbiased=False).item())
    if var < 1e-18:
        return 0.0
    return float((diff**2).mean().item() / var)


def lag_correlation(series: list[float] | torch.Tensor, lag: int) -> float:
    x = torch.as_tensor(series, dtype=torch.float64)
    if lag <= 0 or lag >= x.numel():
        return float("nan")
    x = x - x.mean()
    std = float(x.std(unbiased=False).item())
    if std < 1e-18:
        return 0.0
    x = x / std
    return float((x[:-lag] * x[lag:]).mean().item())


def scan_observable_period(
    series: list[float],
    *,
    max_lag: int = 128,
    model_lags: tuple[int, ...] = (21, 41, 82, 256, 512),
) -> dict:
    """Scan T=1..max_lag for shift residual and autocorrelation."""
    n = len(series)
    cap = min(max_lag, max(1, n // 3))
    lags: list[dict] = []
    best_lag, best_res = None, float("inf")
    for lag in range(1, cap + 1):
        res = shift_residual(series, lag)
        ac = lag_correlation(series, lag)
        lags.append({"T": lag, "shift_mse_norm": round(res, 6), "ac": round(ac, 4)})
        if res < best_res:
            best_res, best_lag = res, lag
    model_rows = []
    for lag in model_lags:
        if lag >= n or lag > cap:
            continue
        model_rows.append(
            {
                "T": lag,
                "shift_mse_norm": round(shift_residual(series, lag), 6),
                "ac": round(lag_correlation(series, lag), 4),
            }
        )
    return {
        "n": n,
        "best_shift_T": best_lag,
        "best_shift_mse_norm": round(best_res, 6) if best_lag else None,
        "lags_sample": lags[: min(12, len(lags))],
        "model_ring_lags": model_rows,
    }


def ca_leapfrog_mismatch(
    f_curr: torch.Tensor,
    f_past: torch.Tensor,
    f_curr_shift: torch.Tensor,
    f_past_shift: torch.Tensor,
) -> float:
    """Relative L1 mismatch between two leapfrog pairs on Z_N[i] lanes."""
    diff = (f_curr - f_curr_shift).abs().to(torch.float64) + (f_past - f_past_shift).abs().to(
        torch.float64
    )
    scale = f_curr.abs().to(torch.float64).mean() + f_past.abs().to(torch.float64).mean() + 1.0
    return float(diff.mean().item() / scale.item())


def scan_ca_leapfrog_period(
    f_currs: list[torch.Tensor],
    f_pasts: list[torch.Tensor],
    *,
    max_lag: int = 128,
) -> dict:
    """Minimal T with mean pairwise mismatch ≈ 0; exact-match rate per T."""
    n = len(f_currs)
    if len(f_pasts) != n:
        raise ValueError("f_currs / f_pasts length mismatch")
    cap = min(max_lag, max(1, n // 3))
    rows: list[dict] = []
    best_exact_T: int | None = None
    for lag in range(1, cap + 1):
        mismatches: list[float] = []
        exact = 0
        pairs = n - lag
        for t in range(pairs):
            eq = torch.equal(f_currs[t + lag], f_currs[t]) and torch.equal(
                f_pasts[t + lag], f_pasts[t]
            )
            if eq:
                exact += 1
            mismatches.append(
                ca_leapfrog_mismatch(f_currs[t], f_pasts[t], f_currs[t + lag], f_pasts[t + lag])
            )
        rate = exact / pairs if pairs else 0.0
        mean_m = sum(mismatches) / len(mismatches) if mismatches else float("nan")
        rows.append(
            {
                "T": lag,
                "exact_match_rate": round(rate, 6),
                "mean_mismatch": round(mean_m, 8),
            }
        )
        if rate >= 1.0 - 1e-12 and best_exact_T is None:
            best_exact_T = lag
    return {
        "n_ticks": n,
        "exact_period_T": best_exact_T,
        "lags_sample": rows[: min(24, len(rows))],
    }
