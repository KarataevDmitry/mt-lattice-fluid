# Книга (LaTeX)

Читаемая версия модели для людей: **не** `model/*.md` (рабочая спецификация для кода).

## Сборка

```powershell
cd book
./build.ps1
```

PDF: `book/pdf/main.pdf` (XeLaTeX, Times New Roman).

## Структура

| Глава | Файл | Содержание |
|-------|------|------------|
| Предисловие | `frontmatter.tex` | |
| 0 | `chapters/00-foundations.tex` | Основания, Thm 0.1 с доказательством |
| 1 | `chapters/01-carrier.tex` | FCC, две $c$, гекс-срез |
| 2 | `chapters/02-axioms.tex` | A1–A16, Teorem 2.3 с доказательствами |
| 3 | `chapters/03-evolution.tex` | Закон $g$, SU(2), bit budget |
| 4 | `chapters/04-macro.tex` | M→T, Teorem T-CR |
| 5 | `chapters/05-matter.tex` | Thm 5.1, lattice fluid |
| 6 | `chapters/06-si-sm.tex` | SI, $\alpha$, массы, SM |

Главы написаны **вручную** в LaTeX (теоремы, доказательства, связный текст).
`model/` остаётся SSOT для impl; расхождения --- баг книги, не модели.

## Граница

- **Книга** --- показать человеку, читать с PDF.
- **model/** --- контракт с кодом, verify.
- **DEVLOG.md** --- impl, численные проверки, open leaves.
