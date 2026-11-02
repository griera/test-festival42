import os
import re
from datetime import datetime
from zoneinfo import ZoneInfo
import argparse

# File paths (adjust if files are located in subdirectories)
INDEX_FILE = "index.html"
APP_JS_FILE = "app.js"
TIMEZONE = "Europe/Madrid"

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
    """Replaces text in a file using regular expressions. Returns the match count."""
    if not os.path.exists(filepath):
        print(f"     └─ ⚠️ Warning: File {filepath} not found.")
        return 0
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    new_content, count = re.subn(pattern, replacement, content)
    
    if count > 0:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
            
    return count

def update_code_version(bump_type):
    """Updates the semantic version for app.js and styles.css in index.html with clean indentation."""
    if not os.path.exists(INDEX_FILE):
        print(f"     └─ ⚠️ Warning: File {INDEX_FILE} not found.")
        return False
    
    with open(INDEX_FILE, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    match = re.search(r'(app\.js|styles\.css)\s*\?v=(\d+\.\d+\.\d+)', html_content)
    if match:
        current_ver_str = match.group(2)
        current_ver_list = parse_version(current_ver_str)
        new_ver_str = bump_version(current_ver_list, bump_type)
        
        print(f"     ├─ SemVer version: {current_ver_str} ➔ {new_ver_str} (Type: {bump_type})")
        
        html_pattern = r'((?:app\.js|styles\.css)\s*\?v=)\d+\.\d+\.\d+'
        matches_count = update_file_content(INDEX_FILE, html_pattern, rf'\g<1>{new_ver_str}')
        
        if matches_count > 0:
            print(f"     └─ ✔ {INDEX_FILE} successfully updated ({matches_count} match(es))")
            return True
    else:
        print("     └─ ⚠️ Could not detect a prior semantic version in index.html (e.g., app.js?v=1.0.0)")
    return False

def main():
    parser = argparse.ArgumentParser(description="Automates versioning and timestamps for the fair web app.")
    parser.add_argument(
        "action",
        choices=["data", "code"],
        help="Specify what changed: 'data' (updates timestamp and auto-bumps code patch) or 'code' (bumps code version)."
    )
    parser.add_argument(
        "--type", 
        choices=["patch", "minor", "major"], 
        default="patch",
        help="Semantic version bump type (only used when action is 'code', default: patch)"
    )
    
    args = parser.parse_args()

    print("🚀 Running version manager...")

    if args.action == "data":
        new_timestamp = get_current_timestamp()
        print("  └─ Data change detected. Updating app.js timestamp...")
        print(f"     ├─ New timestamp (CET/CEST): {new_timestamp}")
        
        js_pattern = r"(const\s+TIMESTAMP_VERSION\s*=\s*['\"])\d{14}(['\"])"
        replacement = rf"\g<1>{new_timestamp}\g<2>"
        matches_count = update_file_content(APP_JS_FILE, js_pattern, replacement)
        
        if matches_count > 0:
            print(f"     └─ ✔ {APP_JS_FILE} successfully updated ({matches_count} match(es))")
            print("  └─ Data update implies a code change (app.js modified). Bumping code version (patch)...")
            update_code_version("patch")
        else:
            print(f"     └─ ⚠️ Pattern not found in {APP_JS_FILE}")

    elif args.action == "code":
        print(f"  └─ Code-only change detected. Bumping version ({args.type})...")
        update_code_version(args.type)

    print("✨ Versioning process completed successfully!")

if __name__ == "__main__":
    main()
