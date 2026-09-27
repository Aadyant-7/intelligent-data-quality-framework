"""Create a reproducible, explicitly edited public QA example from the source CSV."""

import csv
from decimal import Decimal
from pathlib import Path


DIRECTORY = Path(__file__).resolve().parent
SOURCE = DIRECTORY / "supermarket_sales_source.csv"
OUTPUT = DIRECTORY / "supermarket_sales_demo.csv"


def build() -> None:
    with SOURCE.open(newline="", encoding="utf-8-sig") as source_file:
        reader = csv.DictReader(source_file)
        fieldnames = reader.fieldnames
        rows = list(reader)
    if fieldnames is None or len(rows) != 1000:
        raise ValueError("The supermarket source should have its original 1,000 rows.")

    # Disjoint source-row groups make each deliberate change easy to audit.
    for row in rows[0:100]:
        row["Branch"] = ""                  # 100 missing values
    for row in rows[120:160]:
        row["Unit price"] = str(-Decimal(row["Unit price"]))  # 40 invalid prices
    for row in rows[200:280]:
        row["Total"] = str(Decimal(row["Total"]) + Decimal("25"))  # 80 wrong totals
    for index in range(30):
        rows[350 + index] = rows[400 + index].copy()  # 30 exact duplicates

    with OUTPUT.open("w", newline="", encoding="utf-8") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    build()
