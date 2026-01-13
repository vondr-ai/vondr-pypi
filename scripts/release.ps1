Param(
    [Parameter(Mandatory = $true)]
    [string]$Version,

    [ValidateSet("pypi", "testpypi")]
    [string]$Repository = "pypi",

    [switch]$SkipTests
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Step($Message) {
    Write-Host "`n==> $Message" -ForegroundColor Cyan
}

Write-Step "Bumping version to $Version"
poetry version $Version

Write-Step "Installing dependencies"
poetry install --no-interaction

if (-not $SkipTests) {
    Write-Step "Running tests"
    poetry run pytest
} else {
    Write-Host "Skipping tests per flag" -ForegroundColor Yellow
}

Write-Step "Building distributions"
poetry build

Write-Step "Publishing to $Repository"
if ($Repository -eq "pypi") {
    poetry publish --no-interaction
} else {
    poetry publish --no-interaction --repository $Repository
}

if (Test-Path .git) {
    Write-Step "Committing and tagging release"
    git add .
    if (-not (git diff --cached --quiet 2>$null)) {
        git commit -m "Release v$Version"
    } else {
        Write-Host "No changes to commit" -ForegroundColor Yellow
    }

    $tag = "v$Version"
    if (-not (git rev-parse "$tag" 2>$null)) {
        git tag -a $tag -m $tag
    } else {
        Write-Host "Tag $tag already exists, skipping tag creation" -ForegroundColor Yellow
    }

    if ((git remote) -ne $null) {
        git push --follow-tags
    } else {
        Write-Host "No git remote configured; skipped push" -ForegroundColor Yellow
    }
} else {
    Write-Host "Git repository not initialized; skipped commit/tag/push" -ForegroundColor Yellow
}

Write-Host "`nRelease complete." -ForegroundColor Green

