"""Probe N_a0 from carrier integers (no optical a0)."""
from __future__ import annotations

import itertools
import math

from mt_ca.si_constants import KAPPA_FCC_1TICK, N12_FCC_CAUSAL_LINKS, SI, hv_bit_budget

kappa = KAPPA_FCC_1TICK
N12 = float(N12_FCC_CAUSAL_LINKS)
Nphi = 13.0
Nhier = 8.0
HV = hv_bit_budget()
N_ring = float(HV.N_ring)
B = float(HV.B_hV)
N_a0_opt = 5.29177210903e-11 / SI.l_P
alpha_c = 7.2973525693e-3
mPe = SI.m_P / SI.m_e_CODATA


def score(val: float) -> tuple[float, float]:
    return abs(val / N_a0_opt - 1.0), val / N_a0_opt


def stack_alpha(n_a0: float) -> float:
    def mapped(a: float) -> float:
        lam = 1.0 / 8.0 + 2.0 * a / math.pi
        return Nphi / (n_a0 * (a**10) * 2.0 * math.sqrt(math.pi * lam))

    a = (Nphi / (n_a0 * math.sqrt(math.pi / 2.0))) ** (1.0 / 11.0)
    for _ in range(80):
        a = 0.5 * a + 0.5 * mapped(a)
    return a


def bare_alpha(n_a0: float) -> float:
    return (Nphi / (n_a0 * math.sqrt(math.pi / 2.0))) ** (1.0 / 11.0)


def main() -> None:
    print("HV", HV)
    print("N_a0_opt", N_a0_opt)
    target_stack = Nphi / (
        2 * math.sqrt(math.pi) * (alpha_c**11) * math.sqrt(1 / 8 + 2 * alpha_c / math.pi)
    )
    print("N_a0 target CODATA-stack", target_stack)

    forms: dict[str, float] = {
        "156**8": 156.0**8,
        "137**8": 137.0**8,
        "(Nphi*N12)**Nhier": (Nphi * N12) ** Nhier,
        "N_ring**Nhier": N_ring**Nhier,
        "N_ring**(Nhier+1)": N_ring ** (Nhier + 1),
        "N_ring**8 * Nphi": N_ring**8 * Nphi,
        "N_ring**8 * N12": N_ring**8 * N12,
        "N_ring**8 * 156": N_ring**8 * 156,
        "N_ring**8 * 137": N_ring**8 * 137,
        "2**81": float(2**81),
        "2**82": float(2**82),
        "N_c * 137": mPe * 137,
        "N_c * 156": mPe * 156,
        "N_c * Nphi": mPe * Nphi,
        "N_c * N12": mPe * N12,
        "N_c * Nhier": mPe * Nhier,
        "N_c * B_hV": mPe * B,
        "N_c * 4pi": mPe * 4 * math.pi,
        "N_c * Nphi*N12/Nhier": mPe * Nphi * N12 / Nhier,
        "N_c * 156/Nphi": mPe * 156 / Nphi,
        "N_c * Nphi**2/N12": mPe * Nphi**2 / N12,
        "N_c * Nphi**2/Nhier": mPe * Nphi**2 / Nhier,
        "N_c0 * 137": kappa * mPe * 137,
        "N_c0 * 156": kappa * mPe * 156,
        "N_c / kappa": mPe / kappa,
        # H as electron Compton × phase budget of brick
        "N_c * N_ring / Nphi": mPe * N_ring / Nphi,
        "N_c * N_ring / N12": mPe * N_ring / N12,
        "N_c * N_ring / Nhier": mPe * N_ring / Nhier,
        "N_c * frac_bits**Nhier": mPe * (HV.frac_bits**Nhier),
        "N_c * 2**frac_bits": mPe * (2**HV.frac_bits),
        "N_c * 2**(frac_bits+mod_bits)": mPe * (2 ** (HV.frac_bits + HV.mod_bits)),
        "N_c * n_states": mPe * float(HV.n_states),
    }

    cands: list[tuple[float, float, float, str]] = []
    for name, val in forms.items():
        rel, ratio = score(float(val))
        cands.append((rel, ratio, float(val), name))

    for a, b, c, d in itertools.product(range(0, 8), range(0, 8), range(0, 6), range(0, 4)):
        val = (Nphi**a) * (N12**b) * (Nhier**c) * (N_ring**d)
        if 1e23 < val < 1e26:
            rel, ratio = score(val)
            if rel < 0.05:
                cands.append((rel, ratio, val, f"13^{a}*12^{b}*8^{c}*512^{d}"))

    cands.sort()
    print("\n=== closest ===")
    for rel, ratio, val, name in cands[:30]:
        print(f"{rel:.6f} ratio={ratio:.6f}  {val:.6e}  {name}")

    print("\n=== alpha from top N_a0 ===")
    for rel, ratio, val, name in cands[:15]:
        ab = bare_alpha(val)
        a_s = stack_alpha(val)
        print(name)
        print(
            f"  bare  inv={1/ab:.6f}  ppm={(ab-alpha_c)/alpha_c*1e6:+.1f}  "
            f"stack inv={1/a_s:.6f} ppm={(a_s-alpha_c)/alpha_c*1e6:+.1f}"
        )


if __name__ == "__main__":
    main()
