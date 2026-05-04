# Run Desloppify scans for Python backend and TypeScript frontend separately (recommended for monorepos).
# Prerequisites: activate a venv where backend/requirements-dev.txt is installed, then run this from anywhere:
#   .\scripts\desloppify-scan.ps1
# Optional: install Cursor workflow guide once — desloppify update-skill cursor
$ErrorActionPreference = 'Stop'
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Set-Location $RepoRoot

function Resolve-Desloppify {
    $fromPath = Get-Command desloppify -ErrorAction SilentlyContinue
    if ($fromPath) {
        return $fromPath.Source
    }
    # Canonical backend venv (see backend/start.ps1 — outside OneDrive for large ML wheels)
    $studymate = 'C:\dev\venvs\studymate-v2\Scripts\desloppify.exe'
    if (Test-Path $studymate) {
        return $studymate
    }
    foreach ($rel in @(
            'backend\.venv\Scripts\desloppify.exe',
            '.venv\Scripts\desloppify.exe'
        )) {
        $candidate = Join-Path $RepoRoot $rel
        if (Test-Path $candidate) {
            return $candidate
        }
    }
    throw @"
desloppify not found. Install dev deps, then re-run (recommended venv matches backend/start.ps1):

  python -m venv C:\dev\venvs\studymate-v2
  C:\dev\venvs\studymate-v2\Scripts\pip install -r backend/requirements.txt -r backend/requirements-dev.txt
"@
}

$exe = Resolve-Desloppify
Write-Host "Using: $exe"

& $exe --lang python scan --path ./backend
& $exe --lang typescript scan --path ./frontend

Write-Host @"

Next: fix items from the queue, mark resolved, repeat:
  desloppify next
  desloppify plan   # optional: triage / reorder

State lives under .desloppify/ (gitignored). Exclude noisy paths with: desloppify exclude <path>
"@
