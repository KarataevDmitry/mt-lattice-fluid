# Серия «Кипящий океан»

Семантические тома (не `main`, не `vol-I`). SSOT формул: `model/`.

## Принципы (мета)

1. **construction** включает **matter** (`05-matter`) — механика ячейки и вход в T; без этого нет лестницы.
2. **Физика дальше дробится** по мере копания (новые тома, когда появляется **свой класс критических экспериментов**, а не «ещё одна глава»).
3. **Каждый том заканчивается блоком «Критические эксперименты»** — предсказание + что считается провалом модели; без этого мало смысла. Шаблоны: `sources/volumes/chapter-critical-experiments-<id>.tex`.
4. **§4.8 (системные кванты):** алгебра fractal в construction / macro; узел наблюдателя, **R_eff**, сравнение видов — том **observer**.
5. **Вычислительная лаборатория** — `computational-laboratory.tex`; журнал CE в `sources/lab-journal/*.tex` (ручной \LaTeX{}, четыре `\subsubsection*`). Обёртка: `labrecord` / `labseries` только дают заголовок и `\input`.
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

`build.ps1` гоняет XeLaTeX столько раз, сколько нужно (до стабилизации ссылок в `.log`), с повторным `biber` при undefined citations. Межтомные номера: `generated/construction-vol-refs.tex` (для **floors**, макросы `\bcref`/`\bref`) и `generated/floors-vol-refs.tex` (для **construction**, `\fcref`/`\fvolrefs`); сборка **construction** при необходимости сначала гоняет **floors** (и наоборот), без рекурсии — флаги `-SkipFloorsPrebuild` / `-SkipConstructionPrebuild`.

Перед сборкой **construction**: `scripts/gen_lab_records_tex.py` → только `generated/lab-si-pdg-table.tex` (сводка модель/PDG). **Журнал CE** (постановка, ход, анализ, погрешность) --- `book/sources/lab-journal/*.tex`, правка вручную после прогона verify.

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
