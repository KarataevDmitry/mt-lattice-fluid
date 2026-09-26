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


def linear_spectrum_verdict(rep: dict) -> list[str]:
    """Human lines for ``run_boil_linear_spectrum`` report."""
    lines: list[str] = []
    modes = rep.get("modes") or []
    stable = [m for m in modes if m.get("stable_mode")]
    if not stable:
        top = modes[0] if modes else {}
        ab = top.get("abs_lambda", "?")
        lines.append(
            f"Линearization: нейтральных мод (|λ|≤1) среди low-k — НЕТ; типично |λ|≈{ab} → фон усиливает возмущения, не «крутится» малым T."
        )
    else:
        lines.append(f"Линearization: {len(stable)} мод с |λ|≤1 — кандидаты на осцилляцию (смотри inferred_T только у stable).")

    ring_mse: dict = rep.get("contrast_shift_mse_at_ring") or {}
    ring_t = rep.get("model_ring_T") or []
    if ring_mse:
        best_ring = min(ring_mse.items(), key=lambda kv: kv[1])
        scan = rep.get("contrast_scan") or {}
        best_any_t = scan.get("best_shift_T")
        best_any_mse = scan.get("best_shift_mse_norm")
        lines.append(
            f"Contrast vs MODEL T: на кольце (21/41/82…) mse={ring_mse} — это не нули; минимум на кольце T={best_ring[0]} (mse={best_ring[1]})."
        )
        if best_any_mse is not None and best_any_mse < 0.01 and best_ring[1] > best_any_mse * 3:
            lines.append(
                f"  → Лестница E₀ ({ring_t}) не объясняет «лучший» T={best_any_t} contrast — другая физика (дрейф/чётность шага)."
            )
        lines.append(
            "Итог: период океана = кольцо planckon на одной hV — в этих probe НЕ подтверждён (и не обязан — разные объекты)."
        )
    return lines


def print_verdict(title: str, lines: list[str]) -> None:
    print(f"=== {title} ===")
    for line in lines:
        print(line)
    print()
