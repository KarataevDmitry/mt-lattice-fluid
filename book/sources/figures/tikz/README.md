# TikZ figures (hand-edited)

One conceptual diagram per `.tex` file — one `\begin{figure}` in the chapter.
No multi-panel composites; edit a single file when a drawing needs a fix.

Chapters include via `\input{figures/tikz/<name>.tex}`.

`scripts/render_*_figures.py` are legacy; `book/build.ps1` does not call them.
