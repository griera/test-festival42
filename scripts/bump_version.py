import argparse
import re
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

# Paths resolved against the repository root (this script lives in scripts/),
# so it works no matter which directory it is launched from
ROOT = Path(__file__).resolve().parent.parent
INDEX_FILE = ROOT / "index.html"
SW_FILE = ROOT / "sw.js"
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


def update_data_version():
    """Sets a new data timestamp in index.html (data.json preload link) and sw.js. Returns True on success."""
    new_timestamp = get_current_timestamp()
    print(f"     ├─ New timestamp (CET/CEST): {new_timestamp}")

    html_matches = update_file_content(INDEX_FILE, DATA_VERSION_PATTERN, rf'\g<1>{new_timestamp}')
    print(f"     ├─ {'✔' if html_matches else '❌'} {INDEX_FILE.name} data.json preload link: {html_matches} match(es)")

    sw_matches = update_file_content(SW_FILE, DATA_VERSION_PATTERN, rf'\g<1>{new_timestamp}')
    print(f"     └─ {'✔' if sw_matches else '❌'} {SW_FILE.name} data.json precache entry: {sw_matches} match(es)")

    return html_matches > 0 and sw_matches > 0


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


def main():
    parser = argparse.ArgumentParser(description="Automates versioning and timestamps for the fair web app.")
    parser.add_argument(
        "action",
        choices=["data", "code", "check"],
        help="'data': new data timestamp (app.js is not touched); "
             "'code': bump the app.js/styles.css version; "
             "'check': only verify that index.html and sw.js are aligned."
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
        print("  └─ Data change. Updating the data.json version in index.html and sw.js...")
        ok = update_data_version()
    elif args.action == "code":
        print(f"  └─ Code change. Bumping version ({args.type})...")
        ok = update_code_version(args.type)

    ok = check_consistency() and ok

    if ok:
        print("✨ Versioning process completed successfully!")
    else:
        print("💥 Versioning process finished with errors (see ❌ above).")
        sys.exit(1)


if __name__ == "__main__":
    main()
