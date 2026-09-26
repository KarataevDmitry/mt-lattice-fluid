# §2 · Однородное заполнение МЗВ

### §2.0 · τ

На макро-сетке `(ny, nx)`:

$$
\tau(x,y) = \tau_0 \quad \forall (x,y)
$$

где $\tau_0$ берётся из column model в точке Voyager (или эквивалентный якорь в `data/ism_constraints_v0.yaml`), **без** пространственного градиента.

Код: `tau_uniform_ism_blanket` (`mt_ca.blanket.surface`).

### §2.1 · Геометрия слоёв

Толщина `thickness` — число z-слайсов над интерфейсом. На каждый слой:

$$
\mathbf{z}_{k+1} = \mathbf{z}_{\mathrm{iface}} \cdot e^{-\tau_0 / \mathrm{thickness}}
$$

(attention: spinor ℂ² — attenuation broadcast по компонентам).

### §2.2 · Temperature map

База: $T_{\mathrm{eq}} = T_{\mathrm{WNM}}(n_H)$ из Γ=Λ.

Модуляция:

$$
T_{\mathrm{map}} = T_{\mathrm{eq}} \left(1 + c\left(\frac{\Phi_{\mathrm{blanket}}}{\Phi_{\mathrm{ocean,ref}}} - 1\right)\right)
$$

$c$ = `model_v1.thermal_coupling`; clamp ripple — в коде.

**`lic.T_K_warm_nominal`** используется только в **pass** (`ok_match_LIC_observation`), не в этой формуле.

### §2.3 · Pass (scale)

`pass_blanket.T_lic_K_range` — проверка порядка **10³ K**, не Planck и не CMB.
