#!/usr/bin/env pwsh
# Build book/pdf/main.pdf — hand-written LaTeX only
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$Book = Join-Path $PSScriptRoot '.'
$PdfDir = Join-Path $Book 'pdf'
New-Item -ItemType Directory -Force -Path $PdfDir | Out-Null

Push-Location $Book
try {
    foreach ($i in 1..3) {
        xelatex -interaction=nonstopmode -output-directory=pdf main.tex 2>&1 | Out-Null
    }
    if (-not (Test-Path pdf/main.pdf)) { throw "main.pdf not produced" }
    Write-Host "Built: $PdfDir/main.pdf"
} finally {
    Pop-Location
}
