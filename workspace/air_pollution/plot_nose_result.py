from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


OUT = Path(r"D:\Database_Project\NoSE-Reproduction\experiments\results\air_pollution_nose_summary.png")

indexes = [
    ("I1", "Pollutant trend index", 5390),
    ("I2", "Station-month summary index", 4620),
]

queries = [
    ("PollutantTrend", 40, "I1"),
    ("StationMonthlySummary", 30, "I2"),
    ("StationPollutantRange", 20, "I2 + filter"),
]


def font(size, bold=False):
    candidates = [
        r"C:\Windows\Fonts\arialbd.ttf" if bold else r"C:\Windows\Fonts\arial.ttf",
        r"C:\Windows\Fonts\segoeuib.ttf" if bold else r"C:\Windows\Fonts\segoeui.ttf",
    ]
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size=size)
    return ImageFont.load_default()


def bar(draw, x, y, width, height, value, max_value, color, label, fnt):
    draw.rounded_rectangle((x, y, x + width, y + height), radius=6, fill=(232, 236, 241))
    filled = int(width * value / max_value)
    draw.rounded_rectangle((x, y, x + filled, y + height), radius=6, fill=color)
    draw.text((x, y - 24), label, fill=(32, 37, 45), font=fnt)
    draw.text((x + width + 14, y + 5), str(value), fill=(32, 37, 45), font=fnt)


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)

    image = Image.new("RGB", (1200, 760), "white")
    draw = ImageDraw.Draw(image)

    title_font = font(34, bold=True)
    subtitle_font = font(20)
    body_font = font(20)
    small_font = font(17)

    draw.text((50, 36), "NoSE Air Pollution Read-Only Result", fill=(20, 28, 40), font=title_font)
    draw.text(
        (50, 82),
        "Dataset model: 1 station, 11 pollutants, 55 monthly measurements",
        fill=(85, 95, 110),
        font=subtitle_font,
    )

    draw.text((50, 140), "Index Size", fill=(20, 28, 40), font=subtitle_font)
    max_index = max(size for _, _, size in indexes)
    colors = [(36, 118, 182), (56, 150, 122)]
    for i, (name, label, size) in enumerate(indexes):
        bar(draw, 50, 195 + i * 88, 530, 34, size, max_index, colors[i], f"{name}: {label}", body_font)

    draw.text((660, 140), "Workload Weight", fill=(20, 28, 40), font=subtitle_font)
    max_weight = max(weight for _, weight, _ in queries)
    for i, (name, weight, target) in enumerate(queries):
        bar(draw, 660, 195 + i * 88, 360, 34, weight, max_weight, (207, 104, 65), name, body_font)
        draw.text((660, 237 + i * 88), f"uses {target}", fill=(85, 95, 110), font=small_font)

    draw.line((50, 470, 1150, 470), fill=(215, 222, 232), width=2)
    draw.text((50, 510), "Query Plan Mapping", fill=(20, 28, 40), font=subtitle_font)

    rows = [
        ("PollutantTrend", "PollutantID -> Month ordered values", "I1"),
        ("StationMonthlySummary", "StationID + Month -> pollutant values", "I2"),
        ("StationPollutantRange", "StationID + PollutantID + Month range", "I2 + filter"),
    ]
    y = 560
    for query, pattern, idx in rows:
        draw.rounded_rectangle((50, y - 10, 1150, y + 42), radius=8, fill=(247, 249, 252), outline=(220, 226, 235))
        draw.text((70, y), query, fill=(36, 60, 90), font=body_font)
        draw.text((360, y), pattern, fill=(42, 48, 57), font=body_font)
        draw.text((1010, y), idx, fill=(20, 88, 72), font=body_font)
        y += 62

    draw.text(
        (50, 720),
        "Note: I1/I2 are report-friendly aliases; raw NoSE IDs are generated automatically at runtime.",
        fill=(105, 114, 128),
        font=small_font,
    )

    image.save(OUT)
    print(OUT)


if __name__ == "__main__":
    main()
