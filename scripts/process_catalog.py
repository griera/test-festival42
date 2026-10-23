#!/usr/bin/env python3
import argparse
import csv
import json
import os
import unicodedata

SOURCE_COLUMNS = [
    "EAN", "LLIBRE", "AUTORI", "EDITORIAL", "DISTRIBUÏDOR", "TIPUS", "PVP", "TEMA", "HORARIS",
]

OUTPUT_HEADER = [
    "type", "ean", "title", "author", "publisher", "distributor", "category",
    "price", "theme", "schedule", "quantity", "location", "datetime",
]


def clean_text(text, replacements):
    # Normalize Unicode and replace non-breaking spaces with regular spaces.
    text = unicodedata.normalize("NFC", text).replace("\u00a0", " ")
    for original, corrected in replacements.items():
        text = text.replace(original, corrected)
    return text.strip()


def parse_float(val):
    """Convert numeric strings with a comma (e.g., '28,80') to float (28.80)."""
    if not val:
        return 0.0
    try:
        return float(val.replace(',', '.'))
    except ValueError:
        return 0.0


def parse_int(val):
    """Safely convert strings to integers."""
    if not val:
        return 0
    try:
        return int(val)
    except ValueError:
        return 0


def main():
    # Set up argument parser with detailed usage and execution examples
    parser = argparse.ArgumentParser(
        description="Process raw catalog CSV and convert it directly into a structured JSON payload for the web app.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Examples:
  python3 process_catalog.py data/data.csv data.json
  python3 process_catalog.py data/data.csv data.json --encoding cp1252
  python3 process_catalog.py data/data.csv data.json --replacements replacements.json --no-minify
  python3 process_catalog.py --help
""",
    )
    parser.add_argument("input_file", help="Source raw CSV file (default: data/data.csv)", nargs="?", default="data/data.csv")
    parser.add_argument("output_file", help="Generated JSON file (default: data.json)", nargs="?", default="data.json")
    parser.add_argument(
        "--encoding",
        default="utf-8-sig",
        help="Input file encoding (default: utf-8-sig)",
    )
    parser.add_argument(
        "--replacements",
        help="JSON file containing text replacements, e.g. replacements.json",
    )
    
    # Minification flags (Enabled by default)
    parser.add_argument(
        "--minify",
        dest="minify",
        action="store_true",
        help="Minify the output JSON by removing whitespace (enabled by default)",
    )
    parser.add_argument(
        "--no-minify",
        dest="minify",
        action="store_false",
        help="Disable minification and use a readable indented format",
    )
    parser.set_defaults(minify=True)

    args = parser.parse_args()

    replacements = {}
    if args.replacements:
        with open(args.replacements, encoding="utf-8") as replacements_file:
            replacements = json.load(replacements_file)

    records = []

    # Read the source CSV using its configured encoding (e.g. cp1252 / utf-8-sig).
    with open(
        args.input_file, "r", encoding=args.encoding, newline=""
    ) as source_file:
        reader = csv.reader(source_file, delimiter=";")
        header = next(reader, None)

        if header is None:
            raise SystemExit("The input file is empty.")

        # The source example ends its header with a semicolon.
        if len(header) == len(SOURCE_COLUMNS) + 1 and header[-1] == "":
            header.pop()

        if header != SOURCE_COLUMNS:
            raise SystemExit(
                "The header does not match the expected columns.\n"
                f"Expected: {SOURCE_COLUMNS}\n"
                f"Received: {header}"
            )

        for line_number, row in enumerate(reader, start=2):
            if not row or all(value == "" for value in row):
                continue

            # Remove the extra empty field caused by a trailing semicolon.
            if len(row) == len(SOURCE_COLUMNS) + 1 and row[-1] == "":
                row.pop()

            if len(row) != len(SOURCE_COLUMNS):
                raise SystemExit(
                    f"Line {line_number}: expected "
                    f"{len(SOURCE_COLUMNS)} fields, found {len(row)}."
                )

            # Clean and normalize text values across all columns
            row = [clean_text(value, replacements) for value in row]

            ean = row[0]
            title = row[1]
            author = row[2]
            publisher = row[3]
            distributor = row[4]
            category = row[5]
            
            # Handle price parsing: default to 0.0 if empty or whitespace
            raw_price = row[6].strip()
            price = parse_float(raw_price) if raw_price else 0.0
            
            theme = row[7]
            schedule = row[8]
            quantity = 0  # Default quantity to 0 since it is absent in raw source

            # Construct the ordered item dictionary matching OUTPUT_HEADER
            item = {
                "type": "book",
                "ean": ean,
                "title": title,
                "author": author,
                "publisher": publisher,
                "distributor": distributor,
                "category": category,
                "price": price,
                "theme": theme,
                "schedule": schedule,
                "quantity": quantity,
                "location": "",
                "datetime": "",
            }

            # Add local cover image path based on the EAN field
            cover_path = f"assets/covers/{ean}.webp"
            if ean and os.path.exists(cover_path):
                item["cover"] = cover_path
            else:
                item["cover"] = ""

            records.append(item)

    # Determine indentation: None removes whitespace for minification, 2 keeps it readable
    indent_value = None if args.minify else 2

    # Save the result into a structured JSON file
    with open(args.output_file, mode="w", encoding="utf-8") as json_file:
        json.dump(records, json_file, ensure_ascii=False, indent=indent_value)

    format_status = "minified (optimized)" if args.minify else "formatted (readable)"
    print(f"Process completed! Successfully converted {len(records)} records from {args.input_file} to {args.output_file} [{format_status}]")


if __name__ == "__main__":
    main()
