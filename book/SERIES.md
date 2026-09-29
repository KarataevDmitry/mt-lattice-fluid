# Серия «Кипящий океан»

Семантические тома (не `main`, не `vol-I`). SSOT формул: `model/`.

## Принципы (мета)

1. **construction** включает **matter** (`05-matter`) — механика ячейки и вход в T; без этого нет лестницы.
2. **Физика дальше дробится** по мере копания (новые тома, когда появляется **свой класс критических экспериментов**, а не «ещё одна глава»).
3. **Каждый том заканчивается блоком «Критические эксперименты»** — предсказание + что считается провалом модели; без этого мало смысла. Шаблоны: `sources/volumes/chapter-critical-experiments-<id>.tex`.
4. **§4.8 (системные кванты):** алгебра fractal в construction / macro; узел наблюдателя, **R_eff**, сравнение видов — том **observer**.
5. **Вычислительная лаборатория** — `sources/chapters/computational-laboratory.tex` + макросы `glossary/lab-protocol.tex` (`labrecord`, `labseries`). Серия = затянувшаяся лаба: MODEL / аппарат / журнал прогонов.
6. **Обработка результатов измерений** — `measurement-processing.tex` через `include-measurement-processing.tex` **в каждом томе** после гл. лаборатории, перед «Критическими экспериментами». GUM, Стьюдент, $E_n$.
7. **Критические эксперименты** — не буллет-лист: `\input{volumes/lab-*-records.tex}` с полными постановками (construction: `lab-construction-records.tex`; floors: `lab-floors-records.tex`).

| ID | Содержание | `main-*.tex` | PDF `out/pdf/` |
|----|------------|--------------|------------|
| **construction** | Построение: спуск, **g**, macro, **matter**, **α**, SI-лестница | `main-construction.tex` | `construction.pdf` |
| **floors** | Этажи 0–2 (отдельно от построения) | `main-floors.tex` | `floors.pdf` |
| **cosmology** | BB, CMB, `N_tick`, META §3 | `main-cosmology.tex` | `cosmology.pdf` |
| **observer** | Узел (M, R_eff), ε, τ_frame | `main-observer.tex` | `observer.pdf` |
| **chemistry** | Химия / физ. химия на T | `main-chemistry.tex` | `chemistry.pdf` |
| **compute** | Вычислительная архитектура под **g** | `main-compute.tex` | `compute.pdf` |

## Сборка

```powershell
cd book
./build.ps1                          # construction (default); xelatex+biber until refs/cites resolve
./build.ps1 -Volume floors   # prebuild construction → generated/construction-vol-refs.tex
./build.ps1 -Volume cosmology
```

`build.ps1` гоняет XeLaTeX столько раз, сколько нужно (до стабилизации ссылок в `.log`), с повторным `biber` при undefined citations. Ссылки на другой том (напр. `ch:floor*` из `construction`) не считаются ошибкой.

Перед сборкой **construction** / **floors**: `scripts/gen_lab_records_tex.py` → `lab-si-pdg-table.tex`, `lab-ce-m-0{0,1,2,3,4}-{analysis,experiment}.tex`, `lab-ce-a-0{2,3}-{analysis,experiment}.tex` (журнал CE-M / CE-A, не «мы решили что ок»).

`-Volume`: `construction` | `floors` | `cosmology` | `observer` | `chemistry` | `compute`

## construction — главы

`volumes/vol-construction-body.tex`: `00-descent` … `06-si-sm`, **вычисл. лаборатория**, **обработка измерений**, **журнал CE-M**, приложение CA.

**Не входит:** этажи 0–2 → `floors`; нарратив наблюдателя → `observer`.

## floors — главы

`volumes/vol-floors-body.tex`: `09-floors-preface` … `12-floor2`, **лаборатория**, **метрология**, **журнал CE-F / CE-A**.

Граница с construction может сдвигаться; новые rung’и — расширение этого тома или новый том по правилу (3).

## Остальные тома

Заготовки в `volumes/vol-<id>-body.tex`; при наполнении — финальная глава критических экспериментов по тому же шаблону.

## Глоссарий

`sources/notation.tex`, `sources/glossary/` — общий; при конфликте побеждает `model/`.
