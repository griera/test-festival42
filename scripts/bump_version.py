import argparse
import hashlib
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import parse_qs
from zoneinfo import ZoneInfo

from cover_version import cover_version

# Paths resolved against the repository root (this script lives in scripts/),
# so it works no matter which directory it is launched from
ROOT = Path(__file__).resolve().parent.parent
INDEX_FILE = ROOT / "index.html"
SW_FILE = ROOT / "sw.js"
DATA_FILE = ROOT / "data.json"

# Fingerprint of the data.json content, stored next to its version in the data preload link of index.html.
# The ?v= timestamp only changes when 'data' is run: if data.json is regenerated without it, its URL stays the
# same and every device keeps its cached copy (Service Worker, browsers, Cloudflare). The fingerprint lets
# every run (and the deployment workflow, through 'check') detect that situation.
DATA_HASH_ATTRIBUTE = "data-content-hash"
DATA_PRELOAD_TAG = re.compile(r'<link\b[^>]*\bid="dataPreload"[^>]*>')
TIMEZONE = "Europe/Madrid"

# Versioned URLs kept in sync between index.html and the Service Worker precache list (sw.js).
# The data version lives only in these two files: app.js reads it from the data.json preload link
# in index.html, so a data update never changes app.js and its long-lived cache stays valid.
CODE_VERSION_PATTERN = r'((?:app\.js|styles\.css)\s*\?v=)\d+\.\d+\.\d+'
DATA_VERSION_PATTERN = r'(data\.json\?v=)\d{14}'


def get_current_timestamp():
    """Generates the current timestamp in YYYYMMDDHHMMSS format using CET/CEST timezone."""
    return datetime.now(ZoneInfo(TIMEZONE)).strftime("%Y%m%d%H%M%S")


def parse_version(version_str):
    """Converts a version string like '1.2.3' into a list of integers [1, 2, 3]."""
    try:
        return list(map(int, version_str.split('.')))
    except ValueError:
        return [1, 0, 0]


def bump_version(version_list, bump_type):
    """Increments the semantic version based on the specified bump type (patch, minor, major)."""
    major, minor, patch = version_list
    if bump_type == "major":
        major += 1
        minor = 0
        patch = 0
    elif bump_type == "minor":
        minor += 1
        patch = 0
    else:  # default to patch
        patch += 1
    return f"{major}.{minor}.{patch}"


def update_file_content(filepath, pattern, replacement):
    """Replaces text in a file using regular expressions. Returns the match count (0 if the file is missing)."""
    if not filepath.exists():
        print(f"     └─ ❌ File {filepath.name} not found.")
        return 0

    content = filepath.read_text(encoding='utf-8')
    new_content, count = re.subn(pattern, replacement, content)
    if count > 0:
        filepath.write_text(new_content, encoding='utf-8')
    return count


def update_code_version(bump_type):
    """Bumps the semantic version of app.js and styles.css in index.html and sw.js. Returns True on success."""
    if not INDEX_FILE.exists():
        print(f"     └─ ❌ File {INDEX_FILE.name} not found.")
        return False

    match = re.search(r'(?:app\.js|styles\.css)\s*\?v=(\d+\.\d+\.\d+)', INDEX_FILE.read_text(encoding='utf-8'))
    if not match:
        print(f"     └─ ❌ Could not detect a prior semantic version in {INDEX_FILE.name} (e.g., app.js?v=1.0.0)")
        return False

    current_ver_str = match.group(1)
    new_ver_str = bump_version(parse_version(current_ver_str), bump_type)
    print(f"     ├─ SemVer version: {current_ver_str} ➔ {new_ver_str} (Type: {bump_type})")

    html_matches = update_file_content(INDEX_FILE, CODE_VERSION_PATTERN, rf'\g<1>{new_ver_str}')
    print(f"     ├─ {'✔' if html_matches else '❌'} {INDEX_FILE.name}: {html_matches} match(es)")

    sw_matches = update_file_content(SW_FILE, CODE_VERSION_PATTERN, rf'\g<1>{new_ver_str}')
    print(f"     └─ {'✔' if sw_matches else '❌'} {SW_FILE.name}: {sw_matches} match(es)")

    return html_matches > 0 and sw_matches > 0


def data_fingerprint():
    """First 8 characters of the SHA-256 of data.json (None if the file is missing)."""
    if not DATA_FILE.exists():
        return None
    return hashlib.sha256(DATA_FILE.read_bytes()).hexdigest()[:8]


def set_data_fingerprint(fingerprint):
    """Writes the data.json fingerprint into the data preload link of index.html. Returns True on success."""
    if not INDEX_FILE.exists():
        return False
    html = INDEX_FILE.read_text(encoding='utf-8')
    match = DATA_PRELOAD_TAG.search(html)
    if not match:
        return False
    tag = match.group(0)
    if f'{DATA_HASH_ATTRIBUTE}="' in tag:
        new_tag = re.sub(rf'{DATA_HASH_ATTRIBUTE}="[^"]*"', f'{DATA_HASH_ATTRIBUTE}="{fingerprint}"', tag)
    else:
        new_tag = tag.replace('id="dataPreload"', f'id="dataPreload" {DATA_HASH_ATTRIBUTE}="{fingerprint}"', 1)
    INDEX_FILE.write_text(html[:match.start()] + new_tag + html[match.end():], encoding='utf-8')
    return True


def update_data_version():
    """Sets a new data timestamp in index.html (data.json preload link) and sw.js, and records the data.json
    fingerprint. Returns True on success."""
    new_timestamp = get_current_timestamp()
    print(f"     ├─ New timestamp (CET/CEST): {new_timestamp}")

    fingerprint = data_fingerprint()
    recorded = fingerprint is not None and set_data_fingerprint(fingerprint)
    print(f"     ├─ {'✔' if recorded else '❌'} data.json fingerprint {fingerprint or '(data.json not found)'} recorded in {INDEX_FILE.name}")

    html_matches = update_file_content(INDEX_FILE, DATA_VERSION_PATTERN, rf'\g<1>{new_timestamp}')
    print(f"     ├─ {'✔' if html_matches else '❌'} {INDEX_FILE.name} data.json preload link: {html_matches} match(es)")

    sw_matches = update_file_content(SW_FILE, DATA_VERSION_PATTERN, rf'\g<1>{new_timestamp}')
    print(f"     └─ {'✔' if sw_matches else '❌'} {SW_FILE.name} data.json precache entry: {sw_matches} match(es)")

    return recorded and html_matches > 0 and sw_matches > 0


def recorded_data_fingerprint():
    """Fingerprint stored in the data preload link of index.html by the last 'data' run (None if absent)."""
    if not INDEX_FILE.exists():
        return None
    match = DATA_PRELOAD_TAG.search(INDEX_FILE.read_text(encoding='utf-8'))
    recorded = re.search(rf'{DATA_HASH_ATTRIBUTE}="([^"]*)"', match.group(0)) if match else None
    return recorded.group(1) if recorded else None


def data_versions_aligned():
    """True if index.html and sw.js reference the same single data.json version."""
    if not INDEX_FILE.exists() or not SW_FILE.exists():
        return False
    versions = [set(re.findall(r'data\.json\?v=(\d+)', path.read_text(encoding='utf-8'))) for path in (INDEX_FILE, SW_FILE)]
    return len(versions[0]) == 1 and versions[0] == versions[1]


def check_data_fingerprint():
    """Verifies that data.json has not changed since its version was last bumped."""
    print("  └─ Checking that data.json matches its version...")
    fingerprint = data_fingerprint()
    if fingerprint is None:
        print(f"     └─ ❌ File {DATA_FILE.name} not found.")
        return False
    recorded = recorded_data_fingerprint()
    if not recorded:
        print(f"     └─ ❌ No data.json fingerprint in {INDEX_FILE.name}: run 'bump_version.py data' once to record it.")
        return False
    if recorded != fingerprint:
        print(f"     ├─ ❌ data.json changed since its last version bump (recorded {recorded}, current {fingerprint}).")
        print("     └─ ❌ Run 'bump_version.py data', otherwise devices would keep their cached copy.")
        return False
    print(f"     └─ ✔ data.json matches its version (fingerprint {fingerprint})")
    return True


def check_consistency():
    """Verifies that index.html and sw.js reference exactly the same versioned URLs. Returns True if aligned."""
    print("  └─ Checking that index.html and sw.js are aligned...")
    if not INDEX_FILE.exists() or not SW_FILE.exists():
        print("     └─ ❌ index.html or sw.js not found.")
        return False

    html = INDEX_FILE.read_text(encoding='utf-8')
    sw = SW_FILE.read_text(encoding='utf-8')
    aligned = True
    for name, pattern in [("app.js", r'app\.js\?v=([\w.-]+)'),
                          ("styles.css", r'styles\.css\?v=([\w.-]+)'),
                          ("data.json", r'data\.json\?v=(\d+)')]:
        html_versions = set(re.findall(pattern, html))
        sw_versions = set(re.findall(pattern, sw))
        ok = len(html_versions) == 1 and html_versions == sw_versions
        aligned = aligned and ok
        print(f"     ├─ {'✔' if ok else '❌'} {name}: index.html {sorted(html_versions)} | sw.js {sorted(sw_versions)}")
    print(f"     └─ {'✔ Aligned' if aligned else '❌ Not aligned: fix the files above before deploying'}")
    return aligned


def check_cover_versions():
    """Verifies that every cover URL in data.json carries the fingerprint of the current cover file.

    A mismatch means the covers were regenerated without running process_catalog.py afterwards: the new
    images would be published under their old URLs, and devices that cached them would keep the old ones.
    """
    print("  └─ Checking that the cover URLs in data.json match the cover files...")
    if not DATA_FILE.exists():
        print(f"     └─ ❌ File {DATA_FILE.name} not found.")
        return False
    try:
        records = json.loads(DATA_FILE.read_text(encoding='utf-8'))
    except json.JSONDecodeError as error:
        print(f"     └─ ❌ {DATA_FILE.name} is not valid JSON: {error}")
        return False

    checked, outdated, missing = 0, set(), set()
    for record in records:
        cover = record.get("cover") if isinstance(record, dict) else None
        if not cover:
            continue
        path, _, query = cover.partition("?")
        cover_file = ROOT / path
        if not cover_file.exists():
            missing.add(path)
            continue
        checked += 1
        if parse_qs(query).get("v", [""])[0] != cover_version(cover_file):
            outdated.add(path)

    for label, paths in (("missing cover file(s)", missing), ("outdated cover version(s)", outdated)):
        if paths:
            sample = ", ".join(sorted(paths)[:5]) + (" …" if len(paths) > 5 else "")
            print(f"     ├─ ❌ {len(paths)} {label}: {sample}")
    if missing or outdated:
        print("     └─ ❌ Run process_catalog.py after extract_covers.py, then 'bump_version.py data'.")
        return False
    print(f"     └─ ✔ {checked} cover URL(s) up to date")
    return True


def main():
    parser = argparse.ArgumentParser(description="Automates versioning and timestamps for the fair web app.")
    parser.add_argument(
        "action",
        choices=["data", "code", "check"],
        help="'data': new data timestamp when data.json has changed (app.js is not touched); "
             "'code': bump the app.js/styles.css version; "
             "'check': only verify that index.html and sw.js are aligned, that the cover URLs in "
             "data.json match the cover files, and that data.json has not changed since its last 'data' run."
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Only with 'data': create a new data version even if data.json has not changed "
             "(by default 'data' does nothing in that case, so devices do not download the same data again)",
    )
    parser.add_argument(
        "--type",
        choices=["patch", "minor", "major"],
        default="patch",
        help="Semantic version bump type (only used when action is 'code', default: patch)"
    )
    args = parser.parse_args()

    print("🚀 Running version manager...")
    ok = True

    if args.action == "data":
        fingerprint = data_fingerprint()
        unchanged = fingerprint is not None and fingerprint == recorded_data_fingerprint() and data_versions_aligned()
        if unchanged and not args.force:
            # A new timestamp would show a false "last data update" date and make every device download the
            # same data again, so nothing is bumped
            print(f"  └─ data.json has not changed since its last version (fingerprint {fingerprint}): nothing to bump.")
            print("     └─ ℹ️ Use --force to create a new data version anyway.")
        else:
            print("  └─ Data change. Updating the data.json version in index.html and sw.js...")
            ok = update_data_version()
    elif args.action == "code":
        print(f"  └─ Code change. Bumping version ({args.type})...")
        ok = update_code_version(args.type)

    ok = check_consistency() and ok
    ok = check_cover_versions() and ok
    ok = check_data_fingerprint() and ok

    if ok:
        print("✨ Versioning process completed successfully!")
    else:
        print("💥 Versioning process finished with errors (see ❌ above).")
        sys.exit(1)


if __name__ == "__main__":
    main()
