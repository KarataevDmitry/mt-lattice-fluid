# Монография (LaTeX)

Читаемая версия теории для человека: **не** `model/*.md` (рабочая спецификация для кода).

## Сборка

Требуется **XeLaTeX** (скрипт сам ставит **MiKTeX** через `winget`, если TeX нет, и дописывает `...\MiKTeX\miktex\bin\x64` в user PATH).

```powershell
cd book
./build.ps1
```

PDF: `book/out/main.pdf` (XeLaTeX, Times New Roman, три прохода). Все артефакты (`main.aux`, `.log`, …) только в `book/out/` — не копируй `.aux` в `sources/` (ломает `\ref`).

**Обозначения:** `glossaries-extra`, список в `sources/notation.tex`, записи в `sources/glossary/notation-entries.tex`. Записи `symb:…` в `notation-entries.tex`; в тексте и в `equation` — `\gls{symb:…}` (как в учебнике). Опционально короткие `\hl` = `\gls{symb:a}`. Код: `hL`/`hT`/`hV`. `\makenoidxglossaries`.

## Структура каталога

```
book/
  build.ps1          # сборка sources → out
  sources/           # исходники (только .tex)
    main.tex
    preamble.tex
    frontmatter.tex
    chapters/
    figures/         # PDF-иллюстрации (генерятся scripts/render_carrier_figures.py)
    appendix/
  out/               # артефакты сборки (gitignore, кроме .gitkeep)
```

Правка текста — прямо в `sources/*.tex`. Без одноразовых патч-скриптов и дампов в `book/`: справочники и черновики — вне репо или в `model/` / KB, не рядом с LaTeX.

## Оглавление (sources)

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
| — | **часть «Этажи вверх»** | |
| 9 | `chapters/09-floors-preface.tex` | От пола к трём этажам |
| 10 | `chapters/10-floor0.tex` | Этаж 0: планковский пол |
| 11 | `chapters/11-floor1.tex` | Этаж 1: облако $\rho_\Theta$, $\varepsilon$-оболочки |
| 12 | `chapters/12-floor2.tex` | Этаж 2: составной узел, кварки (схема) |
| **13** | **`chapters/07-alpha.tex`** | **Постоянная тонкой структуры** |
| 14 | `chapters/06-si-sm.tex` | Лестница $M\to T$, SI, массы, SM |
| A | `appendix/00-background.tex` | CA, Тоффоли/Фредкин, Маделунг |

Текст — связная русская проза; `model/` остаётся SSOT для кода и verify.

## Граница

- **Книга** (`book/sources/`) — монография для чтения.
- **model/** — контракт с реализацией.
- **DEVLOG.md** — impl / verify (не входят в книгу).
