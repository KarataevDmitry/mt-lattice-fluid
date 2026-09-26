# Глоссарий · одеяло МЗВ

**Канон имён** для `BLANKET.md` и проверочных прогонов. Код (`apply_ism_blanket`, `T_K_warm_nominal`) не переименовывается без миграции yaml.

| термин | смысл |
|--------|--------|
| **Океан (ST)** | Первая поверхность: `VACUUM_BOIL` / `boil_ocean_spinor_3d` — живая решётка до excitations. SSOT: MODEL + `mt_ca.app`. |
| **Одеяло (МЗВ)** | Вторая поверхность: несколько z-слоёв над интерфейсом с exp(−τ) от однородного τ; macro-T порядка kK. |
| **МЗВ** | Warm neutral medium; здесь — **однородное** заполнение (без «полос ветра» на τ или T). |
| **LIC** | Local Interstellar Cloud; `n_H`, `T_K_warm_nominal` в data — **якорь наблюдения**, не knob в `ism_T_map_K`. |
| **$T_{\mathrm{eq}}$** | Решение Γ=Λ (`wnm_equilibrium_T_K`) при `n_H` из constraints. |
| **$T_{\mathrm{ISM}}$ map** | $T_{\mathrm{eq}} \times (1 + \kappa(\|\Phi\|/\Phi_{\mathrm{ref}} - 1))$ — ripple от sim ℬ. |
| **τ (column)** | Эффективный optical depth screen из $N_H \sigma_{\mathrm{eff}}$; на одеяле — **одно** значение на всю макро-плоскость. |
| **CMB readout** | 2.7 K — **не** целевая температура одеяла в этой гипотезе. |
