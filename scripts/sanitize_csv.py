#!/usr/bin/env python3
import argparse
import csv
import json
import unicodedata

SOURCE_COLUMNS = [
    "TITULO", "EAN", "AUTOR", "EDITORIAL", "COLECCION", "MATERIA",
    "CANTIDAD", "PRECIO", "DESCUENTO", "IVA", "TOTALLINEA",
]

OUTPUT_HEADER = [
    "type", "title", "ean", "author", "publisher", "collection", "category",
    "quantity", "price", "discount", "tax", "total", "location", "datetime",
]


def clean_text(text, replacements):
    # Normalize Unicode and replace non-breaking spaces with regular spaces.
    text = unicodedata.normalize("NFC", text).replace("\u00a0", " ")
    for original, corrected in replacements.items():
        text = text.replace(original, corrected)
    return text


def main():
    parser = argparse.ArgumentParser(
        description="Transform a semicolon-delimited CSV file.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Examples:
  python3 sanitize_csv.py input.csv output.csv
  python3 sanitize_csv.py input.csv output.csv --encoding utf-8-sig
  python3 sanitize_csv.py input.csv output.csv --replacements replacements.json
  python3 sanitize_csv.py --help
""",
    )
    parser.add_argument("input_file", help="Source CSV file")
    parser.add_argument("output_file", help="Generated CSV file")
    parser.add_argument(
        "--encoding",
        default="utf-8-sig",
        help="Input file encoding (default: utf-8-sig)",
    )
    parser.add_argument(
        "--replacements",
        help="JSON file containing text replacements, e.g. replacements.json",
    )
    args = parser.parse_args()

    replacements = {}
    if args.replacements:
        with open(args.replacements, encoding="utf-8") as replacements_file:
            replacements = json.load(replacements_file)

    # Read the source CSV using its configured encoding (e.g. cp1252).
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

        
        with open(
            args.output_file, "w", encoding="utf-8", newline=""
        ) as output_file:
            writer = csv.writer(output_file, delimiter=";", lineterminator="\n")
            writer.writerow(OUTPUT_HEADER)

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

                row = [clean_text(value, replacements) for value in row]
                writer.writerow(["book", *row, "", ""])


if __name__ == "__main__":
    main()

