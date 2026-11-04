#!/usr/bin/env python3
import argparse
import csv
import json
import os
import re
import unicodedata
from datetime import datetime, date

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

# Fair date boundaries for disambiguating mixed date formats (dd/mm vs mm/dd)
FAIR_START = date(2026, 11, 4)
FAIR_END = date(2026, 11, 8)


def clean_text(text, replacements):
    """Normalize Unicode and replace non-breaking spaces with regular spaces."""
    text = unicodedata.normalize("NFC", text).replace("\u00a0", " ")
    for original, corrected in replacements.items():
        text = text.replace(original, corrected)
    return text.strip()

def remove_accents(input_str):
    """Normalize string by removing diacritics (accents) for correct alphabetical sorting."""
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)])

def parse_float(val):
    """Convert numeric strings with a comma and optional currency symbols (e.g., '28,80', '23,12 €') to float."""
    if not val:
        return 0.0
    try:
        # Remove currency symbols (like €), letters, and whitespace, keeping digits, commas, dots, and minus signs
        cleaned_val = re.sub(r'[^\d,\.-]', '', str(val))
        return float(cleaned_val.replace(',', '.'))
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

def format_schedule_dates(schedule_str):
    """
    Normalize mixed dd/mm/yyyy and mm/dd/yyyy formats using fair bounds context,
    standardize output to dd/mm/yyyy, and ensure times are strictly HH:MM.
    """
    if not schedule_str:
        return schedule_str

    # Match date patterns separated by slash or dash
    pattern_date = r'\b(\d{1,2})[/-](\d{1,2})[/-](\d{4})\b'

    def date_replacer(match):
        p1, p2, year_str = match.groups()
        n1, n2, yr = int(p1), int(p2), int(year_str)

        # Try interpretation as DD/MM/YYYY (p1 = day, p2 = month)
        try:
            dt_dmy = date(yr, n2, n1)
            if FAIR_START <= dt_dmy <= FAIR_END:
                return dt_dmy.strftime('%d/%m/%Y')
        except ValueError:
            pass

        # Try interpretation as MM/DD/YYYY (p1 = month, p2 = day)
        try:
            dt_mdy = date(yr, n1, n2)
            if FAIR_START <= dt_mdy <= FAIR_END:
                return dt_mdy.strftime('%d/%m/%Y')
        except ValueError:
            pass

        # Fallback: default to standard DD/MM/YYYY if valid, else keep original
        try:
            dt_default = date(yr, n2, n1)
            return dt_default.strftime('%d/%m/%Y')
        except ValueError:
            return match.group(0)

    schedule_str = re.sub(pattern_date, date_replacer, schedule_str)

    # Force time format to HH:MM by removing seconds (e.g., 18:00:00 -> 18:00)
    pattern_time = r'\b([0-1]?[0-9]|2[0-3]):([0-5][0-9]):([0-5][0-9])\b'
    schedule_str = re.sub(pattern_time, r'\1:\2', schedule_str)

    return schedule_str

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
  python3 process_catalog.py data/data.csv data.json --extra-data data/extra_data.json
  python3 process_catalog.py --help
""",
    )
    parser.add_argument("input_file", help="Source raw CSV file (default: data/data.csv)", nargs="?", default="data/data.csv")
    parser.add_argument("output_file", help="Generated JSON file (default: data.json)", nargs="?", default="data.json")
    parser.add_argument(
        "--encoding",
        default="utf-8-sig",
        help="Input CSV file encoding (default: utf-8-sig)",
    )
    parser.add_argument(
        "--replacements",
        help="JSON file containing text replacements, e.g. replacements.json",
    )
    parser.add_argument(
        "--extra-data",
        help="JSON file containing extra records (e.g., books/activities) to append at the end",
    )
    
    # Minification flags (enabled by default)
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
            raise SystemExit("[ERROR]: The input file is empty.")

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
                "[ERROR]: The header does not match any expected columns.\n"
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
                    f"[ERROR]:Line {line_number}: expected {expected_length} fields, found {len(row)}."
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
                schedule = format_schedule_dates(row[9])
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
                schedule = format_schedule_dates(row[8])
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

    # Sort records alphabetically by author name (case-insensitive)
    records.sort(key=lambda x: remove_accents(x.get('author', '')).lower())

    # Append extra data JSON if provided (equivalent to jq . + $new[0])
    if args.extra_data:
        try:
            with open(args.extra_data, "r", encoding="utf-8") as extra_file:
                extra_data = json.load(extra_file)
                if isinstance(extra_data, list):
                    for extra_item in extra_data:
                        # Format schedule and datetime fields if present in extra records
                        if "schedule" in extra_item and extra_item["schedule"]:
                            extra_item["schedule"] = format_schedule_dates(extra_item["schedule"])
                        if "datetime" in extra_item and extra_item["datetime"]:
                            extra_item["datetime"] = format_schedule_dates(extra_item["datetime"])

                    records.extend(extra_data)
                    print(f"[INFO]: Successfully appended {len(extra_data)} extra record(s) from '{args.extra_data}'.")
                else:
                    print(f"[WARNING]: Extra data file '{args.extra_data}' does not contain a JSON array. Skipped.")
        except FileNotFoundError:
            raise SystemExit(f"[ERROR]: Extra data file '{args.extra_data}' not found.")
        except json.JSONDecodeError as e:
            raise SystemExit(f"[ERROR]: Failed to parse JSON from extra data file '{args.extra_events}': {e}")

    # Determine indentation and separators for strict minification or readability
    if args.minify:
        indent_value = None
        separators_value = (',', ':')
    else:
        indent_value = 2
        separators_value = None

    # Check for duplicate EANs (ignoring empty strings)
    ean_counts = {}
    for item in records:
        ean = item.get('ean', '').strip()
        if ean:
            ean_counts[ean] = ean_counts.get(ean, 0) + 1

    duplicates = [ean for ean, count in ean_counts.items() if count > 1]

    if duplicates:
        print(f"[WARNING]: Found {len(duplicates)} duplicate EAN(s) in '{args.input_file}': {duplicates}")

    # Save the result into a structured JSON file
    with open(args.output_file, mode="w", encoding="utf-8") as json_file:
        json.dump(records, json_file, ensure_ascii=False, indent=indent_value, separators=separators_value)

    format_status = "minified (optimized)" if args.minify else "formatted (readable)"
    print(f"[SUCCESS]: Process completed! Successfully converted {len(records)} total records to {args.output_file} [{format_status}]")


if __name__ == "__main__":
    main()
