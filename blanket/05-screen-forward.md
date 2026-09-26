# §5 · Column screen forward (смежный harness)

**Не геометрия одеяла.** Отдельная цепочка: contrast после ν-damp → τ column → CMB ΔT/T target, VLISM $n_e$ magnetothermal.

Код legacy path: `mt_ca.ism_screen` (`evaluate_ism_screen_v2`).

Общие куски column τ вынесены в **`mt_ca.blanket.column`** (SSOT формулы $N_H(r)$, τ).

Одеяло использует **только** scalar $\tau_0$ из column в якорной точке, без radial map на macro grid.

Verify: `verify_checks/cosmology.py`, `scripts/run_ism_screen_forward_v0.py`.
