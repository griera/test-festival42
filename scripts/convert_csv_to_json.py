#!/usr/bin/env python3
import csv
import json
import argparse
import os

def parse_float(val):
    """ Convert numeric strings with a comma (e.g., '28,80') to float (28.80). """
    if not val:
        return 0.0
    try:
        return float(val.replace(',', '.'))
    except ValueError:
        return 0.0

def parse_int(val):
    """ Safely convert strings to integers. """
    if not val:
        return 0
    try:
        return int(val)
    except ValueError:
        return 0

def convert_csv_to_json(csv_filename, json_filename, minify=True):
    """ Reads a semicolon-delimited CSV file and converts it into a structured JSON file. """
    records = []

    # Open the CSV file specifying the semicolon delimiter ';'
    with open(csv_filename, mode='r', encoding='utf-8', errors='ignore') as csv_file:
        reader = csv.DictReader(csv_file, delimiter=';')

        for row in reader:
            item = {}
            for key, val in row.items():
                if not key:
                    continue

                # Normalize keys to lowercase and strip whitespace
                clean_key = key.strip().lower()
                clean_val = val.strip() if val else ""

                # Convert numeric fields accordingly
                if clean_key in ['quantity', 'tax']:
                    item[clean_key] = parse_int(clean_val)
                elif clean_key in ['price', 'discount', 'total']:
                    item[clean_key] = parse_float(clean_val)
                else:
                    item[clean_key] = clean_val

            # Add local cover image path based on the EAN field
            ean_value = item.get("ean", "")
            cover_path = f"assets/covers/{ean_value}.png"

            if ean_value and os.path.exists(cover_path):
                item["cover"] = cover_path
            else:
                item["cover"] = ""

            records.append(item)

    # Determine indentation: None removes whitespace for minification, 2 keeps it readable
    indent_value = None if minify else 2

    # Save the result into a structured JSON file
    with open(json_filename, mode='w', encoding='utf-8') as json_file:
        json.dump(records, json_file, ensure_ascii=False, indent=indent_value)

    format_status = "minified (optimized)" if minify else "formatted (readable)"
    print(f"Process completed! Successfully converted {len(records)} records from {csv_filename} to {json_filename} [{format_status}]")

if __name__ == '__main__':
    # Set up argument parser with detailed usage and execution examples
    parser = argparse.ArgumentParser(
        description="Convert a semicolon-delimited festival CSV file into a structured JSON payload for the web app.",
        epilog="Examples of execution:\n"
               "  1. Convert default catalog CSV (minified by default):\n"
               "     python3 scripts/convert_csv_to_json.py\n\n"
               "  2. Convert generating a readable/indented JSON (no minification):\n"
               "     python3 scripts/convert_csv_to_json.py --no-minify\n\n"
               "  3. Convert a custom CSV input and output file:\n"
               "     python3 scripts/convert_csv_to_json.py -i data/catalog_large.csv -o data.json\n\n"
               "  4. Display help menu:\n"
               "     python3 scripts/convert_csv_to_json.py --help",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        "-i", "--input",
        type=str,
        default="data/data.csv",
        help="Path to the input CSV file to convert (default: data/data.csv)"
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        default="data.json",
        help="Path to the output JSON file (default: data.json)"
    )
    
    # Minification flags (Enabled by default)
    parser.add_argument(
        "--minify",
        dest="minify",
        action="store_true",
        help="Minify the output JSON by removing whitespace (enabled by default)"
    )
    parser.add_argument(
        "--no-minify",
        dest="minify",
        action="store_false",
        help="Disable minification and use a readable indented format"
    )
    parser.set_defaults(minify=True)

    args = parser.parse_args()

    # Run conversion using arguments
    convert_csv_to_json(args.input, args.output, minify=args.minify)
