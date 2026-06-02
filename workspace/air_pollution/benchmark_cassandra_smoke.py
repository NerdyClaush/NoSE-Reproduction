import argparse
import csv
import json
import random
import subprocess
import time
from pathlib import Path


PROJECT_ROOT = Path(r"D:\Database_Project\NoSE-Reproduction")
RESULTS_DIR = PROJECT_ROOT / "experiments" / "results"
DEFAULT_DATA_DIR = PROJECT_ROOT / "experiments" / "data" / "air_pollution_synthetic"
POLLUTANTS = ["CH4", "CO", "NMHC", "NO", "NO2", "NOx", "O3", "PM10", "PM2.5", "SO2", "THC"]


def run_cql(query):
    command = [
        "docker",
        "compose",
        "-f",
        str(PROJECT_ROOT / "docker-compose.yml"),
        "exec",
        "-T",
        "cassandra-rubis",
        "cqlsh",
        "127.0.0.1",
        "9042",
        "-e",
        query,
    ]
    start = time.perf_counter()
    completed = subprocess.run(command, cwd=PROJECT_ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    elapsed_ms = (time.perf_counter() - start) * 1000.0
    return completed.returncode, elapsed_ms, completed.stdout, completed.stderr


def percentile(values, pct):
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, round((pct / 100.0) * (len(ordered) - 1)))
    return ordered[index]


def summarize(rows):
    groups = sorted({row["query_type"] for row in rows})
    summary = []
    for group in groups:
        timings = [float(row["elapsed_ms"]) for row in rows if row["query_type"] == group and row["status"] == "ok"]
        if not timings:
            continue
        summary.append(
            {
                "query_type": group,
                "count": len(timings),
                "mean_ms": f"{sum(timings) / len(timings):.3f}",
                "p50_ms": f"{percentile(timings, 50):.3f}",
                "p95_ms": f"{percentile(timings, 95):.3f}",
                "min_ms": f"{min(timings):.3f}",
                "max_ms": f"{max(timings):.3f}",
            }
        )
    return summary


def main():
    parser = argparse.ArgumentParser(description="Run a cqlsh-based Cassandra smoke benchmark for the synthetic air pollution schema.")
    parser.add_argument("--iterations", type=int, default=30)
    parser.add_argument("--stations", type=int, default=20)
    parser.add_argument("--seed", type=int, default=123)
    parser.add_argument("--data-dir", default=str(DEFAULT_DATA_DIR))
    parser.add_argument("--out", default=str(RESULTS_DIR / "air_pollution_cassandra_smoke.csv"))
    args = parser.parse_args()

    random.seed(args.seed)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    manifest_path = Path(args.data_dir) / "manifest.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        station_count = int(manifest["stations"])
        month_start = manifest["month_start"]
        month_end = manifest["month_end"]
        months = []
        year, month = [int(part) for part in month_start.split("-")]
        while True:
            months.append(f"{year:04d}-{month:02d}")
            if months[-1] == month_end:
                break
            month += 1
            if month == 13:
                year += 1
                month = 1
    else:
        station_count = args.stations
        months = [f"2020-{month:02d}" for month in range(1, 13)]
    stations = [f"S{i + 1:03d}" for i in range(station_count)]

    rows = []
    query_templates = [
        (
            "PollutantTrend",
            lambda: "SELECT month, average_value, note FROM air_pollution.measurements_by_pollutant "
            f"WHERE pollutant_id = '{random.choice(POLLUTANTS)}';",
        ),
        (
            "StationMonthlySummary",
            lambda: "SELECT average_value, pollutant_name, unit FROM air_pollution.measurements_by_station_month "
            f"WHERE station_id = '{random.choice(stations)}' AND month = '{random.choice(months)}';",
        ),
        (
            "StationPollutantRange",
            lambda: "SELECT month, average_value FROM air_pollution.measurements_by_station_pollutant "
            f"WHERE station_id = '{random.choice(stations)}' AND pollutant_id = '{random.choice(POLLUTANTS)}' "
            f"AND month >= '{months[0]}' AND month <= '{months[-1]}';",
        ),
    ]

    for iteration in range(1, args.iterations + 1):
        for query_type, factory in query_templates:
            query = factory()
            status_code, elapsed_ms, stdout, stderr = run_cql(query)
            rows.append(
                {
                    "iteration": iteration,
                    "query_type": query_type,
                    "elapsed_ms": f"{elapsed_ms:.3f}",
                    "status": "ok" if status_code == 0 else "error",
                    "query": query,
                    "stderr": stderr.strip().replace("\n", " "),
                }
            )

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["iteration", "query_type", "elapsed_ms", "status", "query", "stderr"])
        writer.writeheader()
        writer.writerows(rows)

    summary_path = out.with_name(out.stem + "_summary.csv")
    with summary_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["query_type", "count", "mean_ms", "p50_ms", "p95_ms", "min_ms", "max_ms"])
        writer.writeheader()
        writer.writerows(summarize(rows))

    print(out)
    print(summary_path)
    for row in summarize(rows):
        print(row)


if __name__ == "__main__":
    main()
