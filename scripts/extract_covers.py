#!/usr/bin/env python3
import argparse
import io
import os
import re
from PIL import Image
import pymupdf  # Modern PyMuPDF API

# Minimum dimension thresholds adjusted to support smaller catalog grid thumbnails
MIN_COVER_WIDTH = 40
MIN_COVER_HEIGHT = 60
# WebP encoding. Covers are small thumbnails (96x144 CSS px on screen): quality 75 halves the file size of
# quality 85 with no visible difference at that size, and method 6 (slowest, most efficient encoder effort)
# saves about 10% more at the same quality. Use --quality to try other values.
WEBP_QUALITY = 75
WEBP_METHOD = 6

# Covers are shown 144 CSS px tall; 3x that height is enough for the densest phone screens.
# Taller embedded images are downscaled (never upscaled), so an oversized catalog image is never published.
MAX_COVER_HEIGHT = 432


def extract_covers_from_pdf(
    pdf_path, output_dir="assets/covers/", force_include_xrefs=None, debug=False, quality=WEBP_QUALITY
):
    """Extracts unique book cover images from a PDF catalog, converts them to WebP,

    finds the corresponding 13-digit EAN to the right of each cover, and saves
    the image named after its EAN.
    """
    if force_include_xrefs is None:
        force_include_xrefs = set()

    os.makedirs(output_dir, exist_ok=True)

    # Open the PDF document using the modern pymupdf API
    doc = pymupdf.open(pdf_path)
    image_counter = 0
    total_bytes = 0  # Size of all saved covers, to compare quality settings
    resized_counter = 0
    processed_instances = (
        set()
    )  # Track unique cover bounding boxes per page to avoid duplicate processing

    print(f"Processing PDF '{pdf_path}'...")
    print(
        "Extracting covers, converting to WebP, and searching for EANs on the right..."
    )

    for page_num in range(len(doc)):
        page = doc[page_num]
        page_cover_counter = 0  # Counter for covers extracted on the current page

        # Get detailed image information including bounding box (bbox) and xref
        image_infos = page.get_image_info(xrefs=True)

        if debug:
            print(
                f"\n--- Page {page_num + 1} --- (Raw images found: {len(image_infos)})"
            )

        for img_info in image_infos:
            xref = img_info.get("xref")
            if not xref or xref <= 0:
                continue

            bbox = img_info.get("bbox")  # (x0, y0, x1, y1) on page
            if not bbox:
                continue

            width = img_info.get("width")
            height = img_info.get("height")

            # Calculate actual rendered dimensions on the page
            bbox_width = bbox[2] - bbox[0]
            bbox_height = bbox[3] - bbox[1]

            # Unique instance key per page based on bbox to avoid duplicate processing
            instance_key = (page_num, tuple(round(coord, 2) for coord in bbox))
            if instance_key in processed_instances:
                continue

            if debug:
                print(
                    f"  [Img xref {xref}] raw_w={width}, raw_h={height} | bbox_w={bbox_width:.1f}, bbox_h={bbox_height:.1f} | bbox={bbox}"
                )

            # Check if it's explicitly forced by the command-line whitelist
            is_forced = xref in force_include_xrefs

            # Filter conditions:
            # A cover is valid if its rendered bounding box is vertical (bbox_width < bbox_height)
            # OR if raw dimensions are vertical, meeting the flexible minimum size thresholds.
            is_vertical_bbox = bbox_width < bbox_height
            is_vertical_raw = width and height and width < height

            passes_size_check = (
                bbox_width >= MIN_COVER_WIDTH
                and bbox_height >= MIN_COVER_HEIGHT
            )

            if is_forced or (is_vertical_bbox and passes_size_check):
                if is_forced and debug:
                    print(
                        f"    -> [Override] Forcing processing for xref {xref} via command-line argument!"
                    )

                processed_instances.add(instance_key)

                # Extract the base image using doc.extract_image
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]

                # Define a clipping rectangle to the right side of the cover image
                right_rect = pymupdf.Rect(
                    bbox[2] - 5, bbox[1] - 10, bbox[2] + 250, bbox[3] + 10
                )
                right_text = page.get_text("text", clip=right_rect)

                # Clean whitespace and newlines to handle text wrapped across lines safely
                cleaned_text = re.sub(r"\s+", "", right_text)

                # Search for a valid 13-digit EAN starting with 978 or 979
                ean_match = re.search(r"97[89]\d{10}", cleaned_text)

                if not ean_match:
                    ean_match = re.search(r"\b\d{13}\b", right_text)

                if ean_match:
                    current_ean = re.sub(r"\D", "", ean_match.group(0))

                    if len(current_ean) == 13:
                        image_filename = f"{current_ean}.webp"
                        image_path = os.path.join(output_dir, image_filename)

                        # Convert image bytes to WebP using Pillow without any rotation
                        try:
                            image = Image.open(io.BytesIO(image_bytes))

                            # Convert RGBA or Palette to RGB if necessary
                            if image.mode in ("RGBA", "P"):
                                image = image.convert("RGB")

                            # Downscale oversized images, keeping the aspect ratio
                            if image.height > MAX_COVER_HEIGHT:
                                new_width = round(image.width * MAX_COVER_HEIGHT / image.height)
                                image = image.resize((new_width, MAX_COVER_HEIGHT), Image.Resampling.LANCZOS)
                                resized_counter += 1

                            image.save(image_path, "WEBP", quality=quality, method=WEBP_METHOD)
                            total_bytes += os.path.getsize(image_path)
                            image_counter += 1
                            page_cover_counter += (
                                1  # Increment per-page counter upon success
                            )
                            print(
                                f"[Success] Saved cover for EAN {current_ean} (Page {page_num + 1})"
                            )
                        except Exception as e:
                            print(
                                f"[Error] Converting image for EAN {current_ean}: {e}"
                            )
                    else:
                        print(
                            f"[Warning] Found 13-digit match but invalid length on page {page_num + 1}"
                        )
                else:
                    print(
                        f"[Warning] Cover found on page {page_num + 1} (xref {xref}), but no EAN detected on the right."
                    )
                    if debug:
                        print(f"    Extracted right text: {repr(right_text)}")
            else:
                if debug and width and height:
                    print(
                        f"    -> Ignored due to size/proportion (bbox_w={bbox_width:.1f}, bbox_h={bbox_height:.1f})"
                    )

        # Summary for the current page
        print(
            f"[Page Summary] Page {page_num + 1}: Extracted {page_cover_counter} cover(s)."
        )

    print(
        f"\nExtraction completed! Saved {image_counter} optimized WebP covers to '{output_dir}'."
    )
    if image_counter:
        print(
            f"Total size: {format_size(total_bytes)} "
            f"(average {total_bytes / image_counter / 1024:.1f} KB per cover, WebP quality {quality}, method {WEBP_METHOD})."
        )
    if resized_counter:
        print(f"Downscaled {resized_counter} cover(s) taller than {MAX_COVER_HEIGHT}px.")


def format_size(num_bytes):
    """Human-readable size: KB below 1 MB, MB above."""
    if num_bytes < 1024 * 1024:
        return f"{num_bytes / 1024:.1f} KB"
    return f"{num_bytes / 1024 / 1024:.1f} MB"


def webp_quality(value):
    """argparse type: an integer WebP quality between 1 and 100."""
    quality = int(value)
    if not 1 <= quality <= 100:
        raise argparse.ArgumentTypeError("quality must be between 1 and 100")
    return quality


def main():
    parser = argparse.ArgumentParser(
        description="Extract unique vertical book covers, convert to WebP, and name them using the EAN found on their right."
    )
    parser.add_argument("pdf_file", help="Source PDF catalog file")
    parser.add_argument(
        "--output",
        default="assets/covers/",
        help="Directory to save extracted cover images (default: assets/covers/)",
    )
    parser.add_argument(
        "--force-xrefs",
        default="",
        help="Comma-separated list of image xref IDs to forcefully include, bypassing size/proportion filters (e.g., '393,412')",
    )
    parser.add_argument(
        "--quality",
        type=webp_quality,
        default=WEBP_QUALITY,
        help=f"WebP quality from 1 to 100 (default: {WEBP_QUALITY}). Lower values give smaller files.",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Show detailed debug information to audit each image and text",
    )
    args = parser.parse_args()

    # Parse comma-separated string into a set of integers (defaults to empty set if none provided)
    force_include_xrefs = {
        int(x.strip()) for x in args.force_xrefs.split(",") if x.strip().isdigit()
    }

    extract_covers_from_pdf(
        args.pdf_file, args.output, force_include_xrefs, args.debug, args.quality
    )


if __name__ == "__main__":
    main()
