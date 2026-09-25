#!/usr/bin/env pwsh
# Build book/out/main.pdf from book/sources/main.tex (XeLaTeX × 3)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$Root = $PSScriptRoot
$Sources = Join-Path $Root 'sources'
$Out = Join-Path $Root 'out'
$JobName = 'main'

function Test-FileWritableExclusive {
    param([Parameter(Mandatory)][string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) { return $true }
    try {
        $fs = [System.IO.File]::Open(
            $Path,
            [System.IO.FileMode]::Open,
            [System.IO.FileAccess]::ReadWrite,
            [System.IO.FileShare]::None
        )
        $fs.Close()
        $fs.Dispose()
        return $true
    } catch {
        return $false
    }
}

function Stop-ProcessesLockingPdf {
    param([Parameter(Mandatory)][string]$PdfPath)

    if (Test-FileWritableExclusive -Path $PdfPath) { return }

    $pdfFull = (Resolve-Path -LiteralPath $PdfPath).Path
    Write-Host "PDF locked: $pdfFull — stopping viewer processes..."

    $viewerNames = @(
        'SumatraPDF',
        'AcroRd32', 'Acrobat', 'AcrobatDC',
        'FoxitReader', 'FoxitPDFReader',
        'PDFXEdit', 'PDFXCview',
        'Okular', 'mupdf',
        'NitroPDF', 'NitroPDFReader',
        'evince', 'zathura'
    )

    foreach ($name in $viewerNames) {
        Get-Process -Name $name -ErrorAction SilentlyContinue | ForEach-Object {
            Write-Host "  stop $($_.ProcessName) pid=$($_.Id)"
            Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
        }
    }

    foreach ($browser in @('msedge', 'chrome')) {
        Get-Process -Name $browser -ErrorAction SilentlyContinue | ForEach-Object {
            try {
                $cmd = (Get-CimInstance Win32_Process -Filter "ProcessId = $($_.Id)").CommandLine
                if ($cmd -and ($cmd -like "*$pdfFull*" -or $cmd -like "*main.pdf*")) {
                    Write-Host "  stop $($_.ProcessName) pid=$($_.Id) (opened PDF)"
                    Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
                }
            } catch {
                # ignore WMI failures
            }
        }
    }

    Start-Sleep -Milliseconds 400

    if (-not (Test-FileWritableExclusive -Path $PdfPath)) {
        throw @"
PDF still locked after stopping common viewers: $pdfFull
Close the viewer manually or end the process holding the file, then rerun build.ps1.
"@
    }
    Write-Host "PDF unlocked."
}

if (-not (Test-Path (Join-Path $Sources 'main.tex'))) {
    throw "Missing sources/main.tex — run from book/ root"
}

New-Item -ItemType Directory -Force -Path $Out | Out-Null
$pdf = Join-Path $Out "$JobName.pdf"
Stop-ProcessesLockingPdf -PdfPath $pdf

Push-Location $Sources
try {
    foreach ($pass in 1..3) {
        Write-Host "xelatex pass $pass/3 ..."
        & xelatex -interaction=nonstopmode -halt-on-error -output-directory="$Out" -jobname="$JobName" main.tex
        if ($LASTEXITCODE -ne 0) {
            throw "xelatex failed (exit $LASTEXITCODE) on pass $pass"
        }
    }

    if (-not (Test-Path $pdf)) {
        throw "PDF not produced: $pdf"
    }
    Write-Host "Built: $pdf"
}
finally {
    Pop-Location
}
