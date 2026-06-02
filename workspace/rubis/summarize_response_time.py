import argparse
import csv
from pathlib import Path


def read_rows(path):
    with Path(path).open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def parse_float(value):
    if value is None or value == "":
        return None
    return float(value)


def summarize(rows):
    measured = []
    for row in rows:
        mean = parse_float(row.get("mean"))
        weight = parse_float(row.get("weight"))
        if mean is None:
            continue
        measured.append((row, mean, weight if weight is not None else 1.0))

    if not measured:
        return None

    average = sum(mean for _, mean, _ in measured) / len(measured)
    total_weight = sum(weight for _, _, weight in measured)
    weighted = sum(mean * weight for _, mean, weight in measured) / total_weight
    return {
        "queries": len(measured),
        "average_response_time": average,
        "weighted_average_response_time": weighted,
        "total_weight": total_weight,
    }


def main():
    parser = argparse.ArgumentParser(description="Summarize NoSE RUBiS response-time CSV output.")
    parser.add_argument("csv_files", nargs="+")
    parser.add_argument("--out", default=None)
    args = parser.parse_args()

    summaries = []
    for csv_file in args.csv_files:
        rows = read_rows(csv_file)
        summary = summarize(rows)
        if summary is None:
            continue
        summary["file"] = str(csv_file)
        labels = sorted({row.get("label", "") for row in rows})
        summary["label"] = labels[0] if len(labels) == 1 else ",".join(labels)
        summaries.append(summary)

    fieldnames = [
        "file",
        "label",
        "queries",
        "total_weight",
        "average_response_time",
        "weighted_average_response_time",
    ]

    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(summaries)

    writer = csv.DictWriter(open(1, "w", newline=""), fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(summaries)


if __name__ == "__main__":
    main()
