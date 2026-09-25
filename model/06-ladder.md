# §6. Иерархия M → SM (масштабная лестница, часть модели)

### §6.0 · Полная лестница M → T (все рунги до макромира)

**Зачем.** Один взгляд: от кирпича до метра — **каждый** рунг в hops `N·dl` и, где stamped, в степенях **`α_fs`**.

**Не путать** (разные «лестницы», одно слово):

| имя | что считает | где |
|-----|-------------|-----|
| **§0…§8** | оглавление MODEL | [`MODEL.md`](../MODEL.md) |
| **CL-1…CL-8** | битовая иерархия на `ℤ_{N_ring}` | §3.12 |
| **рунги k** (ниже) | длина в **`N·dl`**, якорь Compton **`k=0`** | эта таблица |
| **кванты `s₀→E₀`** | механика **на одном** `hV` | §5.2.2 |

**Две оси на одной лестнице:**
$$
N = \frac{L}{dl}=\frac{L}{l_P}\in\mathbb{R}_{+},\qquad
N_c=\frac{m_P}{m_e}\approx 2.3\times 10^{22}.
$$
- **Геометрия звезды:** $N=N_{12}^{m}$ ($m=0,1,2,\ldots$) — составные оболочки **до** IR.
- **IR / EM (hop-лестница, §8.2·α·H2):** от якоря $N_c$ вверх по длине
$$
N_{k+1}=\frac{N_k}{\alpha_{\mathrm{fs}}},\qquad
N_{-1}=\alpha_{\mathrm{fs}} N_c\;(r_e),\quad
N_0=N_c\;(\bar\lambda_C),\quad
N_1=\frac{N_c}{\alpha}\;(a_0),\quad N_2=\frac{N_c}{\alpha^2},\ \ldots
$$
- **Массы (степени α, §8.2):** $v\sim\alpha^{8}$, $m_H\sim\alpha^{8}$, $m_p\sim\alpha^{1}v$, $m_e\sim\alpha^{2}m_H$, $m_\nu\sim\alpha^{5}m_H$ — **энергия**, не длина; длина того же тела: $N=M\mapsto m_P/M$.

**Порядок величин** ($\log_{10}N$ при $N_{12}=12$, $\alpha^{-1}\approx 137$):

| k | $N$ (hops `dl`) | $\log_{10}N$ | α-рунг / масса | объект | слой | статус |
|---|-----------------|--------------|----------------|--------|------|--------|
| **0** | $1$ | $0$ | $m_P$ | кирпич `hV`, pra-дефект, $n\in\mathbb{Z}$, $E_0\cdot\mathbb{Z}$ | M | **CLOSED** |
| **1** | $N_{12}=12$ | $1.1$ | — | ε-звезда; $R_{\mathrm{dress}}=1\cdot dl$ | M | **CLOSED** |
| **2** | $N_{12}^2=144$ | $2.2$ | — | 2-я коорд. сфера | M | геом. |
| **3** | $N_{12}^3=1728$ | $3.2$ | — | floor1 окно (C4 пре-резонанс) | M | §6·floor1* |
| **4** | $N_{12}^4=2.07\times 10^4$ | $4.3$ | — | floor1 полоса | M | **IN PROGRESS** |
| **5** | $N_{12}^5\approx 2.5\times 10^5$ | $5.4$ | — | верх floor1; C2 единственная устойчивая $B{=}0$ материя | M | census **CLOSED** |
| **6** | $\sim 10^{15}$ | $15$ | confining | floor2: кварковые foci ($\sim d{=}3$) | M | схема |
| **7** | $N_{-1}=\alpha N_c\sim 1.7\times 10^{20}$ | $20.2$ | $k{=}{-}1$ | $r_e$; hadron / packing | M·T | hop **CLOSED** |
| **8** | $N_0=N_c\sim 2.3\times 10^{22}$ | $22.4$ | $k{=}0$ | $\bar\lambda_C(e)$; $m_e$ stamped | M→T | масса **CLOSED** |
| **9** | $N_1=N_c/\alpha\sim 3.2\times 10^{24}$ | $24.5$ | $k{=}1$ | Bohr $a_0$; H-облако | M hop·T | **OPEN** $N_{a0}$ из H |
| **10** | $N_2\sim 4.4\times 10^{26}$ | $26.6$ | $k{=}2$ | Å-орбиталь, $N_{\mathrm{pack}}$ (§5.2.4) | T | $N_{\mathrm{pack}}$ **OPEN** |
| **11** | $N_3\sim 6\times 10^{28}$ | $28.8$ | $k{=}3$ | молекула / узел кристалла | T | ансамбль |
| **12** | $N_4\sim 8\times 10^{30}$ | $31.0$ | $k{=}4$ | микро-объект | T | |
| **13** | $N_5\sim 10^{33}$ | $33.1$ | $k{=}5$ | мм–см | T | |
| **14** | $N_6\sim 10^{35}$ | $35.3$ | $k{=}6$ | **метр**, macro-газ / тело (§5.3) | T | NLSE/NS |
| **15** | $\lambda\gg\sigma_R\,dl$ | — | — | **макромир**: Newton, гладкая волна (Thm **T-CR**, §4.1.0-T) | T | readout **forced** |

Строки **k≥10** — **продолжение** $N_k=N_c/\alpha^k$ (порядок; не fitted knobs). Точные целые $N_k$ — когда hop-лестница и $N_{\mathrm{pack}}$ закрыты (§8.2·H·ask).

```
k=0..5     N=N₁₂^m           геометрия составного узла (M)
k=6        ~10¹⁵·dl          floor2 кварки (схема)
k=7..9     N_{-1},N₀,N₁      EM IR: r_e → λ̄_C → a₀
k≥10       N_k=N_c/α^k       атом → химия → метр
k=15       λ≫σ_R·dl          continuum T (без hL→0)
         ─── M→T мост на каждом readout: Green-R · binomial · |Φ|² (§4) ───
```

**Мост M→T** (не отдельный рунг — **обязателен** на пути вниз): §4.0 — без coarse нет доступа; §2.1 — Born = UI; §4.1.1 — NLSE/GL + $\nu_{CA}$.

**Проверка модели** — только на **T** (таблица PDG, $\Gamma$, $d\sigma/d\Omega$, lab SI). **M** refuted только если T-инварианты не сходятся.

**Северная звезда:** рекурсивный спуск **M→T→SM** на каждом leaf; рунги **k≤9** — субатомика + IR (milestone); **k≥10** — macro/T-ансамбли; META/UI — над T.

**Антипутаница:** dressing $R=1\cdot dl$ (k=1) **≠** Compton $N_c$ (k=8) **≠** Bohr $N_1$ (k=9); $N_{12}^{m}$ (k≤5) **≠** $N_c/\alpha^k$ (k≥7).
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
**Не один C3.** Gauge-fixed `VACUUM` (class 0) — Φ=0, мёртвый. `VACUUM_BOIL` — вся решётка кирпичами, NN Δφ=Δφ_min: live, контраст сам ~1.5→773, ρ_max→1 за 1024 тика.
**Денсометр (§10.5):** старый A10 (`∮ d arg(z₂/z₁)`) на locked boil был слеп → ложный `emerged_b=False`. Dual-channel rel / u1=`Arg(z₁+z₂)` / auto — **b читается**. Probes: `SYNTH_U1`, `VORTEX_P` → **`b=1`**; family `PLANE_WAVE` → `born=1`.
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
