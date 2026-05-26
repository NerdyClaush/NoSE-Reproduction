param(
  [string]$InputDir = ".\handoff"
)

$ErrorActionPreference = "Stop"

$Root = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$In = Join-Path $Root $InputDir

if (!(Test-Path $In)) {
  throw "Input directory not found: $In"
}

Push-Location $Root
try {
  Write-Host "==> Loading Docker images..."
  docker load -i (Join-Path $In "nose-full-stack-images.tar")

  Write-Host "==> Creating Docker volumes if needed..."
  docker volume create nose-reproduction_mysql-rubis-data | Out-Null
  docker volume create nose-reproduction_cassandra-rubis-data | Out-Null

  Write-Host "==> Restoring MySQL volume..."
  docker run --rm `
    -v nose-reproduction_mysql-rubis-data:/volume `
    -v "${In}:/backup" `
    alpine sh -c "cd /volume && tar xzf /backup/nose-mysql-rubis-data.tar.gz"

  Write-Host "==> Restoring Cassandra volume..."
  docker run --rm `
    -v nose-reproduction_cassandra-rubis-data:/volume `
    -v "${In}:/backup" `
    alpine sh -c "cd /volume && tar xzf /backup/nose-cassandra-rubis-data.tar.gz"

  Write-Host "==> Starting database containers..."
  docker compose up -d mysql-rubis cassandra-rubis
  docker compose ps

  Write-Host ""
  Write-Host "Done. Verify with:"
  Write-Host "  docker compose ps"
  Write-Host "  docker compose run --rm nose-runner bash -lc `"rubis-write-nose-config && bundle exec nose execute rubis_baseline --mix=browsing --num-iterations=5 --repeat=1 --no-fail-on-empty --format=csv`""
}
finally {
  Pop-Location
}

