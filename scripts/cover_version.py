"""Content-based version of a cover image, used in its URL: assets/covers/<EAN>.webp?v=<version>.

Covers are cached for a long time by Cloudflare, browsers and the Service Worker, so a changed image must get
a new URL to reach devices that already have it. Deriving the version from the file content does it
automatically: a regenerated cover with different bytes gets a new URL, and an unchanged one keeps its URL,
so it is never downloaded again.

Shared by process_catalog.py (writes the versions into data.json) and bump_version.py (checks them before
every deployment), so both always compute exactly the same value.
"""
import hashlib

# 8 hex characters of SHA-256: only needs to tell apart successive versions of the same cover
VERSION_LENGTH = 8


def cover_version(path):
    """Returns the content version of the cover file at path (first characters of its SHA-256)."""
    with open(path, "rb") as cover_file:
        return hashlib.sha256(cover_file.read()).hexdigest()[:VERSION_LENGTH]
