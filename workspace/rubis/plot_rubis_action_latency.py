#!/usr/bin/env python3
"""Plot RUBiS per-action response time from NoSE benchmark CSV files.

The script intentionally uses only the Python standard library so it can run
inside the reproduction environment without adding plotting dependencies.
"""

from __future__ import annotations

import argparse
import csv
import html
from collections import defaultdict
from pathlib import Path


SCHEMA_ORDER = ["baseline", "expert", "nose"]
SCHEMA_DISPLAY = {
    "baseline": "Baseline",
    "expert": "Expert",
    "nose": "NoSE",
}
COLORS = {
    "baseline": "#8a8f98",
    "expert": "#2f6f9f",
    "nose": "#d69b2d",
}
ACTION_ORDER = [
    "StoreComment",
    "PutComment",
    "RegisterItem",
    "RegisterUser",
    "StoreBuyNow",
    "BuyNow",
    "BidHistory",
    "AboutMe",
    "StoredBid",
    "UserInfo",
    "Regions",
    "SearchByRegion",
    "Categories",
    "ViewItem",
    "SearchByCategory",
]
ACTION_DISPLAY = {
    "StoreComment": "StoreComment",
    "PutComment": "PutComment",
    "RegisterItem": "RegisterItem",
    "RegisterUser": "RegisterUser",
    "StoreBuyNow": "StoreBuyNow",
    "BuyNow": "BuyNow",
    "ViewBidHistory": "BidHistory",
    "AboutMe": "AboutMe",
    "StoreBid": "StoredBid",
    "ViewUserInfo": "UserInfo",
    "BrowseRegions": "Regions",
    "SearchItemsByRegion": "SearchByRegion",
    "BrowseCategories": "Categories",
    "ViewItem": "ViewItem",
    "SearchItemsByCategory": "SearchByCategory",
}


def schema_key(label: str) -> str:
    if "baseline" in label:
        return "baseline"
    if "expert" in label:
        return "expert"
    if "nose" in label:
        return "nose"
    raise ValueError(f"Cannot infer schema key from label: {label}")


def action_label(group: str) -> str:
    return ACTION_DISPLAY.get(group, group)


def read_action_means(paths: list[Path]) -> dict[str, dict[str, dict[str, float]]]:
    grouped: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))

    for path in paths:
        with path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                grouped[action_label(row["group"])][schema_key(row["label"])].append(float(row["mean"]) * 1000)

    summary: dict[str, dict[str, dict[str, float]]] = {}
    for group, by_label in grouped.items():
        summary[group] = {}
        for label, values in by_label.items():
            summary[group][label] = {
                "statements": len(values),
                "avg_ms": sum(values) / len(values),
            }

    return summary


def write_summary_csv(summary: dict[str, dict[str, dict[str, float]]], out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["group", "lowest_schema", "baseline_ms", "expert_ms", "nose_ms"])
        for group in figure17_groups(summary):
            values = summary[group]
            lowest = min(values, key=lambda label: values[label]["avg_ms"])
            writer.writerow(
                [
                    group,
                    SCHEMA_DISPLAY.get(lowest, lowest),
                    f"{values['baseline']['avg_ms']:.3f}",
                    f"{values['expert']['avg_ms']:.3f}",
                    f"{values['nose']['avg_ms']:.3f}",
                ]
            )


def text(x: float, y: float, content: str, **attrs: str) -> str:
    attr = " ".join(f'{key.replace("_", "-")}="{html.escape(str(value))}"' for key, value in attrs.items())
    return f'<text x="{x:.1f}" y="{y:.1f}" {attr}>{html.escape(content)}</text>'


def rect(x: float, y: float, width: float, height: float, **attrs: str) -> str:
    attr = " ".join(f'{key.replace("_", "-")}="{html.escape(str(value))}"' for key, value in attrs.items())
    return f'<rect x="{x:.1f}" y="{y:.1f}" width="{width:.1f}" height="{height:.1f}" {attr}/>'


def line(x1: float, y1: float, x2: float, y2: float, **attrs: str) -> str:
    attr = " ".join(f'{key.replace("_", "-")}="{html.escape(str(value))}"' for key, value in attrs.items())
    return f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" {attr}/>'


def render_svg(summary: dict[str, dict[str, dict[str, float]]], title: str) -> str:
    groups = figure17_groups(summary)
    max_value = max(summary[group][label]["avg_ms"] for group in groups for label in SCHEMA_ORDER)

    width = 1480
    left = 235
    right = 120
    top = 100
    row_height = 54
    bar_height = 12
    plot_width = width - left - right
    height = top + len(groups) * row_height + 90

    def x_for(value: float) -> float:
        return left + (value / max_value) * plot_width

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        "<style>",
        "text{font-family:Arial, Helvetica, sans-serif; fill:#252a31}",
        ".title{font-size:22px;font-weight:700}",
        ".subtitle{font-size:12px;fill:#555f6d}",
        ".axis{font-size:11px;fill:#5a6472}",
        ".group{font-size:12px;font-weight:600}",
        ".value{font-size:10px;fill:#2f343b}",
        ".winner{font-size:10px;fill:#111827;font-weight:700}",
        "</style>",
        rect(0, 0, width, height, fill="#ffffff"),
        text(24, 38, title, class_="title"),
        text(
            24,
            60,
            "Grouped by RUBiS action. Values are mean response time of statements inside each action group; lower is better.",
            class_="subtitle",
        ),
    ]

    legend_x = width - 360
    for idx, label in enumerate(SCHEMA_ORDER):
        lx = legend_x + idx * 115
        parts.append(rect(lx, 24, 16, 16, fill=COLORS[label], rx="2"))
        parts.append(text(lx + 22, 37, SCHEMA_DISPLAY[label], class_="axis"))

    ticks = [0, max_value * 0.25, max_value * 0.5, max_value * 0.75, max_value]
    axis_y = top - 24
    parts.append(line(left, axis_y, left + plot_width, axis_y, stroke="#aeb6c2", stroke_width="1"))
    for tick in ticks:
        x = x_for(tick)
        parts.append(line(x, axis_y - 4, x, top + len(groups) * row_height - 6, stroke="#e2e7ee", stroke_width="1"))
        parts.append(text(x - 12, axis_y - 10, f"{tick:.0f}", class_="axis"))
    parts.append(text(left + plot_width - 40, axis_y - 34, "ms", class_="axis"))

    for group_index, group in enumerate(groups):
        row_y = top + group_index * row_height
        values = summary[group]
        lowest = min(values, key=lambda label: values[label]["avg_ms"])

        if group_index % 2 == 0:
            parts.append(rect(12, row_y - 20, width - 24, row_height, fill="#f7f8fa"))

        parts.append(text(24, row_y + 8, group, class_="group"))

        for label_index, label in enumerate(SCHEMA_ORDER):
            value = values[label]["avg_ms"]
            bar_y = row_y - 16 + label_index * 15
            bar_x = left
            bar_w = max(2.0, x_for(value) - left)
            parts.append(rect(bar_x, bar_y, bar_w, bar_height, fill=COLORS[label], rx="2"))
            label_text = f"{value:.3f}"
            value_x = min(bar_x + bar_w + 5, width - 76)
            cls = "winner" if label == lowest else "value"
            parts.append(text(value_x, bar_y + 10, label_text, class_=cls))

        parts.append(
            text(
                left + plot_width + 18,
                row_y + 2,
                f"min: {SCHEMA_DISPLAY[lowest]}",
                class_="winner",
            )
        )

    note_y = height - 32
    parts.append(
        text(
            24,
            note_y,
            "Interpretation: NoSE optimizes the weighted workload, so write/update actions may be slower even when overall weighted RT is lowest.",
            class_="subtitle",
        )
    )
    parts.append("</svg>")
    return "\n".join(parts)


def group_sort_key(group: str) -> tuple[int, str]:
    if group in ACTION_ORDER:
        return (ACTION_ORDER.index(group), group)
    return (len(ACTION_ORDER), group)


def figure17_groups(summary: dict[str, dict[str, dict[str, float]]]) -> list[str]:
    return [group for group in ACTION_ORDER if group in summary]


def main() -> None:
    parser = argparse.ArgumentParser(description="Plot per-action RUBiS response time.")
    parser.add_argument("csv", nargs=3, type=Path, help="Baseline, expert, and NoSE CSV files.")
    parser.add_argument("--out", required=True, type=Path, help="Output SVG path.")
    parser.add_argument("--summary-csv", type=Path, help="Optional per-action summary CSV path.")
    parser.add_argument(
        "--title",
        default="RUBiS Medium 5x Bidding: Per-Action Response Time",
        help="Chart title.",
    )
    args = parser.parse_args()

    summary = read_action_means(args.csv)
    if args.summary_csv:
        write_summary_csv(summary, args.summary_csv)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(render_svg(summary, args.title), encoding="utf-8")
    print(f"Wrote {args.out}")
    if args.summary_csv:
        print(f"Wrote {args.summary_csv}")


if __name__ == "__main__":
    main()
