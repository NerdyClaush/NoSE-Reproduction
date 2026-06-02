import argparse
import csv
import json
import random
from pathlib import Path


POLLUTANTS = [
    ("CH4", "ppm", 2.10, 0.10),
    ("CO", "ppm", 0.28, 0.08),
    ("NMHC", "ppm", 0.05, 0.02),
    ("NO", "ppb", 1.80, 0.90),
    ("NO2", "ppb", 8.40, 2.00),
    ("NOx", "ppb", 10.20, 3.00),
    ("O3", "ppb", 34.50, 5.00),
    ("PM10", "ug/m3", 24.00, 8.00),
    ("PM2.5", "ug/m3", 12.00, 5.00),
    ("SO2", "ppb", 1.15, 0.45),
    ("THC", "ppm", 2.17, 0.12),
]

STATION_NAMES = [
    "Keelung",
    "Taipei",
    "NewTaipei",
    "Taoyuan",
    "Hsinchu",
    "Miaoli",
    "Taichung",
    "Changhua",
    "Yunlin",
    "Chiayi",
    "Tainan",
    "Kaohsiung",
    "Pingtung",
    "Yilan",
    "Hualien",
    "Taitung",
    "Nantou",
    "Penghu",
    "Kinmen",
    "Lienchiang",
    "Banqiao",
    "Sanchong",
    "Zhongli",
    "Zhubei",
    "Fengyuan",
    "Dali",
    "Xitun",
    "Douliu",
    "Xinying",
    "Fengshan",
    "Zuoying",
    "Xiaogang",
    "Linyuan",
    "Chaozhou",
    "Suao",
    "Yuli",
    "Guanshan",
    "Magong",
    "Matsu",
    "Yangmingshan",
]

REGIONS = ["North", "Central", "South", "East", "Islands"]
STATION_TYPES = ["urban", "suburban", "industrial", "traffic", "background"]
TYPE_BIAS = {
    "urban": 1.08,
    "suburban": 1.00,
    "industrial": 1.22,
    "traffic": 1.16,
    "background": 0.86,
}
POLLUTANT_TYPE_BIAS = {
    "PM2.5": {"industrial": 1.28, "traffic": 1.16, "background": 0.80},
    "PM10": {"industrial": 1.24, "traffic": 1.12, "background": 0.82},
    "NO": {"traffic": 1.35, "industrial": 1.12, "background": 0.76},
    "NO2": {"traffic": 1.30, "industrial": 1.10, "background": 0.78},
    "NOx": {"traffic": 1.32, "industrial": 1.12, "background": 0.78},
    "O3": {"background": 1.15, "traffic": 0.92, "industrial": 0.96},
    "SO2": {"industrial": 1.42, "background": 0.70},
}


def month_sequence(start_year, start_month, count):
    year = start_year
    month = start_month
    for _ in range(count):
        yield f"{year:04d}-{month:02d}"
        month += 1
        if month == 13:
            year += 1
            month = 1


def season_for(month_text):
    month = int(month_text[-2:])
    if month in (3, 4, 5):
        return "spring"
    if month in (6, 7, 8):
        return "summer"
    if month in (9, 10, 11):
        return "autumn"
    return "winter"


def seasonal_bias(pollutant_id, season):
    winter_high = {"PM2.5", "PM10", "NO", "NO2", "NOx", "CO"}
    summer_high = {"O3"}
    if pollutant_id in winter_high and season == "winter":
        return 1.18
    if pollutant_id in winter_high and season == "summer":
        return 0.88
    if pollutant_id in summer_high and season == "summer":
        return 1.20
    if pollutant_id in summer_high and season == "winter":
        return 0.86
    return 1.0


def clamp(value):
    return max(value, 0.0)


def write_csv(path, fieldnames, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(description="Generate synthetic air pollution data for NoSE/Cassandra smoke benchmarks.")
    parser.add_argument("--rows", type=int, default=10000, help="Number of monthly measurement rows to generate.")
    parser.add_argument("--stations", type=int, default=20, help="Number of synthetic stations.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed.")
    parser.add_argument(
        "--out-dir",
        default=r"D:\Database_Project\NoSE-Reproduction\experiments\data\air_pollution_synthetic",
        help="Output directory.",
    )
    args = parser.parse_args()

    if args.stations < 1:
        raise SystemExit("--stations must be at least 1")

    random.seed(args.seed)
    out_dir = Path(args.out_dir)

    station_count = min(args.stations, len(STATION_NAMES))
    stations = [
        {
            "station_id": f"S{i + 1:03d}",
            "station_name": STATION_NAMES[i],
            "region_name": REGIONS[i % len(REGIONS)],
            "station_type": STATION_TYPES[i % len(STATION_TYPES)],
            "population_band": ["low", "medium", "high"][i % 3],
        }
        for i in range(station_count)
    ]

    months_needed = max(1, (args.rows + (station_count * len(POLLUTANTS)) - 1) // (station_count * len(POLLUTANTS)))
    months = list(month_sequence(2020, 1, months_needed))

    measurements = []
    measurement_no = 1
    for month in months:
        season = season_for(month)
        for station in stations:
            station_bias = TYPE_BIAS[station["station_type"]] + random.uniform(-0.08, 0.08)
            for pollutant_id, unit, base, spread in POLLUTANTS:
                if measurement_no > args.rows:
                    break
                type_bias = POLLUTANT_TYPE_BIAS.get(pollutant_id, {}).get(station["station_type"], 1.0)
                expected = base * seasonal_bias(pollutant_id, season) * station_bias * type_bias
                value = clamp(random.gauss(expected, spread / 3.0))
                measurements.append(
                    {
                        "measurement_id": f"M{measurement_no:08d}",
                        "station_id": station["station_id"],
                        "station_name": station["station_name"],
                        "region_name": station["region_name"],
                        "station_type": station["station_type"],
                        "population_band": station["population_band"],
                        "pollutant_id": pollutant_id,
                        "pollutant_name": pollutant_id,
                        "unit": unit,
                        "month": month,
                        "season": season,
                        "average_value": f"{value:.4f}",
                        "note": "",
                    }
                )
                measurement_no += 1
            if measurement_no > args.rows:
                break
        if measurement_no > args.rows:
            break

    base_fields = [
        "measurement_id",
        "station_id",
        "station_name",
        "region_name",
        "station_type",
        "population_band",
        "pollutant_id",
        "pollutant_name",
        "unit",
        "month",
        "season",
        "average_value",
        "note",
    ]
    write_csv(out_dir / "measurements_normalized.csv", base_fields, measurements)

    write_csv(
        out_dir / "measurements_by_pollutant.csv",
        ["pollutant_id", "month", "measurement_id", "average_value", "note", "station_id", "region_name", "station_type"],
        [
            {
                "pollutant_id": row["pollutant_id"],
                "month": row["month"],
                "measurement_id": row["measurement_id"],
                "average_value": row["average_value"],
                "note": row["note"],
                "station_id": row["station_id"],
                "region_name": row["region_name"],
                "station_type": row["station_type"],
            }
            for row in measurements
        ],
    )

    write_csv(
        out_dir / "measurements_by_station_month.csv",
        [
            "station_id",
            "month",
            "measurement_id",
            "pollutant_id",
            "average_value",
            "pollutant_name",
            "unit",
            "region_name",
            "station_type",
            "note",
        ],
        [
            {
                "station_id": row["station_id"],
                "month": row["month"],
                "measurement_id": row["measurement_id"],
                "pollutant_id": row["pollutant_id"],
                "average_value": row["average_value"],
                "pollutant_name": row["pollutant_name"],
                "unit": row["unit"],
                "region_name": row["region_name"],
                "station_type": row["station_type"],
                "note": row["note"],
            }
            for row in measurements
        ],
    )

    write_csv(
        out_dir / "measurements_by_station_pollutant.csv",
        [
            "station_id",
            "pollutant_id",
            "month",
            "measurement_id",
            "average_value",
            "pollutant_name",
            "unit",
            "region_name",
            "station_type",
            "note",
        ],
        [
            {
                "station_id": row["station_id"],
                "pollutant_id": row["pollutant_id"],
                "month": row["month"],
                "measurement_id": row["measurement_id"],
                "average_value": row["average_value"],
                "pollutant_name": row["pollutant_name"],
                "unit": row["unit"],
                "region_name": row["region_name"],
                "station_type": row["station_type"],
                "note": row["note"],
            }
            for row in measurements
        ],
    )

    schema = """CREATE KEYSPACE IF NOT EXISTS air_pollution WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1};

USE air_pollution;

DROP TABLE IF EXISTS measurements_by_pollutant;
DROP TABLE IF EXISTS measurements_by_station_month;
DROP TABLE IF EXISTS measurements_by_station_pollutant;

CREATE TABLE measurements_by_pollutant (
  pollutant_id text,
  month text,
  measurement_id text,
  average_value double,
  note text,
  station_id text,
  region_name text,
  station_type text,
  PRIMARY KEY ((pollutant_id), month, measurement_id)
);

CREATE TABLE measurements_by_station_month (
  station_id text,
  month text,
  measurement_id text,
  pollutant_id text,
  average_value double,
  pollutant_name text,
  unit text,
  region_name text,
  station_type text,
  note text,
  PRIMARY KEY ((station_id), month, measurement_id, pollutant_id)
);

CREATE TABLE measurements_by_station_pollutant (
  station_id text,
  pollutant_id text,
  month text,
  measurement_id text,
  average_value double,
  pollutant_name text,
  unit text,
  region_name text,
  station_type text,
  note text,
  PRIMARY KEY ((station_id, pollutant_id), month, measurement_id)
);
"""
    (out_dir / "schema.cql").write_text(schema, encoding="utf-8")

    manifest = {
        "rows": len(measurements),
        "stations": station_count,
        "pollutants": len(POLLUTANTS),
        "months": len(months),
        "month_start": months[0],
        "month_end": months[-1],
        "regions": REGIONS,
        "station_types": STATION_TYPES,
        "seed": args.seed,
        "dimension_formula": "Station x Pollutant x Month, with region/station_type/population_band attributes",
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    print(f"Generated {len(measurements)} rows in {out_dir}")
    print(out_dir / "measurements_normalized.csv")
    print(out_dir / "measurements_by_pollutant.csv")
    print(out_dir / "measurements_by_station_month.csv")
    print(out_dir / "measurements_by_station_pollutant.csv")
    print(out_dir / "schema.cql")
    print(out_dir / "manifest.json")


if __name__ == "__main__":
    main()
