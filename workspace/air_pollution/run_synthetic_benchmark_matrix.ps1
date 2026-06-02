param(
    [int[]]$Rows = @(2000, 5000, 10000),
    [int]$Stations = 20,
    [int]$Iterations = 30
)

$ErrorActionPreference = "Stop"

$projectRoot = "D:\Database_Project\NoSE-Reproduction"
$python = "C:\Users\Rachel\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"

foreach ($rowCount in $Rows) {
    $dataDir = "$projectRoot\experiments\data\air_pollution_synthetic_$rowCount"
    $resultPath = "$projectRoot\experiments\results\air_pollution_cassandra_${rowCount}.csv"

    & $python "$projectRoot\workspace\air_pollution\generate_synthetic_dataset.py" `
        --rows $rowCount `
        --stations $Stations `
        --out-dir $dataDir

    powershell -ExecutionPolicy Bypass -File "$projectRoot\workspace\air_pollution\load_synthetic_to_cassandra.ps1" `
        -DataDir $dataDir

    & $python "$projectRoot\workspace\air_pollution\benchmark_cassandra_smoke.py" `
        --iterations $Iterations `
        --stations $Stations `
        --data-dir $dataDir `
        --out $resultPath
}
