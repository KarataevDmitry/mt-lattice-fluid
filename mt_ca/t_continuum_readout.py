"""§4.1.0-T — Theorem T-CR: continuum as forced T-readout (algebra).

No hL→0 on M. Soft Green + small-k spectral match ⇒ smooth T appearance.
"""

from __future__ import annotations

import math
from collections import Counter


def _fcc_nn() -> set[tuple[int, int, int]]:
    neigh: set[tuple[int, int, int]] = set()
    for x, y in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
        neigh.add((x, y, 0))
        neigh.add((x, 0, y))
        neigh.add((0, x, y))
    return neigh


def _hex_nn() -> set[tuple[int, int]]:
    # axial 2D hex / triangular lattice unit steps
    return {(1, 0), (1, -1), (0, -1), (-1, 0), (-1, 1), (0, 1)}


def binomial_spectral_row(*, n_k: int = 256, r_passes: int = 16) -> dict[str, float]:
    """Ŵ=cos²(k/2); after R: match Gaussian with σ²=R/2; small-k rel err."""
    ks = [math.pi * i / (n_k - 1) for i in range(n_k)]
    sig2 = r_passes / 2.0
    sig = math.sqrt(sig2)
    max_rel_030 = 0.0
    max_rel_050 = 0.0
    for k in ks:
        w = math.cos(k / 2.0) ** 2
        w_r = w**r_passes
        g = math.exp(-sig2 * k * k / 2.0)
        if g < 1e-30:
            continue
        rel = abs(w_r - g) / g
        if k * sig < 0.30:
            max_rel_030 = max(max_rel_030, rel)
        if k * sig < 0.50:
            max_rel_050 = max(max_rel_050, rel)
    # identity checks at sample k
    k0 = math.pi / 3.0
    w0 = 0.5 + 0.5 * math.cos(k0)
    # Leading coeff: log(Ŵ_R/G_R) ∼ −R k⁴/96  (§4.1.0-T(A3))
    k_probe = 0.05
    w_r = math.cos(k_probe / 2.0) ** (2 * r_passes)
    g = math.exp(-sig2 * k_probe * k_probe / 2.0)
    log_ratio = math.log(w_r / g)
    leading = -r_passes * (k_probe**4) / 96.0
    return {
        "R": float(r_passes),
        "sigma2": sig2,
        "var_atom": 0.5,  # E[X²] on {-1,0,+1} with [1,2,1]/4
        "multiplier_id_err": abs(w0 - math.cos(k0 / 2.0) ** 2),
        "max_rel_err_k_sigma_lt_0_30": max_rel_030,
        "max_rel_err_k_sigma_lt_0_50": max_rel_050,
        "taylor_leading_R_over_96": abs(log_ratio - leading) / abs(leading),
        "note": "§4.1.0-T(A): cos^{2R}(k/2) ↔ exp(−σ²k²/2), σ²=R/2; log∼−R k⁴/96",
    }


def _depth2_green(neigh: set[tuple]) -> dict[str, float | int]:
    origin = tuple(0 for _ in next(iter(neigh)))
    counts: Counter[tuple] = Counter()
    for u in neigh:
        for d in neigh:
            p = tuple(u[i] + d[i] for i in range(len(u)))
            counts[p] += 1
    n_walks = len(neigh) ** 2
    w0 = counts[origin]
    w_nn = sum(counts[u] for u in neigh)
    w_other = n_walks - w0 - w_nn
    return {
        "n_nn": len(neigh),
        "n_walks": n_walks,
        "w_origin": w0,
        "w_nn_shell": w_nn,
        "w_other": w_other,
        "p_origin": w0 / n_walks,
        "p_nn_shell": w_nn / n_walks,
        "n_endpoints": len(counts),
    }


def fcc_depth2_green_row() -> dict[str, float | int | str]:
    row = _depth2_green(_fcc_nn())
    row["note"] = "§4.1.0-T(B): FCC N₁₂ depth-2 path-Green; w(0)=12/144"
    return row


def hex_depth2_green_row() -> dict[str, float | int | str]:
    row = _depth2_green(_hex_nn())
    row["note"] = "§4.1.0-T(B): hex N₆ depth-2 path-Green; w(0)=6/36"
    return row


def t_continuum_readout_row() -> dict[str, float | int | bool | str]:
    """Bundle for verify — identities that force continuum-looking T."""
    spec = binomial_spectral_row()
    fcc = fcc_depth2_green_row()
    hx = hex_depth2_green_row()
    # path combinatorics: [1,1]/2 ∗ [1,1]/2 = [1,2,1]
    atom = (1, 1)
    conv = (
        atom[0] * atom[0],
        atom[0] * atom[1] + atom[1] * atom[0],
        atom[1] * atom[1],
    )
    return {
        "var_atom": spec["var_atom"],
        "sigma2_R16": spec["sigma2"],
        "multiplier_id_err": spec["multiplier_id_err"],
        "max_rel_err_k_sigma_lt_0_30": spec["max_rel_err_k_sigma_lt_0_30"],
        "max_rel_err_k_sigma_lt_0_50": spec["max_rel_err_k_sigma_lt_0_50"],
        "taylor_leading_R_over_96": spec["taylor_leading_R_over_96"],
        "path_atom_conv": conv,
        "path_atom_is_121": conv == (1, 2, 1),
        "fcc_n_nn": fcc["n_nn"],
        "fcc_n_walks": fcc["n_walks"],
        "fcc_w_origin": fcc["w_origin"],
        "fcc_p_origin": fcc["p_origin"],
        "fcc_w_nn_shell": fcc["w_nn_shell"],
        "hex_n_nn": hx["n_nn"],
        "hex_n_walks": hx["n_walks"],
        "hex_w_origin": hx["w_origin"],
        "hex_p_origin": hx["p_origin"],
        "separable_121_is_not_fcc_law": True,  # documented: different kernel
        "note": "§4.1.0-T: continuum T-readout forced; no hL→0",
    }
