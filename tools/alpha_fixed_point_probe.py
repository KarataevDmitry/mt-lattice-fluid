"""Probe: first fixed-point for α_fs from m_e(α) cascade + fixed N_a0 (optical Bohr)."""
from __future__ import annotations

import math

from mt_ca.si_constants import KAPPA_FCC_1TICK, SI

kappa = KAPPA_FCC_1TICK
N_phi = 13.0
N_hier = 8.0
a0 = 5.29177210903e-11  # CODATA Bohr radius [m] — α-independent optical length
N_a0 = a0 / SI.l_P
alpha_codata = 7.2973525693e-3
alpha_pi = SI.alpha_fs
m_P_GeV = (SI.hbar / SI.t_P) / 1.602176634e-10


def cascade(alpha: float) -> tuple[float, float, float, float, float]:
    v = (alpha**N_hier) * m_P_GeV * math.sqrt(2.0 * math.pi)
    m_H_bare = v / 2.0
    delta_lam = alpha / (4.0 * math.pi)
    lam = 1.0 / N_hier + N_hier * delta_lam
    m_H = math.sqrt(2.0 * lam) * v
    m_e = (alpha**2) * m_H / N_phi
    m_e_bare = (alpha**2) * m_H_bare / N_phi
    return m_e, m_e_bare, m_H, v, lam


def map_alpha(alpha: float, *, bare: bool = False) -> float:
    m_e, m_e_bare, *_ = cascade(alpha)
    m = m_e_bare if bare else m_e
    N_c = m_P_GeV / m  # macro Compton hops = m_P/m_e
    return N_c / N_a0


def solve(*, bare: bool = False) -> float:
    lo, hi = 1e-4, 0.05
    flo = map_alpha(lo, bare=bare) - lo
    fhi = map_alpha(hi, bare=bare) - hi
    assert flo * fhi < 0, (flo, fhi)
    for _ in range(100):
        mid = 0.5 * (lo + hi)
        fm = map_alpha(mid, bare=bare) - mid
        if flo * fm <= 0:
            hi, fhi = mid, fm
        else:
            lo, flo = mid, fm
    return 0.5 * (lo + hi)


def main() -> None:
    print("m_P_GeV", m_P_GeV)
    print("N_a0", N_a0)
    print("kappa", kappa)
    print("map(pi)", map_alpha(alpha_pi), "codata", alpha_codata)
    print("SI m_e check", cascade(alpha_pi)[0], SI.electron_mass_row()["m_e_GeV"])

    for bare in (False, True):
        a_fp = solve(bare=bare)
        m_e, m_e_bare, m_H, v, lam = cascade(a_fp)
        m_use = m_e_bare if bare else m_e
        print(f"\nFIXED POINT bare={bare}")
        print(f"  alpha_fp = {a_fp:.14e}")
        print(f"  inv      = {1/a_fp:.10f}")
        print(f"  map      = {map_alpha(a_fp, bare=bare):.14e}")
        print(f"  residual = {abs(map_alpha(a_fp, bare=bare)-a_fp)/a_fp:.3e}")
        print(f"  vs_codata_ppm = {(a_fp-alpha_codata)/alpha_codata*1e6:.2f}")
        print(f"  vs_pi_ppm     = {(a_fp-alpha_pi)/alpha_pi*1e6:.2f}")
        print(f"  m_e* GeV = {m_use:.12e}")
        print(f"  m_H* GeV = {m_H:.8f}  v*={v:.8f}  lam*={lam:.8f}")

    print("\n=== damped iteration w=0.15 ===")
    for seed in [alpha_pi, alpha_codata, 1 / 137, 0.01, 0.001, 0.02]:
        a = seed
        for _ in range(400):
            a = 0.85 * a + 0.15 * map_alpha(a)
        print(f"  seed={seed:.5f} -> {a:.14e} inv={1/a:.8f}")

    a = alpha_pi
    K = map_alpha(a) * (a**10)
    print("\nK_eff~", K, "K^(1/11)~", K ** (1 / 11))


if __name__ == "__main__":
    main()
