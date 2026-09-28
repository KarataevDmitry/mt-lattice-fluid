# Серия «Кипящий океан» (LaTeX)

Несколько томов — см. **[`SERIES.md`](SERIES.md)**. Читаемая проза: **не** SSOT (`model/` = контракт с кодом).

## Сборка

Требуется **XeLaTeX** и **biber** (скрипт сам ставит **MiKTeX** через `winget`, если TeX нет, и дописывает `...\MiKTeX\miktex\bin\x64` в user PATH).
Сборка: `xelatex` → `biber` → `xelatex` ×2; библиография — `sources/references.bib`.

```powershell
cd book
./build.ps1                        # out/pdf/construction.pdf
./build.ps1 -Volume floors
./build.ps1 -Volume observer
```

Готовые PDF: `book/out/pdf/<volume>.pdf` (Git LFS; на машине один раз `git lfs install`, потом обычный clone). Сборочный мусор XeLaTeX: `book/out/work/`. См. [`SERIES.md`](SERIES.md).

**Обозначения:** глава «Условные обозначения» (`notation.tex`) — таблица **Обозначение · Смысл · Единица**; записи в `glossary/notation-entries*.tex` (`\newnotationentry`, поле `user1`). `notation-macros.tex` — **camelCase** → `\gls{symb:…}` (клик в ту же главу). В каждом томе в frontmatter — `\input{notation.tex}`. Составные единицы SI в тексте и таблице — через `\SiFrac` / макросы `\NotationUnit…` из `glossary/notation-units.tex` (дроби `\frac`, не слэш в `\mathrm{…/…}`); `build.ps1` это проверяет.

## Структура каталога

```
book/
  SERIES.md          # семантические тома
  build.ps1          # -Volume construction|floors|…
  sources/
    main-construction.tex, main-floors.tex, main-cosmology.tex, …
    volumes/         # vol-*-body.tex
    preamble.tex
    frontmatter.tex
    chapters/
    figures/         # PDF-иллюстрации (генерятся scripts/render_carrier_figures.py)
    appendix/
  out/pdf/           # готовые PDF (в git)
  out/work/          # вспомогательные файлы XeLaTeX
```

Правка текста — прямо в `sources/*.tex`. Без одноразовых патч-скриптов и дампов в `book/`: справочники и черновики — вне репо или в `model/` / KB, не рядом с LaTeX.

## construction — оглавление (текущий текст)

| PDF гл. | Файл | Содержание |
|---------|------|------------|
| — | `frontmatter.tex` | Предисловие |
| 1 | `chapters/00-descent.tex` | Требования, макромир, микромир, КМ, КТП, планковский мир |
| 2 | `chapters/00-axiom-rationale.tex` | Перенос требований |
| 3 | `chapters/02-axioms.tex` | Реестр $A_1$–$A_{16}$, теорема 2.3 |
| 4 | `chapters/01-carrier.tex` | Геометрия: гекс-срез и FCC |
| 5 | `chapters/00-foundations.tex` | Теорема дискретности |
| 6 | `chapters/03-evolution.tex` | Закон $g$ |
| 7 | `chapters/04-macro.tex` | Переход $M\to T$, теорема T-CR |
| 8 | `chapters/05-matter.tex` | Механика ячейки, материя |
| **13** | **`chapters/07-alpha.tex`** | **Постоянная тонкой структуры** |
| 14 | `chapters/06-si-sm.tex` | Лестница $M\to T$, SI, массы, SM |

**floors** (отдельный PDF): `09-floors-preface` … `12-floor2` — см. [`SERIES.md`](SERIES.md).
| A | `appendix/00-background.tex` | CA, Тоффоли/Фредкин, Маделунг |

Текст — связная русская проза; SSOT физики и верификация — `model/` и репозиторий `mt_ca/`.

## Граница

- **Книга** (`book/`, [`SERIES.md`](SERIES.md)) — тома для чтения.
- **model/** — контракт с реализацией.
- **DEVLOG.md** — impl / verify (не входят в книгу).
