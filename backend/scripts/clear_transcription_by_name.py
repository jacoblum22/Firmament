"""
Remove cached transcription / output artifacts for an upload by original filename substring,
or by explicit path to the same file bytes (SHA256 must match what the API uses).

Usage (from backend/):
  python scripts/clear_transcription_by_name.py "Pigeons"
  python scripts/clear_transcription_by_name.py --file "C:\\path\\to\\Pigeons Are GPS Drones.mp3"
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path


def backend_root() -> Path:
    return Path(__file__).resolve().parent.parent


def content_hash_of_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def remove_for_hash(root: Path, content_hash: str) -> list[str]:
    removed: list[str] = []
    targets = [
        root / "cache" / "transcriptions" / f"{content_hash}.txt",
        root / "cache" / "transcriptions" / f"{content_hash}.meta.json",
        root / "cache" / "processed" / f"{content_hash}.json",
        root / "cache" / "processed" / f"{content_hash}.meta.json",
        root / "output" / f"{content_hash}_transcription.txt",
        root / "processed" / f"{content_hash}_processed.json",
        root / "processed" / f"{content_hash}_chunks.json",
    ]
    for p in targets:
        if p.is_file():
            p.unlink()
            removed.append(str(p))
    # Strip from cache index
    index_path = root / "cache" / "index.json"
    if index_path.is_file():
        try:
            data = json.loads(index_path.read_text(encoding="utf-8"))
            entries = data.get("entries") or {}
            if content_hash in entries:
                del entries[content_hash]
                data["entries"] = entries
                index_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
                removed.append(f"{index_path} (entry {content_hash[:12]}…)")
        except (json.JSONDecodeError, OSError):
            pass
    return removed


def find_hashes_by_substring(root: Path, needle: str) -> list[str]:
    found: list[str] = []
    meta_dir = root / "cache" / "transcriptions"
    if not meta_dir.is_dir():
        return found
    for meta in meta_dir.glob("*.meta.json"):
        try:
            data = json.loads(meta.read_text(encoding="utf-8"))
            name = str(data.get("original_filename") or "")
            if needle.lower() in name.lower():
                h = data.get("content_hash") or meta.stem
                if isinstance(h, str) and len(h) == 64:
                    found.append(h)
        except (json.JSONDecodeError, OSError):
            continue
    return list(dict.fromkeys(found))


def main() -> int:
    parser = argparse.ArgumentParser(description="Clear transcription cache for a file.")
    parser.add_argument(
        "needle",
        nargs="?",
        default=None,
        help="Substring of original filename (e.g. Pigeons)",
    )
    parser.add_argument(
        "--file",
        type=Path,
        default=None,
        help="Path to the exact audio file; deletes artifacts for its SHA256 content hash.",
    )
    parser.add_argument(
        "--hash",
        dest="content_hash",
        default=None,
        help="64-char SHA256 of file bytes (same as processing_id / content hash in API).",
    )
    args = parser.parse_args()
    root = backend_root()

    hashes: list[str] = []
    if args.content_hash:
        h = args.content_hash.strip().lower()
        if len(h) != 64 or any(c not in "0123456789abcdef" for c in h):
            print("--hash must be a 64-character hex SHA256.", file=sys.stderr)
            return 1
        hashes.append(h)
    elif args.file:
        if not args.file.is_file():
            print(f"Not a file: {args.file}", file=sys.stderr)
            return 1
        hashes.append(content_hash_of_file(args.file))
    elif args.needle:
        hashes.extend(find_hashes_by_substring(root, args.needle))
        if not hashes:
            # Known historical hash for "Pigeons Are GPS Drones.mp3" from prior sessions (same bytes only).
            legacy = "f4cc6ae7a623a40e1b34618195669154488cd0b24ce49d2bae881ec89b065255"
            out_txt = root / "output" / f"{legacy}_transcription.txt"
            if out_txt.is_file():
                hashes.append(legacy)
    else:
        parser.print_help()
        return 1

    if not hashes:
        print("No matching cache metadata found and no output transcription file for legacy hash.")
        print(f"Searched under: {root}")
        return 0

    all_removed: list[str] = []
    for h in hashes:
        all_removed.extend(remove_for_hash(root, h))

    if not all_removed:
        print(f"No files removed for hash(es): {', '.join(h[:16] + '…' for h in hashes)}")
        return 0

    print("Removed:")
    for line in all_removed:
        print(f"  {line}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
