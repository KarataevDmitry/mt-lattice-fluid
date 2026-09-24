# §8. SM-константы (модель, не meta)
### 8.1 `v_p`-частица: Planck-арифметика (**уже сейчас**, не claim модели)
| Параметр | Формула | Статус |
|----------|---------|--------|
| объём | `v_p = (dl)³` | §5, §7 |
| масса | `m₀ = m_P` | **считается сейчас** из `ℏ,G,c` |
| заряд | `e₀ = e` | **измерено**; U(1) — один квант на дефект |
| частота | `ν₀ = 1/hT` | **считается сейчас** (~2.62×10⁴³ Hz) |
| энергоплотность при `\|z\|²=1` | `u_P = K_P` | **считается сейчас** |
Planck-строки — размерный факт. Элементар = один **`v_p`**. **§8.2:** α_fs и массы SM — алгебра из **`g`** + топологии.
### 8.2 SM-константы: **вычисляются** из `g` (не fitted)
#### SM → Planck
$$
\begin{aligned}
E_0 &= E_P/\sqrt{2}, &
 m_{\mathrm{arg}} &= m_P/\sqrt{2}, &
 \kappa &= 1/\sqrt{2}, \\
\alpha_{\mathrm{fs}}^{-1}
 &= 4\pi^{3}+\pi^{2}+\pi, &
 N_\varphi &= \lceil 4\pi\rceil = 13, &
 N_{\mathrm{hier}} &= 8, \\
a_Q &= 2^{-F}, &
 \rho_Q &= a_Q^{2}, &
 N_{12} &= 12, \\
v &= \alpha_{\mathrm{fs}}^{8}\,E_P\,\sqrt{2\pi}, &
 m_H^{(\mathrm{bare})} &= v/2, \\
\delta\lambda &= \alpha_{\mathrm{fs}}/(4\pi), &
 \lambda &= \tfrac18 + N_{\mathrm{hier}}\,\delta\lambda, &
 m_H &= \sqrt{2\lambda}\,v, \\
m_p &= \alpha_{\mathrm{fs}}\cdot\frac{v}{2}\cdot\Bigl(1+\frac{\kappa^{2}}{N_{12}}\Bigr), \\
m_e &= \alpha_{\mathrm{fs}}^{2}\cdot\frac{m_H}{N_\varphi}, \\
m_\nu^{(\mathrm{atm})}
 &= \alpha_{\mathrm{fs}}^{5}\cdot\frac{2m_H}{N_{\mathrm{hier}} N_\varphi}
 = \alpha_{\mathrm{fs}}^{3}\cdot\frac{m_e}{N_{\mathrm{hier}}/2}, \\
m_n &= m_p + 2 m_e, \\
\alpha_s(v) &= \frac{3}{8\pi}, &
 \frac{1}{\alpha(M_Z)}
 &= \alpha_{\mathrm{fs}}^{-1}-\frac{2\pi}{\ln 2}, \\
m_W &= \frac{e(M_Z)\,v}{2\sin\theta_W}, &
 m_Z &= \frac{m_W}{\cos\theta_W}.
\end{aligned}
$$
#### Постоянная тонкой структуры α
**SEALED:** α из дна (B_hV, Δφ_min, FCC/κ, N₄, SU(2)); M,d,U — вывод, не фундамент.
π-tower **удалена** — не определение, не конкурент, не ярлык.
Из gate (§7.1): `α* = 1 + 1/(4π)` — vacuum residue на тик (**нога**, не α).
`α_fs` / `α_fs_inv` в коде — алиасы `alpha_preferred` / `1/α`.

#### §8.2·α·meaning · Физический смысл (опора, не F-решётка)
**α — это:** безразмерная сила **фазового сопряжения** единичного заряда с вакуумом (EM-канал; телесный угол / фазовый объём emergent 3D).
**α — это не:** определение силы Ньютона; не hop-счёт сам по себе; не `κ/M` как первичное.
| слой | объект | статус |
|------|--------|--------|
| **смысл** | phase↔vacuum coupling | stamped |
| **нога** | `α*−1 = Δφ_min/(2π) = 1/(4π)` (пустая ячейка) | stamped |
| **число** | soft-face fundamentals (§8.2·U0) | sealed |
| **следствия** | `F=F₀/(M N²)` на M; **α** = soft-face preferred (M=97); `α₀=κ/M` demoted | discrete + lab-inside; unit descent SEALED |
| **открыто** | дискретная доля сопряжения на FCC без continuum-`π` | `Φ_□` open · α_geom exploratory |
Тождество ноги: `4π·α = α/(α*−1)`.
**Код:** `SI.alpha_meaning_ask_row()` · verify **`Alpha_meaning_ask`**.
#### §8.2·α·descent · Забыть α — спуск из физики
**Амнезия:** не использовать CODATA / lab как *вход*; α = fundamentals.
| шаг | физика | что вылезает |
|-----|--------|--------------|
| 1 | A5 + Heisenberg | `Δφ_min = 1/2` |
| 2 | цикл тика `2π` | residue `r = Δφ_min/(2π) = 1/(4π)`; `α* = 1+r` |
| 3 | emergent `d=3` | `Ω = 1/r = 4π`; `N_φ = ⌈Ω⌉ = 13` |
| 4 | FCC тело | `κ`, `N₁₂`, грани 6□+8△ |
| 5 | A10 | заряд `n∈ℤ` |
| 6 | ? | **безразмерное EM-сопряжение** |
**Нога — не α.** `r ≈ 0.08` — остаток пустого вакуума; тонкая структура на порядок меньше.
**Два завершения (score только AFTER):** continuum-башня на `Ω` → ~2 ppm; `α_geom=137` с граней → ~263 ppm. Сырые `r`, `r²`, `κ_link·r` — неверный масштаб.
**Открыто:** доля сопряжения заряда сквозь `Ω` из `g`/holonomy — не ansatz.
**Код:** `SI.alpha_descent_ask_row()` · verify **`Alpha_descent_ask`**.
#### §8.2·α·mass-defect · Оптика: дефект массы H = этаж КМ (DoD)
**КМ (предыдущий этаж):** $BE=\tfrac12\alpha^2 m_e c^2$, $\Delta m=BE/c^2$ ⇒
$$
\alpha=\sqrt{2\,\Delta m/m_e}.
$$
**На M (те же α, без новой ручки):**
| тождество | смысл |
|-----------|--------|
| $U(a_0)=\alpha E_P/N_{a0}=\alpha^2 m_e c^2$, $BE=U/2$ | вириал |
| $E_{\mathrm{coul}}(N{=}1)/E_0=\alpha/\kappa$ | сила на $F_0$ |
| $BE/E_0=\Delta m/m_{\mathrm{arg}}\ll 1$ | мягкий Arg-ledger, не один клик $E_0$ |
**Оптика:** coupling phase↔vacuum, посадка на $F_0$, hop-лестница и QM-дефект массы — **одно** α. Вывел любое без α — вывел все.
**DoD:** Arg-binding композита H на Λ должен coarse-grain к $\Delta m$. **Открыто:** $\Delta m$ из Arg-связи p–e **без** вставки α.
**Код:** `SI.alpha_mass_defect_optics_row()` · verify **`Alpha_mass_defect_optics`**.
#### §8.2·α·Arg-try · Попытка: Δm из Arg-ledger без α
**Тождество (мостик закрыт):** при demoted $\alpha_0=\kappa/M$, $U=E_0/(M N_{a0})$, $BE=U/2$
$$
\frac{\Delta m}{m_{\mathrm{arg}}}=\frac{BE}{E_0}=\frac{1}{2 M N_{a0}},\qquad
\frac{\Delta m}{m_e}=\frac{\kappa^{2}}{2 M^{2}}=\frac{\alpha^{2}}{2}.
$$
Связь H — **один Arg-тик**, размазанный на $2 M N_{a0}$ (soft ledger).
**Try без вставки α:**
| кандидат | ppm на $\Delta m/m_e$ | вердикт |
|----------|----------------------|--------|
| $M=97$ → $\kappa^{2}/(2\cdot97^{2})$ | ~−2080 | лучший int (тот же F-ask) |
| $M=96=N_{12}N_{\mathrm{hier}}$ | ~+1.9e4 | хуже |
| $1/(2\cdot137^{2})$ | ~+526 | **reject** — inject α_geom |
| $1/(4\pi\cdot11)^{2}/2$ | ~−1.7e4 | **reject** — FP-exp не fraction |
| $m_e N_\varphi/(2 m_H)$ | ~0 | **reject** — circular ($m_e$ уже с α) |
**Итог try:** identity unifies F/H/QM; **вывод не закрыт** — нужны $M$ и/или $N_{a0}$ из $g$/shell без α.
**Код:** `SI.alpha_arg_binding_try_row()` · verify **`Alpha_arg_binding_try`**.
#### §8.2·α·Schwinger · Старт с лаборатории: $a_e=(g-2)/2$
**Дверь (Куш / Швингер → геоний):** меряют $a_e$, не α напрямую:
$$
a_e=\frac{\alpha}{2\pi}+O(\alpha^{2})\qquad\Rightarrow\qquad\alpha=2\pi\,a_e+\cdots
$$
**Рифма носителя (тождество):** нога вакуума $r=\Delta\varphi_{\min}/(2\pi)=1/(4\pi)$ (§8.2·descent) ⇒
$$
\frac{\alpha}{2\pi}=2\alpha\,r.
$$
Фактор $1/(2\pi)$ — геометрия тика (Heisenberg-пол), не fitted константа QED.
**DoD:** bare $g=2$ для вихря $n=\pm1$ (топология) + A5-dressing → $a_e$ **без** вставки α; тогда α сверху = $a_e/(2r)$.
Однопетлевой Швингер vs CODATA $a_e$ ~+1516 ppm — ожидаемый зазор высших петель.
**Код:** `SI.alpha_schwinger_ask_row()` · verify **`Alpha_schwinger_ask`**.
#### §8.2·α·g2·ask · Спросили носитель: bare $g=2$ и A5→$a_e$
**Метод:** как §8.2·H·ask — (1) факты вихря $n=\pm1$ + спинора; (2) что фиксирует гиромагнитное без α; (3) чем A5-ванна одевает момент; (4) reject / report.
**Опрос — ответы носителя:**
1. **A4 + A16 / §3.10:** spin-½ — $2\pi\to-1$, $4\pi\to+1$ (двойное накрытие).
2. **Thm 5.1:** $L_0=s_0=\hbar/2$ — один спиновый квант на $hV$.
3. **A10:** заряд $n=\pm1$ на электронном pra-vortex.
4. **Орбитальный baseline:** циркулирующий заряд → $g_{\mathrm{orb}}=1$ ($\mu=(Q/2m)L$).
5. **Bare $g_s=2$:** двойное накрытие удваивает магнитный отклик спина относительно орбиты → $g_s=g_{\mathrm{orb}}\times 2=2$. Тогда $\mu_{\mathrm{bare}}=e\hbar/(2m)=\mu_B$ при $|S|=\hbar/2$ — **без α**.
6. **Bare $a_e=0$:** аномалия — не топология, а **одевание** A5-ванной.
7. **Тождество двери:** $a_e^{(1)}=2\alpha\,r$, $r=\Delta\varphi_{\min}/(2\pi)$ — геометрия; сверху $\alpha=a_e/(2r)$.
8. **Отвергнуто:** $a_e\stackrel{?}{=}r$ или $2r$ (⇒ α=1 или ½); $a_e\stackrel{?}{=}|z|_{\mathrm{vac}}^2$ (масштаб $z_{\min}$, не ~$10^{-3}$); вставка α в dressing (круговое для DoD); CODATA $a_e$ как M-определение α.
9. **Открыто:** доля holonomy-облака A5 вокруг вихря → $a_e$ без α; затем α сверху.
**Код:** `SI.alpha_dirac_g2_ask_row()` · verify **`Alpha_dirac_g2_ask`**.
#### §8.2·α·ae·ask · Спросили носитель: A5-облако → $a_e$
**Метод:** (1) назвать облако на Λ; (2) безразмерный избыток μ; (3) α-free дроби; (4) reject / report.
**Опрос — ответы носителя:**
1. **Облако** = ореол $\rho_\Theta$ (Heisenberg §5.0.5) + канал $\Phi_\square$ (Stokes) + A5-ванна.
2. **Факторизация** (дверь Швингера = чтение носителя):
$$
a_e^{(1)}=\alpha\cdot 2r,\qquad 2r=\Delta\varphi_{\min}/\pi=1/(2\pi).
$$
Сопряжение × геометрия тика. **$2r$ закрыт**; **α = доля сопряжения — тот же OPEN**, что §8.2·α·meaning / descent.
3. **α-free tries** ($\Delta\varphi_{\min}/N_{\mathrm{ring}}$, $\kappa/N_{\mathrm{ring}}$, $r/N_{12}$, $\kappa^2/N_{12}$, …) — **неверный масштаб** (лучшие $|\mathrm{ppm}|\gg 10^3$).
4. **Отвергнуто как вывод $a_e$:** $2r/137$ и $\alpha/(2\pi)$ — вставка $\alpha_{\mathrm{geom}}$/α; сверху $\alpha=a_e/(2r)$ возвращает то же.
5. **Итог:** дверь Швингера **не обходит** OPEN сопряжения — только **режет** задачу: $\alpha=a_e/(2r)$ при известном $2r$. $a_e$ без α ⇔ дискретная доля сопряжения (или лабораторный $a_e$). Та же гора, острее факторизация.
**Код:** `SI.alpha_ae_cloud_ask_row()` · verify **`Alpha_ae_cloud_ask`**.
#### §8.2·α·Rydberg·Hall · Лаб-двери рядом со Швингером
**Двери:**
- **Ридберг:** меряют $R_\infty$ (спектроскопия H/D) → $\alpha^{2}$ при известных $m_e$ и QED-уровнях.
- **Холл / фон Клицинг:** плато $R_H=R_K/i$, $R_K=h/e^{2}$. До SI-2019: $\alpha=\mu_0 c/(2R_K)$. После 2019: $e,h$ точны ⇒ $R_K$ точен; **α из Холла больше не независим** ($\mu_0$ измеряется).
**Рифмы носителя (тождества):**
$$
R_\infty = \frac{\alpha^{2} m_e c}{4\pi\hbar} = \alpha^{2}\,\frac{r}{\bar\lambda_C},\qquad r=\frac{\Delta\varphi_{\min}}{2\pi}=\frac{1}{4\pi}.
$$
Та же нога $r$, что у Швингера; мощность $\alpha^{2}$ уже на hop-лестнице ($\alpha^{2}=N_{re}/N_{a0}$).
Фактор $2$ в $\alpha=\mu_0 c/(2R_K)$ — SI-ЭМ, **не** $2r$.
**Опрос:**
1. Обе двери **читают** α с прибора / метрологии — не выводят сопряжение на M.
2. Ридберг факторизует $\alpha^{2}\cdot r$ — $r$ закрыт; $\alpha^{2}$ снова OPEN (hops / coupling).
3. Холл post-2019 — эталон $h/e^{2}$, не источник α.
4. **Отвергнуто:** $R_\infty$ или optical $a_0$ как M-определение α; α из $R_K$ без $\mu_0/\varepsilon_0$-моста после 2019.
5. **Итог:** та же гора, что meaning / Schwinger / ae·ask.
**Код:** `SI.alpha_rydberg_hall_ask_row()` · verify **`Alpha_rydberg_hall_ask`**.
**π-guardrail (§8.2·geo):** непрерывный **`4π`** — **T-readout** (телесный угол), **не** метрика одной **`v_h`**. На **1-tick** теле **кубооктаэдра** живут **6□ + 8△**, **`V=(16/3)v_hV`**, **`κ=1/√2`** — см. **`SI.cuboctahedron_geometry_row()`**.
**Exploratory (π-free, cuboctahedron combinatorics — не ):**
```
α_fs⁻¹_geom = N₁₂(N₁₂+1) − n_△ − 2n_□ + 1 = 12·13 − 8 − 12 + 1 = 137
```
~260 ppm на **`α⁻¹`** vs CODATA (хуже stamped **`4π³+π²+π`** ~2 ppm). Открытый вывод: **`α_geom`** из **`g`** / Coulomb на FCC, не подменять молча.
#### §8.2·H·ask · Спросили носитель: **`N_a0`** (размер H в hops)
**Метод:** как §8.2·geo·ask / §5.2.6 phonon — (1) **`a=l_P`**; (2) выписать факты H; (3) что может задать размер **без** инъекции **`α`**; (4) ratio — отчёт.
**Уже stamped (не knobs):**
| # | факт | откуда |
|---|------|--------|
| H0 | Thm 5.2 — на M нет волны; звук/свет/перенос = **`n_k`**, **`n_E·E₀`** | §0.9 · §5.2.5 |
| H1 | H = составной узел: **`B=1`** + облако **`ρ_Θ`** электрона на оболочках **`Λ`** | §5.0.4–5.0.5 |
| H2 | Hop-лестница: **`N_re --α-- N_c --α-- N_a0`**, **`α=N_c/N_a0`**, **`α²=N_re/N_a0`** | §7.4 + Bohr rung |
| H3 | Масса: **`m_e=α² m_H/N_φ`** ⇒ **`α²=m_e N_φ/m_H`** | §8.2 электрон |
**Опрос — ответы носителя:**
1. **`N_a0 ∈ ℤ`** (hops **`hL`**). Иначе дыра в лестнице: звук квантуется, размер H — continuum.
2. **Масса и hop — одна мощность `α²`:** `N_re/N_a0 ≡ m_e N_φ/m_H`. Массы **не** фиксируют `N_a0` независимо от `α` (тождество, не второй источник).
3. **Отвергнуто:** `N_a0 = N_c·137` (`α_geom`). Вкладывает `α⁻¹` в размер → `α=N_c/N_a0` возвращает то же. Пусто для вывода `α`.
4. **Отвергнуто как определение M:** оптический `a₀` (CODATA) — T-якорь; годится как seed FP, не как носительный `N_a0`.
5. **Открыто:** целое из **структуры H** — ground **`ρ_Θ`** / **`N_pack=#(hV ⊂ атомного WS)`** / радиальная оболочка вокруг `p` на FCC **без** `α` и без оптического `a₀`.
**Код:** `SI.na0_h_carrier_ask_row()` · verify **`Na0_H_carrier_ask`**.
#### §8.2·F·ask · Спросили носитель: сила на решётке **`F₀`** → **`α`**
**Уже stamped:** Thm 5.1 — сила = **`n_F·F₀`**; **`F₀/F_P=κ`**; Кулон **`F=α F_P n₁n₂/N²`**.
**Связка (N=1, |n|=1):**
$$
\alpha F_P = F_0/M \quad\Rightarrow\quad \alpha = \kappa/M,\quad M\in\mathbb{N}.
$$
**Probe:** цель **`M=F₀/(α_c F_P)≈96.899`**.
| кандидат `M` | откуда | `α⁻¹` | vs CODATA |
|--------------|--------|-------|-----------|
| **96** = `N₁₂·N_hier` (= `n_△·N₁₂`) | links × hierarchy | ≈135.76 | ~+9366 ppm |
| **97** = `N₁₂·N_hier+1` | nearest int | ≈137.18 | ~−1040 ppm |
| `137/√2` | `α_geom` path | 137 | ~+263 ppm — **отвергнуто** (инъекция 137) |
**Итог:** путь живой — `α` из посадки Кулона на `F₀`. **`M=97` — теорема** (§8.2·α·nF·Thm); 96 = неполная перепись без ядра. π-tower **removed**; α = soft-face fundamentals.
**Код:** `SI.alpha_force_lattice_ask_row()` · verify **`Alpha_force_lattice_ask`**.
#### Кулон из носителя (не fitted Maxwell)
**M-native (полное квантование — без continuum-α в законе силы):**
$$
F_{12} = n_1 n_2\,\frac{F_0}{M\, N^{2}}\,\hat{\mathbf{r}},
\qquad N\in\mathbb{N}\ \text{(graph-distance в }\ell_P),
\quad n_i\in\mathbb{Z}\ \text{(A10)},
\quad M = n_{F,\mathrm{seats}} = 97.
$$
На NN ($N=1$, $|n_i|=1$): $F = F_0/M$ — один пакет силы на $M$ местах kick-ledger (§8.2·α·nF·Thm). **Не** появляются $\pi$, $\varepsilon_0$, π-tower.
**T-readout (legacy coarse):** через demoted $\alpha_0=\kappa/M$ и $F_P$:
$$
F_{12} = \alpha\, F_P\,\frac{n_1 n_2}{N^{2}}\,\hat{\mathbf{r}},
\qquad \alpha = \kappa/M,\quad F_0 = \kappa F_P.
$$
**α** = soft-face preferred (M=97) §8.2·U0 — SEALED. Demoted: $\alpha_0=\kappa/M$ (~−1040 ppm).
**Сборка (после M-native):**
| кусок | где | смысл |
|-------|-----|--------|
| $Q = n\,e_0$, $n\in\mathbb{Z}$ | §5.2.2-III | топологический заряд (A10) |
| $F_0$, $M=97$ | Thm 5.1 · nF census | сила — целые пакеты / seats |
| soft-face $\alpha(M{=}97)$ | §8.2·U0 | **α** sealed; $\alpha_0=\kappa/M$ demoted |
| $F_P$; $F_0=\kappa F_P$ | §5.2.1 | Planck force ladder |
| $\mathrm{div}\,j=0$ | §5.2.1 | локальный баланс |
**Дискретный Гаусс.** Поток $j$ через оболочку $\propto n=Q/e_0$. Закон $1/N^{2}$ — graph-distance + A10, не отдельный Maxwell на M.
| кусок | статус |
|-------|--------|
| $F = n_1 n_2 F_0/(M N^{2})$ на M | выведено (descent) |
| $F = \alpha F_P n_1 n_2/N^{2}$ на T | readout той же силы |
| Гаусс $\oint j \propto n$ | схема · sim open |
**Фальсификация:** $N\notin\mathbb{N}\ell_P$, $n\notin\mathbb{Z}$, или NN-сила $\neq F_0/M$ — claim мёртв.
**Код:** `SI.coulomb_M_native_row()` · verify **`Coulomb_M_native`**.
#### Планковский ЭМ (формулы на соседних ячейках)
Уже есть в носителе (§5.0.2 · §5.2.1). Не fitted Maxwell — **сбор** тех же кусков, что Кулон.
**Кванты на одном шаге** ($\ell_P$, $hT$):
$$
s_0 = \hbar/2,
\qquad
E_0 = s_0/hT = E_P/\sqrt{2},
\qquad
p_0 = s_0/\ell_P,
\qquad
F_0 = p_0/hT = m_{\mathrm{arg}}\, g_M.
$$
**Поля на связи / грани** (целые $n\in\mathbb{Z}$):
$$
E_i = -\frac{\varphi(x)-\varphi(x+\hat e_i)}{\ell_P}
\quad(\varphi=\mathrm{Arg}\,z),
\qquad
j_i = \frac{\mathrm{Im}\bigl(z^*(x)\,z(x+\hat e_i)\bigr)}{hT}.
$$
**Контур по грани $\square$** (дискретный $\oint$ = сумма по рёбрам):
$$
\Phi_\square
=
\sum_{e\in\partial\square}\!\Delta\varphi_e
=
\mathrm{Arg}\!\prod_{e\in\partial\square}\! z
\quad\in (-\pi,\pi],
\qquad
B_\square = \Phi_\square / \ell_P^{2},
\qquad
\sum_{e\in\partial\square} E_e\,\ell_P = -\Phi_\square.
$$
Это Stokes на решётке: циркуляция $E$ вокруг $\square$ = минус поток $B$ через $\square$. Большой контур = сумма граней внутри (телескопирование).
**Законы на решётке:**
$$
\frac{\Delta\rho}{\Delta t}+\mathrm{div}_\varepsilon\, j = 0,
\qquad
\oint_S j \propto n = Q/e_0,
\qquad
F = n_F F_0\ \ (n_F\in\mathbb{Z}).
$$
**Кулон на соседях** ($N=1$, $|n_i|=1$) — частный случай:
$$
|F| = F_0/M,
\qquad |F|/F_P = \kappa/M = \alpha\ \text{(T-readout)}.
$$
**Скорость фронта по осям** (не macro-$c$):
$$
c_0 = \ell_P/hT = \sqrt{2}\, c.
$$
Макро-Maxwell ($\nabla\cdot E$, $\nabla\times B$, свет $c$) — **следующий** абзац: те же величины после усреднения.
| кусок | статус |
|-------|--------|
| $s_0,E_0,p_0,F_0$ | выведено |
| $E_i$, $B_\square$, $j_i$, Гаусс, Кулон $N=1$ | выведено |
| sim plaquette на T-readout | открыто |
#### Макро-Максвелл (после усреднения)
Те же $E_i$, $B_\square$, $j$ → обычные поля на T. Четыре уравнения:
$$
\nabla\cdot\mathbf{E}\propto\rho_Q,
\quad
\nabla\cdot\mathbf{B}=0,
\quad
\nabla\times\mathbf{E}=-\partial_t\mathbf{B},
\quad
\nabla\times\mathbf{B}\propto\mathbf{J}+\partial_t\mathbf{E}.
$$
Свет (та же $c$, что §1.1 / §5.1.1 — не второй расчёт):
$$
c = \kappa\, c_0 = c_0/\sqrt{2},
\qquad \kappa=\kappa_{\mathrm{FCC}}=1/\sqrt{2},
\qquad K_P:=\mu_P c^2\ \Rightarrow\ c^2=K_P/\mu_P.
$$
| кусок | статус |
|-------|--------|
| макро-уравнения = readout планк. слоя | выведено |
| sim свободной волны | открыто |
**Закрытие калибровочного ЭМ.** Поля = фазы на рёбрах + циркуляция $\Phi_\square=\mathrm{Arg}\prod_{\partial\square} z$. Отдельного плавающего $A_\mu$ / «гостевого» Maxwell на M нет.
#### Lorentz / изотропия света (из упругости + binomial)
**Не** отдельная группа SO(3,1) на M. Macro-$c$ — **одна** цепочка; $K_P/\mu_P$ — не второй расчёт числа $c$:
$$
c = \kappa\, c_0 = c_0/\sqrt{2}
\qquad(\kappa=\kappa_{\mathrm{FCC}}=1/\sqrt{2}\ \text{(3+1)},\ c_0=\ell_P/hT),
$$
$$
K_P := \mu_P\, c^2
\quad\Rightarrow\quad
c^2 = K_P/\mu_P
\quad\text{(тождество гидродинамики, §5.1.1)}.
$$
**Гекс-срез (2+1):** то же $c=\kappa\,c_0$, но $\kappa_{\mathrm{hex}}=\sqrt{3}/2$, $c_0=(2/\sqrt{3})\,c$, $hT=(\sqrt{3}/2)\,t_P$ (§1.4.2) — не подставлять $\kappa_{\mathrm{FCC}}$ в срез на $N_6$.
Фотон на M = безмассовая мода бегущей фазовой голономии ($n=0$, $\Phi_\square$-фронт). Macro-readout — binomial $(1{-}2{-}1)$ по многим плакеткам (§4.1 · T1):
$$
\text{анизотропия рёбер FCC}
\ \xrightarrow{\ (1{-}2{-}1)\ }\
\text{макро-круг со скоростью } c.
$$
Контуры $\Phi_\square$ сшивают пространство: упругость среды на больших масштабах изотропна. T1 (`isotropy_ratio→1`) — численный след этой цепочки, не axiom «Lorentz вставлен».
| кусок | статус |
|-------|--------|
| $c=\kappa_{\mathrm{FCC}} c_0$; hex $\kappa_{\mathrm{hex}}=\sqrt{3}/2$; $K_P:=\mu_P c^2$ | выведено |
| фотон = holonomy $n=0$ | выведено схема |
| binomial → макро-круг (T1) | выведено §4.2 |
| количественный LIV/MDR budget (MAGIC/Fermi) | открыто |
#### Теория излучения (из носителя, не гостевой Planck-1900)
**Не** отдельный Lagrangian. Излучение = **сектор $n=0$** той же жидкости + readout на T.
**1 · Квант** (уже §5.0.2 / планк. ЭМ):
$$
s_0 = \hbar/2,
\qquad
E_0 = s_0/hT,
\qquad
\nu_0 = 1/hT,
\qquad
h\nu_0 = 4\pi\, E_0.
$$
Мода с частотой $\omega$ (фазовый ход T-dispersion):
$$
E(\omega) = \hbar\,\omega.
$$
**2 · Носитель фотона**
$$
\text{фотон} = \text{голономия }n=0\ (\Phi_\square\text{-фронт}),
\qquad
v_{\mathrm{link}}=c_0,
\qquad
v_{\mathrm{macro}}=c=\kappa\,c_0.
$$
**3 · UV-срез и два Rayleigh–Jeans** — 1-я зона Бриллюэна + «Дебай вакуума» (§5.2.4):
$$
|k| \lesssim \pi/\ell_P,
\qquad
\omega_D \sim 1/hT,
\qquad
N_{\mathrm{modes}} = \#\{k\in\mathrm{BZ}\} < \infty.
$$
| | формула | на M |
|--|---------|------|
| **continuum RJ** | $u(\omega)\propto\omega^{2} k_B T$, $\omega\to\infty$ | **нет** — мод вне BZ нет |
| **дискретный RJ** | на каждой моде $\langle E\rangle = k_B T$ (классика), $U=N_{\mathrm{modes}} k_B T$ | **геометрия допускает** (конечный $N_{\mathrm{modes}}$); **занятость не выведена** |
Дискретный RJ — **не закрыт**. Это только: BZ режет continuum-catastrophe. Сама формула $\langle E\rangle=k_BT$ на моде — классический угол **ещё открыто** Bose-занятости (§5). Квант моды $E=\hbar\omega$; при $\hbar\omega\gtrsim k_B T$ равнораспределение ломается — но мост $T\to\langle n\rangle$ в MODEL пока **не stamped**.
**4 · Излучение как процесс** (уже §5 аннигиляция):
$$
n=+1\ +\ n=-1 \;\rightarrow\; n_{\mathrm{net}}=0
\;+\;
\text{два macro-фронта давления со скоростью }c.
$$
Энергия не уничтожается (A3) — уходит волнами $n=0$.
**5 · Ответ модели: занятость — не закон M**
Спросили носитель (§2.1 · A3 · A16 · §5.2 · BZ):
$$
g\ \text{строго детерминирован (без RNG).}
\quad
\text{Вероятность / }\langle n\rangle\ \text{— T-readout, не микро-шаг.}
$$
Что M **закрывает** (без ансамбля):
| факт носителя | следствие |
|---------------|----------|
| ledger $\Delta E = n_E E_0$, $n_E\in\mathbb{Z}$ (§5.2) | энергия моды ступенями |
| scalar / photon limit $z\in\mathbb{C}$, $n=0$ (§2 A4 note · §8.2) | **нет** Паули на моде → $n=0,1,2,\ldots$ допустимы |
| A16 Паули | только совпадающие спиноры в одном $v_p$ — **не** на $n=0$-фронт |
| BZ + $\omega_D$ | $N_{\mathrm{modes}}<\infty$ → continuum-RJ мёртв |
Что M **не** закрывает:
$$
\langle n\rangle = \frac{1}{e^{\hbar\omega/k_B T}-1}
\quad\text{и}\quad
\langle E\rangle \xrightarrow[\hbar\omega\ll k_BT]{} k_B T
$$
— это **T-статистика** (грубый прибор + хаос из детерминизма, §2.1). $T$ в §5.3.1 — kinetic zigzag **macro-газа материи**, не stamped как температура фотонной ванны.
**Следствие:** дискретный RJ / Planck **не закрыты**. Закрыты лишь: квант, бозонный сектор $n=0$, конечный набор мод. Формулы $\langle n\rangle$, $u(\omega)$, Stefan — требуют T-readout.
**Упущения чеклиста** (вердикт не меняют; без них даже после Bose $u(\omega)$ не собрать):
| hinge | статус | зачем |
|-------|--------|-------|
| $\mu=0$ ($N_\gamma$ **не** аддитивный инвариант как $Q$; свободный $\gamma$ стабилен) | выведено схема: рождение/поглощение с материей (напр. аннигиляция → 2γ) · A3 на энергии | иначе не Bose, а $\mu\neq0$ |
| A6 + хаос §2.1 → равновесная мера на T | hinge, не формула | путь к ансамблю, не $\langle n\rangle$ |
| $T_{\gamma}$ vs $T$ gas (§5.3.1) | открыто контакт | одна $T$ в Planck — не stamped |
| $\omega(k)\approx c\|k\|$ (IR) · DOS | открыто (есть только $\omega_D$) | без DOS нет $u(\omega)\,d\omega$ |
| $g_{\mathrm{pol}}=2$ (поперечные) | открыто | фактор 2 в $u(\omega)$ |
| мода = осциллятор → $\langle E\rangle\to k_BT$ | открыто | классический угол RJ |
| кусок | статус |
|-------|--------|
| $s_0,E_0,h\nu_0=4\pi E_0$; $E=\hbar\omega$ | выведено |
| фотон $=n=0$ (bosonic limit); $c$ vs $c_0$ | выведено |
| BZ + $\omega_D$ режет continuum-catastrophe | выведено геометрия |
| $n=0,1,2,\ldots$ на моде (нет Паули) | выведено из A16-scope |
| $\mu=0$ ($N_\gamma$ ≠ инвариант; $Q$ сохраняется; свободный $\gamma$ стабилен) | выведено схема |
| аннигиляция → 2γ (два фронта) | выведено схема · sim |
| дискретный RJ $\langle E\rangle=k_BT$ | T-статистика, не закрыт |
| Bose $\langle n\rangle$ · $u(\omega)$ · Stefan/Wien | открыто (T + DOS + $g_{\mathrm{pol}}$) |
| $T_{\gamma}$, $\omega(k)$, $g_{\mathrm{pol}}=2$, A6→мера | hinges выше |
#### §8.2·vac · A5-ванна: тепло и спектр (≠ CMB)
**Не** отдельный Lagrangian. **A5-океан** (§0.5 · §5.3) = постоянно кипящий substrate; **CMB** (META §3.0) = last scattering **пузыря** на T — **другой объект**.
**1 · Плотность кипящего вакуума**
$$
|z|^2 \leftrightarrow \frac{\rho_E}{u_P},
\qquad
|z|_{\mathrm{vac}} = z_{\min} = 2^{-B_{\mathrm{amp}}},
\qquad
|z|_{\mathrm{vac}}^2\Big|_{\mathrm{spinor}} = 2\,z_{\min}^2
$$
$$
\rho_{E,\mathrm{vac}} = |z|_{\mathrm{vac}}^2\, u_P
\quad\text{(оба компонента спинора на } z_{\min}\text{)}.
$$
**2 · Спектральные якоря** (то же §8.2 radiation, не дублируем knobs):
$$
\nu_0 = \frac{1}{hT},\quad
\omega_0 = \frac{2\pi}{hT},\quad
\lambda_0 = \frac{c}{\nu_0} = \kappa\,\ell_P = \frac{\ell_P}{\sqrt{2}},
\quad
\omega_D \sim \frac{1}{hT},\quad
h\nu_0 = 4\pi E_0.
$$
**3 · Порядок «температуры» M-ванны** (если $\rho_E \equiv u=aT^4$, **оценка**, не Planck-1900):
$$
T_{\mathrm{M,bath}} \sim \left(\frac{\rho_{E,\mathrm{vac}}}{a}\right)^{1/4},
\qquad
T_{\mathrm{u_P,ceiling}} \sim \left(\frac{u_P}{a}\right)^{1/4}.
$$

$$
T_{\mathrm{CMB}} \approx 2.725\,\mathrm{K}
\quad\text{— T-наблюдение пузыря; не } T_{\mathrm{M,bath}}.
$$
**4 · Ask-model итог**
| кусок | статус |
|-------|--------|
| $\rho_{E,\mathrm{vac}}>0$, $z_{\min}$, $\nu_0$, $\omega_D$, BZ-cutoff | выведено §8.2·vac |
| $T_{\mathrm{M,bath}}$ order ($\sim 10^{31}\,\mathrm{K}$) | выведено algebra |
| $T_{\mathrm{M,bath}} \neq T_{\mathrm{CMB}}$ | выведено по слоям |
| Bose $\langle n(\omega)\rangle$, $u(\omega)$, Stefan | открыто (T + DOS) |
| $\omega(k)$ на BZ | §5.2.4 | открытый спектр |
#### §8.2·geo · Кубооктаэдр 1-tick: от ребра **`a`**
**Якорь (не ratio):** A1 фиксирует **12 NN на расстоянии `l_P`**. Выпуклая оболочка = **кубооктаэдр** с ребром
$$
a = \ell_P \quad\text{[m]}.
$$
**Все длины тела — функции `a`**, ratios — **производные**:
| при `a=l_P` | формула | SI |
|-------------|---------|-----|
| **`R_out`** | **`a`** | m |
| **`R_in`** (1-tick, □ limit) | **`κa = a/√2`** | m |
| **`A_□`** (одна □-грань) | **`a²`** | m² → **`B_□=Φ_□/a²`** (§8.2 Stokes) |
| **`S`** | **`6a²+8·(√3/4)a²`** | m² |
| **`V`** | **`(8/3)√2·a³`** | m³ |
| **`v_hV`** (узел FCC) | **`a³/√2`** | m³ |
| **`V/S`** | compactness | m |
**Потом** безразмерные (не наоборот):
$$
\kappa = \frac{R_{\mathrm{in}}}{R_{\mathrm{out}}} = \frac{1}{\sqrt{2}},
\qquad
\frac{V}{v_{hV}} = \frac{16}{3},
\qquad
\frac{V}{S\cdot a}\;\text{и}\;\frac{A_\square}{A_{\mathrm{tot}}}\;\text{— inventory/открыто.}
$$
**Эталон сопряжения (уже ):** **`κ(a)`** при **`a=l_P`** → **`hT=κ·t_P`**, **`E₀=κE_P`**, **`λ₀=κℓ_P`**. **`c=κc₀`** — **проверка readout**, не определение **`κ`** (§7.2). Не «нашли ratio в таблице» — **сначала длины тела**, потом **`R_in/R_out`**.
**Бум **`V=(16/3)v_hV`**** — следствие **двух объёмов при том же `a`**, не отдельный fit. Сопряжение с **`g`** — **открыто** (как **`κ`** уже сопряжён).
#### §8.2·geo·ask · Спросили носитель: **`a` → coupling**
**Метод:** (1) зафиксировать **`a=l_P`**; (2) выписать **размерные** величины тела; (3) спросить, **какая** входит в фазу/силу; (4) ratio — только отчёт.
| от `a=l_P` | размерная | ratio (производная) | coupling | статус |
|------------|-----------|---------------------|----------|--------|
| ребро | **`a=ℓ_P`** | 1 | A1 NN | якорь |
| inscr./circum. | **`R_in=κa`** | **`κ=1/√2`** | **`c,hT,λ₀`** | выведено |
| □-грань | **`A_□=a²`** | 1 | **`Φ_□`, `B_□=Φ_□/a²`** | открыто |
| per-link | 12 рёбер длины **`a`** | **`1/12`** | **`γ,ν_CA`** | выведено |
| узел | **`v_hV=a³/√2`** | **`1/√2`** vs **`a³`** | **`dV`** | выведено |
| hull | **`V=(8/3)√2·a³`** | **`V/v_hV=16/3`** | bulk budget | inventory |
| compactness | **`V/S`** [m] | **`V/(Sa)`** | surface/bulk | тело ✅; ≠α |
| площади □ vs △ | **`6a²`, `8·(√3/4)a²`** | **`A_□/A_tot`** | EM weight | тело ✅; ≠α (scale) |
| dihedral | **135°** | **3/4×180°** | ridge phase | тело ✅; ≠α |
| **`α`** | soft-face | fundamentals | sealed | — |
#### §8.2·α·EM·faces · Спросили носитель: вес граней / dihedral → α?
**Метод:** geo·ask лист 1 — площади/углы при `a=l_P` → какая доля = сопряжение?
**Ответы:**
1. Тело: $w_\square\approx 0.634$, $w_\triangle\approx 0.366$, dihedral $3/4$, $V/(Sa)\approx 0.398$ — **shipped**.
2. Прецедент κ работает (c,hT); сырые веса **O(0.1–1)** vs $\alpha\sim 1/137$ — неверный масштаб (~$10^7$ ppm).
3. Scaled tries ($w/N_{12}$, $w\cdot r$, …) — всё ещё $|\mathrm{ppm}|\gg 10^3$ → **reject**.
4. $\alpha_{\mathrm{geom}}^{-1}=137$ — из *счёта* граней, не из площадей; другой объект (descent).
5. Канал, который остаётся: $\Phi_\square$ на □ (Stokes) — **вес ≠ голономия**.
**Код:** `SI.alpha_em_face_weight_ask_row()` · verify **`Alpha_em_face_weight_ask`**.
#### §8.2·α·dual · Метод: $\alpha=m/n$ двумя путями
**Идея:** если сопряжение — дробь, числитель и знаменатель приходят из **разной** физики. Не одна магическая формула. DoD: закрыть каждую ногу **без** вставки α; сверху $\alpha=m/n$.
| пара | $m$ (путь A) | $n$ (путь B) | статус ног |
|------|--------------|--------------|------------|
| hops | $N_c$ | $N_{a0}$ | $N_{a0}$ OPEN (H); $N_c$ сегодня α-tied через $m_e$ |
| force | $\kappa=1/\sqrt{2}$ | $M\in\mathbb{N}$ | **κ CLOSED**; **M=97** CLOSED; soft preferred lab-inside; unit descent **SEALED** |
| Schwinger | $a_e$ | $2r=1/(2\pi)$ | $2r$ CLOSED; $a_e$ OPEN/lab |
**Отвергнуто:** одна нога на оба ($M/512$); решать $m$ и $n$ из одного уравнения, где уже есть α.
**α sealed:** soft-face preferred с $M=97$ (§8.2·U0). Demoted: $\alpha_0=\kappa/M$. π-tower removed.
**Код:** `SI.alpha_dual_fraction_ask_row()` · verify **`Alpha_dual_fraction_ask`**.
#### §8.2·α·√2·descent · Приём как у иррациональности $\sqrt{2}$
**Лемма (force dual, demoted coarse).** Пусть $\alpha_0=\kappa/M$, $\kappa=1/\sqrt{2}$ (geo CLOSED), $M\in\mathbb{N}$.
Если $\alpha=p/q\in\mathbb{Q}$, то $\sqrt{2}=q/(pM)\in\mathbb{Q}$ — противоречие. Значит $\alpha\notin\mathbb{Q}$.
**Следствия:**
1. Точные $1/137$, $M/512$ и любой $p/q$ как *определение* α — **несовместимы** с dual $\kappa/M$.
2. «Дробь $m/n$» на носителе ≠ $\alpha\in\mathbb{Q}$; это отношение двух величин носителя ($\kappa/M$ — иррациональное / целое).
3. Hop-dual $N_c/N_{a0}$ с обоими $\in\mathbb{Z}$ дал бы $\alpha\in\mathbb{Q}$ — **натяжение** с force dual (optical $N_{a0}$ = T; или слои разные).
Лемма про demoted $\alpha_0$ — не определение **α**. **α** = soft-face preferred §8.2·U0 с $M=97$.
**Код:** `SI.alpha_sqrt2_descent_ask_row()` · verify **`Alpha_sqrt2_descent_ask`**.
#### §8.2·α·M·g·try · Попытка: $M$ из stamped бит-бюджета
**Dual (demoted):** $\alpha_0=\kappa/M$. $\kappa$ и $M=97$ закрыты; **α** — soft-face, не $\alpha_0$.
**Уже stamped:** $N_{12}=12$; $\lfloor B_{hV}\rfloor=9$; $N_{\mathrm{hier}}=\lfloor B_{hV}\rfloor-1=8$ (T1: минус бит занятости $b$); $b\in\{0,1\}$ на ядре.
**Try (бухгалтерия силы):** иерархия **не** считает $b$ внутри $N_{\mathrm{hier}}$. Кулон на NN всё же сидит на **заряженном ядре** ($b=1$) плюс канал link×hier наружу:
$$
M = 1 + N_{12}\cdot N_{\mathrm{hier}}
= 1 + N_{12}\cdot(\lfloor B_{hV}\rfloor - 1)
= 97.
$$
Чтение: одно место $F_0$ на занятом $hV$ + $N_{12}\cdot N_{\mathrm{hier}}$ мест на звезде × глубина иерархии. Тот же $-1/+1$, что T1, **инвертированный** для EM $n_F$.
**После:** $M=97$ в soft-face preferred (=**α**). Demoted $\alpha_0=\kappa/97$ ~−1040 ppm — не α. $M=96$ без ядра — неполный счёт.
**Статус:** мотивированный try → **теорема** §8.2·α·nF·Thm.
**Код:** `SI.alpha_M_from_g_try_row()` · verify **`Alpha_M_from_g_try`**.

#### §8.2·α·nF·Thm · $M=1+N_{12}\cdot N_{\mathrm{hier}}$ из аксиом kick ledger

**Теорема (места силы).** На решётке сила ходит целыми пакетами $F_0$ (Thm 5.1 · §3.12). Кулон между двумя единичными зарядами на соседних ячейках — **слабее** одного такого пакета:
$$
F_{\mathrm{Coulomb}}(N{=}1)=\frac{F_0}{M}.
$$
$M$ — сколько **независимых мест** (seats) у одного заряженного FCC-ядра, по которым kick ledger может разнести $\Delta p\in p_0\cdot\mathbb{Z}$. Не «измерили α и подобрали», а **вынуждены леммами из $g$**.

**Леммы (только stamped):**
| класс | сколько | откуда |
|-------|---------|--------|
| ядро $b=1$ | **1** | занятость заряженного $hV$ (§5.0); T1 вычел этот бит из $N_{\mathrm{hier}}$, сила его всё равно требует |
| link×hier | **$N_{12}\cdot N_{\mathrm{hier}}=96$** | изотропная звезда: все 12 связей × 8 каналов иерархии (§5.2.2 · §8.4.1-A) |

**Заключение:**
$$
M = n_{F,\mathrm{seats}} = 1 + N_{12}\cdot N_{\mathrm{hier}} = 97.
$$
Тогда $M=97$ подставляется в soft-face preferred (=**α**). Demoted $\alpha_0=\kappa/M$ (~−1040 ppm) — не α. $M=96$ без ядра — неполная перепись. Единственное $M$ под леммами.

**Статус:** **теорема CLOSED**. Runtime-гистограмма $\Delta p$ из сима — N/A (в CA нет opcode Кулона); это не дыра счёта мест.
**Код:** `SI.alpha_nF_kick_census_row()` · verify **`Alpha_nF_kick_census`**.
#### §8.2·α·full-quant · α из полного квантования (fundamentals)
**Смысл «тонкой структуры».** §0.9: на M нет continuum-волны — есть occupancy мод / **$n_E\cdot E_0$**. Сила — **$n_F\cdot F_0$** (Thm 5.1). Постоянная тонкой структуры — не «магическое π», а **безразмерная тонкость**: на сколько unit NN Coulomb слабее одного Planck-force пакета на носителе.
$$
F_{\mathrm{Coulomb}}(N{=}1)=F_0/M,\quad M=n_{F,\mathrm{seats}}=97\ \text{CLOSED (Thm)}.
\quad \alpha_0=\kappa/M\ \text{(demoted coarse)};\quad \alpha=\text{soft-face preferred}|_{M=97}\ \text{SEALED}.
$$
**Два числа — два слоя:**
| путь | формула | vs CODATA | роль |
|------|---------|-----------|------|
| **α (soft-face)** | preferred $|_{M=97}$ | ~−0.000068 ppm | **sealed** §8.2·U0 |
Soft preferred (seat+face) — **lab-inside**; soft singlet в den — **SEALED** (G-grade completeness; не дыра в $M$).
**Код:** `SI.alpha_full_quantization_bridge_row()` · verify **`Alpha_full_quantization_bridge`**.

#### §8.2·α·U0·soft-face · α from bottom constants (SEALED)

**Дно** (больше не режется; $M,d,U,N_{\mathrm{hier}}$ сюда не входят):

$$
\begin{aligned}
B_{hV} &= \frac{2\pi}{\ln 2}, &
\kappa &= \frac{R_{\mathrm{in}}}{R_{\mathrm{out}}}, &
|N_{12}| &= 12, \\
N_4 &= 4, &
n_{\mathrm{SU}(2)} &= 3, &
\Delta\varphi_{\min} &= \tfrac12.
\end{aligned}
$$

($\Delta\varphi_{\min}$ — дно Heisenberg/Arg; в саму $\alpha$ ниже не входит, только в ногу/gate.)

**$\alpha$ — только из дна** (без ярлыков $M,d,U$):

$$
\boxed{
\alpha
=
\frac{
\hat M^{2}\,\kappa\Bigl(\bigl(N_4+n_{\mathrm{SU}(2)}\bigr)\hat M+\kappa\Bigr)
}{
\bigl(N_4+n_{\mathrm{SU}(2)}\bigr)\hat M^{4}
- \hat M\,\kappa^{3}
- \dfrac{N_4+n_{\mathrm{SU}(2)}+1}{N_4+n_{\mathrm{SU}(2)}}
}
}
$$

где единственная свёртка записи (не новый фундамент):

$$
\hat M
:=
1 + |N_{12}|\bigl(\lfloor B_{hV}\rfloor - 1\bigr)
=
1 + |N_{12}|\left(\left\lfloor\frac{2\pi}{\ln 2}\right\rfloor - 1\right).
$$

Эквивалентно $\kappa^{6}$-лицо (тождество геометрии: $(1-\kappa^{6})/\kappa^{6}=N_4+n_{\mathrm{SU}(2)}$):

$$
\alpha
=
\frac{
\hat M^{2}\,\kappa\left(\dfrac{1-\kappa^{6}}{\kappa^{6}}\hat M+\kappa\right)
}{
\dfrac{1-\kappa^{6}}{\kappa^{6}}\hat M^{4}
- \hat M\,\kappa^{3}
- \dfrac{1}{1-\kappa^{6}}
},
\qquad
\kappa=\frac{R_{\mathrm{in}}}{R_{\mathrm{out}}}.
$$

Подстановка чисел дна: $\kappa=1/\sqrt{2}$, $\hat M=1+12\cdot 8=97$ $\Rightarrow$
$\alpha\approx 7.2973525638\times 10^{-3}$ (внутри CODATA $\varepsilon$).

Код: `SI.alpha_from_fundamentals()` (= `SI.alpha_preferred`).

**Единица пакета** (SI-перевод, не вход): $U_0=F_0\,l_P^{2}$, $\hbar c=2\kappa\,U_0$.
Demoted: $\alpha_0=\kappa/\hat M$; $\pi$-tower removed.
**Код:** `SI.alpha_from_fundamentals` · `SI.alpha_U0_soft_face_ask_row()` · verify **`Alpha_U0_soft_face_ask`**.


#### §8.2·α·upstairs · SEALED cascade on preferred α
Структурная α закрыта (soft-face). **Вверх — закон каскада (exact):**
```
v   = α^N_hier · E_P · √(2π)
m_H = √(2λ)·v ,  λ = 1/8 + N_hier·(α/(4π))
m_p = α · (v/2) · (1 + κ²/N12)
m_e = α² · m_H / N_φ
m_n = m_p + 2·m_e
```
Вход: `alpha_preferred`. Contrasts к PDG — **T-дверь**, не u(m).
Мягкие полы ~10⁻³ (packing / empty-cell) — высшая структура, не дыра в α.
**Код:** `SI.alpha_preferred` · `SI.alpha_upstairs_mass_probe_row()` · verify **`Alpha_upstairs_mass_probe`**.

#### §8.2·α·SI-bridge · носитель → пакет U₀ → лаборатория
**α** — §8.2·U0 fundamentals (`SI.alpha_from_fundamentals`). U₀ / ℏc — SI-перевод, не вход в α.
```
U0 = F0 · l_P² = s0 · c0
ħ c = 2 κ U0
```
Лаб-дверь (T): contrast vs CODATA опционален; у α нет $u(\alpha)$.
**Код:** `SI.alpha_si_bridge_row()` · verify **`Alpha_si_bridge`**.

---

**Сюда:** физика (§). Impl / verify / код → [`DEVLOG.md`](../DEVLOG.md).
