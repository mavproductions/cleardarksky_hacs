# Helper script to create a new release (PowerShell version)
# Usage: .\release.ps1 1.2.1

param(
    [Parameter(Mandatory=$true)]
    [string]$Version
)

$ErrorActionPreference = "Stop"

Write-Host "Creating release v$Version..." -ForegroundColor Cyan

# Update manifest.json version
Write-Host "Updating manifest.json..." -ForegroundColor Yellow
$manifestPath = "custom_components\cleardarksky\manifest.json"
$manifest = Get-Content $manifestPath -Raw
$manifest = $manifest -replace '"version": "[^"]*"', "`"version`": `"$Version`""
Set-Content $manifestPath $manifest

# Check if CHANGELOG.md needs updating
$changelogContent = Get-Content "CHANGELOG.md" -Raw
if (-not ($changelogContent -match "\[$Version\]")) {
    Write-Host ""
    Write-Host "⚠️  CHANGELOG.md does not contain version $Version" -ForegroundColor Red
    Write-Host "Please update CHANGELOG.md before continuing." -ForegroundColor Yellow
    Write-Host ""
    $response = Read-Host "Open CHANGELOG.md now? (y/n)"
    if ($response -eq 'y') {
        notepad CHANGELOG.md
    }
    exit 1
}

# Show changes
Write-Host ""
Write-Host "Changes to be released:" -ForegroundColor Cyan
git diff custom_components/cleardarksky/manifest.json

Write-Host ""
$response = Read-Host "Create release v$Version? (y/n)"
if ($response -ne 'y') {
    Write-Host "Release cancelled." -ForegroundColor Red
    git checkout custom_components/cleardarksky/manifest.json
    exit 1
}

# Commit and tag
git add custom_components/cleardarksky/manifest.json CHANGELOG.md
git commit -m "Release v$Version"
git tag -a "v$Version" -m "Release v$Version"

Write-Host ""
Write-Host "✅ Release prepared locally!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. Review the commit: git show HEAD"
Write-Host "  2. Push to GitHub: git push origin main --tags"
Write-Host "  3. GitHub Actions will automatically create the release"
Write-Host ""
Write-Host "Or to cancel:" -ForegroundColor Yellow
Write-Host "  git reset HEAD~1"
Write-Host "  git tag -d v$Version"
