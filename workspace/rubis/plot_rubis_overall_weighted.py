#!/usr/bin/env python3
"""Plot Fig. 18-style overall weighted RUBiS response time."""

from __future__ import annotations

import argparse
import csv
import html
from collections import defaultdict
from pathlib import Path


SCHEMA_ORDER = ["nose", "baseline", "expert"]
SCHEMA_DISPLAY = {
    "baseline": "Normalized Baseline",
    "expert": "Expert",
    "nose": "NoSE",
}
COLORS = {
    "baseline": "#8a8f98",
    "expert": "#2f6f9f",
    "nose": "#d69b2d",
}


def schema_key(label: str) -> str:
    if "baseline" in label:
        return "baseline"
    if "expert" in label:
        return "expert"
    if "nose" in label:
        return "nose"
    raise ValueError(f"Cannot infer schema key from label: {label}")


def group_weighted_average(path: Path) -> tuple[str, float]:
    rows_by_group: dict[str, list[tuple[float, float]]] = defaultdict(list)
    label = ""

    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            label = row["label"]
            rows_by_group[row["group"]].append((float(row["mean"]) * 1000, float(row["weight"])))

    group_means = []
    for rows in rows_by_group.values():
        group_mean = sum(mean for mean, _ in rows)
        group_weight = rows[0][1]
        group_means.append((group_mean, group_weight))

    total_weight = sum(weight for _, weight in group_means)
    weighted = sum(mean * weight for mean, weight in group_means) / total_weight
    return schema_key(label), weighted


def text(x: float, y: float, content: str, **attrs: str) -> str:
    attr = " ".join(f'{key.replace("_", "-")}="{html.escape(str(value))}"' for key, value in attrs.items())
    return f'<text x="{x:.1f}" y="{y:.1f}" {attr}>{html.escape(content)}</text>'


def rect(x: float, y: float, width: float, height: float, **attrs: str) -> str:
    attr = " ".join(f'{key.replace("_", "-")}="{html.escape(str(value))}"' for key, value in attrs.items())
    return f'<rect x="{x:.1f}" y="{y:.1f}" width="{width:.1f}" height="{height:.1f}" {attr}/>'


def line(x1: float, y1: float, x2: float, y2: float, **attrs: str) -> str:
    attr = " ".join(f'{key.replace("_", "-")}="{html.escape(str(value))}"' for key, value in attrs.items())
    return f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" {attr}/>'


def render_svg(results: dict[str, dict[str, float]], title: str) -> str:
    workloads = list(results)
    max_value = max(results[workload][schema] for workload in workloads for schema in SCHEMA_ORDER)

    width = 980
    height = 610
    left = 90
    right = 40
    top = 90
    bottom = 92
    plot_width = width - left - right
    plot_height = height - top - bottom
    group_width = plot_width / len(workloads)
    bar_width = 58

    def y_for(value: float) -> float:
        return top + plot_height - (value / max_value) * plot_height

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        "<style>",
        "text{font-family:Arial, Helvetica, sans-serif; fill:#252a31}",
        ".title{font-size:22px;font-weight:700}",
        ".subtitle{font-size:12px;fill:#555f6d}",
        ".axis{font-size:12px;fill:#5a6472}",
        ".label{font-size:13px;font-weight:700}",
        ".value{font-size:11px;fill:#1f2937;font-weight:700}",
        "</style>",
        rect(0, 0, width, height, fill="#ffffff"),
        text(26, 38, title, class_="title"),
        text(26, 60, "Group-weighted average response time by workload. Lower is better.", class_="subtitle"),
    ]

    legend_x = width - 480
    for idx, schema in enumerate(SCHEMA_ORDER):
        lx = legend_x + idx * 150
        parts.append(rect(lx, 24, 16, 16, fill=COLORS[schema], rx="2"))
        parts.append(text(lx + 22, 37, SCHEMA_DISPLAY[schema], class_="axis"))

    ticks = 5
    for i in range(ticks + 1):
        value = max_value * i / ticks
        y = y_for(value)
        parts.append(line(left, y, left + plot_width, y, stroke="#e1e6ed", stroke_width="1"))
        parts.append(text(42, y + 4, f"{value:.0f}", class_="axis"))
    parts.append(text(18, top - 18, "ms", class_="axis"))
    parts.append(line(left, top, left, top + plot_height, stroke="#aeb6c2", stroke_width="1"))
    parts.append(line(left, top + plot_height, left + plot_width, top + plot_height, stroke="#aeb6c2", stroke_width="1"))

    for workload_index, workload in enumerate(workloads):
        center = left + group_width * workload_index + group_width / 2
        start_x = center - (len(SCHEMA_ORDER) * bar_width + (len(SCHEMA_ORDER) - 1) * 18) / 2
        for schema_index, schema in enumerate(SCHEMA_ORDER):
            value = results[workload][schema]
            x = start_x + schema_index * (bar_width + 18)
            y = y_for(value)
            h = top + plot_height - y
            parts.append(rect(x, y, bar_width, h, fill=COLORS[schema], rx="3"))
            parts.append(text(x + 6, y - 8, f"{value:.2f}", class_="value"))
        parts.append(text(center - 30, top + plot_height + 34, workload, class_="label"))

    parts.append(
        text(
            26,
            height - 26,
            "Note: this chart follows Fig. 18 style: workload-level weighted averages only, not per-action bars.",
            class_="subtitle",
        )
    )
    parts.append("</svg>")
    return "\n".join(parts)


def main() -> None:
    parser = argparse.ArgumentParser(description="Plot Fig. 18-style RUBiS weighted averages.")
    parser.add_argument("--browsing", nargs=3, required=True, type=Path)
    parser.add_argument("--bidding", nargs=3, required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--summary-csv", type=Path)
    parser.add_argument(
        "--title",
        default="RUBiS Medium 5x: Weighted Average Response Time",
    )
    args = parser.parse_args()

    results = {"Browsing": {}, "Bidding": {}}
    for path in args.browsing:
        schema, value = group_weighted_average(path)
        results["Browsing"][schema] = value
    for path in args.bidding:
        schema, value = group_weighted_average(path)
        results["Bidding"][schema] = value

    if args.summary_csv:
        args.summary_csv.parent.mkdir(parents=True, exist_ok=True)
        with args.summary_csv.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(["workload", "schema", "group_weighted_avg_ms"])
            for workload, by_schema in results.items():
                for schema in SCHEMA_ORDER:
                    writer.writerow([workload, SCHEMA_DISPLAY[schema], f"{by_schema[schema]:.3f}"])

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(render_svg(results, args.title), encoding="utf-8")
    print(f"Wrote {args.out}")
    if args.summary_csv:
        print(f"Wrote {args.summary_csv}")


if __name__ == "__main__":
    main()
