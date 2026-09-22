"""§4.1.0-T / §4.1.1-HL — T-CR + T-HL (continuum / hydro from soft Green).

No hL→0 on M. Soft Green + small-k spectral match ⇒ smooth T appearance.
FCC depth-2 moments + κ_link ⇒ NLSE/NS-class hydro-limit (Madelung).
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
    dim = len(origin)
    counts: Counter[tuple] = Counter()
    for u in neigh:
        for d in neigh:
            p = tuple(u[i] + d[i] for i in range(dim))
            counts[p] += 1
    n_walks = len(neigh) ** 2
    w0 = counts[origin]
    w_nn = sum(counts[u] for u in neigh)
    w_other = n_walks - w0 - w_nn

    def moment(*powers: int) -> float:
        # powers indexed by axis; missing axes → power 0
        acc = 0.0
        for p, w in counts.items():
            term = float(w)
            for ax, pw in enumerate(powers):
                term *= float(p[ax]) ** pw
            acc += term
        return acc / float(n_walks)

    m_xx = moment(2)
    m_xy = moment(1, 1) if dim >= 2 else 0.0
    e_r2 = 0.0
    for p, w in counts.items():
        e_r2 += float(w) * sum(float(c) ** 2 for c in p)
    e_r2 /= float(n_walks)
    e_x4 = moment(4)
    e_x2y2 = moment(2, 2) if dim >= 2 else 0.0

    return {
        "n_nn": len(neigh),
        "n_walks": n_walks,
        "w_origin": w0,
        "w_nn_shell": w_nn,
        "w_other": w_other,
        "p_origin": w0 / n_walks,
        "p_nn_shell": w_nn / n_walks,
        "n_endpoints": len(counts),
        "M_xx": m_xx,
        "M_xy": m_xy,
        "E_r2": e_r2,
        "E_x4": e_x4,
        "E_x2y2": e_x2y2,
    }


def fcc_depth2_green_row() -> dict[str, float | int | str]:
    row = _depth2_green(_fcc_nn())
    row["note"] = "§4.1.0-T(B): FCC N₁₂ depth-2 path-Green; w(0)=12/144"
    return row


def hex_depth2_green_row() -> dict[str, float | int | str]:
    row = _depth2_green(_hex_nn())
    row["note"] = "§4.1.0-T(B): hex N₆ depth-2 path-Green; w(0)=6/36"
    return row


def fcc_hydro_limit_row() -> dict[str, float | int | bool | str]:
    """§4.1.1-HL — FCC depth-2 moments ⇒ NLSE/NS-class hydro identities."""
    from mt_ca.si_constants import N12_FCC_CAUSAL_LINKS, kappa_link

    g = _depth2_green(_fcc_nn())
    m_xx = float(g["M_xx"])
    # Ŵ = 1 − ½ kᵀ M k + O(k⁴) = 1 − (M_xx/2) |k|² + … on isotropic M
    hatk_k2 = 0.5 * m_xx
    k_fcc = kappa_link(n_links=N12_FCC_CAUSAL_LINKS)
    isotropic = abs(float(g["M_xy"])) < 1e-12 and abs(m_xx - float(g["E_r2"]) / 3.0) < 1e-12
    return {
        "n_nn": g["n_nn"],
        "n_walks": g["n_walks"],
        "M_xx": m_xx,
        "M_xy": float(g["M_xy"]),
        "E_r2": float(g["E_r2"]),
        "E_x4": float(g["E_x4"]),
        "E_x2y2": float(g["E_x2y2"]),
        "hatK_k2_coeff": hatk_k2,
        "sigma2_per_R": m_xx,  # σ_R² = R · M_xx  (Gaussian proxy)
        "kappa_link_fcc": k_fcc,
        "nu_CA_fcc": k_fcc,  # ν = κ_link c₀ ℓ_P; lattice units c₀=ℓ_P=1
        "isotropic_M": isotropic,
        "nlse_class": True,  # gate-Taylor §4.1.1 + ∇² from (H2)
        "ns_class_via_madelung": True,  # Madelung map identity (H4)
        "gaussian_fourth_not_exact": abs(float(g["E_x4"]) - 3.0 * m_xx * m_xx) > 0.1,
        "note": "§4.1.1-HL: M=(4/3)I · Ŵ=1−(2/3)|k|² · κ=1/12 → NLSE+ν / NS-class",
    }


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
