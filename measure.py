"""Compare two tiktoken encodings locally; never download during measurement."""

import argparse
from importlib import metadata
import json
from pathlib import Path
import sys
import unicodedata
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent
TIKTOKEN_VERSION = "0.12.0"
ENCODINGS = ("cl100k_base", "o200k_base")


def load_fixtures(path):
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list) or not data:
        raise ValueError("fixtures must be a nonempty JSON array")
    seen = set()
    for row in data:
        if not isinstance(row, dict) or set(row) != {"id", "group", "text"}:
            raise ValueError("each fixture must have id, group, and text")
        if not all(isinstance(row[k], str) for k in row):
            raise ValueError("fixture values must be strings")
        if not row["id"] or not row["group"] or row["id"] in seen:
            raise ValueError("fixture IDs must be nonempty and unique; group must be nonempty")
        row["text"].encode("utf-8", errors="strict")
        seen.add(row["id"])
    return data


def make_report(fixtures, encodings, normalization):
    if normalization not in ("none", "NFC", "NFD"):
        raise ValueError("unexpected normalization")
    output = []
    for row in fixtures:
        raw = row["text"]
        analyzed = raw if normalization == "none" else unicodedata.normalize(normalization, raw)
        metrics = {}
        for name, encoding in encodings.items():
            ids = encoding.encode_ordinary(analyzed)
            metrics[name] = {
                "count": len(ids),
                "ids": ids,
                "round_trip": encoding.decode_bytes(ids) == analyzed.encode("utf-8"),
            }
        output.append({
            "id": row["id"], "group": row["group"], "input": raw,
            "analyzed": analyzed, "utf8_bytes": len(analyzed.encode("utf-8")),
            "encodings": metrics,
        })
    return {"schema": 1, "tiktoken": TIKTOKEN_VERSION,
            "unicode_data": unicodedata.unidata_version,
            "normalization": normalization, "rows": output}


def json_text(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def load_encodings():
    try:
        installed = metadata.version("tiktoken")
    except metadata.PackageNotFoundError:
        raise RuntimeError("tiktoken is not installed; see README.md") from None
    if installed != TIKTOKEN_VERSION:
        raise RuntimeError(f"expected tiktoken {TIKTOKEN_VERSION}; found {installed}")
    from tiktoken import get_encoding
    from tiktoken import load

    def no_download(*_args, **_kwargs):
        raise RuntimeError("encoding cache missing or invalid; stage it first (see README.md)")

    # Both pinned encodings use load_tiktoken_bpe -> read_file_cached.
    # In the pinned implementation a verified cache hit bypasses read_file.
    # Blocking the fallback prevents first-load network access in this CLI.
    with patch.object(load, "read_file", side_effect=no_download):
        return {name: get_encoding(name) for name in ENCODINGS}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixtures", type=Path, default=ROOT / "fixtures.json")
    parser.add_argument("--normalize", choices=("none", "NFC", "NFD"), default="none")
    args = parser.parse_args(argv)
    try:
        result = make_report(load_fixtures(args.fixtures), load_encodings(), args.normalize)
    except (RuntimeError, ValueError, OSError) as err:
        parser.exit(2, f"{parser.prog}: {err}\n")
    # Explicit UTF-8 and LF keep output stable across shell locales and OSes.
    sys.stdout.buffer.write(json_text(result).encode("utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
