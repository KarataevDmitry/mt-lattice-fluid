# Монография (LaTeX)

Читаемая версия теории для человека: **не** `model/*.md` (рабочая спецификация для кода).

## Сборка

```powershell
cd book
./build.ps1
```

PDF: `book/out/main.pdf` (XeLaTeX, Times New Roman, три прохода).

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
| **9** | **`chapters/07-alpha.tex`** | **Постоянная тонкой структуры** (журнал поиска $\alpha$) |
| 10 | `chapters/06-si-sm.tex` | Лестница $M\to T$, SI, массы, SM |
| A | `appendix/00-background.tex` | CA, Тоффоли/Фредкин, Маделунг |

Текст — связная русская проза; `model/` остаётся SSOT для кода и verify.

## Граница

- **Книга** (`book/sources/`) — монография для чтения.
- **model/** — контракт с реализацией.
- **DEVLOG.md** — impl / verify (не входят в книгу).
