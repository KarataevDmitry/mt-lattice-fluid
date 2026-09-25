# TikZ figures (hand-edited)

Conceptual diagrams live here as `.tex` fragments included from chapters via `\input{figures/tikz/...}`.

Edit coordinates and arrows directly in TikZ — no matplotlib render step for these figures.

Legacy PDF pipeline (`scripts/render_*_figures.py`) remains only for 3D packing / heavy plots; run `book/build.ps1 -RenderFigures` when those need regeneration.
