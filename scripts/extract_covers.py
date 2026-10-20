#!/usr/bin/env python3
import argparse
import csv
import os
import pymupdf  # Modern PyMuPDF API

# Minimum dimension thresholds to ignore tiny vertical icons or badges
MIN_COVER_WIDTH = 100
MIN_COVER_HEIGHT = 150


def extract_covers_from_pdf(pdf_path, csv_path, output_dir="assets/covers/"):
    """Extracts unique vertical book cover images from a PDF document,

    filtering out tiny graphics and duplicates, and maps them to their
    corresponding EANs based on sequential CSV row order.
    """
    os.makedirs(output_dir, exist_ok=True)

    # Read EANs from the CSV in exact sequential order
    eans = []
    with open(csv_path, mode="r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f, delimiter=";")
        for row in reader:
            if row.get("ean"):
                eans.append(row["ean"])

    # Open the PDF document using the modern pymupdf API
    doc = pymupdf.open(pdf_path)
    image_counter = 0
    seen_xrefs = set()  # Track unique image references to prevent duplicates across pages

    print(f"Processing PDF... Found {len(eans)} books in the CSV catalog.")
    print("Filtering by vertical orientation, minimum size, and unique instances...")

    for page_num in range(len(doc)):
        page = doc[page_num]
        image_list = page.get_images(full=True)

        for img in image_list:
            xref = img[0]

            # Skip if this exact image reference was already processed in the document
            if xref in seen_xrefs:
                continue

            base_image = doc.extract_image(xref)
            width = base_image.get("width")
            height = base_image.get("height")

            # Filter: Vertical (width < height), meets minimum size thresholds for a book cover
            if (
                width
                and height
                and width < height
                and width >= MIN_COVER_WIDTH
                and height >= MIN_COVER_HEIGHT
            ):

                seen_xrefs.add(xref)
                image_bytes = base_image["image"]
                image_ext = base_image["ext"]  # e.g., png, jpeg

                # Map the filtered cover image to the corresponding EAN by index order
                if image_counter < len(eans):
                    current_ean = eans[image_counter]
                    image_filename = f"{current_ean}.{image_ext}"
                    image_path = os.path.join(output_dir, image_filename)

                    with open(image_path, "wb") as img_file:
                        img_file.write(image_bytes)

                    image_counter += 1

    print(
        f"Extraction completed! Saved {image_counter} unique cover images to '{output_dir}'."
    )


def main():
    parser = argparse.ArgumentParser(
        description="Extract unique vertical book cover images from a PDF matching CSV catalog order."
    )
    parser.add_argument("pdf_file", help="Source PDF catalog file")
    parser.add_argument("csv_file", help="Processed CSV catalog file")
    parser.add_argument(
        "--output",
        default="assets/covers/",
        help="Directory to save extracted cover images (default: assets/covers/)",
    )
    args = parser.parse_args()

    extract_covers_from_pdf(args.pdf_file, args.csv_file, args.output)


if __name__ == "__main__":
    main()
