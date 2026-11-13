"""Download and verify a release of the official CERT Insider Threat Dataset.

Examples:
    python scripts/download_cert.py --release r1 --include-answers --extract
    python scripts/download_cert.py --list
"""

from __future__ import annotations

import argparse
import hashlib
import json
import tarfile
import urllib.request
from pathlib import Path


ARTICLE_URL = "https://api.figshare.com/v2/articles/12841247"
CHUNK_SIZE = 1024 * 1024


def get_files() -> dict[str, dict[str, object]]:
    with urllib.request.urlopen(ARTICLE_URL) as response:  # noqa: S310
        article = json.load(response)
    return {file["name"]: file for file in article["files"]}


def download(file_info: dict[str, object], destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() and destination.stat().st_size == file_info["size"]:
        print(f"Already downloaded: {destination.name}")
        return

    existing_size = destination.stat().st_size if destination.exists() else 0
    if existing_size > int(file_info["size"]):
        raise ValueError(f"Local file is larger than source: {destination}")
    action = "Resuming" if existing_size else "Downloading"
    print(f"{action} {file_info['name']} ({file_info['size']:,} bytes)...")
    request = urllib.request.Request(str(file_info["download_url"]))
    if existing_size:
        request.add_header("Range", f"bytes={existing_size}-")
    mode = "ab" if existing_size else "wb"
    with urllib.request.urlopen(request) as response, destination.open(mode) as output:  # noqa: S310
        if existing_size and response.status != 206:
            raise RuntimeError("Server did not accept a resumed download; delete the partial file and retry.")
        while chunk := response.read(CHUNK_SIZE):
            output.write(chunk)
    print(f"Saved: {destination}")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(CHUNK_SIZE), b""):
            digest.update(chunk)
    return digest.hexdigest()


def extract_safely(archive: Path, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    root = destination.resolve()
    with tarfile.open(archive, "r:bz2") as tar:
        members = tar.getmembers()
        for member in members:
            if not (destination / member.name).resolve().is_relative_to(root):
                raise ValueError(f"Unsafe archive member: {member.name}")
        tar.extractall(destination, members=members, filter="data")
    print(f"Extracted: {destination}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--release", default="r1", help="CERT release, e.g. r1 or r4.2")
    parser.add_argument("--data-dir", type=Path, default=Path("data/raw/cert"))
    parser.add_argument("--include-answers", action="store_true")
    parser.add_argument("--extract", action="store_true")
    parser.add_argument("--list", action="store_true", help="List official downloadable files")
    args = parser.parse_args()

    files = get_files()
    if args.list:
        for name, file in files.items():
            print(f"{name:28} {int(file['size']):>15,} bytes")
        return

    archive_name = f"{args.release}.tar.bz2"
    if archive_name not in files:
        raise SystemExit(f"Unknown release '{args.release}'. Run with --list.")
    archive = args.data_dir / "archives" / archive_name
    download(files[archive_name], archive)

    if args.include_answers:
        download(files["answers.tar.bz2"], args.data_dir / "archives" / "answers.tar.bz2")

    if args.extract:
        extract_safely(archive, args.data_dir / args.release)
        if args.include_answers:
            extract_safely(args.data_dir / "archives" / "answers.tar.bz2", args.data_dir / "answers")

    print(f"SHA-256 {archive.name}: {sha256(archive)}")


if __name__ == "__main__":
    main()
