#!/usr/bin/env python3
"""Print individual system quanta + Compton lexicon (MODEL §4.8)."""

from __future__ import annotations

from mt_ca.si_constants import (
    SI,
    compton_scattering_shift,
    compton_wavelength,
    reduced_compton_wavelength,
    system_quanta,
    tau_frame_seconds,
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

    # R at ~human mean density (70 kg in R=11 cm) for fly mass scale
    rho_ref = 70.0 / (4.0 / 3.0 * 3.14159265 * 0.11**3)
    r_fly = (3.0 * 1e-6 / (4.0 * 3.14159265 * rho_ref)) ** (1.0 / 3.0)

    examples = [
        ("Human 70 kg, R=11 cm", 70.0, 0.11),
        (f"Drosophila 1 mg, R={r_fly*1e3:.2f} mm (ρ=ρ_human)", 1e-6, r_fly),
        ("Drosophila 1 mg, R=0.63 mm (≈4 ms τ)", 1e-6, 6.3e-4),
        ("Brain pool ~1.4 kg, R=11 cm", 1.4, 0.11),
    ]

    print(
        f"{'System':<40} {'λ̄_C=Δx':>12} {'τ_frame':>12} {'Δt':>12} "
        f"{'N_frame':>12} {'Δx/l_P':>10}"
    )
    print("-" * 102)
    for label, mass, radius in examples:
        q = system_quanta(mass, radius_m=radius)
        tau_ms = q.tau_frame_s * 1e3
        closed_ms = tau_frame_seconds(mass, radius) * 1e3
        print(
            f"{label:<40} {_fmt(q.dx):>12} {tau_ms:>10.3f} ms "
            f"{_fmt(q.dt):>12} {_fmt(q.n_frame):>12} {q.dx_over_l_P:>10.4e}"
        )
        if abs(tau_ms - closed_ms) > 1e-6 * max(tau_ms, 1e-12):
            raise SystemExit(f"τ closure mismatch: {tau_ms} vs {closed_ms}")
        if q.i_max_bits is not None:
            print(f"  Bekenstein I_max ≈ {_fmt(q.i_max_bits)} bit/frame")


if __name__ == "__main__":
    main()
