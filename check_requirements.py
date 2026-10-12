#!/usr/bin/env python3
"""Check every line of a requirements.txt against the PyPI JSON API.

Usage:
    python check_requirements.py [requirements.txt]
"""
import json
import sys
import urllib.error
import urllib.request
from datetime import datetime


def fetch_json(url):
    """Return parsed JSON, or None if PyPI answers 404."""
    req = urllib.request.Request(url, headers={"User-Agent": "requirements-checker/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise


def parse_line(line):
    """'name==version' -> (name, version)."""
    name, _, version = line.partition("==")
    return name.strip(), version.strip()


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "requirements.txt"
    with open(path, encoding="utf-8") as f:
        lines = [l.strip() for l in f if l.strip() and not l.strip().startswith("#")]

    missing_packages = 0
    missing_versions = 0
    oldest = None  # (upload_datetime, name, version)

    for line in lines:
        name, version = parse_line(line)

        if fetch_json(f"https://pypi.org/pypi/{name}/json") is None:
            missing_packages += 1
            continue

        release = fetch_json(f"https://pypi.org/pypi/{name}/{version}/json")
        if release is None:
            missing_versions += 1
            continue

        files = release.get("urls", [])
        if not files:
            continue  # release exists but has no files, so no upload_time
        uploaded = datetime.fromisoformat(files[0]["upload_time"])  # first file listed
        if oldest is None or uploaded < oldest[0]:
            oldest = (uploaded, name, version)

    print(f"Dependencies checked: {len(lines)}")
    print(f"Packages not on PyPI: {missing_packages}")
    print(f"Versions not on PyPI: {missing_versions}")
    if oldest:
        print(f"Oldest pinned release: {oldest[1]}=={oldest[2]} ({oldest[0].year})")
    else:
        print("Oldest pinned release: none")


if __name__ == "__main__":
    main()
