import argparse
import csv
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


PROJECT_ROOT = Path(r"D:\Database_Project\NoSE-Reproduction")
RESULTS_DIR = PROJECT_ROOT / "experiments" / "results"


def font(size, bold=False):
    candidates = [
        r"C:\Windows\Fonts\arialbd.ttf" if bold else r"C:\Windows\Fonts\arial.ttf",
        r"C:\Windows\Fonts\segoeuib.ttf" if bold else r"C:\Windows\Fonts\segoeui.ttf",
    ]
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size=size)
    return ImageFont.load_default()


def load_rows(paths):
    rows = []
    for path in paths:
        size_label = path.stem.replace("air_pollution_cassandra_", "").replace("_summary", "")
        with path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                row["dataset_size"] = size_label
                rows.append(row)
    return rows


def draw_grouped_bars(draw, rows, metric, x, y, width, body_font):
    query_types = sorted({row["query_type"] for row in rows})
    sizes = sorted({row["dataset_size"] for row in rows}, key=lambda value: int(value) if value.isdigit() else value)
    max_value = max(float(row[metric]) for row in rows) if rows else 1.0
    colors = [(44, 123, 182), (68, 155, 120), (213, 103, 61)]
    group_gap = 34
    bar_h = 18

    current_y = y
    for query_type in query_types:
        draw.text((x, current_y), query_type, fill=(25, 35, 50), font=body_font)
        current_y += 28
        for idx, size in enumerate(sizes):
            match = [row for row in rows if row["query_type"] == query_type and row["dataset_size"] == size]
            if not match:
                continue
            value = float(match[0][metric])
            fill_w = int(width * value / max_value)
            draw.rounded_rectangle((x, current_y, x + width, current_y + bar_h), radius=5, fill=(232, 236, 241))
            draw.rounded_rectangle((x, current_y, x + fill_w, current_y + bar_h), radius=5, fill=colors[idx % len(colors)])
            draw.text((x + width + 12, current_y - 2), f"{size}: {value:.1f} ms", fill=(54, 62, 74), font=body_font)
            current_y += 30
        current_y += group_gap


def main():
    parser = argparse.ArgumentParser(description="Plot Cassandra smoke benchmark summaries.")
    parser.add_argument("--summaries", nargs="+", default=[str(path) for path in RESULTS_DIR.glob("air_pollution_cassandra_*_summary.csv")])
    parser.add_argument("--out", default=str(RESULTS_DIR / "air_pollution_cassandra_benchmark_summary.png"))
    args = parser.parse_args()

    paths = [Path(path) for path in args.summaries if Path(path).exists()]
    if not paths:
        raise SystemExit("No summary CSV files found.")

    rows = load_rows(paths)
    query_types = sorted({row["query_type"] for row in rows})
    sizes = sorted({row["dataset_size"] for row in rows}, key=lambda value: int(value) if value.isdigit() else value)
    dynamic_height = 220 + len(query_types) * (60 + len(sizes) * 30) + 80
    image = Image.new("RGB", (1300, dynamic_height), "white")
    draw = ImageDraw.Draw(image)
    title_font = font(34, bold=True)
    subtitle_font = font(21)
    body_font = font(18)

    draw.text((50, 38), "Synthetic Air Pollution Cassandra Benchmark", fill=(20, 28, 40), font=title_font)
    draw.text((50, 85), "Smoke benchmark summary by dataset size and query behavior", fill=(82, 92, 108), font=subtitle_font)

    draw.text((50, 140), "Mean Latency", fill=(20, 28, 40), font=subtitle_font)
    draw_grouped_bars(draw, rows, "mean_ms", 50, 180, 360, body_font)

    draw.text((700, 140), "P95 Latency", fill=(20, 28, 40), font=subtitle_font)
    draw_grouped_bars(draw, rows, "p95_ms", 700, 180, 360, body_font)

    draw.text(
        (50, dynamic_height - 45),
        "Note: cqlsh smoke benchmark includes docker exec and client startup overhead; use for trend comparison, not final paper-grade latency.",
        fill=(105, 114, 128),
        font=body_font,
    )

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    image.save(out)
    print(out)


if __name__ == "__main__":
    main()
