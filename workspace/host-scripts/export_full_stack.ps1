param(
  [string]$OutputDir = ".\handoff"
)

$ErrorActionPreference = "Stop"

$Root = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$Out = Join-Path $Root $OutputDir
New-Item -ItemType Directory -Force -Path $Out | Out-Null

Push-Location $Root
try {
  Write-Host "==> Exporting Docker images..."
  docker save -o (Join-Path $Out "nose-full-stack-images.tar") `
    nose-repro-runner:latest `
    nose-rubis-generator:latest `
    nose-repro-advisor-release:latest `
    mysql:5.7 `
    cassandra:2.1

  Write-Host "==> Stopping database containers before volume backup..."
  docker compose stop mysql-rubis cassandra-rubis

  Write-Host "==> Exporting MySQL volume..."
  docker run --rm `
    -v nose-reproduction_mysql-rubis-data:/volume `
    -v "${Out}:/backup" `
    alpine tar czf /backup/nose-mysql-rubis-data.tar.gz -C /volume .

  Write-Host "==> Exporting Cassandra volume..."
  docker run --rm `
    -v nose-reproduction_cassandra-rubis-data:/volume `
    -v "${Out}:/backup" `
    alpine tar czf /backup/nose-cassandra-rubis-data.tar.gz -C /volume .

  Write-Host "==> Restarting database containers..."
  docker compose up -d mysql-rubis cassandra-rubis

  Write-Host "==> Writing manifest..."
  $manifest = Join-Path $Out "manifest.txt"
  "NoSE Reproduction Docker handoff" | Set-Content $manifest
  "ExportedAt: $(Get-Date -Format o)" | Add-Content $manifest
  "" | Add-Content $manifest
  "Git status:" | Add-Content $manifest
  git status --short | Add-Content $manifest
  "" | Add-Content $manifest
  "Docker images:" | Add-Content $manifest
  docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.ID}}\t{{.Size}}" | Add-Content $manifest
  "" | Add-Content $manifest
  "Docker volumes:" | Add-Content $manifest
  docker volume ls | Add-Content $manifest

  Write-Host ""
  Write-Host "Done. Handoff files are in:"
  Write-Host "  $Out"
  Write-Host ""
  Get-ChildItem $Out | Select-Object Name, Length, LastWriteTime
}
finally {
  Pop-Location
}

