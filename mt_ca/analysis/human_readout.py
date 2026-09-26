"""Plain-language verdicts for boil period probes (explicit «what we did not find»)."""
from __future__ import annotations


def functional_period_verdict(rep: dict) -> list[str]:
    """Human lines for ``run_boil_functional_period`` report."""
    lines: list[str] = []

    ca = rep.get("ca_leapfrog")
    if ca is not None:
        exact = ca.get("exact_period_T")
        if exact is None:
            lines.append(
                "КА (поле целиком): малого T с полным повтором пары (f_curr, f_past) на Z_N[i] — НЕТ."
            )
        else:
            lines.append(f"КА: найден точный период поля T={exact} (100% совпадений пары на окне).")

    obs = rep.get("observables") or {}
    contrast = obs.get("field_rho_contrast") or {}
    _observable_verdict(
        lines,
        name="ρ_contrast (поле)",
        scan=contrast,
        period_mse_threshold=1e-3,
    )

    for site, block in obs.items():
        if site == "field_rho_contrast" or not isinstance(block, dict):
            continue
        if "best_shift_T" in block:
            continue
        for key, scan in block.items():
            if not isinstance(scan, dict):
                continue
            thresh = 1e-3 if key in ("n_E",) else 0.05
            _observable_verdict(lines, name=f"{site}.{key}", scan=scan, period_mse_threshold=thresh)

    return lines


def _observable_verdict(
    lines: list[str],
    *,
    name: str,
    scan: dict,
    period_mse_threshold: float,
) -> None:
    best_t = scan.get("best_shift_T")
    mse = scan.get("best_shift_mse_norm")
    if mse is None:
        return
    ring = scan.get("model_ring_lags") or []
    ring_ok = [r for r in ring if r.get("shift_mse_norm", 1.0) <= period_mse_threshold]
    if mse <= period_mse_threshold and ring_ok:
        lines.append(f"{name}: период по O(t+T)=O(t) — ДА (mse≤{period_mse_threshold}, T={best_t}).")
    elif mse <= period_mse_threshold:
        lines.append(
            f"{name}: ряд почти не меняется (mse={mse}); это не обязательно цикл g — часто константа (n_E=0)."
        )
    else:
        lines.append(
            f"{name}: периода по определению НЕТ (лучший mse={mse} при T={best_t} — не доказывает f(t+T)=f(t))."
        )
    if ring and not ring_ok:
        parts = [str(r["T"]) for r in ring]
        lines.append(
            f"  → MODEL-кандидаты T∈{{{', '.join(parts)}}} на {name} не дают малого residual — связь с кольцом 512 здесь НЕ видна."
        )
    if name.startswith("ρ_contrast") and best_t == 2 and mse is not None and mse < 0.02:
        lines.append(
            f"  → (строка 3) best_shift T=2 при mse={mse}: дрейф, не кольцо 41/512 и не доказательство периода 2."
        )


def linear_spectrum_verdict(rep: dict) -> list[str]:
    """Human lines for ``run_boil_linear_spectrum`` report."""
    lines: list[str] = []
    lines.extend(linear_probe_three_lines(rep))
    modes = rep.get("modes") or []
    stable = [m for m in modes if m.get("stable_mode")]
    if stable:
        lines.append(
            f"Дополнительно: {len(stable)} low-k мод с |λ|≤1 — только у них имеет смысл inferred_T."
        )
    return lines


def linear_probe_three_lines(rep: dict) -> list[str]:
    """Fixed «three lines» summary matching MODEL table (explicit negatives)."""
    modes = rep.get("modes") or []
    top = modes[0] if modes else {}
    ab = top.get("abs_lambda", "?")
    stable = [m for m in modes if m.get("stable_mode")]

    if not stable:
        line1 = (
            f"1) Low-k на boil: |λ|≈{ab} (>1) → формула «T∼2π/arg λ» здесь НЕ ПРИМЕНИМА "
            "(это не «не нашли T», а «фаза не задаёт период», пока мода раздувается)."
        )
    else:
        line1 = (
            f"1) Low-k: есть нейтральные моды (|λ|≤1); T∼2π/arg λ читать только у stable_mode."
        )

    ring_mse: dict = rep.get("contrast_shift_mse_at_ring") or {}
    if ring_mse:
        ordered = sorted((int(t), float(v)) for t, v in ring_mse.items())
        chain = " → ".join(f"{t}:{v:.3g}" for t, v in ordered[:4])
        line2 = (
            f"2) Ring 21/41/82 vs ρ_contrast: shift_mse растёт ({chain}) — "
            "минимумов на лестнице §5.0.4-A НЕТ (алгебра одной hV ≠ spatial contrast)."
        )
    else:
        line2 = (
            "2) Ring vs contrast: данных нет в этом прогоне — перезапусти boil_linear_spectrum."
        )

    scan = rep.get("contrast_scan") or {}
    bt = scan.get("best_shift_T")
    bm = scan.get("best_shift_mse_norm")
    if bt is not None and bm is not None:
        line3 = (
            f"3) Functional best_shift: T={bt}, mse={bm} — "
            "это артеfact медленного дрейfa/шага leapfrog, НЕ период кольца и НЕ f(t+T)=f(t)."
        )
    else:
        line3 = "3) Functional best_shift: нет contrast_scan в отчёте."

    return [line1, line2, line3]


def print_verdict(title: str, lines: list[str]) -> None:
    print(f"=== {title} ===")
    for line in lines:
        print(line)
    print()
