#!/usr/bin/env pwsh
# Build book/out/main.pdf from book/sources/main.tex (XeLaTeX × 3)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$Root = $PSScriptRoot
$Sources = Join-Path $Root 'sources'
$Out = Join-Path $Root 'out'
$JobName = 'main'

if (-not ('FileLockInspector' -as [type])) {
    Add-Type -TypeDefinition @'
using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;
using System.Text;

public static class FileLockInspector
{
    private const int CCH_RM_MAX_APP_NAME = 255;
    private const int CCH_RM_MAX_SVC_NAME = 63;
    private const int ERROR_MORE_DATA = 234;

    [StructLayout(LayoutKind.Sequential)]
    public struct RM_UNIQUE_PROCESS
    {
        public int dwProcessId;
        public long ProcessStartTime;
    }

    [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
    public struct RM_PROCESS_INFO
    {
        public RM_UNIQUE_PROCESS Process;
        [MarshalAs(UnmanagedType.ByValTStr, SizeConst = CCH_RM_MAX_APP_NAME + 1)]
        public string strAppName;
        [MarshalAs(UnmanagedType.ByValTStr, SizeConst = CCH_RM_MAX_SVC_NAME + 1)]
        public string strServiceShortName;
        public int ApplicationStatus;
        public int TSSessionId;
        [MarshalAs(UnmanagedType.Bool)]
        public bool bRestartable;
    }

    [DllImport("rstrtmgr.dll", CharSet = CharSet.Unicode)]
    private static extern int RmStartSession(out uint pSessionHandle, int dwSessionFlags, StringBuilder strSessionKey);

    [DllImport("rstrtmgr.dll", CharSet = CharSet.Unicode)]
    private static extern int RmRegisterResources(
        uint pSessionHandle,
        uint nFiles,
        string[] rgsFilenames,
        uint nApplications,
        IntPtr rgApplications,
        uint nServices,
        IntPtr rgsServiceNames);

    [DllImport("rstrtmgr.dll")]
    private static extern int RmGetList(
        uint dwSessionHandle,
        out uint pnProcInfoNeeded,
        ref uint pnProcInfo,
        [In, Out] RM_PROCESS_INFO[] rgAffectedApps,
        ref uint lpdwRebootReasons);

    [DllImport("rstrtmgr.dll")]
    private static extern int RmEndSession(uint pSessionHandle);

    public static RM_PROCESS_INFO[] GetLockingProcesses(string path)
    {
        uint handle;
        var sessionKey = new StringBuilder(256);
        int rc = RmStartSession(out handle, 0, sessionKey);
        if (rc != 0)
        {
            throw new InvalidOperationException("RmStartSession failed: " + rc);
        }

        try
        {
            rc = RmRegisterResources(handle, 1, new[] { path }, 0, IntPtr.Zero, 0, IntPtr.Zero);
            if (rc != 0)
            {
                throw new InvalidOperationException("RmRegisterResources failed: " + rc);
            }

            uint needed = 0;
            uint count = 0;
            uint rebootReasons = 0;
            var probe = Array.Empty<RM_PROCESS_INFO>();
            rc = RmGetList(handle, out needed, ref count, probe, ref rebootReasons);
            if (rc != 0 && rc != ERROR_MORE_DATA)
            {
                throw new InvalidOperationException("RmGetList failed: " + rc);
            }

            if (needed == 0)
            {
                return Array.Empty<RM_PROCESS_INFO>();
            }

            count = needed;
            var infos = new RM_PROCESS_INFO[count];
            rc = RmGetList(handle, out needed, ref count, infos, ref rebootReasons);
            if (rc != 0)
            {
                throw new InvalidOperationException("RmGetList(2) failed: " + rc);
            }

            if (count < infos.Length)
            {
                var trimmed = new RM_PROCESS_INFO[count];
                Array.Copy(infos, trimmed, count);
                return trimmed;
            }

            return infos;
        }
        finally
        {
            RmEndSession(handle);
        }
    }
}
'@
}

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

function Get-FileLockingProcesses {
    param([Parameter(Mandatory)][string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) { return @() }
    $full = (Resolve-Path -LiteralPath $Path).Path
    $self = $PID
    [FileLockInspector]::GetLockingProcesses($full) |
        Where-Object { $_.Process.dwProcessId -gt 0 -and $_.Process.dwProcessId -ne $self } |
        ForEach-Object {
            $procId = $_.Process.dwProcessId
            $name = $_.strAppName
            try {
                $proc = Get-Process -Id $procId -ErrorAction Stop
                [PSCustomObject]@{
                    Id = $procId
                    ProcessName = $proc.ProcessName
                    AppName = $name
                }
            } catch {
                [PSCustomObject]@{
                    Id = $procId
                    ProcessName = '(exited)'
                    AppName = $name
                }
            }
        }
}

function Stop-ProcessesLockingPdf {
    param([Parameter(Mandatory)][string]$PdfPath)

    if (Test-FileWritableExclusive -Path $PdfPath) { return }

    $pdfFull = (Resolve-Path -LiteralPath $PdfPath).Path
    Write-Host "PDF locked: $pdfFull"

    $lockers = @(Get-FileLockingProcesses -Path $PdfPath)
    if ($lockers.Count -eq 0) {
        throw @"
PDF is locked but Restart Manager returned no process (antivirus / shell preview?).
Close the viewer manually: $pdfFull
"@
    }

    foreach ($p in $lockers) {
        Write-Host "  stop $($p.ProcessName) pid=$($p.Id) [$($p.AppName)]"
        Stop-Process -Id $p.Id -Force -ErrorAction Stop
    }

    Start-Sleep -Milliseconds 300

    if (-not (Test-FileWritableExclusive -Path $PdfPath)) {
        $still = @(Get-FileLockingProcesses -Path $PdfPath)
        $list = ($still | ForEach-Object { "$($_.ProcessName) (pid $($_.Id))" }) -join ', '
        throw "PDF still locked: $pdfFull. Holding: $list"
    }
    Write-Host "PDF unlocked."
}

if (-not (Test-Path (Join-Path $Sources 'main.tex'))) {
    throw "Missing sources/main.tex — run from book/ root"
}

New-Item -ItemType Directory -Force -Path $Out | Out-Null
$figScript = Join-Path (Join-Path (Split-Path $Root -Parent) 'scripts') 'render_carrier_figures.py'
if (Test-Path -LiteralPath $figScript) {
    Write-Host 'render carrier figures ...'
    & python $figScript
    if ($LASTEXITCODE -ne 0) { throw "render_carrier_figures.py failed (exit $LASTEXITCODE)" }
}

$axiomFigScript = Join-Path (Join-Path (Split-Path $Root -Parent) 'scripts') 'render_axiom_figures.py'
if (Test-Path -LiteralPath $axiomFigScript) {
    & python $axiomFigScript
    if ($LASTEXITCODE -ne 0) { throw "render_axiom_figures.py failed (exit $LASTEXITCODE)" }
}
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
