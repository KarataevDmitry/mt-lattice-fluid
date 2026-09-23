#!/usr/bin/env pwsh
# Build book/pdf/main.pdf — hand-written LaTeX only
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$Book = Join-Path $PSScriptRoot '.'
$PdfDir = Join-Path $Book 'pdf'
New-Item -ItemType Directory -Force -Path $PdfDir | Out-Null

Push-Location $Book
try {
    $job = 'main'
    foreach ($i in 1..3) {
        $out = xelatex -interaction=nonstopmode -output-directory=pdf -jobname=$job main.tex 2>&1
        if ($LASTEXITCODE -ne 0 -and $out -match 'Unable to open.*main\.pdf') {
            Write-Warning 'main.pdf locked (close viewer); building main-latest.pdf'
            $job = 'main-latest'
        }
    }
    $pdf = Join-Path $PdfDir "$job.pdf"
    if (-not (Test-Path $pdf)) { throw "PDF not produced ($job)" }
    if ($job -eq 'main-latest') {
        Write-Warning 'Open pdf/main-latest.pdf — main.pdf was locked and not updated.'
    }
    Write-Host "Built: $pdf"
} finally {
    Pop-Location
}
