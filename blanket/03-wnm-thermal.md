# §3 · WNM thermal balance

### §3.0 · Задача

При фиксированном `n_H` (LIC nominal) найти $T$ такое, что **Γ = Λ** (erg cm⁻³ s⁻¹, cgs).

**Не** подставлять наблюдательную 7000 K в солвер.

### §3.1 · Heating Γ

- Cosmic rays: $\zeta_H$ (`wnm_thermal.zeta_H_s-1`).
- UV photoelectric: Habing `G0`, `dust_pe_efficiency`.

### §3.2 · Cooling Λ

Каналы (анalytic Wolfire-order):

- [C II] 158 μm (dominant),
- [O I],
- Lyman-α,
- free-free.

`wnm_thermal.cooling_scale` — **нормировка сил линий** под баланс при LIC `n_H`; это калибровка табличной Λ, **не** input T_LIC.

### §3.3 · H + He

- H: Saha с `n_eff_saha_cm3` (избегает артефакта при очень малых n).
- Photoionization floor / cap из `model_v1`.
- He: approximate He II fraction vs T.

$n_e(T)$ входит в Γ и Λ; решение — bisection / scan на `[T_min_K, T_max_K]`.

Код: `mt_ca.blanket.wnm.wnm_equilibrium_T_K`.

### §3.4 · OPEN

Заменить scalar `cooling_scale` на tabulated Λ(T) (Ferriere/Koyama) — уменьшить единственный fudge.
