#!/usr/bin/env python3
"""Print individual system quanta + Compton lexicon (MODEL.md §4.7.5)."""

from __future__ import annotations

from mt_ca.si_constants import (
    SI,
    compton_scattering_shift,
    compton_wavelength,
    reduced_compton_wavelength,
    system_quanta,
)


def _fmt(x: float) -> str:
    return f"{x:.4e}"


def main() -> None:
    print("M-layer SI bridge (CODATA)")
    print(f"  l_P = {_fmt(SI.l_P)} m")
    print(f"  hT  = {_fmt(SI.hT)} s")
    print(f"  c0  = {_fmt(SI.c0)} m/s")
    print(f"  K_P = {_fmt(SI.K_P)} J/m³")
    print()

    m_e = SI.m_e_CODATA
    print("Electron Compton (M = m_e):")
    print(f"  λ̄_C = ℏ/(m_e c) = {_fmt(reduced_compton_wavelength(m_e))} m")
    print(f"  λ_C  = h/(m_e c)  = {_fmt(compton_wavelength(m_e))} m")
    print(f"  Δλ(θ=90°)         = {_fmt(compton_scattering_shift(m_e, 1.5707963))} m")
    print()

    examples = [
        ("Human 70 kg, τ=15 ms", 70.0, 15e-3, 0.11),
        ("Drosophila 1 mg, τ=4 ms", 1e-6, 4e-3, None),
        ("Brain pool ~1.4 kg, τ=15 ms", 1.4, 15e-3, 0.11),
    ]

    print(
        f"{'System':<32} {'λ̄_C=Δx':>12} {'λ_C':>12} {'Δt':>12} {'N_frame':>12} {'Δx/l_P':>10}"
    )
    print("-" * 94)
    for label, mass, tau, radius in examples:
        q = system_quanta(mass, tau, radius_m=radius)
        print(
            f"{label:<32} {_fmt(q.dx):>12} {_fmt(q.lambda_compton):>12} "
            f"{_fmt(q.dt):>12} {_fmt(q.n_frame):>12} {q.dx_over_l_P:>10.4e}"
        )
        if q.i_max_bits is not None:
            print(f"  Bekenstein I_max ≈ {_fmt(q.i_max_bits)} bit/frame")


if __name__ == "__main__":
    main()
