# §6. Иерархия M → SM (масштабная лестница, часть модели)
| Уровень | Масштаб | Объект |
|---------|---------|--------|
| 0 | 1·dV = (dl)³ | **pra-дефект** в одном dV, заряд `e₀`, `m₀` |
| 1 | 10³–10⁵·dl | пре-резонансы / лептонные узлы (составные) |
| 2 | ~10¹⁵·dl | кварковые фокусы (составные) |
| 3 | ~10²⁰·dl | адроны (протон), SM |
#### §6·floor1·ask · Прогулка по этажу 1
**Окно длины (не CODATA):** таблица $10^3\ldots 10^5\cdot\mathrm{dl}$ совпадает со степенями каузальной звезды:
$$
N_{12}^{3}=1728,\qquad N_{12}^{4}=20736,\qquad N_{12}^{5}\approx 2.5\cdot 10^{5}.
$$
**Это не:** Compton/$a_0$ ($\sim 10^{22}\ldots 10^{24}\cdot\mathrm{dl}$, IR); confining этаж 2 ($\sim 10^{15}$); $N_{\mathrm{gen}}=d$ (счёт стеков, не длина). **Не претендует:** $m_\mu/m_e$ как размер этажа 1.
**Это может быть:** мультиклеточные лептонные ($B=0$) пре-резонансы / обёртки на итерациях звезды — своя теория сборки на том же $g$, не новая калибровка.
**Статус:** окно мотивировано; класс-census B=0 — §6·floor1·B0·census.
**Код:** `SI.floor1_leptonic_ask_row()` · verify **`Floor1_leptonic_ask`**.
#### §6·floor1·B0·census · Что устойчиво при $B=0$ на $N_{12}^{3}\ldots N_{12}^{4}$
**Критерий (уже §8.2):** нет downhill-$g$ с теми же аддитивными инвариантами и меньшей энергией.
| класс | стабилен? | зачем |
|-------|-----------|-------|
| C0 вакуум/A5 | нет (не объект) | фон |
| C1 свободный $\gamma$ | да | уже vacuum; не blob радиуса $N_{12}^{k}$ |
| **C2** легчайший $Q=\pm1$ + ε-dressing | **да** | топо-защита + легчайший $Q$; ядро floor0, обёртка $R=1\cdot\mathrm{dl}$ (dressing·close) |
| C3 возбуждённый/составной тот же $Q$ | **нет** | канал $C3\to C2+\gamma$ **существует** (Q+A3); $\Gamma$ soft |
| **C4** $Q=0$ мультиклеточный blob | **нет** | нет топозаряда → A5 → вакуум = **пре-резонанс** |
| C5 пара $\pm$ на этом R | нет | аннигиляция §5.0.3 |
| C6 нейтральный $L$-сектор | возможно (off-band) | $R_\nu\not\equiv N_{12}^{3\ldots4}$ — не объект полосы |
**Острый вывод:** единственная устойчивая *материя* B=0 на этом радиусе — **C2** (одетый легчайший $Q=\pm1$). Имя этажа «пре-резонанс» = **C4** — неустойчиво по построению.
**Код (leftovers):** `SI.floor1_leftovers_close_row()` · verify **`Floor1_leftovers_close`** — существование C3-канала CLOSED; $\nu$ off-band.
#### §6·floor1·C3·gamma·close · что с «скоростью» распада
**Не закон M:** $N(t)=N_0 e^{-t/\tau}$, $\Gamma=\hbar/\tau$ — это T-статистика многих систем (§8.2 · §2.1), не онтология тика.
**CLOSED на M:** форма часов = $n_{\mathrm{ticks}}\in\mathbb{N}\cdot hT$ (не float $\Gamma$).
**SOFT (reopen):** гипотеза $n_{\mathrm{ticks}}=1$ для *одиночного* multi-shell C3 (A1+local downhill) может быть артефактом пустоты. Dogfood вакуума: кипение нормальное только когда задали *всю* решётку — пустоты нет. $n_{\mathrm{ticks}}$ для C3 в заполненной A5-ванне **не stamped**.
**Не здесь:** PDG-время жизни $\mu$ (нужен лист массы/композита).
**Код:** `SI.floor1_C3_gamma_close_row()` · verify **`Floor1_C3_gamma_close`** (continuum reject + soft bath clock).
#### §6·floor1·C3·bath·dogfood · предыдущий этаж целиком
**Не один C3.** Gauge-fixed `VACUUM` (class 0) — Φ=0, мёртвый. `VACUUM_BOIL` — вся решётка кирпичами, NN Δφ=Δφ_min: live, контраст сам ~1.5→773, ρ_max→1 за 1024 тика; **b-matter пока нет** (`emerged_b=False`).
**Код:** `SeedClass.VACUUM_BOIL` · `scripts/run_filled_bath_emergence.py` · `SI.floor1_C3_bath_dogfood_row()` · verify **`Floor1_C3_bath_dogfood`**.
**Код:** `SI.floor1_B0_census_ask_row()` · verify **`Floor1_B0_census_ask`**.
#### §6·floor1·dressing·ask · Что за обёртка электрона
**Вопрос носителю (§5.0.5), не выдумка:** что такое near-zone легчайшего $Q=\pm1$, и что фиксирует её радиус?
**CLOSED:**
- обёртка = облако $\rho_\Theta$ вокруг ядра $b=1$ (не вторая частица, не Compton/$a_0$);
- $\rho_\Theta(x)\propto f(|\Delta\varphi_N|,|\zeta|)$ с полом $\Delta\varphi_{\min}$;
- минимальный хвост $\supseteq$ $\varepsilon$-окрестность $\Lambda$ $\Rightarrow$ $R_{\min}=1\cdot\mathrm{dl}$, звезда $N_{12}$;
- anti-smear $K_P$ держит ядро; Гейзенберг держит неустранимый ореол;
- оболочки = моды $\rho_\Theta$ на координационных сферах.
**Код (ask):** `SI.floor1_dressing_ask_row()` · verify **`Floor1_dressing_ask`**.
#### §6·floor1·dressing·close · $R_{\mathrm{dress}}=1\cdot\mathrm{dl}$
**Лемма:**
1. Winding-1 на звезде: $\Delta\varphi_{\mathrm{ring}}=2\pi/N_{12}$. Из $N_\varphi=\lceil 2\pi/\Delta\varphi_{\min}\rceil$ следует $N_{12}<N_\varphi\Leftrightarrow 2\pi/N_{12}>\Delta\varphi_{\min}$ — вся ε-звезда над полом.
2. Локальный баланс/gate только на $N(x)$ (A1 · §5.2); вторая оболочка за один $hT$ запрещена.
3. Ground легчайшего $Q$: multi-shell $\rho_\Theta$ = возбуждение → downhill к минимальному ореолу (логика C3 vs C2).
$$\Rightarrow\quad R_{\mathrm{dress}}=R_{\min}=1\cdot\mathrm{dl},\quad N_{\mathrm{star}}=N_{12}.$$
Полоса этажа 1 $N_{12}^{3}\ldots N_{12}^{4}$ — окно C4, **не** радиус e-halo.
**Код:** `SI.floor1_dressing_close_row()` · verify **`Floor1_dressing_close`**.
#### §6·floor1·dressing·f·close · форма $f$
**CLOSED:** на M нет float-knobs; §5.0.5 — облако = где сигнал $\ge$ пола; $\int\rho_\Theta\sim n_E\in\mathbb{Z}$; $\langle\rho_\Theta\rangle_T$ = binomial (§4.1).
$$\rho_\Theta(x)=\mathbf{1}\big[|\Delta\varphi_N(x)|\ge\Delta\varphi_{\min}\big].$$
$|\zeta|$ — scalar gate, без stamped $\zeta_{\min}$ → не вторая свободная ось. Гладкость — T-binomial, не $f$ на M.
**REJECT:** continuum-ansätze (exp/Gauss/$1/r$); $\alpha$/$a_0$ внутри $f$.
**Код:** `SI.floor1_dressing_f_close_row()` · verify **`Floor1_dressing_f_close`**.
Конфайнмент: «вытащить кварк» = разорвать топологический узел → **пара pra-дефектов**, не один dV.
**Цвет ≠ вход.** Кратность фокусов в устойчивом составном узле — **prediction** из топологии на FCC/$\varepsilon$ + Паули + $K_P$; ожидание $\sim d=3$ (**§8.4.1-D**). SM-$N_c$ — T-имя, не axiom M.
---

---

**Сюда:** физика (§). Impl / verify / код → [`DEVLOG.md`](../DEVLOG.md).
