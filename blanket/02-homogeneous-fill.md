# §2 · Однородное заполнение МЗВ

### §2.0 · τ

На сетке `(ny, nx)`: $\tau(x,y)=\tau_0$; $\tau_0$ из модели колонки в точке Voyager (`data/ism_constraints_v0.yaml`), без градиента.

### §2.1 · Слои

Толщина `thickness` — число z-срезов. На слой:

$$
\mathbf{z}_{k+1} = \mathbf{z}_{\mathrm{iface}} \cdot e^{-\tau_0 / \mathrm{thickness}}
$$

(спинор ℂ² — затухание по компонентам).

### §2.2 · Карта температуры

$T_{\mathrm{eq}} = T_{\mathrm{WNM}}(n_H)$ из Γ=Λ;

$$
T_{\mathrm{map}} = T_{\mathrm{eq}} \left(1 + c\left(\frac{\Phi_{\mathrm{blanket}}}{\Phi_{\mathrm{ocean,ref}}} - 1\right)\right)
$$

$c$ = `thermal_coupling`. `T_K_warm_nominal` — только в критерии `ok_match_LIC_observation`.

### §2.3 · Масштаб

`pass_blanket.T_lic_K_range` — порядок **10³ K**, не Planck и не CMB.
