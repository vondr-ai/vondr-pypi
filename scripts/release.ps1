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

function Assert-Success($Label) {
    if ($LASTEXITCODE -ne 0) {
        throw "$Label failed with exit code $LASTEXITCODE"
    }
}

Write-Step "Bumping version to $Version"
poetry version $Version
Assert-Success "Version bump"

Write-Step "Installing dependencies"
poetry install --no-interaction
Assert-Success "Dependency install"

if (-not $SkipTests) {
    Write-Step "Running tests"
    poetry run pytest
    Assert-Success "Tests"
} else {
    Write-Host "Skipping tests per flag" -ForegroundColor Yellow
}

Write-Step "Building distributions"
poetry build
Assert-Success "Build"

Write-Step "Publishing to $Repository"
if ($Repository -eq "pypi") {
    poetry publish --no-interaction
} else {
    poetry publish --no-interaction --repository $Repository
}
Assert-Success "Publish"

if (Test-Path .git) {
    Write-Step "Committing and tagging release"
    git add .
    if (-not (git diff --cached --quiet 2>$null)) {
        git commit -m "Release v$Version"
        Assert-Success "Commit"
    } else {
        Write-Host "No changes to commit" -ForegroundColor Yellow
    }

    $tag = "v$Version"
    git show-ref --verify --quiet "refs/tags/$tag"
    $tagExists = $LASTEXITCODE -eq 0
    if (-not $tagExists) {
        git tag -a $tag -m $tag
        Assert-Success "Tag $tag"
    } else {
        Write-Host "Tag $tag already exists, skipping tag creation" -ForegroundColor Yellow
    }

    $remotes = git remote
    if ($remotes -and $remotes.Trim().Length -gt 0) {
        git push --follow-tags
        Assert-Success "Push"
    } else {
        Write-Host "No git remote configured; skipped push" -ForegroundColor Yellow
    }
} else {
    Write-Host "Git repository not initialized; skipped commit/tag/push" -ForegroundColor Yellow
}

Write-Host "`nRelease complete." -ForegroundColor Green
