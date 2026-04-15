# Dot-source from scripts/: . (Join-Path $PSScriptRoot "Resolve-CoachingPython.ps1")
# Resolves the coaching virtualenv interpreter (same order as pre-commit-check.ps1).

function Get-CoachingPythonExecutable {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$RepoRoot
    )
    $Candidates = @(
        (Join-Path $RepoRoot "coaching\.venv\Scripts\python.exe"),
        (Join-Path $RepoRoot "coaching\.venv-ci\Scripts\python.exe")
    )
    if ($env:VIRTUAL_ENV) {
        $Candidates += (Join-Path $env:VIRTUAL_ENV "Scripts\python.exe")
    }
    foreach ($candidate in $Candidates) {
        if (Test-Path -LiteralPath $candidate) {
            return (Resolve-Path -LiteralPath $candidate).Path
        }
    }
    return $null
}
