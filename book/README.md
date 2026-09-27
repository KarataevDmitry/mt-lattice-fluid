# Серия «Кипящий океан» (LaTeX)

Несколько томов — см. **[`SERIES.md`](SERIES.md)**. Читаемая проза: **не** SSOT (`model/` = контракт с кодом).

## Сборка

Требуется **XeLaTeX** (скрипт сам ставит **MiKTeX** через `winget`, если TeX нет, и дописывает `...\MiKTeX\miktex\bin\x64` в user PATH).

```powershell
cd book
./build.ps1                        # out/construction.pdf
./build.ps1 -Volume floors
./build.ps1 -Volume observer
```

PDF: `book/out/<construction|floors|cosmology|…>.pdf` — см. [`SERIES.md`](SERIES.md). Артефакты только в `book/out/`.

**Обозначения:** `glossaries-extra`, список в `sources/notation.tex`, записи в `sources/glossary/notation-entries.tex`. Записи `symb:…` в `notation-entries.tex`; в тексте и в `equation` — `\gls{symb:…}` (как в учебнике). Опционально короткие `\hl` = `\gls{symb:a}`. Код: `hL`/`hT`/`hV`. `\makenoidxglossaries`.

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
  out/               # артефакты сборки (gitignore, кроме .gitkeep)
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
