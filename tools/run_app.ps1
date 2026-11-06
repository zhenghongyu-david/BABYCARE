# Start exactly one preview instance and record its PID for screenshot tools.
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

Get-CimInstance Win32_Process |
    Where-Object { $_.CommandLine -match 'main\.py' -and $_.Name -match 'python' } |
    ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }

$env:KIVY_NO_ARGS = "1"
$env:STAR_DATA_DIR = Join-Path $root "demo_data"
$python = Join-Path $root ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    $python = Join-Path $root ".venv313\Scripts\python.exe"
}
$out = Join-Path $root "app_stdout.log"
$err = Join-Path $root "app_stderr.log"
$p = Start-Process -FilePath $python -ArgumentList "main.py" -WorkingDirectory $root `
    -RedirectStandardOutput $out -RedirectStandardError $err -PassThru
$p.Id | Set-Content (Join-Path $root ".app_pid")
Write-Output "started $($p.Id)"
