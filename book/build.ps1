#!/usr/bin/env pwsh
# Build book/out/main.pdf from book/sources/main.tex (XeLaTeX × 3)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$Root = $PSScriptRoot
$Sources = Join-Path $Root 'sources'
$Out = Join-Path $Root 'out'
$JobName = 'main'

if (-not (Test-Path (Join-Path $Sources 'main.tex'))) {
    throw "Missing sources/main.tex — run from book/ root"
}

New-Item -ItemType Directory -Force -Path $Out | Out-Null

Push-Location $Sources
try {
    foreach ($pass in 1..3) {
        Write-Host "xelatex pass $pass/3 ..."
        & xelatex -interaction=nonstopmode -halt-on-error -output-directory="$Out" -jobname="$JobName" main.tex
        if ($LASTEXITCODE -ne 0) {
            throw "xelatex failed (exit $LASTEXITCODE) on pass $pass"
        }
    }

    $pdf = Join-Path $Out "$JobName.pdf"
    if (-not (Test-Path $pdf)) {
        throw "PDF not produced: $pdf"
    }
    Write-Host "Built: $pdf"
}
finally {
    Pop-Location
}
