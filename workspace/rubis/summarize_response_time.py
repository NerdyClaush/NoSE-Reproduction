import argparse
import csv
from collections import defaultdict
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

    statement_average = sum(mean for _, mean, _ in measured) / len(measured)
    statement_total_weight = sum(weight for _, _, weight in measured)
    statement_weighted = (
        sum(mean * weight for _, mean, weight in measured) / statement_total_weight
    )

    grouped = defaultdict(list)
    for row, mean, weight in measured:
        grouped[row.get("group", "")].append((mean, weight))

    group_means = []
    for group_rows in grouped.values():
        group_mean = sum(mean for mean, _ in group_rows)
        group_weight = group_rows[0][1]
        group_means.append((group_mean, group_weight))

    group_average = sum(mean for mean, _ in group_means) / len(group_means)
    group_total_weight = sum(weight for _, weight in group_means)
    group_weighted = (
        sum(mean * weight for mean, weight in group_means) / group_total_weight
    )

    return {
        "queries": len(measured),
        "groups": len(group_means),
        "statement_average_response_time": statement_average,
        "statement_weighted_average_response_time": statement_weighted,
        "statement_total_weight": statement_total_weight,
        "group_average_response_time": group_average,
        "group_weighted_average_response_time": group_weighted,
        "group_total_weight": group_total_weight,
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
        "groups",
        "statement_total_weight",
        "statement_average_response_time",
        "statement_weighted_average_response_time",
        "group_total_weight",
        "group_average_response_time",
        "group_weighted_average_response_time",
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
