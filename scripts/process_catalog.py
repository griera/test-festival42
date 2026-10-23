#!/usr/bin/env python3
import argparse
import csv
import json
import os
import unicodedata

# Defined expected headers
HEADER_9_COL = [
    "EAN", "LLIBRE", "AUTORI", "EDITORIAL", "DISTRIBUÏDOR", "TIPUS", "PVP", "TEMA", "HORARIS"
]

HEADER_12_COL = [
    "type", "ean", "title", "author", "publisher", "distributor",
    "category", "price", "theme", "schedule", "location", "datetime"
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

        # Remove trailing empty column caused by a trailing semicolon if present
        if header and header[-1] == "":
            header.pop()

        # Detect format based on header structure
        has_type_column = False

        if header == HEADER_12_COL or (len(header) > 0 and header[0].strip().lower() == "type"):
            has_type_column = True
            expected_length = len(HEADER_12_COL)
        elif header == HEADER_9_COL:
            has_type_column = False
            expected_length = len(HEADER_9_COL)
        else:
            raise SystemExit(
                "The header does not match any expected columns.\n"
                f"Expected 9-col: {HEADER_9_COL}\n"
                f"Or Expected 12-col: {HEADER_12_COL}\n"
                f"Received: {header}"
            )

        for line_number, row in enumerate(reader, start=2):
            if not row or all(value == "" for value in row):
                continue

            # Remove trailing empty field caused by trailing semicolon
            if len(row) == expected_length + 1 and row[-1] == "":
                row.pop()

            if len(row) != expected_length:
                raise SystemExit(
                    f"Line {line_number}: expected {expected_length} fields, found {len(row)}."
                )

            # Clean and normalize text values across all columns
            row = [clean_text(value, replacements) for value in row]

            if has_type_column:
                # 12-column format (with 'type' already as 1st column)
                item_type = row[0].strip().lower() if row[0].strip() else "book"
                ean = row[1]
                title = row[2]
                author = row[3]
                publisher = row[4]
                distributor = row[5]
                category = row[6]
                raw_price = row[7].strip()
                price = parse_float(raw_price) if raw_price else 0.0
                theme = row[8]
                schedule = row[9]
                location = row[10]
                datetime_val = row[11]
            else:
                # 9-column format (raw bookseller format, defaulting type to 'book')
                item_type = "book"
                ean = row[0]
                title = row[1]
                author = row[2]
                publisher = row[3]
                distributor = row[4]
                category = row[5]
                raw_price = row[6].strip()
                price = parse_float(raw_price) if raw_price else 0.0
                theme = row[7]
                schedule = row[8]
                location = ""
                datetime_val = ""

            # Default quantity to "No Disponible" since it is absent in raw source
            quantity = "No Disponible"

            # Construct the ordered item dictionary matching the final payload
            item = {
                "type": item_type,
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
                "location": location,
                "datetime": datetime_val,
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
