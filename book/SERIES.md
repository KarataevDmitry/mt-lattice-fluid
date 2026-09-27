# Серия «Кипящий океан»

Семантические тома (не `main`, не `vol-I`). SSOT формул: `model/`.

| ID | Содержание | `main-*.tex` | PDF `out/` |
|----|------------|--------------|------------|
| **construction** | Построение: спуск, **g**, macro, matter, **α**, SI-лестница | `main-construction.tex` | `construction.pdf` |
| **floors** | Этажи 0–2 (отдельно от построения; границы уточняются) | `main-floors.tex` | `floors.pdf` |
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

`volumes/vol-construction-body.tex`: `00-descent` … `05-matter`, `07-alpha`, `06-si-sm`, приложение CA.

**Не входит:** этажи 0–2 → `floors`.

## floors — главы

`volumes/vol-floors-body.tex`: `09-floors-preface`, `10-floor0` … `12-floor2`.

Отделение от **construction** — черновая граница; возможен пересмотр (что ещё относится к «этажам» vs лестнице).

## Остальные тома

Заготовки в `volumes/vol-<id>-body.tex`. Наполнение — отдельные UoW.

## Глоссарий

`sources/notation.tex`, `sources/glossary/` — общий; при конфликте побеждает `model/`.
