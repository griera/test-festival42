#!/usr/bin/env python3
import argparse
import os
import re
import pymupdf  # Modern PyMuPDF API

# Minimum dimension thresholds to ignore tiny vertical icons or badges
MIN_COVER_WIDTH = 100
MIN_COVER_HEIGHT = 150


def extract_covers_from_pdf(pdf_path, output_dir="assets/covers/"):
    """Extracts unique vertical book cover images from a PDF document,

    filters out tiny graphics and duplicates, extracts the corresponding EAN
    from the text located to the right of each cover, and saves the image
    named after its EAN.
    """
    os.makedirs(output_dir, exist_ok=True)

    # Open the PDF document using the modern pymupdf API
    doc = pymupdf.open(pdf_path)
    image_counter = 0
    seen_xrefs = set()  # Track unique image references to prevent duplicates across pages

    print(f"Processing PDF '{pdf_path}'...")
    print(
        "Extracting covers and searching for EANs on the right side of each image..."
    )

    for page_num in range(len(doc)):
        page = doc[page_num]
        
        # Get detailed image information including page bounding box (bbox) and xref
        image_infos = page.get_image_info(xrefs=True)

        for img_info in image_infos:
            xref = img_info.get("xref")
            if not xref or xref <= 0:
                continue

            # Skip if this exact image reference was already processed in the document
            if xref in seen_xrefs:
                continue

            bbox = img_info.get("bbox")  # (x0, y0, x1, y1) on page
            if not bbox:
                continue

            width = img_info.get("width")
            height = img_info.get("height")

            # Filter: Vertical (width < height), meets minimum size thresholds for a book cover
            if (
                width
                and height
                and width < height
                and width >= MIN_COVER_WIDTH
                and height >= MIN_COVER_HEIGHT
            ):

                seen_xrefs.add(xref)

                # Extract the base image using doc.extract_image
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                image_ext = base_image["ext"]  # e.g., png, jpeg

                # Define a clipping rectangle to the right side of the cover image to find the EAN
                # bbox[2] is x1 (right edge of image), bbox[1] is y0, bbox[3] is y1
                right_rect = pymupdf.Rect(
                    bbox[2], bbox[1] - 5, bbox[2] + 200, bbox[3] + 5
                )
                right_text = page.get_text("text", clip=right_rect)

                # Search for a valid 13-digit EAN (usually starting with 978 or 979) in the extracted text block
                ean_match = re.search(r"\b\d{13}\b", right_text)

                if ean_match:
                    current_ean = ean_match.group(0)
                    image_filename = f"{current_ean}.{image_ext}"
                    image_path = os.path.join(output_dir, image_filename)

                    with open(image_path, "wb") as img_file:
                        img_file.write(image_bytes)

                    image_counter += 1
                    print(
                        f"Found cover for EAN {current_ean} on page {page_num + 1}"
                    )
                else:
                    print(
                        f"Warning: Cover found on page {page_num + 1}, but no valid EAN was detected on its right side."
                    )

    print(
        f"Extraction completed! Saved {image_counter} unique cover images to '{output_dir}'."
    )


def main():
    parser = argparse.ArgumentParser(
        description="Extract unique vertical book cover images from a PDF and name them using the EAN found on their right."
    )
    parser.add_argument("pdf_file", help="Source PDF catalog file")
    parser.add_argument(
        "--output",
        default="assets/covers/",
        help="Directory to save extracted cover images (default: assets/covers/)",
    )
    args = parser.parse_args()

    extract_covers_from_pdf(args.pdf_file, args.output)


if __name__ == "__main__":
    main()
