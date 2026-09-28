# Серия «Кипящий океан»

Семантические тома (не `main`, не `vol-I`). SSOT формул: `model/`.

## Принципы (мета)

1. **construction** включает **matter** (`05-matter`) — механика ячейки и вход в T; без этого нет лестницы.
2. **Физика дальше дробится** по мере копания (новые тома, когда появляется **свой класс критических экспериментов**, а не «ещё одна глава»).
3. **Каждый том заканчивается блоком «Критические эксперименты»** — предсказание + что считается провалом модели; без этого мало смысла. Шаблоны: `sources/volumes/chapter-critical-experiments-<id>.tex`.
4. **§4.8 (системные кванты):** алгебра fractal в construction / macro; узел наблюдателя, **R_eff**, сравнение видов — том **observer**.

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
./build.ps1                          # construction (default)
./build.ps1 -Volume floors
./build.ps1 -Volume cosmology
```

`-Volume`: `construction` | `floors` | `cosmology` | `observer` | `chemistry` | `compute`

## construction — главы

`volumes/vol-construction-body.tex`: `00-descent` … `05-matter`, `07-alpha`, `06-si-sm`, **критические эксперименты**, приложение CA.

**Не входит:** этажи 0–2 → `floors`; нарратив наблюдателя → `observer`.

## floors — главы

`volumes/vol-floors-body.tex`: `09-floors-preface`, `10-floor0` … `12-floor2`, **критические эксперименты (этажи)**.

Граница с construction может сдвигаться; новые rung’и — расширение этого тома или новый том по правилу (3).

## Остальные тома

Заготовки в `volumes/vol-<id>-body.tex`; при наполнении — финальная глава критических экспериментов по тому же шаблону.

## Глоссарий

`sources/notation.tex`, `sources/glossary/` — общий; при конфликте побеждает `model/`.
