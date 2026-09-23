#!/usr/bin/env pwsh
# Build book/pdf/main.pdf — hand-written LaTeX only
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$Book = Join-Path $PSScriptRoot '.'
$PdfDir = Join-Path $Book 'pdf'
New-Item -ItemType Directory -Force -Path $PdfDir | Out-Null

Push-Location $Book
try {
    $job = 'main-latest'
    foreach ($i in 1..3) {
        $null = xelatex -interaction=nonstopmode -output-directory=pdf -jobname=$job main.tex 2>&1
    }
    $latest = Join-Path $PdfDir "$job.pdf"
    if (-not (Test-Path $latest)) { throw "PDF not produced ($job)" }

    $main = Join-Path $PdfDir 'main.pdf'
    try {
        Copy-Item -LiteralPath $latest -Destination $main -Force
        Write-Host "Built: $main"
    }
    catch {
        Write-Warning 'main.pdf locked (close viewer); open pdf/main-latest.pdf'
        Write-Host "Built: $latest"
    }
}
finally {
    Pop-Location
}
